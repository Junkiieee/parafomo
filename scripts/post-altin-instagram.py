#!/usr/bin/env python3
"""
ParaFOMO — Günlük altın fiyatları kartını Instagram'a postlar.

Akış: altin-card.py'nin ürettiği günlük kart (public/social/altin-<tarih>.jpg)
public URL'den Instagram Graph API ile yayınlanır. Caption ilk satırı
altin-yorum.py'den (haber+veri yorumu), gerisi sabit + hashtag.

NOT: Görselin önce DEPLOY edilmiş (canlı public URL) olması gerekir; orkestrasyon
altin-daily.sh bunu yapar. dedup: logs/altin-last.txt (tarih damgası).

Kullanım:
  python3 scripts/post-altin-instagram.py            # bugünün kartını postla
  python3 scripts/post-altin-instagram.py --dry      # postlama; caption+URL göster
  python3 scripts/post-altin-instagram.py --force    # aynı gün tekrar
"""
import os
import sys
import json
import time
import subprocess
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
STATE_FILE = os.path.join(ROOT, "logs", "altin-last.txt")
ENV_FILE = os.path.expanduser("~/.config/parafomo/instagram.env")
SITE = "https://parafomo.com"
# Görsel public URL: GitHub raw (repo public) — push'tan saniyeler sonra canlı,
# site build'ini beklemeye gerek yok. IG bu URL'den görseli kendi çeker.
RAW = "https://raw.githubusercontent.com/Junkiieee/parafomo/main/public/social"
API = "https://graph.facebook.com/v21.0"

HASHTAGS = ("#altın #gramaltın #çeyrekaltın #altınfiyatları #cumhuriyetaltını "
            "#yatırım #ekonomi #parafomo")


def tr_now():
    return datetime.now(timezone.utc) + timedelta(hours=3)


def load_env():
    env = {}
    if not os.path.exists(ENV_FILE):
        sys.exit(f"[altin] HATA: {ENV_FILE} yok")
    for ln in open(ENV_FILE):
        ln = ln.strip()
        if ln and not ln.startswith("#") and "=" in ln:
            k, v = ln.split("=", 1)
            env[k] = v
    for k in ("IG_BUSINESS_ACCOUNT_ID", "IG_PAGE_TOKEN"):
        if not env.get(k):
            sys.exit(f"[altin] HATA: {ENV_FILE} içinde {k} yok")
    return env


def get_comment():
    try:
        r = subprocess.run(["python3", os.path.join(SCRIPTS, "altin-yorum.py")],
                           capture_output=True, text=True, timeout=180)
        c = r.stdout.strip().split("\n")[-1].strip()
        if c:
            return c
    except Exception:
        pass
    return "Güncel altın fiyatları aşağıda."


def build_caption(date_label):
    comment = get_comment()
    body = (f"📊 Güncel altın fiyatları · {date_label}\n"
            "Gram, çeyrek, yarım, tam, cumhuriyet 👆\n"
            "Detaylı analizler → parafomo.com")
    return "\n\n".join([comment, body, HASHTAGS])


def http_post(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"error": {"message": f"HTTP {e.code}", "raw": str(e)}}


def url_ok(url):
    try:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "parafomo-ig/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def main():
    args = sys.argv[1:]
    dry = "--dry" in args
    force = "--force" in args

    now = tr_now()
    date_label = now.strftime("%d.%m.%Y")
    stamp = now.strftime("%Y%m%d")
    img_path = os.path.join(ROOT, "public", "social", f"altin-{stamp}.jpg")
    img_url = f"{RAW}/altin-{stamp}.jpg"

    if not os.path.exists(img_path):
        sys.exit(f"[altin] HATA: kart yok ({img_path}). Önce altin-card.py çalıştır.")

    caption = build_caption(date_label)
    print(f"[altin] görsel : {img_path}")
    print(f"[altin] URL    : {img_url}")
    print(f"[altin] ----- caption -----\n{caption}\n[altin] -----------------")

    # dedup (gün damgası)
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    last = open(STATE_FILE).read().strip() if os.path.exists(STATE_FILE) else ""
    if not force and last == stamp:
        print(f"[altin] {stamp} zaten paylaşılmış, atlanıyor (--force ile zorla)")
        return

    if dry:
        print("[altin] --dry: yayınlanmadı.")
        return

    if not url_ok(img_url):
        sys.exit(f"[altin] HATA: görsel canlı değil ({img_url}). Önce deploy et.")

    env = load_env()
    ig_id, token = env["IG_BUSINESS_ACCOUNT_ID"], env["IG_PAGE_TOKEN"]

    cont = http_post(f"{API}/{ig_id}/media", {
        "image_url": img_url, "caption": caption, "access_token": token,
    })
    if "id" not in cont:
        sys.exit(f"[altin] HATA (konteyner): {json.dumps(cont, ensure_ascii=False)}")
    creation_id = cont["id"]
    print(f"[altin] konteyner: {creation_id}")
    time.sleep(4)

    pub = http_post(f"{API}/{ig_id}/media_publish", {
        "creation_id": creation_id, "access_token": token,
    })
    if "id" not in pub:
        sys.exit(f"[altin] HATA (yayın): {json.dumps(pub, ensure_ascii=False)}")
    print(f"[altin] ✅ YAYINLANDI! media_id={pub['id']}")
    open(STATE_FILE, "w").write(stamp)


if __name__ == "__main__":
    main()
