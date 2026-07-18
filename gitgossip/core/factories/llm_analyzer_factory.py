"""Factory responsible for creating configured LLM analyzers for GitGossip."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from gitgossip.config.config_service import ConfigService
from gitgossip.core.interfaces.chat_client import IChatClient
from gitgossip.core.interfaces.llm_analyzer import ILLMAnalyzer
from gitgossip.core.llm.clients.agent_cli_chat_client import AgentCliChatClient
from gitgossip.core.llm.clients.openai_chat_client import OpenAIChatClient
from gitgossip.core.llm.llm_analyzer import LLMAnalyzer
from gitgossip.core.llm.mock_llm_analyzer import MockLLMAnalyzer
from gitgossip.core.llm.prompt_builder import PromptBuilder


class LLMAnalyzerFactory:
    """Factory for constructing LLM analyzers based purely on user configuration."""

    def __init__(self) -> None:
        """Initialize an LLMAnalyzerFactory."""
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__config_service = ConfigService()

    def get_analyzer(self, use_mock: bool = False) -> ILLMAnalyzer:
        """Return a configured analyzer — Mock or real — depending on user settings."""
        if use_mock:
            self.__logger.debug("Using MockLLMAnalyzer (explicit request).")
            return MockLLMAnalyzer()

        cfg = self.__config_service.load()
        llm_cfg: dict[str, Any] = cfg.get("llm", {})
        provider = llm_cfg.get("provider")

        chat_client = (
            self.__build_agent_client(llm_cfg) if provider == "agent" else self.__build_openai_client(llm_cfg)
        )

        prompts_dir = cfg.get("paths", {}).get("prompts")
        prompt_builder = PromptBuilder(user_dir=Path(prompts_dir) if prompts_dir else None)
        return LLMAnalyzer(chat_client=chat_client, prompt_builder=prompt_builder)

    def __build_agent_client(self, llm_cfg: dict[str, Any]) -> IChatClient:
        """Build the subprocess-backed client for provider=agent."""
        agent_cli = llm_cfg.get("agent_cli")
        if agent_cli not in ("claude", "codex"):
            msg = (
                "Missing or invalid 'agent_cli' for the agent provider (expected 'claude' or 'codex'). "
                "Please run 'gitgossip init' again to configure your environment."
            )
            self.__logger.error(msg)
            raise ValueError(msg)
        self.__logger.debug("Initializing AgentCliChatClient: agent_cli=%s", agent_cli)
        return AgentCliChatClient(
            agent_cli=agent_cli,
            model=llm_cfg.get("model") or None,
            timeout=int(llm_cfg.get("timeout") or 120),
        )

    def __build_openai_client(self, llm_cfg: dict[str, Any]) -> IChatClient:
        """Build the HTTP client for provider=local/cloud."""
        model = llm_cfg.get("model")
        base_url = llm_cfg.get("base_url")
        missing_fields = [k for k, v in {"model": model, "base_url": base_url}.items() if not v]
        if missing_fields:
            msg = (
                f"Missing required LLM configuration: {', '.join(missing_fields)}. "
                "Please run 'gitgossip init' again to configure your environment."
            )
            self.__logger.error(msg)
            raise ValueError(msg)
        self.__logger.debug("Initializing OpenAIChatClient: model=%s, base_url=%s", model, base_url)
        return OpenAIChatClient(base_url=base_url, model=model, api_key=llm_cfg.get("api_key"))
