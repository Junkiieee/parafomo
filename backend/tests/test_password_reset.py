"""Şifre sıfırlama: sızdırmazlık, tek kullanım, süre, oturum düşürme, mail bombardımanı."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from conftest import bearer, ip, register
from sqlalchemy import select, update

from app import ratelimit
from app.db import SessionLocal
from app.models import PasswordResetToken

GENERIC = "Eğer bu e-posta kayıtlıysa, şifre sıfırlama bağlantısı gönderildi."


def _request(client, email="a@example.com", addr="10.9.0.1"):
    return client.post("/auth/request-password-reset", json={"email": email}, headers=ip(addr))


def _token_from(mail: dict) -> str:
    m = re.search(r"/portfoy/sifre-sifirla\?token=([A-Za-z0-9_\-]+)", mail["body"])
    assert m, mail["body"]
    return m.group(1)


def test_same_response_for_known_and_unknown(client, outbox):
    register(client)
    known = _request(client)
    unknown = _request(client, email="nobody@example.com")
    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json() == {"message": GENERIC}
    assert [m["to"] for m in outbox] == ["a@example.com"]
    assert outbox[0]["body"].count("https://parafomo.com/portfoy/sifre-sifirla?token=") == 1


def test_token_entropy_and_hashed_storage(client, outbox):
    register(client)
    _request(client)
    raw = _token_from(outbox[0])
    assert len(raw) >= 43  # token_urlsafe(32) = 256 bit
    with SessionLocal() as db:
        stored = db.scalar(select(PasswordResetToken.token_hash))
    assert raw not in stored and len(stored) == 64


def test_reset_is_single_use_and_revokes_sessions(client, outbox):
    old_session = register(client)
    _request(client)
    _request(client)
    first, second = _token_from(outbox[0]), _token_from(outbox[1])

    r = client.post("/auth/reset-password", json={"token": second, "new_password": "new-password-1"})
    assert r.status_code == 200
    new_session = r.json()["access_token"]

    # aynı token ikinci kez çalışmaz
    again = client.post("/auth/reset-password", json={"token": second, "new_password": "new-password-2"})
    assert again.status_code == 400
    # aynı kullanıcının diğer açık bağlantısı da kapandı
    other = client.post("/auth/reset-password", json={"token": first, "new_password": "new-password-3"})
    assert other.status_code == 400
    # eski oturum düştü, yenisi geçerli
    assert client.get("/auth/me", headers=bearer(old_session)).status_code == 401
    assert client.get("/auth/me", headers=bearer(new_session)).status_code == 200
    # yeni şifre geçerli, eskisi değil
    assert client.post("/auth/login", json={"email": "a@example.com", "password": "new-password-1"}).status_code == 200
    assert client.post("/auth/login", json={"email": "a@example.com", "password": "password123"}).status_code == 401


def test_successful_reset_clears_login_lock(client, outbox):
    register(client)
    for _ in range(10):  # saldırgan kurbanın girişini kilitler
        client.post("/auth/login", json={"email": "a@example.com", "password": "wrong-password"},
                    headers=ip("10.9.5.1"))
    assert client.post("/auth/login", json={"email": "a@example.com", "password": "password123"}).status_code == 429
    _request(client)
    r = client.post("/auth/reset-password", json={"token": _token_from(outbox[0]), "new_password": "new-password-1"})
    assert r.status_code == 200
    assert client.post("/auth/login", json={"email": "a@example.com", "password": "new-password-1"}).status_code == 200


def test_expired_token_rejected(client, outbox):
    register(client)
    _request(client)
    raw = _token_from(outbox[0])
    with SessionLocal() as db:
        db.execute(update(PasswordResetToken).values(
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)))
        db.commit()
    r = client.post("/auth/reset-password", json={"token": raw, "new_password": "new-password-1"})
    assert r.status_code == 400


def test_bad_tokens_rejected(client):
    register(client)
    for tok in ("", "x", "a" * 256):
        r = client.post("/auth/reset-password", json={"token": tok, "new_password": "new-password-1"})
        assert r.status_code == 400
    r = client.post("/auth/reset-password", json={"token": "a" * 257, "new_password": "new-password-1"})
    assert r.status_code == 422
    r = client.post("/auth/reset-password", json={"token": "abc", "new_password": "short"})
    assert r.status_code == 422


def test_no_mail_bombing_same_address(client, outbox):
    register(client)
    for i in range(6):
        r = _request(client, addr=f"10.9.1.{i}")  # farklı IP'ler
        assert r.status_code == 200 and r.json()["message"] == GENERIC
    assert len(outbox) == 3  # aynı adrese saatte en çok 3


def test_reset_request_rate_limited_per_ip(client, outbox):
    for i in range(10):
        assert _request(client, email=f"x{i}@example.com", addr="10.9.2.1").status_code == 200
    assert _request(client, email="y@example.com", addr="10.9.2.1").status_code == 429


def test_global_public_mail_budget(client, outbox, monkeypatch):
    for i in range(4):
        register(client, email=f"u{i}@example.com")
    monkeypatch.setattr(ratelimit.public_mail_budget.hour, "limit", 2)
    for i in range(4):
        assert _request(client, email=f"u{i}@example.com", addr=f"10.9.3.{i}").status_code == 200
    assert len(outbox) == 2


def test_google_only_account_can_set_password_via_reset(client, outbox, monkeypatch):
    from app.routers import auth as auth_router

    monkeypatch.setattr(auth_router, "verify_google_id_token",
                        lambda cred: {"sub": "g-1", "email": "g@example.com", "name": None, "email_verified": True})
    assert client.post("/auth/google", json={"credential": "c"}).status_code == 200
    _request(client, email="g@example.com")
    assert len(outbox) == 1
    r = client.post("/auth/reset-password", json={"token": _token_from(outbox[0]), "new_password": "new-password-1"})
    assert r.status_code == 200
    assert client.post("/auth/login", json={"email": "g@example.com", "password": "new-password-1"}).status_code == 200


def test_mail_queued_after_response_not_inline(client, monkeypatch):
    """SMTP süresi yanıt süresine eklenmesin (zamanlamayla hesap tespiti): gönderim
    yanıttan sonra çalışan BackgroundTasks kuyruğuna girer, uç içinde çağrılmaz."""
    from fastapi import BackgroundTasks
    from starlette.requests import Request

    from app.routers import auth as auth_router
    from app.schemas import PasswordResetRequest

    register(client)
    inline = []
    monkeypatch.setattr(auth_router, "send_password_reset", lambda *a: inline.append(a))
    bt = BackgroundTasks()
    req = Request({"type": "http", "headers": [], "client": ("10.9.4.1", 1)})
    with SessionLocal() as db:
        out = auth_router.request_password_reset(PasswordResetRequest(email="a@example.com"), req, bt, db)
    assert out.message == GENERIC
    assert inline == []
    assert len(bt.tasks) == 1 and bt.tasks[0].args[0] == "a@example.com"
