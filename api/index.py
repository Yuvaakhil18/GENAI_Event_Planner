from pathlib import Path
from fastapi.responses import FileResponse
from app.main import app, STATIC_DIR

# Handle /api and /api/index paths if Vercel routes without stripping prefix
@app.get("/api", include_in_schema=False)
@app.get("/api/index", include_in_schema=False)
def vercel_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
