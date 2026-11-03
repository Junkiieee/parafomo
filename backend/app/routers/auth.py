"""Kimlik doğrulama uç noktaları: kayıt, giriş, Google, şifre sıfırlama, ben-kimim."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..deps import get_current_user
from ..mailer import send_password_reset
from ..models import (
    Goal,
    Holding,
    PasswordResetToken,
    PortfolioSnapshot,
    PriceAlert,
    Transaction,
    User,
    WatchItem,
)
from ..ratelimit import RateLimiter, client_ip, enforce, public_mail_budget
from ..schemas import (
    GoogleLogin,
    Message,
    PasswordResetConfirm,
    PasswordResetRequest,
    Token,
    UserLogin,
    UserOut,
    UserRegister,
    UserUpdate,
)
from ..security import (
    create_access_token,
    dummy_verify_password,
    generate_reset_token,
    hash_password,
    hash_reset_token,
    verify_google_id_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
_settings = get_settings()
logger = logging.getLogger("parafomo.auth")

# Kaba kuvvet / kötüye kullanım sınırları (IP başına; CGNAT'ta paylaşılan IP'ye pay bırakır)
_login_ip = RateLimiter(limit=30, window=300)
_login_fail = RateLimiter(limit=10, window=900)    # e-posta başına hatalı giriş
_register_ip = RateLimiter(limit=10, window=3600)
_google_ip = RateLimiter(limit=30, window=300)      # her deneme Google'a dış istek
_reset_ip = RateLimiter(limit=10, window=3600)
_reset_email = RateLimiter(limit=3, window=3600)    # aynı adrese saatte en çok 3 sıfırlama maili


def _normalize_email(email: str) -> str:
    return email.strip().lower()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(body: UserRegister, request: Request, db: Session = Depends(get_db)) -> Token:
    enforce(_register_ip, client_ip(request))
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
    try:
        db.commit()
    except IntegrityError:  # eşzamanlı aynı e-posta kaydı → 500 değil 409
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu e-posta ile zaten bir hesap var.",
        )
    db.refresh(user)
    return Token(access_token=create_access_token(user.id, user.password_hash))


@router.post("/login", response_model=Token)
def login(body: UserLogin, request: Request, db: Session = Depends(get_db)) -> Token:
    enforce(_login_ip, client_ip(request))
    email = _normalize_email(body.email)
    # Hesap var/yok fark etmeksizin sayılır → kilit mesajı da varlık sızdırmaz
    if not _login_fail.allowed(email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Bu e-posta için çok fazla hatalı deneme. 15 dakika sonra tekrar dene ya da şifreni sıfırla.",
        )
    user = db.scalar(select(User).where(User.email == email))
    if user is None or user.password_hash is None:
        dummy_verify_password(body.password)  # yanıt süresi hesabın varlığını sızdırmasın
        ok = False
    else:
        ok = verify_password(body.password, user.password_hash)
    if not ok:
        _login_fail.hit(email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı.",
        )
    _login_fail.reset(email)
    return Token(access_token=create_access_token(user.id, user.password_hash))


@router.post("/google", response_model=Token)
def google_login(body: GoogleLogin, request: Request, db: Session = Depends(get_db)) -> Token:
    if not _settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google ile giriş henüz yapılandırılmadı.",
        )
    enforce(_google_ip, client_ip(request))
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
            # Var olan e-posta hesabına Google'ı bağla. Kayıtta e-posta doğrulanmadığı için
            # hesabı adresi önceden kaydeden başkası açmış olabilir (ön-ele geçirme): Google
            # adresin sahibini doğruladı → önceki parolayı geçersiz kıl; eski oturumlar da
            # pwv ile düşer. Parola isteyen kullanıcı "Şifreni mi unuttun?" ile yeniden belirler.
            user.google_sub = info["sub"]
            user.password_hash = None
            if not user.display_name and info.get("name"):
                user.display_name = info["name"]
        db.commit()
        db.refresh(user)
    return Token(access_token=create_access_token(user.id, user.password_hash))


_INVALID_RESET = "Bağlantı geçersiz veya süresi dolmuş. Lütfen yeniden talep et."


@router.post("/request-password-reset", response_model=Message)
def request_password_reset(
    body: PasswordResetRequest,
    request: Request,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Message:
    enforce(_reset_ip, client_ip(request))
    # Hesabın varlığını SIZDIRMA — her durumda aynı yanıt (sınır aşımında da).
    generic = Message(
        message="Eğer bu e-posta kayıtlıysa, şifre sıfırlama bağlantısı gönderildi."
    )
    email = _normalize_email(body.email)
    if not _reset_email.hit(email):
        return generic  # aynı adrese mail bombardımanı yok
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        return generic
    # Google-only hesap da sıfırlayabilir: adres Google'da doğrulanmış, parola belirlemiş olur
    if not public_mail_budget.hit("mail"):
        logger.warning("Üyeliksiz e-posta bütçesi doldu — şifre sıfırlama maili atlandı.")
        return generic

    now = datetime.now(timezone.utc)
    db.execute(delete(PasswordResetToken).where(PasswordResetToken.expires_at < now - timedelta(days=1)))
    raw, token_hash, expires_at = generate_reset_token()
    db.add(PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
    db.commit()

    reset_url = f"{_settings.frontend_base_url}/portfoy/sifre-sifirla?token={raw}"
    # SMTP yanıttan SONRA: süre farkı hesabın varlığını sızdırmasın
    background.add_task(send_password_reset, user.email, reset_url)
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_INVALID_RESET)
    new_hash = hash_password(body.new_password)  # bcrypt yazma kilidi alınmadan önce
    # Tek kullanımlık: koşullu UPDATE — aynı token'la eşzamanlı iki istekten yalnız biri geçer
    claimed = db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.id == prt.id, PasswordResetToken.used_at.is_(None))
        .values(used_at=now)
    ).rowcount
    user = db.get(User, prt.user_id)
    if claimed != 1 or user is None:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_INVALID_RESET)
    user.password_hash = new_hash
    # Kullanıcının diğer açık sıfırlama bağlantıları da kapanır; eski oturumlar pwv ile düşer
    db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
        .values(used_at=now)
    )
    db.commit()
    return Token(access_token=create_access_token(user.id, user.password_hash))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me", response_model=UserOut)
def update_me(
    body: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    fields = body.model_dump(exclude_unset=True)
    if "display_name" in fields:
        dn = (fields["display_name"] or "").strip()
        user.display_name = dn or None
    if fields.get("monthly_email") is not None:
        user.monthly_email = fields["monthly_email"]
    db.commit()
    db.refresh(user)
    return user


@router.delete(
    "/me", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Hesabı ve TÜM verilerini kalıcı siler (KVKK silme hakkı).

    Pozisyonlar, işlem defteri, değer geçmişi, alarmlar, izleme listesi, hedefler ve
    sıfırlama token'ları açıkça silinir — canlı DB'de bir tablo CASCADE'siz
    oluşturulmuş olsa da veri kalmasın. Geri alınamaz.
    """
    for model in (Holding, Transaction, PortfolioSnapshot, PriceAlert, Goal, WatchItem, PasswordResetToken):
        db.execute(delete(model).where(model.user_id == user.id))
    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
