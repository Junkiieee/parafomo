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

# Basit TTL cache: {cache_key: (timestamp, price)}
_CACHE: dict[str, tuple[float, float]] = {}
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


def _cache_get(key: str) -> float | None:
    hit = _CACHE.get(key)
    if hit and (time.time() - hit[0]) < _TTL_SECONDS:
        return hit[1]
    return None


def _cache_set(key: str, price: float) -> None:
    _CACHE[key] = (time.time(), price)


def _fetch_truncgil() -> dict:
    with httpx.Client(timeout=20, headers={"User-Agent": _UA}) as client:
        r = client.get(_TRUNCGIL_URL)
        r.raise_for_status()
        return r.json()


def _gold_silver_price(asset_type: AssetType) -> float | None:
    key = "gram-altin" if asset_type is AssetType.GOLD else "gumus"
    cached = _cache_get(key)
    if cached is not None:
        return cached
    try:
        data = _fetch_truncgil()
    except (httpx.HTTPError, ValueError):
        return None
    price = _num((data.get(key) or {}).get("Selling"))
    if price is not None:
        _cache_set(key, price)
    return price


def _bist_price(ticker: str) -> float | None:
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
    if price is not None:
        _cache_set(cache_key, price)
    return price


def get_price(asset_type: AssetType, symbol: str) -> float | None:
    """Bir varlığın güncel birim fiyatını (TL) döndürür; alınamazsa None."""
    if asset_type is AssetType.BIST:
        return _bist_price(symbol)
    return _gold_silver_price(asset_type)
