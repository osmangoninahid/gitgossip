"""Service responsible for summarizing commits from Git repositories."""

from __future__ import annotations

from gitgossip.core.interfaces.commit_parser import ICommitParser
from gitgossip.core.interfaces.llm_analyzer import ILLMAnalyzer


class SummarizerService:
    """Generates structured commit summaries for one or more repositories."""

    def __init__(self, commit_parser: ICommitParser, llm_analyzer: ILLMAnalyzer) -> None:
        """Initialize summarizer service with injected dependencies."""
        self.__commit_parser = commit_parser
        self.__llm_analyzer = llm_analyzer

    def summarize_repository(
        self,
        author: str | None = None,
        since: str | None = None,
        limit: int = 100,
    ) -> str:
        """Summarize commits for a single repository."""
        return self.__llm_analyzer.analyze_commits(
            self.__commit_parser.get_commits(author=author, since=since, limit=limit)
        )

    def summarize_for_merge_request(self, target_branch: str) -> tuple[str, str]:
        """Compare current branch with the target branch and generate a Merge Request title & description."""
        diff_text = self.__commit_parser.repo_provider.get_diff_between_branches(target_branch)

        if not diff_text.strip():
            return (
                "No code changes detected",
                "There are no differences between the current branch and the target branch.",
            )

        return self.__llm_analyzer.generate_mr_summary(diff_text)
