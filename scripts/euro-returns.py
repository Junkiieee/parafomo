#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ParaFOMO — Euro Getiri Analizi (dollar-returns.py kalıbı).

Euroyu (EUR/TRY) elde tutmanın TL bazında geçmiş getirisini hesaplar ve aynı dönemde doları
(USD/TRY) yan yana koyar — "euro mu dolar mı" karar sorusu için:
  getiri = bugünkü kur / o günkü kur - 1;  EUR/USD paritesi = EURTRY / USDTRY (türetilmiş).
Yahoo Finance'ten EURTRY=X ve USDTRY=X aylık kapanışları; YTD + 1/3/5/10 yıl.

- Seri ağ hatası NON-FATAL; başarısızlıkta mevcut depoyu korur (asla boş yazmaz).
- Cron: daily-content.sh veri adımları.
"""
import json
import os
import sys
import datetime as dt
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
STORE = os.path.join(REPO, "data", "euro-getiri.json")
PUBLIC = os.path.join(REPO, "public", "euro-getiri.json")

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
        eurtry = yahoo_series("EURTRY=X")
        usdtry = yahoo_series("USDTRY=X")
    except Exception as e:
        print(f"HATA: Yahoo serileri çekilemedi: {e}", file=sys.stderr)
        return 1
    if len(eurtry) < 12 or len(usdtry) < 12:
        print("HATA: yetersiz seri verisi", file=sys.stderr)
        return 1

    def rates(ts):
        e = nearest(eurtry, ts)[1]
        u = nearest(usdtry, ts)[1]
        return e, u

    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    e_now, u_now = rates(now)

    def row(label, past_ts, years=None):
        e, u = rates(past_ts)
        r = {
            "label": label,
            "eurtry_then": round(e, 4),
            "eurtry_now": round(e_now, 4),
            "return_tl_pct": round((e_now / e - 1) * 100, 1),
            "usdtry_then": round(u, 4),
            "usd_return_tl_pct": round((u_now / u - 1) * 100, 1),
            "eurusd_then": round(e / u, 4),
            "eurusd_change_pct": round(((e_now / u_now) / (e / u) - 1) * 100, 1),
        }
        if years is not None:
            r["years"] = years
        return r

    rows = []
    for label, yrs in [("1 yıl", 1), ("3 yıl", 3), ("5 yıl", 5), ("10 yıl", 10)]:
        past_ts = now - int(yrs * 365.25 * 86400)
        if past_ts < eurtry[0][0] - 40 * 86400 or past_ts < usdtry[0][0] - 40 * 86400:
            continue
        rows.append(row(label, past_ts, yrs))

    year_start = int(dt.datetime(dt.datetime.now().year, 1, 1, tzinfo=dt.timezone.utc).timestamp())
    ytd = row("Yıl başından beri", year_start)

    if not rows:
        print("HATA: hesaplanan dönem yok", file=sys.stderr)
        return 1

    out = {
        "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00"),
        "source": "Yahoo Finance (EURTRY=X ve USDTRY=X kur, aylık kapanış); EUR/USD = EURTRY ÷ USDTRY",
        "eurtry_now": round(e_now, 4),
        "usdtry_now": round(u_now, 4),
        "eurusd_now": round(e_now / u_now, 4),
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
    print(f"[+] euro-getiri.json yazıldı: EUR/TRY {e_now:.2f}, {ten['years']}y TL +%{ten['return_tl_pct']} "
          f"(dolar +%{ten['usd_return_tl_pct']}), EUR/USD {e_now / u_now:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
