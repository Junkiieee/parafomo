"""Parola hash'leme, JWT, şifre sıfırlama token'ı ve Google kimlik doğrulama."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import httpx
import jwt

from .config import get_settings

_settings = get_settings()

_GOOGLE_TOKENINFO = "https://oauth2.googleapis.com/tokeninfo"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=_settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, _settings.jwt_secret, algorithm=_settings.jwt_algorithm)


def decode_access_token(token: str) -> int | None:
    """Token geçerliyse user_id döndürür, değilse None."""
    try:
        payload = jwt.decode(
            token, _settings.jwt_secret, algorithms=[_settings.jwt_algorithm]
        )
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except (jwt.PyJWTError, ValueError):
        return None


# ---- Şifre sıfırlama token'ı ----
def generate_reset_token() -> tuple[str, str, datetime]:
    """(ham_token, token_hash, expires_at) döndürür. Ham token yalnız e-postaya gider."""
    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=_settings.reset_token_expire_minutes
    )
    return raw, token_hash, expires_at


def hash_reset_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---- Google kimlik doğrulama ----
def verify_google_id_token(credential: str) -> dict | None:
    """Google ID token'ını doğrular; geçerliyse {sub,email,name,email_verified} döndürür.

    tokeninfo uç noktası imza + son kullanma doğrulamasını Google tarafında yapar;
    biz audience (client_id) ve email_verified kontrolünü ekleriz.
    """
    if not _settings.google_client_id:
        return None
    try:
        with httpx.Client(timeout=15) as client:
            r = client.get(_GOOGLE_TOKENINFO, params={"id_token": credential})
        if r.status_code != 200:
            return None
        data = r.json()
    except (httpx.HTTPError, ValueError):
        return None

    if data.get("aud") != _settings.google_client_id:
        return None
    if str(data.get("email_verified")).lower() not in ("true", "1"):
        return None
    if not data.get("sub") or not data.get("email"):
        return None
    return {
        "sub": data["sub"],
        "email": data["email"],
        "name": data.get("name"),
        "email_verified": True,
    }
