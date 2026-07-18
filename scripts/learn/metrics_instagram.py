#!/usr/bin/env python3
"""
ParaFOMO — Instagram metrik toplayıcı.

Ledger'daki instagram kayıtlarının media_id'lerini alır, Graph API'den etkileşim
çeker → data/learning/metrics.jsonl.

İki katman:
  • Alan sorgusu (like_count, comments_count) → TEMEL izinle çalışır (şu an mevcut)
  • Insights (reach, saved, shares) → 'instagram_manage_insights' izni gerekir.
    İzin yoksa (#10) sessizce atlanır, boru hattı durmaz.

Kimlik: ~/.config/parafomo/instagram.env (IG_BUSINESS_ACCOUNT_ID, IG_PAGE_TOKEN)
"""
import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

API = "https://graph.facebook.com/v21.0"


def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def main():
    env = lib.load_env(lib.IG_ENV)
    tok = env.get("IG_PAGE_TOKEN")
    if not tok:
        print("[ig] token yok, atlandı"); return 0
    items = [r for r in lib.read_jsonl(lib.LEDGER) if r["channel"] == "instagram"]
    if not items:
        print("[ig] ledger'da IG içeriği yok"); return 0

    rows = []
    fetched = lib.iso()
    insights_ok = None  # None=deneme, True/False=öğrenildi
    for r in items:
        mid = r["refs"].get("media_id")
        if not mid:
            continue
        m = {}
        # temel alanlar
        try:
            q = urllib.parse.urlencode({"fields": "like_count,comments_count", "access_token": tok})
            d = get(f"{API}/{mid}?{q}")
            m["likes"] = d.get("like_count", 0)
            m["comments"] = d.get("comments_count", 0)
        except (urllib.error.HTTPError, urllib.error.URLError):
            continue
        # insights (izin varsa)
        if insights_ok is not False:
            try:
                q = urllib.parse.urlencode(
                    {"metric": "reach,saved,shares", "access_token": tok})
                ins = get(f"{API}/{mid}/insights?{q}")
                for i in ins.get("data", []):
                    m[i["name"]] = i["values"][0]["value"]
                insights_ok = True
            except urllib.error.HTTPError:
                insights_ok = False
        rows.append({"id": r["id"], "channel": "instagram", "fetched_utc": fetched, "metrics": m})
    lib.append_jsonl(lib.METRICS, rows)
    tag = "insights VAR" if insights_ok else "insights YOK (izin gerekli — sadece beğeni/yorum)"
    print(f"[+] ig metrik eklendi: {len(rows)} gönderi ({tag})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
