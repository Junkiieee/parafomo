#!/usr/bin/env python3
"""IndexNow — yeni/değişen URL'leri Bing, Yandex, Seznam, Naver'a anında bildir.

Neden: Google dışı arama motorları (Bing → ChatGPT/Copilot araması, DuckDuckGo; Yandex
Türkiye'de) siteyi yalnız kendi tarama hızlarıyla keşfediyordu. IndexNow tek POST ile tüm
katılımcı motorlara URL'i iletir; anahtar dosyası public/<anahtar>.txt ile kanıtlanır.

Kullanım:  python3 scripts/indexnow.py          # canlı sitemap'te yeni/lastmod'u değişen URL'ler
           python3 scripts/indexnow.py --all    # sitemap'teki her URL (ilk kurulum)
           python3 scripts/indexnow.py URL...   # yalnız verilen URL'ler
Durum: logs/indexnow-state.json (git dışı). Ağ hatasında sessizce 0 döner (hattı bozmaz).
"""
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = "parafomo.com"
KEY = "e073f91a9fc9acf20d58e42f85d2b3fc"
FEED = f"https://{HOST}/sitemap-index.xml"
ENDPOINT = "https://api.indexnow.org/indexnow"
STATE = os.path.join(REPO, "logs", "indexnow-state.json")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "parafomo-indexnow/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def sitemap_entries():
    """{url: lastmod-or-''} canlı sitemap'ten."""
    out = {}
    for sm in re.findall(r"<loc>([^<]+)</loc>", fetch(FEED)):
        for block in re.findall(r"<url>(.*?)</url>", fetch(sm), re.S):
            loc = re.search(r"<loc>([^<]+)</loc>", block)
            mod = re.search(r"<lastmod>([^<]+)</lastmod>", block)
            if loc:
                out[loc.group(1)] = mod.group(1) if mod else ""
    return out


def submit(urls):
    total = 0
    for i in range(0, len(urls), 10000):
        body = json.dumps({
            "host": HOST, "key": KEY,
            "keyLocation": f"https://{HOST}/{KEY}.txt",
            "urlList": urls[i:i + 10000],
        }).encode()
        req = urllib.request.Request(ENDPOINT, data=body, method="POST",
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"[indexnow] {len(urls[i:i + 10000])} URL → HTTP {r.status}")
        total += len(urls[i:i + 10000])
    return total


def main():
    args = sys.argv[1:]
    try:
        state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    except Exception:
        state = {}
    try:
        if args and args[0] != "--all":
            submit(args)
            return 0
        entries = sitemap_entries()
        if "--all" in args:
            todo = sorted(entries)
        else:
            todo = sorted(u for u, m in entries.items() if state.get(u) != m)
        if not todo:
            print("[indexnow] yeni/değişen URL yok")
            return 0
        submit(todo)
        state.update({u: entries[u] for u in todo})
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        json.dump(state, open(STATE, "w"), indent=0)
    except Exception as e:  # ağ — hattı bozma
        print(f"[indexnow] UYARI: gönderilemedi: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
