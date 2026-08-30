#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ParaFOMO — Dolar Getiri Analizi (özgün veri varlığı / link-mıknatısı).

Doları (USD/TRY) elde tutmanın TL bazında geçmiş getirisini hesaplar:
  "10 yıl önce 1 dolar X TL'ydi, bugün Y TL" → getiri = Y/X - 1.
Yahoo Finance'ten USD/TRY (USDTRY=X) aylık kapanışlarını çeker; bugüne göre
YTD + 1/3/5/10 yıl getirilerini verir. altin-getiri.py'nin dolar kardeşi —
"altın vs dolar getiri" kümesini tamamlar.

- Seri ağ hatası NON-FATAL; toplam başarısızlıkta mevcut depoyu korur (asla boş yazmaz).
- Cron: daily-content.sh içinde günlük tazelenir.
"""
import json
import os
import sys
import datetime as dt
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
STORE = os.path.join(REPO, "data", "dolar-getiri.json")
PUBLIC = os.path.join(REPO, "public", "dolar-getiri.json")

UA = {"User-Agent": "Mozilla/5.0 (compatible; ParaFOMO/1.0)"}


def yahoo_series(sym, rng="10y", interval="1mo"):
    """(timestamp, close) listesi döndürür (close None olanlar atlanır)."""
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + sym
        + f"?interval={interval}&range={rng}"
    )
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as fh:
        d = json.load(fh)
    res = d["chart"]["result"][0]
    ts = res["timestamp"]
    closes = res["indicators"]["quote"][0]["close"]
    out = []
    for t, c in zip(ts, closes):
        if c is not None and c > 0:
            out.append((t, float(c)))
    return out


def nearest(series, target_ts):
    """target_ts'e en yakın (ts, value) noktasını döndürür."""
    return min(series, key=lambda p: abs(p[0] - target_ts))


def main():
    try:
        usdtry = yahoo_series("USDTRY=X")     # USD/TRY
    except Exception as e:
        print(f"HATA: Yahoo serisi çekilemedi: {e}", file=sys.stderr)
        return 1
    if len(usdtry) < 12:
        print("HATA: yetersiz seri verisi", file=sys.stderr)
        return 1

    def rate(ts):
        _, r = nearest(usdtry, ts)
        return r

    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    now_rate = rate(now)

    periods = [
        ("1 yıl", 1),
        ("3 yıl", 3),
        ("5 yıl", 5),
        ("10 yıl", 10),
    ]
    rows = []
    for label, yrs in periods:
        past_ts = now - int(yrs * 365.25 * 86400)
        if past_ts < usdtry[0][0] - 40 * 86400:
            continue
        past_rate = rate(past_ts)
        rows.append({
            "label": label,
            "years": yrs,
            "usdtry_then": round(past_rate, 4),
            "usdtry_now": round(now_rate, 4),
            "return_tl_pct": round((now_rate / past_rate - 1) * 100, 1),
        })

    # YTD (yıl başı)
    year_start = int(dt.datetime(dt.datetime.now().year, 1, 1, tzinfo=dt.timezone.utc).timestamp())
    ytd_rate = rate(year_start)
    ytd = {
        "label": "Yıl başından beri",
        "usdtry_then": round(ytd_rate, 4),
        "usdtry_now": round(now_rate, 4),
        "return_tl_pct": round((now_rate / ytd_rate - 1) * 100, 1),
    }

    if not rows:
        print("HATA: hesaplanan dönem yok", file=sys.stderr)
        return 1

    out = {
        "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00"),
        "source": "Yahoo Finance (USDTRY=X kur, aylık kapanış)",
        "usdtry_now": round(now_rate, 4),
        "ytd": ytd,
        "periods": rows,
    }
    ten = next((r for r in rows if r["years"] == 10), rows[-1])
    out["headline_years"] = ten["years"]
    out["headline_return_tl_pct"] = ten["return_tl_pct"]

    for path in (STORE, PUBLIC):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"[+] dolar-getiri.json yazıldı: USD/TRY {now_rate:.2f}, 10y TL +%{ten['return_tl_pct']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
