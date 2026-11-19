"""Parola hash'leme, JWT, şifre sıfırlama token'ı ve Google kimlik doğrulama."""
from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import httpx
import jwt

from .config import get_settings

_settings = get_settings()
logger = logging.getLogger("parafomo.security")

_GOOGLE_TOKENINFO = "https://oauth2.googleapis.com/tokeninfo"
_GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}

# Repo herkese açık: varsayılan/şablon sır ile imzalanan token'ı herkes üretebilir.
# Böyle bir sırla açılırsa süreç başına rastgele sır kullan (oturumlar yeniden
# başlatmada düşer ama sahte token imkânsız) ve logda bağır.
_PLACEHOLDER_SECRETS = {"", "dev-insecure-secret-change-me", "change-me-to-a-long-random-secret"}
if _settings.jwt_secret.strip() in _PLACEHOLDER_SECRETS:
    logger.critical(
        "PORTFOLIO_JWT_SECRET ayarlı değil ya da şablon değer — geçici rastgele sır "
        "kullanılıyor; her yeniden başlatmada oturumlar düşer. backend/.env'e güçlü bir sır koy."
    )
    _JWT_SECRET = secrets.token_urlsafe(48)
else:
    if len(_settings.jwt_secret) < 32:
        logger.warning("PORTFOLIO_JWT_SECRET 32 karakterden kısa — daha uzun bir sır önerilir.")
    _JWT_SECRET = _settings.jwt_secret

# Yalnız HMAC: "none" ya da asimetrik algoritma ayarla açılmasın
_JWT_ALGORITHM = _settings.jwt_algorithm if _settings.jwt_algorithm in ("HS256", "HS384", "HS512") else "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


_DUMMY_HASH: bytes | None = None


def dummy_verify_password(password: str) -> None:
    """Kullanıcı yokken de bir bcrypt kontrolü yap — yanıt süresi hesabın
    varlığını sızdırmasın (bilinmeyen e-posta anında, var olan ~0,3 sn dönüyordu)."""
    global _DUMMY_HASH
    if _DUMMY_HASH is None:
        _DUMMY_HASH = bcrypt.hashpw(secrets.token_bytes(16), bcrypt.gensalt())
    try:
        bcrypt.checkpw(password.encode("utf-8"), _DUMMY_HASH)
    except (ValueError, TypeError):
        pass


def password_fingerprint(password_hash: str | None) -> str:
    """Token'a gömülen parola parmak izi (pwv). Parola değişince (sıfırlama, Google
    bağlama) eski token'lar geçersizleşir. Hash'in kendisi token'a girmez (HMAC)."""
    return hmac.new(
        _JWT_SECRET.encode("utf-8"), b"pwv\x00" + (password_hash or "").encode("utf-8"), hashlib.sha256
    ).hexdigest()[:16]


def create_access_token(user_id: int, password_hash: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=_settings.jwt_expire_minutes),
        "pwv": password_fingerprint(password_hash),
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


def decode_access_payload(token: str) -> dict | None:
    """İmza + süre + zorunlu alanlar geçerliyse payload, değilse None."""
    try:
        payload = jwt.decode(
            token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM], options={"require": ["exp", "sub"]}
        )
        int(payload["sub"])
        return payload
    except (jwt.PyJWTError, ValueError, TypeError):
        return None


def decode_access_token(token: str) -> int | None:
    """Token geçerliyse user_id döndürür, değilse None."""
    payload = decode_access_payload(token)
    return int(payload["sub"]) if payload else None


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
        with httpx.Client(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            r = client.get(_GOOGLE_TOKENINFO, params={"id_token": credential})
        if r.status_code != 200:
            return None
        data = r.json()
    except (httpx.HTTPError, ValueError):
        return None
    if not isinstance(data, dict):
        return None

    if data.get("aud") != _settings.google_client_id:
        return None
    if data.get("iss") not in _GOOGLE_ISSUERS:
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
