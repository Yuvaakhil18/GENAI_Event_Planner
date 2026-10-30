"""Dated task timeline. Compresses the schedule when lead time is short."""

from __future__ import annotations

from datetime import date, timedelta

from .exceptions import PastDateError
from .models import EventRequest, EventType, TimelineTask

# (days before the event, task, category). The first row is the longest lead time.
MILESTONES: dict[EventType, list[tuple[int, str, str]]] = {
    EventType.WEDDING: [
        (365, "Book venue and officiant", "venue"),
        (300, "Hire photographer and videographer", "photography"),
        (270, "Book caterer and schedule a tasting", "catering"),
        (240, "Reserve band or DJ", "music"),
        (180, "Order invitations and save-the-dates", "stationery"),
        (120, "Start attire fittings", "attire"),
        (60, "Send formal invitations", "stationery"),
        (30, "Confirm final headcount with caterer and venue", "catering"),
        (14, "Finalize seating chart and day-of schedule", "planning"),
        (1, "Confirm vendor arrival times", "planning"),
        (0, "Event day", "planning"),
    ],
    EventType.BIRTHDAY: [
        (60, "Set date, guest list and budget", "planning"),
        (45, "Book venue or entertainment", "venue"),
        (30, "Send invitations", "stationery"),
        (14, "Order cake and food", "food"),
        (7, "Buy decorations and favors", "decor"),
        (2, "Confirm RSVPs and headcount", "planning"),
        (0, "Event day", "planning"),
    ],
    EventType.COMMUNITY: [
        (90, "Confirm organizing committee and goals", "planning"),
        (75, "Apply for permits and insurance", "permits"),
        (60, "Book venue and equipment", "venue"),
        (45, "Recruit volunteers", "volunteers"),
        (30, "Launch promotion and sign-ups", "marketing"),
        (14, "Order supplies and food", "food"),
        (3, "Confirm volunteer shifts", "volunteers"),
        (0, "Event day", "planning"),
    ],
}

RUSH_DAYS = 14


def build_timeline(req: EventRequest, today: date) -> tuple[list[TimelineTask], list[str]]:
    """Build a dated task timeline, compressing when lead time is short.

    Args:
        req: Validated event request.
        today: Current date for calculating lead time.

    Returns:
        A tuple of (sorted tasks, advisory notes about compressed schedule).

    Raises:
        ValueError: If the event date is in the past.
    """
    days_left = (req.event_date - today).days
    if days_left < 0:
        raise PastDateError("The event date is in the past.")

    milestones = MILESTONES[req.event_type]
    longest_lead = milestones[0][0]
    scale = min(1.0, days_left / longest_lead)

    notes: list[str] = []
    if scale < 1.0:
        notes.append("Lead time is shorter than typical, so the schedule is compressed.")
    if days_left < RUSH_DAYS:
        notes.append("Less than two weeks away: focus on urgent bookings first.")

    tasks = []
    for offset, title, category in milestones:
        # Never schedule a task before today, even after compression.
        due = max(today, req.event_date - timedelta(days=round(offset * scale)))
        tasks.append(TimelineTask(due=due, title=title, category=category))

    tasks.sort(key=lambda task: (task.due, task.title))
    return tasks, notes
