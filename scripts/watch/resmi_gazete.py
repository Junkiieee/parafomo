#!/usr/bin/env python3
"""ParaFOMO — Resmî Gazete bekçisi (2026-11-10, CEO raporu R27).

Her sabah günün (ve kaçırılmış son N günün) Resmî Gazete fihristini okur, sitenin rakamlarını değiştirebilecek
düzenlemeleri konu başlığıyla yakalar ve /root/parafomo-data/rg/<gün>.json'a yazar. Sabah CEO raporu bunu okur;
eşleşme varsa Claude karar metnini (PDF/HTM) açıp doğrular, ilgili data/*.json'u günceller. Betik rakam DEĞİŞTİRMEZ.

  python scripts/watch/resmi_gazete.py [--gun 3]      son 3 gün (bugün dahil)

Mükerrer sayılar (ör. 20251231M1…M6.htm) da okunur: yıl sonu vergi tebliğleri (veraset, MTV, damga, harç, gelir
vergisi tarifesi) hep mükerrerde çıkar — 31.12.2025'in 6 mükerrerinden M5'teki 7 tebliğ eskiden hiç görülmüyordu.
"""
import argparse, datetime as dt, html, json, os, re, time, urllib.error, urllib.request

OUT = "/root/parafomo-data/rg"
BASE = "https://www.resmigazete.gov.tr/eskiler"
UA = {"User-Agent": "Mozilla/5.0 (compatible; ParaFOMO/1.0; +https://parafomo.com)"}

# konu → (başlıkta aranacak ifadeler [küçük harf], etkilenen sayfa/veri)
KONULAR = {
    "stopaj": (["geçici 67", "tevkifat oran", "stopaj", "mevduat"], "data/stopaj-mevduat.json · /mevduat-faizi-hesaplama/ · stopaj yazısı"),
    "yeniden_degerleme": (["vergi usul kanunu genel tebliğ", "yeniden değerleme"], "data/yeniden-degerleme.json · /yeniden-degerleme-orani/"),
    "harc_ceza": (["harçlar kanunu", "harç tarifeleri", "idari para ceza"], "harç/MTV/ceza sayfaları"),
    "mtv": (["motorlu taşıtlar vergisi"], "/mtv-hesaplama/"),
    "veraset": (["veraset ve intikal"], "data/veraset-2026.json · /veraset-ve-intikal-vergisi-hesaplama/"),
    "gelir_vergisi": (["gelir vergisi genel tebliğ"],
                      "yeni yıl GV tarifesi: data/gelir-vergisi-tarife.json (vergi-dilimi, gelir-vergisi, net-maas, deger-artis-kazanci)"),
    "damga": (["damga vergisi"], "/damga-vergisi-hesaplama/ (BAZ_YIL, maktu tutarlar)"),
    "asgari_ucret": (["asgari ücret"], "net maaş / asgari ücret sayfaları"),
    "memur_emekli": (["memur maaş", "katsayı", "toplu sözleşme"], "emekli/memur zammı sayfaları"),
    "kredi_karti": (["kredi kartı", "banka kartları ve kredi kartları"], "/kredi-karti-faiz-hesaplama/"),
    "kkdf_bsmv": (["kaynak kullanımını destekleme fonu", "banka ve sigorta muameleleri vergisi"], "kredi/faiz hesaplayıcıları"),
}
# Başlığı konuyu söylemeyen düzenlemeler: metinde bu ifadelerden biri yoksa eşleşme sayılmaz
# (VUK genel tebliğleri hep aynı başlıkla çıkar; 2026-11-10 Sıra 597 = vergi borçlusu ilanı, YD değil)
GOVDE_SART = {
    "yeniden_degerleme": ["yeniden değerleme oranı"],
}
# Başlıkta geçse de konu DEĞİL: meslek ücret tarifeleri her yıl "… Asgari Ücret Tarifesi" adıyla çıkar
# (31.12.2025: "Uzlaştırmacı Asgari Ücret Tarifesi", SPK "Gayrimenkul Değerleme Asgari Ücret Tarifesi"; avukatlık,
# arabuluculuk…). Gerçek karar "Asgari Ücret Tespit Komisyonu Kararı" başlığıyla yayımlanır.
HARIC = {
    "asgari_ucret": ["tarife", "uzlaştırmacı", "değerleme"],
}
MUKERRER_EN_COK = 8          # bir günde izlenecek en fazla mükerrer sayı (31.12.2025'te 6 tane vardı)
SURE_BUTCESI = 200           # sn: sabah_veri.py bu betiği 300 sn zaman aşımıyla çağırır; bütçe aşılınca mükerrerler atlanır
_BASLANGIC = time.monotonic()


def getir(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("cp1254", errors="replace")


def kucuk(s):
    """Türkçe küçük harf: str.lower() "İntikal"i "i̇ntikal" (i + birleşik nokta) yapıp "veraset ve intikal"i kaçırıyordu."""
    return s.replace("I", "ı").replace("İ", "i").lower()


def metin(url):
    if not url.endswith(".htm"):
        return None   # PDF: metin okunmaz → eşleşme "kontrol et" notuyla bırakılır
    try:
        return kucuk(re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", getir(url)))))
    except Exception:
        return None


def fihrist(gun):
    url = f"{BASE}/{gun:%Y}/{gun:%m}/{gun:%Y%m%d}.htm"
    try:
        s = getir(url)
    except urllib.error.HTTPError as e:
        return url, None if e.code == 404 else e
    except Exception as e:
        return url, e
    items = _maddeler(s, gun)
    # Mükerrer sayılar: ana fihristte 20251231M1.htm … bağlantısı (mutlak ya da göreli). Aynı ayıklama + aynı taban URL.
    mukerrer = sorted(set(re.findall(rf'href="(?:[^"]*/)?({gun:%Y%m%d}M\d+\.htm)"', s)),
                      key=lambda h: int(re.search(r"M(\d+)\.htm$", h).group(1)))
    for h in mukerrer[:MUKERRER_EN_COK]:
        murl = f"{BASE}/{gun:%Y}/{gun:%m}/{h}"
        if time.monotonic() - _BASLANGIC > SURE_BUTCESI:
            items.append({"baslik": f"[mükerrer {h} okunmadı: süre bütçesi doldu — elle bak]", "link": murl})
            continue
        try:
            items += [{**it, "mukerrer": h[:-4]} for it in _maddeler(getir(murl, timeout=20), gun)]
        except Exception as e:
            items.append({"baslik": f"[mükerrer {h} okunamadı: {str(e)[:60]} — elle bak]", "link": murl})
    if len(mukerrer) > MUKERRER_EN_COK:
        items.append({"baslik": f"[{len(mukerrer) - MUKERRER_EN_COK} mükerrer daha var, okunmadı — elle bak]", "link": url})
    return url, items


def _maddeler(s, gun):
    items = []
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', s, re.S):
        t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", m.group(2)))).strip(" –-")
        if len(t) > 15:
            href = m.group(1)
            items.append({"baslik": t, "link": href if href.startswith("http") else f"{BASE}/{gun:%Y}/{gun:%m}/{href.split('/')[-1]}"})
    return items


def eslestir(items):
    bulunan = []
    for it in items:
        low = kucuk(it["baslik"])
        for konu, (kel, etki) in KONULAR.items():
            if not any(x in low for x in kel):
                continue
            if any(x in low for x in HARIC.get(konu, [])):
                continue
            not_ = ""
            if konu in GOVDE_SART:
                txt = metin(it["link"])
                if txt is None:
                    not_ = "metin okunamadı (PDF) — elle kontrol et"
                elif not any(x in txt for x in GOVDE_SART[konu]):
                    continue   # başlık tuttu, içerik başka konu
            bulunan.append({**it, "konu": konu, "etkilenen": etki, **({"not": not_} if not_ else {})})
            break
    return bulunan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gun", type=int, default=3)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    bugun = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=3)).date()
    for k in range(a.gun - 1, -1, -1):
        gun = bugun - dt.timedelta(days=k)
        url, items = fihrist(gun)
        if items is None:
            print(f"[rg] {gun}: fihrist yok (yayın yok ya da henüz çıkmadı)")
            continue
        if isinstance(items, Exception):
            print(f"[rg] {gun}: HATA {items}")
            continue
        bulunan = eslestir(items)
        json.dump({"gun": str(gun), "fihrist": url, "madde": len(items), "eslesen": bulunan},
                  open(os.path.join(OUT, f"{gun}.json"), "w"), ensure_ascii=False, indent=1)
        print(f"[rg] {gun}: {len(items)} madde, {len(bulunan)} eşleşme")
        for b in bulunan:
            print(f"   ⚑ {b['konu']}: {b['baslik'][:160]}\n     {b['link']}\n     → {b['etkilenen']}" + (f"\n     ! {b['not']}" if b.get("not") else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
