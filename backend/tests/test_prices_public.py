"""Fiyat servisi + halka açık uçlar: SSRF'siz URL, zaman aşımında asılmama, bozuk veri, hız sınırı."""
from __future__ import annotations

import time

import httpx
import pytest
from conftest import bearer, ip, register

from app import prices
from app.models import AssetType

_REAL_CLIENT = httpx.Client


@pytest.fixture
def fake_net(monkeypatch):
    """prices.httpx.Client → MockTransport. handler(request) testte atanır; istekler kaydedilir."""
    state = {"handler": None, "requests": []}

    def handler(request):
        state["requests"].append(request)
        return state["handler"](request)

    monkeypatch.setattr(prices.httpx, "Client",
                        lambda *a, **kw: _REAL_CLIENT(transport=httpx.MockTransport(handler)))
    return state


def _yahoo_ok(price=100.0, prev=95.0):
    return httpx.Response(200, json={"chart": {"result": [{"meta": {
        "regularMarketPrice": price, "previousClose": prev}}]}})


def test_bist_url_is_fixed_host_and_path(fake_net):
    fake_net["handler"] = lambda r: _yahoo_ok()
    assert prices.get_quote(AssetType.BIST, " thyao ")[0] == 100.0
    req = fake_net["requests"][0]
    assert req.url.host == "query1.finance.yahoo.com"
    assert req.url.path == "/v8/finance/chart/THYAO.IS" and not req.url.query


@pytest.mark.parametrize("sym", ["../../v7/finance/quote?symbols=X#", "A?range=max", "A/B", "A B", "", "Ş"])
def test_unsafe_symbols_never_fetched(fake_net, sym):
    fake_net["handler"] = lambda r: _yahoo_ok()
    assert prices.get_quote(AssetType.BIST, sym) is None
    assert prices.get_bist_history(sym, "1y") is None
    assert fake_net["requests"] == []


def test_history_params_are_encoded(fake_net):
    fake_net["handler"] = lambda r: httpx.Response(200, json={"chart": {"result": [{
        "timestamp": [1700000000, 1700086400, None],
        "indicators": {"quote": [{"close": [10.0, None, 12.0]}]}}]}})
    pts = prices.get_bist_history("THYAO", "1y")
    assert pts == [{"t": "2023-11-14", "p": 10.0}]
    q = dict(fake_net["requests"][0].url.params)
    assert q == {"range": "1y", "interval": "1d"}


def test_timeout_marks_source_down_so_requests_do_not_pile_up(fake_net):
    def hang(request):
        raise httpx.ReadTimeout("asılı", request=request)

    fake_net["handler"] = hang
    for sym in ("AKBNK", "GARAN", "THYAO", "TUPRS"):
        assert prices.get_quote(AssetType.BIST, sym) is None
    assert len(fake_net["requests"]) == 1  # ilki zaman aşımı, gerisi beklemeden None


def test_fast_failure_only_skips_that_symbol(fake_net):
    fake_net["handler"] = lambda r: httpx.Response(404) if "XXXXX" in r.url.path else _yahoo_ok()
    assert prices.get_quote(AssetType.BIST, "XXXXX") is None
    assert prices.get_quote(AssetType.BIST, "XXXXX") is None  # negatif cache: tekrar istek yok
    assert prices.get_quote(AssetType.BIST, "AKBNK")[0] == 100.0
    assert len(fake_net["requests"]) == 2


@pytest.mark.parametrize("payload", [
    {"chart": {"result": [{"meta": {"regularMarketPrice": "NaN"}}]}},
    {"chart": {"result": [{"meta": {"regularMarketPrice": float("inf")}}]}},
    {"chart": {"result": []}},
    {"chart": None},
    [],
    "x",
])
def test_garbage_from_source_is_none(fake_net, payload):
    fake_net["handler"] = lambda r: httpx.Response(200, content=__import__("json").dumps(payload).encode())
    assert prices.get_quote(AssetType.BIST, "THYAO") is None


def test_truncgil_fetched_once_for_all_metals_and_fx(fake_net):
    fake_net["handler"] = lambda r: httpx.Response(200, json={
        "gram-altin": {"Selling": "3.250,50", "Change": "%0,43"},
        "gumus": {"Selling": "41,20", "Change": "%-1,2"},
        "USD": {"Selling": "41,95", "Change": "%0,1"},
        "EUR": {"Selling": "48,10", "Change": "%0,2"},
    })
    assert prices.get_quote(AssetType.GOLD, "GOLD") == (3250.5, 0.43)
    assert prices.get_quote(AssetType.SILVER, "SILVER") == (41.2, -1.2)
    assert prices.get_quote(AssetType.USD, "USD")[0] == 41.95
    assert prices.get_usd_try() == 41.95
    assert len(fake_net["requests"]) == 1


def test_truncgil_bad_shapes(fake_net):
    fake_net["handler"] = lambda r: httpx.Response(200, json={"gram-altin": "x", "USD": {"Selling": "Infinity"}})
    assert prices.get_quote(AssetType.GOLD, "GOLD") is None
    assert prices.get_usd_try() is None


def test_coingecko_bad_values(fake_net):
    fake_net["handler"] = lambda r: httpx.Response(200, json={"bitcoin": {"try": "abc"}, "ethereum": {"try": 1e5}})
    assert prices.get_quote(AssetType.BTC, "BTC") is None
    assert prices.get_quote(AssetType.ETH, "ETH") == (100000.0, None)


def test_all_sources_down_summary_degrades_fast(client, no_network):
    """Ağ yok: özet hızlı ve 200 döner, fiyatlar None; snapshot yanlış dip yazmaz."""
    h = bearer(register(client))
    for body in ({"asset_type": "gold", "symbol": "x", "quantity": 1, "cost_price": 3000},
                 {"asset_type": "bist", "symbol": "THYAO", "quantity": 1, "cost_price": 300},
                 {"asset_type": "btc", "symbol": "x", "quantity": 1, "cost_price": 1}):
        assert client.post("/portfolio/holdings", headers=h, json=body).status_code == 201
    t0 = time.monotonic()
    r = client.get("/portfolio/summary", headers=h)
    assert r.status_code == 200 and time.monotonic() - t0 < 5
    s = r.json()
    assert all(x["current_price"] is None for x in s["holdings"])
    assert s["usd_try"] is None and s["gold_gram_try"] is None
    assert client.get("/portfolio/history", headers=h).json() == []


def test_public_price_validates_symbol(client, no_network):
    assert client.get("/public/price", params={"asset_type": "bist", "symbol": "A?range=max#"}).status_code == 400
    assert client.get("/public/price", params={"asset_type": "bist", "symbol": ""}).status_code == 400
    assert client.get("/public/history", params={"asset_type": "bist", "symbol": "../x"}).status_code == 400
    r = client.get("/public/price", params={"asset_type": "bist", "symbol": "thyao"})
    assert r.status_code == 200 and r.json() == {"asset_type": "bist", "symbol": "THYAO", "price": None}
    assert not [u for u in no_network if "?" in u.split("/chart/")[-1]]


def test_public_rate_limit_per_ip(client):
    for _ in range(30):
        assert client.get("/public/price", params={"asset_type": "cash"}, headers=ip("10.6.0.1")).status_code == 200
    assert client.get("/public/price", params={"asset_type": "cash"}, headers=ip("10.6.0.1")).status_code == 429
    assert client.get("/public/price", params={"asset_type": "cash"}, headers=ip("10.6.0.2")).status_code == 200


_RSS = b"""<?xml version="1.0"?><rss xmlns:n="https://news.google.com/rss"><channel>
<item><title>Haber</title><link>https://example.com/a</link><pubDate>Mon, 02 Nov 2026 10:00:00 GMT</pubDate>
<n:source>Kaynak</n:source></item></channel></rss>"""


def test_public_news_cache_bounded(client, monkeypatch):
    from app.routers import public as public_router

    seen = []

    def handler(request):
        seen.append(request.url)
        return httpx.Response(200, content=_RSS)

    monkeypatch.setattr(httpx, "Client", lambda *a, **kw: _REAL_CLIENT(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(public_router, "_NEWS_CACHE_MAX", 5)
    for i in range(12):
        r = client.get("/public/news", params={"asset_type": "bist", "symbol": "THYAO", "name": f"ad{i}"},
                       headers=ip(f"10.6.1.{i}"))
        assert r.json()["items"][0]["t"] == "Haber"
    assert len(seen) == 12 and seen[0].host == "news.google.com"
    assert 0 < len(public_router._NEWS_CACHE) <= 5
