"""LLMAnalyzer module."""

from __future__ import annotations

import logging
import os
from typing import List

from openai import APIConnectionError, APIError, OpenAI, RateLimitError

from gitgossip.core.interfaces.llm_analyzer import ILLMAnalyzer
from gitgossip.core.models.commit import Commit


class LLMAnalyzer(ILLMAnalyzer):
    """Uses an LLM (e.g., GPT-4/5) to analyze multiple commits.

    And produce a repository-level summary of contributions.
    """

    def __init__(self, model: str = "llama3:8b", api_key: str | None = None) -> None:
        """Initialize an LLMAnalyzer with an LLM model."""
        self.__client = OpenAI(base_url="http://localhost:11434/v1")
        self.__model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
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
            response = self.__client.chat.completions.create(
                model=self.__model,
                messages=[
                    {"role": "system", "content": "You summarize git repository activity clearly and succinctly."},
                    {"role": "user", "content": commit_summaries},
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

        # Keep the prompt compact and management-friendly
        prompt = f"""
            You are an expert software assistant generating concise and professional Merge Request
            titles and descriptions from raw git diffs.
        
            Below is the code diff between two branches:
        
            {diff_text[:8000]}
        
            Instructions:
            1. Create a short, action-oriented title (≤ 10 words).
            2. Write 3-6 bullet points describing what changed and why, in non-technical terms.
            3. Avoid commit messages; infer meaning from code modifications.
        
            Respond exactly in this format:
        
            Title: <short title>
            Description:
            - <bullet 1>
            - <bullet 2>
            ...
            """

        try:
            response = self.__client.chat.completions.create(
                model=self.__model,
                messages=[
                    {"role": "system", "content": "You generate professional Merge Request titles and descriptions."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=500,
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
