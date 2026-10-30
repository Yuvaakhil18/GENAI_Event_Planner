"""Vercel serverless entrypoint for the Event Planning Assistant."""

from fastapi.responses import FileResponse

from app.main import STATIC_DIR, app


@app.get("/api", include_in_schema=False)
@app.get("/api/index", include_in_schema=False)
def vercel_index() -> FileResponse:
    """Serve the single-page application when invoked via prefixed serverless path."""
    return FileResponse(STATIC_DIR / "index.html")
