"""Abstract interface for providing Git repository access."""

from __future__ import annotations

from abc import ABC, abstractmethod

from git import Repo


class IRepoProvider(ABC):
    """Defines an abstract contract for accessing a Git repository.

    Implementations must handle repository initialization, validation,
    and return a usable `Repo` instance from GitPython.
    """

    @abstractmethod
    def get_repo(self) -> Repo:
        """Return a valid GitPython Repo object for the given path.

        Raises:
            FileNotFoundError: If the path does not exist or is invalid.
        """
