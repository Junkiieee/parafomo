"""Gelen kutusu: sabit-zamanlı sır karşılaştırması, boyut sınırı, güvenli dosya yazımı."""
from __future__ import annotations

import stat
from pathlib import Path

from app import config
from app.routers import inbox as inbox_router

SECRET = "inbox-test-secret"


def _files():
    root = Path(config.get_settings().inbox_dir)
    return sorted(root.rglob("*.eml")) if root.exists() else []


def test_disabled_without_secret(client, monkeypatch):
    monkeypatch.setattr(config.get_settings(), "inbox_secret", "")
    r = client.post("/inbox/ingest", content=b"x", headers={"X-Inbox-Secret": ""})
    assert r.status_code == 503


def test_wrong_or_missing_secret(client):
    before = len(_files())
    assert client.post("/inbox/ingest", content=b"From: a\r\n\r\nhi").status_code == 403
    assert client.post("/inbox/ingest", content=b"x", headers={"X-Inbox-Secret": "nope"}).status_code == 403
    assert client.post("/inbox/ingest", content=b"x", headers={"X-Inbox-Secret": SECRET + "x"}).status_code == 403
    assert len(_files()) == before


def test_secret_compared_in_constant_time(client, monkeypatch):
    calls = []
    real = inbox_router.hmac.compare_digest
    monkeypatch.setattr(inbox_router.hmac, "compare_digest", lambda a, b: (calls.append(1), real(a, b))[1])
    client.post("/inbox/ingest", content=b"x", headers={"X-Inbox-Secret": "nope"})
    assert calls


def test_stores_mail_owner_only_and_strips_header_injection(client):
    before = set(_files())
    r = client.post("/inbox/ingest", content=b"From: a@example.com\r\nSubject: hi\r\n\r\nbody",
                    headers={"X-Inbox-Secret": SECRET, "X-Mail-From": "a@example.com\tX-Evil: 1",
                             "X-Mail-To": "ajan@parafomo.com"})
    assert r.status_code == 204
    new = set(_files()) - before
    assert len(new) == 1
    f = new.pop()
    assert stat.S_IMODE(f.stat().st_mode) == 0o600
    data = f.read_bytes()
    assert data.startswith(b"X-Envelope-From: a@example.comX-Evil: 1\r\nX-Envelope-To: ajan@parafomo.com\r\n")
    assert data.endswith(b"body")
    # dosya adı sunucuda üretilir (yol geçişi yok)
    assert f.parent.parent == Path(config.get_settings().inbox_dir)


def test_envelope_value_sanitizer():
    assert inbox_router._envelope_value("a@b.c\r\nBcc: x@y.z") == "a@b.cBcc: x@y.z"
    assert len(inbox_router._envelope_value("a" * 1000)) == 320


def test_size_limits(client):
    assert client.post("/inbox/ingest", content=b"", headers={"X-Inbox-Secret": SECRET}).status_code == 413
    big = b"x" * (5 * 1024 * 1024 + 1)
    assert client.post("/inbox/ingest", content=big, headers={"X-Inbox-Secret": SECRET}).status_code == 413
    huge = b"x" * (6 * 1024 * 1024 + 1)  # ara katman sınırı: gövde belleğe okunmadan
    assert client.post("/inbox/ingest", content=huge, headers={"X-Inbox-Secret": SECRET}).status_code == 413
