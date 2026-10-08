#!/usr/bin/env python3
"""GSC'ye sitemap'i yeniden gönder — canlı sitemap'teki URL kümesi değiştiyse (ya da 7 günden eskiyse).

Neden: Google sitemap-index'i 2026-07-03'ten 2026-10-08'e kadar hiç yeniden indirmemişti; 10-07'de
açılan 40 halka arz sayfası "URL is unknown to Google" kaldı. Yeni sayfa açan her hat
(blog, halka arz arşivi, veri sayfaları) deploy ettikten sonra bu betik Google'ı dürter.

Kullanım:  python scripts/gsc-sitemap.py            # gerekirse gönder
           python scripts/gsc-sitemap.py --status   # yalnız durumu yaz
           python scripts/gsc-sitemap.py --force    # koşulsuz gönder
Durum: logs/gsc-sitemap-state.json (git dışı). Ağ/izin hatasında sessizce 0 döner (hattı bozmaz).
"""
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = os.path.expanduser("~/.config/parafomo/ga-sa.json")  # dashboard.py ile aynı servis hesabı
SITE = "sc-domain:parafomo.com"
FEED = "https://parafomo.com/sitemap-index.xml"
STATE = os.path.join(REPO, "logs", "gsc-sitemap-state.json")
MAX_AGE_DAYS = 7


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "parafomo-sitemap-check/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def live_urls():
    idx = fetch(FEED)
    urls = []
    for sm in re.findall(r"<loc>([^<]+)</loc>", idx):
        urls += re.findall(r"<loc>([^<]+)</loc>", fetch(sm))
    return sorted(set(urls))


def client():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds = service_account.Credentials.from_service_account_file(
        KEY, scopes=["https://www.googleapis.com/auth/webmasters"])
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def main():
    args = set(sys.argv[1:])
    try:
        sc = client()
        if "--status" in args:
            for x in sc.sitemaps().list(siteUrl=SITE).execute().get("sitemap", []):
                print(f"{x.get('path')} · gönderim {x.get('lastSubmitted')} · indirme {x.get('lastDownloaded')}")
            return 0
        urls = live_urls()
    except Exception as e:  # ağ/izin — hattı bozma
        print(f"[gsc-sitemap] UYARI: {type(e).__name__}: {str(e)[:200]}")
        return 0
    digest = hashlib.sha256("\n".join(urls).encode()).hexdigest()
    try:
        state = json.load(open(STATE))
    except Exception:
        state = {}
    now = dt.datetime.now(dt.timezone.utc)
    last = state.get("submitted_utc")
    age = (now - dt.datetime.fromisoformat(last)).days if last else 999
    changed = digest != state.get("digest")
    if not ("--force" in args or changed or age >= MAX_AGE_DAYS):
        print(f"[gsc-sitemap] değişiklik yok ({len(urls)} URL, son gönderim {age} gün önce) — atlandı")
        return 0
    try:
        sc.sitemaps().submit(siteUrl=SITE, feedpath=FEED).execute()
    except Exception as e:
        print(f"[gsc-sitemap] UYARI: gönderim başarısız: {type(e).__name__}: {str(e)[:200]}")
        return 0
    new = sorted(set(urls) - set(state.get("urls", [])))
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump({"digest": digest, "submitted_utc": now.isoformat(), "urls": urls}, open(STATE, "w"))
    print(f"[gsc-sitemap] gönderildi · {len(urls)} URL · yeni {len(new) if state else 'ilk kayıt'}")
    for u in new[:10] if state else []:
        print("   +", u)
    return 0


if __name__ == "__main__":
    sys.exit(main())
