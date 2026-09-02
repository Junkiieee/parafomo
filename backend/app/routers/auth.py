"""Kimlik doğrulama uç noktaları: kayıt, giriş, Google, şifre sıfırlama, ben-kimim."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..deps import get_current_user
from ..mailer import send_password_reset
from ..models import PasswordResetToken, User
from ..schemas import (
    GoogleLogin,
    Message,
    PasswordResetConfirm,
    PasswordResetRequest,
    Token,
    UserLogin,
    UserOut,
    UserRegister,
)
from ..security import (
    create_access_token,
    generate_reset_token,
    hash_password,
    hash_reset_token,
    verify_google_id_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
_settings = get_settings()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(body: UserRegister, db: Session = Depends(get_db)) -> Token:
    email = _normalize_email(body.email)
    exists = db.scalar(select(User).where(User.email == email))
    if exists is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu e-posta ile zaten bir hesap var.",
        )
    user = User(
        email=email,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return Token(access_token=create_access_token(user.id))


@router.post("/login", response_model=Token)
def login(body: UserLogin, db: Session = Depends(get_db)) -> Token:
    email = _normalize_email(body.email)
    user = db.scalar(select(User).where(User.email == email))
    if user is None or user.password_hash is None or not verify_password(
        body.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı.",
        )
    return Token(access_token=create_access_token(user.id))


@router.post("/google", response_model=Token)
def google_login(body: GoogleLogin, db: Session = Depends(get_db)) -> Token:
    if not _settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google ile giriş henüz yapılandırılmadı.",
        )
    info = verify_google_id_token(body.credential)
    if info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google doğrulaması başarısız.",
        )
    email = _normalize_email(info["email"])
    # Önce google_sub, sonra e-posta ile eşle; yoksa oluştur.
    user = db.scalar(select(User).where(User.google_sub == info["sub"]))
    if user is None:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email, google_sub=info["sub"], display_name=info.get("name"))
            db.add(user)
        else:
            # Var olan e-posta hesabına Google'ı bağla
            user.google_sub = info["sub"]
            if not user.display_name and info.get("name"):
                user.display_name = info["name"]
        db.commit()
        db.refresh(user)
    return Token(access_token=create_access_token(user.id))


@router.post("/request-password-reset", response_model=Message)
def request_password_reset(
    body: PasswordResetRequest, db: Session = Depends(get_db)
) -> Message:
    # Hesabın varlığını SIZDIRMA — her durumda aynı yanıt.
    generic = Message(
        message="Eğer bu e-posta kayıtlıysa, şifre sıfırlama bağlantısı gönderildi."
    )
    email = _normalize_email(body.email)
    user = db.scalar(select(User).where(User.email == email))
    if user is None or user.password_hash is None:
        # Google-only hesaplar için de sızdırma yapma
        return generic

    raw, token_hash, expires_at = generate_reset_token()
    db.add(PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
    db.commit()

    reset_url = f"{_settings.frontend_base_url}/portfoy/sifre-sifirla?token={raw}"
    send_password_reset(user.email, reset_url)
    return generic


@router.post("/reset-password", response_model=Token)
def reset_password(body: PasswordResetConfirm, db: Session = Depends(get_db)) -> Token:
    token_hash = hash_reset_token(body.token)
    prt = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    now = datetime.now(timezone.utc)
    expires_at = prt.expires_at if prt else None
    # SQLite naive datetime dönebilir — UTC varsay
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if prt is None or prt.used_at is not None or expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bağlantı geçersiz veya süresi dolmuş. Lütfen yeniden talep et.",
        )
    user = db.get(User, prt.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kullanıcı bulunamadı.")
    user.password_hash = hash_password(body.new_password)
    prt.used_at = now
    db.commit()
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
