#!/usr/bin/env python3
"""
ParaFOMO — BIST halka arz takvimi toplayıcı.

Halkarz.com (BİRİNCİL, ücretsiz kaynak) WordPress REST API'sinden en güncel halka
arz kayıtlarını (şirketleri) çeker, her kaydın künye sayfasını ayrıştırarak tarih,
fiyat/aralık, dağıtım yöntemi, pay (lot), aracı kurum ve BİST kodunu çıkarır.
Sonucu kalıcı bir depoya yazar (data/halka-arz.json). Sayfa (src/pages/halka-arz.astro)
bu JSON'u build sırasında okur; günlük cron çalıştığı için takvim güncel kalır.

Tasarım: yalnızca standart kütüphane. Ağ hatasında çökmez — mevcut depoyu korur.
Tarihe göre durum belirler: Devam Ediyor / Yaklaşan / Tarih Bekleniyor / Tamamlandı.

Kullanım:  python3 scripts/fetch-halka-arz.py
"""
import json
import os
import re
import sys
import time
import html as htmllib
import urllib.request
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(ROOT, "data", "halka-arz.json")

BASE = "https://halkarz.com"
FIELDS = "id,slug,link,title,date,modified"
LIST_URL = BASE + "/wp-json/wp/v2/posts?per_page=50&_fields=" + FIELDS
CAT_URL = BASE + "/wp-json/wp/v2/categories?slug={slug}&_fields=id"
YEAR_URL = BASE + "/wp-json/wp/v2/posts?categories={cid}&per_page=50&_fields=" + FIELDS
UA = "Mozilla/5.0 (compatible; ParaFOMO/1.0; +https://parafomo.com)"
SOURCE_NAME = "halkarz.com"

# Geçmiş halka arzlardan kaç tanesini takvimde tutalım (en yeni tamamlananlar).
KEEP_COMPLETED = 12

TR_MONTHS = {
    "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4,
    "mayıs": 5, "mayis": 5, "haziran": 6, "temmuz": 7, "ağustos": 8,
    "agustos": 8, "eylül": 9, "eylul": 9, "ekim": 10, "kasım": 11,
    "kasim": 11, "aralık": 12, "aralik": 12,
}
MONTH_RE = "|".join(sorted(TR_MONTHS, key=len, reverse=True))


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def clean(s):
    """HTML etiketlerini at, varlıkları çöz, boşlukları sıkıştır."""
    s = re.sub(r"<[^>]+>", " ", s)
    s = htmllib.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def parse_tr_dates(text):
    """'25-26 Aralık 2025' / '29 Eylül - 1 Ekim 2025' / '5 Aralık 2025' ->
    (start_iso, end_iso). Tarih yoksa (Hazırlanıyor... vb.) (None, None)."""
    low = text.lower()
    ym = re.search(r"(20\d{2})", low)
    if not ym:
        return (None, None)
    year = int(ym.group(1))
    # Sırayla token'ları topla: gün sayıları ve ay adları.
    tokens = re.findall(r"\d{1,2}|" + MONTH_RE, low)
    pending_days, pairs = [], []  # pairs: (day, month)
    for tok in tokens:
        if tok in TR_MONTHS:
            month = TR_MONTHS[tok]
            for d in pending_days:
                pairs.append((d, month))
            pending_days = []
        elif tok.isdigit():
            n = int(tok)
            if 1 <= n <= 31:
                pending_days.append(n)
    dates = []
    for d, m in pairs:
        try:
            dates.append(date(year, m, d))
        except ValueError:
            pass
    if not dates:
        return (None, None)
    return (min(dates).isoformat(), max(dates).isoformat())


def parse_detail(html):
    """Künye tablosundan alan->değer çıkar."""
    m = re.search(r'<table class="sp-table".*?</table>', html, re.S)
    block = m.group(0) if m else html
    fields = {}
    for em, td in re.findall(r"<em>([^<:]+):\s*</em>.*?<td>(.*?)</td>", block, re.S):
        label = clean(em)
        # Aracı kurum hücresinde konsorsiyum listesi olabilir; ilk değeri al.
        val = clean(td)
        if label:
            fields[label] = val
    # Tarih <time datetime="..."> içinde de olabilir; metni yeterli.
    return fields


def first(fields, *keys):
    for k in keys:
        for fk, v in fields.items():
            if fk.lower().startswith(k.lower()):
                return v
    return ""


def is_pending(s):
    s = (s or "").lower()
    return (not s) or ("hazırlan" in s) or ("hazirlan" in s) or ("belli deg" in s) or ("belli değ" in s)


def status_for(start, end):
    if not start:
        return "Tarih Bekleniyor"
    today = date.today().isoformat()
    if today < start:
        return "Yaklaşan"
    if start <= today <= (end or start):
        return "Devam Ediyor"
    return "Tamamlandı"


def year_category_id(year):
    try:
        data = json.loads(fetch(CAT_URL.format(slug=year)))
        return data[0]["id"] if data else None
    except Exception:
        return None


def gather_posts():
    """En yeni başvurular (taslak/yaklaşan akışı) + içinde bulunulan ve önceki yıl
    kategorileri (tarihli/tamamlanan halka arzlar). Slug'a göre tekilleştirilir."""
    seen, posts = set(), []
    sources = [LIST_URL]
    this_year = date.today().year
    for y in (this_year, this_year - 1):
        cid = year_category_id(str(y))
        if cid:
            sources.append(YEAR_URL.format(cid=cid))
    for url in sources:
        try:
            for p in json.loads(fetch(url)):
                slug = p.get("slug", "")
                if slug and slug not in seen:
                    seen.add(slug)
                    posts.append(p)
        except Exception as e:
            print(f"    [uyarı] liste alınamadı {url}: {e}", file=sys.stderr)
    return posts


def build():
    posts = gather_posts()
    items = []
    for p in posts:
        slug = p.get("slug", "")
        link = p.get("link") or (BASE + "/" + slug + "/")
        title = clean((p.get("title") or {}).get("rendered", "")) or slug
        try:
            html = fetch(link)
        except Exception as e:  # tek sayfa hatası tüm işi bozmasın
            print(f"    [uyarı] {slug}: {e}", file=sys.stderr)
            continue
        f = parse_detail(html)
        date_text = first(f, "Halka Arz Tarihi")
        price = first(f, "Halka Arz Fiyat")
        if is_pending(date_text):
            date_text = ""
        start, end = parse_tr_dates(date_text) if date_text else (None, None)
        items.append({
            "company": title,
            "bist_code": first(f, "Bist Kodu", "BİST Kodu", "Borsa Kodu"),
            "slug": slug,
            "link": link,
            "date_text": date_text,
            "start": start,
            "end": end,
            "status": status_for(start, end),
            "price": "" if is_pending(price) else price,
            "distribution": first(f, "Dağıtım Yöntemi"),
            "lot": first(f, "Pay"),
            "broker": first(f, "Aracı Kurum"),
        })
        time.sleep(0.3)

    # Tamamlananları sınırla, gerisini koru.
    completed = [i for i in items if i["status"] == "Tamamlandı"]
    completed.sort(key=lambda i: i.get("end") or i.get("start") or "", reverse=True)
    keep_completed = {id(i) for i in completed[:KEEP_COMPLETED]}
    items = [i for i in items if i["status"] != "Tamamlandı" or id(i) in keep_completed]

    # Sıralama: Devam Ediyor > Yaklaşan (tarihe göre) > Tarih Bekleniyor > Tamamlandı.
    order = {"Devam Ediyor": 0, "Yaklaşan": 1, "Tarih Bekleniyor": 2, "Tamamlandı": 3}
    items.sort(key=lambda i: (
        order.get(i["status"], 9),
        i.get("start") or ("9999" if i["status"] != "Tamamlandı" else ""),
    ))
    if any(i["status"] == "Tamamlandı" for i in items):
        # Tamamlananları en yeni önce.
        comp = [i for i in items if i["status"] == "Tamamlandı"]
        comp.sort(key=lambda i: i.get("end") or i.get("start") or "", reverse=True)
        items = [i for i in items if i["status"] != "Tamamlandı"] + comp

    return {
        "updated": datetime.now().astimezone().isoformat(timespec="minutes"),
        "source": SOURCE_NAME,
        "source_url": BASE,
        "count": len(items),
        "items": items,
    }


def main():
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    try:
        data = build()
    except Exception as e:
        print(f"HATA: halka arz verisi çekilemedi: {e}", file=sys.stderr)
        if os.path.exists(STORE):
            print("Mevcut depo korunuyor.", file=sys.stderr)
            return 0
        return 1
    if not data["items"]:
        print("UYARI: hiç kayıt bulunamadı; depo güncellenmiyor.", file=sys.stderr)
        return 0 if os.path.exists(STORE) else 1
    with open(STORE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    n = sum(1 for i in data["items"] if i["status"] in ("Yaklaşan", "Devam Ediyor"))
    print(f"[+] {data['count']} kayıt yazıldı ({n} aktif/yaklaşan) -> {STORE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
