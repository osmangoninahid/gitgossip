"""Service responsible for summarizing commits from Git repositories."""

from __future__ import annotations

from typing import List, Optional

from gitgossip.core.interfaces.commit_parser import ICommitParser
from gitgossip.core.models.commit import Commit


class SummarizerService:
    """Generates structured commit summaries for one or more repositories."""

    def __init__(
        self,
        commit_parser: ICommitParser,
    ) -> None:
        """Initialize summarizer service with injected dependencies."""
        self.__commit_parser = commit_parser

    def summarize_repository(
        self,
        author: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> List[Commit]:
        """Summarize commits for a single repository."""
        return self.__commit_parser.get_commits(author=author, since=since, limit=limit)
