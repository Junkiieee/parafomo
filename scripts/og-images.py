#!/usr/bin/env python3
"""Canlı rakamlı OG kartları → public/og/<slug>.png (1200×630).

Neden: tüm sayfalar tek statik og-default.png paylaşıyordu. Sosyal paylaşım + Google Discover'da
CTR'ı belirleyen görsel, sayfanın SAYISINI taşımalı ("Altın 1 yıl +%24" gibi). Kartlar veri
dosyalarından beslenir; getiri yüzdeleri TAM SAYIYA yuvarlanır ki her gün piksel değişip git'i
şişirmesin (aynı piksel = aynı PNG baytı = commit yok). Tarih karta yazılmaz (churn önleme).

Çağıran: daily-content.sh (veri adımlarından sonra) + kira-artis-update.sh (aylık kartlar).
Sayfa tarafı: BaseLayout'a image="/og/<slug>.png" geçilir. Hata = o kart atlanır, eskisi kalır.

Kullanım: python3 scripts/og-images.py [--only slug1,slug2] [--force]
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "public", "og")
FONT_DIR = os.path.join(REPO, "assets", "fonts")
DEJAVU = "/usr/share/fonts/truetype/dejavu"

W, H = 1200, 630
BG = (10, 56, 47)        # koyu marka teali (brand-ink ailesi)
BG2 = (7, 44, 37)        # alt bant
ACCENT = (43, 177, 148)  # --brand-2
LIGHT = (207, 237, 229)  # açık teal metin
WHITE = (255, 255, 255)
MUTED = (140, 190, 176)

MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
          "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def F(name, size):
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    except Exception:
        return ImageFont.truetype(os.path.join(DEJAVU, "DejaVuSans-Bold.ttf"), size)


def tr_pct(x, dec=1):
    s = f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def ay_adi(key):  # "2026-09" → "Eylül 2026"
    return f"{MONTHS[int(key[5:]) - 1]} {key[:4]}"


def load(name):
    return json.load(open(os.path.join(REPO, "data", name), encoding="utf-8"))


# ------------------------------------------------------------------ kart tanımları
def returns_card(fname, varlik):
    def fn():
        d = load(fname)
        p1 = next(p for p in d["periods"] if p.get("years") == 1)
        pct = p1["return_tl_pct"]
        sign = "+" if pct >= 0 else "−"
        return {
            "kicker": f"{varlik} · 1 YILLIK GETİRİ (TL)",
            "stat": f"{sign}%{abs(round(pct))}",
            "sub": "10 yıllık seri · her gün otomatik güncellenir",
        }
    return fn


def yd_card(kicker_tpl, sub_calc):
    def fn():
        d = load("yeniden-degerleme.json")
        oran = d.get("tebligOrani") or d["onikiAyOrt"]
        kesin = bool(d.get("tebligOrani")) or d.get("ekimVerisiGeldi")
        stat = ("%" if kesin else "≈%") + tr_pct(round(oran, 1), 1)
        return {"kicker": kicker_tpl.format(yil=d["hedefYil"]),
                "stat": stat, "sub": sub_calc(d, kesin)}
    return fn


def emekli_card():
    t = load("tufe-aylik.json")
    by = {m["ay"]: m["aylik"] for m in t["months"]}
    cum, n = 1.0, 0
    for k in ["2026-07", "2026-08", "2026-09", "2026-10", "2026-11", "2026-12"]:
        if k in by:
            cum *= 1 + by[k] / 100
            n += 1
    return {"kicker": "OCAK 2027 EMEKLİ ZAMMI", "stat": f"%{tr_pct((cum - 1) * 100, 2)}",
            "sub": f"kesinleşen {n}/6 ay · SSK, Bağ-Kur ve memur hesabı"}


def kira_card():
    d = load("kira-artis-2026.json")
    return {"kicker": "KİRA ARTIŞ ORANI", "stat": f"%{tr_pct(d['guncelOran'], 2)}",
            "sub": f"{d['guncelAy']} · 12 aylık TÜFE ortalaması"}


def enflasyon_card():
    t = load("tufe-aylik.json")
    m = t["months"][0]
    return {"kicker": "YILLIK ENFLASYON (TÜFE)", "stat": f"%{tr_pct(m['yillik'], 2)}",
            "sub": f"{ay_adi(m['ay'])} · TÜİK açıklama takvimiyle"}


def halka_arz_card():
    d = load("halka-arz.json")
    aktif = sum(1 for i in d["items"] if i.get("status") != "Tamamlandı")
    return {"kicker": "HALKA ARZ TAKVİMİ", "stat": str(aktif),
            "sub": "süren ve yaklaşan arz · tarih, fiyat, lot"}


CARDS = {
    "yeniden-degerleme-orani": yd_card(
        "YENİDEN DEĞERLEME ORANI {yil}",
        lambda d, k: ("kesinleşti · MTV, harç ve cezaların zam oranı" if k
                      else f"{ay_adi(d['sonAy'])} Yİ-ÜFE tahmini · Kasım'da kesinleşir")),
    "mtv-hesaplama": yd_card(
        "MTV {yil} ZAM TAHMİNİ",
        lambda d, k: "2026 MTV'nizden 2027 tahmininizi hesaplayın"),
    "emekli-zammi-hesaplama": emekli_card,
    "kira-artis-orani-hesaplama": kira_card,
    "enflasyon-takvimi": enflasyon_card,
    "halka-arz": halka_arz_card,
    "altin-getiri": returns_card("altin-getiri.json", "ALTIN"),
    "dolar-getiri": returns_card("dolar-getiri.json", "DOLAR"),
    "gumus-getiri": returns_card("gumus-getiri.json", "GÜMÜŞ"),
    "euro-getiri": returns_card("euro-getiri.json", "EURO"),
    "bitcoin-getiri": returns_card("bitcoin-getiri.json", "BİTCOİN"),
    "bist-getiri": returns_card("bist-getiri.json", "BIST 100"),
}


def render(card):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 92, W, H], fill=BG2)
    d.rectangle([64, 74, 72, 118], fill=ACCENT)  # aksan çubuğu

    f_brand = F("Anton-Regular.ttf", 44)
    f_kicker = F("Oswald.ttf", 44)
    f_stat = F("Anton-Regular.ttf", 230)
    f_sub = F("Oswald.ttf", 38)
    f_foot = F("Oswald.ttf", 30)

    d.text((88, 66), "PARAFOMO", font=f_brand, fill=WHITE)
    kicker = card["kicker"]
    if d.textlength(kicker, font=f_kicker) > W - 128:
        f_kicker = F("Oswald.ttf", 36)
    d.text((66, 178), kicker, font=f_kicker, fill=LIGHT)

    # Büyük rakam: bbox ile ölç — genişliğe VE alt çizgiye (sub satırına) sığana kadar küçült
    stat, top, sub_y_max = card["stat"], 252, 492
    size = 210
    while size > 100:
        fs = F("Anton-Regular.ttf", size)
        box = d.textbbox((58, top), stat, font=fs)
        if box[2] <= W - 64 and box[3] <= sub_y_max - 16:
            break
        size -= 15
    d.text((58, top - (box[1] - top)), stat, font=fs, fill=WHITE)  # görsel üst = top

    d.text((66, sub_y_max), card["sub"], font=f_sub, fill=MUTED)
    d.text((66, H - 64), "parafomo.com", font=f_foot, fill=ACCENT)
    tw = d.textlength("Güncel veri · yatırım tavsiyesi değildir", font=f_foot)
    d.text((W - 66 - tw, H - 64), "Güncel veri · yatırım tavsiyesi değildir", font=f_foot, fill=MUTED)
    return img


def main():
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    force = "--force" in sys.argv
    os.makedirs(OUT_DIR, exist_ok=True)
    made = skipped = failed = 0
    for slug, fn in CARDS.items():
        if only and slug not in only:
            continue
        try:
            card = fn() if callable(fn) else fn
            img = render(card)
            path = os.path.join(OUT_DIR, f"{slug}.png")
            import io
            buf = io.BytesIO()
            img.save(buf, "PNG", optimize=True)
            new = buf.getvalue()
            if not force and os.path.exists(path) and open(path, "rb").read() == new:
                skipped += 1
                continue
            with open(path, "wb") as f:
                f.write(new)
            made += 1
            print(f"[og] {slug}.png ← {card['stat']} ({card['kicker'][:40]})")
        except Exception as e:
            failed += 1
            print(f"[og] UYARI {slug}: {e}")
    print(f"[og] bitti: {made} yazıldı, {skipped} değişmedi, {failed} hata")
    return 0


if __name__ == "__main__":
    sys.exit(main())
