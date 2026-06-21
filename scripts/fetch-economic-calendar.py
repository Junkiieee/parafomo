#!/usr/bin/env python3
"""
ParaFOMO — Ekonomik takvim toplayıcı.

Her gün TEK bir dış sorgu yapar (Investing.com ekonomik takvim — Türkiye + küresel
makro), bunu Türkiye'ye özgü sabit olaylarla (TCMB faiz kararları) birleştirir.
Sonucu kalıcı bir depoda biriktirir (data/economic-calendar.json) ve içerik
üreticisinin okuyacağı insan/LLM-dostu bir özet yazar (docs/economic-calendar.md).

Kaynaklar:
  1) Investing.com (BİRİNCİL) — Türkiye (TÜFE, işsizlik, PMI, dış ticaret, faiz)
     + küresel majörler (Fed, ECB, ABD enflasyon/istihdam). Tek POST sorgusu.
  2) TCMB sabit PPK takvimi (data/tr-fixed-events.json) — her zaman birleştirilir
     (resmi, güvenilir; faiz kararı için otorite).
  3) YEDEK (yalnız Investing çekilemezse): ForexFactory haftalık XML (küresel) +
     TÜİK enflasyon kuralı (~ayın 3'ü).

Tasarım: yalnızca standart kütüphane. Ağ hatasında çökmez — mevcut depoyu korur.
Idempotent: aynı olayı iki kez eklemez (dedup).

Kullanım:  python3 scripts/fetch-economic-calendar.py
"""
import json
import os
import re
import sys
import html as htmllib
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(ROOT, "data", "economic-calendar.json")
TR_FIXED = os.path.join(ROOT, "data", "tr-fixed-events.json")
OUT_MD = os.path.join(ROOT, "docs", "economic-calendar.md")

# --- Investing.com ekonomik takvim AJAX uç noktası ---
INV_URL = "https://www.investing.com/economic-calendar/Service/getCalendarFilteredData"
# Ülke ID'leri: 63=Türkiye, 5=ABD, 72=Euro Bölgesi
INV_COUNTRIES = [63, 5, 72]
INV_TZ = 63  # GMT+3 (İstanbul) — saatler TR saatiyle gelir

# --- ForexFactory yedeği ---
FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
MAJOR = {"USD", "EUR", "GBP", "CNY", "JPY"}

HORIZON_DAYS = 35          # ileriye kaç gün tutalım
PRUNE_BEFORE_DAYS = 3      # geçmiş olayları kaç gün sonra silelim

TR_GUN = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
FLAG = {"TR": "🇹🇷", "USD": "🇺🇸", "EUR": "🇪🇺", "GBP": "🇬🇧", "CNY": "🇨🇳", "JPY": "🇯🇵"}

# Para birimi -> depo bölge kodu (TR bayrağı/akışı için TRY'yi TR'ye çeviriyoruz)
CUR2REGION = {"TRY": "TR", "USD": "USD", "EUR": "EUR", "GBP": "GBP", "CNY": "CNY", "JPY": "JPY"}

# Küresel olaylar için içerik kancası — AYNI ZAMANDA beyaz liste:
# yüksek etkili küresel bir olay buradaki bir anahtarla eşleşmezse takvime alınmaz
# (tahvil ihalesi, petrol stoğu, konuşmacı vb. gürültüyü ele).
GLOBAL_HOOKS = [
    ("Interest Rate Decision", "Faiz kararı — küresel faiz beklentisi TL ve borsayı etkiler."),
    ("Fed Interest Rate", "Fed faiz kararı — 'Fed faizi TL ve borsayı nasıl etkiler' explainer'ı."),
    ("Federal Funds", "Fed faiz kararı — 'Fed faizi TL ve borsayı nasıl etkiler' explainer'ı."),
    ("FOMC", "Fed/FOMC — küresel faiz beklentisi TL'yi etkiler."),
    ("Deposit Facility", "ECB faiz kararı — euro ve küresel faiz."),
    ("ECB", "ECB — euro ve küresel faiz beklentisi."),
    ("Core PCE", "ABD çekirdek enflasyon (PCE) — Fed'in tercih ettiği gösterge, dolar yönü."),
    ("CPI", "Enflasyon verisi — dolar/euro yönü ve küresel faiz beklentisi."),
    ("Nonfarm Payrolls", "ABD istihdam (NFP) — dolar ve risk iştahı."),
    ("Unemployment Rate", "İşsizlik verisi — büyüme ve faiz beklentisi."),
    ("GDP", "Büyüme verisi — küresel görünüm."),
    ("ISM", "ISM/PMI — ABD ekonomik aktivitesi, risk iştahı."),
    ("Retail Sales", "Perakende satışlar — tüketim ve büyüme sinyali."),
]

# Türkiye olayları için başlık çevirisi + kanca (Investing İngilizce başlık verir).
# (anahtar = başlıkta geçen İngilizce ibare; sırayla denenir)
TR_TITLE_MAP = [
    ("Interest Rate Decision", "TCMB faiz kararı (PPK)",
     "Faiz kararı kredi, mevduat, döviz ve borsayı doğrudan etkiler — 'faiz kararı paranı nasıl etkiler' explainer'ı."),
    ("CPI (YoY)", "TÜİK enflasyon (TÜFE, yıllık)",
     "Enflasyon verisi öncesi 'enflasyon nasıl okunur / paranı nasıl korursun' explainer'ı."),
    ("CPI (MoM)", "TÜİK enflasyon (TÜFE, aylık)",
     "Aylık enflasyon — sepet ve alım gücü yorumu."),
    ("PPI", "TÜİK üretici enflasyonu (ÜFE)",
     "ÜFE-TÜFE makası — fiyatlara yansıma beklentisi."),
    ("Unemployment Rate", "İşsizlik oranı (TÜİK)",
     "İşgücü verisi — ekonomik görünüm."),
    ("GDP", "Büyüme (GSYİH)",
     "Büyüme verisi — ekonominin gidişatı."),
    ("Trade Balance", "Dış ticaret dengesi",
     "İhracat-ithalat ve cari açık görünümü."),
    ("Current Account", "Cari işlemler dengesi",
     "Cari denge — TL ve dış finansman."),
    ("Manufacturing PMI", "İmalat PMI",
     "Sanayi aktivitesi öncü göstergesi."),
    ("Consumer Confidence", "Tüketici güven endeksi",
     "Hane halkı beklentileri."),
    ("Economic Confidence", "Ekonomik güven endeksi",
     "Genel ekonomik beklenti."),
    ("Capacity Utilization", "Kapasite kullanım oranı",
     "Sanayi kapasitesi — üretim sinyali."),
    ("Industrial Production", "Sanayi üretimi",
     "Üretim verisi — büyüme öncüsü."),
    ("Retail Sales", "Perakende satışlar",
     "Tüketim gücü göstergesi."),
]

IMP_MAP = {"bull1": "Low", "bull2": "Medium", "bull3": "High"}

# TR'de okuyucu için amiral göstergeler — Investing yıldızı düşük olsa bile
# içerik seçici yakalasın diye High'a yükselt (TÜFE, faiz, büyüme, işsizlik).
TR_FORCE_HIGH = ("enflasyon", "faiz", "büyüme", "işsizlik")


# ----------------------------- BİRİNCİL: Investing.com -----------------------------

def fetch_investing(today):
    """Investing.com ekonomik takvim — TR + küresel. Tek POST sorgusu."""
    hi = today + timedelta(days=HORIZON_DAYS)
    params = [("country[]", str(c)) for c in INV_COUNTRIES]
    params += [
        ("importance[]", "2"), ("importance[]", "3"),  # Orta + Yüksek
        ("dateFrom", today.isoformat()), ("dateTo", hi.isoformat()),
        ("timeZone", str(INV_TZ)), ("currentTab", "custom"), ("limit_from", "0"),
    ]
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(INV_URL, data=data, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.investing.com/economic-calendar/",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    })
    with urllib.request.urlopen(req, timeout=25) as r:
        payload = json.load(r)
    raw = payload.get("data", "")

    events = []
    # Gün ayraçlarını ve event satırlarını sırayla yakala
    blocks = re.findall(r'(theDay[^>]*>[^<]+<|<tr id="eventRowId_.*?</tr>)', raw, re.S)
    for b in blocks:
        if b.startswith("theDay"):
            continue
        dt = re.search(r'data-event-datetime="([^"]+)"', b)
        cur = re.search(r'flagCur[^>]*>.*?</span>\s*([A-Z]{3})', b, re.S)
        imp = re.search(r'data-img_key="(bull\d)"', b)
        tt = re.search(r'class="left event"[^>]*><a[^>]*>(.*?)</a>', b, re.S)
        if not (dt and tt):
            continue
        iso = dt.group(1).split()[0].replace("/", "-")          # 2026/07/03 -> 2026-07-03
        time_s = dt.group(1).split()[1][:5] if " " in dt.group(1) else ""
        region = CUR2REGION.get(cur.group(1) if cur else "", cur.group(1) if cur else "?")
        impact = IMP_MAP.get(imp.group(1) if imp else "", "")
        title = htmllib.unescape(re.sub("<[^>]+>", "", tt.group(1))).strip()
        title = re.sub(r"\s{2,}", " ", title)

        if region == "TR":
            tr_title, hook = tr_localize(title)
            if any(w in tr_title.lower() for w in TR_FORCE_HIGH):
                impact = "High"
            events.append({"date": iso, "time": time_s, "region": "TR",
                           "impact": impact, "title": tr_title,
                           "source": "investing", "hook": hook})
        else:
            # Küresel: yalnız yüksek etki + içerik beyaz listesi (gürültüyü ele)
            if impact != "High":
                continue
            hook = global_hook(title)
            if not hook:
                continue
            events.append({"date": iso, "time": time_s, "region": region,
                           "impact": "High", "title": title,
                           "source": "investing", "hook": hook})
    return events


def tr_localize(title):
    """TR başlığını Türkçeleştir + kanca ver. Eşleşme yoksa başlığı koru."""
    for k, tr, hook in TR_TITLE_MAP:
        if k.lower() in title.lower():
            return tr, hook
    return title, ""


def global_hook(title):
    for k, h in GLOBAL_HOOKS:
        if k.lower() in title.lower():
            return h
    return ""


# ------------------------------- YEDEK: ForexFactory -------------------------------

def fetch_forexfactory():
    """ForexFactory haftalık XML — küresel yüksek etkili (Investing çökerse yedek)."""
    req = urllib.request.Request(FF_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
    root = ET.fromstring(raw)
    events = []
    for ev in root.findall("event"):
        cur = (ev.findtext("country") or "").strip()
        impact = (ev.findtext("impact") or "").strip()
        title = (ev.findtext("title") or "").strip()
        d = (ev.findtext("date") or "").strip()
        t = (ev.findtext("time") or "").strip()
        if cur not in MAJOR or impact != "High" or not d:
            continue
        try:
            iso = datetime.strptime(d, "%m-%d-%Y").date().isoformat()
        except ValueError:
            continue
        events.append({"date": iso, "time": t, "region": cur, "impact": "High",
                       "title": title, "source": "forexfactory", "hook": global_hook(title)})
    return events


def tuik_inflation_events(today):
    """TÜİK TÜFE ~ayın 3'ünde (hafta sonu ise sonraki iş günü). Investing yedeği."""
    out = []
    y, m = today.year, today.month
    for _ in range(3):
        d = date(y, m, 3)
        while d.weekday() >= 5:
            d += timedelta(days=1)
        out.append({
            "date": d.isoformat(), "time": "10:00", "region": "TR", "impact": "High",
            "title": "TÜİK enflasyon (TÜFE) verisi", "source": "tuik-rule",
            "hook": "Enflasyon verisi öncesi 'enflasyon nasıl okunur / paranı nasıl korursun' explainer'ı.",
        })
        m += 1
        if m > 12:
            m, y = 1, y + 1
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
    source_label = ""
    fetch_ok = True
    try:
        fetched = fetch_investing(today)
        source_label = "investing"
        print(f"[+] Investing.com: {len(fetched)} olay (TR + küresel, filtreli)")
    except Exception as exc:
        fetch_ok = False
        print(f"[!] Investing çekilemedi ({exc}); ForexFactory + TÜİK kuralına düşülüyor")
        try:
            fetched += fetch_forexfactory()
            print(f"    [yedek] ForexFactory: {len(fetched)} küresel olay")
            fetch_ok = True
        except Exception as exc2:
            print(f"    [yedek] ForexFactory da çekilemedi ({exc2}); depo korunuyor")
        fetched += tuik_inflation_events(today)
        source_label = "forexfactory+tuik (yedek)"

    # Birincil kaynak (Investing) çalıştıysa, depodaki eski yedek-kaynak
    # (forexfactory/tuik-rule) kayıtlarını taşıma — tekrar/gürültü yapmasınlar.
    if source_label == "investing":
        stored = [e for e in stored if e.get("source") not in ("forexfactory", "tuik-rule")]

    candidates = stored + fetched + load_tr_fixed()

    # dedup (kaynak önceliği: tcmb > investing > forexfactory > tuik-rule > stored)
    prio = {"tcmb": 4, "investing": 3, "forexfactory": 2, "tuik-rule": 1}
    merged = {}
    for e in candidates:
        k = key(e)
        if k not in merged or prio.get(e.get("source"), 0) >= prio.get(merged[k].get("source"), 0):
            merged[k] = e

    lo = today - timedelta(days=PRUNE_BEFORE_DAYS)
    hi = today + timedelta(days=HORIZON_DAYS)
    events = [e for e in merged.values()
              if lo.isoformat() <= e["date"] <= hi.isoformat()]
    events.sort(key=lambda e: (e["date"], e.get("time", "")))

    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    with open(STORE, "w", encoding="utf-8") as f:
        json.dump({"updated": today.isoformat(), "fetch_ok": fetch_ok,
                   "source": source_label, "events": events},
                  f, ensure_ascii=False, indent=2)
    print(f"[+] Depo: {len(events)} olay (ufuk {HORIZON_DAYS} gün) -> {STORE}")

    write_markdown(events, today)


def write_markdown(events, today):
    upcoming = [e for e in events if e["date"] >= today.isoformat()]
    lines = [
        "# Ekonomik Takvim (otomatik)",
        "",
        f"> Son güncelleme: {today.isoformat()} · `scripts/fetch-economic-calendar.py` tarafından üretilir. ELLE DÜZENLEME.",
        "> Kaynaklar: Investing.com (TR + küresel, birincil), TCMB (faiz kararı), yedek: ForexFactory + TÜİK kuralı.",
        "",
        "İçerik üreticisi için: yaklaşan **🔴 High** etkili bir TR/küresel olay 1-3 gün içindeyse,",
        "o olayın `hook`'una göre bir **explainer** yazısını sıraya al (omurga evergreen akışını bozmadan).",
        "",
        "## Yaklaşan olaylar",
        "",
        "| Tarih | Gün | Saat | Bölge | Etki | Olay | İçerik fırsatı |",
        "|-------|-----|------|-------|------|------|----------------|",
    ]
    if not upcoming:
        lines.append("| — | — | — | — | — | Yaklaşan kayıtlı olay yok | — |")
    for e in upcoming:
        d = date.fromisoformat(e["date"])
        gun = TR_GUN[d.weekday()]
        flag = FLAG.get(e["region"], e["region"])
        impact = {"High": "🔴 High", "Medium": "🟡 Med", "Low": "⚪ Low"}.get(e.get("impact"), e.get("impact", ""))
        hook = (e.get("hook") or "").replace("|", "/")
        lines.append(f"| {e['date']} | {gun} | {e.get('time','')} | {flag} | {impact} | {e['title']} | {hook} |")
    lines.append("")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[+] Özet yazıldı -> {OUT_MD} ({len(upcoming)} yaklaşan olay)")


if __name__ == "__main__":
    sys.exit(main())
