#!/usr/bin/env python3
"""
ParaFOMO — günlük yazıyı Instagram'a (@parafomo) paylaşır.

Meta Graph API "Content Publishing" akışı: önce bir medya konteyneri
(image_url + caption) oluşturur, sonra yayınlar. Görsel JPEG ve PUBLIC bir
URL olmalı (IG sunucusu URL'i kendi çeker) → her yazı için 1080x1350 dikey
markalı bir IG görseli üretip public/social/<slug>-ig.jpg olarak kaydeder;
bu dosya parafomo.com'a deploy edildikten sonra URL'i IG'ye verilir.

Kimlik bilgileri repo DIŞINDA: ~/.config/parafomo/instagram.env
  IG_BUSINESS_ACCOUNT_ID, IG_PAGE_TOKEN (süresiz Page token)

Kullanım:
  python3 scripts/post-instagram.py              # daily-log'daki en yeni yazı
  python3 scripts/post-instagram.py --slug X      # belirli yazı
  python3 scripts/post-instagram.py --dry         # yayınlama; metin+görsel URL göster
  python3 scripts/post-instagram.py --force       # daha önce paylaşılmış olsa da
"""
import os
import re
import sys
import json
import glob
import time
import urllib.parse
import urllib.request
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "public", "social")
WORDMARK = os.path.join(ROOT, "public", "parafomo-wordmark.png")
BLOG_DIR = os.path.join(ROOT, "src", "content", "blog")
LOG_FILE = os.path.join(ROOT, "docs", "daily-log.md")
STATE_FILE = os.path.join(ROOT, "logs", "instagram-last.txt")
ENV_FILE = os.path.expanduser("~/.config/parafomo/instagram.env")
SITE = "https://parafomo.com"
API = "https://graph.facebook.com/v21.0"

# IG dikey format (4:5, feed'de en geniş alan)
W, H = 1080, 1350
MARGIN = 90

INK = (18, 20, 23)
DEEP = (30, 107, 127)
BRAND = (43, 177, 148)
LIGHT = (99, 212, 145)
GREY = (90, 100, 110)
WHITE = (255, 255, 255)

SERIF_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


def f(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def fit_title(draw, text, max_w, max_h, max_lines=6):
    for size in range(96, 47, -2):
        font = f(SERIF_BOLD, size)
        lines = wrap(draw, text, font, max_w)
        lh = int(size * 1.16)
        if len(lines) <= max_lines and len(lines) * lh <= max_h:
            return font, lines, lh
    font = f(SERIF_BOLD, 48)
    return font, wrap(draw, text, font, max_w)[:max_lines], int(48 * 1.16)


def make_ig_image(title, category, slug):
    """1080x1350 dikey markalı IG görseli (JPEG)."""
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    # Sol kenar gradyan şerit
    bar = Image.new("RGB", (22, H), DEEP)
    bd = bar.load()
    for y in range(H):
        t = y / H
        bd_col = (
            int(DEEP[0] + (LIGHT[0] - DEEP[0]) * t),
            int(DEEP[1] + (LIGHT[1] - DEEP[1]) * t),
            int(DEEP[2] + (LIGHT[2] - DEEP[2]) * t),
        )
        for x in range(22):
            bd[x, y] = bd_col
    img.paste(bar, (0, 0))

    # Sağ üst yumuşak marka parıltısı
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W - 320, -200, W + 180, 320], fill=(99, 212, 145, 40))
    gd.ellipse([W - 220, -120, W + 150, 240], fill=(43, 177, 148, 32))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    d = ImageDraw.Draw(img)

    # Kategori pill
    cat = (category or "Finans").upper()
    cf = f(SANS_BOLD, 32)
    tw = d.textlength(cat, font=cf)
    px, py = MARGIN, 150
    pill_h = 60
    d.rounded_rectangle([px, py, px + tw + 56, py + pill_h], radius=30, fill=BRAND)
    d.text((px + 28, py + pill_h / 2), cat, font=cf, fill=WHITE, anchor="lm")

    # Başlık (dikey alanın büyük kısmı)
    title_top = py + pill_h + 60
    max_title_h = H - title_top - 220
    font, lines, lh = fit_title(d, title, W - 2 * MARGIN, max_title_h)
    y = title_top
    for ln in lines:
        d.text((MARGIN, y), ln, font=font, fill=INK)
        y += lh

    # Alt: gradyan çizgi + wordmark + slogan
    d.rectangle([MARGIN, H - 150, W - MARGIN, H - 147], fill=BRAND)
    if os.path.exists(WORDMARK):
        wm = Image.open(WORDMARK).convert("RGBA")
        target_h = 56
        ratio = target_h / wm.height
        wm = wm.resize((int(wm.width * ratio), target_h), Image.LANCZOS)
        img.paste(wm, (MARGIN, H - 118), wm)
    d.text((W - MARGIN, H - 90), "parana akıl kat.", font=f(SANS, 30),
           fill=GREY, anchor="rm")

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"{slug}-ig.jpg")
    img.save(out, "JPEG", quality=90)
    return out


def fm_value(text, key):
    m = re.search(rf'^{key}:\s*"?(.*?)"?\s*$', text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def load_post(slug):
    path = os.path.join(BLOG_DIR, f"{slug}.md")
    if not os.path.exists(path):
        sys.exit(f"[ig] HATA: yazı bulunamadı: {path}")
    parts = open(path, encoding="utf-8").read().split("---", 2)
    front = parts[1] if len(parts) >= 3 else ""
    return {
        "slug": slug,
        "title": fm_value(front, "title") or slug,
        "category": fm_value(front, "category") or "Finans",
        "description": fm_value(front, "description"),
    }


def newest_slug():
    line = ""
    for ln in open(LOG_FILE, encoding="utf-8"):
        if "Yayınlanan yazı" in ln:
            line = ln
            break
    m = re.search(r"\(/blog/([^)]+)\)", line)
    if not m:
        sys.exit("[ig] HATA: daily-log.md'den yazı ayrıştırılamadı")
    return m.group(1)


def load_env():
    env = {}
    if not os.path.exists(ENV_FILE):
        sys.exit(f"[ig] HATA: {ENV_FILE} yok")
    for ln in open(ENV_FILE):
        ln = ln.strip()
        if ln and not ln.startswith("#") and "=" in ln:
            k, v = ln.split("=", 1)
            env[k] = v
    for k in ("IG_BUSINESS_ACCOUNT_ID", "IG_PAGE_TOKEN"):
        if not env.get(k):
            sys.exit(f"[ig] HATA: {ENV_FILE} içinde {k} yok")
    return env


def build_caption(post):
    url = f"{SITE}/blog/{post['slug']}"
    tags = "#finans #yatırım #parafomo #kişiselfinans #borsa #tasarruf #ekonomi"
    parts = [post["title"]]
    if post["description"]:
        parts.append(post["description"])
    parts.append(f"📖 Yazının tamamı: {url}\n(Profildeki linkten de ulaşabilirsin)")
    parts.append(tags)
    return "\n\n".join(parts)


def http_post(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


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
    slug = args[args.index("--slug") + 1] if "--slug" in args else newest_slug()

    post = load_post(slug)
    img_path = make_ig_image(post["title"], post["category"], slug)
    img_url = f"{SITE}/social/{slug}-ig.jpg"
    caption = build_caption(post)

    print(f"[ig] yazı   : {post['title']}")
    print(f"[ig] görsel : {img_path}")
    print(f"[ig] URL    : {img_url}")
    print(f"[ig] ----- caption -----\n{caption}\n[ig] -----------------")

    # dedup
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    last = open(STATE_FILE).read().strip() if os.path.exists(STATE_FILE) else ""
    if not force and last == slug:
        print(f"[ig] '{slug}' zaten paylaşılmış, atlanıyor (--force ile zorla)")
        return

    if dry:
        print("[ig] --dry: yayınlanmadı. Görselin canlı olduğundan emin ol, sonra "
              "--dry'sız çalıştır.")
        return

    if not url_ok(img_url):
        sys.exit(f"[ig] HATA: görsel canlı değil ({img_url}). Önce deploy et "
                 "(commit + npx wrangler deploy), sonra tekrar dene.")

    env = load_env()
    ig_id = env["IG_BUSINESS_ACCOUNT_ID"]
    token = env["IG_PAGE_TOKEN"]

    # 1) konteyner
    cont = http_post(f"{API}/{ig_id}/media", {
        "image_url": img_url, "caption": caption, "access_token": token,
    })
    if "id" not in cont:
        sys.exit(f"[ig] HATA (konteyner): {json.dumps(cont, ensure_ascii=False)}")
    creation_id = cont["id"]
    print(f"[ig] konteyner oluştu: {creation_id}")
    time.sleep(3)  # IG'nin görseli çekmesi için kısa bekleme

    # 2) yayınla
    pub = http_post(f"{API}/{ig_id}/media_publish", {
        "creation_id": creation_id, "access_token": token,
    })
    if "id" not in pub:
        sys.exit(f"[ig] HATA (yayın): {json.dumps(pub, ensure_ascii=False)}")
    print(f"[ig] ✅ YAYINLANDI! media_id={pub['id']}  → instagram.com/parafomo")
    open(STATE_FILE, "w").write(slug)


if __name__ == "__main__":
    main()
