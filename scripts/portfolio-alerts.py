#!/root/.venvs/parafomo-api/bin/python
"""Fiyat alarmı kontrolü — aktif alarmları canlı veriyle karşılaştırır.

Türler: kind="price" (₺ eşiği, fiyat üstüne/altına) · kind="day_pct" (günlük
değişim %, above=en az +X / below=en az −X). repeat=True alarmlar tetiklenince
kapanmaz: koşul düzelince kendini yeniden kurar (armed).

Cron: */15 * * * * — aktif alarm yoksa anında çıkar.
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
from app.prices import get_quote  # noqa: E402

ASSET_NAME = {
    AssetType.BIST: lambda s: s,
    AssetType.GOLD: lambda s: "Gram altın",
    AssetType.SILVER: lambda s: "Gram gümüş",
}


def _tl(v: float) -> str:
    return f"{v:,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(v: float) -> str:
    return ("%" + f"{v:,.2f}").replace(",", "X").replace(".", ",").replace("X", ".")


def _is_hit(a: PriceAlert, price: float, change_pct: float | None) -> bool | None:
    """Koşul sağlandı mı? day_pct için veri yoksa None (karar verme)."""
    if a.kind == "day_pct":
        if change_pct is None:
            return None
        return change_pct >= a.threshold if a.direction == "above" else change_pct <= -a.threshold
    return price >= a.threshold if a.direction == "above" else price <= a.threshold


def _mail(a: PriceAlert, user: User, price: float, change_pct: float | None) -> tuple[str, str]:
    name = ASSET_NAME[a.asset_type](a.symbol)
    if a.kind == "day_pct":
        yon = "yükseldi" if a.direction == "above" else "düştü"
        subject = f"🔔 {name} bugün {_pct(abs(change_pct or 0))} {yon} — ParaFOMO"
        koşul = f"günlük değişim {_pct(a.threshold)} {'üzeri yükseliş' if a.direction == 'above' else 'üzeri düşüş'}"
    else:
        yon = "üstüne çıktı" if a.direction == "above" else "altına indi"
        subject = f"🔔 {name} {_tl(a.threshold)} eşiğinin {yon} — ParaFOMO"
        koşul = f"fiyat {_tl(a.threshold)} {'üstü' if a.direction == 'above' else 'altı'}"
    body = (
        f"Merhaba{' ' + user.display_name if user.display_name else ''},\n\n"
        f"Kurduğun fiyat alarmı tetiklendi:\n"
        f"{name} şu an {_tl(price)}"
        + (f" (bugün {_pct(change_pct)})" if change_pct is not None else "") + "\n"
        f"Koşul: {koşul}\n\n"
        f"Portföyün: https://app.parafomo.com/portfoy/\n\n"
        + ("Bu alarm tekrarlayan türde: koşul düzelince kendini yeniden kurar.\n"
           if a.repeat else
           "Bu alarm tek seferlikti ve kapandı; istersen uygulamadan yenisini kurabilirsin.\n")
        + "— ParaFOMO · parafomo.com"
    )
    return subject, body


def main(dry: bool = False) -> None:
    init_db()
    db = SessionLocal()
    try:
        alerts = list(db.scalars(select(PriceAlert).where(PriceAlert.active)))
        if not alerts:
            return  # sessiz çık — log şişmesin
        quote_cache: dict[tuple[AssetType, str], tuple[float, float | None] | None] = {}
        fired = rearmed = 0
        for a in alerts:
            key = (a.asset_type, a.symbol)
            if key not in quote_cache:
                quote_cache[key] = get_quote(a.asset_type, a.symbol)
            q = quote_cache[key]
            if q is None:
                continue
            price, change_pct = q
            hit = _is_hit(a, price, change_pct)
            if hit is None:
                continue
            if a.armed and hit:
                user = db.get(User, a.user_id)
                if user is None:
                    a.active = False
                    continue
                subject, body = _mail(a, user, price, change_pct)
                if dry:
                    print(f"[dry] {user.email} ← {subject}")
                else:
                    send_email(user.email, subject, body)
                a.triggered_at = datetime.now(timezone.utc)
                a.triggered_price = round(price, 4)
                if a.repeat:
                    a.armed = False   # koşul sürerken tekrar tekrar mail atma
                else:
                    a.active = False
                fired += 1
            elif not a.armed and not hit:
                a.armed = True        # koşul düzeldi → yeniden kurul
                rearmed += 1
        if (fired or rearmed) and not dry:
            db.commit()
            print(f"[alerts] {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC · "
                  f"{fired} tetiklendi · {rearmed} yeniden kuruldu")
        elif dry:
            db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
