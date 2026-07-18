"""Unit tests for the prompts scaffolding command."""

from pathlib import Path
from unittest.mock import patch

from gitgossip.commands.prompts import prompts_init_cmd


class TestPromptsInit:
    """Verify template scaffolding into the configured prompts dir."""

    @patch("gitgossip.commands.prompts.ConfigService")
    def test_copies_all_default_templates(self, mock_config_cls, tmp_path: Path) -> None:
        # given
        target = tmp_path / "prompts"
        mock_config_cls.return_value.load.return_value = {"paths": {"prompts": str(target)}}

        # when
        prompts_init_cmd()

        # then
        names = sorted(p.name for p in target.iterdir())
        assert names == ["chunk.txt", "commit.txt", "final.txt", "synthesis.txt"]

    @patch("gitgossip.commands.prompts.ConfigService")
    def test_does_not_overwrite_existing_files(self, mock_config_cls, tmp_path: Path) -> None:
        # given
        target = tmp_path / "prompts"
        target.mkdir()
        (target / "chunk.txt").write_text("MY CUSTOM", encoding="utf-8")
        mock_config_cls.return_value.load.return_value = {"paths": {"prompts": str(target)}}

        # when
        prompts_init_cmd()

        # then
        assert (target / "chunk.txt").read_text(encoding="utf-8") == "MY CUSTOM"
        assert (target / "commit.txt").exists()
