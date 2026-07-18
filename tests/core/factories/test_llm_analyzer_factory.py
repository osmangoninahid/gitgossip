"""Unit tests for LLMAnalyzerFactory provider selection."""

from unittest.mock import patch

import pytest

from gitgossip.core.factories.llm_analyzer_factory import LLMAnalyzerFactory
from gitgossip.core.llm.llm_analyzer import LLMAnalyzer
from gitgossip.core.llm.mock_llm_analyzer import MockLLMAnalyzer


class TestLLMAnalyzerFactory:
    """Verify analyzer construction per provider."""

    def test_use_mock_returns_mock_analyzer(self) -> None:
        # given / when
        analyzer = LLMAnalyzerFactory().get_analyzer(use_mock=True)

        # then
        assert isinstance(analyzer, MockLLMAnalyzer)

    @patch("gitgossip.core.factories.llm_analyzer_factory.OpenAIChatClient")
    @patch("gitgossip.core.factories.llm_analyzer_factory.ConfigService")
    def test_local_provider_builds_openai_client(self, mock_config_cls, mock_openai_client) -> None:
        # given
        mock_config_cls.return_value.load.return_value = {
            "llm": {"provider": "local", "model": "qwen2.5-coder:1.5b", "base_url": "http://x/v1", "api_key": "local"},
            "paths": {"prompts": "/tmp/prompts"},
        }

        # when
        analyzer = LLMAnalyzerFactory().get_analyzer()

        # then
        assert isinstance(analyzer, LLMAnalyzer)
        mock_openai_client.assert_called_once_with(base_url="http://x/v1", model="qwen2.5-coder:1.5b", api_key="local")

    @patch("gitgossip.core.factories.llm_analyzer_factory.AgentCliChatClient")
    @patch("gitgossip.core.factories.llm_analyzer_factory.ConfigService")
    def test_agent_provider_builds_agent_client(self, mock_config_cls, mock_agent_client) -> None:
        # given
        mock_config_cls.return_value.load.return_value = {
            "llm": {"provider": "agent", "agent_cli": "claude", "model": "", "timeout": 60},
            "paths": {"prompts": "/tmp/prompts"},
        }

        # when
        analyzer = LLMAnalyzerFactory().get_analyzer()

        # then
        assert isinstance(analyzer, LLMAnalyzer)
        mock_agent_client.assert_called_once_with(agent_cli="claude", model=None, timeout=60)

    @patch("gitgossip.core.factories.llm_analyzer_factory.ConfigService")
    def test_agent_provider_missing_cli_raises(self, mock_config_cls) -> None:
        # given
        mock_config_cls.return_value.load.return_value = {
            "llm": {"provider": "agent"},
            "paths": {"prompts": "/tmp/prompts"},
        }

        # when / then
        with pytest.raises(ValueError, match="gitgossip init"):
            LLMAnalyzerFactory().get_analyzer()

    @patch("gitgossip.core.factories.llm_analyzer_factory.ConfigService")
    def test_cloud_provider_missing_fields_raises(self, mock_config_cls) -> None:
        # given
        mock_config_cls.return_value.load.return_value = {
            "llm": {"provider": "cloud", "model": "", "base_url": ""},
            "paths": {"prompts": "/tmp/prompts"},
        }

        # when / then
        with pytest.raises(ValueError, match="gitgossip init"):
            LLMAnalyzerFactory().get_analyzer()
