"""Errors raised by chat-client transports."""

from __future__ import annotations


class ChatClientError(Exception):
    """Raised when a chat client fails to produce a completion."""
