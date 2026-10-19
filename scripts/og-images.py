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


def memur_zam():
    """src/data/zam2027.ts ile AYNI mantık → (zam oranı, kesin mi)."""
    t = load("tufe-aylik.json")
    by = {m["ay"]: m["aylik"] for m in t["months"]}
    keys = ["2026-07", "2026-08", "2026-09", "2026-10", "2026-11", "2026-12"]
    known = [k for k in keys if k in by]
    cum = 1.0
    for k in known:
        cum *= 1 + by[k] / 100
    assume = round(sum(m["aylik"] for m in t["months"][:3]) / 3, 2)
    cum6 = cum * (1 + assume / 100) ** (len(keys) - len(known)) - 1
    return (1 + max(0.0, (1 + cum6) / 1.07 - 1)) * 1.05 - 1, len(known) == len(keys)


def evde_bakim_card():
    # 2828 s.K. ek md.7: 10.000 gösterge × memur aylık katsayısı; Ocak 2027 = katsayı × (1 + memur zammı)
    k = load("emekli-memur.json")["memurKatsayi"]["aylikKatsayi"]
    zam, kesin = memur_zam()
    simdi, ocak = 10000 * k, 10000 * k * (1 + zam)
    tl = lambda x: f"{round(x):,}".replace(",", ".")
    return {"kicker": "EVDE BAKIM MAAŞI OCAK 2027", "stat": ("₺" if kesin else "≈₺") + tl(ocak),
            "sub": f"şu an ₺{tl(simdi)} · 10.000 gösterge × memur katsayısı"}


def engelli_card():
    # 2022 s.K. aylıkları: bütçe K cetveli göstergesi × memur aylık katsayısı + %5 ek ödeme (5454 md.1/e); ASHB ile kuruşu kuruşuna
    d = load("sosyal-aylik-2026.json")
    k = load("emekli-memur.json")["memurKatsayi"]["aylikKatsayi"]
    zam, kesin = memur_zam()
    g = d["butce"]["2027"]["engelli"] if "2027" in d["butce"] else d["butce"]["2026"]["engelli"]
    def aylik(kat):
        base = round(g * kat + 1e-9, 2)
        return base + round(base * 0.05 + 1e-9, 2)
    tl = lambda x: f"{round(x):,}".replace(",", ".")
    return {"kicker": "ENGELLİ MAAŞI OCAK 2027", "stat": ("₺" if kesin else "≈₺") + tl(aylik(k * (1 + zam))),
            "sub": f"%40–69 engelli · şu an ₺{tl(aylik(k))} · %70+ ve 65 yaş aylığı da artar"}


def memur_card():
    # src/data/zam2027.ts ile AYNI mantık: TS 2026-H2 %7, 2027-H1 %5; kalan aylar = son 3 ay ortalaması
    t = load("tufe-aylik.json")
    by = {m["ay"]: m["aylik"] for m in t["months"]}
    keys = ["2026-07", "2026-08", "2026-09", "2026-10", "2026-11", "2026-12"]
    known = [k for k in keys if k in by]
    cum = 1.0
    for k in known:
        cum *= 1 + by[k] / 100
    assume = round(sum(m["aylik"] for m in t["months"][:3]) / 3, 2)
    cum6 = cum * (1 + assume / 100) ** (len(keys) - len(known)) - 1
    zam = (1 + max(0.0, (1 + cum6) / 1.07 - 1)) * 1.05 - 1
    kesin = len(known) == len(keys)
    return {"kicker": "OCAK 2027 MEMUR ZAMMI", "stat": ("%" if kesin else "≈%") + tr_pct(zam * 100, 1),
            "sub": "toplu sözleşme %5 + enflasyon farkı · maaşını hesapla"}


def emekli_memur_card(kind):
    def fn():
        d = load("emekli-memur.json")
        if kind == "taban":
            return {"kicker": "EN DÜŞÜK EMEKLİ MAAŞI", "stat": "₺" + f"{d['enDusukEmekliAyligi']['tutar']:,}".replace(",", "."),
                    "sub": "SSK · Bağ-Kur · Ocak 2027 senaryosu ve ödeme günleri"}
        b = d["bayramIkramiyesi"]
        return {"kicker": f"BAYRAM İKRAMİYESİ {b['yil']}", "stat": "₺" + f"{b['tutar']:,}".replace(",", "."),
                "sub": "2027 Ramazan ve Kurban tarihleri · hisseye göre tutar"}
    return fn


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


def faiz_card(group, key, kicker, field, sub):
    # data/faiz-oranlari.json (scripts/evds-rates.py, haftalık). 1 ondalık: haftada en çok bir PNG değişir.
    def fn():
        r = load("faiz-oranlari.json")[group][key]
        return {"kicker": kicker, "stat": f"%{tr_pct(r[field], 1)}",
                "sub": ("aylık · " if field == "aylik" else "yıllık · ") + sub}
    return fn


def asgari_card():
    # data/asgari-ucret.json — yeni yıl açıklanınca (scripts/asgari-ucret-watch.py) kart da yeni yıla döner
    d = load("asgari-ucret.json")
    y = d.get("yeni") or d["guncel"]
    net = f"{y['net']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    sub = "açıklandı · 1 Ocak'ta yürürlükte · brütü hesapla" if d.get("yeni") else "net · brüt, kesinti, işveren maliyeti hesapla"
    return {"kicker": f"ASGARİ ÜCRET {y['yil']}", "stat": f"₺{net}", "sub": sub}


def vergi_dilimi_card():
    # 2026 tarifesi sabit (332 Seri No'lu GVK Tebliği); Ocak 2027'de sayfayla birlikte güncelle
    return {"kicker": "GELİR VERGİSİ DİLİMLERİ 2026", "stat": "%15–40",
            "sub": "190.000 ₺'ye kadar %15 · dilimini ve vergini hesapla"}


CARDS = {
    "vergi-borcu-sorgulama": lambda: {
        # CB Kararı 10556 (RG 13.11.2025) %3,7; oran değişirse güncelle
        "kicker": "VERGİ BORCU SORGULAMA", "stat": "%3,7",
        "sub": "aylık gecikme zammı · e-Devlet ve GİB adımları"},
    "dogum-yardimi": lambda: {
        # 633 s. KHK ek md.4 (7546 s.K.); tutar CB kararıyla değişirse güncelle
        "kicker": "DOĞUM YARDIMI 2026", "stat": "₺5.000",
        "sub": "2. çocuk 1.500 ₺/ay · 3. ve sonraki 5.000 ₺/ay · 60 ay"},
    "veraset-ve-intikal-vergisi-hesaplama": lambda: {
        # VİVK Genel Tebliği Seri 57 (RG 31.12.2025); Ocak 2027'de güncelle
        "kicker": "VERASET VE İNTİKAL VERGİSİ 2026", "stat": "₺2.907.136",
        "sub": "çocuk/eş istisnası · bağışta ₺66.935 · 2027 tahmini"},
    "noter-ucretleri": lambda: {
        # Harçlar K. Tebliğ Seri 98 + Noterlik Ücret Tarifesi 2026; Ocak 2027'de güncelle
        "kicker": "NOTER ÜCRETLERİ 2026", "stat": "₺307,90",
        "sub": "vekaletname harcı (imza başına) · araç satışında binde 2"},
    "tapu-harci-hesaplama": lambda: {
        # Harçlar K. (4) s. tarife binde 20+20; TKGM 2026 döner sermaye; Ocak 2027'de güncelle
        "kicker": "TAPU HARCI 2026", "stat": "%2 + %2",
        "sub": "alıcı ve satıcı ayrı · döner sermaye 2.227 ₺ × katsayı"},
    "arac-muayene-ucreti": lambda: {
        # TÜVTÜRK 2026 tarifesi (KTK md.35, YD oranıyla); Ocak 2027'de sayfayla birlikte güncelle
        "kicker": "ARAÇ MUAYENE ÜCRETİ 2026", "stat": "₺3.288",
        "sub": "otomobil · gecikme %5/ay · 2027 tahminini hesapla"},
    "damga-vergisi-hesaplama": lambda: {
        # DVK Genel Tebliği Seri 71 (RG 31.12.2025) oranları; Ocak 2027'de sayfayla birlikte güncelle
        "kicker": "DAMGA VERGİSİ 2026", "stat": "binde 9,48",
        "sub": "kira binde 1,89 · maaş binde 7,59 · 2027 tutar tahmini"},
    "tasit-kredisi-hesaplama": faiz_card(
        "kredi", "tasit", "TAŞIT KREDİSİ FAİZİ", "aylik", "TCMB ortalaması · peşinat ve BDDK vade sınırı"),
    "vergi-dilimi-hesaplama": vergi_dilimi_card,
    "ihbar-tazminati-hesaplama": lambda: {
        # İş Kanunu md.17 — sabit kural
        "kicker": "İHBAR TAZMİNATI 2026", "stat": "2–8 hafta",
        "sub": "kıdeme göre ihbar süresi · brüt ve net tazminatı hesapla"},
    "yillik-izin-hesaplama": lambda: {
        # İş Kanunu md.53 — sabit kural
        "kicker": "YILLIK İZİN 2026", "stat": "14 · 20 · 26 gün",
        "sub": "kıdeme göre izin hakkı · kullanılmayan izin ücretini hesapla"},
    "gelir-vergisi-hesaplama": lambda: {
        # 332 Seri No'lu GVK Tebliği; Ocak 2027'de sayfayla birlikte güncelle
        "kicker": "KİRA GELİR VERGİSİ 2026", "stat": "₺58.000",
        "sub": "konut kira istisnası · %15 götürü gider · beyan Mart 2027"},
    "yeniden-degerleme-orani": yd_card(
        "YENİDEN DEĞERLEME ORANI {yil}",
        lambda d, k: ("kesinleşti · MTV, harç ve cezaların zam oranı" if k
                      else f"{ay_adi(d['sonAy'])} Yİ-ÜFE tahmini · Kasım'da kesinleşir")),
    "mtv-hesaplama": yd_card(
        "MTV {yil} ZAM TAHMİNİ",
        lambda d, k: "2026 MTV'nizden 2027 tahmininizi hesaplayın"),
    "emlak-vergisi-hesaplama": yd_card(
        "EMLAK VERGİSİ {yil} ARTIŞI",
        lambda d, k: "vergi değeri × oran · 2. taksit son gün 30 Kasım"),
    "trafik-cezalari-hesaplama": lambda: {
        # 7574 sayılı Kanun tutarları (RG 27.02.2026); 2027 artışı netleşince güncelle
        "kicker": "TRAFİK CEZALARI 2026", "stat": "₺5.000",
        "sub": "kırmızı ışık · hız cezanızı hesaplayın (2.000-30.000 ₺)"},
    "pasaport-ehliyet-harci": yd_card(
        "PASAPORT · EHLİYET HARCI {yil}",
        lambda d, k: "2026: 10 yıllık pasaport 14.761 ₺ · harç zammı tahmini"),
    "konut-kredisi-hesaplama": faiz_card(
        "kredi", "konut", "KONUT KREDİSİ FAİZİ", "aylik", "TCMB ortalaması · taksit ve peşinat hesapla"),
    "ihtiyac-kredisi-hesaplama": faiz_card(
        "kredi", "ihtiyac", "İHTİYAÇ KREDİSİ FAİZİ", "aylik", "TCMB ortalaması · KKDF+BSMV dahil taksit"),
    "kredi-hesaplama": faiz_card(
        "kredi", "ihtiyac", "KREDİ HESAPLAMA", "aylik", "ihtiyaç kredisi TCMB ortalaması · taksit tablosu"),
    "mevduat-faizi-hesaplama": faiz_card(
        "mevduat", "ay3", "MEVDUAT FAİZ ORANI", "basit", "3 aya kadar · TCMB ortalaması · net getiri hesapla"),
    "emekli-zammi-hesaplama": emekli_card,
    "evde-bakim-maasi": evde_bakim_card,
    "engelli-maasi": engelli_card,
    "memur-zammi-hesaplama": memur_card,
    "en-dusuk-emekli-maasi": emekli_memur_card("taban"),
    "bayram-ikramiyesi": emekli_memur_card("bayram"),
    "kira-artis-orani-hesaplama": kira_card,
    "asgari-ucret-hesaplama": asgari_card,
    "enflasyon-takvimi": enflasyon_card,
    "enflasyon-hesaplama": enflasyon_card,
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
