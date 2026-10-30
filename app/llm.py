"""LLM client abstraction. The planner depends on this protocol, not on a vendor SDK."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import httpx


@runtime_checkable
class TextGenerator(Protocol):
    """Abstract text-generation interface used by the planner."""

    def generate(self, system: str, user: str) -> str:
        """Return the model's text reply given a system and user prompt."""
        ...


class AnthropicTextGenerator:
    """Calls the Anthropic Messages API to generate text."""

    API_URL: str = "https://api.anthropic.com/v1/messages"
    API_VERSION: str = "2023-06-01"
    MAX_TOKENS: int = 800

    def __init__(self, api_key: str, model: str, timeout: float = 15.0) -> None:
        """Initialize the Anthropic client wrapper with credentials and settings."""
        self._api_key: str = api_key
        self._model: str = model
        self._timeout: float = timeout

    def __repr__(self) -> str:
        """Return developer-facing string representation without leaking secrets."""
        return f"AnthropicTextGenerator(model={self._model!r})"

    def generate(self, system: str, user: str) -> str:
        """Send a messages-API request and return the concatenated text blocks."""
        response = httpx.post(
            self.API_URL,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": self.API_VERSION,
                "content-type": "application/json",
            },
            json={
                "model": self._model,
                "max_tokens": self.MAX_TOKENS,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        data: Any = response.json()
        if not isinstance(data, dict):
            return ""
        blocks: Any = data.get("content", [])
        if not isinstance(blocks, list):
            return ""
        return "".join(
            str(block.get("text", ""))
            for block in blocks
            if isinstance(block, dict) and block.get("type") == "text"
        )
