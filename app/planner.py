"""Orchestrates budget, timeline, vendors, warnings and ideas into one plan.

The decision logic lives here: each rule looks at the request context and
decides what the user should be warned about.
"""

from __future__ import annotations

from datetime import date, timedelta

from .budget import allocate, per_guest_warning
from .ideas import generate_ideas
from .llm import TextGenerator
from .models import EventRequest, EventType, Plan, Venue
from .timeline import build_timeline
from .vendors import vendor_checklist

MAX_LEAD_YEARS = 5
LARGE_WEDDING = 150
LARGE_COMMUNITY_EVENT = 200


def context_warnings(req: EventRequest) -> list[str]:
    """Generate context-specific warnings about venue, capacity, and budget.

    Args:
        req: Validated event request.

    Returns:
        List of warning messages for potential logistical constraints.
    """
    warnings: list[str] = []
    if req.venue != Venue.INDOOR:
        warnings.append(
            "Outdoor or mixed setting: book a weather backup and check the venue's cancellation policy."
        )
    if req.event_type == EventType.WEDDING and req.guest_count > LARGE_WEDDING:
        warnings.append("Large guest list: confirm venue capacity and plan seating early.")
    if req.event_type == EventType.COMMUNITY and req.guest_count >= LARGE_COMMUNITY_EVENT:
        warnings.append(
            "Large public gathering: check local permit thresholds, crowd capacity and safety rules early."
        )
    budget_note = per_guest_warning(req)
    if budget_note:
        warnings.append(budget_note)
    return warnings


def build_plan(req: EventRequest, today: date, generator: TextGenerator | None = None) -> Plan:
    """Orchestrate all sub-modules into a single Plan response.

    Args:
        req: Validated event request from the API.
        today: Current date, injected for testability.
        generator: Optional LLM backend for AI-generated ideas.

    Returns:
        A fully assembled Plan ready for JSON serialisation.

    Raises:
        ValueError: If the event date is too far in the future or in the past.
    """
    if req.event_date > today + timedelta(days=365 * MAX_LEAD_YEARS):
        raise ValueError(f"The event date must be within {MAX_LEAD_YEARS} years.")

    budget_lines = allocate(req)
    timeline, timeline_notes = build_timeline(req, today)
    ideas, ideas_source = generate_ideas(req, budget_lines, generator)

    return Plan(
        event_name=req.name,
        event_type=req.event_type,
        event_date=req.event_date,
        currency=req.currency,
        budget_total=req.budget,
        budget=budget_lines,
        timeline=timeline,
        vendors=vendor_checklist(req),
        warnings=[*timeline_notes, *context_warnings(req)],
        ideas=ideas,
        ideas_source=ideas_source,
    )
