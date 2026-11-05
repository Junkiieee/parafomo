"""Kimlik doğrulama: JWT, giriş kaba kuvveti, kayıt, Google bağlama, hesap silme."""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

import httpx
import jwt
from conftest import BACKEND, bearer, ip, register
from sqlalchemy import select, text

from app import security
from app.db import SessionLocal, engine
from app.models import (
    Goal,
    Holding,
    PasswordResetToken,
    PortfolioSnapshot,
    PriceAlert,
    Transaction,
    User,
    WatchItem,
)
from app.routers import auth as auth_router

SECRET = os.environ["PORTFOLIO_JWT_SECRET"]
_REAL_CLIENT = httpx.Client


def _b64(d: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()


def test_register_login_me(client):
    token = register(client)
    r = client.get("/auth/me", headers=bearer(token))
    assert r.status_code == 200
    assert r.json()["email"] == "a@example.com"
    assert r.headers["cache-control"] == "no-store"
    r = client.post("/auth/login", json={"email": "A@Example.com", "password": "password123"})
    assert r.status_code == 200 and r.json()["access_token"]


def test_password_is_bcrypt_hashed(client, monkeypatch):
    from conftest import REAL_GENSALT

    monkeypatch.setattr(security.bcrypt, "gensalt", REAL_GENSALT)  # canlı maliyet
    register(client)
    with SessionLocal() as db:
        h = db.scalar(select(User.password_hash))
    assert h.startswith("$2b$12$") and "password123" not in h


def test_forged_tokens_rejected(client):
    register(client)
    now = int(time.time())
    forged = [
        # alg=none
        _b64({"alg": "none", "typ": "JWT"}) + "." + _b64({"sub": "1", "exp": now + 3600}) + ".",
        # repo'daki varsayılan/şablon sırla imzalı
        jwt.encode({"sub": "1", "exp": now + 3600}, "dev-insecure-secret-change-me", algorithm="HS256"),
        jwt.encode({"sub": "1", "exp": now + 3600}, "change-me-to-a-long-random-secret", algorithm="HS256"),
        # süresi dolmuş
        jwt.encode({"sub": "1", "exp": now - 10}, SECRET, algorithm="HS256"),
        # exp yok → sonsuz token kabul edilmez
        jwt.encode({"sub": "1"}, SECRET, algorithm="HS256"),
        # taşan / bozuk sub → 500 değil 401
        jwt.encode({"sub": str(2**70), "exp": now + 3600}, SECRET, algorithm="HS256"),
        jwt.encode({"sub": "abc", "exp": now + 3600}, SECRET, algorithm="HS256"),
        "abc.def.ghi",
    ]
    for tok in forged:
        r = client.get("/auth/me", headers=bearer(tok))
        assert r.status_code == 401, (tok, r.status_code)


def test_legacy_token_without_pwv_still_valid(client):
    """Dağıtım öncesi verilmiş (pwv'siz) token'lar süreleri dolana dek çalışır."""
    register(client)
    legacy = jwt.encode({"sub": "1", "iat": int(time.time()), "exp": int(time.time()) + 600},
                        SECRET, algorithm="HS256")
    assert client.get("/auth/me", headers=bearer(legacy)).status_code == 200


def test_placeholder_secret_replaced_with_random():
    """Şablon sırla açılan süreç sahte token kabul etmesin (ayrı süreçte, ağsız)."""
    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "from app import config\n"
        "config.Settings.model_config['env_file'] = None\n"
        "from app import security\n"
        "assert security._JWT_SECRET not in ('dev-insecure-secret-change-me', '')\n"
        "assert len(security._JWT_SECRET) >= 32\n"
        "print('ok')\n" % str(BACKEND)
    )
    env = {**os.environ, "PORTFOLIO_JWT_SECRET": "dev-insecure-secret-change-me"}
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert "ok" in out.stdout
    assert "PORTFOLIO_JWT_SECRET" in out.stderr  # CRITICAL log


def test_login_same_error_and_dummy_hash_for_unknown_user(client, monkeypatch):
    register(client)
    calls = []
    real = security.dummy_verify_password
    monkeypatch.setattr(auth_router, "dummy_verify_password", lambda p: (calls.append(p), real(p)))
    wrong = client.post("/auth/login", json={"email": "a@example.com", "password": "wrong-password"})
    unknown = client.post("/auth/login", json={"email": "nobody@example.com", "password": "wrong-password"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    assert calls == ["wrong-password"]  # bilinmeyen kullanıcıda da bcrypt maliyeti ödendi


def test_login_bruteforce_locks_per_email(client):
    register(client)
    for _ in range(10):
        r = client.post("/auth/login", json={"email": "a@example.com", "password": "wrong-password"},
                        headers=ip("10.1.0.1"))
        assert r.status_code == 401
    # 11. deneme doğru şifreyle ve başka IP'den de olsa kilitli
    r = client.post("/auth/login", json={"email": "a@example.com", "password": "password123"},
                    headers=ip("10.1.0.2"))
    assert r.status_code == 429
    # kilit mesajı bilinmeyen e-posta için de aynı (varlık sızdırmaz)
    for _ in range(10):
        client.post("/auth/login", json={"email": "ghost@example.com", "password": "x" * 8},
                    headers=ip("10.1.0.3"))
    r2 = client.post("/auth/login", json={"email": "ghost@example.com", "password": "x" * 8},
                     headers=ip("10.1.0.4"))
    assert r2.status_code == 429 and r2.json() == r.json()


def test_login_success_resets_failures(client):
    register(client)
    for _ in range(9):
        client.post("/auth/login", json={"email": "a@example.com", "password": "wrong-password"})
    assert client.post("/auth/login", json={"email": "a@example.com", "password": "password123"}).status_code == 200
    for _ in range(9):
        client.post("/auth/login", json={"email": "a@example.com", "password": "wrong-password"})
    assert client.post("/auth/login", json={"email": "a@example.com", "password": "password123"}).status_code == 200


def test_login_rate_limited_per_ip(client):
    for i in range(30):
        r = client.post("/auth/login", json={"email": f"u{i}@example.com", "password": "password123"},
                        headers=ip("10.2.0.1"))
        assert r.status_code == 401
    r = client.post("/auth/login", json={"email": "z@example.com", "password": "password123"},
                    headers=ip("10.2.0.1"))
    assert r.status_code == 429
    # başka IP etkilenmez
    r = client.post("/auth/login", json={"email": "z@example.com", "password": "password123"},
                    headers=ip("10.2.0.2"))
    assert r.status_code == 401


def test_spoofed_cf_header_does_not_change_identity(client):
    for i in range(30):
        client.post("/auth/login", json={"email": f"u{i}@example.com", "password": "password123"},
                    headers={**ip("10.3.0.1"), "CF-Connecting-IP": f"203.0.113.{i}"})
    r = client.post("/auth/login", json={"email": "z@example.com", "password": "password123"},
                    headers={**ip("10.3.0.1"), "CF-Connecting-IP": "203.0.113.250"})
    assert r.status_code == 429


def test_login_password_length_capped(client):
    r = client.post("/auth/login", json={"email": "a@example.com", "password": "x" * 129})
    assert r.status_code == 422


def test_register_rate_limited_per_ip(client):
    for i in range(10):
        register(client, email=f"r{i}@example.com", addr="10.4.0.1")
    r = client.post("/auth/register", json={"email": "r99@example.com", "password": "password123"},
                    headers=ip("10.4.0.1"))
    assert r.status_code == 429


def test_register_duplicate_is_409(client):
    register(client)
    r = client.post("/auth/register", json={"email": "A@EXAMPLE.com", "password": "password123"})
    assert r.status_code == 409


def test_google_link_invalidates_preexisting_password(client, monkeypatch):
    """Ön-ele geçirme: saldırgan kurbanın adresiyle kayıt olur; kurban Google ile gelince
    saldırganın parolası ve oturumu geçersizleşmeli."""
    attacker_token = register(client, email="victim@gmail.com", password="attacker-pass")
    monkeypatch.setattr(auth_router, "verify_google_id_token",
                        lambda cred: {"sub": "g-123", "email": "victim@gmail.com", "name": "V", "email_verified": True})
    r = client.post("/auth/google", json={"credential": "x" * 50})
    assert r.status_code == 200
    victim_token = r.json()["access_token"]
    assert client.get("/auth/me", headers=bearer(victim_token)).status_code == 200
    assert client.get("/auth/me", headers=bearer(attacker_token)).status_code == 401
    r = client.post("/auth/login", json={"email": "victim@gmail.com", "password": "attacker-pass"})
    assert r.status_code == 401
    # Sonraki Google girişleri hesabı değiştirmez
    assert client.post("/auth/google", json={"credential": "x" * 50}).status_code == 200
    with SessionLocal() as db:
        assert db.scalar(select(User.google_sub)) == "g-123"


def test_google_rejects_bad_verification(client, monkeypatch):
    monkeypatch.setattr(auth_router, "verify_google_id_token", lambda cred: None)
    assert client.post("/auth/google", json={"credential": "abc"}).status_code == 401
    assert client.post("/auth/google", json={"credential": "x" * 9000}).status_code == 422


def test_google_tokeninfo_checks_audience_and_issuer(monkeypatch):
    def fake_client(payload):
        def handler(request):
            return httpx.Response(200, json=payload)
        return lambda *a, **kw: _REAL_CLIENT(transport=httpx.MockTransport(handler))

    base = {"aud": "test-google-client", "iss": "https://accounts.google.com", "sub": "1",
            "email": "g@example.com", "email_verified": "true"}
    monkeypatch.setattr(security.httpx, "Client", fake_client(base))
    assert security.verify_google_id_token("tok")["email"] == "g@example.com"
    for bad in ({"aud": "other-client"}, {"iss": "https://evil.example"}, {"email_verified": "false"}):
        monkeypatch.setattr(security.httpx, "Client", fake_client({**base, **bad}))
        assert security.verify_google_id_token("tok") is None


def test_google_tokeninfo_network_failure_is_none():
    # no_network: httpx bağlantısı hata verir → None, istisna sızmaz
    assert security.verify_google_id_token("tok") is None


def test_delete_account_removes_all_rows(client, outbox):
    token = register(client)
    other = register(client, email="b@example.com")
    h = bearer(token)
    client.post("/portfolio/transactions", headers=h, json={
        "asset_type": "cash", "symbol": "cash", "side": "buy", "quantity": 100, "price": 1})
    client.post("/portfolio/goals", headers=h, json={"kind": "try", "target": 1000})
    client.post("/portfolio/watchlist", headers=h, json={"asset_type": "cash", "symbol": "x"})
    client.post("/portfolio/alerts", headers=h, json={
        "asset_type": "cash", "symbol": "x", "direction": "above", "threshold": 2})
    client.get("/portfolio/summary", headers=h)  # günün snapshot'ı
    client.post("/auth/request-password-reset", json={"email": "a@example.com"})
    with SessionLocal() as db:
        uid = db.scalar(select(User.id).where(User.email == "a@example.com"))
        for model in (Holding, Transaction, PortfolioSnapshot, PriceAlert, Goal, WatchItem, PasswordResetToken):
            assert db.scalar(select(model).where(model.user_id == uid)) is not None, model

    assert client.delete("/auth/me", headers=h).status_code == 204
    assert client.get("/auth/me", headers=h).status_code == 401
    with SessionLocal() as db:
        assert db.scalar(select(User).where(User.id == uid)) is None
        for model in (Holding, Transaction, PortfolioSnapshot, PriceAlert, Goal, WatchItem, PasswordResetToken):
            assert db.scalar(select(model).where(model.user_id == uid)) is None, model
    assert client.get("/auth/me", headers=bearer(other)).status_code == 200


def test_delete_account_works_without_db_cascade(client):
    """Canlı DB'de bir tablo ON DELETE CASCADE'siz oluşturulmuş olsa da silme çalışmalı."""
    token = register(client)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE portfolio_snapshots"))
        conn.execute(text(
            "CREATE TABLE portfolio_snapshots (id INTEGER PRIMARY KEY, "
            "user_id INTEGER NOT NULL REFERENCES users(id), day DATE NOT NULL, "
            "total_value FLOAT NOT NULL, total_cost FLOAT NOT NULL, created_at DATETIME)"))
        conn.execute(text("INSERT INTO portfolio_snapshots (user_id, day, total_value, total_cost) "
                          "VALUES (1, '2026-01-01', 1, 1)"))
    assert client.delete("/auth/me", headers=bearer(token)).status_code == 204
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM portfolio_snapshots")).scalar() == 0
        assert conn.execute(text("SELECT count(*) FROM users")).scalar() == 0


def test_reset_tokens_cleanup_keeps_recent(client, outbox):
    register(client)
    with SessionLocal() as db:
        old = datetime.now(timezone.utc) - timedelta(days=3)
        db.add(PasswordResetToken(user_id=1, token_hash="0" * 64, expires_at=old))
        db.commit()
    client.post("/auth/request-password-reset", json={"email": "a@example.com"})
    with SessionLocal() as db:
        hashes = list(db.scalars(select(PasswordResetToken.token_hash)))
    assert "0" * 64 not in hashes and len(hashes) == 1
