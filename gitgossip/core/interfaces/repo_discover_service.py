"""Interface for discovering Git repositories within a given directory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class IRepoDiscoveryService(ABC):
    """Abstract interface defining Git repository discovery behavior."""

    @abstractmethod
    def find_repositories(self) -> List[Path]:
        """Find Git repositories inside the given directory.

        Returns:
            A list of Paths representing valid Git repositories.
        """
        raise NotImplementedError

    @abstractmethod
    def is_valid_repo(self) -> bool:
        """Check if the given path is a valid Git repository.

        Returns:
            True if the path represents a valid Git repository, False otherwise.
        """
        raise NotImplementedError
