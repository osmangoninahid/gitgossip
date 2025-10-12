"""Utility for constructing prompts for LLM summarization."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

PromptType = Literal["chunk", "synthesis", "final"]


class PromptBuilder:
    """Loads and builds prompt templates (default or user-defined)."""

    def __init__(self, project_name: str = "GitGossip") -> None:
        """Initialize PromptBuilder."""
        self.project_name = project_name
        self.logger = logging.getLogger(self.__class__.__name__)

        # Default template dir inside the package
        self._default_dir = Path(__file__).parent / "prompts"

        # User custom prompts can live here
        self._user_dir = Path.home() / ".gitgossip" / "prompts"
        self._user_dir.mkdir(parents=True, exist_ok=True)

    def build(
        self,
        prompt_type: PromptType,
        content: str,
        context: str | None = None,
        metadata: str | None = None,
    ) -> str:
        """Return a ready-to-send prompt string."""
        template = self._load_template(prompt_type)
        prompt = (
            template.replace("{{project_name}}", self.project_name)
            .replace("{{content}}", self._truncate(content))
            .replace("{{context}}", context or "")
            .replace("{{metadata}}", metadata or "")
        )
        return prompt.strip()

    def _load_template(self, prompt_type: PromptType) -> str:
        """Load template from user dir or fallback to default."""
        user_file = self._user_dir / f"{prompt_type}.txt"
        default_file = self._default_dir / f"{prompt_type}.txt"

        if user_file.exists():
            self.logger.debug("Using user-defined template for %s", prompt_type)
            return user_file.read_text(encoding="utf-8")

        if default_file.exists():
            self.logger.debug("Using default template for %s", prompt_type)
            return default_file.read_text(encoding="utf-8")

        self.logger.warning("No template found for %s; using fallback.", prompt_type)
        return self._fallback_template(prompt_type)

    def _truncate(self, text: str, limit: int = 8000) -> str:
        """Trim large content to avoid context overflow."""
        if len(text) > limit:
            self.logger.debug("Truncating text from %d to %d chars", len(text), limit)
            return text[:limit] + "\n[TRUNCATED]"
        return text

    @staticmethod
    def _fallback_template(prompt_type: PromptType) -> str:
        """Simple fallback if neither user nor default templates exist."""
        if prompt_type == "chunk":
            return "You are summarizing a raw git diff for {{project_name}}:\n\n{{content}}"
        if prompt_type == "synthesis":
            return "You are merging partial summaries into one summary for {{project_name}}:\n\n{{content}}"
        return "You are generating a final Merge Request title and description for {{project_name}}:\n\n{{content}}"
