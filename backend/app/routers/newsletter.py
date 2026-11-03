"""Bülten aboneliği — çift onay (double opt-in), kendi altyapımız.

POST /newsletter/subscribe   → kayıt (pending) + onay maili (Brevo SMTP)
GET  /newsletter/confirm     → token ile confirmed, siteye yönlendirir
GET/POST /newsletter/unsubscribe → token ile unsubscribed (POST: RFC 8058 tek-tık)

Hesabın varlığı sızdırılmaz: subscribe her durumda aynı yanıtı döner.
"""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..mailer import send_newsletter_confirm
from ..models import NewsletterSubscriber
from ..ratelimit import RateLimiter, client_ip, enforce, public_mail_budget
from ..schemas import Message, NewsletterSubscribe

router = APIRouter(prefix="/newsletter", tags=["newsletter"])
_settings = get_settings()
logger = logging.getLogger("parafomo.newsletter")

# IP başına 10 dakikada 5 kayıt denemesi. IP ratelimit.client_ip'ten: CF-Connecting-IP'ye
# körü körüne güvenmek (api DNS-only) her istekte sahte IP ile sınırı atlatıyordu.
_limiter = RateLimiter(limit=5, window=600)
# Aynı adrese onay maili en sık bu aralıkla yeniden gider
_RESEND_AFTER = timedelta(minutes=10)

_GENERIC = "Neredeyse tamam! Gelen kutuna onay e-postası gönderdik — linke tıklayınca aboneliğin başlar."


def _rate_limit(request: Request) -> None:
    enforce(_limiter, client_ip(request))


def _aware(dt: datetime | None) -> datetime | None:
    # SQLite naive datetime dönebilir — UTC varsay
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _links(token: str) -> tuple[str, str]:
    api = "https://api.parafomo.com"
    return (
        f"{api}/newsletter/confirm?token={token}",
        f"{api}/newsletter/unsubscribe?token={token}",
    )


@router.post("/subscribe", response_model=Message)
def subscribe(
    body: NewsletterSubscribe,
    request: Request,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Message:
    if body.website:  # bal küpü dolu → bot; sessizce başarı dön
        return Message(message=_GENERIC)
    if not body.consent:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Abone olmak için onay kutusunu işaretlemelisin.",
        )
    _rate_limit(request)

    email = body.email.strip().lower()
    now = datetime.now(timezone.utc)
    sub = db.scalar(select(NewsletterSubscriber).where(NewsletterSubscriber.email == email))
    if sub is None:
        sub = NewsletterSubscriber(
            email=email, token=secrets.token_urlsafe(32), source=body.source, consent_at=now
        )
        db.add(sub)
    elif sub.status == "confirmed":
        return Message(message=_GENERIC)  # zaten abone — mail atma, sızdırma
    else:
        sent = _aware(sub.confirm_sent_at)
        if sub.status == "pending" and sent is not None and now - sent < _RESEND_AFTER:
            return Message(message=_GENERIC)
        if sub.status == "unsubscribed":
            sub.token = secrets.token_urlsafe(32)
            sub.unsubscribed_at = None
        sub.status = "pending"
        sub.consent_at = now
        sub.source = body.source or sub.source

    sub.confirm_sent_at = now
    try:
        db.commit()
    except IntegrityError:  # aynı adres eşzamanlı iki kez → 500 değil, aynı yanıt
        db.rollback()
        return Message(message=_GENERIC)
    if not public_mail_budget.hit("mail"):
        logger.warning("Üyeliksiz e-posta bütçesi doldu — bülten onay maili atlandı.")
        return Message(message=_GENERIC)
    confirm_url, unsub_url = _links(sub.token)
    # SMTP yanıttan SONRA: süre farkı adresin zaten abone olup olmadığını sızdırmasın
    background.add_task(send_newsletter_confirm, email, confirm_url, unsub_url)
    return Message(message=_GENERIC)


def _redirect(path: str) -> RedirectResponse:
    return RedirectResponse(f"{_settings.frontend_base_url}{path}", status_code=303)


@router.get("/confirm")
def confirm(token: str = Query(..., max_length=64), db: Session = Depends(get_db)):
    sub = db.scalar(select(NewsletterSubscriber).where(NewsletterSubscriber.token == token))
    if sub is None or sub.status == "unsubscribed":
        return _redirect("/bulten/?durum=gecersiz")
    if sub.status != "confirmed":
        sub.status = "confirmed"
        sub.confirmed_at = datetime.now(timezone.utc)
        db.commit()
    return _redirect("/bulten/?durum=onaylandi")


def _unsubscribe(token: str, db: Session) -> bool:
    sub = db.scalar(select(NewsletterSubscriber).where(NewsletterSubscriber.token == token))
    if sub is None:
        return False
    if sub.status != "unsubscribed":
        sub.status = "unsubscribed"
        sub.unsubscribed_at = datetime.now(timezone.utc)
        db.commit()
    return True


@router.get("/unsubscribe")
def unsubscribe(token: str = Query(..., max_length=64), db: Session = Depends(get_db)):
    ok = _unsubscribe(token, db)
    return _redirect("/bulten/?durum=ayrildi" if ok else "/bulten/?durum=gecersiz")


@router.post("/unsubscribe", response_model=Message)
def unsubscribe_one_click(token: str = Query(..., max_length=64), db: Session = Depends(get_db)) -> Message:
    """RFC 8058 List-Unsubscribe-Post — posta istemcisinin 'Abonelikten çık' butonu."""
    _unsubscribe(token, db)
    return Message(message="Abonelikten çıkıldı.")
