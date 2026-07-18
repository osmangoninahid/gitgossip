"""Unit tests for AgentCliChatClient."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from gitgossip.core.llm.clients.agent_cli_chat_client import AgentCliChatClient
from gitgossip.core.llm.errors import ChatClientError


def _completed(stdout: str = "ok", returncode: int = 0, stderr: str = "") -> MagicMock:
    proc = MagicMock()
    proc.stdout = stdout
    proc.stderr = stderr
    proc.returncode = returncode
    return proc


class TestAgentCliChatClient:
    """Verify the subprocess-backed agent CLI chat client."""

    def test_unsupported_cli_raises_value_error(self) -> None:
        # when / then
        with pytest.raises(ValueError, match="Unsupported agent CLI"):
            AgentCliChatClient(agent_cli="gemini")

    @patch("gitgossip.core.llm.clients.agent_cli_chat_client.subprocess.run")
    def test_claude_command_and_prompt_concatenation(self, mock_run) -> None:
        # given
        mock_run.return_value = _completed(stdout="summary text\n")
        client = AgentCliChatClient(agent_cli="claude")

        # when
        result = client.complete(system="You summarize.", user="diff here", temperature=0.3, max_tokens=100)

        # then
        assert result == "summary text"
        cmd = mock_run.call_args.args[0]
        assert cmd[:2] == ["claude", "-p"]
        assert "You summarize." in cmd[2]
        assert "diff here" in cmd[2]

    @patch("gitgossip.core.llm.clients.agent_cli_chat_client.subprocess.run")
    def test_claude_with_model_flag(self, mock_run) -> None:
        # given
        mock_run.return_value = _completed()
        client = AgentCliChatClient(agent_cli="claude", model="haiku")

        # when
        client.complete(system="s", user="u", temperature=0.3, max_tokens=100)

        # then
        cmd = mock_run.call_args.args[0]
        assert cmd[-2:] == ["--model", "haiku"]

    @patch("gitgossip.core.llm.clients.agent_cli_chat_client.subprocess.run")
    def test_codex_command_shape(self, mock_run) -> None:
        # given
        mock_run.return_value = _completed()
        client = AgentCliChatClient(agent_cli="codex", model="gpt-5")

        # when
        client.complete(system="s", user="u", temperature=0.3, max_tokens=100)

        # then
        cmd = mock_run.call_args.args[0]
        assert cmd[:2] == ["codex", "exec"]
        assert cmd[-2:] == ["-m", "gpt-5"]

    @patch("gitgossip.core.llm.clients.agent_cli_chat_client.subprocess.run")
    def test_missing_binary_raises_with_install_hint(self, mock_run) -> None:
        # given
        mock_run.side_effect = FileNotFoundError()
        client = AgentCliChatClient(agent_cli="claude")

        # when / then
        with pytest.raises(ChatClientError, match="not found"):
            client.complete(system="s", user="u", temperature=0.3, max_tokens=100)

    @patch("gitgossip.core.llm.clients.agent_cli_chat_client.subprocess.run")
    def test_timeout_raises(self, mock_run) -> None:
        # given
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=120)
        client = AgentCliChatClient(agent_cli="claude")

        # when / then
        with pytest.raises(ChatClientError, match="timed out"):
            client.complete(system="s", user="u", temperature=0.3, max_tokens=100)

    @patch("gitgossip.core.llm.clients.agent_cli_chat_client.subprocess.run")
    def test_nonzero_exit_raises_with_stderr(self, mock_run) -> None:
        # given
        mock_run.return_value = _completed(stdout="", returncode=1, stderr="not logged in")
        client = AgentCliChatClient(agent_cli="claude")

        # when / then
        with pytest.raises(ChatClientError, match="not logged in"):
            client.complete(system="s", user="u", temperature=0.3, max_tokens=100)

    @patch("gitgossip.core.llm.clients.agent_cli_chat_client.subprocess.run")
    def test_empty_output_raises(self, mock_run) -> None:
        # given
        mock_run.return_value = _completed(stdout="   ")
        client = AgentCliChatClient(agent_cli="claude")

        # when / then
        with pytest.raises(ChatClientError, match="Empty response"):
            client.complete(system="s", user="u", temperature=0.3, max_tokens=100)
