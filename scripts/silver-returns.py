#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ParaFOMO — Gümüş Getiri Analizi (gold-returns.py kalıbı).

Gram gümüşün TL ve USD bazında geçmiş getirisini hesaplar:
  gram gümüş TL ≈ (ons USD / 31.1035) * USDTRY
Yahoo Finance'ten gümüş (SI=F, USD/ons), altın (GC=F, altın/gümüş oranı için) ve USD/TRY (USDTRY=X)
aylık kapanışlarını çeker; bugüne göre YTD + 1/3/5/10 yıl getirilerini TL ve USD (ons) bazında verir.

- Ağ hatası NON-FATAL; başarısızlıkta mevcut depoyu korur (asla boş yazmaz).
- Cron: daily-content.sh veri adımları.
"""
import json
import os
import sys
import datetime as dt
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
STORE = os.path.join(REPO, "data", "gumus-getiri.json")
PUBLIC = os.path.join(REPO, "public", "gumus-getiri.json")

UA = {"User-Agent": "Mozilla/5.0 (compatible; ParaFOMO/1.0)"}
OZ = 31.1035  # 1 troy ons = 31.1035 gram


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
        silver = yahoo_series("SI=F")         # USD/ons
        gold = yahoo_series("GC=F")           # USD/ons (altın/gümüş oranı)
        usdtry = yahoo_series("USDTRY=X")     # USD/TRY
    except Exception as e:
        print(f"HATA: Yahoo serileri çekilemedi: {e}", file=sys.stderr)
        return 1
    if len(silver) < 12 or len(usdtry) < 12 or len(gold) < 12:
        print("HATA: yetersiz seri verisi", file=sys.stderr)
        return 1

    def gram_tl(ts):
        _, oz_usd = nearest(silver, ts)
        _, rate = nearest(usdtry, ts)
        return (oz_usd / OZ) * rate, oz_usd

    def ratio(ts):
        return nearest(gold, ts)[1] / nearest(silver, ts)[1]

    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    now_tl, now_oz = gram_tl(now)

    rows = []
    for label, yrs in [("1 yıl", 1), ("3 yıl", 3), ("5 yıl", 5), ("10 yıl", 10)]:
        past_ts = now - int(yrs * 365.25 * 86400)
        if past_ts < silver[0][0] - 40 * 86400 or past_ts < usdtry[0][0] - 40 * 86400:
            continue
        past_tl, past_oz = gram_tl(past_ts)
        rows.append({
            "label": label,
            "years": yrs,
            "gram_tl_then": round(past_tl, 2),
            "gram_tl_now": round(now_tl, 2),
            "return_tl_pct": round((now_tl / past_tl - 1) * 100, 1),
            "oz_usd_then": round(past_oz, 2),
            "oz_usd_now": round(now_oz, 2),
            "return_usd_pct": round((now_oz / past_oz - 1) * 100, 1),
            "gold_silver_ratio_then": round(ratio(past_ts), 1),
        })

    year_start = int(dt.datetime(dt.datetime.now().year, 1, 1, tzinfo=dt.timezone.utc).timestamp())
    ytd_tl, ytd_oz = gram_tl(year_start)
    ytd = {
        "label": "Yıl başından beri",
        "gram_tl_then": round(ytd_tl, 2),
        "gram_tl_now": round(now_tl, 2),
        "return_tl_pct": round((now_tl / ytd_tl - 1) * 100, 1),
        "oz_usd_then": round(ytd_oz, 2),
        "oz_usd_now": round(now_oz, 2),
        "return_usd_pct": round((now_oz / ytd_oz - 1) * 100, 1),
    }

    if not rows:
        print("HATA: hesaplanan dönem yok", file=sys.stderr)
        return 1

    # Altın/gümüş oranının 10 yıllık aralığı (aylık kapanışlar)
    ratios = [nearest(gold, t)[1] / c for t, c in silver]
    out = {
        "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00"),
        "source": "Yahoo Finance (SI=F ons gümüş, GC=F ons altın, USDTRY=X kur); gram = ons/31.1035 × USDTRY",
        "gram_tl_now": round(now_tl, 2),
        "oz_usd_now": round(now_oz, 2),
        "gold_silver_ratio_now": round(ratio(now), 1),
        "gold_silver_ratio_min": round(min(ratios), 1),
        "gold_silver_ratio_max": round(max(ratios), 1),
        "gold_silver_ratio_avg": round(sum(ratios) / len(ratios), 1),
        "ytd": ytd,
        "periods": rows,
    }
    ten = next((r for r in rows if r["years"] == 10), rows[-1])
    out["headline_years"] = ten["years"]
    out["headline_return_tl_pct"] = ten["return_tl_pct"]
    out["headline_return_usd_pct"] = ten["return_usd_pct"]

    for path in (STORE, PUBLIC):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"[+] gumus-getiri.json yazıldı: gram {now_tl:.2f} TL, {ten['years']}y TL +%{ten['return_tl_pct']}, "
          f"USD +%{ten['return_usd_pct']}, altın/gümüş {out['gold_silver_ratio_now']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
