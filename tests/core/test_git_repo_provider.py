"""Unit tests for GitRepoProvider."""

from pathlib import Path

import pytest
from git import Repo

from gitgossip.core.providers.git_repo_provider import GitRepoProvider


class TestGitRepoProvider:
    """Test behavior of GitRepoProvider."""

    def test_get_repo_valid_path(self, tmp_path: Path) -> None:
        """Should return Repo instance for valid path."""
        # given
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        Repo.init(repo_dir)
        provider = GitRepoProvider(repo_dir)
        # when
        repo = provider.get_repo()

        # then
        assert repo.working_tree_dir == str(repo_dir)

    def test_get_repo_invalid_path(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError if path invalid."""
        # given
        invalid = tmp_path / "nope"
        provider = GitRepoProvider(invalid)

        # when & then
        with pytest.raises(FileNotFoundError):
            provider.get_repo()
