#!/usr/bin/env python3
"""Günlük Instagram trend radarı: Türkçe para hesaplarında hangi Reels patlıyor?

Neden (Kaan 2026-11-17: "Instagram için de aynı araştırmayı yapabilir miyiz?"): Instagram API başka hesapları aramaya
izin vermiyor (hashtag araması Meta incelemesi istiyor), ama işletme/üretici hesaplarının herkese açık Reels'ini
izlenme, beğeni ve yorumla verir (business_discovery). Bu betik takip listesindeki para hesaplarının son Reels'ini
çeker ve hesabın kendi ortancasının çok üstüne çıkanları işaretler. İlk koşuda örnek: @lordlutfu 1.816 takipçiyle
Reel başına ortanca 317 bin izlenme ("İş arkadaşımla aynı maaşı alıyoruz…" 2,6 milyon).

Takip listesi kendini büyütür: yt_trend.py'nin bulduğu YouTube kanallarının açıklamalarındaki Instagram adları
denenir; işletme/üretici hesabıysa ve son 30 günde Reel paylaştıysa listeye girer.

Çıktı repo DIŞINDA: /root/parafomo-data/trend/ig-trend.json, liste: ig-hesaplar.json.
Yalnız GET. Jeton hiçbir yere yazılmaz/basılmaz. Kullanım: python3 scripts/learn/ig_trend.py [--kuru]
"""
import argparse
import datetime as dt
import json
import os
import re
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from yt_trend import SIYASI, PARA  # noqa: E402  (aynı süzgeçler)

ENV = os.path.expanduser("~/.config/parafomo/instagram.env")
API = "https://graph.facebook.com/v21.0"
DIR = "/root/parafomo-data/trend"
OUT = os.path.join(DIR, "ig-trend.json")
LISTE = os.path.join(DIR, "ig-hesaplar.json")
YT = os.path.join(DIR, "yt-trend.json")
TAHMIN = re.compile(r"devalüasyon|olası|tahmin|çökecek|çöküş|uçacak|düşecek|yükselecek|patlayacak|kriz geliyor", re.I)
BASLANGIC = ["lordlutfu", "harunkevrek", "herkodolog", "apara", "tayinsepeti", "dunyagazetesi"]   # 2026-11-17 doğrulandı
IG_AD = re.compile(r"instagram\.com/([A-Za-z0-9_.]{2,30})|(?:instagram|ig|insta)\s*[:：\-–]?\s*@([A-Za-z0-9_.]{2,30})", re.I)


def env():
    e = {}
    for ln in open(ENV, encoding="utf-8"):
        if "=" in ln and not ln.lstrip().startswith("#"):
            k, v = ln.strip().split("=", 1)
            e[k.strip()] = v.strip()
    return e


E = None


def bd(username, n=20):
    """business_discovery: hesabın son n gönderisi. Hata → None (mesajda jeton olmaz)."""
    fields = (f"business_discovery.username({username}){{username,followers_count,media.limit({n})"
              "{id,caption,media_product_type,timestamp,like_count,comments_count,view_count,permalink,thumbnail_url}}")
    q = urllib.parse.urlencode({"fields": fields, "access_token": E["IG_PAGE_TOKEN"]})
    try:
        with urllib.request.urlopen(f"{API}/{E['IG_BUSINESS_ACCOUNT_ID']}?{q}", timeout=40) as r:
            return json.loads(r.read().decode()).get("business_discovery")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        return None


def kesif(liste, simdi):
    """YouTube radarındaki kanalların açıklamalarından yeni Instagram hesabı adayları (en çok 15 deneme/gün)."""
    try:
        yt = json.load(open(YT, encoding="utf-8"))
        ids = list(dict.fromkeys(x["kanal_id"] for x in yt.get("en_cok", []) + yt.get("patlayan_kucuk", []) if x.get("kanal_id")))
    except (OSError, ValueError):
        return 0
    denenen = set(liste.get("denenen", []))
    ids = [i for i in ids if i not in denenen][:50]
    if not ids:
        return 0
    from yt_trend import servis
    r = servis().channels().list(part="snippet", id=",".join(ids)).execute()
    eklenen = 0
    for c in r.get("items", []):
        liste.setdefault("denenen", []).append(c["id"])
        m = IG_AD.search(c["snippet"].get("description") or "")
        if not m:
            continue
        u = (m.group(1) or m.group(2)).strip(".").lower()
        if u in liste["hesaplar"] or u in ("p", "reel", "reels", "explore", "stories", "accounts", "tv"):
            continue
        d = bd(u, 12)
        if not d:
            continue
        reels = [x for x in d.get("media", {}).get("data", []) if x.get("media_product_type") == "REELS"]
        taze = any(simdi - dt.datetime.fromisoformat(x["timestamp"].replace("+0000", "+00:00")) < dt.timedelta(days=30) for x in reels)
        metin = " ".join((x.get("caption") or "")[:200] for x in reels)
        if taze and PARA.search(metin) and not SIYASI.search(metin):
            liste["hesaplar"][u] = {"eklendi": simdi.date().isoformat(), "kaynak": f"YouTube: {c['snippet'].get('title', '')[:40]}"}
            eklenen += 1
    liste["denenen"] = liste["denenen"][-2000:]
    return eklenen


def main():
    global E
    ap = argparse.ArgumentParser()
    ap.add_argument("--kuru", action="store_true")
    ap.add_argument("--gun", type=int, default=10, help="patlayan Reel için en çok yaş (gün)")
    a = ap.parse_args()
    E = env()
    simdi = dt.datetime.now(dt.timezone.utc)
    os.makedirs(DIR, exist_ok=True)
    try:
        liste = json.load(open(LISTE, encoding="utf-8"))
    except (OSError, ValueError):
        liste = {"hesaplar": {u: {"eklendi": "2026-11-17", "kaynak": "elle doğrulandı"} for u in BASLANGIC}}
    yeni = 0 if a.kuru else kesif(liste, simdi)
    patlayan, hepsi, hesap_ozet = [], [], []
    for u in list(liste["hesaplar"]):
        d = bd(u)
        if not d:
            liste["hesaplar"][u]["hata"] = simdi.date().isoformat()
            continue
        reels = [x for x in d.get("media", {}).get("data", []) if x.get("media_product_type") == "REELS" and x.get("view_count") is not None]
        if not reels:
            continue
        med = statistics.median(x["view_count"] for x in reels)
        hesap_ozet.append({"hesap": u, "takipci": d.get("followers_count"), "ortanca": round(med)})
        for x in reels:
            yas = (simdi - dt.datetime.fromisoformat(x["timestamp"].replace("+0000", "+00:00"))).total_seconds() / 86400
            cap = (x.get("caption") or "").replace("\n", " ").strip()
            if yas > a.gun or SIYASI.search(cap) or TAHMIN.search(cap):
                continue
            satir = {"hesap": u, "takipci": d.get("followers_count"), "izlenme": x["view_count"], "begeni": x.get("like_count"),
                     "yorum": x.get("comments_count"), "gun": round(yas, 1), "kat": round(x["view_count"] / max(med, 1), 1),
                     "kanca": re.split(r"(?<=[.!?…])\s", cap)[0][:140], "url": x.get("permalink"), "kapak": x.get("thumbnail_url")}
            hepsi.append(satir)
            if x["view_count"] >= max(2.5 * med, 50000):
                patlayan.append(satir)
    patlayan.sort(key=lambda s: -s["izlenme"])
    hepsi.sort(key=lambda s: -s["izlenme"])
    out = {"tarih": simdi.isoformat(timespec="seconds"), "hesap_sayisi": len(hesap_ozet), "yeni_hesap": yeni,
           "hesaplar": hesap_ozet, "patlayan": patlayan[:15], "en_cok": hepsi[:15],
           "not": "Yalnız açı ve kanca ilhamı; metin, rakam ve karakter KOPYALANMAZ. Siyasi ve tahmin içerikli olanlar ayıklandı."}
    print(f"[ig-trend] {len(hesap_ozet)} hesap ({yeni} yeni), {len(hepsi)} Reel (son {a.gun} gün), {len(patlayan)} patlayan")
    for s in patlayan[:8]:
        print(f"   {s['izlenme']:>9,} izl · @{s['hesap']} ({s['takipci']:,} takipçi, ortancanın {s['kat']} katı) · {s['kanca'][:70]}")
    if a.kuru:
        return 0
    for p_, o in ((OUT, out), (LISTE, liste)):
        json.dump(o, open(p_ + ".tmp", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        os.replace(p_ + ".tmp", p_)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:   # ağ/izin hatası: eski dosya kalır, çağıran hat bozulmaz (jeton mesaja girmez)
        print(f"[ig-trend] HATA: {type(e).__name__}", file=sys.stderr)
        sys.exit(1)
