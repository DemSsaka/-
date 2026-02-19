from datetime import UTC, datetime
import uuid
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from itsdangerous import URLSafeSerializer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.models import RefreshTokenDenylist, User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
csrf_serializer = URLSafeSerializer(settings.jwt_secret, salt="csrf")
oauth_state_serializer = URLSafeSerializer(settings.jwt_secret, salt="oauth-state")


def to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        bio=user.bio,
        birth_date=user.birth_date,
        theme=user.theme,
        balance_cents=user.balance_cents,
        email_verified=user.email_verified,
    )


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="none",
        max_age=settings.access_token_expires_minutes * 60,
        path="/",
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="none",
        max_age=settings.refresh_token_expires_days * 24 * 3600,
        path="/api/auth",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/auth")


def csrf_for_user(user_id: int) -> str:
    return csrf_serializer.dumps({"uid": user_id})


def _google_redirect_uri() -> str:
    return settings.google_redirect_uri or f"{settings.api_origin}/api/auth/google/callback"


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    existing = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password))
    db.add(user)
    await db.flush()

    access = create_access_token(str(user.id))
    refresh, _, _ = create_refresh_token(str(user.id), user.refresh_version)
    set_auth_cookies(response, access, refresh)
    await db.commit()

    return AuthResponse(user=to_user_response(user), csrf_token=csrf_for_user(user.id))


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_access_token(str(user.id))
    refresh, _, _ = create_refresh_token(str(user.id), user.refresh_version)
    set_auth_cookies(response, access, refresh)
    return AuthResponse(user=to_user_response(user), csrf_token=csrf_for_user(user.id))


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
) -> AuthResponse:
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        payload = decode_refresh_token(refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    user_id = int(payload["sub"])
    jti = payload["jti"]
    deny = await db.scalar(select(RefreshTokenDenylist).where(RefreshTokenDenylist.jti == jti))
    if deny:
        raise HTTPException(status_code=401, detail="Refresh token revoked")

    user = await db.scalar(select(User).where(User.id == user_id))
    if not user or int(payload.get("ver", -1)) != user.refresh_version:
        raise HTTPException(status_code=401, detail="Invalid refresh token version")

    access = create_access_token(str(user.id))
    refresh_value, _, _ = create_refresh_token(str(user.id), user.refresh_version)
    set_auth_cookies(response, access, refresh_value)
    return AuthResponse(user=to_user_response(user), csrf_token=csrf_for_user(user.id))


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    current_user.refresh_version += 1
    db.add(
        RefreshTokenDenylist(
            jti=f"global-{current_user.id}-{current_user.refresh_version}",
            expires_at=datetime.now(UTC),
        )
    )
    await db.commit()
    clear_auth_cookies(response)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return to_user_response(current_user)


@router.get("/google/start")
async def google_start() -> RedirectResponse:
    if not settings.google_client_id or not settings.google_client_secret:
        return RedirectResponse(url=f"{settings.web_origin}/?oauth_error=google_not_configured")

    state = oauth_state_serializer.dumps({"nonce": str(uuid.uuid4())})
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": _google_redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}")


@router.get("/google/callback")
async def google_callback(code: str, state: str, db: AsyncSession = Depends(get_db)) -> RedirectResponse:
    if not settings.google_client_id or not settings.google_client_secret:
        return RedirectResponse(url=f"{settings.web_origin}/?oauth_error=google_not_configured")

    try:
        oauth_state_serializer.loads(state)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc

    token_payload = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": _google_redirect_uri(),
        "grant_type": "authorization_code",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_resp = await client.post("https://oauth2.googleapis.com/token", data=token_payload)
            token_resp.raise_for_status()
            token_data = token_resp.json()
            id_token = token_data.get("id_token")
            if not id_token:
                return RedirectResponse(url=f"{settings.web_origin}/?oauth_error=google_token")
            verify_resp = await client.get("https://oauth2.googleapis.com/tokeninfo", params={"id_token": id_token})
            verify_resp.raise_for_status()
            claims = verify_resp.json()
    except Exception:
        return RedirectResponse(url=f"{settings.web_origin}/?oauth_error=google_callback_failed")

    if claims.get("aud") != settings.google_client_id:
        return RedirectResponse(url=f"{settings.web_origin}/?oauth_error=google_audience")

    sub = claims.get("sub")
    email = str(claims.get("email", "")).lower().strip()
    name = claims.get("name")
    picture = claims.get("picture")
    email_verified = str(claims.get("email_verified", "false")).lower() == "true"

    if not sub or not email:
        return RedirectResponse(url=f"{settings.web_origin}/?oauth_error=google_profile")

    user = await db.scalar(
        select(User).where(User.oauth_provider == "google", User.oauth_subject == str(sub))
    )
    if not user:
        user = await db.scalar(select(User).where(User.email == email))

    if not user:
        user = User(
            email=email,
            password_hash=hash_password(str(uuid.uuid4())),
            nickname=str(name)[:80] if name else None,
            avatar_url=str(picture) if picture else None,
            oauth_provider="google",
            oauth_subject=str(sub),
            email_verified=email_verified,
        )
        db.add(user)
        await db.flush()
    else:
        user.oauth_provider = "google"
        user.oauth_subject = str(sub)
        if email_verified:
            user.email_verified = True
        if not user.nickname and name:
            user.nickname = str(name)[:80]
        if not user.avatar_url and picture:
            user.avatar_url = str(picture)

    access = create_access_token(str(user.id))
    refresh, _, _ = create_refresh_token(str(user.id), user.refresh_version)
    redirect = RedirectResponse(url=f"{settings.web_origin}/app")
    set_auth_cookies(redirect, access, refresh)
    await db.commit()
    return redirect
