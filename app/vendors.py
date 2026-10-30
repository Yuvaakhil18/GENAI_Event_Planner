"""Vendor checklists, with conditional items based on the event context."""

from __future__ import annotations

from .models import EventRequest, EventType, Venue

ACCESSIBILITY_ITEM = "Accessibility check: step-free route, accessible restrooms, seating"

BASE_VENDORS: dict[EventType, list[str]] = {
    EventType.WEDDING: [
        "Venue", "Caterer", "Photographer", "Videographer", "Florist",
        "Band or DJ", "Officiant", "Hair and makeup", "Baker",
        "Rentals (tables, chairs, linens)",
    ],
    EventType.BIRTHDAY: [
        "Venue or space", "Caterer or food service", "Cake baker",
        "Entertainer", "Decorations", "Party supplies",
    ],
    EventType.COMMUNITY: [
        "Venue", "Event insurance", "Permits", "Sound and AV equipment",
        "Food vendor", "Security or first aid", "Printing and signage",
    ],
}


def vendor_checklist(req: EventRequest) -> list[str]:
    """Return the vendor checklist, adding conditional items for venue and size."""
    items = [*BASE_VENDORS[req.event_type], ACCESSIBILITY_ITEM]
    if req.venue != Venue.INDOOR:
        items.append("Weather backup plan and tent rental")
    if req.guest_count >= 100:
        items.append("Restroom capacity check (portable units if needed)")
    if req.event_type == EventType.WEDDING and req.guest_count > 150:
        items.append("Shuttle service for guests")
    if req.event_type == EventType.COMMUNITY and req.guest_count >= 100:
        items.append("Parking and crowd management")
    return items
