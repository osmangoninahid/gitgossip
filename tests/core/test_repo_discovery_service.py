"""Unit tests for RepoDiscoveryService."""

from pathlib import Path

import pytest
from git import Repo

from gitgossip.core.services.repo_discovery_service import RepoDiscoveryService


class TestRepoDiscoveryService:
    """Verify repository discovery behavior."""

    def test_find_repositories_non_recursive(self, tmp_path: Path) -> None:
        """Should find direct subdirectory repos only."""
        # given
        repo1 = tmp_path / "repo1"
        repo1.mkdir()
        Repo.init(repo1)
        service = RepoDiscoveryService(base_dir=tmp_path, recursive=False)

        # when
        repos = service.find_repositories()

        # then
        assert repo1 in repos

    def test_find_repositories_recursive(self, tmp_path: Path) -> None:
        """Should find nested repos when recursive=True."""
        # given
        nested = tmp_path / "parent" / "nested"
        nested.mkdir(parents=True)
        Repo.init(nested)
        service = RepoDiscoveryService(base_dir=tmp_path, recursive=True)

        # when
        repos = service.find_repositories()

        # then
        assert any("nested" in str(r) for r in repos)

    def test_invalid_directory_raises(self, tmp_path: Path) -> None:
        """Should raise if base_dir does not exist."""
        # when
        bad = tmp_path / "missing"

        # given
        service = RepoDiscoveryService(base_dir=bad)

        # then
        with pytest.raises(FileNotFoundError):
            service.find_repositories()
