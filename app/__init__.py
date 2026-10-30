"""Event Planning Assistant package.

Public domain interfaces, models, orchestrators, and exception hierarchies.
"""

from __future__ import annotations

from .budget import allocate, per_guest_warning
from .config import Settings
from .exceptions import EventPlannerError, InvalidPlanningWindowError, PastDateError
from .ideas import generate_ideas, parse_ideas, template_ideas
from .llm import AnthropicTextGenerator, TextGenerator
from .main import app, create_app
from .models import (
    BudgetLine,
    EventRequest,
    EventType,
    Idea,
    Plan,
    TimelineTask,
    Venue,
)
from .planner import build_plan, context_warnings
from .timeline import build_timeline
from .vendors import vendor_checklist

__all__ = [
    "AnthropicTextGenerator",
    "BudgetLine",
    "EventPlannerError",
    "EventRequest",
    "EventType",
    "Idea",
    "InvalidPlanningWindowError",
    "PastDateError",
    "Plan",
    "Settings",
    "TextGenerator",
    "TimelineTask",
    "Venue",
    "allocate",
    "app",
    "build_plan",
    "build_timeline",
    "context_warnings",
    "create_app",
    "generate_ideas",
    "parse_ideas",
    "per_guest_warning",
    "template_ideas",
    "vendor_checklist",
]
