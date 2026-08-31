#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ParaFOMO — BIST 100 Getiri Analizi (özgün veri varlığı / link-mıknatısı).

Borsayı (BIST 100 endeksi) elde tutmanın TL bazında geçmiş getirisini hesaplar:
  "10 yıl önce BIST 100 X puandı, bugün Y puan" → getiri = Y/X - 1.
Yahoo Finance'ten XU100.IS aylık kapanışlarını çeker; bugüne göre
YTD + 1/3/5/10 yıl getirilerini verir. altin-getiri.py / dollar-returns.py'nin
kardeşi — "altın vs dolar vs borsa getiri" kümesini tamamlar.

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
STORE = os.path.join(REPO, "data", "bist-getiri.json")
PUBLIC = os.path.join(REPO, "public", "bist-getiri.json")

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
        bist = yahoo_series("XU100.IS")     # BIST 100 endeksi (TL puan)
    except Exception as e:
        print(f"HATA: Yahoo serisi çekilemedi: {e}", file=sys.stderr)
        return 1
    if len(bist) < 12:
        print("HATA: yetersiz seri verisi", file=sys.stderr)
        return 1

    def level(ts):
        _, r = nearest(bist, ts)
        return r

    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    now_level = level(now)

    periods = [
        ("1 yıl", 1),
        ("3 yıl", 3),
        ("5 yıl", 5),
        ("10 yıl", 10),
    ]
    rows = []
    for label, yrs in periods:
        past_ts = now - int(yrs * 365.25 * 86400)
        if past_ts < bist[0][0] - 40 * 86400:
            continue
        past_level = level(past_ts)
        rows.append({
            "label": label,
            "years": yrs,
            "bist_then": round(past_level, 2),
            "bist_now": round(now_level, 2),
            "return_tl_pct": round((now_level / past_level - 1) * 100, 1),
        })

    # YTD (yıl başı)
    year_start = int(dt.datetime(dt.datetime.now().year, 1, 1, tzinfo=dt.timezone.utc).timestamp())
    ytd_level = level(year_start)
    ytd = {
        "label": "Yıl başından beri",
        "bist_then": round(ytd_level, 2),
        "bist_now": round(now_level, 2),
        "return_tl_pct": round((now_level / ytd_level - 1) * 100, 1),
    }

    if not rows:
        print("HATA: hesaplanan dönem yok", file=sys.stderr)
        return 1

    out = {
        "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00"),
        "source": "Yahoo Finance (XU100.IS BIST 100 endeksi, aylık kapanış)",
        "bist_now": round(now_level, 2),
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
    print(f"[+] bist-getiri.json yazıldı: BIST 100 {now_level:.0f}, 10y TL +%{ten['return_tl_pct']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
