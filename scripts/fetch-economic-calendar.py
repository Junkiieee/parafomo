#!/usr/bin/env python3
"""
ParaFOMO — Ekonomik takvim toplayıcı.

Her gün TEK bir dış sorgu yapar (ForexFactory haftalık XML — küresel makro),
bunu Türkiye'ye özgü sabit olaylarla (TCMB faiz kararları) ve kural-bazlı
TÜİK enflasyon tarihleriyle birleştirir. Sonucu kalıcı bir depoda biriktirir
(data/economic-calendar.json) ve içerik üreticisinin okuyacağı insan/LLM-dostu
bir özet yazar (docs/economic-calendar.md).

Tasarım: yalnızca standart kütüphane. Ağ hatasında çöker değil — mevcut depoyu
korur, sadece özetini yeniden üretir. Idempotent: aynı olayı iki kez eklemez.

Kullanım:  python3 scripts/fetch-economic-calendar.py
"""
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(ROOT, "data", "economic-calendar.json")
TR_FIXED = os.path.join(ROOT, "data", "tr-fixed-events.json")
OUT_MD = os.path.join(ROOT, "docs", "economic-calendar.md")

FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
# TL ve küresel risk iştahını en çok etkileyen para birimleri
MAJOR = {"USD", "EUR", "GBP", "CNY", "JPY"}
HORIZON_DAYS = 35          # ileriye kaç gün tutalım
PRUNE_BEFORE_DAYS = 3      # geçmiş olayları kaç gün sonra silelim

TR_GUN = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
FLAG = {"TR": "🇹🇷", "USD": "🇺🇸", "EUR": "🇪🇺", "GBP": "🇬🇧", "CNY": "🇨🇳", "JPY": "🇯🇵"}

# Küresel olaylar için içerik kancası ipuçları (başlıkta anahtar kelime geçerse)
GLOBAL_HOOKS = [
    ("Federal Funds Rate", "Fed faiz kararı — 'Fed faizi TL ve borsayı nasıl etkiler' explainer'ı."),
    ("FOMC", "Fed/FOMC — küresel faiz beklentisi TL'yi etkiler."),
    ("CPI", "ABD enflasyonu — dolar yönü ve küresel faiz beklentisi."),
    ("Non-Farm", "ABD istihdam (NFP) — dolar ve risk iştahı."),
    ("Main Refinancing Rate", "ECB faiz kararı — euro ve küresel faiz."),
    ("GDP", "Büyüme verisi — küresel görünüm."),
]


def fetch_forexfactory():
    """ForexFactory haftalık XML — küresel yüksek etkili olaylar. Tek dış sorgu."""
    req = urllib.request.Request(FF_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
    root = ET.fromstring(raw)
    events = []
    for ev in root.findall("event"):
        cur = (ev.findtext("country") or "").strip()
        impact = (ev.findtext("impact") or "").strip()
        title = (ev.findtext("title") or "").strip()
        d = (ev.findtext("date") or "").strip()      # MM-DD-YYYY
        t = (ev.findtext("time") or "").strip()
        if cur not in MAJOR or impact != "High" or not d:
            continue
        try:
            iso = datetime.strptime(d, "%m-%d-%Y").date().isoformat()
        except ValueError:
            continue
        hook = ""
        for key, h in GLOBAL_HOOKS:
            if key.lower() in title.lower():
                hook = h
                break
        events.append({
            "date": iso, "time": t, "region": cur, "impact": "High",
            "title": title, "source": "forexfactory", "hook": hook,
        })
    return events


def tuik_inflation_events(today):
    """TÜİK TÜFE (enflasyon) verisi ~her ayın 3'ünde açıklanır (hafta sonu ise sonraki iş günü)."""
    out = []
    y, m = today.year, today.month
    for _ in range(3):  # bu ay + 2 ay ileri
        d = date(y, m, 3)
        while d.weekday() >= 5:  # cmt/paz -> pazartesi
            d += timedelta(days=1)
        out.append({
            "date": d.isoformat(), "time": "10:00", "region": "TR", "impact": "High",
            "title": "TÜİK enflasyon (TÜFE) verisi",
            "source": "tuik-rule",
            "hook": "Enflasyon verisi öncesi 'enflasyon verisi nasıl okunur / paranı nasıl korursun' explainer'ı.",
        })
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def load_tr_fixed():
    try:
        with open(TR_FIXED, encoding="utf-8") as f:
            data = json.load(f)
        out = []
        for e in data.get("events", []):
            e = dict(e)
            e.setdefault("time", "")
            e["source"] = "tcmb"
            out.append(e)
        return out
    except (OSError, ValueError):
        return []


def load_store():
    try:
        with open(STORE, encoding="utf-8") as f:
            return json.load(f).get("events", [])
    except (OSError, ValueError):
        return []


def key(e):
    return (e["date"], e["region"], e["title"])


def main():
    today = date.today()
    stored = load_store()

    fetched = []
    fetch_ok = True
    try:
        fetched = fetch_forexfactory()
        print(f"[+] ForexFactory: {len(fetched)} küresel yüksek-etkili olay")
    except Exception as exc:  # ağ/parse hatası — depoyu koru
        fetch_ok = False
        print(f"[!] ForexFactory çekilemedi ({exc}); mevcut depo korunuyor")

    candidates = stored + fetched + load_tr_fixed() + tuik_inflation_events(today)

    # dedup (kaynak önceliği: tcmb > tuik > forexfactory > stored)
    prio = {"tcmb": 3, "tuik-rule": 2, "forexfactory": 1}
    merged = {}
    for e in candidates:
        k = key(e)
        if k not in merged or prio.get(e.get("source"), 0) >= prio.get(merged[k].get("source"), 0):
            merged[k] = e

    # geçmişi buda + ufku sınırla
    lo = today - timedelta(days=PRUNE_BEFORE_DAYS)
    hi = today + timedelta(days=HORIZON_DAYS)
    events = [e for e in merged.values()
              if lo.isoformat() <= e["date"] <= hi.isoformat()]
    events.sort(key=lambda e: (e["date"], e.get("time", "")))

    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    with open(STORE, "w", encoding="utf-8") as f:
        json.dump({"updated": today.isoformat(), "fetch_ok": fetch_ok, "events": events},
                  f, ensure_ascii=False, indent=2)
    print(f"[+] Depo: {len(events)} olay (ufuk {HORIZON_DAYS} gün) -> {STORE}")

    write_markdown(events, today)


def write_markdown(events, today):
    upcoming = [e for e in events if e["date"] >= today.isoformat()]
    lines = [
        "# Ekonomik Takvim (otomatik)",
        "",
        f"> Son güncelleme: {today.isoformat()} · `scripts/fetch-economic-calendar.py` tarafından üretilir. ELLE DÜZENLEME.",
        "> Kaynaklar: ForexFactory (küresel), TCMB (faiz kararı), TÜİK kuralı (enflasyon ~ayın 3'ü).",
        "",
        "İçerik üreticisi için: yaklaşan **🔴 High** etkili bir TR/küresel olay 1-3 gün içindeyse,",
        "o olayın `hook`'una göre bir **explainer** yazısını sıraya al (omurga evergreen akışını bozmadan).",
        "",
        "## Yaklaşan olaylar",
        "",
        "| Tarih | Gün | Bölge | Etki | Olay | İçerik fırsatı |",
        "|-------|-----|-------|------|------|----------------|",
    ]
    if not upcoming:
        lines.append("| — | — | — | — | Yaklaşan kayıtlı olay yok | — |")
    for e in upcoming:
        d = date.fromisoformat(e["date"])
        gun = TR_GUN[d.weekday()]
        flag = FLAG.get(e["region"], e["region"])
        impact = {"High": "🔴 High", "Medium": "🟡 Med", "Low": "⚪ Low"}.get(e.get("impact"), e.get("impact", ""))
        hook = (e.get("hook") or "").replace("|", "/")
        lines.append(f"| {e['date']} | {gun} | {flag} | {impact} | {e['title']} | {hook} |")
    lines.append("")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[+] Özet yazıldı -> {OUT_MD} ({len(upcoming)} yaklaşan olay)")


if __name__ == "__main__":
    sys.exit(main())
