"""Unit tests for vendor checklist conditional branches."""

import pytest

from app.vendors import ACCESSIBILITY_ITEM, vendor_checklist


@pytest.mark.parametrize("event_type", ["wedding", "birthday", "community"])
def test_base_vendors_always_present(make_request, event_type):
    req = make_request(event_type=event_type, guest_count=10, venue="indoor")
    items = vendor_checklist(req)
    assert len(items) >= 2


def test_accessibility_item_always_included(make_request):
    for event_type in ("wedding", "birthday", "community"):
        req = make_request(event_type=event_type, guest_count=10, venue="indoor")
        assert ACCESSIBILITY_ITEM in vendor_checklist(req)


def test_outdoor_venue_adds_weather_backup(make_request):
    req = make_request(venue="outdoor", guest_count=10)
    items = vendor_checklist(req)
    assert any("weather" in item.lower() for item in items)


def test_mixed_venue_adds_weather_backup(make_request):
    req = make_request(venue="mixed", guest_count=10)
    items = vendor_checklist(req)
    assert any("weather" in item.lower() for item in items)


def test_indoor_venue_no_weather_backup(make_request):
    req = make_request(venue="indoor", guest_count=10)
    items = vendor_checklist(req)
    assert not any("weather" in item.lower() for item in items)


def test_large_guest_count_adds_restroom_check(make_request):
    req = make_request(guest_count=100, venue="indoor")
    items = vendor_checklist(req)
    assert any("restroom" in item.lower() for item in items)


def test_small_guest_count_no_restroom_check(make_request):
    req = make_request(guest_count=50, venue="indoor")
    items = vendor_checklist(req)
    assert not any("restroom capacity" in item.lower() for item in items)


def test_large_wedding_adds_shuttle(make_request):
    req = make_request(event_type="wedding", guest_count=200, venue="indoor")
    items = vendor_checklist(req)
    assert any("shuttle" in item.lower() for item in items)


def test_wedding_under_threshold_no_shuttle(make_request):
    req = make_request(event_type="wedding", guest_count=100, venue="indoor")
    items = vendor_checklist(req)
    assert not any("shuttle" in item.lower() for item in items)


def test_large_community_adds_crowd_management(make_request):
    req = make_request(event_type="community", guest_count=100, venue="indoor")
    items = vendor_checklist(req)
    assert any("crowd" in item.lower() or "parking" in item.lower() for item in items)


def test_small_community_no_crowd_management(make_request):
    req = make_request(event_type="community", guest_count=50, venue="indoor")
    items = vendor_checklist(req)
    assert not any("crowd" in item.lower() or "parking" in item.lower() for item in items)
