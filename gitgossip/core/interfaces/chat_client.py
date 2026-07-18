"""Interface defining the contract for chat-completion transports."""

from __future__ import annotations

from abc import ABC, abstractmethod


class IChatClient(ABC):
    """Defines a minimal chat-completion contract independent of transport (HTTP SDK or subprocess)."""

    @abstractmethod
    def complete(self, system: str, user: str, temperature: float, max_tokens: int) -> str:
        """Return the assistant's text for a system+user prompt pair.

        Raises:
            ChatClientError: If the transport fails or returns an empty response.
        """
        raise NotImplementedError
