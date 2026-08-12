"""Security middleware: headers, rate limiting, request size, API key auth."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.auth import SESSION_COOKIE, auth_required, hash_api_key, verify_session_token
from app.core.config import Settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add defense-in-depth HTTP security headers."""

    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-XSS-Protection"] = "0"

        csp = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp

        if self.settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject oversized request bodies."""

    def __init__(self, app, max_bytes: int):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": f"Request body exceeds {self.max_bytes} bytes"},
                    )
            except ValueError:
                pass
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory sliding-window rate limiter per client IP."""

    EXEMPT_PREFIXES = (
        "/api/health",
        "/api/settings",
        "/api/stats",
    )

    def __init__(self, app, requests_per_minute: int, *, localhost_multiplier: int = 3):
        super().__init__(app)
        self.limit = max(requests_per_minute, 1)
        self.localhost_multiplier = max(localhost_multiplier, 1)
        self.window = 60.0
        self._hits: dict[str, list[float]] = defaultdict(list)

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _is_exempt(self, request: Request) -> bool:
        path = request.url.path
        if any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES):
            return True
        if request.method == "GET" and path.startswith("/api/jobs"):
            return True
        if request.method == "GET" and path.startswith("/api/selector-hints"):
            return True
        if request.method == "GET" and path.startswith("/api/settings"):
            return True
        return False

    def _effective_limit(self, ip: str) -> int:
        if ip in ("127.0.0.1", "::1", "localhost"):
            return self.limit * self.localhost_multiplier
        return self.limit

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        if self._is_exempt(request):
            return await call_next(request)

        now = time.monotonic()
        ip = self._client_ip(request)
        window_start = now - self.window
        limit = self._effective_limit(ip)

        hits = [t for t in self._hits[ip] if t > window_start]
        if len(hits) >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": "60"},
            )
        hits.append(now)
        self._hits[ip] = hits

        return await call_next(request)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Optional API key authentication via X-API-Key header (env or DB keys)."""

    EXEMPT_PATHS = {
        "/api/health",
        "/api/health/live",
        "/api/health/ready",
        "/api/health/detail",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/api/auth/login",
        "/api/auth/status",
    }

    def __init__(self, app, api_key: str | None = None):
        super().__init__(app)
        self.api_key = api_key

    def _db_key_valid(self, provided: str) -> bool:
        if not provided:
            return False
        try:
            from app.db.database import get_session_factory
            from app.db.models import ApiKeyRecord

            db = get_session_factory()()
            try:
                key_hash = hash_api_key(provided)
                record = (
                    db.query(ApiKeyRecord)
                    .filter(ApiKeyRecord.key_hash == key_hash, ApiKeyRecord.revoked_at.is_(None))
                    .first()
                )
                return record is not None
            finally:
                db.close()
        except Exception:
            return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        if request.url.path in self.EXEMPT_PATHS or request.url.path.startswith("/api/auth/"):
            return await call_next(request)

        provided = request.headers.get("x-api-key", "")
        if self.api_key and provided == self.api_key:
            request.state.api_key_valid = True
            return await call_next(request)
        if self._db_key_valid(provided):
            request.state.api_key_valid = True
            return await call_next(request)

        if self.api_key:
            logger.warning("Unauthorized API access attempt from %s", request.client)
            return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})

        return await call_next(request)


class SessionAuthMiddleware(BaseHTTPMiddleware):
    """Require admin session cookie when ADMIN_USER/PASSWORD are configured."""

    EXEMPT_PATHS = {
        "/api/health",
        "/api/health/live",
        "/api/health/ready",
        "/api/health/detail",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/api/auth/login",
        "/api/auth/status",
        "/api/settings",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not auth_required():
            return await call_next(request)
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        if request.url.path in self.EXEMPT_PATHS or request.url.path.startswith("/api/auth/"):
            return await call_next(request)

        if getattr(request.state, "api_key_valid", False):
            return await call_next(request)

        token = request.cookies.get(SESSION_COOKIE)
        if verify_session_token(token):
            return await call_next(request)

        return JSONResponse(status_code=401, content={"detail": "Authentication required"})
