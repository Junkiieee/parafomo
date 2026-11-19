#!/usr/bin/env python3
"""ParaFOMO — yıl devri bekçisi (denetim 2026-11-18, veri-5 + seo-5c).

Yıla bağlı veri dosyaları ve sayfa sabitleri yeni yıla geçmeden kalırsa sabah CEO raporunda ⚑ yazar. Rakam
DEĞİŞTİRMEZ, yalnız raporlar (resmi_gazete.py gibi). Neden: Ocak tebliğleri (veraset, gelir vergisi tarifesi,
damga, harç) 31 Aralık'ta mükerrer Resmî Gazete'de çıkar; TÜİK yeni yıl takvimini ~2 Ocak'ta yayımlar. Bunları
güncellemeyi hatırlatan tek yer agent/plan/week.md'deki bir liste idi ve onu okuyan aktif bir iş yok.

  python scripts/watch/yil_devri.py                 bugün
  python scripts/watch/yil_devri.py --tarih 2027-01-10 --root /kopya/repo     prova

Durumlar: ⚑ eşik günü geçti, hâlâ eski yıl · · bekleniyor (15 Aralık'tan itibaren yaklaşan Ocak işleri de) ·
✓ güncel. Çıkış kodu her zaman 0; son satır özet.
"""
import argparse, datetime as dt, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# (tür, dosya, json yolu | regex (1. grup = yıl), eşik (ay, gün): bu günden sonra hâlâ eskiyse ⚑, ne yapılır)
# Yıl bilgisi dosya ADINDA olanlar (veraset-2026.json…) yeni yılda da aynı dosyada güncellenir; içindeki yil ilerler.
KONTROLLER = [
    ("json", "data/asgari-ucret.json", "guncel.yil", (1, 2),
     "asgari-ucret-watch.py 1 Ocak'ta kendisi taşır; taşımadıysa yeni yılı 'yeni'ye yaz (≥2 kaynak)"),
    ("json", "data/gelir-vergisi-tarife.json", "yil", (1, 3),
     "Gelir Vergisi Genel Tebliği (31 Aralık, mükerrer RG): tarifeler'e yeni yıl (ücret/ücret dışı) + yil → net maaş, vergi dilimi, "
     "gelir vergisi, değer artışı; sonra o sayfaların METIN_YILI metinleri"),
    ("json", "data/veraset-2026.json", "yil", (1, 5), "VİVK Genel Tebliği (31 Aralık, mükerrer RG): istisnalar + dilimler"),
    ("const", "src/pages/damga-vergisi-hesaplama.astro", r"const BAZ_YIL = (\d{4})", (1, 5),
     "Damga Vergisi Genel Tebliği (31 Aralık, mükerrer RG): maktu tutarlar ve üst sınır, sonra BAZ_YIL"),
    ("const", "src/pages/mevduat-faizi-hesaplama.astro", r"31\.12\.(\d{4})'y[ae] kadar", (1, 2),
     "mevduat stopaj oranları CB kararıyla bu yılın sonuna kadardı: yeni karar (RG) → oranlar + yorum + SSS"),
    ("json", "data/tapu-harci-2026.json", "yil", (1, 10), "TKGM yeni yıl döner sermaye fiyat listesi (gösterge); harç oranı kanunda"),
    ("json", "data/bagkur-prim-2026.json", "yil", (1, 10), "SGK genelgesi: Bağ-Kur prim oranları / tavan katı"),
    ("const", "src/pages/noter-ucretleri.astro", r"const BAZ = (\d{4})", (1, 10), "Noterlik Ücret Tarifesi + Harçlar Genel Tebliği tutarları"),
    ("json", "data/asgari-ucret.json", "oranlar.yil", (1, 15), "SGK işçi/işveren prim oranları ve teşvik puanları"),
    ("json", "data/dogum-yardimi-2026.json", "yil", (1, 15), "tutarlar kanunla sabit: artış yoksa doğrulayıp yil'i ilerlet"),
    ("json", "data/asgari-ucret.json", "destek.yil", (1, 31), "işverene asgari ücret desteği: yeni yıl tutarı (karar çıkınca)"),
    ("json", "data/emekli-memur.json", "bayramIkramiyesi.yil", (2, 15), "Ramazan Bayramı öncesi: emekli bayram ikramiyesi tutarı"),
]
# Metinleri belli bir yıl için elle yazılmış sayfalar: verinin yılı metnin yılını geçerse ⚑ (build de uyarır; sayfa
# o arada kendi yılının verisiyle tutarlı kalır — gelir vergisi tarifesi tarifeler[METIN_YILI], asgari ücret yalın mod).
METIN_YILI = [
    ("src/pages/vergi-dilimi-hesaplama.astro", r"const METIN_YILI = (\d{4})", "data/gelir-vergisi-tarife.json", "yil"),
    ("src/pages/gelir-vergisi-hesaplama.astro", r"const METIN_YILI = (\d{4})", "data/gelir-vergisi-tarife.json", "yil"),
    ("src/pages/deger-artis-kazanci-hesaplama.astro", r"const METIN_YILI = (\d{4})", "data/gelir-vergisi-tarife.json", "yil"),
    ("src/pages/asgari-ucret-hesaplama.astro", r"const METIN_YILI = (\d{4})", "data/asgari-ucret.json", "guncel.yil"),
]
# Zam dönemi sayfaları (src/data/zam2027.ts PERIOD): hedef dönemin TÜFE'si açıklanınca (~3 Şubat / ~3 Ağustos) sonraki
# dönem başlar. Metinlerde dönem adı ("Ocak 2027") elle yazılı; PERIOD + TS oranı + metinler birlikte taşınmalı.
ZAM_MODUL = "src/data/zam2027.ts"
ZAM_SAYFALAR = ["memur-zammi-hesaplama", "emekli-zammi-hesaplama", "engelli-maasi", "enflasyon-farki-hesaplama",
                "emekli-refah-payi-seyyanen-zam", "kidem-tazminati-hesaplama", "en-dusuk-emekli-maasi",
                "2027-zam-hesaplama", "evde-bakim-maasi", "dul-ve-yetim-maasi", "zam-alarmi", "bedelli-askerlik-ucreti"]
ZAM_ESIK_GUN = 40  # hedef ay başından: Ocak → ~10 Şubat, Temmuz → ~10 Ağustos


def oku(root, yol):
    with open(os.path.join(root, yol), encoding="utf-8") as f:
        return f.read()


def json_deger(root, dosya, yol):
    d = json.loads(oku(root, dosya))
    for k in yol.split("."):
        d = d[k]
    return int(d)


def regex_deger(root, dosya, rx):
    m = re.search(rx, oku(root, dosya))
    if not m:
        raise ValueError(f"desen yok: {rx}")
    return int(m.group(1))


def kontrol(root, bugun):
    satirlar, ozet = [], {"⚑": 0, "·": 0, "✓": 0, "?": 0}
    aralik_sonu = bugun.month == 12 and bugun.day >= 15
    hedef = bugun.year + 1 if aralik_sonu else bugun.year

    def ekle(durum, metin):
        ozet[durum] += 1
        if durum != "✓":
            satirlar.append(f"{durum} {metin}")

    for tur, dosya, yol, (ay, gun), ne in KONTROLLER:
        try:
            v = json_deger(root, dosya, yol) if tur == "json" else regex_deger(root, dosya, yol)
        except (OSError, ValueError, KeyError, TypeError) as e:
            ekle("?", f"{dosya} {yol}: okunamadı ({type(e).__name__}: {str(e)[:60]})")
            continue
        if v >= hedef:
            ekle("✓", "")
            continue
        esik = dt.date(hedef, ay, gun)
        durum = "⚑" if bugun >= esik else "·"
        ek = " geçti" if durum == "⚑" else ""
        ekle(durum, f"{dosya} [{yol if tur == 'json' else 'yıl'}] = {v} → {hedef} bekleniyor "
                    f"(eşik {gun} {AYLAR[ay - 1]}{ek}): {ne}")

    # TÜİK yeni yıl takvimi: data/tuik-enflasyon-<yıl>.json (enflasyon takvimi, sonuç kutuları, geri sayımlar)
    tuik = f"data/tuik-enflasyon-{hedef}.json"
    if os.path.exists(os.path.join(root, tuik)):
        ekle("✓", "")
    else:
        esik = dt.date(hedef, 1, 3)
        durum = "⚑" if bugun >= esik else "·"
        ekle(durum, f"{tuik} yok ({'eşik 3 Ocak geçti' if durum == '⚑' else 'eşik 3 Ocak'}): TÜİK {hedef} Ulusal Veri "
                    f"Yayımlama Takvimi'nden TÜFE yayım günleri (biçim {hedef - 1} dosyasıyla aynı); o zamana dek tarihler "
                    "hafta sonu kaydırmalı '(tahmini)'")

    for dosya, rx, veri, yol in METIN_YILI:
        try:
            m, v = regex_deger(root, dosya, rx), json_deger(root, veri, yol)
        except (OSError, ValueError, KeyError, TypeError) as e:
            ekle("?", f"{dosya}: okunamadı ({type(e).__name__})")
            continue
        if v > m:
            ekle("⚑", f"{dosya}: metinler {m} için yazıldı, {veri} [{yol}] = {v} → sayfa {m} verisiyle kaldı; "
                      f"yıl/dilim metinlerini {v} yılına göre yaz, METIN_YILI = {v} (build de uyarıyor)")
        else:
            ekle("✓", "")

    try:
        mod = oku(root, ZAM_MODUL)
        son = re.search(r"export const PERIOD = \[([^\]]*)\]", mod).group(1)
        y, a = map(int, re.findall(r"'(\d{4})-(\d{2})'", son)[-1])
        hy, ha = (y + 1, 1) if a == 12 else (y, a + 1)
        donem = f"{AYLAR[ha - 1]} {hy}"
        esik = dt.date(hy, ha, 1) + dt.timedelta(days=ZAM_ESIK_GUN)
        if bugun >= esik:
            sayim = []
            for s in ZAM_SAYFALAR:
                p = os.path.join(root, "src/pages", s + ".astro")
                if os.path.exists(p):
                    n = oku(root, os.path.relpath(p, root)).count(donem)
                    if n:
                        sayim.append(f"{s} {n}")
            ekle("⚑", f"zam dönemi hâlâ {donem} ({ZAM_MODUL} PERIOD son ay {y}-{a:02d}); {donem} kesinleşti, sonraki "
                      f"döneme geçiş zamanı: PERIOD + toplu sözleşme oranı + sayfa metinleri. Elle '{donem}' geçen "
                      f"sayfalar: {', '.join(sayim) or '—'}")
        else:
            ekle("✓", "")
    except (OSError, AttributeError, IndexError, ValueError) as e:
        ekle("?", f"{ZAM_MODUL}: PERIOD okunamadı ({type(e).__name__})")

    return satirlar, ozet, hedef


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--tarih", help="YYYY-MM-DD (prova)")
    ap.add_argument("--root", default=ROOT, help="repo kökü (prova için kopya)")
    a = ap.parse_args()
    bugun = dt.date.fromisoformat(a.tarih) if a.tarih else (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=3)).date()
    satirlar, ozet, hedef = kontrol(a.root, bugun)
    for s in sorted(satirlar, key=lambda s: "⚑?·".index(s[0])):
        print(s)
    print(f"[yıl devri {bugun} → hedef {hedef}] ⚑ {ozet['⚑']} · bekleyen {ozet['·']} · okunamayan {ozet['?']} · "
          f"güncel {ozet['✓']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
