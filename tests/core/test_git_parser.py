"""Unit tests for GitParser core logic."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from git import Repo

from gitgossip.core.git_parser import GitParser
from gitgossip.core.models.commit import Commit


class TestGitParser:  # noqa: D101
    """Test suite for GitParser class."""

    @pytest.fixture()
    def tmp_git_repo(self, tmp_path: Path) -> Path:  # noqa: D102
        """Create a temporary Git repository for testing."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        repo = Repo.init(repo_path)

        # Create a dummy file and commit
        test_file = repo_path / "README.md"
        test_file.write_text("# Sample\n")
        repo.index.add([str(test_file)])
        repo.index.commit("Initial commit", author_date="2025-10-08T12:00:00", commit_date="2025-10-08T12:00:00")

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
        assert isinstance(commits, list)
        assert all(isinstance(c, Commit) for c in commits)
        assert commits[0].hash
        assert commits[0].author
        assert isinstance(commits[0].date, datetime)

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
