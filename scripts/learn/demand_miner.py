#!/usr/bin/env python3
"""Google Autocomplete talep madencisi → data/learning/demand-gaps.json.

Ajanın körlüğünü giderir: GSC yalnız ZATEN gösterim aldığımız sorguları gösterir; bu script
Google'ın otomatik tamamlamasından (ücretsiz uç) gerçek kullanıcı sorgularını çeker ve sitede
karşılığı olmayanları işaretler. Brief'in "Talep radarı" bölümü + haftalık koşu konu seçimi okur.

Tohumlar: data/tr-seasonal-seo.json (bu ay + gelecek ay) + script içi çekirdek liste.
Kapsama: öneri token'larının çoğu tek bir sayfa/yazı slug'ında geçiyorsa "kapsanıyor" sayılır
(kaba bir sinyal — kesin hüküm değil). Ağ hatasında mevcut dosyaya dokunmaz.

Kullanım: python3 scripts/learn/demand_miner.py [--verbose]
"""
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "learning", "demand-gaps.json")
SEASONAL = os.path.join(ROOT, "data", "tr-seasonal-seo.json")
API = "https://suggestqueries.google.com/complete/search?client=firefox&hl=tr&gl=tr&q={q}"

CORE_SEEDS = [
    "altın fiyatı ne zaman", "dolar mı altın mı", "mevduat faizi", "halka arz",
    "emekli zammı", "asgari ücret 2027", "kira artış oranı", "vergi dilimi",
    "mtv 2027", "yeniden değerleme", "faiz kararı", "enflasyon ne zaman",
    "bes mi mevduat mı", "kıdem tazminatı", "temettü", "borsa",
]

STOP = set("mı mi mu mü ne nasıl kaç kadar için ile ve veya da de bu şu o en çok hangi "
           "nedir olacak oldu olur yılı yili ayı ayi".split())
ASCII = str.maketrans("şŞıİğĞüÜöÖçÇâî", "sSiIgGuUoOcCai")


def norm_tokens(s):
    s = s.lower().translate(ASCII)
    return [t for t in re.findall(r"[a-z0-9]+", s) if t not in STOP and len(t) > 1]


def site_slugs():
    slugs = []
    pages = os.path.join(ROOT, "src", "pages")
    for f in os.listdir(pages):
        if f.endswith(".astro") and f not in ("index.astro", "404.astro"):
            slugs.append(f[:-6])
    blog = os.path.join(ROOT, "src", "content", "blog")
    if os.path.isdir(blog):
        slugs += [f.rsplit(".", 1)[0] for f in os.listdir(blog) if f.endswith((".md", ".mdx"))]
    return [set(norm_tokens(s.replace("-", " "))) for s in slugs]


def covered(query, slug_sets):
    toks = set(norm_tokens(query)) - {"2025", "2026", "2027", "2028"}
    if not toks:
        return True
    best = max((len(toks & ss) / len(toks)) for ss in slug_sets) if slug_sets else 0
    return best >= 0.6


def suggest(q):
    url = API.format(q=urllib.parse.quote(q))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    return [s for s in data[1] if isinstance(s, str)]


def seasonal_seeds(today):
    try:
        d = json.load(open(SEASONAL, encoding="utf-8"))
    except Exception:
        return []
    months = {today.month, today.month % 12 + 1}
    seeds = []
    for item in d.get("takvim", []):
        if item.get("ay") in months:
            seeds += item.get("sorgular", [])[:2]
    return seeds


def main():
    verbose = "--verbose" in sys.argv
    today = dt.date.today()
    seeds = list(dict.fromkeys(seasonal_seeds(today) + CORE_SEEDS))[:24]
    slug_sets = site_slugs()
    results, failures = [], 0
    for seed in seeds:
        try:
            sugs = suggest(seed)
        except Exception as e:
            failures += 1
            if verbose:
                print(f"[demand] {seed!r} hata: {e}")
            if failures >= 4:
                break
            continue
        rows = [{"q": s, "covered": covered(s, slug_sets)} for s in sugs[:10] if len(s) < 90]
        results.append({"seed": seed, "suggestions": rows})
        time.sleep(0.4)
    got = sum(len(r["suggestions"]) for r in results)
    if got < 10:
        print(f"[demand] UYARI: yeterli öneri alınamadı ({got}, {failures} hata) — dosyaya dokunulmadı")
        return 0
    uncovered = []
    seen = set()
    for r in results:
        for s in r["suggestions"]:
            if not s["covered"] and s["q"] not in seen:
                seen.add(s["q"])
                uncovered.append(s["q"])
    data = {
        "_aciklama": ("Google Autocomplete (tr) önerileri; covered = site slug'larıyla kaba eşleşme. "
                      "Kapsanmayanlar = potansiyel yeni sayfa/yazı konusu — talebi GSC/rakiple doğrula."),
        "generated_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "uncovered_top": uncovered[:40],
        "seeds": results,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"[demand] {len(results)} tohum → {got} öneri, {len(uncovered)} kapsanmamış")
    return 0


if __name__ == "__main__":
    sys.exit(main())
