from datetime import date, timedelta

import pytest

from app.timeline import build_timeline

TODAY = date(2026, 1, 1)


def test_full_lead_time_is_not_compressed(make_request):
    event = TODAY + timedelta(days=365)
    tasks, notes = build_timeline(make_request(event_date=event), TODAY)
    assert notes == []
    assert min(task.due for task in tasks) == TODAY
    assert max(task.due for task in tasks) == event


def test_short_lead_time_compresses_schedule(make_request):
    event = TODAY + timedelta(days=60)
    tasks, notes = build_timeline(make_request(event_date=event), TODAY)
    assert any("compressed" in note for note in notes)
    assert all(TODAY <= task.due <= event for task in tasks)
    assert max(task.due for task in tasks) == event


def test_under_two_weeks_adds_rush_note(make_request):
    event = TODAY + timedelta(days=10)
    _, notes = build_timeline(make_request(event_type="birthday", event_date=event), TODAY)
    assert any("two weeks" in note for note in notes)


def test_event_today_puts_every_task_today(make_request):
    tasks, _ = build_timeline(make_request(event_type="birthday", event_date=TODAY), TODAY)
    assert all(task.due == TODAY for task in tasks)


def test_past_event_is_rejected(make_request):
    with pytest.raises(ValueError):
        build_timeline(make_request(event_date=TODAY - timedelta(days=1)), TODAY)


def test_tasks_are_sorted_by_due_date(make_request):
    tasks, _ = build_timeline(make_request(event_date=TODAY + timedelta(days=200)), TODAY)
    dues = [task.due for task in tasks]
    assert dues == sorted(dues)
