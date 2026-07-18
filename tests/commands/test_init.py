"""Unit tests for the init command's agent-provider flow."""

from unittest.mock import patch

from gitgossip.commands.init import _configure_agent_llm, _select_provider


class TestSelectProvider:
    """Verify provider selection accepts the new agent option."""

    @patch("gitgossip.commands.init.Prompt.ask", return_value="agent")
    def test_agent_input_returns_agent(self, _mock_ask) -> None:
        # when / then
        assert _select_provider("local") == "agent"

    @patch("gitgossip.commands.init.Prompt.ask", return_value="nonsense")
    def test_invalid_input_defaults_to_local(self, _mock_ask) -> None:
        # when / then
        assert _select_provider("local") == "local"


class TestConfigureAgentLlm:
    """Verify agent CLI detection and config writing."""

    @patch("gitgossip.commands.init.Prompt.ask", side_effect=["claude", ""])
    @patch(
        "gitgossip.commands.init.shutil.which",
        side_effect=lambda name: "/usr/local/bin/claude" if name == "claude" else None,
    )
    def test_detected_claude_is_configured(self, _mock_which, _mock_ask) -> None:
        # given
        cfg = {"llm": {}}

        # when
        _configure_agent_llm(cfg)

        # then
        assert cfg["llm"]["agent_cli"] == "claude"
        assert cfg["llm"]["model"] == ""

    @patch("gitgossip.commands.init.Prompt.ask", side_effect=["codex", "gpt-5"])
    @patch("gitgossip.commands.init.shutil.which", return_value=None)
    def test_no_cli_detected_still_configurable(self, _mock_which, _mock_ask) -> None:
        # given
        cfg = {"llm": {}}

        # when
        _configure_agent_llm(cfg)

        # then
        assert cfg["llm"]["agent_cli"] == "codex"
        assert cfg["llm"]["model"] == "gpt-5"
