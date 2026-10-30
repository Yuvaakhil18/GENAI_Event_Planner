"""FastAPI application: serves the planner UI and the /api/plan endpoint."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.types import ExceptionHandler

from .config import Settings
from .llm import AnthropicTextGenerator, TextGenerator
from .models import EventRequest, Plan
from .planner import build_plan

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "X-Permitted-Cross-Domain-Policies": "none",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def create_app(
    settings: Settings | None = None,
    generator: TextGenerator | None = None,
    today_provider: Callable[[], date] = date.today,
) -> FastAPI:
    """Build and configure the FastAPI event planner application."""
    settings = settings or Settings.from_env()
    if generator is None and settings.anthropic_api_key:
        generator = AnthropicTextGenerator(
            settings.anthropic_api_key, settings.model, settings.request_timeout
        )

    limiter = Limiter(key_func=get_remote_address)
    app = FastAPI(
        title="Event Planning Assistant",
        description="AI-powered event planning assistant providing budget allocation, adaptive timelines, vendor checklists, risk warnings, and creative ideas.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=[
            {
                "name": "Planner",
                "description": "Core event planning and strategy generation endpoints.",
            }
        ],
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, cast(ExceptionHandler, _rate_limit_exceeded_handler))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response: Response = await call_next(request)
        response.headers.update(SECURITY_HEADERS)
        return response

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.post(
        "/api/plan",
        response_model=Plan,
        tags=["Planner"],
        summary="Generate a comprehensive event plan",
        description="Generates budget breakdown, milestone timeline, vendor checklist, risk analysis, and creative recommendations.",
        responses={
            200: {"description": "Successfully generated event plan."},
            422: {"description": "Validation error in event parameters."},
            429: {"description": "Rate limit exceeded (10 requests/minute)."},
        },
    )
    @limiter.limit("10/minute")
    def create_plan(request: Request, body: EventRequest) -> Plan:
        logger.info(
            "Generating event plan: type=%s, budget=%.2f %s, guests=%d",
            body.event_type.value,
            body.budget,
            body.currency,
            body.guest_count,
        )
        try:
            return build_plan(body, today=today_provider(), generator=generator)
        except ValueError as exc:
            logger.warning("Event plan validation rejected: %s", exc)
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return app


app = create_app()
