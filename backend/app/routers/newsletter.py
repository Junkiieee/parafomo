"""Bülten aboneliği — çift onay (double opt-in), kendi altyapımız.

POST /newsletter/subscribe   → kayıt (pending) + onay maili (Brevo SMTP)
GET  /newsletter/confirm     → token ile confirmed, siteye yönlendirir
GET/POST /newsletter/unsubscribe → token ile unsubscribed (POST: RFC 8058 tek-tık)

Hesabın varlığı sızdırılmaz: subscribe her durumda aynı yanıtı döner.
"""
from __future__ import annotations

import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..mailer import send_newsletter_confirm
from ..models import NewsletterSubscriber
from ..schemas import Message, NewsletterSubscribe

router = APIRouter(prefix="/newsletter", tags=["newsletter"])
_settings = get_settings()

# IP başına 10 dakikada 5 kayıt denemesi
_WINDOW = 600
_LIMIT = 5
_hits: dict[str, deque] = defaultdict(deque)
# Aynı adrese onay maili en sık bu aralıkla yeniden gider
_RESEND_AFTER = timedelta(minutes=10)

_GENERIC = "Neredeyse tamam! Gelen kutuna onay e-postası gönderdik — linke tıklayınca aboneliğin başlar."


def _client_ip(request: Request) -> str:
    # Cloudflare arkasında gerçek IP bu başlıkta
    return request.headers.get("cf-connecting-ip") or (
        request.client.host if request.client else "?"
    )


def _rate_limit(request: Request) -> None:
    ip = _client_ip(request)
    now = time.time()
    q = _hits[ip]
    while q and now - q[0] > _WINDOW:
        q.popleft()
    if len(q) >= _LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Çok fazla deneme. Lütfen birkaç dakika sonra tekrar dene.",
        )
    q.append(now)


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
    body: NewsletterSubscribe, request: Request, db: Session = Depends(get_db)
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
    db.commit()
    confirm_url, unsub_url = _links(sub.token)
    send_newsletter_confirm(email, confirm_url, unsub_url)
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
