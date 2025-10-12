"""LLMAnalyzer module."""

from __future__ import annotations

import logging
from typing import List

from openai import APIConnectionError, APIError, OpenAI, RateLimitError

from gitgossip.core.interfaces.llm_analyzer import ILLMAnalyzer
from gitgossip.core.llm.prompt_builder import PromptBuilder
from gitgossip.core.models.commit import Commit


class LLMAnalyzer(ILLMAnalyzer):
    """Uses an LLM (e.g., GPT-4/5) to analyze multiple commits.

    And produce a repository-level summary of contributions.
    """

    def __init__(self, base_url: str, model: str, api_key: str | None = None) -> None:
        """Initialize an LLMAnalyzer with an LLM model."""
        self.__client = OpenAI(base_url=base_url, api_key=api_key)
        self.__prompt_builder = PromptBuilder(project_name="GitGossip")
        self.__model = model
        self.__logger = logging.getLogger(self.__class__.__name__)

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

        try:
            prompt = self.__prompt_builder.build(
                "chunk",
                content=commit_summaries,
                context="Recent repository activity to summarize.",
            )
            response = self.__client.chat.completions.create(
                model=self.__model,
                messages=[
                    {"role": "system", "content": "You summarize git repository activity clearly and succinctly."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=500,
            )
            content = response.choices[0].message.content
            if not content:
                return "[LLM ERROR] Empty response from model"
            return content.strip()
        except (APIError, APIConnectionError, RateLimitError) as e:
            self.__logger.error("LLM API request failed: %s", e)
            return f"[LLM ERROR] {e}"
        except OSError as e:
            self.__logger.error("System or network issue during LLM call: %s", e)
            return f"[SYSTEM ERROR] {e}"

    def generate_mr_summary(self, diff_text: str) -> tuple[str, str]:
        """Generate a Merge Request title and description from a diff."""
        if not diff_text or not diff_text.strip():
            return "No changes detected", "No differences found between branches."

        try:
            prompt = self.__prompt_builder.build(
                "final",
                content=self._safe_truncate(diff_text),
                context="Generate a concise, factual Merge Request summary suitable for team review.",
            )

            response = self.__client.chat.completions.create(
                model=self.__model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You create professional, factual Merge Request titles and " "descriptions from code diffs."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=600,
            )

            content = response.choices[0].message.content
            if not content:
                return "[LLM ERROR]", "Empty response from model"
            output = content.strip()
            return self._parse_mr_output(output)

        except (APIError, APIConnectionError, RateLimitError) as e:
            self.__logger.error("LLM API request failed: %s", e)
            return "[LLM ERROR]", str(e)
        except OSError as e:
            self.__logger.error("System or network issue during LLM MR call: %s", e)
            return "[SYSTEM ERROR]", str(e)

    def summarize_diff_chunk(self, diff_chunk: str, metadata: str | None = None) -> str:
        """Summarize a single diff chunk into concise technical bullet points."""
        if not diff_chunk.strip():
            return "No changes detected in this chunk."

        try:
            prompt = self.__prompt_builder.build(
                "chunk",
                content=self._safe_truncate(diff_chunk),
                context="You are analyzing a small portion of a git diff to summarize code changes.",
                metadata=metadata or "",
            )

            response = self.__client.chat.completions.create(
                model=self.__model,
                messages=[
                    {
                        "role": "system",
                        "content": "You summarize code diffs concisely and factually without speculation.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=400,
            )

            content = response.choices[0].message.content
            if not content:
                return "[LLM ERROR] Empty response from model"

            return content.strip()

        except (APIError, APIConnectionError, RateLimitError) as e:
            self.__logger.error("LLM API request failed during chunk summary: %s", e)
            return f"[LLM ERROR] {e}"
        except OSError as e:
            self.__logger.error("System or network issue during LLM chunk call: %s", e)
            return f"[SYSTEM ERROR] {e}"

    def synthesize_chunk_summaries(self, chunk_summaries: list[str]) -> str:
        """Combine multiple chunk summaries into a coherent overall summary."""
        if not chunk_summaries:
            return "No summaries to synthesize."

        try:
            merged_text = "\n".join(chunk_summaries)

            prompt = self.__prompt_builder.build(
                "synthesis",
                content=merged_text,
                context="Merge partial diff summaries into one cohesive overview for a Merge Request.",
            )

            response = self.__client.chat.completions.create(
                model=self.__model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You create professional, factual Merge Request titles and " "descriptions from code diffs."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=600,
            )

            content = response.choices[0].message.content
            if not content:
                return "[LLM ERROR] Empty synthesis response"

            return content.strip()

        except (APIError, APIConnectionError, RateLimitError) as e:
            self.__logger.error("LLM API request failed during synthesis: %s", e)
            return f"[LLM ERROR] {e}"
        except OSError as e:
            self.__logger.error("System or network issue during synthesis call: %s", e)
            return f"[SYSTEM ERROR] {e}"

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
