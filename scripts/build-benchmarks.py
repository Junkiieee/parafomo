#!/usr/bin/env python3
"""Kıyas serileri → data/benchmarks.json

Aylık kapanışlar (Yahoo chart API): USD/TRY, BIST 100 (XU100), gram altın TL
(ons USD × kur ÷ 31,1035). Uygulamadaki "ne olsaydı" kıyası ve metal detay
grafikleri bu dosyadan beslenir; app'e deploy-app.sh kopyalar.

Cron: ayın 2'si (scripts/benchmarks-update.sh) · elle: python3 scripts/build-benchmarks.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone

OUT = "/root/parafomo/data/benchmarks.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) parafomo-benchmarks/1.0"
OZ = 31.1034768  # troy ons → gram


def yahoo_monthly(symbol: str, rng: str = "15y") -> dict[str, float]:
    """Ay kapanışları — GÜNLÜK seriden türetilir (aylık mumlar boşluklu geliyor).

    Her ay için son işlem gününün kapanışı alınır.
    """
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?range={rng}&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    res = data["chart"]["result"][0]
    ts = res["timestamp"]
    closes = res["indicators"]["quote"][0]["close"]
    out: dict[str, float] = {}
    for t, c in zip(ts, closes):
        if c is None:
            continue
        ym = datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m")
        out[ym] = float(c)  # kronolojik sırada geldiği için ayın SON kapanışı kalır
    return out


def main() -> None:
    usd = yahoo_monthly("USDTRY=X")
    time.sleep(1)
    xu = yahoo_monthly("XU100.IS")
    time.sleep(1)
    gc = yahoo_monthly("GC=F")  # ons altın USD
    time.sleep(1)
    si = yahoo_monthly("SI=F")  # ons gümüş USD

    months = sorted(set(usd) & set(gc))
    series = []
    for ym in months:
        row = {"ay": ym, "usd": round(usd[ym], 4),
               "gold": round(gc[ym] * usd[ym] / OZ, 2)}
        if ym in xu:
            row["xu100"] = round(xu[ym], 2)
        if ym in si:
            row["silver"] = round(si[ym] * usd[ym] / OZ, 2)
        series.append(row)

    # mantık bekçisi: seri kısaysa ya da son ay çok eskiyse yazma
    if len(series) < 60:
        sys.exit(f"HATA: seri beklenenden kısa ({len(series)} ay) — yazılmadı")
    now = datetime.now(timezone.utc).strftime("%Y-%m")
    if series[-1]["ay"] < f"{int(now[:4]) - 1}":
        sys.exit("HATA: son ay bir yıldan eski görünüyor — kaynak bozuk olabilir")

    doc = {
        "_aciklama": ("Aylık kapanışlar: usd=USD/TRY, gold=gram altın TL (GC=F×kur÷31,1035), "
                      "xu100=BIST 100 endeksi. Kaynak: Yahoo Finance chart API."),
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "months": series,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print(f"[benchmarks] {len(series)} ay yazıldı ({series[0]['ay']} → {series[-1]['ay']}) · "
          f"son: usd {series[-1]['usd']} · gram altın {series[-1]['gold']} ₺ · xu100 {series[-1].get('xu100')}")


if __name__ == "__main__":
    main()
