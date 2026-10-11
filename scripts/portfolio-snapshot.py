#!/root/.venvs/parafomo-api/bin/python
"""Gece portföy değer fotoğrafı — TÜM kullanıcılar için günün satırını yazar.

/portfolio/summary çağrısı gün içinde kendi satırını tazeler; bu cron o gün hiç
girmeyen kullanıcıların grafiği boş kalmasın diye vardır. Gün başına tek satır.

Cron: 50 20 * * * (23:50 TR) — çalıştır: /root/.venvs/parafomo-api/bin/python scripts/portfolio-snapshot.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

sys.path.insert(0, "/root/parafomo/backend")

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal, init_db  # noqa: E402
from app.models import AssetType, Holding, PortfolioSnapshot, User  # noqa: E402
from app.prices import get_quote  # noqa: E402


def main() -> None:
    init_db()
    today = datetime.now(timezone.utc).date()
    db = SessionLocal()
    quote_cache: dict[tuple[AssetType, str], tuple[float, float | None] | None] = {}
    written = skipped = 0
    try:
        users = list(db.scalars(select(User)))
        for user in users:
            holdings = list(db.scalars(select(Holding).where(Holding.user_id == user.id)))
            if not holdings:
                continue
            total_value = total_cost = 0.0
            for h in holdings:
                key = (h.asset_type, h.symbol)
                if key not in quote_cache:
                    quote_cache[key] = get_quote(h.asset_type, h.symbol)
                q = quote_cache[key]
                total_cost += h.quantity * h.cost_price
                if q:
                    total_value += h.quantity * q[0]
            if total_value <= 0 and total_cost > 0:
                skipped += 1  # fiyat kaynağı çökmüş — yanlış dip yazma
                continue
            snap = db.scalar(select(PortfolioSnapshot).where(
                PortfolioSnapshot.user_id == user.id, PortfolioSnapshot.day == today
            ))
            if snap is None:
                db.add(PortfolioSnapshot(
                    user_id=user.id, day=today,
                    total_value=round(total_value, 2), total_cost=round(total_cost, 2),
                ))
            else:
                snap.total_value = round(total_value, 2)
                snap.total_cost = round(total_cost, 2)
            written += 1
        db.commit()
    finally:
        db.close()
    print(f"[snapshot] {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC · "
          f"{written} kullanıcı yazıldı · {skipped} atlandı (fiyat yok)")


if __name__ == "__main__":
    main()
