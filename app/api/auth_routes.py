"""Authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app.core.auth import (
    SESSION_COOKIE,
    SESSION_MAX_AGE,
    auth_required,
    create_session_token,
    verify_password,
    verify_session_token,
)
from app.core.config import get_settings

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthStatusResponse(BaseModel):
    auth_enabled: bool
    authenticated: bool
    username: str | None = None


@router.get("/status", response_model=AuthStatusResponse)
def auth_status(request: Request) -> AuthStatusResponse:
    enabled = auth_required()
    if not enabled:
        return AuthStatusResponse(auth_enabled=False, authenticated=True)
    token = request.cookies.get(SESSION_COOKIE)
    user = verify_session_token(token)
    return AuthStatusResponse(auth_enabled=True, authenticated=bool(user), username=user)


@router.get("/me", response_model=AuthStatusResponse)
def auth_me(request: Request) -> AuthStatusResponse:
    enabled = auth_required()
    if not enabled:
        return AuthStatusResponse(auth_enabled=False, authenticated=True)
    token = request.cookies.get(SESSION_COOKIE)
    user = verify_session_token(token)
    return AuthStatusResponse(
        auth_enabled=True,
        authenticated=bool(user),
        username=user,
    )


@router.post("/login")
def login(body: LoginRequest, response: Response) -> dict:
    if not auth_required():
        return {"message": "Authentication is not configured", "authenticated": True}
    if not verify_password(body.username, body.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_session_token(body.username)
    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
        path="/",
    )
    return {"message": "Logged in", "authenticated": True, "username": body.username}


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(key=SESSION_COOKIE, path="/")
    return {"message": "Logged out", "authenticated": False}
