"""ajan@parafomo.com gelen kutusu — Cloudflare Email Worker buraya POST eder.

Akış: Email Routing (ajan@ → worker `parafomo`) → worker/index.js `email()` → bu uç →
ham .eml dosyası `inbox_dir/YYYY-MM-DD/` altına. Okuma: `python3 scripts/inbox.py`.
Repo herkese açık; paylaşılan anahtar yalnız backend/.env (PORTFOLIO_INBOX_SECRET) ve
Cloudflare worker secret'ında (INBOX_SECRET) durur. Anahtar boşsa uç kapalıdır.
"""
from __future__ import annotations

import hmac
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request, Response, status

from ..config import get_settings

router = APIRouter(prefix="/inbox", tags=["inbox"])

_MAX_BYTES = 5 * 1024 * 1024
_CTRL = re.compile(r"[\x00-\x1f\x7f]")


def _envelope_value(value: str) -> str:
    # Zarf adresi .eml başlığına yazılır: CR/LF ile sahte başlık eklenemesin
    return _CTRL.sub("", value)[:320]


@router.post("/ingest", status_code=status.HTTP_204_NO_CONTENT)
async def ingest(
    request: Request,
    x_inbox_secret: str = Header(default=""),
    x_mail_from: str = Header(default=""),
    x_mail_to: str = Header(default=""),
) -> Response:
    settings = get_settings()
    if not settings.inbox_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="inbox kapalı")
    if not hmac.compare_digest(x_inbox_secret.encode(), settings.inbox_secret.encode()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    raw = await request.body()
    if not raw or len(raw) > _MAX_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    now = datetime.now(timezone.utc)
    day = Path(settings.inbox_dir) / now.strftime("%Y-%m-%d")
    day.mkdir(mode=0o700, parents=True, exist_ok=True)
    name = f"{now.strftime('%H%M%S')}-{secrets.token_hex(4)}.eml"
    envelope = (
        f"X-Envelope-From: {_envelope_value(x_mail_from)}\r\n"
        f"X-Envelope-To: {_envelope_value(x_mail_to)}\r\n"
    ).encode()
    # Kişisel veri (gelen mail): yalnız sahibi okuyabilsin
    fd = os.open(day / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(envelope + raw)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
