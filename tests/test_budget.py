"""Unit tests for budget allocation and per-guest warnings."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from app.budget import ALLOCATION, allocate, per_guest_warning
from app.models import EventRequest, EventType


@pytest.mark.parametrize("event_type", list(EventType))
def test_each_allocation_sums_to_one(event_type: EventType) -> None:
    """Every event type's category weights sum to exactly 1.0."""
    assert sum(ALLOCATION[event_type].values()) == pytest.approx(1.0)


@pytest.mark.parametrize("event_type", ["wedding", "birthday", "community"])
def test_lines_add_up_exactly_to_budget(
    make_request: Callable[..., EventRequest], event_type: str
) -> None:
    """Allocated amounts always sum back to the original budget."""
    req = make_request(event_type=event_type, budget=12345.67)
    lines = allocate(req)
    assert round(sum(line.amount for line in lines), 2) == 12345.67


def test_contingency_is_last_and_absorbs_drift(
    make_request: Callable[..., EventRequest],
) -> None:
    """The contingency line is last and absorbs rounding drift."""
    req = make_request(budget=100.01)
    lines = allocate(req)
    assert lines[-1].category == "contingency"
    assert round(sum(line.amount for line in lines), 2) == 100.01


def test_low_per_guest_budget_triggers_warning(
    make_request: Callable[..., EventRequest],
) -> None:
    """A per-guest spend below the floor produces a warning."""
    req = make_request(budget=1000, guest_count=100)  # $10 per guest for a wedding
    assert per_guest_warning(req) is not None


def test_adequate_budget_has_no_warning(
    make_request: Callable[..., EventRequest],
) -> None:
    """A healthy per-guest budget returns None."""
    req = make_request(budget=20000, guest_count=100)
    assert per_guest_warning(req) is None
