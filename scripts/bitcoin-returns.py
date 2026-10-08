#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ParaFOMO — Bitcoin Getiri Analizi (gold-returns.py kalıbı).

Bitcoin'in TL ve USD bazında geçmiş getirisini ve en büyük düşüşlerini hesaplar:
  BTC TL ≈ BTC-USD × USDTRY
Yahoo Finance'ten BTC-USD ve USDTRY=X aylık kapanışları; YTD + 1/3/5/10 yıl getirisi,
10 yılın en büyük zirveden düşüşü (aylık kapanışlarla) ve bugün zirveden uzaklık.

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
STORE = os.path.join(REPO, "data", "bitcoin-getiri.json")
PUBLIC = os.path.join(REPO, "public", "bitcoin-getiri.json")

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


def max_drawdown(points):
    """(ts, değer) listesinde en büyük zirveden-dibe düşüş: (yüzde, zirve_ts, dip_ts)."""
    peak_v, peak_t = points[0][1], points[0][0]
    worst = (0.0, peak_t, peak_t)
    for t, v in points:
        if v > peak_v:
            peak_v, peak_t = v, t
        dd = (v / peak_v - 1) * 100
        if dd < worst[0]:
            worst = (dd, peak_t, t)
    return worst


def ym(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m")


def main():
    try:
        btc = yahoo_series("BTC-USD")
        usdtry = yahoo_series("USDTRY=X")
    except Exception as e:
        print(f"HATA: Yahoo serileri çekilemedi: {e}", file=sys.stderr)
        return 1
    if len(btc) < 12 or len(usdtry) < 12:
        print("HATA: yetersiz seri verisi", file=sys.stderr)
        return 1

    def price(ts):
        _, usd = nearest(btc, ts)
        _, rate = nearest(usdtry, ts)
        return usd * rate, usd

    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    now_tl, now_usd = price(now)

    def row(label, past_ts, years=None):
        tl, usd = price(past_ts)
        r = {
            "label": label,
            "btc_tl_then": round(tl, 2),
            "btc_tl_now": round(now_tl, 2),
            "return_tl_pct": round((now_tl / tl - 1) * 100, 1),
            "btc_usd_then": round(usd, 2),
            "btc_usd_now": round(now_usd, 2),
            "return_usd_pct": round((now_usd / usd - 1) * 100, 1),
        }
        if years is not None:
            r["years"] = years
        return r

    rows = []
    for label, yrs in [("1 yıl", 1), ("3 yıl", 3), ("5 yıl", 5), ("10 yıl", 10)]:
        past_ts = now - int(yrs * 365.25 * 86400)
        if past_ts < btc[0][0] - 40 * 86400 or past_ts < usdtry[0][0] - 40 * 86400:
            continue
        rows.append(row(label, past_ts, yrs))
    year_start = int(dt.datetime(dt.datetime.now().year, 1, 1, tzinfo=dt.timezone.utc).timestamp())
    ytd = row("Yıl başından beri", year_start)

    if not rows:
        print("HATA: hesaplanan dönem yok", file=sys.stderr)
        return 1

    usd_pts = btc
    tl_pts = [(t, c * nearest(usdtry, t)[1]) for t, c in btc]
    dd_usd, pk_usd, tr_usd = max_drawdown(usd_pts)
    dd_tl, pk_tl, tr_tl = max_drawdown(tl_pts)
    ath_usd = max(c for _, c in usd_pts)
    out = {
        "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00"),
        "source": "Yahoo Finance (BTC-USD, USDTRY=X; aylık kapanış); BTC TL = BTC-USD × USDTRY",
        "btc_tl_now": round(now_tl, 2),
        "btc_usd_now": round(now_usd, 2),
        "max_drawdown_usd_pct": round(dd_usd, 1),
        "max_drawdown_usd_from": ym(pk_usd),
        "max_drawdown_usd_to": ym(tr_usd),
        "max_drawdown_tl_pct": round(dd_tl, 1),
        "max_drawdown_tl_from": ym(pk_tl),
        "max_drawdown_tl_to": ym(tr_tl),
        "ath_usd_monthly_close": round(ath_usd, 2),
        "from_ath_usd_pct": round((now_usd / ath_usd - 1) * 100, 1),
        "ytd": ytd,
        "periods": rows,
    }
    longest = next((r for r in rows if r["years"] == 10), rows[-1])
    out["headline_years"] = longest["years"]
    out["headline_return_tl_pct"] = longest["return_tl_pct"]
    out["headline_return_usd_pct"] = longest["return_usd_pct"]

    for path in (STORE, PUBLIC):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"[+] bitcoin-getiri.json yazıldı: BTC {now_usd:,.0f} $ / {now_tl:,.0f} TL, {longest['years']}y TL +%"
          f"{longest['return_tl_pct']}, max düşüş $ %{out['max_drawdown_usd_pct']} ({ym(pk_usd)}→{ym(tr_usd)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
