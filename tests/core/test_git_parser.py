"""Unit tests for GitParser core logic."""

from __future__ import annotations

from pathlib import Path

import pytest
from git import Repo

from gitgossip.core.git_parser import GitParser


class TestGitParser:  # noqa: D101
    """Test suite for GitParser class."""

    @pytest.fixture()
    def tmp_git_repo(self, tmp_path: Path) -> Path:  # noqa: D102
        """Create a temporary Git repository for testing."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        repo = Repo.init(repo_path)

        test_file = repo_path / "README.md"

        # Commit 1 — base version
        test_file.write_text("# Sample\n")
        repo.index.add([str(test_file)])
        repo.index.commit(
            "Initial commit",
            author_date="2025-10-08T12:00:00",
            commit_date="2025-10-08T12:00:00",
        )

        # Commit 2 — create some real content
        test_file.write_text("# Sample Title\nLine 1\nLine 2\nLine 3\n")
        repo.index.add([str(test_file)])
        repo.index.commit(
            "docs: initial version",
            author_date="2025-10-08T12:05:00",
            commit_date="2025-10-08T12:05:00",
        )

        # Commit 3 — modify lines to produce real hunks
        test_file.write_text(
            "# Updated Sample Title\nLine 1 changed\nLine 2 added\nLine 3 removed\nLine 4 new content\n"
        )
        repo.index.add([str(test_file)])
        repo.index.commit(
            "docs: update README with new section",
            author_date="2025-10-08T12:10:00",
            commit_date="2025-10-08T12:10:00",
        )

        return repo_path

    def test_init_valid_repo(self, tmp_git_repo: Path) -> None:  # noqa: D102
        """Should initialize correctly for a valid repository."""
        parser = GitParser(str(tmp_git_repo))
        assert parser.repo is not None
        assert isinstance(parser.has_commits, bool)

    def test_init_invalid_path(self, tmp_path: Path) -> None:  # noqa: D102
        """Should raise FileNotFoundError for invalid path."""
        invalid_path = tmp_path / "nonexistent"
        with pytest.raises(FileNotFoundError):
            GitParser(str(invalid_path))

    def test_get_commits_returns_list_of_commits(self, tmp_git_repo: Path) -> None:  # noqa: D102
        """Should return list of Commit objects."""
        parser = GitParser(str(tmp_git_repo))
        commits = parser.get_commits()
        latest = commits[0]
        assert latest.changes, "Expected structured changes"
        first_change = latest.changes[0]
        assert "file" in first_change
        assert first_change["file"].endswith("README.md")
        assert isinstance(first_change["hunks"], list)
        assert any("added" in h for h in first_change["hunks"]), "Expected added lines in hunks"
        assert isinstance(first_change["summary"], list)
        assert any("Added" in s or "Modified" in s for s in first_change["summary"])

    def test_get_commits_with_author_filter(self, tmp_git_repo: Path) -> None:  # noqa: D102
        """Should return empty list for unknown author."""
        parser = GitParser(str(tmp_git_repo))
        commits = parser.get_commits(author="ghost@example.com")
        assert isinstance(commits, list)
        assert not commits  # noqa: C1803

    def test_get_commits_with_limit(self, tmp_git_repo: Path) -> None:  # noqa: D102
        """Should respect the limit argument."""
        parser = GitParser(str(tmp_git_repo))
        commits = parser.get_commits(limit=1)
        assert len(commits) <= 1

    def test_get_commits_with_since_days(self, tmp_git_repo: Path) -> None:  # noqa: D102
        """Should handle 'since' argument (e.g. '1days') without error."""
        parser = GitParser(str(tmp_git_repo))
        commits = parser.get_commits(since="1days")
        assert isinstance(commits, list)

    def test_extract_diffs_detects_changes(self, tmp_git_repo: Path) -> None:  # noqa: D102
        """Should detect changed content and summarize it properly."""
        parser = GitParser(str(tmp_git_repo))
        commits = parser.get_commits(limit=2)
        latest = commits[0]

        # verify that summary text is meaningful
        summaries = [s.lower() for s in latest.changes[0]["summary"]]
        assert any("added" in s or "modified" in s for s in summaries)
