#!/usr/bin/env python3
"""
ParaFOMO — Feed kartını Instagram STORY'sine (1080x1920) saran tasarım.

Bir feed kartını (1080x1350) alıp lacivert markalı dikey story üretir:
üstte wordmark + etiket, ortada yuvarlak köşeli/gölgeli kart, altta CTA.

Kullanım:
  python3 scripts/story-card.py <kaynak_kart.jpg> <çıktı.jpg> --label "GÜNCEL" --cta "Detaylar profilde"
Bağımlılık: Pillow.
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORDMARK = os.path.join(ROOT, "public", "parafomo-wordmark.png")
FONT_DIR = "/usr/share/fonts/truetype/dejavu"

W, H = 1080, 1920
NAVY_TOP, NAVY_BOT = (9, 24, 48), (16, 44, 80)
WHITE, SOFT, TEAL, TEAL_LT = (238, 243, 250), (150, 170, 196), (43, 177, 148), (99, 212, 145)


def F(n, s):
    return ImageFont.truetype(os.path.join(FONT_DIR, n), s)


def vgrad(w, h, top, bot):
    base = Image.new("RGB", (w, h), top)
    tl = Image.new("RGB", (w, h), bot)
    mask = Image.new("L", (w, h))
    md = mask.load()
    for y in range(h):
        v = int(255 * (y / max(1, h - 1)) ** 1.1)
        for x in range(w):
            md[x, y] = v
    base.paste(tl, (0, 0), mask)
    return base


def rounded(im, rad):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.size[0], im.size[1]], radius=rad, fill=255)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def build(card_path, label, cta):
    img = vgrad(W, H, NAVY_TOP, NAVY_BOT).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 16], fill=TEAL)

    # üst wordmark
    if os.path.exists(WORDMARK):
        wm = Image.open(WORDMARK).convert("RGBA")
        ww = 300
        wm = wm.resize((ww, int(wm.height * ww / wm.width)))
        img.alpha_composite(wm, ((W - ww) // 2, 110))

    # etiket
    if label:
        f_lbl = F("DejaVuSans-Bold.ttf", 34)
        lb = d.textbbox((0, 0), label, font=f_lbl)
        lw = lb[2] - lb[0]
        d.rounded_rectangle([(W - lw - 60) // 2, 195, (W + lw + 60) // 2, 255],
                            radius=30, fill=TEAL)
        d.text(((W - lw) // 2, 205), label, font=f_lbl, fill=(8, 22, 44))

    # kart (gölge + yuvarlak köşe)
    card = Image.open(card_path).convert("RGB")
    cw = 920
    ch = int(card.height * cw / card.width)
    card = card.resize((cw, ch))
    cardr = rounded(card, 36)
    cx, cy = (W - cw) // 2, (H - ch) // 2 + 30
    # gölge
    sh = Image.new("RGBA", (cw + 60, ch + 60), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([30, 30, 30 + cw, 30 + ch], radius=44, fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    img.alpha_composite(sh, (cx - 30, cy - 22))
    img.alpha_composite(cardr, (cx, cy))

    # alt CTA
    f_cta = F("DejaVuSans-Bold.ttf", 44)
    f_sub = F("DejaVuSans.ttf", 32)
    # yukarı ok (chevron)
    ax, ay = W // 2, cy + ch + 70
    d.line([(ax - 26, ay + 18), (ax, ay - 12)], fill=TEAL_LT, width=8)
    d.line([(ax + 26, ay + 18), (ax, ay - 12)], fill=TEAL_LT, width=8)
    cta = cta or "Detaylar profilde"
    cb = d.textbbox((0, 0), cta, font=f_cta)
    d.text(((W - (cb[2] - cb[0])) // 2, ay + 50), cta, font=f_cta, fill=WHITE)
    handle = "@parafomo · parafomo.com"
    hb = d.textbbox((0, 0), handle, font=f_sub)
    d.text(((W - (hb[2] - hb[0])) // 2, ay + 112), handle, font=f_sub, fill=TEAL_LT)
    return img.convert("RGB")


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        sys.exit("Kullanım: story-card.py <kaynak> <çıktı> [--label X] [--cta Y]")
    src, out = args[0], args[1]
    label = args[args.index("--label") + 1] if "--label" in args else "GÜNCEL"
    cta = args[args.index("--cta") + 1] if "--cta" in args else "Detaylar profilde"
    build(src, label, cta).save(out, "JPEG", quality=90)
    print(f"[story] üretildi: {out}")


if __name__ == "__main__":
    main()
