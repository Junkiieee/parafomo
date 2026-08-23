#!/usr/bin/env python3
"""
ParaFOMO — Güncel Dolar Endeksi (DXY) veri çekici (data/dxy.json).

/dolar-endeksi sayfası bu dosyadan build-time'da değeri okur. Site günlük
rebuild edildiği için değer her gün tazelenir. Yahoo Finance chart API'sinden
DXY (DX-Y.NYB) + endeksi oluşturan 6 döviz çiftini + bağlam için USD/TRY çeker.

Kaynak sessizce bozulabilir (bkz. learnings): fetch başarısızsa MEVCUT
data/dxy.json korunur (non-fatal), asla boş yazmaz. Tek sembol düşerse diğerleri
yine yazılır (degrade edebilir).

Kullanım: python3 scripts/dxy.py   (token harcamaz)
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "dxy.json")

# DXY sepet ağırlıkları (ICE resmi, 1999'dan beri sabit).
# (Yahoo sembol, etiket, ağırlık%, ters mi [USD paydada mı])
COMPONENTS = [
    ("EURUSD=X", "Euro (EUR)",        57.6, True),   # EUR/USD → USD payda: ters
    ("USDJPY=X", "Japon Yeni (JPY)",  13.6, False),
    ("GBPUSD=X", "İngiliz Sterlini (GBP)", 11.9, True),
    ("USDCAD=X", "Kanada Doları (CAD)",  9.1, False),
    ("USDSEK=X", "İsveç Kronu (SEK)",  4.2, False),
    ("USDCHF=X", "İsviçre Frangı (CHF)", 3.6, False),
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


def pct(price, prev):
    if price is None or prev in (None, 0):
        return None
    return round((price - prev) / prev * 100, 2)


def main():
    dxy, dxy_prev = yahoo("DX-Y.NYB")
    if dxy is None:
        print("[dxy] DXY fetch başarısız → mevcut dosya korunuyor", file=sys.stderr)
        if os.path.exists(OUT):
            return 0
        # ilk çalıştırma ve kaynak yok: yazma
        return 1

    components = []
    for sym, label, weight, invert in COMPONENTS:
        p, pc = yahoo(sym)
        if p is None:
            continue
        components.append({
            "symbol": sym, "label": label, "weight": weight,
            "rate": round(p, 4), "change": pct(p, pc),
        })

    usdtry, usdtry_prev = yahoo("USDTRY=X")

    tr_now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3)))
    TR_AY = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
             "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    etiket = f"{tr_now.day} {TR_AY[tr_now.month]} {tr_now.year}, {tr_now:%H:%M}"
    out = {
        "_aciklama": "Dolar Endeksi (DXY) ve bileşenleri. Yahoo Finance. Site günlük rebuild'de tazelenir; anlık/kesin işlem değeri değildir, göstergedir.",
        "_kaynak": "Yahoo Finance (ICE US Dollar Index DX-Y.NYB)",
        "guncellenme": tr_now.strftime("%Y-%m-%dT%H:%M:%S+03:00"),
        "guncellemeEtiket": etiket,
        "dxy": round(dxy, 3),
        "dxyChange": pct(dxy, dxy_prev),
        "dxyPrev": round(dxy_prev, 3) if dxy_prev else None,
        "usdtry": round(usdtry, 4) if usdtry else None,
        "usdtryChange": pct(usdtry, usdtry_prev),
        "components": components,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[dxy] DXY={out['dxy']} ({out['dxyChange']:+}%), {len(components)} bileşen yazıldı → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
