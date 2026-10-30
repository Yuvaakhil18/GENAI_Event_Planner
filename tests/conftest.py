"""Shared test fixtures for the event planner test suite."""

from __future__ import annotations

from collections.abc import Callable, Generator
from datetime import date
from typing import Any

import pytest

from app.models import EventRequest


@pytest.fixture
def make_request() -> Callable[..., EventRequest]:
    """Factory fixture for valid EventRequest objects with optional overrides."""

    def _make(**overrides: Any) -> EventRequest:
        data: dict[str, Any] = {
            "event_type": "wedding",
            "name": "Test event",
            "event_date": date(2027, 6, 1),
            "guest_count": 100,
            "budget": 20000,
            "currency": "USD",
            "venue": "indoor",
            "notes": "",
        }
        data.update(overrides)
        return EventRequest(**data)

    return _make


@pytest.fixture(autouse=True)
def _clear_idea_cache() -> Generator[None, None, None]:
    """Prevent LLM response cache from leaking between tests."""
    from app.ideas import _idea_cache

    _idea_cache.clear()
    yield
    _idea_cache.clear()
