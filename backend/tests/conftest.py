"""Test ortamı: ağsız, geçici DB, gerçek backend/.env'e dokunmaz.

Ayarlar app modülleri import edilmeden ÖNCE ortam değişkeniyle verilir (get_settings
lru_cache'li ve modüller import anında okuyor). Dış ağ (httpx, SMTP, soket) tamamen
kapalıdır; fiyat/mail davranışı testlerde taklit edilir.
"""
from __future__ import annotations

import atexit
import os
import shutil
import socket
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

_TMP = Path(tempfile.mkdtemp(prefix="parafomo-tests-"))
atexit.register(shutil.rmtree, _TMP, ignore_errors=True)
os.environ.update({
    "PORTFOLIO_DB_PATH": str(_TMP / "test.db"),
    "PORTFOLIO_JWT_SECRET": "test-jwt-secret-0123456789abcdef0123456789abcdef",
    "PORTFOLIO_JWT_EXPIRE_MINUTES": "60",
    "PORTFOLIO_INBOX_SECRET": "inbox-test-secret",
    "PORTFOLIO_INBOX_DIR": str(_TMP / "inbox"),
    "PORTFOLIO_SMTP_HOST": "",
    "PORTFOLIO_GOOGLE_CLIENT_ID": "test-google-client",
    "PORTFOLIO_CORS_ORIGINS": "https://app.parafomo.com,https://parafomo.com",
    "PORTFOLIO_FRONTEND_BASE_URL": "https://parafomo.com",
    "PORTFOLIO_TRUST_CF_CONNECTING_IP": "false",
    "PORTFOLIO_PUBLIC_MAIL_PER_HOUR": "100",
    "PORTFOLIO_PUBLIC_MAIL_PER_DAY": "1000",
})

from app import config  # noqa: E402

# Sunucuda çalıştırılsa bile gerçek backend/.env (SMTP şifresi, canlı DB yolu) okunmasın
config.Settings.model_config["env_file"] = None
config.get_settings.cache_clear()

import bcrypt  # noqa: E402
import httpx  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware  # noqa: E402

from app import mailer, prices, ratelimit, security  # noqa: E402
from app.db import Base, engine  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.routers import auth as auth_router  # noqa: E402
from app.routers import newsletter as newsletter_router  # noqa: E402
from app.routers import public as public_router  # noqa: E402

assert config.get_settings().db_path.startswith(str(_TMP)), "testler geçici DB dışına yazmamalı"


class NetworkBlocked(OSError):
    pass


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Gerçek dış bağlantı yok: httpx taşıması ve soket bağlantısı hata verir."""
    calls: list[str] = []

    def blocked_transport(self, request):
        calls.append(str(request.url))
        raise httpx.ConnectError("ağ testlerde kapalı", request=request)

    real_connect = socket.socket.connect
    real_create = socket.create_connection
    loopback = {"127.0.0.1", "::1", "localhost"}

    def guarded_connect(self, address):
        # yerel geri döngü serbest (bazı platformlarda event loop socketpair'i böyle kurar)
        if isinstance(address, tuple) and address and address[0] in loopback:
            return real_connect(self, address)
        raise NetworkBlocked("ağ testlerde kapalı")

    def guarded_create(address, *args, **kwargs):
        if address and address[0] in loopback:
            return real_create(address, *args, **kwargs)
        raise NetworkBlocked("ağ testlerde kapalı")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked_transport)
    monkeypatch.setattr(socket, "create_connection", guarded_create)
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    return calls


REAL_GENSALT = bcrypt.gensalt


@pytest.fixture(autouse=True)
def fast_bcrypt(monkeypatch):
    """Testler hızlı olsun: bcrypt maliyeti 4 (canlı 12 — test_auth bunu ayrıca doğrular)."""
    monkeypatch.setattr(security.bcrypt, "gensalt", lambda rounds=4, prefix=b"2b": REAL_GENSALT(4, prefix))


@pytest.fixture(autouse=True)
def clean_state():
    """Her test temiz DB, sıfır hız sınırı sayacı ve boş fiyat cache'iyle başlar."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    for mod in (auth_router, newsletter_router, public_router, ratelimit):
        for value in vars(mod).values():
            if isinstance(value, (ratelimit.RateLimiter, ratelimit.MailBudget)):
                value.clear()
    prices._CACHE.clear()
    prices._FAILED.clear()
    prices._HIST_CACHE.clear()
    prices._TRUNCGIL_DOC = None
    public_router._NEWS_CACHE.clear()
    yield


@pytest.fixture
def outbox(monkeypatch):
    """Gönderilen e-postaları yakala (SMTP'ye gitmez)."""
    sent: list[dict] = []

    def fake_send(to, subject, body):
        sent.append({"to": to, "subject": subject, "body": body})
        return True

    monkeypatch.setattr(mailer, "send_email", fake_send)
    return sent


@pytest.fixture
def client():
    # Canlıdaki gibi: Caddy → uvicorn proxy-headers. X-Forwarded-For ile istemci IP'si verilir.
    wrapped = ProxyHeadersMiddleware(fastapi_app, trusted_hosts="testclient")
    with TestClient(wrapped) as c:
        yield c


def ip(addr: str) -> dict:
    return {"X-Forwarded-For": addr}


def register(client, email="a@example.com", password="password123", addr="10.0.0.1") -> str:
    r = client.post("/auth/register", json={"email": email, "password": password}, headers=ip(addr))
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
