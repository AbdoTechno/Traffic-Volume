from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.routers.forecast import router as forecast_router

app = FastAPI(title="Traffic Volume Forecast API", version="2.0.0")

# ── CORS Middleware ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8001",
        "http://localhost:8001",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://traffic-volume-production.up.railway.app",
        "https://traffic-volume-production.up.railway.app",
        "null",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Validation Error Handler ─────────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return user-friendly validation error messages."""
    errors = exc.errors()
    if errors:
        first = errors[0]
        field = first.get("loc", ("",))[1] if len(first.get("loc", ())) > 1 else ""
        msg = first.get("msg", "Invalid input")
        if field == "days" and "less than or equal" in msg:
            detail = "Number of days must be between 1 and 3."
        elif field in ("start_hour", "end_hour"):
            detail = "Hours must be between 0 and 23."
        elif "end_hour" in str(first.get("loc", "")):
            detail = "End hour must be greater than or equal to start hour."
        else:
            detail = msg
    else:
        detail = "Invalid request data."
    return JSONResponse(status_code=422, content={"detail": detail})


# ── Mount Static Files ───────────────────────────────────────────────────────
static_path = Path(__file__).parent.parent / "src"
app.mount("/static", StaticFiles(directory=static_path), name="static")
app.mount("/js", StaticFiles(directory=static_path / "js"), name="js")


@app.get("/styles.css")
def get_styles() -> FileResponse:
    """Serve styles.css at root for relative path compatibility."""
    return FileResponse(static_path / "styles.css", media_type="text/css")


@app.get("/favicon.svg")
@app.get("/favicon.ico")
def get_favicon() -> FileResponse:
    """Serve brand favicon."""
    return FileResponse(static_path / "favicon.svg", media_type="image/svg+xml")



# ── Include Routers ──────────────────────────────────────────────────────────
app.include_router(forecast_router)


# ── Frontend Dashboard Route ─────────────────────────────────────────────────
@app.get("/")
def home() -> FileResponse:
    """Serve the frontend dashboard."""
    index_path = static_path / "index.html"
    return FileResponse(index_path, media_type="text/html")

