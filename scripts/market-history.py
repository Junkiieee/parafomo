#!/usr/bin/env python3
"""
ParaFOMO — geçmiş piyasa verisi (ücretsiz, Yahoo Finance; API key yok).

"Geri-dönük getiri" ve "karşılaştırma" viral formatları için GERÇEK geçmiş seri
sağlar. Sayılar uydurma değil, canlı veriden hesaplanır.

Enstrümanlar:
  gold  → gram altın (TL)  = (XAU ons USD / 31.1035) × USDTRY   (GC=F + USDTRY=X)
  usd   → dolar/TL                                              (USDTRY=X)
  bist  → BIST 100                                              (XU100.IS)

API (key yok):
  https://query1.finance.yahoo.com/v8/finance/chart/<symbol>?range=<r>&interval=<i>

Kullanım (CLI test):
  python3 scripts/market-history.py gold --range 1y
  python3 scripts/market-history.py compare --range 1y
"""
import sys
import json
import time
import argparse
import datetime
import urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
GRAMS_PER_OZ = 31.1035

LABELS = {"gold": "Gram Altın", "usd": "Dolar/TL", "bist": "BIST 100"}
UNITS = {"gold": "TL", "usd": "TL", "bist": ""}


def _fetch(symbol, rng, interval):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib_q(symbol)}"
           f"?range={rng}&interval={interval}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            data = json.load(urllib.request.urlopen(req, timeout=25))
            break
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(1.5)
    res = data["chart"]["result"][0]
    ts = res["timestamp"]
    close = res["indicators"]["quote"][0]["close"]
    out = [(t, c) for t, c in zip(ts, close) if c is not None]
    return out


def urllib_q(s):
    import urllib.parse
    return urllib.parse.quote(s, safe="")


def _month_label(ts):
    d = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
    return d.strftime("%m/%y")


def _to_monthly(series):
    """[(ts,val)] → ay başına TEK nokta (mükerrer ayı son değerle birleştir), sıralı."""
    by_lbl = {}
    for t, v in series:
        by_lbl[_month_label(t)] = (t, v)   # aynı ay tekrar gelirse son değer kazanır
    return sorted(by_lbl.values())          # ts'ye göre sıralı


def gram_altin_series(rng, interval):
    """GC=F (USD/ons) ve USDTRY=X'i ay etiketine göre hizalayıp gram altın TL üretir."""
    gold = _to_monthly(_fetch("GC=F", rng, interval))
    usd = _to_monthly(_fetch("USDTRY=X", rng, interval))
    um = {_month_label(t): v for t, v in usd}
    series = []
    for t, c in gold:
        lbl = _month_label(t)
        if lbl in um:
            series.append((t, (c / GRAMS_PER_OZ) * um[lbl]))
    return series


def instrument(name, rng="1y", interval="1mo"):
    """Tek enstrüman → {name,label,unit,points,x,start,end,pct}."""
    if name == "gold":
        series = gram_altin_series(rng, interval)
    elif name == "usd":
        series = _to_monthly(_fetch("USDTRY=X", rng, interval))
    elif name == "bist":
        series = _to_monthly(_fetch("XU100.IS", rng, interval))
    else:
        raise ValueError(f"bilinmeyen enstrüman: {name}")
    if len(series) < 2:
        raise RuntimeError(f"{name}: yetersiz veri ({len(series)} nokta)")
    pts = [round(v, 2) for _, v in series]
    xs = [_month_label(t) for t, _ in series]
    start, end = pts[0], pts[-1]
    pct = round((end - start) / start * 100)
    return {"name": name, "label": LABELS[name], "unit": UNITS[name],
            "points": pts, "x": xs, "start": start, "end": end, "pct": pct}


def compare(rng="1y", interval="1mo"):
    """Üç enstrümanın aynı dönemdeki yüzde getirisi (karşılaştırma formatı)."""
    items = []
    for n in ("gold", "usd", "bist"):
        try:
            d = instrument(n, rng, interval)
            items.append({"name": d["label"], "key": n, "pct": d["pct"],
                          "start": d["start"], "end": d["end"], "unit": d["unit"]})
        except Exception as e:
            print(f"[i] {n} alınamadı: {str(e)[:60]}", file=sys.stderr)
    items.sort(key=lambda i: i["pct"], reverse=True)
    return {"period": rng, "items": items}


def backtest(name, amount=10000, rng="1y", interval="1mo"):
    """amount TL'yi dönem başında al → bugünkü değer + getiri."""
    d = instrument(name, rng, interval)
    end_val = round(amount * d["end"] / d["start"])
    return {**d, "amount": amount, "end_value": end_val,
            "profit": end_val - amount}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gold", "usd", "bist", "compare", "backtest"])
    ap.add_argument("--range", default="1y")
    ap.add_argument("--interval", default="1mo")
    ap.add_argument("--amount", type=int, default=10000)
    args = ap.parse_args()
    if args.cmd == "compare":
        out = compare(args.range, args.interval)
    elif args.cmd == "backtest":
        out = backtest("gold", args.amount, args.range, args.interval)
    else:
        out = instrument(args.cmd, args.range, args.interval)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
