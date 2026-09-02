"""Halka açık (üyeliksiz) uç noktalar — SEO hesaplama aracı için canlı fiyat.

Kimlik gerektirmez; hafif IP rate-limit + prices.py'nin 120sn cache'i kötüye
kullanımı sınırlar. Hiçbir veri saklanmaz.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import APIRouter, HTTPException, Query, Request, status

from ..models import AssetType
from ..prices import get_price

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
