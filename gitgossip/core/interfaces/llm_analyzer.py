"""Interface defining contract for any LLM-based commit analyzer."""

from __future__ import annotations

from abc import ABC, abstractmethod

from gitgossip.core.models.commit import Commit


class ILLMAnalyzer(ABC):
    """Defines contract for commit analysis using a Large Language Model."""

    @abstractmethod
    def analyze_commits(self, commits: list[Commit]) -> str:
        """Generate a natural-language analysis of given commits."""
        raise NotImplementedError

    @abstractmethod
    def generate_mr_summary(self, diff_text: str) -> tuple[str, str]:
        """Generate a Merge Request title and description from a diff."""
        raise NotImplementedError

    @abstractmethod
    def summarize_diff_chunk(self, diff_chunk: str, metadata: str | None = None) -> str:
        """Summarize a single diff chunk into concise bullet points."""
        raise NotImplementedError

    @abstractmethod
    def synthesize_chunk_summaries(self, chunk_summaries: list[str]) -> str:
        """Combine multiple chunk summaries into a coherent overall summary."""
        raise NotImplementedError
