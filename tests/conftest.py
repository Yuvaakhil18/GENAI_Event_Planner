from datetime import date

import pytest

from app.models import EventRequest


@pytest.fixture
def make_request():
    """Factory for valid EventRequest objects with optional overrides."""

    def _make(**overrides):
        data = {
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
def _clear_idea_cache():
    """Prevent LLM response cache from leaking between tests."""
    from app.ideas import _idea_cache

    _idea_cache.clear()
