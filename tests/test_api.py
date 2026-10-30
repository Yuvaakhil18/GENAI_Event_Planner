"""Integration tests for the FastAPI application and its middleware."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

TODAY = date(2026, 10, 22)


class FakeGenerator:
    """Deterministic stub that satisfies the TextGenerator protocol."""

    def generate(self, system: str, user: str) -> str:
        """Return a fixed JSON array of one idea."""
        return (
            '[{"title": "Lantern walk", '
            '"description": "Guests light paper lanterns for an evening walk."}]'
        )


def payload(**overrides: Any) -> dict[str, Any]:
    """Build a valid API request body, optionally overriding fields."""
    body: dict[str, Any] = {
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


def make_client(generator: FakeGenerator | None = None) -> TestClient:
    """Create a TestClient with a fixed date and optional fake generator."""
    settings = Settings(anthropic_api_key=None, model="test", request_timeout=1.0)
    app = create_app(settings=settings, generator=generator, today_provider=lambda: TODAY)
    return TestClient(app)


@pytest.fixture
def client() -> TestClient:
    """Shared test client without an LLM generator."""
    return make_client()


# ── Happy-path tests ──────────────────────────────────────────────────────


def test_index_serves_ui_with_security_headers(client: TestClient) -> None:
    """GET / serves the SPA and includes core security headers."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Plan your event" in response.text
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_plan_returns_complete_plan_without_api_key(client: TestClient) -> None:
    """POST /api/plan with no generator returns template ideas and all sections."""
    response = client.post("/api/plan", json=payload())
    assert response.status_code == 200
    body = response.json()
    assert body["ideas_source"] == "template"
    assert body["budget"] and body["timeline"] and body["vendors"] and body["ideas"]
    assert any("weather" in warning.lower() for warning in body["warnings"])


def test_ai_ideas_are_used_when_generator_is_available() -> None:
    """When a generator is wired in, ideas come from AI."""
    response = make_client(FakeGenerator()).post("/api/plan", json=payload())
    body = response.json()
    assert body["ideas_source"] == "ai"
    assert body["ideas"][0]["title"] == "Lantern walk"


# ── Validation / rejection tests ─────────────────────────────────────────


def test_past_date_is_rejected(client: TestClient) -> None:
    """An event date before today is rejected with 422."""
    response = client.post(
        "/api/plan",
        json=payload(event_date=(TODAY - timedelta(days=1)).isoformat()),
    )
    assert response.status_code == 422


def test_too_far_ahead_is_rejected(client: TestClient) -> None:
    """An event date more than 5 years away is rejected with 422."""
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
def test_invalid_input_is_rejected(client: TestClient, overrides: dict[str, Any]) -> None:
    """Various invalid payloads are all rejected with 422."""
    assert client.post("/api/plan", json=payload(**overrides)).status_code == 422


def test_control_characters_are_stripped_from_name(client: TestClient) -> None:
    """Control characters and extra whitespace are normalised out of the name."""
    response = client.post("/api/plan", json=payload(name="Maya\x00s  party"))
    assert response.status_code == 200
    assert response.json()["event_name"] == "Maya s party"


def test_blank_name_is_rejected(client: TestClient) -> None:
    """A whitespace-only name is rejected with 422."""
    assert client.post("/api/plan", json=payload(name="   ")).status_code == 422


# ── create_app branch coverage ───────────────────────────────────────────


def test_create_app_instantiates_generator_when_api_key_provided() -> None:
    """When anthropic_api_key is set, create_app auto-creates a generator."""
    settings = Settings(anthropic_api_key="sk-test-key", model="claude-test", request_timeout=2.0)
    app = create_app(settings=settings, today_provider=lambda: TODAY)
    test_client = TestClient(app)
    response = test_client.get("/")
    assert response.status_code == 200


# ── Security middleware tests ────────────────────────────────────────────


def test_security_headers_include_hsts_and_permissions(client: TestClient) -> None:
    """All enterprise security headers are present in every response."""
    response = client.get("/")
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    assert "camera=()" in response.headers["Permissions-Policy"]
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"


def test_oversized_request_body_returns_413(client: TestClient) -> None:
    """A request exceeding 1 MB is rejected with 413 before route handling."""
    response = client.post(
        "/api/plan",
        content=b"x" * (1_048_576 + 1),
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(1_048_576 + 1),
        },
    )
    assert response.status_code == 413


def test_currency_case_insensitivity(client: TestClient) -> None:
    """Lowercase currency codes are accepted and normalized to uppercase."""
    response = client.post("/api/plan", json=payload(currency="eur"))
    assert response.status_code == 200
    assert response.json()["currency"] == "EUR"


def test_docs_and_openapi_metadata(client: TestClient) -> None:
    """Swagger UI /docs and OpenAPI schema are accessible with detailed tags."""
    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 200

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    schema = openapi_resp.json()
    assert "Planner" in [t["name"] for t in schema.get("tags", [])]
    assert "/api/plan" in schema["paths"]
    assert "413" in schema["paths"]["/api/plan"]["post"]["responses"]
