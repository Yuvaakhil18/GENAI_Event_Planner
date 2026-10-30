"""Unit tests for the planner orchestration and context warnings."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta

import pytest

from app.models import EventRequest
from app.planner import build_plan, context_warnings

TODAY = date(2026, 10, 22)


def test_outdoor_venue_warns_about_weather(
    make_request: Callable[..., EventRequest],
) -> None:
    """Outdoor venue triggers a weather-related warning."""
    req = make_request(venue="outdoor")
    warnings = context_warnings(req)
    assert any("weather" in w.lower() for w in warnings)


def test_indoor_venue_no_weather_warning(
    make_request: Callable[..., EventRequest],
) -> None:
    """Indoor venue produces no weather warning."""
    req = make_request(venue="indoor", budget=20000, guest_count=100)
    warnings = context_warnings(req)
    assert not any("weather" in w.lower() for w in warnings)


def test_large_wedding_warns_about_capacity(
    make_request: Callable[..., EventRequest],
) -> None:
    """A wedding with >150 guests triggers a capacity/seating warning."""
    req = make_request(event_type="wedding", guest_count=200)
    warnings = context_warnings(req)
    assert any("capacity" in w.lower() or "seating" in w.lower() for w in warnings)


def test_small_wedding_no_capacity_warning(
    make_request: Callable[..., EventRequest],
) -> None:
    """A wedding at or below 150 guests has no capacity warning."""
    req = make_request(event_type="wedding", guest_count=100)
    warnings = context_warnings(req)
    assert not any("capacity" in w.lower() or "seating" in w.lower() for w in warnings)


def test_large_community_event_warns_about_permits(
    make_request: Callable[..., EventRequest],
) -> None:
    """A community event with >=200 guests warns about permits."""
    req = make_request(event_type="community", guest_count=200)
    warnings = context_warnings(req)
    assert any("permit" in w.lower() for w in warnings)


def test_small_community_event_no_permit_warning(
    make_request: Callable[..., EventRequest],
) -> None:
    """A small community event has no permit warning."""
    req = make_request(event_type="community", guest_count=50, budget=5000)
    warnings = context_warnings(req)
    assert not any("permit" in w.lower() for w in warnings)


def test_low_budget_triggers_warning(
    make_request: Callable[..., EventRequest],
) -> None:
    """A per-guest budget below the floor triggers a budget warning."""
    req = make_request(budget=500, guest_count=100)
    warnings = context_warnings(req)
    assert any("budget" in w.lower() or "per guest" in w.lower() for w in warnings)


def test_adequate_budget_no_warning(
    make_request: Callable[..., EventRequest],
) -> None:
    """An adequate budget produces no per-guest warning."""
    req = make_request(budget=20000, guest_count=100, venue="indoor")
    warnings = context_warnings(req)
    assert not any("per guest" in w.lower() for w in warnings)


def test_build_plan_assembles_all_sections(
    make_request: Callable[..., EventRequest],
) -> None:
    """build_plan returns a Plan with all sections populated."""
    req = make_request(event_date=TODAY + timedelta(days=180))
    plan = build_plan(req, today=TODAY)
    assert plan.event_name == req.name
    assert plan.event_type == req.event_type
    assert plan.budget_total == req.budget
    assert len(plan.budget) > 0
    assert len(plan.timeline) > 0
    assert len(plan.vendors) > 0
    assert len(plan.ideas) > 0
    assert plan.ideas_source in ("ai", "template")


def test_build_plan_rejects_far_future(
    make_request: Callable[..., EventRequest],
) -> None:
    """An event date more than 5 years away raises ValueError."""
    req = make_request(event_date=TODAY + timedelta(days=365 * 6))
    with pytest.raises(ValueError, match="within"):
        build_plan(req, today=TODAY)


def test_build_plan_includes_timeline_warnings_for_short_lead(
    make_request: Callable[..., EventRequest],
) -> None:
    """Short lead time adds a rush-schedule warning to the plan."""
    req = make_request(event_date=TODAY + timedelta(days=10), event_type="birthday")
    plan = build_plan(req, today=TODAY)
    assert any("two weeks" in w.lower() for w in plan.warnings)


def test_multiple_warnings_can_combine(
    make_request: Callable[..., EventRequest],
) -> None:
    """Low budget + outdoor + large wedding produces multiple warnings."""
    req = make_request(
        event_type="wedding", guest_count=200, venue="outdoor", budget=1000
    )
    warnings = context_warnings(req)
    assert len(warnings) >= 3  # weather + capacity + low budget
