"""ajan@parafomo.com gelen kutusu — Cloudflare Email Worker buraya POST eder.

Akış: Email Routing (ajan@ → worker `parafomo`) → worker/index.js `email()` → bu uç →
ham .eml dosyası `inbox_dir/YYYY-MM-DD/` altına. Okuma: `python3 scripts/inbox.py`.
Repo herkese açık; paylaşılan anahtar yalnız backend/.env (PORTFOLIO_INBOX_SECRET) ve
Cloudflare worker secret'ında (INBOX_SECRET) durur. Anahtar boşsa uç kapalıdır.
"""
from __future__ import annotations

import hmac
import secrets
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request, Response, status

from ..config import get_settings

router = APIRouter(prefix="/inbox", tags=["inbox"])

_MAX_BYTES = 5 * 1024 * 1024


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
    day.mkdir(parents=True, exist_ok=True)
    name = f"{now.strftime('%H%M%S')}-{secrets.token_hex(4)}.eml"
    envelope = f"X-Envelope-From: {x_mail_from[:320]}\r\nX-Envelope-To: {x_mail_to[:320]}\r\n".encode()
    (day / name).write_bytes(envelope + raw)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
