#!/usr/bin/env python3
"""
ParaFOMO — BIST açılış/kapanış kartı (Instagram 1080x1350).

Truncgil'den BIST 100 (XU100) + Dolar/Euro/Gram Altın, CoinGecko'dan Bitcoin
çeker; lacivert+teal markalı kart üretir. Tip'e göre rozet değişir.

Kullanım:
  python3 scripts/bist-card.py --type acilis
  python3 scripts/bist-card.py --type kapanis

Çıktı: public/social/bist-<type>-<YYYYMMDD>.jpg
Bağımlılık: Pillow. Token harcamaz.
"""
import os
import re
import sys
import json
import urllib.request
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "public", "social")
WORDMARK = os.path.join(ROOT, "public", "parafomo-wordmark.png")
BG_ASSET = os.path.join(ROOT, "public", "social", "assets", "bist-bg.jpg")
TG = "https://finans.truncgil.com/v4/today.json"
CG = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
FONT_DIR = "/usr/share/fonts/truetype/dejavu"

W, H = 1080, 1350
NAVY_TOP, NAVY_BOT = (10, 28, 56), (14, 40, 74)
WHITE, SOFT, TEAL, TEAL_LT = (238, 243, 250), (150, 170, 196), (43, 177, 148), (99, 212, 145)
GREEN, RED = (60, 200, 130), (235, 92, 92)

BADGE = {"acilis": "GÜNAYDIN · BIST AÇILDI", "kapanis": "BIST KAPANIŞ · GÜN SONU"}


def F(n, s):
    return ImageFont.truetype(os.path.join(FONT_DIR, n), s)


def fmt_tr(n, d=0):
    return f"{n:,.{d}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def fetch():
    t = urllib.request.urlopen(urllib.request.Request(TG, headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read().decode("utf-8", "ignore")

    def pick(k, p):
        m = re.search(r'"' + re.escape(k) + r'"\s*:\s*\{[^}]*?"' + p + r'"\s*:\s*(-?[0-9.]+)', t)
        return float(m.group(1)) if m else None

    data = {
        "bist": (pick("XU100", "Selling"), pick("XU100", "Change")),
        "usd": (pick("USD", "Selling"), pick("USD", "Change")),
        "eur": (pick("EUR", "Selling"), pick("EUR", "Change")),
        "gold": (pick("GRA", "Selling"), pick("GRA", "Change")),
    }
    try:
        d = json.loads(urllib.request.urlopen(urllib.request.Request(CG, headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read())
        data["btc"] = (d["bitcoin"]["usd"], d["bitcoin"]["usd_24h_change"])
    except Exception:
        data["btc"] = (None, None)
    return data


def vgrad(w, h, top, bot):
    base = Image.new("RGB", (w, h), top)
    tl = Image.new("RGB", (w, h), bot)
    mask = Image.new("L", (w, h))
    md = mask.load()
    for y in range(h):
        v = int(255 * (y / max(1, h - 1)) ** 1.15)
        for x in range(w):
            md[x, y] = v
    base.paste(tl, (0, 0), mask)
    return base


def cover(im, w, h):
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1))
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def background():
    """Lacivert gradyan + üstte mum grafik fotosu (aşağı doğru lacivderte erir)."""
    base = vgrad(W, H, NAVY_TOP, NAVY_BOT).convert("RGBA")
    if not os.path.exists(BG_ASSET):
        return base
    ch = cover(Image.open(BG_ASSET).convert("RGB"), W, H).convert("RGBA")
    mask = Image.new("L", (W, H))
    md = mask.load()
    for y in range(H):
        t = y / H
        vis = 0.55 * (1 - t / 0.62) if t < 0.62 else 0.0   # üstte ~%55, %62'de biter
        a = int(255 * max(0.0, vis))
        for x in range(W):
            md[x, y] = a
    ch.putalpha(mask)
    base.alpha_composite(ch)
    # üst kısma hafif koyu vinyet (metin okunurluğu)
    ov = Image.new("RGBA", (W, 470), (10, 28, 56, 60))
    base.alpha_composite(ov, (0, 0))
    return base


def arrow(d, cx, cy, up, color, s=16):
    if up:
        d.polygon([(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)], fill=color)
    else:
        d.polygon([(cx, cy + s), (cx - s, cy - s), (cx + s, cy - s)], fill=color)


def chg_txt(c):
    if c is None:
        return "", SOFT
    up = c >= 0
    return ("▲ " if up else "▼ ") + f"%{abs(c):.2f}".replace(".", ","), (GREEN if up else RED)


def build(ptype, date_label):
    data = fetch()
    img = background()
    d = ImageDraw.Draw(img)
    f_badge = F("DejaVuSans-Bold.ttf", 30)
    f_lbl = F("DejaVuSans.ttf", 36)
    f_hero = F("DejaVuSans-Bold.ttf", 130)
    f_chg = F("DejaVuSans-Bold.ttf", 50)
    f_date = F("DejaVuSans.ttf", 28)
    f_row = F("DejaVuSans.ttf", 38)
    f_val = F("DejaVuSans-Bold.ttf", 40)

    d.rectangle([0, 0, W, 14], fill=TEAL)
    badge = BADGE.get(ptype, "BIST")
    bb = d.textbbox((0, 0), badge, font=f_badge)
    bw = bb[2] - bb[0]
    d.rounded_rectangle([(W - bw - 60) // 2, 64, (W + bw + 60) // 2, 122], radius=29, fill=TEAL)
    d.text(((W - bw) // 2, 75), badge, font=f_badge, fill=(8, 22, 44))

    # tarih
    db = d.textbbox((0, 0), date_label, font=f_date)
    d.text(((W - (db[2] - db[0])) // 2, 150), date_label, font=f_date, fill=SOFT)

    # BIST 100 hero
    lbl = "BIST 100"
    lb = d.textbbox((0, 0), lbl, font=f_lbl)
    d.text(((W - (lb[2] - lb[0])) // 2, 210), lbl, font=f_lbl, fill=TEAL_LT)
    bval, bchg = data["bist"]
    hero = fmt_tr(bval, 0) if bval else "—"
    hb = d.textbbox((0, 0), hero, font=f_hero)
    d.text(((W - (hb[2] - hb[0])) // 2, 260), hero, font=f_hero, fill=WHITE)
    ct, cc = chg_txt(bchg)
    if ct:
        cb = d.textbbox((0, 0), ct, font=f_chg)
        d.text(((W - (cb[2] - cb[0])) // 2, 410), ct, font=f_chg, fill=cc)

    # divider
    d.line([(120, 510), (W - 120, 510)], fill=TEAL, width=3)

    # piyasa özeti satırları
    rows = [
        ("Dolar/TL", data["usd"], "₺", 2),
        ("Euro/TL", data["eur"], "₺", 2),
        ("Gram Altın", data["gold"], "₺", 0),
        ("Bitcoin", data["btc"], "$", 0),
    ]
    top = 560
    rh = 150
    arrow_x = W - 110
    for i, (name, (val, chg), cur, dec) in enumerate(rows):
        cy = top + i * rh
        d.line([(96, cy), (W - 96, cy)], fill=(255, 255, 255, 26), width=1)
        midy = cy + rh // 2
        d.text((96, midy - 22), name, font=f_row, fill=SOFT)
        if val is None:
            vtxt = "—"
        elif cur == "$":
            vtxt = "$" + fmt_tr(val, 0)
        else:
            vtxt = fmt_tr(val, dec) + " ₺"
        vb = d.textbbox((0, 0), vtxt, font=f_val)
        d.text((arrow_x - 56 - (vb[2] - vb[0]), midy - 24), vtxt, font=f_val, fill=WHITE)
        if chg is not None:
            arrow(d, arrow_x, midy, chg >= 0, GREEN if chg >= 0 else RED, 14)
    d.line([(96, top + len(rows) * rh), (W - 96, top + len(rows) * rh)], fill=(255, 255, 255, 26), width=1)

    # footer
    if os.path.exists(WORDMARK):
        wm = Image.open(WORDMARK).convert("RGBA")
        ww = 210
        wm = wm.resize((ww, int(wm.height * ww / wm.width)))
        img.alpha_composite(wm, ((W - ww) // 2, H - 128))
    handle = "@parafomo · parafomo.com"
    hbb = d.textbbox((0, 0), handle, font=f_date)
    d.text(((W - (hbb[2] - hbb[0])) // 2, H - 70), handle, font=f_date, fill=TEAL)
    return img.convert("RGB")


def main():
    args = sys.argv[1:]
    ptype = args[args.index("--type") + 1] if "--type" in args else "acilis"
    now = datetime.now(timezone.utc) + timedelta(hours=3)
    date_label = now.strftime("%d.%m.%Y")
    img = build(ptype, date_label)
    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = now.strftime("%Y%m%d")
    out = os.path.join(OUT_DIR, f"bist-{ptype}-{stamp}.jpg")
    img.save(out, "JPEG", quality=90)
    img.save(os.path.join(OUT_DIR, "bist-preview.jpg"), "JPEG", quality=90)
    print(f"[bist] kart üretildi: {out}")


if __name__ == "__main__":
    main()
