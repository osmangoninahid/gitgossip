"""Core logic for parsing Git repositories and extracting commit metadata."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

from git import InvalidGitRepositoryError, NoSuchPathError, Repo

from gitgossip.core.models.commit import Commit


class GitParser:
    """Parses commits from a Git repository with optional filters (author, since, limit)."""

    def __init__(self, repo_path: str = ".") -> None:
        """Initialize a GitParser instance.

        Args:
            repo_path: Path to the git repository.

        Returns:
            Instance of GitParser instance.

        """
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"{repo_path} does not exist")

        try:
            self.repo = Repo(repo_path)
        except (InvalidGitRepositoryError, NoSuchPathError):
            raise FileNotFoundError(f"{repo_path} does not exist")

        head = self.repo.head
        if head.is_detached or not head.is_valid():
            self.has_commits = False
        else:
            self.has_commits = True

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
            kwargs["since"] = self._parse_since(since)

        commits: list[Commit] = []
        for commit in self.repo.iter_commits(max_count=limit, **kwargs):
            stats = commit.stats.total
            commits.append(
                Commit(
                    hash=commit.hexsha,
                    author=commit.author.name or "Unknown",
                    email=commit.author.email or "unknown@example.com",
                    date=commit.committed_datetime,
                    message=(
                        commit.summary if isinstance(commit.summary, str) else commit.summary.decode("utf-8", "ignore")
                    ),
                    insertions=stats.get("insertions", 0),
                    deletions=stats.get("deletions", 0),
                    files_changed=stats.get("files", 0),
                )
            )
        return commits

    @staticmethod
    def _parse_since(since: str) -> str:
        """Convert a 'since' argument into an ISO date string."""
        since = since.strip().lower()
        if since.endswith("days"):
            try:
                days = int(since.replace("days", "").strip())
            except ValueError:
                raise ValueError(f"{since} is not a valid ISO date")
            return (datetime.now() - timedelta(days=days)).isoformat()
        try:
            dt = datetime.fromisoformat(since)
            return dt.isoformat()
        except ValueError:
            raise ValueError(f"{since} is not a valid ISO date")
