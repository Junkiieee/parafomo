"""Bülten: hız sınırı atlatılamaz, mail bombardımanı yok, çift onay akışı."""
from __future__ import annotations

from conftest import ip
from sqlalchemy import select

from app import config, ratelimit
from app.db import SessionLocal
from app.models import NewsletterSubscriber


def _sub(client, email, headers=None):
    return client.post("/newsletter/subscribe", json={"email": email, "consent": True, "source": "/t"},
                       headers=headers or {})


def test_spoofed_cf_connecting_ip_does_not_bypass_limit(client, outbox):
    codes = [
        _sub(client, f"s{i}@example.com", {**ip("10.5.0.1"), "CF-Connecting-IP": f"198.51.100.{i}"}).status_code
        for i in range(8)
    ]
    assert codes[:5] == [200] * 5 and set(codes[5:]) == {429}
    assert len(outbox) == 5


def test_cf_header_honoured_only_when_configured(client, outbox, monkeypatch):
    monkeypatch.setattr(config.get_settings(), "trust_cf_connecting_ip", True)
    codes = [
        _sub(client, f"t{i}@example.com", {**ip("10.5.0.2"), "CF-Connecting-IP": f"198.51.100.{i}"}).status_code
        for i in range(8)
    ]
    assert codes == [200] * 8


def test_same_address_not_mail_bombed(client, outbox):
    for i in range(4):
        assert _sub(client, "v@example.com", ip(f"10.5.1.{i}")).status_code == 200
    assert len(outbox) == 1  # 10 dk içinde tek onay maili


def test_confirmed_address_gets_no_mail_and_same_response(client, outbox):
    first = _sub(client, "w@example.com", ip("10.5.2.1"))
    token = outbox[0]["body"].split("confirm?token=")[1].split()[0]
    r = client.get("/newsletter/confirm", params={"token": token}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].endswith("durum=onaylandi")
    again = _sub(client, "w@example.com", ip("10.5.2.2"))
    assert again.json() == first.json() and len(outbox) == 1


def test_unsubscribe_and_resubscribe_rotates_token(client, outbox):
    _sub(client, "u@example.com", ip("10.5.3.1"))
    with SessionLocal() as db:
        old = db.scalar(select(NewsletterSubscriber.token))
    r = client.post("/newsletter/unsubscribe", params={"token": old})
    assert r.status_code == 200
    _sub(client, "u@example.com", ip("10.5.3.2"))
    with SessionLocal() as db:
        sub = db.scalar(select(NewsletterSubscriber))
    assert sub.status == "pending" and sub.token != old
    r = client.get("/newsletter/confirm", params={"token": old}, follow_redirects=False)
    assert r.headers["location"].endswith("durum=gecersiz")


def test_honeypot_and_consent(client, outbox):
    r = client.post("/newsletter/subscribe", json={"email": "bot@example.com", "consent": True, "website": "x"})
    assert r.status_code == 200 and outbox == []
    r = client.post("/newsletter/subscribe", json={"email": "n@example.com", "consent": False})
    assert r.status_code == 422 and isinstance(r.json()["detail"], str)


def test_global_mail_budget_caps_confirmations(client, outbox, monkeypatch):
    monkeypatch.setattr(ratelimit.public_mail_budget.hour, "limit", 3)
    for i in range(6):
        assert _sub(client, f"g{i}@example.com", ip(f"10.5.4.{i}")).status_code == 200
    assert len(outbox) == 3


def test_token_query_length_capped(client):
    assert client.get("/newsletter/confirm", params={"token": "x" * 65}, follow_redirects=False).status_code == 422
