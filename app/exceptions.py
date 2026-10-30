"""Domain-specific exception hierarchy for the Event Planning Assistant."""

from __future__ import annotations


class EventPlannerError(Exception):
    """Base domain exception for all event planner operational errors."""


class InvalidPlanningWindowError(EventPlannerError, ValueError):
    """Raised when an event date falls outside the allowed planning lead-time window."""


class PastDateError(InvalidPlanningWindowError):
    """Raised when an event date is scheduled in the past."""

