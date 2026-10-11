"""Portföy uç noktaları: pozisyon ekle/listele/sil + canlı değerleme."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import (
    AssetType,
    Holding,
    PortfolioSnapshot,
    PriceAlert,
    User,
    WatchItem,
)
from ..prices import get_price, get_quote, get_usd_try
from ..schemas import (
    AlertCreate,
    AlertOut,
    HoldingCreate,
    HoldingOut,
    HoldingUpdate,
    HoldingValued,
    PortfolioSummary,
    SnapshotOut,
    WatchCreate,
    WatchOut,
)

_MAX_ACTIVE_ALERTS = 20
_MAX_WATCH_ITEMS = 30

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def _normalize_symbol(asset_type: AssetType, symbol: str) -> str:
    if asset_type is AssetType.BIST:
        return symbol.strip().upper()
    # Altın/gümüş için sembol sabit tutulur
    return asset_type.value.upper()


@router.post("/holdings", response_model=HoldingOut, status_code=status.HTTP_201_CREATED)
def add_holding(
    body: HoldingCreate,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Holding:
    symbol = _normalize_symbol(body.asset_type, body.symbol)

    # Aynı sembolde ikinci alım → ayrı satır AÇMA, mevcut pozisyona BİRLEŞTİR ve
    # adet-ağırlıklı ortalama maliyet hesapla. Kullanıcı "TUPRS 10@100 sonra 5@130"
    # eklediğinde tek satır: 15 adet, ort. maliyet (10*100+5*130)/15 = 110.
    existing = db.scalar(
        select(Holding).where(
            Holding.user_id == user.id,
            Holding.asset_type == body.asset_type,
            Holding.symbol == symbol,
        )
    )
    if existing is not None:
        total_qty = existing.quantity + body.quantity
        existing.cost_price = round(
            (existing.quantity * existing.cost_price + body.quantity * body.cost_price)
            / total_qty,
            6,
        )
        existing.quantity = total_qty
        # En erken alış tarihini koru (pozisyonun başlangıcı)
        if body.purchase_date is not None and (
            existing.purchase_date is None
            or body.purchase_date < existing.purchase_date
        ):
            existing.purchase_date = body.purchase_date
        db.commit()
        db.refresh(existing)
        response.status_code = status.HTTP_200_OK
        return existing

    holding = Holding(
        user_id=user.id,
        asset_type=body.asset_type,
        symbol=symbol,
        quantity=body.quantity,
        cost_price=body.cost_price,
        purchase_date=body.purchase_date,
        note=body.note,
    )
    db.add(holding)
    db.commit()
    db.refresh(holding)
    return holding


@router.get("/holdings", response_model=list[HoldingOut])
def list_holdings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Holding]:
    return list(
        db.scalars(
            select(Holding)
            .where(Holding.user_id == user.id)
            .order_by(Holding.created_at.desc())
        )
    )


@router.patch("/holdings/{holding_id}", response_model=HoldingOut)
def update_holding(
    holding_id: int,
    body: HoldingUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Holding:
    holding = db.get(Holding, holding_id)
    if holding is None or holding.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pozisyon bulunamadı."
        )
    fields = body.model_dump(exclude_unset=True)
    for key, value in fields.items():
        setattr(holding, key, value)
    db.commit()
    db.refresh(holding)
    return holding


@router.delete(
    "/holdings/{holding_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_holding(
    holding_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    holding = db.get(Holding, holding_id)
    if holding is None or holding.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pozisyon bulunamadı."
        )
    db.delete(holding)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/summary", response_model=PortfolioSummary)
def portfolio_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioSummary:
    holdings = list(
        db.scalars(select(Holding).where(Holding.user_id == user.id))
    )

    # Tekil fiyat çağrısı: aynı sembolü tekrar sorgulama
    quote_cache: dict[tuple[AssetType, str], tuple[float, float | None] | None] = {}
    valued: list[HoldingValued] = []
    total_cost = 0.0
    total_value = 0.0
    total_day_change = 0.0
    total_prev_value = 0.0  # gün içi % için önceki-kapanış değeri toplamı

    for h in holdings:
        key = (h.asset_type, h.symbol)
        if key not in quote_cache:
            quote_cache[key] = get_quote(h.asset_type, h.symbol)
        quote = quote_cache[key]
        current_price = quote[0] if quote else None
        change_pct = quote[1] if quote else None

        cost_value = h.quantity * h.cost_price
        total_cost += cost_value

        day_change = None
        if current_price is not None:
            current_value = h.quantity * current_price
            profit_loss = current_value - cost_value
            profit_loss_pct = (profit_loss / cost_value * 100) if cost_value else None
            total_value += current_value
            if change_pct is not None:
                # önceki kapanış = fiyat / (1 + %/100); gün içi K/Z = güncel - önceki
                prev_price = current_price / (1 + change_pct / 100) if change_pct != -100 else 0.0
                prev_value = h.quantity * prev_price
                day_change = current_value - prev_value
                total_day_change += day_change
                total_prev_value += prev_value
        else:
            current_value = profit_loss = profit_loss_pct = None

        valued.append(
            HoldingValued(
                id=h.id,
                asset_type=h.asset_type,
                symbol=h.symbol,
                quantity=h.quantity,
                cost_price=h.cost_price,
                purchase_date=h.purchase_date,
                note=h.note,
                created_at=h.created_at,
                current_price=current_price,
                cost_value=round(cost_value, 2),
                current_value=round(current_value, 2) if current_value is not None else None,
                profit_loss=round(profit_loss, 2) if profit_loss is not None else None,
                profit_loss_pct=round(profit_loss_pct, 2) if profit_loss_pct is not None else None,
                change_pct=round(change_pct, 2) if change_pct is not None else None,
                day_change=round(day_change, 2) if day_change is not None else None,
            )
        )

    total_pl = total_value - total_cost
    total_pl_pct = (total_pl / total_cost * 100) if total_cost else 0.0
    total_day_pct = (
        total_day_change / total_prev_value * 100 if total_prev_value else None
    )

    # Birim çevirileri (dolar / gram altın görünümü için)
    usd_try = get_usd_try()
    gold_q = quote_cache.get((AssetType.GOLD, "GOLD")) or get_quote(AssetType.GOLD, "GOLD")
    gold_try = gold_q[0] if gold_q else None

    # Günün değer fotoğrafı: değer grafiğini besler (gün başına tek satır, tazelenir).
    # Fiyat kaynakları çöktüyse (total_value=0 ama maliyet var) yanlış dip yazma.
    if holdings and (total_value > 0 or total_cost == 0):
        today = datetime.now(timezone.utc).date()
        try:
            snap = db.scalar(
                select(PortfolioSnapshot).where(
                    PortfolioSnapshot.user_id == user.id, PortfolioSnapshot.day == today
                )
            )
            if snap is None:
                db.add(PortfolioSnapshot(
                    user_id=user.id, day=today,
                    total_value=round(total_value, 2), total_cost=round(total_cost, 2),
                ))
            else:
                snap.total_value = round(total_value, 2)
                snap.total_cost = round(total_cost, 2)
            db.commit()
        except Exception:  # snapshot hiçbir zaman özeti düşürmesin
            db.rollback()

    return PortfolioSummary(
        usd_try=usd_try,
        gold_gram_try=gold_try,
        total_cost=round(total_cost, 2),
        total_value=round(total_value, 2),
        total_profit_loss=round(total_pl, 2),
        total_profit_loss_pct=round(total_pl_pct, 2),
        total_day_change=round(total_day_change, 2) if total_prev_value else None,
        total_day_change_pct=round(total_day_pct, 2) if total_day_pct is not None else None,
        holdings=valued,
        priced_at=datetime.now(timezone.utc),
    )


# ---------- değer geçmişi ----------
@router.get("/history", response_model=list[SnapshotOut])
def portfolio_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PortfolioSnapshot]:
    """Günlük portföy değeri serisi (en eski → en yeni, son 400 gün)."""
    rows = list(
        db.scalars(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.user_id == user.id)
            .order_by(PortfolioSnapshot.day.desc())
            .limit(400)
        )
    )
    rows.reverse()
    return rows


# ---------- fiyat alarmları ----------
@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PriceAlert]:
    return list(
        db.scalars(
            select(PriceAlert)
            .where(PriceAlert.user_id == user.id)
            .order_by(PriceAlert.active.desc(), PriceAlert.created_at.desc())
        )
    )


@router.post("/alerts", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
def add_alert(
    body: AlertCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PriceAlert:
    active_count = len(list(db.scalars(
        select(PriceAlert.id).where(PriceAlert.user_id == user.id, PriceAlert.active)
    )))
    if active_count >= _MAX_ACTIVE_ALERTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"En fazla {_MAX_ACTIVE_ALERTS} aktif alarm kurabilirsin. Önce birini sil.",
        )
    symbol = _normalize_symbol(body.asset_type, body.symbol)
    if get_price(body.asset_type, symbol) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu varlık için fiyat bulunamadı — sembolü kontrol et.",
        )
    alert = PriceAlert(
        user_id=user.id,
        asset_type=body.asset_type,
        symbol=symbol,
        direction=body.direction,
        threshold=body.threshold,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.delete(
    "/alerts/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_alert(
    alert_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    alert = db.get(PriceAlert, alert_id)
    if alert is None or alert.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alarm bulunamadı.")
    db.delete(alert)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- izleme listesi ----------
@router.get("/watchlist", response_model=list[WatchOut])
def list_watchlist(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WatchOut]:
    items = list(
        db.scalars(
            select(WatchItem)
            .where(WatchItem.user_id == user.id)
            .order_by(WatchItem.created_at.asc())
        )
    )
    out: list[WatchOut] = []
    quote_cache: dict[tuple[AssetType, str], tuple[float, float | None] | None] = {}
    for w in items:
        key = (w.asset_type, w.symbol)
        if key not in quote_cache:
            quote_cache[key] = get_quote(w.asset_type, w.symbol)
        q = quote_cache[key]
        out.append(WatchOut(
            id=w.id,
            asset_type=w.asset_type,
            symbol=w.symbol,
            current_price=round(q[0], 4) if q else None,
            change_pct=round(q[1], 2) if q and q[1] is not None else None,
        ))
    return out


@router.post("/watchlist", response_model=WatchOut, status_code=status.HTTP_201_CREATED)
def add_watch(
    body: WatchCreate,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchOut:
    symbol = _normalize_symbol(body.asset_type, body.symbol)
    existing = db.scalar(
        select(WatchItem).where(
            WatchItem.user_id == user.id,
            WatchItem.asset_type == body.asset_type,
            WatchItem.symbol == symbol,
        )
    )
    if existing is None:
        count = len(list(db.scalars(select(WatchItem.id).where(WatchItem.user_id == user.id))))
        if count >= _MAX_WATCH_ITEMS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"İzleme listesi en fazla {_MAX_WATCH_ITEMS} varlık alır.",
            )
        existing = WatchItem(user_id=user.id, asset_type=body.asset_type, symbol=symbol)
        db.add(existing)
        db.commit()
        db.refresh(existing)
    else:
        response.status_code = status.HTTP_200_OK
    q = get_quote(existing.asset_type, existing.symbol)
    return WatchOut(
        id=existing.id,
        asset_type=existing.asset_type,
        symbol=existing.symbol,
        current_price=round(q[0], 4) if q else None,
        change_pct=round(q[1], 2) if q and q[1] is not None else None,
    )


@router.delete(
    "/watchlist/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_watch(
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    item = db.get(WatchItem, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kayıt bulunamadı.")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
