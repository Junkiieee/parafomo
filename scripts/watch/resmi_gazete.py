#!/usr/bin/env python3
"""ParaFOMO — Resmî Gazete bekçisi (2026-11-10, CEO raporu R27).

Her sabah günün (ve kaçırılmış son N günün) Resmî Gazete fihristini okur, sitenin rakamlarını değiştirebilecek
düzenlemeleri konu başlığıyla yakalar ve /root/parafomo-data/rg/<gün>.json'a yazar. Sabah CEO raporu bunu okur;
eşleşme varsa Claude karar metnini (PDF/HTM) açıp doğrular, ilgili data/*.json'u günceller. Betik rakam DEĞİŞTİRMEZ.

  python scripts/watch/resmi_gazete.py [--gun 3]      son 3 gün (bugün dahil)
"""
import argparse, datetime as dt, html, json, os, re, urllib.error, urllib.request

OUT = "/root/parafomo-data/rg"
BASE = "https://www.resmigazete.gov.tr/eskiler"
UA = {"User-Agent": "Mozilla/5.0 (compatible; ParaFOMO/1.0; +https://parafomo.com)"}

# konu → (başlıkta aranacak ifadeler [küçük harf], etkilenen sayfa/veri)
KONULAR = {
    "stopaj": (["geçici 67", "tevkifat oran", "stopaj", "mevduat"], "data/stopaj-mevduat.json · /mevduat-faizi-hesaplama/ · stopaj yazısı"),
    "yeniden_degerleme": (["vergi usul kanunu genel tebliğ", "yeniden değerleme"], "data/yeniden-degerleme.json · /yeniden-degerleme-orani/"),
    "harc_ceza": (["harçlar kanunu", "harç tarifeleri", "idari para ceza"], "harç/MTV/ceza sayfaları"),
    "mtv": (["motorlu taşıtlar vergisi"], "/mtv-hesaplama/"),
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


def getir(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("cp1254", errors="replace")


def metin(url):
    if not url.endswith(".htm"):
        return None   # PDF: metin okunmaz → eşleşme "kontrol et" notuyla bırakılır
    try:
        return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", getir(url)))).lower()
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
    items = []
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', s, re.S):
        t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", m.group(2)))).strip(" –-")
        if len(t) > 15:
            href = m.group(1)
            items.append({"baslik": t, "link": href if href.startswith("http") else f"{BASE}/{gun:%Y}/{gun:%m}/{href.split('/')[-1]}"})
    return url, items


def eslestir(items):
    bulunan = []
    for it in items:
        low = it["baslik"].lower()
        for konu, (kel, etki) in KONULAR.items():
            if not any(x in low for x in kel):
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
