#!/usr/bin/env python3
"""TÜFE aylık/yıllık % değişim serisi → data/tufe-aylik.json (TCMB'nin TÜİK tablosundan).

Kaynak: TCMB "Tüketici Fiyatları" sayfası — TÜİK TÜFE'nin aylık ve yıllık % değişimi, ay ay
(2025=100). /emekli-zammi-hesaplama (Ocak/Temmuz emekli-memur zammı birikimli enflasyonu) bu
dosyadan beslenir. Ağ/ayıklama hatasında mevcut dosyaya dokunmaz. "GÜNCELLENDİ" basarsa veri değişti.
"""
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "tufe-aylik.json")
URL = ("https://www.tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Istatistikler/"
       "Enflasyon+Verileri/Tuketici+Fiyatlari")


def main():
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (parafomo-tufe/1.0)"})
        with urllib.request.urlopen(req, timeout=30) as r:
            page = r.read().decode("utf-8", "replace")
    except Exception as e:
        print(f"[tufe] UYARI: çekilemedi: {e}")
        return 0
    page = re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.S | re.I)
    t = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " | ", page)))
    rows = re.findall(r"\b(\d{2})-(\d{4}) [| ]+(-?\d+\.\d+) [| ]+(-?\d+\.\d+)", t)
    months = []
    for mm, yy, yearly, monthly in rows:
        months.append({"ay": f"{yy}-{mm}", "yillik": float(yearly), "aylik": float(monthly)})
    months = sorted({m["ay"]: m for m in months}.values(), key=lambda m: m["ay"], reverse=True)[:48]
    # makullük: en az 12 ay, ardışık, değerler mantıklı aralıkta
    if len(months) < 12 or any(not (-10 < m["aylik"] < 30 and -10 < m["yillik"] < 200) for m in months):
        print(f"[tufe] UYARI: tablo ayıklanamadı ({len(months)} satır) — yazılmadı")
        return 0
    old = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    if old.get("months") == months:
        print(f"[tufe] değişiklik yok (son ay {months[0]['ay']})")
        return 0
    data = {
        "_aciklama": "TÜİK TÜFE aylık ve yıllık % değişim (2025=100). ay = YYYY-AA, en yeni başta.",
        "_kaynak": URL,
        "updated": dt.date.today().isoformat(),
        "months": months,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"[tufe] GÜNCELLENDİ: son ay {months[0]['ay']} yıllık %{months[0]['yillik']} aylık %{months[0]['aylik']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
