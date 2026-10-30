"""Tests for app.llm — covers AnthropicTextGenerator init, repr, and generate."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import httpx
import pytest

from app.llm import AnthropicTextGenerator


def make_response(status_code: int, payload: Any = None) -> httpx.Response:
    """Build a concrete httpx.Response with a bound request for testing."""
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return httpx.Response(status_code, json=payload, request=req)


def test_init_stores_config() -> None:
    """Constructor stores api_key, model, and timeout."""
    gen = AnthropicTextGenerator(api_key="sk-test", model="claude-haiku-5-5", timeout=10.0)
    assert repr(gen) == "AnthropicTextGenerator(model='claude-haiku-5-5')"


def test_repr_shows_model() -> None:
    """Repr includes the model name."""
    gen = AnthropicTextGenerator("sk-x", "claude-test")
    assert "claude-test" in repr(gen)


def test_generate_sends_correct_request_and_returns_text() -> None:
    """generate() posts the right payload and concatenates text blocks."""
    gen = AnthropicTextGenerator("sk-key", "claude-test", timeout=5.0)
    response = make_response(
        200,
        {
            "content": [
                {"type": "text", "text": "Hello "},
                {"type": "text", "text": "World"},
            ]
        },
    )

    with patch.object(httpx, "post", return_value=response) as mock_post:
        result = gen.generate("Be helpful.", "Tell me something.")

    assert result == "Hello World"
    mock_post.assert_called_once()
    assert mock_post.call_args is not None
    _, kwargs = mock_post.call_args
    headers: dict[str, str] = kwargs.get("headers", {})
    json_data: dict[str, Any] = kwargs.get("json", {})
    assert headers.get("x-api-key") == "sk-key"
    assert json_data.get("model") == "claude-test"
    assert json_data.get("system") == "Be helpful."
    assert json_data.get("messages") == [{"role": "user", "content": "Tell me something."}]
    assert kwargs.get("timeout") == 5.0


def test_generate_skips_non_text_blocks() -> None:
    """Non-text content blocks (e.g. images) are filtered out."""
    gen = AnthropicTextGenerator("sk-key", "claude-test")
    response = make_response(
        200,
        {
            "content": [
                {"type": "image", "url": "http://example.com"},
                {"type": "text", "text": "Only text"},
            ]
        },
    )

    with patch.object(httpx, "post", return_value=response):
        result = gen.generate("sys", "usr")

    assert result == "Only text"


def test_generate_returns_empty_string_when_no_content() -> None:
    """An empty content array returns an empty string."""
    gen = AnthropicTextGenerator("sk-key", "claude-test")
    response = make_response(200, {"content": []})

    with patch.object(httpx, "post", return_value=response):
        result = gen.generate("sys", "usr")

    assert result == ""


def test_generate_returns_empty_string_when_payload_not_dict() -> None:
    """Non-dict JSON payload gracefully yields empty string."""
    gen = AnthropicTextGenerator("sk-key", "claude-test")
    response = make_response(200, ["not", "a", "dict"])

    with patch.object(httpx, "post", return_value=response):
        result = gen.generate("sys", "usr")

    assert result == ""


def test_generate_returns_empty_string_when_content_not_list() -> None:
    """When content field is not a list, return empty string."""
    gen = AnthropicTextGenerator("sk-key", "claude-test")
    response = make_response(200, {"content": "not-a-list"})

    with patch.object(httpx, "post", return_value=response):
        result = gen.generate("sys", "usr")

    assert result == ""


def test_generate_raises_on_http_error() -> None:
    """HTTP errors from the provider propagate as HTTPStatusError."""
    gen = AnthropicTextGenerator("sk-key", "claude-test")
    response = make_response(500, {"error": "Server Error"})

    with patch.object(httpx, "post", return_value=response), pytest.raises(
        httpx.HTTPStatusError
    ):
        gen.generate("sys", "usr")
