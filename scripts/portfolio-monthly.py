#!/root/.venvs/parafomo-api/bin/python
"""Ay sonu portföy özeti e-postası — her ayın 1'inde geçen ayı raporlar.

Kaynak: portfolio_snapshots (ay içindeki ilk/son gün) + data/tufe-aylik.json
(enflasyon bağlamı). monthly_email=False olan kullanıcı atlanır.

Cron: 20 6 1 * * · Elle: .../portfolio-monthly.py [--dry]
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone

sys.path.insert(0, "/root/parafomo/backend")

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal, init_db  # noqa: E402
from app.mailer import send_email  # noqa: E402
from app.models import PortfolioSnapshot, User  # noqa: E402

TUFE_PATH = "/root/parafomo/data/benchmarks.json".replace("benchmarks", "tufe-aylik")
AYLAR = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def _tl(v: float) -> str:
    return f"{v:,.0f} ₺".replace(",", ".")


def _pct(v: float) -> str:
    s = f"{abs(v):,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("+%" if v >= 0 else "−%") + s


def main(dry: bool = False) -> None:
    init_db()
    today = datetime.now(timezone.utc).date()
    # geçen ay: bu ayın 1'inden bir gün geri
    last_of_prev = date(today.year, today.month, 1).toordinal() - 1
    prev_end = date.fromordinal(last_of_prev)
    y, m = prev_end.year, prev_end.month
    month_start = date(y, m, 1)

    tufe_txt = ""
    try:
        with open(TUFE_PATH, encoding="utf-8") as f:
            months = json.load(f)["months"]
        hit = next((x for x in months if x["ay"] == f"{y}-{m:02d}"), None)
        if hit:
            tufe_txt = f"O ay enflasyon (TÜFE): %{str(hit['aylik']).replace('.', ',')}.\n"
    except (OSError, ValueError, KeyError):
        pass

    db = SessionLocal()
    sent = 0
    try:
        for user in db.scalars(select(User).where(User.monthly_email)):
            snaps = list(db.scalars(
                select(PortfolioSnapshot)
                .where(PortfolioSnapshot.user_id == user.id,
                       PortfolioSnapshot.day >= month_start,
                       PortfolioSnapshot.day <= prev_end)
                .order_by(PortfolioSnapshot.day.asc())
            ))
            if len(snaps) < 2:
                continue
            first, last = snaps[0], snaps[-1]
            if first.total_value <= 0:
                continue
            change = last.total_value - first.total_value
            invested = last.total_cost - first.total_cost  # ay içi yatırılan/çekilen
            perf = change - invested                        # piyasa etkisi (yaklaşık)
            pct = perf / first.total_value * 100
            ay_adi = f"{AYLAR[m]} {y}"
            subject = f"📊 {ay_adi} portföy özetin: {_pct(pct)} — ParaFOMO"
            lines = [
                f"Merhaba{' ' + user.display_name if user.display_name else ''},",
                "",
                f"{ay_adi} ayında portföyün:",
                f"• Ay başı değer: {_tl(first.total_value)}",
                f"• Ay sonu değer: {_tl(last.total_value)}",
            ]
            if abs(invested) >= 1:
                lines.append(f"• Ay içinde {'eklediğin' if invested > 0 else 'azalttığın'} maliyet: {_tl(abs(invested))}")
            lines += [
                f"• Piyasa etkisi (yaklaşık): {_pct(pct)}",
                "",
            ]
            if tufe_txt:
                lines.append(tufe_txt.rstrip())
            lines += [
                "",
                "Güncel durum ve değer grafiğin: https://app.parafomo.com/portfoy/",
                "",
                "Bu aylık özeti istemiyorsan uygulamada Hesap menüsünden kapatabilirsin.",
                "— ParaFOMO · parafomo.com",
            ]
            body = "\n".join(lines)
            if dry:
                print(f"[dry] {user.email} ← {subject}")
            else:
                send_email(user.email, subject, body)
            sent += 1
        print(f"[monthly] {today} · {sent} özet {'hazırlandı (dry)' if dry else 'gönderildi'} ({AYLAR[m]} {y})")
    finally:
        db.close()


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
