#!/usr/bin/env python3
"""
ParaFOMO — Instagram STORY postlar (Graph API media_type=STORIES).

Verilen public görsel URL'ini 1080x1920 hikaye olarak yayınlar (24 saat görünür).

Kullanım:
  python3 scripts/post-story-instagram.py <public_image_url>
  python3 scripts/post-story-instagram.py <url> --dry
"""
import os
import sys
import json
import time
import urllib.parse
import urllib.request
import urllib.error

ENV_FILE = os.path.expanduser("~/.config/parafomo/instagram.env")
API = "https://graph.facebook.com/v21.0"


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
    if not args:
        sys.exit("Kullanım: post-story-instagram.py <url> [--dry]")
    img_url = args[0]
    dry = "--dry" in args
    print(f"[story] URL: {img_url}")
    if dry:
        print("[story] --dry: yayınlanmadı."); return
    if not url_ok(img_url):
        sys.exit(f"[story] HATA: görsel canlı değil ({img_url}).")
    env = load_env()
    ig_id, token = env["IG_BUSINESS_ACCOUNT_ID"], env["IG_PAGE_TOKEN"]
    cont = http_post(f"{API}/{ig_id}/media", {
        "image_url": img_url, "media_type": "STORIES", "access_token": token})
    if "id" not in cont:
        sys.exit(f"[story] HATA (konteyner): {json.dumps(cont, ensure_ascii=False)}")
    time.sleep(4)
    pub = http_post(f"{API}/{ig_id}/media_publish", {
        "creation_id": cont["id"], "access_token": token})
    if "id" not in pub:
        sys.exit(f"[story] HATA (yayın): {json.dumps(pub, ensure_ascii=False)}")
    print(f"[story] ✅ STORY YAYINLANDI! media_id={pub['id']}")


if __name__ == "__main__":
    main()
