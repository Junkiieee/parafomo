#!/usr/bin/env python3
"""Instagram kaydırmalı gönderi (carousel) yayıncısı — public/social/carousel/<slug>/1.jpg… + slaytlar.json "caption".

Graph API akışı: her görsel için is_carousel_item konteyneri → CAROUSEL konteyneri (children + caption) → media_publish.
Görseller parafomo.com'da yayında olmalı (IG URL'yi kendi çeker): önce commit + deploy.
Yayın kilidi: /root/parafomo-data/PUBLISH_PAUSED varsa yalnız ONAYLI_YAYIN=1 ile; panelde Instagram kapalıysa atlar.

  ONAYLI_YAYIN=1 /root/.venvs/parafomo/bin/python scripts/instagram-carousel.py <slug> [--dry]
"""
import glob
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://graph.facebook.com/v21.0"
SITE = "https://parafomo.com"
KONTROL = "/root/parafomo-data/dash/kontrol.json"
SONUC = "/root/parafomo-data/dash/carousel-yayinlar.json"


def env():
    e = {}
    for line in open(os.path.expanduser("~/.config/parafomo/instagram.env"), encoding="utf-8"):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            e[k] = v
    return e


def istek(method, path, data=None):
    url = f"{API}/{path}"
    body = urllib.parse.urlencode(data).encode() if data and method == "POST" else None
    if data and method == "GET":
        url += "?" + urllib.parse.urlencode(data)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body, method=method), timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"error": {"message": f"HTTP {e.code}"}}


def bekle_hazir(cid, tok, deneme=20):
    for _ in range(deneme):
        r = istek("GET", cid, {"fields": "status_code", "access_token": tok})
        if r.get("status_code") == "FINISHED":
            return True
        if r.get("status_code") == "ERROR":
            return False
        time.sleep(3)
    return False


def main():
    slug = sys.argv[1]
    dry = "--dry" in sys.argv
    d = os.path.join(ROOT, "public", "social", "carousel", slug)
    spec = json.load(open(os.path.join(d, "slaytlar.json"), encoding="utf-8"))
    n = len(glob.glob(os.path.join(d, "[0-9]*.jpg")))
    urls = [f"{SITE}/social/carousel/{slug}/{i}.jpg" for i in range(1, n + 1)]
    caption = spec["caption"]
    print(f"[carousel] {slug}: {n} slayt\n{caption}\n")
    if not 2 <= n <= 10:
        sys.exit("[carousel] HATA: 2–10 slayt olmalı")
    try:
        if not json.load(open(KONTROL, encoding="utf-8")).get("instagram", True):
            print("[carousel] panelde Instagram kapalı — atlandı"); return
    except (OSError, ValueError):
        pass
    for u in urls:
        try:
            with urllib.request.urlopen(urllib.request.Request(u, method="HEAD"), timeout=20) as r:
                assert r.status == 200
        except Exception:
            sys.exit(f"[carousel] HATA: görsel canlı değil: {u} (önce deploy)")
    if dry:
        print("[carousel] --dry: yayınlanmadı"); return
    e = env()
    ig, tok = e["IG_BUSINESS_ACCOUNT_ID"], e["IG_PAGE_TOKEN"]
    cocuk = []
    for u in urls:
        r = istek("POST", f"{ig}/media", {"image_url": u, "is_carousel_item": "true", "access_token": tok})
        if "id" not in r:
            sys.exit(f"[carousel] HATA (slayt): {json.dumps(r, ensure_ascii=False)[:300]}")
        cocuk.append(r["id"])
    for c in cocuk:
        if not bekle_hazir(c, tok):
            sys.exit(f"[carousel] HATA: slayt konteyneri hazır olmadı: {c}")
    r = istek("POST", f"{ig}/media", {"media_type": "CAROUSEL", "children": ",".join(cocuk), "caption": caption, "access_token": tok})
    if "id" not in r:
        sys.exit(f"[carousel] HATA (carousel): {json.dumps(r, ensure_ascii=False)[:300]}")
    if not bekle_hazir(r["id"], tok):
        sys.exit("[carousel] HATA: carousel konteyneri hazır olmadı")
    p = istek("POST", f"{ig}/media_publish", {"creation_id": r["id"], "access_token": tok})
    if "id" not in p:
        sys.exit(f"[carousel] HATA (yayın): {json.dumps(p, ensure_ascii=False)[:300]}")
    perma = istek("GET", p["id"], {"fields": "permalink", "access_token": tok}).get("permalink", "")
    kayit = {}
    try:
        kayit = json.load(open(SONUC, encoding="utf-8"))
    except (OSError, ValueError):
        pass
    kayit[slug] = {"media_id": p["id"], "permalink": perma, "zaman": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    json.dump(kayit, open(SONUC, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[carousel] ✅ yayınlandı: {p['id']} {perma}")


if __name__ == "__main__":
    if os.path.exists("/root/parafomo-data/PUBLISH_PAUSED") and "--dry" not in sys.argv and os.environ.get("ONAYLI_YAYIN") != "1":
        print("[durduruldu] PUBLISH_PAUSED var — yalnız ONAYLI_YAYIN=1 ile yayın."); sys.exit(0)
    main()
