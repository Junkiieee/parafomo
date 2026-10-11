#!/root/.venvs/parafomo-api/bin/python
"""Fiyat alarmı kontrolü — aktif alarmları canlı fiyatla karşılaştırır,
eşik aşılmışsa e-posta gönderir ve alarmı kapatır (tek seferlik).

Cron: */15 * * * * — aktif alarm yoksa anında çıkar, fiyat sorgusu yapmaz.
Elle: /root/.venvs/parafomo-api/bin/python scripts/portfolio-alerts.py [--dry]
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

sys.path.insert(0, "/root/parafomo/backend")

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal, init_db  # noqa: E402
from app.mailer import send_email  # noqa: E402
from app.models import AssetType, PriceAlert, User  # noqa: E402
from app.prices import get_price  # noqa: E402

ASSET_NAME = {
    AssetType.BIST: lambda s: s,
    AssetType.GOLD: lambda s: "Gram altın",
    AssetType.SILVER: lambda s: "Gram gümüş",
}


def _tl(v: float) -> str:
    return f"{v:,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")


def main(dry: bool = False) -> None:
    init_db()
    db = SessionLocal()
    try:
        alerts = list(db.scalars(select(PriceAlert).where(PriceAlert.active)))
        if not alerts:
            return  # sessiz çık — log şişmesin
        price_cache: dict[tuple[AssetType, str], float | None] = {}
        fired = 0
        for a in alerts:
            key = (a.asset_type, a.symbol)
            if key not in price_cache:
                price_cache[key] = get_price(a.asset_type, a.symbol)
            price = price_cache[key]
            if price is None:
                continue
            hit = price >= a.threshold if a.direction == "above" else price <= a.threshold
            if not hit:
                continue
            user = db.get(User, a.user_id)
            if user is None:
                a.active = False
                continue
            name = ASSET_NAME[a.asset_type](a.symbol)
            yon = "üstüne çıktı" if a.direction == "above" else "altına indi"
            subject = f"🔔 {name} {_tl(a.threshold)} eşiğinin {yon} — ParaFOMO"
            body = (
                f"Merhaba{' ' + user.display_name if user.display_name else ''},\n\n"
                f"Kurduğun fiyat alarmı tetiklendi:\n"
                f"{name} şu an {_tl(price)} (eşik: {_tl(a.threshold)} {('üstü' if a.direction == 'above' else 'altı')}).\n\n"
                f"Portföyün: https://app.parafomo.com/portfoy/\n\n"
                f"Bu alarm tek seferlikti ve kapandı; istersen uygulamadan yenisini kurabilirsin.\n"
                f"— ParaFOMO · parafomo.com"
            )
            if dry:
                print(f"[dry] {user.email} ← {subject}")
            else:
                send_email(user.email, subject, body)
            a.active = False
            a.triggered_at = datetime.now(timezone.utc)
            a.triggered_price = round(price, 4)
            fired += 1
        if fired and not dry:
            db.commit()
            print(f"[alerts] {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC · {fired} alarm tetiklendi")
        elif dry:
            db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
