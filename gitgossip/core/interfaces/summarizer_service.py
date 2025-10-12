"""Interface defining the behavior of a commit summarization service."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ISummarizerService(ABC):
    """Abstract interface for summarizing commits from one or more repositories."""

    @abstractmethod
    def summarize_repository(
        self,
        repo_path: Path,
        author: str | None = None,
        since: str | None = None,
        limit: int = 100,
    ) -> str:
        """Summarize commits for a single repository.

        Args:
            repo_path: Path to the Git repository.
            author: Optional author name or email to filter commits.
            since: Optional date or relative time string (e.g., "7days").
            limit: Maximum number of commits to return.

        Returns:
            summarized commits.
        """
        raise NotImplementedError

    @abstractmethod
    def summarize_for_merge_request(self, target_branch: str) -> tuple[str, str]:
        """Summarize commits for a single repository.

        Args:
            target_branch: Target branch to summarize.

        Returns:
            merge request title and description.
        """
        raise NotImplementedError
