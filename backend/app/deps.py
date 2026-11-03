"""Ortak FastAPI bağımlılıkları — oturum sahibi kullanıcı çözümü."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .db import get_db
from .models import User
from .security import decode_access_payload, password_fingerprint

_bearer = HTTPBearer(auto_error=True)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_payload(creds.credentials)
    user_id = int(payload["sub"]) if payload else None
    # SQLite INTEGER 64 bit — taşan id 500 yerine 401
    if user_id is None or not 0 < user_id < 2**63:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş oturum.",
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Kullanıcı bulunamadı."
        )
    # Parola değiştiyse (sıfırlama / Google bağlama) önceki token'lar düşer.
    # pwv'siz eski token'lar süreleri dolana dek (≤7 gün) geçerli kalır.
    if "pwv" in payload and payload["pwv"] != password_fingerprint(user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş oturum.",
        )
    return user
