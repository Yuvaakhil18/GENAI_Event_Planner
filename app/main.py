"""FastAPI application: serves the planner UI and the /api/plan endpoint."""

from collections.abc import Awaitable, Callable
from datetime import date
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import Settings
from .llm import AnthropicTextGenerator, TextGenerator
from .models import EventRequest, Plan
from .planner import build_plan

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

MAX_REQUEST_BODY = 1_048_576  # 1 MB

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    "X-Permitted-Cross-Domain-Policies": "none",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def create_app(
    settings: Settings | None = None,
    generator: TextGenerator | None = None,
    today_provider: Callable[[], date] = date.today,
) -> FastAPI:
    """Build and return the FastAPI application.

    Args:
        settings: Runtime configuration; defaults to ``Settings.from_env()``.
        generator: Optional LLM backend for AI-generated ideas.
        today_provider: Callable returning today's date (injected for testing).

    Returns:
        Fully configured FastAPI app.
    """
    settings = settings or Settings.from_env()
    if generator is None and settings.anthropic_api_key:
        generator = AnthropicTextGenerator(
            settings.anthropic_api_key, settings.model, settings.request_timeout
        )

    limiter = Limiter(key_func=get_remote_address)
    app = FastAPI(
        title="Event Planning Assistant",
        description="Production-grade AI-powered event planning assistant providing budget allocation, adaptive timelines, vendor checklists, risk warnings, and creative ideas.",
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
    app.add_exception_handler(RateLimitExceeded, cast(Any, _rate_limit_exceeded_handler))
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.middleware("http")
    async def add_security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Inject security headers and reject oversized request bodies."""
        # Reject oversized request bodies before any parsing.
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_BODY:
            return Response("Request body too large", status_code=413)
        response: Response = await call_next(request)
        response.headers.update(SECURITY_HEADERS)
        return response

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        """Serve the single-page application."""
        return FileResponse(STATIC_DIR / "index.html")

    @app.post(
        "/api/plan",
        response_model=Plan,
        tags=["Planner"],
        summary="Generate a comprehensive event plan",
        description="Accepts event parameters, validates input boundaries, and generates a synchronized event strategy including budget breakdown, milestone timeline, vendor checklist, risk analysis, and creative recommendations.",
        responses={
            200: {"description": "Successfully generated event plan."},
            413: {"description": "Request body exceeds size limit (1 MB)."},
            422: {"description": "Validation error in event parameters."},
            429: {"description": "Rate limit exceeded (10 requests/minute)."},
        },
    )
    @limiter.limit("10/minute")
    def create_plan(request: Request, body: EventRequest) -> Plan:
        """Accept an event request and return a complete plan."""
        try:
            return build_plan(body, today=today_provider(), generator=generator)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return app


app = create_app()
