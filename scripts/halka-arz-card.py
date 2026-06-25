#!/usr/bin/env python3
"""
ParaFOMO — Yeni halka arz duyuru kartı (Instagram 1080x1350).

data/halka-arz.json'dan bir kaydı alıp lacivert zeminli, teal aksanlı,
ParaFOMO markalı dikey duyuru kartı üretir. Alanlar: hisse adı + BİST kodu,
tarih, dağıtım türü, fiyat, arz büyüklüğü (lot×fiyat), toplam lot, aracı kurum.

Kullanım:
  python3 scripts/halka-arz-card.py --code BETAE     # belirli hisse
  python3 scripts/halka-arz-card.py --slug beta-...  # slug ile
  python3 scripts/halka-arz-card.py                  # ilk "Devam Ediyor"/duyurulabilir

Çıktı: public/social/halka-arz-<bist_code>.jpg
Bağımlılık: Pillow. Token harcamaz.
"""
import json
import os
import re
import sys
import urllib.request
from PIL import Image, ImageDraw, ImageFont

LOGO_CACHE = "/root/.cache/parafomo/halka-arz-logos"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "halka-arz.json")
OUT_DIR = os.path.join(ROOT, "public", "social")
WORDMARK = os.path.join(ROOT, "public", "parafomo-wordmark.png")
FONT_DIR = "/usr/share/fonts/truetype/dejavu"

W, H = 1080, 1350
NAVY_TOP = (10, 28, 56)
NAVY_BOT = (14, 40, 74)
WHITE = (238, 243, 250)
SOFT = (150, 170, 196)
TEAL = (43, 177, 148)
TEAL_LT = (99, 212, 145)


def F(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def fmt_tr(n, dec=0):
    s = f"{n:,.{dec}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def parse_num(s):
    if not s:
        return None
    m = re.findall(r"[\d.,]+", str(s))
    if not m:
        return None
    raw = m[0].replace(".", "").replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def offer_size(lot, price):
    lv, pv = parse_num(lot), parse_num(price)
    if not lv or not pv:
        return None
    total = lv * pv
    if total >= 1e9:
        return "~" + fmt_tr(total / 1e9, 2) + " Milyar TL"
    if total >= 1e6:
        return "~" + fmt_tr(total / 1e6, 0) + " Milyon TL"
    return fmt_tr(total, 0) + " TL"


def clean(s):
    return re.sub(r"\s*\*+\s*$", "", (s or "").strip()).strip()


def fetch_logo(it):
    """Halkarz künye sayfasından şirket logosunu çeker (cache'li). Bulamazsa None."""
    code = (it.get("bist_code") or it.get("slug") or "x").upper()
    os.makedirs(LOGO_CACHE, exist_ok=True)
    cache = os.path.join(LOGO_CACHE, f"{code}.img")
    if os.path.exists(cache) and os.path.getsize(cache) > 1000:
        return cache
    link = it.get("link")
    if not link:
        return None
    try:
        req = urllib.request.Request(link, headers={"User-Agent": "Mozilla/5.0"})
        h = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
    except Exception:
        return None
    m = re.search(r'<img[^>]*class="[^"]*slogo[^"]*"[^>]*>', h) or \
        re.search(r'<img[^>]*wp-post-image[^>]*>', h)
    if not m:
        return None
    s = re.search(r'src="([^"]+)"', m.group(0))
    if not s:
        return None
    try:
        req = urllib.request.Request(s.group(1), headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=20).read()
        open(cache, "wb").write(data)
        return cache
    except Exception:
        return None


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


def load_item(args):
    d = json.load(open(DATA, encoding="utf-8"))
    items = d["items"]
    if "--code" in args:
        code = args[args.index("--code") + 1].upper()
        for it in items:
            if (it.get("bist_code") or "").upper() == code:
                return it
        sys.exit(f"[ha] {code} bulunamadı")
    if "--slug" in args:
        slug = args[args.index("--slug") + 1]
        for it in items:
            if it.get("slug") == slug:
                return it
        sys.exit(f"[ha] {slug} bulunamadı")
    # varsayılan: ilk "Devam Ediyor", yoksa fiyatı+tarihi olan ilk kayıt
    for it in items:
        if it.get("status") == "Devam Ediyor":
            return it
    for it in items:
        if it.get("price") and it.get("start"):
            return it
    sys.exit("[ha] duyurulabilir kayıt yok")


def build(it, ptype="tarih"):
    img = vgrad(W, H, NAVY_TOP, NAVY_BOT).convert("RGBA")
    d = ImageDraw.Draw(img)
    badge_txt = "SPK ONAYI" if ptype == "onay" else "HALKA ARZ TARİHİ"

    f_badge = F("DejaVuSans-Bold.ttf", 30)
    f_co = F("DejaVuSans-Bold.ttf", 50)
    f_code = F("DejaVuSans-Bold.ttf", 38)
    f_lbl = F("DejaVuSans.ttf", 32)
    f_val = F("DejaVuSans-Bold.ttf", 38)
    f_foot = F("DejaVuSans.ttf", 28)

    # --- üst teal şerit + rozet ---
    d.rectangle([0, 0, W, 14], fill=TEAL)
    badge = badge_txt
    bb = d.textbbox((0, 0), badge, font=f_badge)
    bw = bb[2] - bb[0]
    pad = 30
    bx = (W - (bw + pad * 2)) // 2
    by = 70
    d.rounded_rectangle([bx, by, bx + bw + pad * 2, by + 58], radius=29,
                        fill=TEAL, outline=None)
    d.text((bx + pad, by + 11), badge, font=f_badge, fill=(8, 22, 44))

    # --- şirket logosu (halkarz'dan, beyaz yuvarlak rozet içinde) ---
    y = by + 100
    logo_path = fetch_logo(it)
    if logo_path:
        try:
            lg = Image.open(logo_path).convert("RGB")
            bsz, pad2 = 168, 16
            badge_img = Image.new("RGB", (bsz, bsz), (255, 255, 255))
            inner = bsz - pad2 * 2
            lg.thumbnail((inner, inner))
            badge_img.paste(lg, ((bsz - lg.width) // 2, (bsz - lg.height) // 2))
            mask = Image.new("L", (bsz, bsz), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, bsz, bsz], radius=34, fill=255)
            img.paste(badge_img, ((W - bsz) // 2, y), mask)
            y += bsz + 26
        except Exception:
            y = by + 110

    # --- şirket adı (kelime sar) ---
    company = clean(it.get("company"))
    words = company.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textbbox((0, 0), t, font=f_co)[2] <= W - 160:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    for ln in lines[:3]:
        lb = d.textbbox((0, 0), ln, font=f_co)
        d.text(((W - (lb[2] - lb[0])) // 2, y), ln, font=f_co, fill=WHITE)
        y += 64

    # --- BİST kodu chip ---
    code = (it.get("bist_code") or "").upper()
    if code:
        cb = d.textbbox((0, 0), code, font=f_code)
        cw = cb[2] - cb[0]
        cx = (W - (cw + 56)) // 2
        y += 14
        d.rounded_rectangle([cx, y, cx + cw + 56, y + 64], radius=14,
                            fill=None, outline=TEAL_LT, width=3)
        d.text((cx + 28, y + 8), code, font=f_code, fill=TEAL_LT)
        y += 100

    # --- detay satırları ---
    size = offer_size(it.get("lot"), it.get("price"))
    date_val = clean(it.get("date_text")) if ptype != "onay" and clean(it.get("date_text")) \
        else "Yakında açıklanacak"
    rows = [
        ("Halka Arz Tarihi", date_val),
        ("Dağıtım Yöntemi", clean(it.get("distribution"))),
        ("Pay Fiyatı", clean(it.get("price"))),
        ("Arz Büyüklüğü", size or "—"),
        ("Toplam Lot", clean(it.get("lot"))),
    ]
    rows = [(k, v) for k, v in rows if (v and v != "—") or k in ("Arz Büyüklüğü", "Halka Arz Tarihi")]

    top = y + 10
    avail = H - top - 250
    rh = min(120, avail // max(1, len(rows)))
    for i, (lbl, val) in enumerate(rows):
        cy = top + i * rh
        d.line([(96, cy), (W - 96, cy)], fill=(255, 255, 255, 26), width=1)
        d.text((96, cy + rh // 2 - 20), lbl, font=f_lbl, fill=SOFT)
        vb = d.textbbox((0, 0), val, font=f_val)
        d.text((W - 96 - (vb[2] - vb[0]), cy + rh // 2 - 24), val, font=f_val, fill=WHITE)
    rows_bottom = top + len(rows) * rh
    d.line([(96, rows_bottom), (W - 96, rows_bottom)], fill=(255, 255, 255, 26), width=1)

    # --- aracı kurum (alt, küçük; genişliğe göre kısalt) ---
    broker = clean(it.get("broker"))
    if broker:
        broker = re.sub(r"\s+", " ", broker)
        prefix = "Aracı Kurum: "
        maxw = W - 192
        full = prefix + broker
        if d.textbbox((0, 0), full, font=f_foot)[2] > maxw:
            while broker and d.textbbox((0, 0), prefix + broker + "…", font=f_foot)[2] > maxw:
                broker = broker.rsplit(" ", 1)[0] if " " in broker else broker[:-1]
            full = prefix + broker + "…"
        d.text((96, rows_bottom + 22), full, font=f_foot, fill=SOFT)

    # --- footer ---
    if os.path.exists(WORDMARK):
        wm = Image.open(WORDMARK).convert("RGBA")
        ww = 210
        wm = wm.resize((ww, int(wm.height * ww / wm.width)))
        img.alpha_composite(wm, ((W - ww) // 2, H - 150))
    fy = H - 75
    handle = "@parafomo · parafomo.com"
    hb = d.textbbox((0, 0), handle, font=f_foot)
    d.text(((W - (hb[2] - hb[0])) // 2, fy), handle, font=f_foot, fill=TEAL)

    return img.convert("RGB")


def main():
    args = sys.argv[1:]
    ptype = args[args.index("--type") + 1] if "--type" in args else "tarih"
    it = load_item(args)
    img = build(it, ptype)
    os.makedirs(OUT_DIR, exist_ok=True)
    key = (it.get("slug") or it.get("bist_code") or "ha")
    key = re.sub(r"[^A-Za-z0-9-]", "", key)
    out = os.path.join(OUT_DIR, f"halka-arz-{key}-{ptype}.jpg")
    img.save(out, "JPEG", quality=90)
    img.save(os.path.join(OUT_DIR, "halka-arz-preview.jpg"), "JPEG", quality=90)
    print(f"[ha] kart üretildi: {out}  ({it.get('company')})")


if __name__ == "__main__":
    main()
