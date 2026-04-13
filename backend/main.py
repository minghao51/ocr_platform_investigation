from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from routers import (
    upload,
    processing,
    schemas,
    jobs,
    providers,
    text_processing,
    auth,
    websocket,
    benchmarks,
)
from config import get_settings
from limiter import limiter
from pathlib import Path
from paths import REPO_ROOT
import logging

logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title="OCR Platform")

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Keep demo sessions fresh while still allowing hashed frontend assets to cache.
    if not path.startswith("/assets/"):
        response.headers.setdefault("Cache-Control", "no-store")

    return response


# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Include API routers
app.include_router(auth.router)
app.include_router(websocket.router)
app.include_router(upload.router)
app.include_router(processing.router)
app.include_router(schemas.router)
app.include_router(jobs.router)
app.include_router(providers.router)
app.include_router(text_processing.router)
app.include_router(benchmarks.router)

# Mount static files for frontend assets
static_dir = REPO_ROOT / "frontend" / "dist"

# For Docker compatibility
if not static_dir.exists():
    static_dir = Path("/app/frontend/dist")

if (static_dir / "assets").exists():
    app.mount(
        "/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets"
    )


# Serve index.html for root
@app.get("/")
def serve_root():
    if (static_dir / "index.html").exists():
        return FileResponse(str(static_dir / "index.html"))
    return {"message": "Frontend not found. Please build frontend or run in Docker."}


# Middleware to handle SPA routing for unmatched routes
@app.middleware("http")
async def spa_fallback(request: Request, call_next):
    response = await call_next(request)

    # If the route was not found (404) and it's not an API or asset route
    if response.status_code == 404:
        path = request.url.path

        # Don't fall back for API routes, assets, or health
        if not (
            path.startswith("/api/") or path.startswith("/assets/") or path == "/health"
        ):
            # Serve index.html for SPA routes
            index_path = static_dir / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))

    return response


# Graceful shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down OCR Platform...")

    # Close database pool
    try:
        from database.pool import close_pool

        await close_pool()
        logger.info("Database pool closed")
    except Exception as e:
        logger.warning(f"Failed to close database pool: {e}")

    # Close WebSocket connections
    try:
        # The ConnectionManager handles cleanup automatically on disconnect
        logger.info("WebSocket connections will close")
    except Exception as e:
        logger.warning(f"Note: {e}")

    logger.info("Shutdown complete")
