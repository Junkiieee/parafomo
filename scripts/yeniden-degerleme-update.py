#!/usr/bin/env python3
"""Yİ-ÜFE serisi + yeniden değerleme oranı tahmini → data/yeniden-degerleme.json.

Yeniden değerleme oranı (VUK mük. 298/B) = Ekim ayı itibarıyla Yİ-ÜFE'nin "on iki aylık
ortalamalara göre" değişimi; Kasım sonunda VUK tebliğiyle ilan edilir ve ERTESİ yılın vergi,
harç ve cezalarına uygulanır. /yeniden-degerleme-orani ve /mtv-hesaplama bu dosyadan beslenir.

Kaynak: TCMB "Üretici Fiyatları" tablosu (Yİ-ÜFE yıllık/aylık % değişim). 12 aylık ortalama,
aylık değişimlerden endeks yeniden kurularak hesaplanır (taban sadeleşir); sonuç TÜİK bülteni
ile eşleşir (Eylül 2026: hesap %27,81 = TÜİK %27,81 — 2026-10-10 doğrulandı).

Kesin oran: Ekim verisi geldiğinde onikiAyOrt o yılın kesin (hesaplanan) oranıdır; resmi
tebliğ değeri `tebligOrani` alanına ajan/el ile yazılır (sayfa tebliği önceliklendirir).
Ağ/ayıklama hatasında mevcut dosyaya dokunmaz, 0 döner. "GÜNCELLENDİ" basarsa veri değişti.
"""
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "yeniden-degerleme.json")
TUIK_CAL = os.path.join(REPO, "data", "tuik-enflasyon-2026.json")
URL = ("https://www.tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Istatistikler/"
       "Enflasyon+Verileri/Uretici+Fiyatlari")


def fetch_months():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (parafomo-yiufe/1.0)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        page = r.read().decode("utf-8", "replace")
    page = re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.S | re.I)
    t = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " | ", page)))
    months = {}
    # Satır: "MM-YYYY | ... |" içinde 2 sayı (ÜFE 2003=100 sütunları boş): Yİ-ÜFE yıllık, aylık
    for m in re.finditer(r"\b(\d{2})-(\d{4})\b(.{0,120}?)(?=\b\d{2}-\d{4}\b|$)", t):
        nums = re.findall(r"-?\d+\.\d+", m.group(3))
        if len(nums) == 2:
            months[f"{m.group(2)}-{m.group(1)}"] = {"yillik": float(nums[0]), "aylik": float(nums[1])}
    return months


def twelve_mo_avg(months, upto_key):
    """upto_key ayı itibarıyla 12 aylık ortalamalara göre % değişim (aylık serilerden)."""
    keys = sorted(k for k in months if k <= upto_key)[-36:]
    if len(keys) < 24:
        return None
    # ardışıklık kontrolü
    for a, b in zip(keys, keys[1:]):
        y, mo = int(a[:4]), int(a[5:])
        nxt = f"{y + 1}-01" if mo == 12 else f"{y}-{mo + 1:02d}"
        if b != nxt:
            return None
    idx, v = {}, 100.0
    for k in keys:
        v *= 1 + months[k]["aylik"] / 100
        idx[k] = v
    last12 = [idx[k] for k in keys[-12:]]
    prev12 = [idx[k] for k in keys[-24:-12]]
    return round((sum(last12) / 12) / (sum(prev12) / 12) * 100 - 100, 2)


def next_release(today):
    try:
        for r in json.load(open(TUIK_CAL))["releases"]:
            if r["date"] > today.isoformat():
                return r["date"]
    except Exception:
        pass
    y, m = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
    return f"{y}-{m:02d}-03"


def main():
    try:
        months = fetch_months()
    except Exception as e:
        print(f"[yd] UYARI: TCMB çekilemedi: {e}")
        return 0
    if len(months) < 24:
        print(f"[yd] UYARI: tablo ayıklanamadı ({len(months)} ay) — yazılmadı")
        return 0
    bad = [k for k, m in months.items() if not (-15 < m["aylik"] < 40 and -20 < m["yillik"] < 250)]
    if bad:
        print(f"[yd] UYARI: şüpheli değerler {bad[:3]} — yazılmadı")
        return 0
    son_ay = max(months)
    ort = twelve_mo_avg(months, son_ay)
    if ort is None or not (0 < ort < 200):
        print(f"[yd] UYARI: 12 aylık ortalama hesaplanamadı (son ay {son_ay}) — yazılmadı")
        return 0

    old = {}
    if os.path.exists(OUT):
        old = json.load(open(OUT, encoding="utf-8"))
    # Hedef yıl: son ay Kasım/Aralık ise o turun oranı Ekim'de kapandı → tahmin bir sonraki tura kayar
    yil, ay_no = int(son_ay[:4]), int(son_ay[5:])
    hedef_yil = yil + 1 if ay_no <= 10 else yil + 2
    kesin = ay_no == 10  # Ekim verisi = hedef yılın oranı hesaben kesinleşti (tebliğ Kasım sonu)
    keys = sorted(months, reverse=True)[:48]
    data = {
        "_aciklama": ("Yİ-ÜFE yıllık/aylık % değişim + yeniden değerleme oranı. onikiAyOrt = son ay "
                      "itibarıyla 12 aylık ortalamalara göre değişim (Ekim ayında kesinleşir). "
                      "tebligOrani: Resmî Gazete tebliğ değeri (elle/ajan doğrulamasıyla yazılır)."),
        "_kaynak": URL,
        "updated": dt.date.today().isoformat(),
        "sonAy": son_ay,
        "yiufeYillik": months[son_ay]["yillik"],
        "yiufeAylik": months[son_ay]["aylik"],
        "onikiAyOrt": ort,
        "hedefYil": hedef_yil,
        "ekimVerisiGeldi": kesin,
        "tebligOrani": old.get("tebligOrani") if old.get("hedefYil") == hedef_yil else None,
        "sonrakiAciklama": next_release(dt.date.today()),
        "gecmis": old.get("gecmis") or [],
        "months": [{"ay": k, **months[k]} for k in keys],
    }
    if old.get("months") == data["months"] and old.get("tebligOrani") == data["tebligOrani"]:
        print(f"[yd] değişiklik yok (son ay {son_ay}, 12 ay ort %{ort})")
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"[yd] GÜNCELLENDİ: {son_ay} yıllık %{months[son_ay]['yillik']} aylık %{months[son_ay]['aylik']} → 12 ay ort %{ort} ({hedef_yil} YD tahmini)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
