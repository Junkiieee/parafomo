"""Canlı fiyat servisi — ücretsiz kaynaklar.

BIST hisseleri : Yahoo Finance chart API (<TICKER>.IS)
Altın / Gümüş  : Truncgil v3 today.json (gram-altin / gumus, Selling)

Paralı API KULLANILMAZ (kullanıcı kararı 2026-08-30). Bir eksik çıkarsa
tasks-for-user.md'ye yazılır. Fiyatlar kısa süreli cache'lenir (kaynakları
yormamak + hız). Tüm fiyatlar TL cinsindendir.
"""
from __future__ import annotations

import time

import httpx

from .models import AssetType

_TRUNCGIL_URL = "https://finans.truncgil.com/v3/today.json"
_YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.IS"
_UA = "Mozilla/5.0 (ParaFOMO Portfolio)"

# Basit TTL cache: {cache_key: (timestamp, (price, change_pct))}
_CACHE: dict[str, tuple[float, tuple[float, float | None]]] = {}
_TTL_SECONDS = 120


def _num(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _pct(value) -> float | None:
    """Truncgil 'Change' alanı ('%0,43' / '%-1,2') → float yüzde."""
    if value is None:
        return None
    s = str(value).strip().replace("%", "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _cache_get(key: str) -> tuple[float, float | None] | None:
    hit = _CACHE.get(key)
    if hit and (time.time() - hit[0]) < _TTL_SECONDS:
        return hit[1]
    return None


def _cache_set(key: str, quote: tuple[float, float | None]) -> None:
    _CACHE[key] = (time.time(), quote)


def _fetch_truncgil() -> dict:
    with httpx.Client(timeout=20, headers={"User-Agent": _UA}) as client:
        r = client.get(_TRUNCGIL_URL)
        r.raise_for_status()
        return r.json()


def _gold_silver_quote(asset_type: AssetType) -> tuple[float, float | None] | None:
    key = "gram-altin" if asset_type is AssetType.GOLD else "gumus"
    cached = _cache_get(key)
    if cached is not None:
        return cached
    try:
        data = _fetch_truncgil()
    except (httpx.HTTPError, ValueError):
        return None
    entry = data.get(key) or {}
    price = _num(entry.get("Selling"))
    if price is None:
        return None
    quote = (price, _pct(entry.get("Change")))
    _cache_set(key, quote)
    return quote


def get_usd_try() -> float | None:
    """Güncel USD/TRY satış kuru (Truncgil); alınamazsa None."""
    cached = _cache_get("usd-try")
    if cached is not None:
        return cached[0]
    try:
        data = _fetch_truncgil()
    except (httpx.HTTPError, ValueError):
        return None
    price = _num((data.get("USD") or {}).get("Selling"))
    if price is None:
        return None
    _cache_set("usd-try", (price, None))
    return price


def _bist_quote(ticker: str) -> tuple[float, float | None] | None:
    ticker = ticker.strip().upper()
    cache_key = f"bist:{ticker}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    try:
        with httpx.Client(timeout=20, headers={"User-Agent": _UA}) as client:
            r = client.get(_YAHOO_URL.format(symbol=ticker))
            r.raise_for_status()
            data = r.json()
        result = (data.get("chart") or {}).get("result") or []
        meta = result[0].get("meta") if result else None
        price = _num(meta.get("regularMarketPrice")) if meta else None
    except (httpx.HTTPError, ValueError, KeyError, IndexError, AttributeError):
        return None
    if price is None:
        return None
    prev = _num(meta.get("previousClose")) or _num(meta.get("chartPreviousClose"))
    change_pct = ((price - prev) / prev * 100) if prev else None
    quote = (price, change_pct)
    _cache_set(cache_key, quote)
    return quote


def get_quote(asset_type: AssetType, symbol: str) -> tuple[float, float | None] | None:
    """Güncel (birim fiyat TL, gün içi değişim %) döndürür; alınamazsa None."""
    if asset_type is AssetType.BIST:
        return _bist_quote(symbol)
    return _gold_silver_quote(asset_type)


def get_price(asset_type: AssetType, symbol: str) -> float | None:
    """Bir varlığın güncel birim fiyatını (TL) döndürür; alınamazsa None."""
    quote = get_quote(asset_type, symbol)
    return quote[0] if quote else None


# ---- tarihsel seri (varlık detay grafiği) ----
_HIST_TTL = 3600
_HIST_CACHE: dict[str, tuple[float, list[dict]]] = {}
_HIST_RANGES = {"3mo": "1d", "1y": "1d", "5y": "1wk"}


def get_bist_history(ticker: str, rng: str) -> list[dict] | None:
    """BIST kapanış serisi [{t: 'YYYY-MM-DD', p: fiyat}] — Yahoo, 1 saat cache."""
    if rng not in _HIST_RANGES:
        return None
    ticker = ticker.strip().upper()
    key = f"hist:{ticker}:{rng}"
    hit = _HIST_CACHE.get(key)
    if hit and (time.time() - hit[0]) < _HIST_TTL:
        return hit[1]
    url = _YAHOO_URL.format(symbol=ticker) + f"?range={rng}&interval={_HIST_RANGES[rng]}"
    try:
        with httpx.Client(timeout=20, headers={"User-Agent": _UA}) as client:
            r = client.get(url)
            r.raise_for_status()
            data = r.json()
        res = data["chart"]["result"][0]
        ts = res["timestamp"]
        closes = res["indicators"]["quote"][0]["close"]
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        return None
    import datetime as _dt
    points = [
        {"t": _dt.datetime.fromtimestamp(t, tz=_dt.timezone.utc).strftime("%Y-%m-%d"),
         "p": round(float(c), 4)}
        for t, c in zip(ts, closes) if c is not None
    ]
    if not points:
        return None
    _HIST_CACHE[key] = (time.time(), points)
    return points
