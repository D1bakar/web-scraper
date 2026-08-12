"""Session-based authentication for optional admin login."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode

from app.core.config import get_settings

SESSION_COOKIE = "wsp_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


def _signing_key() -> bytes:
    settings = get_settings()
    secret = settings.session_secret or settings.admin_password or "dev-insecure-secret"
    return hashlib.sha256(secret.encode()).digest()


def verify_password(username: str, password: str) -> bool:
    settings = get_settings()
    if not settings.admin_user or not settings.admin_password:
        return False
    user_ok = hmac.compare_digest(username, settings.admin_user)
    pass_ok = hmac.compare_digest(password, settings.admin_password)
    return user_ok and pass_ok


def auth_required() -> bool:
    settings = get_settings()
    return bool(settings.admin_user and settings.admin_password)


def create_session_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": int(time.time()) + SESSION_MAX_AGE,
        "nonce": secrets.token_hex(8),
    }
    body = urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(_signing_key(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify_session_token(token: str | None) -> str | None:
    if not token or "." not in token:
        return None
    body, sig = token.rsplit(".", 1)
    expected = hmac.new(_signing_key(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    pad = "=" * (-len(body) % 4)
    try:
        payload = json.loads(urlsafe_b64decode(body + pad))
    except (json.JSONDecodeError, ValueError):
        return None
    if payload.get("exp", 0) < time.time():
        return None
    return payload.get("sub")


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key() -> str:
    return f"wsp_{secrets.token_urlsafe(32)}"


def key_prefix(raw_key: str) -> str:
    return raw_key[:12] + "…" if len(raw_key) > 12 else raw_key
