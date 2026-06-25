#!/usr/bin/env python3
"""
ParaFOMO — Günlük altın fiyatları kartı (Instagram 1080x1350).

Truncgil v4 today.json'dan altın/gümüş fiyatlarını çeker, lacivert zeminli,
ParaFOMO markalı (teal wordmark) dikey bir kart üretir. Referans düzeni:
tarih rozeti + 2 sütun (ALTIN | FİYAT) + yön okları + footer.

Çıktı: public/social/altin-<YYYYMMDD>.jpg  (+ sabit altin-today.jpg kopyası)

Kullanım:
  python3 scripts/altin-card.py            # bugünün kartını üret
  python3 scripts/altin-card.py --date 25.06.2026   # tarih etiketini zorla

Bağımlılık: Pillow (venv'de). Salt standart kütüphane + PIL. Token harcamaz.
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "public", "social")
GOLD_ASSET = os.path.join(ROOT, "public", "social", "assets", "gold-bars.jpg")
WORDMARK = os.path.join(ROOT, "public", "parafomo-wordmark.png")
API = "https://finans.truncgil.com/v4/today.json"

W, H = 1080, 1350
FONT_DIR = "/usr/share/fonts/truetype/dejavu"

# Renkler
NAVY_TOP = (10, 28, 56)      # #0a1c38
NAVY_BOT = (14, 40, 74)      # #0e284a
WHITE = (238, 243, 250)
SOFT = (150, 170, 196)
GOLD = (212, 175, 90)        # vurgu altın tonu
TEAL = (43, 177, 148)        # marka
GREEN = (60, 200, 130)
RED = (235, 92, 92)
LINE = (255, 255, 255, 28)


def F(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def fmt_tr(n, decimals=0):
    """Türkçe sayı: binlik nokta, ondalık virgül."""
    s = f"{n:,.{decimals}f}"            # 40,654.00 (en-US)
    s = s.replace(",", "§").replace(".", ",").replace("§", ".")
    return s


def fetch():
    req = urllib.request.Request(API, headers={"User-Agent": "Mozilla/5.0 (ParaFOMO)"})
    text = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")

    def pick(key, prop):
        m = re.search(r'"' + re.escape(key) + r'"\s*:\s*\{[^}]*?"' + prop + r'"\s*:\s*(-?[0-9.]+)', text)
        return float(m.group(1)) if m else None

    gra = pick("GRA", "Selling")
    has = pick("HAS", "Selling")
    usd = pick("USD", "Selling")
    # Ons (USD): Truncgil ONS alanı 0 dönüyor; gram has + USD'den türet (saf 24 ayar).
    ons = (has * 31.1035 / usd) if (has and usd) else None
    rows = [
        ("24 Ayar Gram Altın", gra, pick("GRA", "Change"), "₺", 0),
        ("Ons Altın", ons, pick("HAS", "Change"), "$", 0),
        ("22 Ayar Altın", pick("YIA", "Selling"), pick("YIA", "Change"), "₺", 0),
        ("Çeyrek Altın", pick("CEYREKALTIN", "Selling"), pick("CEYREKALTIN", "Change"), "₺", 0),
        ("Cumhuriyet Altını", pick("CUMHURIYETALTINI", "Selling"), pick("CUMHURIYETALTINI", "Change"), "₺", 0),
        ("Gram Gümüş", pick("GUMUS", "Selling"), pick("GUMUS", "Change"), "₺", 2),
    ]
    return rows


def vgrad(w, h, top, bot):
    base = Image.new("RGB", (w, h), top)
    top_l = Image.new("RGB", (w, h), bot)
    mask = Image.new("L", (w, h))
    md = mask.load()
    for y in range(h):
        v = int(255 * (y / max(1, h - 1)) ** 1.15)
        for x in range(w):
            md[x, y] = v
    base.paste(top_l, (0, 0), mask)
    return base


def draw_arrow(d, cx, cy, up, color, s=15):
    if up:
        d.polygon([(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)], fill=color)
    else:
        d.polygon([(cx, cy + s), (cx - s, cy - s), (cx + s, cy - s)], fill=color)


def build(date_label):
    img = vgrad(W, H, NAVY_TOP, NAVY_BOT).convert("RGBA")

    # --- üst altın külçe bandı, navy'ye yumuşak geçiş ---
    band_h = 360
    if os.path.exists(GOLD_ASSET):
        g = Image.open(GOLD_ASSET).convert("RGB")
        gr = g.width / g.height
        tw = W
        th = int(tw / gr)
        if th < band_h:
            th = band_h
            tw = int(th * gr)
        g = g.resize((tw, th))
        gx = (W - tw) // 2
        g = g.crop((-gx if gx < 0 else 0, 0, (-gx if gx < 0 else 0) + W, band_h))
        # alt kenara doğru navy'ye eriyen alpha maske
        mask = Image.new("L", (W, band_h), 255)
        mp = mask.load()
        for y in range(band_h):
            if y < band_h * 0.55:
                a = 235
            else:
                t = (y - band_h * 0.55) / (band_h * 0.45)
                a = int(235 * (1 - t))
            for x in range(W):
                mp[x, y] = a
        img.paste(g.convert("RGBA"), (0, 0), mask)
        # üstte hafif koyu vinyet (metin okunurluğu)
        ov = Image.new("RGBA", (W, band_h), (10, 28, 56, 70))
        img.alpha_composite(ov, (0, 0))

    d = ImageDraw.Draw(img)

    f_title = F("DejaVuSans-Bold.ttf", 58)
    f_head = F("DejaVuSans-Bold.ttf", 34)
    f_row = F("DejaVuSans.ttf", 40)
    f_price = F("DejaVuSans-Bold.ttf", 42)
    f_date = F("DejaVuSans-Bold.ttf", 30)
    f_foot = F("DejaVuSans.ttf", 28)

    # --- tarih rozeti (band ile içerik sınırında) ---
    badge = f"Tarih: {date_label}"
    bb = d.textbbox((0, 0), badge, font=f_date)
    bw, bh = bb[2] - bb[0], bb[3] - bb[1]
    pad = 26
    bx0 = (W - (bw + pad * 2)) // 2
    by0 = band_h - 34
    d.rounded_rectangle([bx0, by0, bx0 + bw + pad * 2, by0 + bh + pad], radius=26,
                        fill=(8, 22, 44), outline=GOLD, width=2)
    d.text((bx0 + pad, by0 + pad // 2 - 2), badge, font=f_date, fill=GOLD)

    # --- başlık ---
    title = "GÜNCEL ALTIN FİYATLARI"
    tb = d.textbbox((0, 0), title, font=f_title)
    d.text(((W - (tb[2] - tb[0])) // 2, band_h + 70), title, font=f_title, fill=WHITE)
    # altın ince çizgi
    ly = band_h + 160
    d.line([(120, ly), (W - 120, ly)], fill=GOLD, width=3)

    # --- sütun başlıkları ---
    head_y = ly + 36
    d.text((96, head_y), "ALTIN", font=f_head, fill=GOLD)
    fiyat = "FİYAT"
    fb = d.textbbox((0, 0), fiyat, font=f_head)
    d.text((W - 96 - (fb[2] - fb[0]) - 90, head_y), fiyat, font=f_head, fill=GOLD)

    # --- satırlar ---
    rows = fetch()
    top = head_y + 70
    avail = H - top - 235
    rh = avail // len(rows)
    arrow_x = W - 96 - 24
    price_right = arrow_x - 56
    midx = W * 0.60
    for i, (name, val, chg, cur, dec) in enumerate(rows):
        cy = top + i * rh + rh // 2
        # satır ayraç
        d.line([(96, top + i * rh), (W - 96, top + i * rh)], fill=(255, 255, 255, 26), width=1)
        # isim
        d.text((96, cy - 22), name, font=f_row, fill=WHITE)
        # fiyat
        if val is None:
            ptxt = "—"
        else:
            ptxt = fmt_tr(val, dec) + " " + cur
        pb = d.textbbox((0, 0), ptxt, font=f_price)
        d.text((price_right - (pb[2] - pb[0]), cy - 24), ptxt, font=f_price, fill=WHITE)
        # ok
        if chg is not None:
            up = chg >= 0
            draw_arrow(d, arrow_x, cy, up, GREEN if up else RED, s=14)
    # son ayraç
    d.line([(96, top + len(rows) * rh), (W - 96, top + len(rows) * rh)], fill=(255, 255, 255, 26), width=1)

    # dikey ince ayırıcı (isim | fiyat)
    d.line([(midx, head_y + 6), (midx, top + len(rows) * rh - 6)], fill=(255, 255, 255, 22), width=1)

    # --- footer ---
    # wordmark (son satırla footer çizgisi arasında, ortalı — satıra yapışmaz)
    rows_bottom = top + len(rows) * rh
    if os.path.exists(WORDMARK):
        wm = Image.open(WORDMARK).convert("RGBA")
        ww = 210
        wm = wm.resize((ww, int(wm.height * ww / wm.width)))
        wm_y = rows_bottom + (H - 95 - rows_bottom - wm.height) // 2
        img.alpha_composite(wm, ((W - ww) // 2, wm_y))

    fy = H - 95
    d.line([(96, fy), (W - 96, fy)], fill=(255, 255, 255, 40), width=1)
    d.text((96, fy + 22), "Altın fiyatları için bizi takip et", font=f_foot, fill=SOFT)
    handle = "@parafomo · parafomo.com"
    hb = d.textbbox((0, 0), handle, font=f_foot)
    d.text((W - 96 - (hb[2] - hb[0]), fy + 22), handle, font=f_foot, fill=TEAL)

    return img.convert("RGB")


def main():
    args = sys.argv[1:]
    if "--date" in args:
        date_label = args[args.index("--date") + 1]
    else:
        now = datetime.now(timezone.utc) + timedelta(hours=3)  # TR
        date_label = now.strftime("%d.%m.%Y")
    img = build(date_label)
    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = date_label.replace(".", "")
    # gg aa yyyy -> yyyyaagg
    dd, mm, yy = date_label.split(".")
    out = os.path.join(OUT_DIR, f"altin-{yy}{mm}{dd}.jpg")
    img.save(out, "JPEG", quality=90)
    img.save(os.path.join(OUT_DIR, "altin-today.jpg"), "JPEG", quality=90)
    print("[altin] kart üretildi:", out)


if __name__ == "__main__":
    main()
