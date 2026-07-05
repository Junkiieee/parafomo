#!/usr/bin/env python3
"""
ParaFOMO — Gündem yakalayıcı (ekonomik takvim → viral news_reaction tetikleyici).

data/economic-calendar.json'daki tarihli + impact:High olayları okur; GÜNÜ GELEN
(bugün) bir yüksek-etkili olay varsa ve o gün için henüz gündem videosu üretilmediyse
`viral-daily.sh --format news_reaction --topic "..."` için hazır bir KONU üretir.

Kanıt (izlenme verisi): gündem-tepki videoları eğitici "nedir" videolarının 5-10 katı
açılış yapıyor (Fed 138/gün, FOMC 186/gün) → bu hattı OTOMATİK besler.

Durum: logs/news-covered.txt (gitignore'lu) → her satır işlenmiş bir TARİH (YYYY-MM-DD).
Günde en fazla 1 gündem videosu (aynı günün birden çok High olayı tek konuya iner).

Komutlar (shorts-state.py arayüzünü taklit eder):
  next            → "<tarih>\t<konu>"  (bugün uygun/işlenmemiş olay yoksa BOŞ çıktı)
  mark <tarih>    → tarihi covered listesine ekle (video başarıyla üretildikten SONRA)

Seçenekler:
  --date YYYY-MM-DD   bugünü ez (test için; varsayılan: UTC bugün)
  --window N          bugün + N gün ileriye bak (varsayılan 0 = yalnız bugün)

Çıkış kodu: 0 (her zaman; boş çıktı = tetikleme yok). Hata durumları stderr'e yazılır.
"""
import os
import sys
import json
import argparse
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = os.path.join(ROOT, "data", "economic-calendar.json")
COVERED = os.path.join(ROOT, "logs", "news-covered.txt")

# Bölge önceliği: yerel izleyici TR verisine en çok tepki verir, sonra ABD (dolar), sonra AB.
REGION_PRIORITY = {"TR": 0, "USD": 1, "USA": 1, "EUR": 2}


def load_covered():
    if not os.path.exists(COVERED):
        return set()
    with open(COVERED, encoding="utf-8") as f:
        return {ln.strip() for ln in f if ln.strip() and not ln.startswith("#")}


def today_utc():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")


def pick_event(target_dates, covered):
    """target_dates penceresindeki, işlenmemiş günlerin en öncelikli High olayını döndür."""
    try:
        cal = json.load(open(CAL, encoding="utf-8"))
    except Exception as e:
        print(f"HATA: takvim okunamadı: {e}", file=sys.stderr)
        return None
    cands = []
    for e in cal.get("events", []):
        if e.get("impact") != "High":
            continue
        d = e.get("date", "")
        if d not in target_dates or d in covered:
            continue
        cands.append(e)
    if not cands:
        return None
    # Sırala: en yakın tarih → bölge önceliği → saat (gün içi ilk). Aynı günün birden çok
    # High olayı olsa da yalnız EN öncelikli biri seçilir (o gün 'mark' ile kapanır).
    cands.sort(key=lambda e: (
        e.get("date", ""),
        REGION_PRIORITY.get(e.get("region", ""), 9),
        e.get("time", "") or "99:99",
    ))
    return cands[0]


def build_topic(e):
    """viral-script.py'nin news_reaction --topic'ine geçecek net, Türkçe odaklı konu."""
    title = (e.get("title") or "").strip()
    region = (e.get("region") or "").strip()
    hook = (e.get("hook") or "").strip()
    base = f"{title} ({region})" if region else title
    return f"{base} — {hook}" if hook else base


def cmd_next(args, covered):
    base = args.date or today_utc()
    start = datetime.datetime.strptime(base, "%Y-%m-%d").date()
    target = {(start + datetime.timedelta(days=i)).isoformat()
              for i in range(0, max(args.window, 0) + 1)}
    e = pick_event(target, covered)
    if not e:
        # boş çıktı: çağıran shell tetikleme yapmaz
        return 0
    print(f"{e['date']}\t{build_topic(e)}")
    return 0


def cmd_mark(args):
    if not args.value:
        print("HATA: mark için tarih gerekli (YYYY-MM-DD)", file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(COVERED), exist_ok=True)
    covered = load_covered()
    if args.value in covered:
        return 0
    with open(COVERED, "a", encoding="utf-8") as f:
        f.write(args.value + "\n")
    print(f"[+] gündem işaretlendi: {args.value}", file=sys.stderr)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["next", "mark"])
    ap.add_argument("value", nargs="?", default="")
    ap.add_argument("--date", default="")
    ap.add_argument("--window", type=int, default=0)
    args = ap.parse_args()

    if args.cmd == "mark":
        return cmd_mark(args)
    return cmd_next(args, load_covered())


if __name__ == "__main__":
    sys.exit(main())
