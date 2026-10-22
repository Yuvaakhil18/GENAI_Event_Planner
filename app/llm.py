"""LLM client abstraction. The planner depends on this protocol, not on a vendor SDK."""

from __future__ import annotations

from typing import Protocol

import httpx


class TextGenerator(Protocol):
    def generate(self, system: str, user: str) -> str: ...


class AnthropicTextGenerator:
    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"
    MAX_TOKENS = 800

    def __init__(self, api_key: str, model: str, timeout: float = 15.0) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def __repr__(self) -> str:
        return f"AnthropicTextGenerator(model={self._model!r})"

    def generate(self, system: str, user: str) -> str:
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
        blocks = response.json().get("content", [])
        return "".join(block.get("text", "") for block in blocks if block.get("type") == "text")
