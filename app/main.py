"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.auth_routes import router as auth_router
from app.api.manage_routes import router as manage_router
from app.api.routes import router
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.core.middleware import (
    APIKeyMiddleware,
    RateLimitMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
    SessionAuthMiddleware,
)
from app.core.scheduler import start_scheduler, stop_scheduler
from app.db.database import init_db

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    init_db()
    start_scheduler()
    yield
    stop_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Enterprise-ready web data extraction platform with async scraping, job queue, and export.",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(GZipMiddleware, minimum_size=500)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key"],
    )

    app.add_middleware(SecurityHeadersMiddleware, settings=settings)
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=settings.max_request_body_bytes)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)
    app.add_middleware(SessionAuthMiddleware)
    app.add_middleware(APIKeyMiddleware, api_key=settings.api_key)

    app.include_router(router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(manage_router, prefix="/api")

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

        @app.get("/", include_in_schema=False)
        async def serve_dashboard():
            return FileResponse(STATIC_DIR / "index.html")

        @app.get("/login", include_in_schema=False)
        async def serve_login():
            return FileResponse(STATIC_DIR / "login.html")

        @app.get("/manifest.json", include_in_schema=False)
        async def serve_manifest():
            return FileResponse(STATIC_DIR / "manifest.json", media_type="application/manifest+json")

        @app.get("/sw.js", include_in_schema=False)
        async def serve_sw():
            return FileResponse(
                STATIC_DIR / "sw.js",
                media_type="application/javascript",
                headers={"Service-Worker-Allowed": "/"},
            )

    return app


app = create_app()


def main() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
