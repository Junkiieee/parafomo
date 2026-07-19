#!/usr/bin/env python3
"""
ParaFOMO — SEO iç-linkleme hedefleri (öğrenme döngüsünün web kolu).

GSC pozisyonlarına bakıp hangi yazıların "zirveye en yakın" olduğunu bulur ve
site şablonunun (İlgili Yazılar) bu sayfalara ÖNCELİKLE iç link vermesi için
src/data/seo-targets.json'a yazar (COMMIT'lenir → Cloudflare build okur).

Mantık:
  near_miss  : pozisyon 4-20, gösterim>0 → sayfa 1'e bir adım; iç link otoritesi
               bunları zirveye iter (en yüksek getiri).
  buried     : pozisyon>20, gösterim>=10 → talep var ama gömülü; küme/otorite gerek.
Çıktı 'boost' listesi (önce near_miss, gösterime göre) şablonda İlgili Yazılar
sıralamasına bonus verir → site içi PageRank kazanan sayfalarda yoğunlaşır.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

OUT = os.path.join(lib.ROOT, "src", "data", "seo-targets.json")


def latest_web():
    out = {}
    for r in lib.read_jsonl(lib.METRICS):
        if r.get("channel") != "web":
            continue
        cur = out.get(r["id"])
        if cur is None or r["fetched_utc"] >= cur["fetched_utc"]:
            out[r["id"]] = r
    return out


def main():
    web = latest_web()
    near, buried = [], []
    for x in web.values():
        m = x["metrics"]
        pos = m.get("position", 0) or 0
        imp = m.get("impressions", 0) or 0
        slug = x["id"].replace("blog:", "")
        if imp > 0 and 4 <= pos <= 20:
            near.append((imp, slug))
        elif imp >= 10 and pos > 20:
            buried.append((imp, slug))
    near.sort(reverse=True)
    buried.sort(reverse=True)
    near_slugs = [s for _, s in near]
    buried_slugs = [s for _, s in buried]
    data = {
        "generated_utc": lib.iso(),
        "boost": near_slugs + buried_slugs,   # şablon sıralama bonusu (önce near-miss)
        "near_miss": near_slugs,
        "buried": buried_slugs,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[+] seo-targets.json: {len(near_slugs)} near-miss + {len(buried_slugs)} gömülü -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
