"""Halka açık (üyeliksiz) uç noktalar — SEO hesaplama aracı için canlı fiyat.

Kimlik gerektirmez; hafif IP rate-limit + prices.py'nin 120sn cache'i kötüye
kullanımı sınırlar. Hiçbir veri saklanmaz.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import APIRouter, HTTPException, Query, Request, status

from ..models import AssetType
from ..prices import get_bist_history, get_price

router = APIRouter(prefix="/public", tags=["public"])

# Basit sliding-window limiter: IP başına 60sn'de 30 istek
_WINDOW = 60
_LIMIT = 30
_hits: dict[str, deque] = defaultdict(deque)


def _rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "?"
    now = time.time()
    q = _hits[ip]
    while q and now - q[0] > _WINDOW:
        q.popleft()
    if len(q) >= _LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Çok fazla istek. Lütfen biraz sonra tekrar dene.",
        )
    q.append(now)


@router.get("/price")
def public_price(
    request: Request,
    asset_type: AssetType = Query(...),
    symbol: str = Query("", max_length=32),
) -> dict:
    """Bir varlığın güncel birim fiyatını (TL) döndürür. Üyelik gerekmez."""
    _rate_limit(request)
    sym = symbol.strip().upper() if asset_type is AssetType.BIST else asset_type.value.upper()
    if asset_type is AssetType.BIST and not sym:
        raise HTTPException(status_code=400, detail="Hisse kodu gerekli.")
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
        sym = symbol.strip().upper()
        if not sym:
            raise HTTPException(status_code=400, detail="Hisse kodu gerekli.")
        points = get_bist_history(sym, range)
        if points is None:
            raise HTTPException(status_code=404, detail="Geçmiş veri alınamadı.")
        return {"asset_type": "bist", "symbol": sym, "granularity": "daily", "points": points}
    # altın / gümüş → aylık seri (gram TL)
    import json as _json
    try:
        with open(_BENCHMARKS_PATH, encoding="utf-8") as f:
            months = _json.load(f)["months"]
    except (OSError, ValueError, KeyError):
        raise HTTPException(status_code=404, detail="Geçmiş veri alınamadı.")
    key = "gold" if asset_type is AssetType.GOLD else "silver"
    n = _RANGE_MONTHS.get(range, 13)
    points = [{"t": m["ay"], "p": m[key]} for m in months if key in m][-n:]
    return {"asset_type": asset_type.value, "symbol": key.upper(),
            "granularity": "monthly", "points": points}
