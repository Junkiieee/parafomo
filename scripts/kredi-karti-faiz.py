#!/usr/bin/env python3
"""TCMB kredi kartı azami faiz oranları (aylık, %) → data/kredi-karti-faiz.json.

Kaynak tablo (birincil): TCMB İstatistikler › Bankacılık Verileri › Kredi Kartı İşlemlerinde Uygulanacak
Azami Faiz Oranları. Satır: tarih · referans · TL <30 bin (akdi, gecikme) · 30-180 bin · >180 bin ·
nakit/KMH · yabancı para. Yeni ay satırı geldiyse dosyayı günceller ("GÜNCELLENDİ" yazar); ağ hatasında
dosyaya dokunmaz. evds-update.sh (Prş+Cum) çağırır.
"""
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "kredi-karti-faiz.json")
URL = ("https://www.tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Istatistikler/Bankacilik+Verileri/"
       "Kredi_Karti_Islemlerinde_Uygulanacak_Azami_Faiz_Oranlari")


def main():
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (parafomo-kk/1.0)"})
        page = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "ignore")
    except Exception as e:
        print(f"[kk-faiz] çekilemedi: {e}")
        return 0
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.S | re.I)
    t = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})((?: \d+,\d+){11})", t)
    if not m:
        print("[kk-faiz] tablo ayıklanamadı — dosya değişmedi")
        return 0
    v = [float(x.replace(",", ".")) for x in m.group(4).split()]
    gecerli = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
    try:
        old = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        old = {}
    data = {
        "gecerli": gecerli,
        "referans": v[0],
        "tl": [
            {"ust": 30000, "akdi": v[1], "gecikme": v[2]},
            {"ust": 180000, "akdi": v[3], "gecikme": v[4]},
            {"ust": None, "akdi": v[5], "gecikme": v[6]},
        ],
        "nakit": {"akdi": v[7], "gecikme": v[8]},
        "yp": {"akdi": v[9], "gecikme": v[10]},
        "kaynak": URL,
        "kontrol": dt.date.today().isoformat(),
        # BDDK Kurul Kararı 11581 (1.10.2026): limit ≤ 100.000 TL → dönem borcunun %20'si, üzeri %40.
        # Eşik değişirse ELLE güncelle (TCMB tablosunda yok).
        "asgari": old.get("asgari") or {"esik": 100000, "alt": 20, "ust": 40, "kaynak": "BDDK 11581 sayılı Kurul Kararı (1.10.2026)"},
    }
    changed = {k: data[k] for k in data if k != "kontrol"} != {k: old.get(k) for k in data if k != "kontrol"}
    if not changed:  # boş commit üretmemek için dosyaya dokunma
        print(f"[kk-faiz] aynı: {gecerli} · <30 bin akdi %{v[1]}")
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[kk-faiz] {'GÜNCELLENDİ' if changed else 'aynı'}: {gecerli} · <30 bin akdi %{v[1]} · referans %{v[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
