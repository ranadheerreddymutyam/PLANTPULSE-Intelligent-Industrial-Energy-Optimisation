"""Main FastAPI Application Entrypoint for PlantPulse."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.routers import (
    config, equipment, telemetry, idle, decisions, control, savings,
    events, analytics, import_data, reports, scenarios, auth
)
from app.core.database import engine, Base

# Initialize tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=f"{settings.PROJECT_DESCRIPTION}\n\nSTATUS: {settings.PROJECT_STATUS}",
    version=settings.MODEL_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pure ASGI Middleware for Provenance Headers (Python 3.14 compatible, no AnyIO task group deadlock)
class ProvenanceHeaderMiddleware:
    def __init__(self, inner_app):
        self.inner_app = inner_app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.inner_app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-project-status", settings.PROJECT_STATUS.encode()))
                headers.append((b"x-data-provenance", settings.DATA_PROVENANCE_DEFAULT.encode()))
                message["headers"] = headers
            await send(message)

        await self.inner_app(scope, receive, send_wrapper)

app.add_middleware(ProvenanceHeaderMiddleware)

# Register API Routers under /api/v1
api_v1_prefix = "/api/v1"
app.include_router(analytics.router, prefix=api_v1_prefix)
app.include_router(config.router, prefix=api_v1_prefix)
app.include_router(equipment.router, prefix=api_v1_prefix)
app.include_router(telemetry.router, prefix=api_v1_prefix)
app.include_router(idle.router, prefix=api_v1_prefix)
app.include_router(decisions.router, prefix=api_v1_prefix)
app.include_router(control.router, prefix=api_v1_prefix)
app.include_router(savings.router, prefix=api_v1_prefix)
app.include_router(events.router, prefix=api_v1_prefix)
app.include_router(import_data.router, prefix=api_v1_prefix)
app.include_router(reports.router, prefix=api_v1_prefix)
app.include_router(scenarios.router, prefix=api_v1_prefix)
app.include_router(auth.router, prefix=api_v1_prefix)

@app.get("/api/v1/info")
def root_info():
    return {
        "project": settings.PROJECT_NAME,
        "title": settings.PROJECT_DESCRIPTION,
        "status": settings.PROJECT_STATUS,
        "data_provenance": settings.DATA_PROVENANCE_DEFAULT,
        "version": settings.MODEL_VERSION,
        "system_notice": "Non-AI, rule-based retrofit decision support. No physical hardware connected. All control actions are simulated.",
        "documentation": "/docs",
        "api_v1": "/api/v1"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "database": "connected",
        "model_version": settings.MODEL_VERSION
    }

# Mount built frontend static files if available
frontend_dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.exists(frontend_dist_dir):
    app.mount("/", StaticFiles(directory=frontend_dist_dir, html=True), name="frontend")

from fastapi.responses import FileResponse
@app.exception_handler(404)
async def spa_fallback_404(request, exc):
    """Fallback handler to support SPA client-side routes on page refresh."""
    if os.path.exists(frontend_dist_dir) and not request.url.path.startswith("/api"):
        index_file = os.path.join(frontend_dist_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=404, content={"detail": "Not Found"})

