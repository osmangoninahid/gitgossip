"""Concrete implementation of IRepoProvider using GitPython."""

from __future__ import annotations

from pathlib import Path

from git import InvalidGitRepositoryError, NoSuchPathError, Repo

from gitgossip.core.interfaces.repo_provider import IRepoProvider


class GitRepoProvider(IRepoProvider):
    """Provides access to a Git repository using GitPython.

    This class implements the `IRepoProvider` interface and ensures
    safe initialization of a valid repository instance.
    """

    def __init__(self, path: Path) -> None:
        """Initialize a GitRepoProvider instance."""
        self.__path = path

    def get_repo(self) -> Repo:
        """Return a GitPython Repo object for the given path.

        Raises:
            FileNotFoundError: If the path does not exist or is invalid.
            InvalidGitRepositoryError: If the path is not a valid Git repository.
        """
        repo_path = Path(self.__path).expanduser().resolve()
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {self.__path}")

        try:
            return Repo(repo_path)
        except (InvalidGitRepositoryError, NoSuchPathError) as exc:
            raise FileNotFoundError(f"Invalid or inaccessible repository: {self.__path}") from exc

    def get_diff_between_branches(self, target_branch: str) -> str:
        """Return the textual diff between the current HEAD and the target branch."""
        repo = self.get_repo()

        if target_branch not in repo.refs:
            raise ValueError(f"Target branch '{target_branch}' not found in repository.")

        try:
            diff_text = str(repo.git.diff(f"{target_branch}...HEAD", unified=3))
            return diff_text.strip()
        except Exception as e:
            raise RuntimeError(f"Failed to generate diff for branch comparison: {e}") from e
