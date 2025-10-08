"""Unit tests for CommitParser logic with injected GitRepoProvider."""

from __future__ import annotations

from pathlib import Path

import pytest
from git import Repo

from gitgossip.core.parsers.commit_parser import CommitParser
from gitgossip.core.providers.git_repo_provider import GitRepoProvider


class TestCommitParser:  # noqa: D101
    """Test suite for CommitParser with real Git repository."""

    @pytest.fixture()
    def tmp_git_repo(self, tmp_path: Path) -> Path:
        """Create a temporary Git repository for testing."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        repo = Repo.init(repo_path)

        test_file = repo_path / "README.md"

        # Commit 1 — base version
        test_file.write_text("# Sample\n")
        repo.index.add([str(test_file)])
        repo.index.commit("Initial commit")

        # Commit 2 — create content
        test_file.write_text("# Sample Title\nLine 1\nLine 2\nLine 3\n")
        repo.index.add([str(test_file)])
        repo.index.commit("docs: initial version")

        # Commit 3 — modify lines
        test_file.write_text("# Updated Title\nLine 1 changed\nLine 2 added\nLine 3 removed\nLine 4 new content\n")
        repo.index.add([str(test_file)])
        repo.index.commit("docs: update README")

        return repo_path

    def test_init_valid_repo(self, tmp_git_repo: Path) -> None:
        """Should initialize correctly for a valid repository."""
        # given
        provider = GitRepoProvider(tmp_git_repo)

        # when
        parser = CommitParser(repo_provider=provider)

        # then
        assert parser.repo is not None
        assert parser.has_commits

    def test_init_invalid_path(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError for invalid path."""
        # given
        invalid = tmp_path / "doesnotexist"

        # when and then
        with pytest.raises(FileNotFoundError):
            CommitParser(repo_provider=GitRepoProvider(invalid))

    def test_get_commits_returns_list(self, tmp_git_repo: Path) -> None:
        """Should return structured commits."""
        # given
        parser = CommitParser(repo_provider=GitRepoProvider(tmp_git_repo))

        # when
        commits = parser.get_commits()

        # then
        assert commits
        latest = commits[0]
        assert latest.hash
        assert isinstance(latest.changes, list)
        assert latest.changes[0]["file"].endswith("README.md")

    def test_get_commits_with_author_filter(self, tmp_git_repo: Path) -> None:
        """Should return empty list for unknown author."""
        # given
        parser = CommitParser(repo_provider=GitRepoProvider(tmp_git_repo))

        # when
        commits = parser.get_commits(author="ghost@example.com")

        # then
        assert not commits

    def test_get_commits_with_limit(self, tmp_git_repo: Path) -> None:
        """Should respect the limit argument."""
        # given
        parser = CommitParser(repo_provider=GitRepoProvider(tmp_git_repo))

        # when
        commits = parser.get_commits(limit=1)

        # then
        assert len(commits) == 1

    def test_extract_diffs_detects_changes(self, tmp_git_repo: Path) -> None:
        """Should detect modified lines and added hunks."""
        # given
        parser = CommitParser(repo_provider=GitRepoProvider(tmp_git_repo))

        # when
        commits = parser.get_commits(limit=2)
        # then
        latest = commits[0]
        summaries = [s.lower() for s in latest.changes[0]["summary"]]
        assert any("added" in s or "modified" in s for s in summaries)
