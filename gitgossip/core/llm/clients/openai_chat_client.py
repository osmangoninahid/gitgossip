"""Chat client backed by any OpenAI-compatible HTTP endpoint (Ollama, OpenAI, Groq, ...)."""

from __future__ import annotations

import logging

from openai import APIConnectionError, APIError, OpenAI, RateLimitError

from gitgossip.core.interfaces.chat_client import IChatClient
from gitgossip.core.llm.errors import ChatClientError


class OpenAIChatClient(IChatClient):
    """Sends chat completions through the OpenAI SDK."""

    def __init__(self, base_url: str, model: str, api_key: str | None = None) -> None:
        """Initialize the client with an endpoint, model, and optional API key."""
        self.__client = OpenAI(base_url=base_url, api_key=api_key)
        self.__model = model
        self.__logger = logging.getLogger(self.__class__.__name__)

    def complete(self, system: str, user: str, temperature: float, max_tokens: int) -> str:
        """Return the completion text for the given prompts.

        Raises:
            ChatClientError: On API/network failure or empty model output.
        """
        try:
            response = self.__client.chat.completions.create(
                model=self.__model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except (APIError, APIConnectionError, RateLimitError) as exc:
            self.__logger.error("LLM API request failed: %s", exc)
            raise ChatClientError(str(exc)) from exc
        except OSError as exc:
            self.__logger.error("System or network issue during LLM call: %s", exc)
            raise ChatClientError(str(exc)) from exc

        content = response.choices[0].message.content
        if not content:
            raise ChatClientError("Empty response from model")
        return content.strip()
