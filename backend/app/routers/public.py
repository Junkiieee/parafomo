"""Halka açık (üyeliksiz) uç noktalar — SEO hesaplama aracı için canlı fiyat.

Kimlik gerektirmez; hafif IP rate-limit + prices.py'nin 120sn cache'i kötüye
kullanımı sınırlar. Hiçbir veri saklanmaz.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, Query, Request

from ..models import AssetType
from ..prices import get_bist_history, get_price, is_valid_bist_symbol
from ..ratelimit import RateLimiter, client_ip, enforce

router = APIRouter(prefix="/public", tags=["public"])

# Sliding-window limiter: IP başına 60sn'de 30 istek (bellek sınırlı, ratelimit.py)
_limiter = RateLimiter(limit=30, window=60)


def _rate_limit(request: Request) -> None:
    enforce(_limiter, client_ip(request), "Çok fazla istek. Lütfen biraz sonra tekrar dene.")


def _bist_symbol(symbol: str) -> str:
    """Kullanıcının yazdığı kod Yahoo URL'sine girer: yalnız harf/rakam."""
    sym = symbol.strip().upper()
    if not sym:
        raise HTTPException(status_code=400, detail="Hisse kodu gerekli.")
    if not is_valid_bist_symbol(sym):
        raise HTTPException(status_code=400, detail="Geçersiz hisse kodu.")
    return sym


@router.get("/price")
def public_price(
    request: Request,
    asset_type: AssetType = Query(...),
    symbol: str = Query("", max_length=32),
) -> dict:
    """Bir varlığın güncel birim fiyatını (TL) döndürür. Üyelik gerekmez."""
    _rate_limit(request)
    sym = _bist_symbol(symbol) if asset_type is AssetType.BIST else asset_type.value.upper()
    price = get_price(asset_type, sym)
    return {"asset_type": asset_type.value, "symbol": sym, "price": price}


_BENCHMARKS_PATH = "/root/parafomo/data/benchmarks.json"
_RANGE_MONTHS = {"3mo": 4, "1y": 13, "5y": 61}


@router.get("/history")
def public_history(
    request: Request,
    asset_type: AssetType = Query(...),
    symbol: str = Query("", max_length=32),
    range: str = Query("1y", max_length=8),
) -> dict:
    """Varlık fiyat geçmişi. BIST: günlük/haftalık (Yahoo); altın/gümüş: aylık (benchmarks)."""
    _rate_limit(request)
    if asset_type is AssetType.BIST:
        sym = _bist_symbol(symbol)
        points = get_bist_history(sym, range)
        if points is None:
            raise HTTPException(status_code=404, detail="Geçmiş veri alınamadı.")
        return {"asset_type": "bist", "symbol": sym, "granularity": "daily", "points": points}
    # metal / döviz / BTC → aylık seri (benchmarks)
    key = {
        AssetType.GOLD: "gold", AssetType.SILVER: "silver",
        AssetType.USD: "usd", AssetType.EUR: "eur", AssetType.BTC: "btc",
    }.get(asset_type)
    if key is None:
        raise HTTPException(status_code=404, detail="Bu varlık için geçmiş grafik yok.")
    import json as _json
    try:
        with open(_BENCHMARKS_PATH, encoding="utf-8") as f:
            months = _json.load(f)["months"]
    except (OSError, ValueError, KeyError):
        raise HTTPException(status_code=404, detail="Geçmiş veri alınamadı.")
    n = _RANGE_MONTHS.get(range, 13)
    points = [{"t": m["ay"], "p": m[key]} for m in months if key in m][-n:]
    return {"asset_type": asset_type.value, "symbol": key.upper(),
            "granularity": "monthly", "points": points}


# ---- pozisyon haberleri (Google News RSS, 30 dk cache) ----
_NEWS_TTL = 1800
_NEWS_CACHE: dict[str, tuple[float, list[dict]]] = {}
_NEWS_CACHE_MAX = 2000  # anahtar kullanıcı girdisi (name) → rastgele adlarla şişmesin
_NEWS_Q = {
    AssetType.GOLD: "gram altın fiyatı",
    AssetType.SILVER: "gümüş fiyatı",
    AssetType.USD: "dolar kuru",
    AssetType.EUR: "euro kuru",
    AssetType.BTC: "bitcoin",
    AssetType.ETH: "ethereum",
}


@router.get("/news")
def public_news(
    request: Request,
    asset_type: AssetType = Query(...),
    symbol: str = Query("", max_length=32),
    name: str = Query("", max_length=80),
) -> dict:
    """Varlıkla ilgili son 3 haber başlığı (Google News)."""
    _rate_limit(request)
    if asset_type is AssetType.BIST:
        sym = symbol.strip().upper()
        if not sym or not sym.isalnum():
            raise HTTPException(status_code=400, detail="Hisse kodu gerekli.")
        clean = "".join(c for c in name if c.isalnum() or c in " ÇĞİÖŞÜçğıöşü.&-")[:60].strip()
        q = f'"{clean}" OR {sym} hisse' if clean else f"{sym} hisse"
    else:
        q = _NEWS_Q.get(asset_type)
        if q is None:
            return {"items": []}
    now_ts = time.time()
    hit = _NEWS_CACHE.get(q)
    if hit and now_ts - hit[0] < _NEWS_TTL:
        return {"items": hit[1]}
    import urllib.parse
    import xml.etree.ElementTree as ET

    import httpx
    url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q)
           + "&hl=tr&gl=TR&ceid=TR:tr")
    try:
        with httpx.Client(timeout=15, headers={"User-Agent": "Mozilla/5.0 (parafomo-news/1.0)"},
                          follow_redirects=True) as client:
            r = client.get(url)
            r.raise_for_status()
        root = ET.fromstring(r.text)
        items = []
        for it in root.iter("item"):
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            pub = (it.findtext("pubDate") or "").strip()
            src = it.find("{https://news.google.com/rss}source")
            src_name = (src.text or "").strip() if src is not None else ""
            if title and link.startswith("http"):
                items.append({"t": title[:160], "u": link, "d": pub[:16], "s": src_name[:40]})
            if len(items) >= 3:
                break
    except Exception:
        return {"items": []}   # haber yoksa sessiz boş — UI bölümü gizler
    if len(_NEWS_CACHE) >= _NEWS_CACHE_MAX:
        for k in [k for k, (ts, _) in _NEWS_CACHE.items() if now_ts - ts >= _NEWS_TTL]:
            del _NEWS_CACHE[k]
        while len(_NEWS_CACHE) >= _NEWS_CACHE_MAX:
            del _NEWS_CACHE[next(iter(_NEWS_CACHE))]
    _NEWS_CACHE[q] = (now_ts, items)
    return {"items": items}
