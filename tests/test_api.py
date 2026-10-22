from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

TODAY = date(2026, 10, 22)


class FakeGenerator:
    def generate(self, system, user):
        return '[{"title": "Lantern walk", "description": "Guests light paper lanterns for an evening walk."}]'


def payload(**overrides):
    body = {
        "event_type": "birthday",
        "name": "Maya's 30th",
        "event_date": (TODAY + timedelta(days=60)).isoformat(),
        "guest_count": 40,
        "budget": 1500,
        "currency": "USD",
        "venue": "outdoor",
        "notes": "Vegetarian options please",
    }
    body.update(overrides)
    return body


def make_client(generator=None):
    settings = Settings(anthropic_api_key=None, model="test", request_timeout=1.0)
    app = create_app(settings=settings, generator=generator, today_provider=lambda: TODAY)
    return TestClient(app)


@pytest.fixture
def client():
    return make_client()


def test_index_serves_ui_with_security_headers(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Plan your event" in response.text
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_plan_returns_complete_plan_without_api_key(client):
    response = client.post("/api/plan", json=payload())
    assert response.status_code == 200
    body = response.json()
    assert body["ideas_source"] == "template"
    assert body["budget"] and body["timeline"] and body["vendors"] and body["ideas"]
    assert any("weather" in warning.lower() for warning in body["warnings"])


def test_ai_ideas_are_used_when_generator_is_available():
    response = make_client(FakeGenerator()).post("/api/plan", json=payload())
    body = response.json()
    assert body["ideas_source"] == "ai"
    assert body["ideas"][0]["title"] == "Lantern walk"


def test_past_date_is_rejected(client):
    response = client.post("/api/plan", json=payload(event_date=(TODAY - timedelta(days=1)).isoformat()))
    assert response.status_code == 422


def test_too_far_ahead_is_rejected(client):
    far = TODAY + timedelta(days=365 * 6)
    response = client.post("/api/plan", json=payload(event_date=far.isoformat()))
    assert response.status_code == 422


@pytest.mark.parametrize(
    "overrides",
    [
        {"budget": -5},
        {"budget": 1e12},
        {"guest_count": 5000},
        {"guest_count": 0},
        {"currency": "usd1"},
        {"event_type": "funeral"},
        {"is_admin": True},
        {"notes": "x" * 501},
    ],
)
def test_invalid_input_is_rejected(client, overrides):
    assert client.post("/api/plan", json=payload(**overrides)).status_code == 422


def test_control_characters_are_stripped_from_name(client):
    response = client.post("/api/plan", json=payload(name="Maya\x00s  party"))
    assert response.status_code == 200
    assert response.json()["event_name"] == "Maya s party"


def test_blank_name_is_rejected(client):
    assert client.post("/api/plan", json=payload(name="   ")).status_code == 422
