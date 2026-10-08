#!/usr/bin/env python3
"""Deploy sonrası canlı sayfayı bekle — headless ajanın for/until curl döngüsü yerine.

Kullanım: python3 scripts/wait-live.py URL [URL ...] [--contains METİN] [--timeout 600]
Her URL 200 dönene (ve --contains verildiyse metni içerene) kadar 15 sn arayla yoklar.
Çıkış kodu: 0 hepsi canlı · 1 zaman aşımı.
"""
import argparse
import sys
import time
import urllib.error
import urllib.request


def check(url: str, contains: str | None) -> tuple[bool, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "parafomo-wait-live", "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8", "replace") if contains else ""
            if contains and contains not in body:
                return False, f"{r.status} (metin yok)"
            return True, str(r.status)
    except urllib.error.HTTPError as e:
        return False, str(e.code)
    except Exception as e:  # ağ hatası
        return False, type(e).__name__


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--contains")
    ap.add_argument("--timeout", type=int, default=600)
    a = ap.parse_args()
    pending = list(a.urls)
    deadline = time.time() + a.timeout
    while pending:
        last = {}
        for u in list(pending):
            ok, info = check(u, a.contains)
            last[u] = info
            if ok:
                print(f"CANLI {info} {u}")
                pending.remove(u)
        if not pending:
            break
        if time.time() > deadline:
            for u in pending:
                print(f"ZAMAN AŞIMI {last.get(u)} {u}")
            return 1
        time.sleep(15)
    return 0


if __name__ == "__main__":
    sys.exit(main())
