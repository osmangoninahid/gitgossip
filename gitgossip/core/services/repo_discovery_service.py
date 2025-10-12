"""Service for discovering Git repositories under a given directory."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError

from gitgossip.core.interfaces.repo_discover_service import IRepoDiscoveryService


class RepoDiscoveryService(IRepoDiscoveryService):
    """Locates Git repositories in a given directory path."""

    def __init__(self, base_dir: Path, recursive: bool = False) -> None:
        """Initialize the discovery service.

        Args:
            base_dir (Path): The directory to discover Git repositories from.
            recursive: Whether to search subdirectories recursively.
        """
        self._base_dir = base_dir
        self.recursive = recursive

    def find_repositories(self) -> List[Path]:
        """Find Git repositories inside the given directory.

        Returns:
            A list of Paths representing valid Git repositories.
        """
        if not self._base_dir.exists():
            raise FileNotFoundError(f"Path does not exist: {self._base_dir}")

        if not self._base_dir.is_dir():
            raise NotADirectoryError(f"Expected directory, got file: {self._base_dir}")

        repos: list[Path] = []

        # Case 1: if this directory itself is a repo
        if (self._base_dir / ".git").exists():
            repos.append(self._base_dir)
            return repos

        # Case 2: look for nested repos
        for sub in self._base_dir.iterdir():
            if (sub / ".git").exists():
                repos.append(sub)
            elif self.recursive and sub.is_dir():
                for root, dirs, _ in os.walk(sub):
                    if ".git" in dirs:
                        repos.append(Path(root))
                        dirs.clear()  # stop recursion below this repo
                        break

        return repos

    def is_valid_repo(self) -> bool:
        """Check whether the given path is a valid Git repository."""
        try:
            _ = Repo(self._base_dir)
            return True
        except (InvalidGitRepositoryError, NoSuchPathError):
            return False
