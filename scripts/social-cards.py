#!/usr/bin/env python3
"""
ParaFOMO — sosyal medya kartı üretici (Twitter/X, 1600x900).

Her blog yazısı için markalı bir görsel üretir: teal-yeşil palet, ParaFOMO
wordmark, kategori etiketi, büyük serif başlık. Çıktı: public/social/<slug>.png
(siteyle yayınlanır → public URL; X planlı gönderiye yüklenir, ileride IG için de).

Kaynak: parafomo.com/rss.xml (tüm yazılar) veya --slug ile tek yazı.
Yalnızca PIL + sistem fontları (Liberation Serif/Sans).
"""
import os
import re
import sys
import html
import urllib.request
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "public", "social")
WORDMARK = os.path.join(ROOT, "public", "parafomo-wordmark.png")
RSS = "https://parafomo.com/rss.xml"

W, H = 1600, 900
MARGIN = 110

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
    for size in range(92, 49, -3):
        font = f(SERIF_BOLD, size)
        lines = wrap(draw, text, font, max_w)
        lh = int(size * 1.16)
        if len(lines) <= max_lines and len(lines) * lh <= max_h:
            return font, lines, lh
    font = f(SERIF_BOLD, 52)
    return font, wrap(draw, text, font, max_w)[:max_lines], int(52 * 1.16)


def make_card(title, category, slug):
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    # Sol kenar gradyan şerit
    bar = lin_gradient(26, H, DEEP, LIGHT, horizontal=False)
    img.paste(bar, (0, 0))

    # Sağ üst köşede yumuşak marka dairesi (hafif)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W - 360, -200, W + 200, 360], fill=(99, 212, 145, 38))
    gd.ellipse([W - 230, -120, W + 160, 270], fill=(43, 177, 148, 30))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    d = ImageDraw.Draw(img)

    # Kategori etiketi (teal pill)
    cat = (category or "Finans").upper()
    cf = f(SANS_BOLD, 30)
    tw = d.textlength(cat, font=cf)
    px, py = MARGIN, 150
    pill_h = 56
    d.rounded_rectangle([px, py, px + tw + 56, py + pill_h], radius=28, fill=BRAND)
    d.text((px + 28, py + pill_h / 2), cat, font=cf, fill=WHITE, anchor="lm")

    # Başlık
    title_top = py + pill_h + 50
    max_title_h = H - title_top - 220
    font, lines, lh = fit_title(d, title, W - 2 * MARGIN - 40, max_title_h, max_lines=4)
    y = title_top
    for ln in lines:
        d.text((MARGIN, y), ln, font=font, fill=INK)
        y += lh

    # Alt çizgi (gradyan) + wordmark + alan adı
    d.rectangle([MARGIN, H - 150, W - MARGIN, H - 147], fill=BRAND)
    if os.path.exists(WORDMARK):
        wm = Image.open(WORDMARK).convert("RGBA")
        target_h = 56
        ratio = target_h / wm.height
        wm = wm.resize((int(wm.width * ratio), target_h), Image.LANCZOS)
        img.paste(wm, (MARGIN, H - 120), wm)
    tag = "parana akıl kat."
    tf = f(SANS, 30)
    d.text((W - MARGIN, H - 92), tag, font=tf, fill=GREY, anchor="rm")

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"{slug}.png")
    img.save(out, "PNG")
    return out


def posts_from_rss():
    xml = urllib.request.urlopen(
        urllib.request.Request(RSS, headers={"User-Agent": "Mozilla/5.0"}), timeout=20
    ).read().decode()
    out = []
    for it in xml.split("<item>")[1:]:
        def pick(tag):
            m = re.search(rf"<{tag}>([\s\S]*?)</{tag}>", it)
            return html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", m.group(1)).strip()) if m else ""
        cats = [html.unescape(c.strip()) for c in re.findall(r"<category>([\s\S]*?)</category>", it)]
        link = pick("link")
        slug = link.rstrip("/").split("/")[-1]
        out.append({"title": pick("title"), "category": cats[0] if cats else "Finans", "slug": slug})
    return out


def main():
    only = None
    if "--slug" in sys.argv:
        only = sys.argv[sys.argv.index("--slug") + 1]
    posts = posts_from_rss()
    n = 0
    for p in posts:
        if only and p["slug"] != only:
            continue
        out = make_card(p["title"], p["category"], p["slug"])
        n += 1
        print(f"[+] {p['slug']}.png  ←  {p['title'][:50]}")
    print(f"[+] {n} kart üretildi -> {OUT_DIR}")


if __name__ == "__main__":
    main()
