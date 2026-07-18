"""LLMAnalyzer module."""

from __future__ import annotations

import logging
from typing import List

from rich.console import Console

from gitgossip.core.interfaces.chat_client import IChatClient
from gitgossip.core.interfaces.llm_analyzer import ILLMAnalyzer
from gitgossip.core.llm.errors import ChatClientError
from gitgossip.core.llm.prompt_builder import PromptBuilder
from gitgossip.core.models.commit import Commit


class LLMAnalyzer(ILLMAnalyzer):
    """Analyzes commits and diffs with an LLM reached through an injected chat client."""

    def __init__(self, chat_client: IChatClient, prompt_builder: PromptBuilder | None = None) -> None:
        """Initialize the analyzer with a chat transport and an optional prompt builder."""
        self.__chat_client = chat_client
        self.__prompt_builder = prompt_builder or PromptBuilder(project_name="GitGossip")
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__console = Console()

    def analyze_commits(self, commits: List[Commit]) -> str:
        """Summarize multiple commits as a coherent changelog."""
        if not commits:
            return "No commits found."

        commit_summaries = "\n".join(
            f"- {c.hash[:7]} by {c.author}: "
            f"{c.message.decode('utf-8', 'ignore') if isinstance(c.message, bytes) else c.message} "
            f"(+{c.insertions}/-{c.deletions})"
            for c in commits
        )
        prompt = self.__prompt_builder.build(
            "chunk",
            content=commit_summaries,
            context="Recent repository activity to summarize.",
        )
        return self.__complete(
            status="[bold cyan]Analyzing commits...",
            system="You summarize git repository activity clearly and succinctly.",
            user=prompt,
            temperature=0.4,
            max_tokens=500,
        )

    def generate_mr_summary(self, diff_text: str) -> tuple[str, str]:
        """Generate a Merge Request title and description from a diff."""
        if not diff_text or not diff_text.strip():
            return "No changes detected", "No differences found between branches."

        prompt = self.__prompt_builder.build(
            "final",
            content=self._safe_truncate(diff_text),
            context="Generate a concise, factual Merge Request summary suitable for team review.",
        )
        output = self.__complete(
            status="[bold cyan] Finalizing merge request summary...",
            system="You create professional, factual Merge Request titles and descriptions from code diffs.",
            user=prompt,
            temperature=0.3,
            max_tokens=600,
        )
        if output.startswith("[LLM ERROR]"):
            return "[LLM ERROR]", output.removeprefix("[LLM ERROR]").strip()
        return self._parse_mr_output(output)

    def generate_commit_message(self, diff_text: str, file_summary: str) -> str:
        """Generate a Conventional Commit message from a staged diff."""
        if not diff_text.strip():
            return "[LLM ERROR] No staged changes to describe."

        prompt = self.__prompt_builder.build(
            "commit",
            content=self._safe_truncate(diff_text),
            context="Generate a conventional commit message for the staged changes.",
            metadata=file_summary,
        )
        return self.__complete(
            status="[bold cyan]Drafting commit message...",
            system="You write concise, factual git commit messages.",
            user=prompt,
            temperature=0.3,
            max_tokens=300,
        )

    def summarize_diff_chunk(self, diff_chunk: str, metadata: str | None = None) -> str:
        """Summarize a single diff chunk into concise technical bullet points."""
        if not diff_chunk.strip():
            return "No changes detected in this chunk."

        prompt = self.__prompt_builder.build(
            "chunk",
            content=self._safe_truncate(diff_chunk),
            context="You are analyzing a small portion of a git diff to summarize code changes.",
            metadata=metadata or "",
        )
        return self.__complete(
            status="[bold cyan]Summarizing diff chunk...",
            system="You summarize code diffs concisely and factually without speculation.",
            user=prompt,
            temperature=0.3,
            max_tokens=400,
        )

    def synthesize_chunk_summaries(self, chunk_summaries: list[str]) -> str:
        """Combine multiple chunk summaries into a coherent overall summary."""
        if not chunk_summaries:
            return "No summaries to synthesize."

        prompt = self.__prompt_builder.build(
            "synthesis",
            content="\n".join(chunk_summaries),
            context="Merge partial diff summaries into one cohesive overview for a Merge Request.",
        )
        return self.__complete(
            status="[bold cyan] Synthesising diff chunk...",
            system="You create professional, factual Merge Request titles and descriptions from code diffs.",
            user=prompt,
            temperature=0.3,
            max_tokens=600,
        )

    def __complete(self, status: str, system: str, user: str, temperature: float, max_tokens: int) -> str:
        """Run one chat completion, mapping transport errors to the '[LLM ERROR]' string contract."""
        try:
            with self.__console.status(status, spinner="dots"):
                return self.__chat_client.complete(
                    system=system, user=user, temperature=temperature, max_tokens=max_tokens
                ).strip()
        except ChatClientError as exc:
            self.__logger.error("LLM request failed: %s", exc)
            return f"[LLM ERROR] {exc}"

    def _safe_truncate(self, text: str, limit: int = 8000) -> str:
        """Truncate large text safely to avoid context overflow."""
        if len(text) > limit:
            self.__logger.warning(
                "Input text length (%d) exceeds model limit (%d). Truncating.",
                len(text),
                limit,
            )
            return text[:limit] + "\n\n[TRUNCATED DUE TO CONTEXT LIMIT]"
        return text

    @staticmethod
    def _parse_mr_output(output: str) -> tuple[str, str]:
        """Extract title and bullet list from model output."""
        title = ""
        bullets: list[str] = []
        for line in output.splitlines():
            if line.lower().startswith("title:"):
                title = line.split(":", 1)[1].strip()
            elif line.lower().startswith("description:"):
                continue
            elif line.strip().startswith("-"):
                bullets.append(line.strip())
        if not title:
            title = "Auto-generated Merge Request"
        return title, "\n".join(bullets)
