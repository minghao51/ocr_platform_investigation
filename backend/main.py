from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import upload, processing, schemas, jobs, providers

app = FastAPI(title="OCR Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Include API routers
app.include_router(upload.router)
app.include_router(processing.router)
app.include_router(schemas.router)
app.include_router(jobs.router)
app.include_router(providers.router)

# Mount static files for frontend assets
import os
static_dir = "/app/frontend/dist"
if not os.path.exists(static_dir):
    # Try looking in local development path
    static_dir = "../frontend/dist"

if os.path.exists(f"{static_dir}/assets"):
    app.mount("/assets", StaticFiles(directory=f"{static_dir}/assets"), name="assets")

# Serve index.html for root
@app.get("/")
def serve_root():
    if os.path.exists(f"{static_dir}/index.html"):
        return FileResponse(f"{static_dir}/index.html")
    return {"message": "Frontend not found. Please build frontend or run in Docker."}

# Middleware to handle SPA routing for unmatched routes
@app.middleware("http")
async def spa_fallback(request: Request, call_next):
    response = await call_next(request)

    # If the route was not found (404) and it's not an API or asset route
    if response.status_code == 404:
        path = request.url.path

        # Don't fall back for API routes, assets, or health
        if not (path.startswith("/api/") or path.startswith("/assets/") or path == "/health"):
            # Serve index.html for SPA routes
            return FileResponse("/app/frontend/dist/index.html")

    return response
