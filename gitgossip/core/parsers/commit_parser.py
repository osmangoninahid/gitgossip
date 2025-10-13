"""Core logic for parsing Git repositories and extracting commit metadata."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional

from git import Commit as GitCommit
from git import Repo

from gitgossip.core.constants import (
    DEFAULT_FUNC_PATTERN,
    IGNORED_DIFF_FILES,
    IGNORED_EXTENSIONS,
    LANG_FUNC_PATTERNS,
    MAX_DIFF_SIZE,
)
from gitgossip.core.interfaces.commit_parser import ICommitParser
from gitgossip.core.interfaces.repo_provider import IRepoProvider
from gitgossip.core.models.commit import Commit
from gitgossip.utils.parse import parse_since


class CommitParser(ICommitParser):
    """Parses commits from a Git repository with optional filters (author, since, limit)."""

    def __init__(self, repo_provider: IRepoProvider) -> None:
        """Initialize a CommitParser with a repo provider."""
        self.__repo_provider = repo_provider
        self.__repo: Repo = repo_provider.get_repo()
        self.has_commits = bool(self.__repo.head.is_valid()) and not self.__repo.head.is_detached

    @property
    def repo_provider(self) -> IRepoProvider:
        """Expose the repository provider used by this parser."""
        return self.__repo_provider

    def get_commits(
        self,
        author: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> list[Commit]:
        """Extract commits from a given Git repository.

        Args:
            author (str, optional): Filter commits by author name or email.
            since (str, optional): Limit commits since a date ("7days" or "YYYY-MM-DD").
            limit (int): Maximum number of commits to return.

        Returns:
            list[dict[str, Any]]: A list of commit metadata dictionaries
            containing hash, author, date, message, and change statistics.

        Raises:
            FileNotFoundError: If `repo_path` does not exist.
            ValueError: If the path is not a valid Git repository
                        or the 'since' parameter is invalid.
        """
        kwargs = {}
        if author is not None:
            kwargs["author"] = author
        if since is not None:
            kwargs["since"] = parse_since(since)

        commits: list[Commit] = []
        for commit in self.__repo.iter_commits(max_count=limit, **kwargs):
            commits.append(self._parse_commit(commit))
        return commits

    def _parse_commit(self, commit: GitCommit) -> Commit:
        """Convert a GitPython Commit object into our Commit domain model."""
        stats = commit.stats.total
        structured_changes = self._extract_diffs(commit)

        return Commit(
            hash=commit.hexsha,
            author=commit.author.name or "Unknown",
            email=commit.author.email or "unknown@example.com",
            date=commit.committed_datetime,
            message=(commit.summary if isinstance(commit.summary, str) else commit.summary.decode("utf-8", "ignore")),
            insertions=stats.get("insertions", 0),
            deletions=stats.get("deletions", 0),
            files_changed=stats.get("files", 0),
            changes=structured_changes,
        )

    def _extract_diffs(self, commit: GitCommit) -> list[dict[str, Any]]:
        """Parse per-file diffs into structured data."""
        diffs: list[dict[str, Any]] = []
        parent = commit.parents[0] if commit.parents else None
        for diff in parent.diff(commit, create_patch=True) if parent else []:
            file_path = diff.b_path or diff.a_path
            if not file_path:
                continue
            path_obj = Path(file_path)
            if path_obj.name in IGNORED_DIFF_FILES or path_obj.suffix in IGNORED_EXTENSIONS:
                continue
            if diff.new_file or diff.deleted_file or diff.renamed_file:
                continue

            try:
                diff_text = self._get_diff_text(diff)
                if not diff_text:
                    continue
                if len(diff_text) > MAX_DIFF_SIZE:
                    diffs.append({"file": file_path, "warning": "Diff too large, skipped"})
                    continue
                file_summary = self._summarize_diff(file_path, diff_text)
                diffs.append(file_summary)
            except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                diffs.append({"file": file_path or "unknown", "error": f"Failed to parse diff: {e}"})
        return diffs

    def _summarize_diff(self, file_path: str, diff_text: str) -> dict[str, Any]:
        """Build file-level structured summary including language, hunks, and changed functions."""
        language = self._detect_language(file_path)
        hunks = self._parse_hunks(diff_text)
        pattern = LANG_FUNC_PATTERNS.get(language, DEFAULT_FUNC_PATTERN)
        changed_functions = list({m.group(1) for m in pattern.finditer(diff_text) if m and m.group(1)})
        summary = self._summarize_hunks(hunks, file_path)
        return {
            "file": file_path,
            "language": language,
            "changed_functions": changed_functions,
            "hunks": hunks,
            "summary": summary,
        }

    @staticmethod
    def _parse_hunks(diff_text: str) -> list[dict[str, Any]]:
        """Extract structured hunks (added/removed/context lines) from unified diff text."""
        hunks: list[dict[str, Any]] = []
        current_hunk: dict[str, Any] | None = None

        for line in diff_text.splitlines():
            if line.startswith("@@"):
                match = re.match(r"@@ -(\d+),?\d* \+(\d+),?\d* @@", line)
                if match:
                    if current_hunk:
                        hunks.append(current_hunk)
                    current_hunk = {
                        "old_start": int(match.group(1)),
                        "new_start": int(match.group(2)),
                        "added": [],
                        "removed": [],
                        "context": [],
                    }
                continue

            if not current_hunk:
                continue

            if line.startswith("+") and not line.startswith("+++"):
                current_hunk["added"].append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                current_hunk["removed"].append(line[1:])
            else:
                current_hunk["context"].append(line)

        if current_hunk:
            hunks.append(current_hunk)
        return hunks

    @staticmethod
    def _detect_language(path: str) -> str:
        """Infer language from file extension."""
        ext = os.path.splitext(path)[1].lower()
        return {
            ".py": "python",
            ".go": "go",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".sh": "bash",
            ".yaml": "yaml",
            ".yml": "yaml",
        }.get(ext, "unknown")

    @staticmethod
    def _summarize_hunks(hunks: list[dict[str, Any]], file_path: str) -> list[str]:
        """Summarize each hunk by describing what changed and roughly where."""
        summaries: list[str] = []
        for h in hunks:
            added = len(h["added"])
            removed = len(h["removed"])
            start = h["new_start"]
            if added and not removed:
                summaries.append(f"Added {added} new lines in {file_path} around line {start}.")
            elif removed and not added:
                summaries.append(f"Removed {removed} lines from {file_path} around line {start}.")
            elif added and removed:
                summaries.append(
                    f"Modified {added + removed} lines in {file_path} "
                    f"({removed} removed, {added} added near line {start})."
                )
        return summaries

    @staticmethod
    def _get_diff_text(diff: Any) -> str:
        """Safely decode diff data to text, with size guard."""
        diff_data = getattr(diff, "diff", "")
        if not diff_data:
            return ""
        if isinstance(diff_data, bytes):
            if len(diff_data) > MAX_DIFF_SIZE:
                return ""
            return diff_data.decode("utf-8", "ignore")
        diff_str = str(diff_data)
        return diff_str if len(diff_str) <= MAX_DIFF_SIZE else ""
