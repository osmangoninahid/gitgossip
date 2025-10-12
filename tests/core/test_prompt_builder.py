"""Unit tests for PromptBuilder using only its public interface."""

import os
from pathlib import Path

import pytest

from gitgossip.core.llm.prompt_builder import PromptBuilder


class TestPromptBuilder:
    """Validate PromptBuilder public behavior end-to-end."""

    @pytest.fixture()
    def temp_prompts_dir(self, tmp_path: Path) -> Path:
        """Create a temporary prompts directory."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        return prompts_dir

    def test_build_uses_default_templates(self) -> None:
        """Should build a prompt successfully with default bundled templates."""
        # given
        builder = PromptBuilder(project_name="GitGossip")

        # when
        prompt = builder.build("chunk", content="example diff")

        # then
        assert "example diff" in prompt
        assert "GitGossip" in prompt

    def test_user_defined_template_precedence(self, temp_prompts_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should prefer user-defined prompt over default template."""
        # given
        (temp_prompts_dir / "chunk.txt").write_text("USER TEMPLATE {{project_name}} :: {{content}}")

        # Simulate ~/.gitgossip/prompts override without touching protected attrs
        home_override = temp_prompts_dir.parent
        gitgossip_dir = home_override / ".gitgossip" / "prompts"
        gitgossip_dir.mkdir(parents=True)
        (gitgossip_dir / "chunk.txt").write_text("USER TEMPLATE {{project_name}} :: {{content}}")

        monkeypatch.setenv("HOME", str(home_override))

        builder = PromptBuilder(project_name="CustomProj")

        # when
        prompt = builder.build("chunk", content="diff content")

        # then
        assert "USER TEMPLATE" in prompt
        assert "CustomProj" in prompt
        assert "diff content" in prompt

    def test_placeholder_and_metadata_replacement(self) -> None:
        """Should replace all placeholders correctly."""
        # given
        builder = PromptBuilder(project_name="GitGossip")

        # when
        prompt = builder.build(
            "chunk",
            content="diff body",
            context="context info",
            metadata="meta info",
        )

        # then
        assert "diff body" in prompt
        assert "meta info" in prompt
        assert "GitGossip" in prompt

    def test_truncation_for_large_input(self) -> None:
        """Should truncate long text safely."""
        # given
        builder = PromptBuilder()
        big_text = "x" * 9000

        # when
        prompt = builder.build("chunk", content=big_text)

        # then
        assert "[TRUNCATED]" in prompt
        assert len(prompt) < 9000

    def test_fallback_template_when_missing_files(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Should gracefully fallback to default string when templates missing."""
        # given
        fake_home = tmp_path / "no_templates_home"
        fake_home.mkdir(parents=True)
        monkeypatch.setenv("HOME", str(fake_home))

        builder = PromptBuilder(project_name="GitGossip")
        # Delete internal template dirs so only fallback applies
        os.environ["GITGOSSIP_DISABLE_DEFAULTS"] = "1"

        # when
        result = builder.build("chunk", content="some diff")

        # then
        assert "git diff" in result.lower() or "summarizing" in result.lower()
