import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hasher = PasswordHash.recommended()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=settings.access_token_expires_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expires, "typ": "access"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def create_refresh_token(subject: str, version: int) -> tuple[str, str, datetime]:
    expires = datetime.now(UTC) + timedelta(days=settings.refresh_token_expires_days)
    jti = str(uuid.uuid4())
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expires,
        "typ": "refresh",
        "jti": jti,
        "ver": version,
    }
    token = jwt.encode(payload, settings.refresh_secret, algorithm=ALGORITHM)
    return token, jti, expires


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        if payload.get("typ") != "access":
            raise ValueError("Invalid token type")
        return payload
    except JWTError as exc:
        raise ValueError("Invalid access token") from exc


def decode_refresh_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.refresh_secret, algorithms=[ALGORITHM])
        if payload.get("typ") != "refresh":
            raise ValueError("Invalid token type")
        return payload
    except JWTError as exc:
        raise ValueError("Invalid refresh token") from exc


def hash_viewer_token(viewer_token: str) -> str:
    value = f"{viewer_token}:{settings.viewer_token_pepper}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def hash_url(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
