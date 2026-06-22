#!/usr/bin/env python3
"""
ParaFOMO — sosyal medya kartı üretici (Twitter/X, 1200x630 = og:image spec).

Her blog yazısı için markalı bir görsel üretir: teal-yeşil palet, ParaFOMO
wordmark, kategori etiketi, büyük serif başlık. Çıktı: public/social/<slug>.png.
Bu görsel her yazının og:image'ı olarak bağlanır → X/WhatsApp/Telegram/LinkedIn
link önizlemesinde yazıya özel kart otomatik çıkar (yükleme gerekmez).

Kaynak: YEREL içerik dosyaları (src/content/blog/*.md) — henüz yayında olmayan
yeni yazılar da build'den önce kart alır. Yalnızca PIL + sistem fontları.

Kullanım:
  python3 scripts/social-cards.py            # tüm yerel yazılar (eksikleri + günceller)
  python3 scripts/social-cards.py --slug X   # tek yazı
  python3 scripts/social-cards.py --missing   # yalnız kartı olmayanları üret
"""
import os
import re
import sys
import glob
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "public", "social")
WORDMARK = os.path.join(ROOT, "public", "parafomo-wordmark.png")
BLOG_DIR = os.path.join(ROOT, "src", "content", "blog")

W, H = 1200, 630
MARGIN = 80

# Palet
INK = (18, 20, 23)
DEEP = (30, 107, 127)       # #1E6B7F
BRAND = (43, 177, 148)      # #2BB194
LIGHT = (99, 212, 145)      # #63D491
GREY = (90, 100, 110)
WHITE = (255, 255, 255)

SERIF_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


def f(path, size):
    return ImageFont.truetype(path, size)


def lin_gradient(w, h, c1, c2, horizontal=True):
    base = Image.new("RGB", (w, h), c1)
    top = Image.new("RGB", (w, h), c2)
    mask = Image.new("L", (w, h))
    md = mask.load()
    for x in range(w):
        for y in range(h):
            t = (x / w) if horizontal else (y / h)
            md[x, y] = int(255 * t)
    base.paste(top, (0, 0), mask)
    return base


def wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
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


def fit_title(draw, text, max_w, max_h, max_lines=4):
    """Başlığı kutuya sığacak en büyük punto + satırlar."""
    for size in range(66, 33, -2):
        font = f(SERIF_BOLD, size)
        lines = wrap(draw, text, font, max_w)
        lh = int(size * 1.16)
        if len(lines) <= max_lines and len(lines) * lh <= max_h:
            return font, lines, lh
    font = f(SERIF_BOLD, 34)
    return font, wrap(draw, text, font, max_w)[:max_lines], int(34 * 1.16)


def make_card(title, category, slug):
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    # Sol kenar gradyan şerit
    bar = lin_gradient(18, H, DEEP, LIGHT, horizontal=False)
    img.paste(bar, (0, 0))

    # Sağ üst köşede yumuşak marka dairesi (hafif)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W - 260, -150, W + 150, 260], fill=(99, 212, 145, 38))
    gd.ellipse([W - 170, -90, W + 120, 200], fill=(43, 177, 148, 30))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    d = ImageDraw.Draw(img)

    # Kategori etiketi (teal pill)
    cat = (category or "Finans").upper()
    cf = f(SANS_BOLD, 24)
    tw = d.textlength(cat, font=cf)
    px, py = MARGIN, 96
    pill_h = 46
    d.rounded_rectangle([px, py, px + tw + 44, py + pill_h], radius=23, fill=BRAND)
    d.text((px + 22, py + pill_h / 2), cat, font=cf, fill=WHITE, anchor="lm")

    # Başlık
    title_top = py + pill_h + 36
    max_title_h = H - title_top - 130
    font, lines, lh = fit_title(d, title, W - 2 * MARGIN - 30, max_title_h, max_lines=4)
    y = title_top
    for ln in lines:
        d.text((MARGIN, y), ln, font=font, fill=INK)
        y += lh

    # Alt çizgi (gradyan) + wordmark + slogan
    d.rectangle([MARGIN, H - 108, W - MARGIN, H - 106], fill=BRAND)
    if os.path.exists(WORDMARK):
        wm = Image.open(WORDMARK).convert("RGBA")
        target_h = 42
        ratio = target_h / wm.height
        wm = wm.resize((int(wm.width * ratio), target_h), Image.LANCZOS)
        img.paste(wm, (MARGIN, H - 84), wm)
    tag = "parana akıl kat."
    tf = f(SANS, 24)
    d.text((W - MARGIN, H - 63), tag, font=tf, fill=GREY, anchor="rm")

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"{slug}.png")
    img.save(out, "PNG")
    return out


def fm_value(text, key):
    """Frontmatter'dan basit alan çek (title/category)."""
    m = re.search(rf'^{key}:\s*"?(.*?)"?\s*$', text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def posts_from_local():
    out = []
    for path in sorted(glob.glob(os.path.join(BLOG_DIR, "*.md"))):
        fm = open(path, encoding="utf-8").read().split("---", 2)
        front = fm[1] if len(fm) >= 3 else ""
        slug = os.path.splitext(os.path.basename(path))[0]
        out.append({
            "slug": slug,
            "title": fm_value(front, "title") or slug,
            "category": fm_value(front, "category") or "Finans",
        })
    return out


def main():
    only = sys.argv[sys.argv.index("--slug") + 1] if "--slug" in sys.argv else None
    missing_only = "--missing" in sys.argv
    posts = posts_from_local()
    n = 0
    for p in posts:
        if only and p["slug"] != only:
            continue
        if missing_only and os.path.exists(os.path.join(OUT_DIR, f"{p['slug']}.png")):
            continue
        make_card(p["title"], p["category"], p["slug"])
        n += 1
        print(f"[+] {p['slug']}.png  ←  {p['title'][:50]}")
    print(f"[+] {n} kart üretildi -> {OUT_DIR}")


if __name__ == "__main__":
    main()
