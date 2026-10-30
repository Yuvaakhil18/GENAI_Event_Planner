"""Request and response models shared by the planner and the API."""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventType(StrEnum):
    """Supported event categories."""
    WEDDING = "wedding"
    BIRTHDAY = "birthday"
    COMMUNITY = "community"


class Venue(StrEnum):
    """Where the event takes place."""
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    MIXED = "mixed"


def _clean_text(value: str) -> str:
    """Replace control characters with spaces and collapse runs of whitespace."""
    printable = "".join(ch if ch.isprintable() else " " for ch in value)
    return " ".join(printable.split())


class EventRequest(BaseModel):
    """Validated user input from the planning form."""
    model_config = ConfigDict(extra="forbid")

    event_type: EventType
    name: str = Field(min_length=1, max_length=100)
    event_date: date
    guest_count: int = Field(ge=1, le=2000)
    budget: float = Field(gt=0, le=10_000_000, allow_inf_nan=False)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    venue: Venue = Venue.INDOOR
    notes: str = Field(default="", max_length=500)

    @field_validator("currency", mode="before")
    @classmethod
    def _currency_uppercase(cls, value: str) -> str:
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("name")
    @classmethod
    def _name_has_content(cls, value: str) -> str:
        cleaned = _clean_text(value)
        if not cleaned:
            raise ValueError("name must contain visible characters")
        return cleaned

    @field_validator("notes")
    @classmethod
    def _notes_clean(cls, value: str) -> str:
        return _clean_text(value)


class BudgetLine(BaseModel):
    """A single row in the budget breakdown."""
    category: str
    amount: float
    share: float


class TimelineTask(BaseModel):
    """A scheduled task with a due date."""
    due: date
    title: str
    category: str


class Idea(BaseModel):
    """A single event idea suggestion."""
    title: str
    description: str


class Plan(BaseModel):
    """Complete event plan returned by the API."""
    event_name: str
    event_type: EventType
    event_date: date
    currency: str
    budget_total: float
    budget: list[BudgetLine]
    timeline: list[TimelineTask]
    vendors: list[str]
    warnings: list[str]
    ideas: list[Idea]
    ideas_source: str  # "ai" or "template"
