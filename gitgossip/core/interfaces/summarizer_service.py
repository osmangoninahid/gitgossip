"""Interface defining the behavior of a commit summarization service."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from gitgossip.core.models.commit import Commit


class ISummarizerService(ABC):
    """Abstract interface for summarizing commits from one or more repositories."""

    @abstractmethod
    def summarize_repository(
        self,
        repo_path: Path,
        author: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> List[Commit]:
        """Summarize commits for a single repository.

        Args:
            repo_path: Path to the Git repository.
            author: Optional author name or email to filter commits.
            since: Optional date or relative time string (e.g., "7days").
            limit: Maximum number of commits to return.

        Returns:
            List of Commit models representing summarized commits.
        """
        raise NotImplementedError

    @abstractmethod
    def summarize_directory(
        self,
        base_dir: Path,
        author: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> dict[str, List[Commit]]:
        """Summarize commits across multiple Git repositories in a directory.

        Args:
            base_dir: Base directory to search for Git repositories.
            author: Optional author filter.
            since: Optional time filter.
            limit: Maximum number of commits to include per repository.

        Returns:
            Dictionary mapping repository name to commit summaries.
        """
        raise NotImplementedError
