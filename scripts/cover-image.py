#!/usr/bin/env python3
"""
ParaFOMO — yazı kapak görseli üretici (Pexels foto → 16:9 kapak).

Her blog yazısı için konuyla alakalı GERÇEK bir Pexels fotoğrafı indirir,
16:9'a kırpar, hafif renk düzeltmesi uygular ve public/covers/<slug>.jpg olarak
kaydeder. Bu görsel sitede blog kartlarında ve yazı sayfasının başında (hero)
gösterilir. (og:image olarak markalı başlık kartı — social-cards.py — kullanılmaya
devam eder; bu ayrı bir on-site kapaktır.)

Arama sorgusu önceliği:
  1. --query "..."            (günlük ajan konuya en uygun terimi verir — en iyi)
  2. frontmatter shorts_broll (Shorts için zaten İngilizce arama terimleri)
  3. SLUG_QUERIES sözlüğü      (mevcut 14 yazı için elle seçilmiş terimler)
  4. kategori fallback'i

Kullanım:
  python3 scripts/cover-image.py <slug> [--query "..."] [--force]
  python3 scripts/cover-image.py --all [--force]      # tüm yazılar
  python3 scripts/cover-image.py --missing            # yalnız kapağı olmayanlar
"""
import os
import re
import sys
import glob
import hashlib
import argparse
import urllib.request
import urllib.parse
from PIL import Image, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG = os.path.join(ROOT, "src", "content", "blog")
OUT_DIR = os.path.join(ROOT, "public", "covers")

W, H = 1600, 900  # 16:9

# Mevcut yazılar için konuya özel İngilizce Pexels sorguları (broll'u olmayanlar için).
SLUG_QUERIES = {
    "acil-durum-fonu-nedir": "emergency savings money jar coins",
    "altin-mi-dolar-mi": "gold bullion bars wealth investment",
    "bes-bireysel-emeklilik-mantikli-mi": "retirement savings planning senior couple",
    "bilesik-faiz-nedir": "coins stack growth plant investment",
    "bitcoin-nedir-nasil-alinir": "bitcoin cryptocurrency golden coin",
    "borsaya-nasil-baslanir": "stock market trading screen beginner",
    "butce-nasil-yapilir-50-30-20": "budget planning calculator notebook money",
    "dca-nedir-maliyet-ortalamasi": "investment chart coins savings",
    "endeks-fonu-nedir": "stock market index chart finance",
    "enflasyondan-nasil-korunur": "inflation rising prices money",
    "gdp-gsyih-nedir-nasil-yorumlanir": "city skyline economy business district",
    "hisse-senedi-nasil-secilir": "stock market analysis charts monitor",
    "pce-nedir-fed-enflasyon-gostergesi": "federal reserve building economy finance",
    "temettu-hisseleri-pasif-gelir": "passive income cash dividend money",
}

CATEGORY_QUERIES = {
    "Yatırım": "investment finance growth chart",
    "Borsa": "stock market trading screen",
    "Kripto": "cryptocurrency bitcoin coin",
    "Kişisel Finans": "personal finance budget money",
    "Ekonomi": "economy finance city business",
    "Emeklilik": "retirement savings planning",
}


def fm(front, key):
    m = re.search(rf'^{key}:\s*"?(.*?)"?\s*$', front, re.MULTILINE)
    return m.group(1).strip() if m else ""


def parse_list(front, key):
    m = re.search(rf'^{key}:\s*\n((?:\s*-\s*.*\n?)+)', front, re.MULTILINE)
    if not m:
        return []
    return [s.strip()[1:].strip().strip('"').strip("'")
            for s in m.group(1).splitlines() if s.strip().startswith("-")]


def read_front(slug):
    path = os.path.join(BLOG, f"{slug}.md")
    raw = open(path, encoding="utf-8").read()
    return raw.split("---", 2)[1] if "---" in raw else ""


def pick_query(slug, front, override):
    if override:
        return override
    broll = parse_list(front, "shorts_broll")
    if broll:
        return broll[0]
    if slug in SLUG_QUERIES:
        return SLUG_QUERIES[slug]
    cat = fm(front, "category")
    return CATEGORY_QUERIES.get(cat, "finance money investment")


def pexels_photo(query, slug):
    """Sorgu için yatay foto seçer; (data_bytes) döner. Anahtar yoksa/sonuç yoksa None."""
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        print("[!] PEXELS_API_KEY yok — .env yüklendi mi?")
        return None
    UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    url = ("https://api.pexels.com/v1/search?orientation=landscape&size=large&per_page=15&query="
           + urllib.parse.quote(query))
    try:
        req = urllib.request.Request(url, headers={"Authorization": key, "User-Agent": UA})
        import json
        data = json.load(urllib.request.urlopen(req, timeout=25))
    except Exception as e:
        print(f"[!] Pexels arama hatası '{query}': {str(e)[:70]}")
        return None
    photos = data.get("photos", [])
    if not photos:
        print(f"[i] '{query}' için sonuç yok")
        return None
    # slug'a göre deterministik ama çeşitli seçim (aynı kategoride aynı foto olmasın)
    idx = int(hashlib.md5(slug.encode()).hexdigest(), 16) % min(len(photos), 10)
    photo = photos[idx]
    src = photo["src"]
    link = src.get("large2x") or src.get("original") or src.get("large")
    try:
        dreq = urllib.request.Request(link, headers={"User-Agent": UA})
        with urllib.request.urlopen(dreq, timeout=60) as r:
            return r.read()
    except Exception as e:
        print(f"[!] Foto indirilemedi: {str(e)[:70]}")
        return None


def process_and_save(data, out_path):
    """16:9 merkez kırpma + hafif renk düzeltmesi → jpg."""
    import io
    img = Image.open(io.BytesIO(data)).convert("RGB")
    sw, sh = img.size
    target = W / H
    if sw / sh > target:           # çok geniş → yanlardan kırp
        nw = int(sh * target)
        x = (sw - nw) // 2
        img = img.crop((x, 0, x + nw, sh))
    else:                          # çok uzun → üst/alttan kırp
        nh = int(sw / target)
        y = (sh - nh) // 2
        img = img.crop((0, y, sw, y + nh))
    img = img.resize((W, H), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(1.06)
    img = ImageEnhance.Contrast(img).enhance(1.03)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "JPEG", quality=86, optimize=True, progressive=True)


def gen_one(slug, override=None, force=False):
    out_path = os.path.join(OUT_DIR, f"{slug}.jpg")
    if os.path.exists(out_path) and not force:
        print(f"[=] {slug}: kapak zaten var (atla; --force ile yenile)")
        return True
    front = read_front(slug)
    query = pick_query(slug, front, override)
    data = pexels_photo(query, slug)
    if not data:
        print(f"[!] {slug}: kapak ÜRETİLEMEDİ (sorgu: '{query}')")
        return False
    process_and_save(data, out_path)
    kb = os.path.getsize(out_path) / 1024
    print(f"[+] {slug}: kapak hazır ← '{query}'  ({kb:.0f} KB)")
    return True


def all_slugs():
    return sorted(os.path.basename(f)[:-3] for f in glob.glob(os.path.join(BLOG, "*.md")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--query", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--missing", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.all or args.missing:
        ok = True
        for slug in all_slugs():
            out = os.path.join(OUT_DIR, f"{slug}.jpg")
            if args.missing and os.path.exists(out):
                continue
            ok = gen_one(slug, force=args.force) and ok
        return 0 if ok else 1
    if not args.slug:
        print("kullanım: cover-image.py <slug> | --all | --missing")
        return 1
    return 0 if gen_one(args.slug, override=args.query, force=args.force) else 1


if __name__ == "__main__":
    sys.exit(main())
