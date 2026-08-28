#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ParaFOMO — 2026 Halka Arz Getiri Analizi (özgün veri varlığı / link-mıknatısı).

data/halka-arz.json'daki TAMAMLANMIŞ (borsada işlem gören) halka arzları alır,
her biri için Yahoo Finance'ten güncel BIST fiyatını çeker ve halka arz fiyatına
göre getiriyi (%) hesaplar. Sonucu data/halka-arz-getiri.json + public kopyasına yazar.

- Her kod için ağ hatası NON-FATAL (o kodu atlar, diğerlerini sürdürür).
- Yahoo'da bulunmayan (çok yeni / kod eşleşmeyen) arzlar sessizce dışarıda kalır.
- Toplam başarısızlıkta mevcut depoyu korur (asla boş yazmaz).

Cron: halka-arz-update.sh içinden çağrılır (fiyatlar 6 saatte bir tazelenir).
"""
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = os.path.join(REPO, "data", "halka-arz.json")
STORE = os.path.join(REPO, "data", "halka-arz-getiri.json")
PUBLIC = os.path.join(REPO, "public", "halka-arz-getiri.json")

UA = {"User-Agent": "Mozilla/5.0 (compatible; ParaFOMO/1.0)"}


def parse_price(s):
    """'76,60 TL' -> 76.60 (binlik ayıracı '.', ondalık ',')."""
    if not s:
        return None
    s = re.sub(r"[^0-9,.]", "", s)
    if not s:
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        v = float(s)
        return v if v > 0 else None
    except ValueError:
        return None


def yahoo_price(sym):
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + sym
        + "?interval=1d&range=1d"
    )
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=15) as fh:
        d = json.load(fh)
    meta = d["chart"]["result"][0]["meta"]
    return meta.get("regularMarketPrice")


def main():
    try:
        src = json.load(open(SRC, encoding="utf-8"))
    except Exception as e:
        print(f"HATA: halka-arz.json okunamadı: {e}", file=sys.stderr)
        return 1

    rows = []
    for i in src.get("items", []):
        if i.get("status") != "Tamamlandı":
            continue
        code = (i.get("bist_code") or "").strip()
        ipo = parse_price(i.get("price", ""))
        if not code or not ipo:
            continue
        try:
            cur = yahoo_price(code + ".IS")
        except Exception:
            cur = None
        if not cur or cur <= 0:
            continue
        ret = (cur - ipo) / ipo * 100.0
        rows.append(
            {
                "code": code,
                "company": i.get("company", ""),
                "link": i.get("link", ""),
                "start": i.get("start"),
                "date_text": i.get("date_text", ""),
                "ipo_price": round(ipo, 2),
                "current_price": round(cur, 2),
                "return_pct": round(ret, 1),
            }
        )
        time.sleep(0.3)

    if not rows:
        print("UYARI: hiç getiri hesaplanamadı; mevcut depo korunuyor.", file=sys.stderr)
        return 0 if os.path.exists(STORE) else 1

    rows.sort(key=lambda r: -r["return_pct"])
    n = len(rows)
    avg = round(sum(r["return_pct"] for r in rows) / n, 1)
    pos = sum(1 for r in rows if r["return_pct"] > 0)
    best = rows[0]
    worst = rows[-1]

    out = {
        "updated": time.strftime("%Y-%m-%dT%H:%M+00:00", time.gmtime()),
        "source": "Halka arz fiyatı: halkarz.com · Güncel fiyat: Yahoo Finance (BIST)",
        "count": n,
        "avg_return_pct": avg,
        "positive_count": pos,
        "positive_pct": round(100 * pos / n),
        "best": {"code": best["code"], "return_pct": best["return_pct"]},
        "worst": {"code": worst["code"], "return_pct": worst["return_pct"]},
        "items": rows,
    }

    with open(STORE, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    try:
        os.makedirs(os.path.dirname(PUBLIC), exist_ok=True)
        with open(PUBLIC, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"UYARI: public kopya yazılamadı: {e}", file=sys.stderr)

    print(f"[+] {n} halka arz getirisi yazıldı (ort %{avg}, {pos}/{n} pozitif) -> {STORE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
