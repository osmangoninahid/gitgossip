"""Factory responsible for creating configured LLM analyzers for GitGossip."""

from __future__ import annotations

import logging
from typing import Any

from gitgossip.config.config_service import ConfigService
from gitgossip.core.interfaces.llm_analyzer import ILLMAnalyzer
from gitgossip.core.llm.llm_analyzer import LLMAnalyzer
from gitgossip.core.llm.mock_llm_analyzer import MockLLMAnalyzer


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
        model = llm_cfg.get("model")
        base_url = llm_cfg.get("base_url")
        api_key = llm_cfg.get("api_key")

        assert isinstance(provider, str)
        assert isinstance(model, str)
        assert isinstance(base_url, str)

        missing_fields = [
            k
            for k, v in {
                "provider": provider,
                "model": model,
                "base_url": base_url,
            }.items()
            if not v
        ]

        if missing_fields:
            msg = (
                f"Missing required LLM configuration: {', '.join(missing_fields)}. "
                "Please run 'gitgossip init' again to configure your environment."
            )
            self.__logger.error(msg)
            raise ValueError(msg)

        self.__logger.info(
            "Initializing LLMAnalyzer: provider=%s, model=%s, base_url=%s",
            provider,
            model,
            base_url,
        )

        return LLMAnalyzer(model=model, api_key=api_key, base_url=base_url)
