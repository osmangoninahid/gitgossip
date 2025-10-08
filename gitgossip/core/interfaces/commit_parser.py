"""Abstract interface for commit parsing behavior."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from gitgossip.core.models.commit import Commit


class ICommitParser(ABC):
    """Defines an abstract contract for parsing a raw Git commit.

    Concrete implementations must transform a GitPython `Commit` object
    into a structured `Commit` domain model containing metadata and
    extracted change details.
    """

    @abstractmethod
    def get_commits(
        self,
        author: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> list[Commit]:
        """Retrieve commits from the repository."""
        raise NotImplementedError
