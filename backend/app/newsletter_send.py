"""Haftalık bülten gönderimi — onaylı abonelere (newsletter_subscribers.status='confirmed').

Kaynak: repodaki veri JSON'ları (getiri kümesi, halka arz, ekonomik takvim) + son 7 günün
blog yazıları. Para birimi değişimini "geçen bültenden beri" göstermek için her gönderimde
fiyat anlık görüntüsü saklanır (db dizininde newsletter-last.json).

Kullanım (backend/ içinden, API venv'i ile):
  python -m app.newsletter_send --dry-run            # HTML'i dosyaya yaz, gönderme
  python -m app.newsletter_send --to ben@ornek.com   # yalnız bu adrese (test)
  python -m app.newsletter_send                      # tüm onaylı abonelere (ISO hafta başına 1 kez)
"""
from __future__ import annotations

import argparse
import html
import json
import re
import smtplib
import sys
import time
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

from sqlalchemy import select

from .config import get_settings
from .db import SessionLocal, init_db
from .models import NewsletterSubscriber

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"
SITE = "https://parafomo.com"
API = "https://api.parafomo.com"
_settings = get_settings()
STATE = Path(_settings.db_path).parent / "newsletter-last.json"

# (etiket, dosya, şimdiki-değer anahtarı, sayfa, birim)
ASSETS = [
    ("Gram altın", "altin-getiri", "gram_tl_now", "/altin-getiri/", "TL"),
    ("Gram gümüş", "gumus-getiri", "gram_tl_now", "/gumus-getiri/", "TL"),
    ("Dolar/TL", "dolar-getiri", "usdtry_now", "/dolar-getiri/", "TL"),
    ("Euro/TL", "euro-getiri", "eurtry_now", "/euro-getiri/", "TL"),
    ("BIST 100", "bist-getiri", "bist_now", "/bist-getiri/", "puan"),
    ("Bitcoin", "bitcoin-getiri", "btc_tl_now", "/bitcoin-getiri/", "TL"),
]


def _tr_num(x: float, dec: int = 2) -> str:
    s = f"{x:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(x: float | None) -> str:
    if x is None:
        return "—"
    sign = "+" if x > 0 else ("−" if x < 0 else "")
    return f"{sign}%{_tr_num(abs(x), 1)}"


def _load(name: str) -> dict:
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


def _utm(path: str, campaign: str) -> str:
    sep = "&" if "?" in path else "?"
    return f"{SITE}{path}{sep}utm_source=bulten&utm_medium=email&utm_campaign={campaign}"


def market_rows(prev: dict) -> tuple[list[dict], dict, str]:
    rows, snap, updated = [], {}, ""
    for label, f, key, page, unit in ASSETS:
        try:
            d = _load(f)
        except (OSError, ValueError):
            continue
        now = d.get(key)
        if now is None:
            continue
        updated = max(updated, str(d.get("updated", ""))[:10])
        snap[f] = now
        one_y = next((p.get("return_tl_pct") for p in d.get("periods", []) if p.get("years") == 1), None)
        before = prev.get(f)
        rows.append({
            "label": label, "page": page,
            "now": _tr_num(now, 0 if now >= 10000 else 2) + (" puan" if unit == "puan" else " TL"),
            "week": _pct((now / before - 1) * 100) if before else None,
            "ytd": _pct((d.get("ytd") or {}).get("return_tl_pct")),
            "y1": _pct(one_y),
        })
    return rows, snap, updated


def ipo_rows(today: date) -> list[dict]:
    try:
        items = _load("halka-arz")["items"]
    except (OSError, ValueError, KeyError):
        return []
    out = []
    for i in items:
        end = i.get("end")
        if i.get("status") == "Tamamlandı" or not i.get("start"):
            continue
        if end and date.fromisoformat(end) < today:
            continue
        out.append(i)
    out.sort(key=lambda i: i["start"])
    return out[:4]


def event_rows(today: date) -> list[dict]:
    """Önümüzdeki 14 günün sabit takvimi (TCMB/TÜİK/Fed) + 7 günün yüksek etkili TR/ABD verisi."""
    horizon, near = (today + timedelta(days=14)).isoformat(), (today + timedelta(days=7)).isoformat()
    t0 = today.isoformat()
    out: list[dict] = []

    def add(d: str, region: str, title: str, page: str | None = None) -> None:
        if t0 <= d <= horizon and not any(o["date"] == d and o["region"] == region for o in out if page):
            out.append({"date": d, "region": region, "title": title, "page": page})

    for name, key, region, title, page in [
        ("tcmb-2026", "meetings", "TR", "TCMB faiz kararı (PPK)", "/tcmb-faiz-takvimi/"),
        ("tuik-enflasyon-2026", "releases", "TR", "TÜİK enflasyon verisi", "/enflasyon-takvimi/"),
        ("fomc-2026", "meetings", "USD", "Fed faiz kararı (FOMC)", "/fed-faiz-takvimi/"),
    ]:
        try:
            for m in _load(name)[key]:
                d = m.get("decisionDate") or m.get("date") or ""
                cov = f" ({m['covers']})" if m.get("covers") else ""
                add(d, region, title + cov, page)
        except (OSError, ValueError, KeyError):
            pass
    try:
        for e in _load("economic-calendar")["events"]:
            if (e.get("impact") == "High" and e.get("region") in ("TR", "USD")
                    and e.get("date", "") <= near
                    and not any(o["date"] == e["date"] and o["region"] == e["region"] and o["page"] for o in out)):
                add(e["date"], e["region"], e["title"])
    except (OSError, ValueError, KeyError):
        pass
    out.sort(key=lambda o: o["date"])
    return out[:6]


def new_posts(today: date) -> list[dict]:
    since = today - timedelta(days=7)
    posts = []
    for md in (REPO / "src/content/blog").glob("*.md"):
        head = md.read_text(encoding="utf-8").split("---", 2)[1]
        m_date = re.search(r"^pubDate:\s*(\d{4}-\d{2}-\d{2})", head, re.M)
        m_title = re.search(r'^title:\s*"?(.*?)"?\s*$', head, re.M)
        if not (m_date and m_title) or re.search(r"^draft:\s*true", head, re.M):
            continue
        d = date.fromisoformat(m_date.group(1))
        if since < d <= today:
            posts.append({"title": m_title.group(1), "path": f"/blog/{md.stem}/", "date": d})
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts[:5]


def _tr_date(d: str) -> str:
    months = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
    dd = date.fromisoformat(d[:10])
    return f"{dd.day} {months[dd.month - 1]}"


def build(today: date, campaign: str, prev: dict) -> tuple[str, str, str, dict]:
    """(konu, html, metin, yeni_anlık_görüntü). {UNSUB} yer tutucusu kişiye göre doldurulur."""
    rows, snap, updated = market_rows(prev)
    ipos, events, posts = ipo_rows(today), event_rows(today), new_posts(today)
    has_week = any(r["week"] for r in rows)
    e = html.escape

    gold = next((r for r in rows if r["label"] == "Gram altın"), None)
    subject = f"Paran bu hafta ne yaptı? · {_tr_date(today.isoformat())}"
    if gold and gold["week"]:
        subject = f"Gram altın {gold['week']} · paran bu hafta ne yaptı?"

    td = 'style="padding:8px 6px;border-bottom:1px solid #e6ebe8;text-align:right;white-space:nowrap"'
    th = 'style="padding:6px;text-align:right;font-size:12px;color:#5c665f;font-weight:600"'
    h2 = 'style="font-size:17px;margin:28px 0 10px;color:#13221b"'
    a = 'style="color:#1e6b7f"'

    parts = [
        '<div style="max-width:600px;margin:0 auto;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;'
        'color:#24302a;font-size:15px;line-height:1.55">',
        f'<p style="margin:0 0 4px;font-size:13px;color:#2bb194;font-weight:700;letter-spacing:.04em">PARAFOMO BÜLTEN</p>',
        f'<h1 style="font-size:22px;margin:0 0 6px;color:#13221b">Paran bu hafta ne yaptı?</h1>',
        f'<p style="margin:0 0 18px;color:#5c665f;font-size:13px">Veriler {e(_tr_date(updated)) if updated else ""} itibarıyla · TL bazında</p>',
        '<table role="presentation" cellspacing="0" cellpadding="0" style="width:100%;border-collapse:collapse;font-size:14px">',
        f'<tr><th style="padding:6px;text-align:left;font-size:12px;color:#5c665f">Varlık</th><th {th}>Şimdi</th>'
        + (f'<th {th}>Geçen bültenden</th>' if has_week else "")
        + f'<th {th}>Yılbaşından</th><th {th}>1 yıl</th></tr>',
    ]
    for r in rows:
        parts.append(
            f'<tr><td style="padding:8px 6px;border-bottom:1px solid #e6ebe8">'
            f'<a {a} href="{_utm(r["page"], campaign)}">{e(r["label"])}</a></td>'
            f'<td {td}>{e(r["now"])}</td>'
            + (f'<td {td}>{e(r["week"] or "—")}</td>' if has_week else "")
            + f'<td {td}>{e(r["ytd"])}</td><td {td}>{e(r["y1"])}</td></tr>'
        )
    parts.append("</table>")
    parts.append(
        f'<p style="font-size:13px;margin:8px 0 0"><a {a} href="{_utm("/altin-dolar-borsa/", campaign)}">'
        "Altın mı dolar mı borsa mı? 10 yıllık karşılaştırma →</a></p>"
    )

    text = [f"PARAFOMO BÜLTEN — Paran bu hafta ne yaptı? (veriler {updated})", ""]
    for r in rows:
        text.append(f"- {r['label']}: {r['now']} | yılbaşından {r['ytd']} | 1 yıl {r['y1']}"
                    + (f" | geçen bültenden {r['week']}" if r["week"] else ""))

    if events:
        parts.append(f"<h2 {h2}>Takvimde neler var</h2><ul style='padding-left:18px;margin:0'>")
        text += ["", "TAKVİMDE NELER VAR"]
        for ev in events:
            flag = "🇹🇷" if ev["region"] == "TR" else "🇺🇸"
            title = e(ev["title"])
            if ev.get("page"):
                title = f"<a {a} href='{_utm(ev['page'], campaign)}'>{title}</a>"
            parts.append(f"<li style='margin:0 0 6px'>{flag} <strong>{e(_tr_date(ev['date']))}</strong> — {title}</li>")
            text.append(f"- {ev['date']} {ev['region']}: {ev['title']}")
        parts.append(f"</ul><p style='font-size:13px;margin:8px 0 0'><a {a} href='{_utm('/ekonomik-takvim/', campaign)}'>Tüm ekonomik takvim →</a></p>")

    if ipos:
        parts.append(f"<h2 {h2}>Yaklaşan halka arzlar</h2><ul style='padding-left:18px;margin:0'>")
        text += ["", "YAKLAŞAN HALKA ARZLAR"]
        for i in ipos:
            when = f"{_tr_date(i['start'])}–{_tr_date(i['end'])}" if i.get("end") else _tr_date(i["start"])
            price = f" · {i['price']}" if i.get("price") else ""
            parts.append(
                f"<li style='margin:0 0 6px'><a {a} href='{_utm('/halka-arz/' + i['slug'] + '/', campaign)}'>"
                f"{e(i['company'])}</a> — {e(when)}{e(price)}</li>"
            )
            text.append(f"- {i['company']} — {when}{price}")
        parts.append("</ul>")
    parts.append(
        f"<p style='font-size:13px;margin:8px 0 0'><a {a} href='{_utm('/halka-arz-getiri/', campaign)}'>"
        "2026 halka arzları ne kazandırdı? Getiri karnesi →</a></p>"
    )

    if posts:
        parts.append(f"<h2 {h2}>Bu hafta sitede</h2><ul style='padding-left:18px;margin:0'>")
        text += ["", "BU HAFTA SİTEDE"]
        for p in posts:
            parts.append(f"<li style='margin:0 0 6px'><a {a} href='{_utm(p['path'], campaign)}'>{e(p['title'])}</a></li>")
            text.append(f"- {p['title']}: {SITE}{p['path']}")
        parts.append("</ul>")

    parts.append(
        "<p style='margin:30px 0 0;padding-top:14px;border-top:1px solid #e6ebe8;font-size:12px;color:#7a847d'>"
        "Bu e-posta bilgi amaçlıdır, yatırım tavsiyesi değildir. Geçmiş getiri gelecek getirinin göstergesi değildir.<br>"
        f"ParaFOMO bültenine onaylı abone olduğun için aldın. <a style='color:#7a847d' href='{{UNSUB}}'>Abonelikten çık</a>"
        "</p></div>"
    )
    text += ["", "Bilgi amaçlıdır, yatırım tavsiyesi değildir.", "Abonelikten çık: {UNSUB}"]
    return subject, "".join(parts), "\n".join(text), snap


def _message(to: str, token: str, subject: str, html_body: str, text_body: str) -> EmailMessage:
    unsub = f"{API}/newsletter/unsubscribe?token={token}"
    msg = EmailMessage()
    msg["From"] = _settings.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg["List-Unsubscribe"] = f"<{unsub}>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    msg.set_content(text_body.replace("{UNSUB}", unsub))
    msg.add_alternative(html_body.replace("{UNSUB}", html.escape(unsub)), subtype="html")
    return msg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="gönderme; HTML'i --out'a yaz")
    ap.add_argument("--out", default=str(Path(_settings.db_path).parent / "newsletter-preview.html"))
    ap.add_argument("--to", help="yalnız bu adrese gönder (test; durum dosyası güncellenmez)")
    ap.add_argument("--force", action="store_true", help="bu ISO haftada zaten gönderildiyse de gönder")
    args = ap.parse_args()

    init_db()
    today = datetime.now(timezone.utc).date()
    iso = today.isocalendar()
    campaign = f"{iso.year}-w{iso.week:02d}"
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    subject, html_body, text_body, snap = build(today, campaign, state.get("snapshot", {}))

    if args.dry_run:
        Path(args.out).write_text(html_body.replace("{UNSUB}", "#"), encoding="utf-8")
        with SessionLocal() as db:
            n = len(db.scalars(select(NewsletterSubscriber).where(NewsletterSubscriber.status == "confirmed")).all())
        print(f"[dry-run] konu: {subject}\n[dry-run] önizleme: {args.out}\n[dry-run] onaylı abone: {n}")
        return 0

    if not _settings.smtp_enabled:
        print("SMTP ayarlı değil (backend/.env PORTFOLIO_SMTP_HOST) — gönderilmedi.", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        if args.to:
            sub = db.scalar(select(NewsletterSubscriber).where(NewsletterSubscriber.email == args.to.lower()))
            targets = [(args.to, sub.token if sub else "test")]
        else:
            if state.get("campaign") == campaign and not args.force:
                print(f"{campaign} zaten gönderildi ({state.get('sent_at')}); --force ile tekrar.")
                return 0
            subs = db.scalars(select(NewsletterSubscriber).where(NewsletterSubscriber.status == "confirmed")).all()
            targets = [(s.email, s.token) for s in subs]

    sent = failed = 0
    if targets:
        with smtplib.SMTP(_settings.smtp_host, _settings.smtp_port, timeout=30) as server:
            if _settings.smtp_starttls:
                server.starttls()
            if _settings.smtp_user:
                server.login(_settings.smtp_user, _settings.smtp_password)
            for to, token in targets:
                try:
                    server.send_message(_message(to, token, subject, html_body, text_body))
                    sent += 1
                except smtplib.SMTPException as exc:
                    failed += 1
                    print(f"HATA {to}: {exc}", file=sys.stderr)
                time.sleep(0.3)  # Brevo hız sınırına saygı

    if not args.to:
        STATE.write_text(json.dumps({
            "campaign": campaign, "sent_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "sent": sent, "failed": failed, "snapshot": snap,
        }, ensure_ascii=False, indent=1))
    print(f"{campaign}: gönderildi {sent}, hata {failed}, konu: {subject}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
