"""Chat client that shells out to an installed coding-agent CLI (claude or codex)."""

from __future__ import annotations

import logging
import subprocess

from gitgossip.core.interfaces.chat_client import IChatClient
from gitgossip.core.llm.errors import ChatClientError

SUPPORTED_AGENT_CLIS = ("claude", "codex")

_INSTALL_HINTS = {
    "claude": "Install Claude Code: npm install -g @anthropic-ai/claude-code (or brew install claude-code)",
    "codex": "Install Codex CLI: npm install -g @openai/codex",
}


class AgentCliChatClient(IChatClient):
    """Runs one-shot completions through a locally installed agent CLI.

    Agent CLIs take a single prompt argument, so the system and user prompts
    are concatenated. ``temperature`` and ``max_tokens`` are accepted for
    interface compatibility but ignored — the CLI controls its own sampling.
    """

    def __init__(self, agent_cli: str, model: str | None = None, timeout: int = 120) -> None:
        """Initialize with the CLI name ('claude' or 'codex'), optional model override, and timeout in seconds."""
        if agent_cli not in SUPPORTED_AGENT_CLIS:
            raise ValueError(f"Unsupported agent CLI '{agent_cli}'. Supported: {', '.join(SUPPORTED_AGENT_CLIS)}")
        self.__agent_cli = agent_cli
        self.__model = model
        self.__timeout = timeout
        self.__logger = logging.getLogger(self.__class__.__name__)

    def complete(self, system: str, user: str, temperature: float, max_tokens: int) -> str:
        """Return the completion text produced by the agent CLI.

        Raises:
            ChatClientError: If the binary is missing, times out, exits non-zero, or prints nothing.
        """
        command = self.__build_command(f"{system}\n\n{user}")
        self.__logger.debug("Running agent CLI: %s", command[0])
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.__timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ChatClientError(
                f"'{self.__agent_cli}' CLI not found on PATH. {_INSTALL_HINTS[self.__agent_cli]}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ChatClientError(
                f"'{self.__agent_cli}' timed out after {self.__timeout}s. "
                "Try a smaller diff or increase llm.timeout in ~/.gitgossip/config.yaml."
            ) from exc

        if result.returncode != 0:
            stderr_excerpt = (result.stderr or "").strip()[:300]
            raise ChatClientError(f"'{self.__agent_cli}' exited with code {result.returncode}: {stderr_excerpt}")

        output = (result.stdout or "").strip()
        if not output:
            raise ChatClientError(f"Empty response from '{self.__agent_cli}' CLI")
        return output

    def __build_command(self, prompt: str) -> list[str]:
        """Build the subprocess argv for the configured CLI."""
        if self.__agent_cli == "claude":
            command = ["claude", "-p", prompt]
            if self.__model:
                command += ["--model", self.__model]
            return command
        command = ["codex", "exec", prompt]
        if self.__model:
            command += ["-m", self.__model]
        return command
