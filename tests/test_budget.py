import pytest

from app.budget import ALLOCATION, allocate, per_guest_warning
from app.models import EventType


@pytest.mark.parametrize("event_type", list(EventType))
def test_each_allocation_sums_to_one(event_type):
    assert sum(ALLOCATION[event_type].values()) == pytest.approx(1.0)


@pytest.mark.parametrize("event_type", ["wedding", "birthday", "community"])
def test_lines_add_up_exactly_to_budget(make_request, event_type):
    req = make_request(event_type=event_type, budget=12345.67)
    lines = allocate(req)
    assert round(sum(line.amount for line in lines), 2) == 12345.67


def test_contingency_is_last_and_absorbs_drift(make_request):
    req = make_request(budget=100.01)
    lines = allocate(req)
    assert lines[-1].category == "contingency"
    assert round(sum(line.amount for line in lines), 2) == 100.01


def test_low_per_guest_budget_triggers_warning(make_request):
    req = make_request(budget=1000, guest_count=100)  # $10 per guest for a wedding
    assert per_guest_warning(req) is not None


def test_adequate_budget_has_no_warning(make_request):
    req = make_request(budget=20000, guest_count=100)
    assert per_guest_warning(req) is None
