"""Budget allocation by category, with a per-guest sanity check."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .models import BudgetLine, EventRequest, EventType

# Category shares per event type. Each row sums to 1.0 and ends with contingency,
# which absorbs rounding drift so the lines always add up to the total budget.
ALLOCATION: dict[EventType, dict[str, float]] = {
    EventType.WEDDING: {
        "venue": 0.30, "catering": 0.30, "photography": 0.10, "attire": 0.07,
        "decor": 0.08, "music": 0.05, "stationery": 0.02, "contingency": 0.08,
    },
    EventType.BIRTHDAY: {
        "venue": 0.15, "food": 0.30, "cake": 0.10, "decor": 0.15,
        "entertainment": 0.15, "favors": 0.05, "contingency": 0.10,
    },
    EventType.COMMUNITY: {
        "venue": 0.25, "food": 0.20, "equipment": 0.15, "permits": 0.05,
        "marketing": 0.10, "volunteer_supplies": 0.10, "contingency": 0.15,
    },
}

# Rough per-guest floors below which a plan is unlikely to be workable.
MIN_PER_GUEST: dict[EventType, float] = {
    EventType.WEDDING: 40.0,
    EventType.BIRTHDAY: 8.0,
    EventType.COMMUNITY: 3.0,
}


def allocate(req: EventRequest) -> list[BudgetLine]:
    """Split the total budget into category lines using pre-defined weights.

    Args:
        req: Validated event request containing event type and budget.

    Returns:
        Ordered list of budget lines whose amounts sum to ``req.budget``.
    """
    weights = ALLOCATION[req.event_type]
    budget_d = Decimal(str(req.budget))
    lines: list[BudgetLine] = []
    for category, share in weights.items():
        amount = float(
            (budget_d * Decimal(str(share))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )
        lines.append(BudgetLine(category=category, amount=amount, share=share))
    # Absorb residual drift into the last (contingency) line.
    total = sum(Decimal(str(line.amount)) for line in lines)
    drift = float((budget_d - total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    last = lines[-1]
    lines[-1] = last.model_copy(update={"amount": round(last.amount + drift, 2)})
    return lines


def per_guest_warning(req: EventRequest) -> str | None:
    """Return a warning string if the per-guest spend falls below the floor.

    Args:
        req: Validated event request.

    Returns:
        A human-readable warning, or ``None`` if the budget is adequate.
    """
    per_guest = req.budget / req.guest_count
    floor = MIN_PER_GUEST[req.event_type]
    if per_guest >= floor:
        return None
    return (
        f"The budget works out to about {req.currency} {per_guest:,.2f} per guest, "
        f"below the usual {req.currency} {floor:,.0f} for this type of event. "
        "Consider a smaller guest list, a simpler format, or a lower-cost venue."
    )
