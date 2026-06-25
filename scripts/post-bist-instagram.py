#!/usr/bin/env python3
"""
ParaFOMO — BIST açılış/kapanış kartını Instagram'a postlar.

bist-card.py'nin ürettiği kartı (GitHub raw URL) yayınlar. Caption ilk satırı
bist-yorum.py'den (haber+veri özeti), gerisi sabit + hashtag. dedup tarih+tip.

Kullanım:
  python3 scripts/post-bist-instagram.py --type acilis
  python3 scripts/post-bist-instagram.py --type kapanis --dry
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
ENV_FILE = os.path.expanduser("~/.config/parafomo/instagram.env")
RAW = "https://raw.githubusercontent.com/Junkiieee/parafomo/main/public/social"
API = "https://graph.facebook.com/v21.0"
HASHTAGS = "#borsa #bist #bist100 #borsaistanbul #yatırım #hisse #ekonomi #parafomo"
LABEL = {"acilis": "BIST açılış", "kapanis": "BIST kapanış"}


def tr_now():
    return datetime.now(timezone.utc) + timedelta(hours=3)


def get_comment(ptype):
    try:
        r = subprocess.run(["python3", os.path.join(SCRIPTS, "bist-yorum.py"), "--type", ptype],
                           capture_output=True, text=True, timeout=180)
        c = r.stdout.strip().split("\n")[-1].strip()
        if c:
            return c
    except Exception:
        pass
    return f"Borsa İstanbul'da günün {LABEL.get(ptype, '')} görünümü aşağıda."


def build_caption(ptype, date_label):
    comment = get_comment(ptype)
    head = "🌅 BIST Açılış" if ptype == "acilis" else "🌆 BIST Kapanış"
    body = (f"{head} · {date_label}\n"
            "BIST 100 ve günün piyasa özeti 👆\n"
            "Detaylı analizler → parafomo.com")
    return "\n\n".join([comment, body, HASHTAGS])


def load_env():
    env = {}
    for ln in open(ENV_FILE):
        ln = ln.strip()
        if ln and not ln.startswith("#") and "=" in ln:
            k, v = ln.split("=", 1)
            env[k] = v
    return env


def http_post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"error": {"message": f"HTTP {e.code}"}}


def url_ok(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "parafomo-ig/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def main():
    args = sys.argv[1:]
    ptype = args[args.index("--type") + 1] if "--type" in args else "acilis"
    dry = "--dry" in args
    force = "--force" in args

    now = tr_now()
    date_label = now.strftime("%d.%m.%Y")
    stamp = now.strftime("%Y%m%d")
    img_path = os.path.join(ROOT, "public", "social", f"bist-{ptype}-{stamp}.jpg")
    img_url = f"{RAW}/bist-{ptype}-{stamp}.jpg"
    state = os.path.join(ROOT, "logs", f"bist-{ptype}-last.txt")

    if not os.path.exists(img_path):
        sys.exit(f"[bist] HATA: kart yok ({img_path}).")

    caption = build_caption(ptype, date_label)
    print(f"[bist] {ptype} | URL: {img_url}")
    print(f"[bist] ----- caption -----\n{caption}\n[bist] -----------------")

    os.makedirs(os.path.dirname(state), exist_ok=True)
    last = open(state).read().strip() if os.path.exists(state) else ""
    if not force and last == stamp:
        print(f"[bist] {ptype} {stamp} zaten paylaşılmış."); return
    if dry:
        print("[bist] --dry: yayınlanmadı."); return
    if not url_ok(img_url):
        sys.exit(f"[bist] HATA: görsel canlı değil ({img_url}).")

    env = load_env()
    ig_id, token = env["IG_BUSINESS_ACCOUNT_ID"], env["IG_PAGE_TOKEN"]
    cont = http_post(f"{API}/{ig_id}/media", {
        "image_url": img_url, "caption": caption, "access_token": token})
    if "id" not in cont:
        sys.exit(f"[bist] HATA (konteyner): {json.dumps(cont, ensure_ascii=False)}")
    time.sleep(4)
    pub = http_post(f"{API}/{ig_id}/media_publish", {
        "creation_id": cont["id"], "access_token": token})
    if "id" not in pub:
        sys.exit(f"[bist] HATA (yayın): {json.dumps(pub, ensure_ascii=False)}")
    print(f"[bist] ✅ YAYINLANDI! media_id={pub['id']}")
    open(state, "w").write(stamp)


if __name__ == "__main__":
    main()
