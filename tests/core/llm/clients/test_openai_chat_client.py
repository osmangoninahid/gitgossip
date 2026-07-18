"""Unit tests for OpenAIChatClient."""

from unittest.mock import MagicMock, patch

import pytest
from openai import APIConnectionError

from gitgossip.core.llm.clients.openai_chat_client import OpenAIChatClient
from gitgossip.core.llm.errors import ChatClientError


class TestOpenAIChatClient:
    """Verify the OpenAI-backed chat client."""

    @patch("gitgossip.core.llm.clients.openai_chat_client.OpenAI")
    def test_complete_returns_stripped_content(self, mock_openai_cls) -> None:
        # given
        mock_client = mock_openai_cls.return_value
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "  hello world  "
        mock_client.chat.completions.create.return_value = mock_response
        client = OpenAIChatClient(base_url="http://localhost:11434/v1", model="qwen2.5-coder:1.5b", api_key="local")

        # when
        result = client.complete(system="sys", user="usr", temperature=0.3, max_tokens=100)

        # then
        assert result == "hello world"
        mock_client.chat.completions.create.assert_called_once_with(
            model="qwen2.5-coder:1.5b",
            messages=[{"role": "system", "content": "sys"}, {"role": "user", "content": "usr"}],
            temperature=0.3,
            max_tokens=100,
        )

    @patch("gitgossip.core.llm.clients.openai_chat_client.OpenAI")
    def test_complete_empty_content_raises(self, mock_openai_cls) -> None:
        # given
        mock_client = mock_openai_cls.return_value
        mock_response = MagicMock()
        mock_response.choices[0].message.content = None
        mock_client.chat.completions.create.return_value = mock_response
        client = OpenAIChatClient(base_url="http://x/v1", model="m")

        # when / then
        with pytest.raises(ChatClientError, match="Empty response"):
            client.complete(system="s", user="u", temperature=0.3, max_tokens=100)

    @patch("gitgossip.core.llm.clients.openai_chat_client.OpenAI")
    def test_complete_api_error_raises_chat_client_error(self, mock_openai_cls) -> None:
        # given
        mock_client = mock_openai_cls.return_value
        mock_client.chat.completions.create.side_effect = APIConnectionError(request=MagicMock())
        client = OpenAIChatClient(base_url="http://x/v1", model="m")

        # when / then
        with pytest.raises(ChatClientError):
            client.complete(system="s", user="u", temperature=0.3, max_tokens=100)
