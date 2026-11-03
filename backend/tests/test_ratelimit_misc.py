"""Hız sınırlayıcı birim testleri + CORS + güvenlik başlıkları + 422 gövdesi."""
from __future__ import annotations

from starlette.requests import Request

from app import config
from app.ratelimit import RateLimiter, client_ip


def _req(host, headers=None):
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    return Request({"type": "http", "headers": raw, "client": (host, 1)})


def test_client_ip_ignores_cf_header_by_default():
    assert client_ip(_req("203.0.113.5", {"CF-Connecting-IP": "1.1.1.1"})) == "203.0.113.5"


def test_client_ip_cf_header_when_trusted(monkeypatch):
    monkeypatch.setattr(config.get_settings(), "trust_cf_connecting_ip", True)
    assert client_ip(_req("172.70.0.1", {"CF-Connecting-IP": "1.1.1.1"})) == "1.1.1.1"
    assert client_ip(_req("172.70.0.1")) == "172.70.0.1"


def test_client_ip_ipv6_grouped_by_64():
    a = client_ip(_req("2001:db8:1:2:aaaa::1"))
    b = client_ip(_req("2001:db8:1:2:ffff::9"))
    assert a == b == "2001:db8:1:2::/64"
    assert client_ip(_req("2001:db8:1:3::1")) != a
    assert client_ip(_req("::ffff:198.51.100.7")) == "198.51.100.7"


def test_limiter_window_and_reset():
    lim = RateLimiter(limit=2, window=60)
    assert lim.hit("k") and lim.hit("k") and not lim.hit("k")
    assert lim.allowed("other") and not lim.allowed("k")
    lim.reset("k")
    assert lim.hit("k")


def test_limiter_memory_bounded():
    lim = RateLimiter(limit=1, window=60, max_keys=100)
    for i in range(10_000):
        lim.hit(f"ip{i}")
    assert len(lim._hits) <= 101


def test_cors_only_allowed_origins(client):
    bad = client.options("/auth/login", headers={"Origin": "https://evil.example",
                                                 "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in bad.headers
    good = client.options("/auth/login", headers={"Origin": "https://app.parafomo.com",
                                                  "Access-Control-Request-Method": "POST",
                                                  "Access-Control-Request-Headers": "authorization,content-type"})
    assert good.status_code == 200
    assert good.headers["access-control-allow-origin"] == "https://app.parafomo.com"
    r = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in r.headers


def test_security_headers(client):
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert "cache-control" not in r.headers
    r = client.get("/portfolio/holdings")
    assert r.headers["cache-control"] == "no-store"


def test_validation_error_with_nan_is_json(client):
    r = client.post("/auth/register", content=b'{"email":"a@example.com","password":NaN}',
                    headers={"Content-Type": "application/json"})
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"] == ["body", "password"]


def test_mail_budget_hourly_and_daily():
    from app.ratelimit import MailBudget

    b = MailBudget(per_hour=3, per_day=5)
    assert [b.hit() for _ in range(4)] == [True, True, True, False]
    b.hour.clear()  # saat döndü: günlük sınır hâlâ geçerli
    assert [b.hit() for _ in range(3)] == [True, True, False]
    assert MailBudget(per_hour=0, per_day=10).hit() is False
