"""Unit tests for timeline building and schedule compression."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta

import pytest

from app.models import EventRequest
from app.timeline import build_timeline

TODAY = date(2026, 1, 1)


def test_full_lead_time_is_not_compressed(
    make_request: Callable[..., EventRequest],
) -> None:
    """A full-year lead time produces an uncompressed schedule."""
    event = TODAY + timedelta(days=365)
    tasks, notes = build_timeline(make_request(event_date=event), TODAY)
    assert notes == []
    assert min(task.due for task in tasks) == TODAY
    assert max(task.due for task in tasks) == event


def test_short_lead_time_compresses_schedule(
    make_request: Callable[..., EventRequest],
) -> None:
    """A 60-day lead time compresses milestone dates."""
    event = TODAY + timedelta(days=60)
    tasks, notes = build_timeline(make_request(event_date=event), TODAY)
    assert any("compressed" in note for note in notes)
    assert all(TODAY <= task.due <= event for task in tasks)
    assert max(task.due for task in tasks) == event


def test_under_two_weeks_adds_rush_note(
    make_request: Callable[..., EventRequest],
) -> None:
    """Less than 14 days triggers a rush-schedule advisory."""
    event = TODAY + timedelta(days=10)
    _, notes = build_timeline(make_request(event_type="birthday", event_date=event), TODAY)
    assert any("two weeks" in note for note in notes)


def test_event_today_puts_every_task_today(
    make_request: Callable[..., EventRequest],
) -> None:
    """An event on today's date collapses all tasks to today."""
    tasks, _ = build_timeline(make_request(event_type="birthday", event_date=TODAY), TODAY)
    assert all(task.due == TODAY for task in tasks)


def test_past_event_is_rejected(
    make_request: Callable[..., EventRequest],
) -> None:
    """A past event date raises ValueError."""
    with pytest.raises(ValueError):
        build_timeline(make_request(event_date=TODAY - timedelta(days=1)), TODAY)


def test_tasks_are_sorted_by_due_date(
    make_request: Callable[..., EventRequest],
) -> None:
    """Timeline tasks are returned sorted by due date."""
    tasks, _ = build_timeline(make_request(event_date=TODAY + timedelta(days=200)), TODAY)
    dues = [task.due for task in tasks]
    assert dues == sorted(dues)
