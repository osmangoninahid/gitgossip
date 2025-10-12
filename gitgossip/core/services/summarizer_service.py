"""Service responsible for summarizing commits from Git repositories."""

from __future__ import annotations

import logging
from typing import List

from rich.progress import Progress

from gitgossip.core.interfaces.commit_parser import ICommitParser
from gitgossip.core.interfaces.llm_analyzer import ILLMAnalyzer


class SummarizerService:
    """Generates structured commit summaries for one or more repositories."""

    def __init__(self, commit_parser: ICommitParser, llm_analyzer: ILLMAnalyzer, chunk_size: int = 8000) -> None:
        """Initialize summarizer service with injected dependencies."""
        self.__commit_parser = commit_parser
        self.__llm_analyzer = llm_analyzer
        self.__chunk_size = chunk_size
        self.__logger = logging.getLogger(self.__class__.__name__)

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

        # Always use chunk-based summarization for diffs
        if len(diff_text) <= self.__chunk_size:
            self.__logger.debug("Small diff detected (%d chars), summarizing directly", len(diff_text))
            chunk_summaries = [self.__llm_analyzer.summarize_diff_chunk(diff_text, metadata="[Single Chunk]")]
        else:
            self.__logger.debug("Large diff detected (%d chars), splitting into chunks", len(diff_text))
            chunk_summaries = self._summarize_diff_in_chunks(diff_text)

        # First, merge all chunk summaries into a readable combined summary
        merged_summary = "\n".join(chunk_summaries)

        # Then, synthesize them into a high-level summary (LLM merging step)
        synthesized_text = self.__llm_analyzer.synthesize_chunk_summaries(chunk_summaries)

        # If synthesis fails or returns placeholder text, fall back to merged_summary
        final_text = (
            synthesized_text if synthesized_text and not synthesized_text.startswith("[LLM ERROR]") else merged_summary
        )

        # Pass combined summary to final MR generator
        return self.__llm_analyzer.generate_mr_summary(final_text)

    def _summarize_diff_in_chunks(self, diff_text: str) -> List[str]:
        """Split a large diff into chunks and summarize each."""
        chunks = self._split_diff(diff_text)
        summaries: List[str] = []

        with Progress(transient=True) as progress:
            task = progress.add_task("[cyan]Summarizing diff chunks...", total=len(chunks))

            for idx, chunk in enumerate(chunks, start=1):
                summary = self.__llm_analyzer.summarize_diff_chunk(
                    diff_chunk=chunk, metadata=f"[Part {idx}/{len(chunks)}]"
                )
                summaries.append(summary)
                progress.update(task, advance=1)

        return summaries

    def _split_diff(self, diff_text: str) -> List[str]:
        """Split large diff text into size-safe chunks preserving line boundaries."""
        lines = diff_text.splitlines()
        chunks: List[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for line in lines:
            line_len = len(line) + 1
            if current_len + line_len > self.__chunk_size:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_len = 0
            current_chunk.append(line)
            current_len += line_len

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        self.__logger.debug("Split diff into %d chunks", len(chunks))
        return chunks
