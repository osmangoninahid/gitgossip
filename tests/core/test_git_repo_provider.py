"""Unit tests for GitRepoProvider."""

import subprocess
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


@pytest.fixture()
def staged_repo(tmp_path: Path) -> Path:
    """Create a temp git repo with one committed file and one staged change."""
    subprocess.run(["git", "init", "-b", "main", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@t.com"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "t"], check=True)
    (tmp_path / "a.txt").write_text("one\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "a.txt"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "--no-gpg-sign", "-m", "init"], check=True, capture_output=True
    )
    (tmp_path / "a.txt").write_text("one\ntwo\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("new file\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "a.txt", "b.txt"], check=True)
    return tmp_path


class TestStagedDiff:
    """Verify staged diff and staged file listing."""

    def test_get_staged_diff_contains_changes(self, staged_repo: Path) -> None:
        # given
        provider = GitRepoProvider(path=staged_repo)

        # when
        diff = provider.get_staged_diff()

        # then
        assert "+two" in diff
        assert "b.txt" in diff

    def test_get_staged_files_lists_names(self, staged_repo: Path) -> None:
        # given
        provider = GitRepoProvider(path=staged_repo)

        # when
        files = provider.get_staged_files()

        # then
        assert sorted(files) == ["a.txt", "b.txt"]

    def test_get_staged_diff_empty_when_nothing_staged(self, staged_repo: Path) -> None:
        # given
        subprocess.run(
            ["git", "-C", str(staged_repo), "commit", "--no-gpg-sign", "-m", "wip"], check=True, capture_output=True
        )
        provider = GitRepoProvider(path=staged_repo)

        # when / then
        assert provider.get_staged_diff() == ""
        assert provider.get_staged_files() == []
