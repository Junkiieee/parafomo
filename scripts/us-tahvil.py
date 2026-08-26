#!/usr/bin/env python3
"""
ParaFOMO — Güncel ABD Hazine tahvil faizleri (data/us-tahvil.json).

/abd-tahvil-faizi sayfası bu dosyadan build-time'da değeri okur. Site günlük
rebuild edildiği için değer her gün tazelenir. Yahoo Finance chart API'sinden
ABD getiri eğrisini (3 ay / 5 yıl / 10 yıl / 30 yıl) + bağlam için USD/TRY çeker.

Kaynak sessizce bozulabilir (bkz. learnings): fetch başarısızsa MEVCUT
data/us-tahvil.json korunur (non-fatal), asla boş yazmaz. Tek sembol düşerse
diğerleri yine yazılır (degrade edebilir).

Kullanım: python3 scripts/us-tahvil.py   (token harcamaz)
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "us-tahvil.json")

# Yahoo getiri endeksleri — değer doğrudan yüzde (ör. 4.639 = %4,639).
# (Yahoo sembol, etiket, kısa vade etiketi)
TENORS = [
    ("^IRX", "3 Aylık (13 hafta)", "3A"),
    ("^FVX", "5 Yıllık", "5Y"),
    ("^TNX", "10 Yıllık", "10Y"),
    ("^TYX", "30 Yıllık", "30Y"),
]


def yahoo(symbol):
    """Yahoo chart → (fiyat, önceki_kapanış). Ağ/JSON hatası → (None, None)."""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ParaFOMO"})
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode("utf-8", "ignore"))
        m = d["chart"]["result"][0]["meta"]
        price = m.get("regularMarketPrice")
        prev = m.get("chartPreviousClose") or m.get("previousClose")
        return price, prev
    except Exception:
        return None, None


def bp(price, prev):
    """Baz puan (bps) değişimi. 1 bps = %0,01 faiz."""
    if price is None or prev is None:
        return None
    return round((price - prev) * 100, 1)


def main():
    tenors = []
    by_key = {}
    for sym, label, key in TENORS:
        p, pc = yahoo(sym)
        if p is None:
            continue
        item = {
            "symbol": sym, "label": label, "key": key,
            "yield": round(p, 3), "changeBps": bp(p, pc),
            "prev": round(pc, 3) if pc is not None else None,
        }
        tenors.append(item)
        by_key[key] = item

    if not tenors:
        print("[us-tahvil] tüm fetch başarısız → mevcut dosya korunuyor", file=sys.stderr)
        return 0 if os.path.exists(OUT) else 1

    usdtry, usdtry_prev = yahoo("USDTRY=X")

    # 10Y-3M spread (Fed'in favori resesyon göstergesi): negatif = ters eğri.
    spread = None
    if "10Y" in by_key and "3A" in by_key:
        spread = round(by_key["10Y"]["yield"] - by_key["3A"]["yield"], 3)

    tr_now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3)))
    TR_AY = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
             "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    etiket = f"{tr_now.day} {TR_AY[tr_now.month]} {tr_now.year}, {tr_now:%H:%M}"
    out = {
        "_aciklama": "ABD Hazine tahvil faizleri (getiri eğrisi). Yahoo Finance. Site günlük rebuild'de tazelenir; anlık/kesin işlem değeri değildir, göstergedir.",
        "_kaynak": "Yahoo Finance (CBOE tahvil getiri endeksleri: ^IRX, ^FVX, ^TNX, ^TYX)",
        "guncellenme": tr_now.strftime("%Y-%m-%dT%H:%M:%S+03:00"),
        "guncellemeEtiket": etiket,
        "us10y": by_key.get("10Y", {}).get("yield"),
        "us10yChangeBps": by_key.get("10Y", {}).get("changeBps"),
        "spread10y3m": spread,
        "inverted": (spread is not None and spread < 0),
        "usdtry": round(usdtry, 4) if usdtry else None,
        "tenors": tenors,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[us-tahvil] 10Y={out['us10y']}% ({out['us10yChangeBps']:+} bps), spread(10Y-3A)={spread}, {len(tenors)} vade yazıldı → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
