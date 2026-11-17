#!/usr/bin/env python3
"""Günlük YouTube trend radarı: son günlerde Türkçe para/finans Shorts'ta ne patlıyor?

Neden (Kaan 2026-11-17: "her gün çok izleme almak için araştırmalar yapıp videolar hazırla"): ilk elle araştırmada
2-4 bin aboneli yeni kanalların 2D para hikâyeleri 1+ milyon izlendi; patlayan açılar haftadan haftaya değişiyor.
Bu betik her gece son N günün en çok izlenen Türkçe para Shorts'larını ve KÜÇÜK kanalda patlayanları bulur.
hikaye_uret.py bunları senaryo istemine yalnız "açı ve başlık kalıbı ilhamı" olarak verir: rakam, iddia,
karakter KOPYALANMAZ; siyasi içerik işaretlenir ve kullanılmaz.

Çıktı repo DIŞINDA: /root/parafomo-data/trend/yt-trend.json (başkalarının içerik listesi herkese açık repoya girmez).
Yalnız okuma: search.list (100 birim), videos.list ve channels.list (1 birim). Günde 8 arama ≈ 850 birim
(proje kotası 10.000/gün; Shorts yükleme başına ≈ 1.650). Hata olursa eski dosyaya dokunmaz.

Kullanım: python3 scripts/learn/yt_trend.py [--gun 7] [--arama 8] [--kuru]
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

OAUTH = "/root/.config/parafomo/youtube_oauth.json"
SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
OUT = "/root/parafomo-data/trend/yt-trend.json"

# Her gün bu havuzdan sırayla --arama kadarı (gün sırasına göre döner; bir haftada hepsi taranır)
SORGULAR = ["maaş", "zam", "asgari ücret", "emekli maaşı", "altın", "enflasyon", "kira", "para biriktirmek",
            "zengin fakir", "ne kadar kazanır", "dolar", "kredi kartı", "memur maaşı", "ev almak", "borç", "fiyatlar"]
PARA = re.compile(r"para|maaş|zam|altın|dolar|euro|enflasyon|kira|emekli|asgari|kredi|borç|zengin|fakir|birikim|"
                  r"biriktir|yatırım|lira|\btl\b|₺|ücret|fiyat|kazan|harca|bütçe|banka|faiz|vergi|ev al|araba|"
                  r"maliyet|ucuz|pahalı|market|sepet|gram|çeyrek|borsa|hisse|memur|işçi|patron|kirac", re.I)
TURKCE = re.compile(r"[ğışĞİŞ]")   # yalnız Türkçeye özgü harfler (ç/ö/ü İspanyolca, Almanca, Endonezce başlıkları da geçiriyordu)
SIYASI = re.compile(r"erdoğan|akp|ak parti|chp|mhp|imamoğlu|özgür özel|bahçeli|hükümet|bakan\b|bakanı|milletvekil|"
                    r"seçim|iktidar|muhalefet|saray|cumhurbaşkan|meclis|tbmm|kayyum|dolandır|çalındı|aklama", re.I)


def servis():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    cfg = json.load(open(OAUTH))
    creds = Credentials(token=None, refresh_token=cfg["refresh_token"], client_id=cfg["client_id"],
                        client_secret=cfg["client_secret"], token_uri="https://oauth2.googleapis.com/token", scopes=[SCOPE])
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def saniye(iso):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 9999
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gun", type=int, default=7)
    ap.add_argument("--arama", type=int, default=8)
    ap.add_argument("--kuru", action="store_true", help="dosyaya yazma, özet bas")
    a = ap.parse_args()
    simdi = dt.datetime.now(dt.timezone.utc)
    bas = (simdi - dt.timedelta(days=a.gun)).strftime("%Y-%m-%dT%H:%M:%SZ")
    k = simdi.timetuple().tm_yday * a.arama % len(SORGULAR)
    sorgular = [SORGULAR[(k + i) % len(SORGULAR)] for i in range(min(a.arama, len(SORGULAR)))]
    yt = servis()
    kota, ids = 0, []
    for q in sorgular:
        r = yt.search().list(part="id", q=q, type="video", videoDuration="short", regionCode="TR", relevanceLanguage="tr",
                             publishedAfter=bas, order="viewCount", maxResults=50).execute()
        kota += 100
        ids += [x["id"]["videoId"] for x in r.get("items", []) if x.get("id", {}).get("videoId")]
    ids = list(dict.fromkeys(ids))
    videolar = []
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50])).execute()
        kota += 1
        videolar += r.get("items", [])
    kanal_ids = list({v["snippet"]["channelId"] for v in videolar})
    abone = {}
    for i in range(0, len(kanal_ids), 50):
        r = yt.channels().list(part="statistics", id=",".join(kanal_ids[i:i + 50])).execute()
        kota += 1
        for c in r.get("items", []):
            st = c.get("statistics", {})
            abone[c["id"]] = None if st.get("hiddenSubscriberCount") else int(st.get("subscriberCount", 0))
    satir = []
    for v in videolar:
        sn, st = v["snippet"], v.get("statistics", {})
        metin = f"{sn.get('title', '')} {sn.get('description', '')[:300]} {' '.join(sn.get('tags', [])[:15])}"
        if saniye(v.get("contentDetails", {}).get("duration")) > 180 or not TURKCE.search(metin[:420]) or not PARA.search(metin):
            continue
        izl = int(st.get("viewCount", 0))
        yas = max(0.25, (simdi - dt.datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))).total_seconds() / 86400)
        ab = abone.get(sn["channelId"])
        satir.append({"baslik": sn.get("title", "")[:120], "kanal": sn.get("channelTitle", "")[:60], "kanal_id": sn["channelId"], "abone": ab,
                      "izlenme": izl, "gunluk": round(izl / yas), "gun": round(yas, 1),
                      "sure": saniye(v["contentDetails"].get("duration")), "url": f"https://youtu.be/{v['id']}",
                      "siyasi": bool(SIYASI.search(metin)), "yorum": int(st.get("commentCount", 0) or 0),
                      "kapak": ((sn.get("thumbnails") or {}).get("high") or (sn.get("thumbnails") or {}).get("medium") or {}).get("url")})
    satir.sort(key=lambda x: -x["izlenme"])
    en_cok = [x for x in satir if not x["siyasi"]][:25]
    kucuk = [x for x in satir if not x["siyasi"] and x["abone"] is not None and x["abone"] < 20000 and x["izlenme"] >= 50000][:15]
    out = {"tarih": simdi.isoformat(timespec="seconds"), "gun": a.gun, "aramalar": sorgular, "kota": kota,
           "toplam": len(satir), "en_cok": en_cok, "patlayan_kucuk": kucuk,
           "not": "Yalnız açı ve başlık kalıbı ilhamı; rakam, iddia ve karakter KOPYALANMAZ. Siyasi içerik ayıklandı."}
    print(f"[trend] {len(sorgular)} arama ({', '.join(sorgular)}), {len(satir)} Türkçe para Shorts'u, "
          f"{len(kucuk)} küçük kanalda patlayan · ≈{kota} kota birimi")
    for x in (kucuk or en_cok)[:8]:
        print(f"   {x['izlenme']:>9,} izl · {x['abone'] if x['abone'] is not None else '?':>7} abone · {x['baslik'][:70]}")
    if a.kuru:
        return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT + ".tmp", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(OUT + ".tmp", OUT)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:   # ağ/kota hatası: eski dosya kalır, çağıran hat bozulmaz
        print(f"[trend] HATA: {str(e)[:300]}", file=sys.stderr)
        sys.exit(1)
