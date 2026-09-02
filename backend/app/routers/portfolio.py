"""Portföy uç noktaları: pozisyon ekle/listele/sil + canlı değerleme."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import AssetType, Holding, User
from ..prices import get_price
from ..schemas import HoldingCreate, HoldingOut, HoldingValued, PortfolioSummary

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def _normalize_symbol(asset_type: AssetType, symbol: str) -> str:
    if asset_type is AssetType.BIST:
        return symbol.strip().upper()
    # Altın/gümüş için sembol sabit tutulur
    return asset_type.value.upper()


@router.post("/holdings", response_model=HoldingOut, status_code=status.HTTP_201_CREATED)
def add_holding(
    body: HoldingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Holding:
    holding = Holding(
        user_id=user.id,
        asset_type=body.asset_type,
        symbol=_normalize_symbol(body.asset_type, body.symbol),
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
    price_cache: dict[tuple[AssetType, str], float | None] = {}
    valued: list[HoldingValued] = []
    total_cost = 0.0
    total_value = 0.0

    for h in holdings:
        key = (h.asset_type, h.symbol)
        if key not in price_cache:
            price_cache[key] = get_price(h.asset_type, h.symbol)
        current_price = price_cache[key]

        cost_value = h.quantity * h.cost_price
        total_cost += cost_value

        if current_price is not None:
            current_value = h.quantity * current_price
            profit_loss = current_value - cost_value
            profit_loss_pct = (profit_loss / cost_value * 100) if cost_value else None
            total_value += current_value
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
            )
        )

    total_pl = total_value - total_cost
    total_pl_pct = (total_pl / total_cost * 100) if total_cost else 0.0

    return PortfolioSummary(
        total_cost=round(total_cost, 2),
        total_value=round(total_value, 2),
        total_profit_loss=round(total_pl, 2),
        total_profit_loss_pct=round(total_pl_pct, 2),
        holdings=valued,
        priced_at=datetime.now(timezone.utc),
    )
