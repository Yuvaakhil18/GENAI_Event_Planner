"""Serverless entrypoint for Vercel deployment."""

from __future__ import annotations

from fastapi.responses import FileResponse

from app.main import STATIC_DIR, app


@app.get("/api", include_in_schema=False)
@app.get("/api/index", include_in_schema=False)
def vercel_index() -> FileResponse:
    """Serve the single-page application for root API aliases."""
    return FileResponse(STATIC_DIR / "index.html")
