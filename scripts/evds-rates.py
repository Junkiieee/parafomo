#!/usr/bin/env python3
"""TCMB EVDS haftalık ağırlıklı ortalama faizler → data/faiz-oranlari.json.

Seriler (EVDS3, haftalık-Cuma, akım = o hafta açılan/yenilenen hesaplar):
  TL mevduat  TP.TRY.MT01..MT06  (1 aya kadar … 1 yıl+, toplam)
  TL kredi    TP.KTF10 ihtiyaç · TP.KTF11 taşıt · TP.KTF12 konut (yalnız sabit faizli) · TP.KTFTUK tüketici
Metodoloji (TCMB metaveri PDF'leri, 2026-10-15 okundu): oranlar YILLIK BİLEŞİK (efektif).
  Kredi → aylık eşdeğer = (1+E)^(1/12) − 1   (hesaplayıcılar aylık faiz ister)
  Mevduat → bankaların ilan ettiği basit yıllık faiz eşdeğeri, b gün vade için:
            ((1+E)^(b/365) − 1) × 365/b      (mevduat hesaplayıcısı basit faiz ister)
Anahtar: /root/.config/parafomo/evds.env → EVDS_API_KEY (repo DIŞI). Anahtar/ağ hatasında dosyaya dokunmaz.
"GÜNCELLENDİ" basarsa yeni hafta geldi.
"""
import datetime as dt
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "faiz-oranlari.json")
API = "https://evds3.tcmb.gov.tr/igmevdsms-dis"
KEYFILE = os.path.expanduser("~/.config/parafomo/evds.env")

DEPOSIT = {  # seri → (anahtar, etiket, basit faiz eşdeğeri için temsilî gün)
    "TP.TRY.MT01": ("ay1", "1 aya kadar", 32),
    "TP.TRY.MT02": ("ay3", "3 aya kadar", 92),
    "TP.TRY.MT03": ("ay6", "6 aya kadar", 181),
    "TP.TRY.MT04": ("yil1", "1 yıla kadar", 365),
    "TP.TRY.MT05": ("yil1plus", "1 yıl ve daha uzun", 365),
    "TP.TRY.MT06": ("toplam", "Toplam (tüm vadeler)", 92),
}
LOAN = {
    "TP.KTF10": ("ihtiyac", "İhtiyaç kredisi"),
    "TP.KTF11": ("tasit", "Taşıt kredisi"),
    "TP.KTF12": ("konut", "Konut kredisi (sabit faizli)"),
    "TP.KTFTUK": ("tuketici", "Tüketici kredisi (toplam)"),
}
SOURCES = {
    "mevduat": "https://www.tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Istatistikler/Faiz+Istatistikleri/Haftalik/Mevduat+Faiz+Oranlari/",
    "kredi": "https://www.tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Istatistikler/Faiz+Istatistikleri/Haftalik/Kredi+Faiz+Oranlari/",
}


def key():
    k = os.environ.get("EVDS_API_KEY", "")
    if not k and os.path.exists(KEYFILE):
        for line in open(KEYFILE, encoding="utf-8"):
            line = line.strip()
            if line.startswith("EVDS_API_KEY="):
                k = line.split("=", 1)[1].strip().strip('"').strip("'")
            elif line and "=" not in line:   # ham anahtar da kabul (Kaan ilk kez öyle yazdı)
                k = line
    return k


def fetch(series, start, end, k):
    url = f"{API}/series={'-'.join(series)}&startDate={start:%d-%m-%Y}&endDate={end:%d-%m-%Y}&type=json"
    req = urllib.request.Request(url, headers={"key": k, "User-Agent": "parafomo-evds/1.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)["items"]


def monthly(e):      # efektif yıllık % → aylık eşdeğer %
    return ((1 + e / 100) ** (1 / 12) - 1) * 100


def simple(e, days):  # efektif yıllık % → b günlük vade için basit yıllık %
    return ((1 + e / 100) ** (days / 365) - 1) * 365 / days * 100


def main():
    k = key()
    if not k:
        print("[evds] UYARI: EVDS_API_KEY yok (~/.config/parafomo/evds.env) — yazılmadı")
        return 0
    end = dt.date.today()
    try:
        items = fetch(list(DEPOSIT) + list(LOAN), end - dt.timedelta(days=400), end, k)
    except Exception as e:
        print(f"[evds] UYARI: çekilemedi: {e}")
        return 0
    rows = []
    for it in items:
        vals = {}
        for code in list(DEPOSIT) + list(LOAN):
            v = it.get(code.replace(".", "_"))
            vals[code] = round(float(v), 2) if v not in (None, "") else None
        if all(v is None for v in vals.values()):
            continue
        d = dt.datetime.strptime(it["Tarih"], "%d-%m-%Y").date()
        rows.append((d, vals))
    rows.sort()
    if len(rows) < 20:
        print(f"[evds] UYARI: yalnız {len(rows)} hafta geldi — yazılmadı")
        return 0
    last_d, last = rows[-1]
    # makullük: TL faizleri %1-%200 aralığında olmalı
    core = [last[c] for c in ("TP.TRY.MT01", "TP.TRY.MT02", "TP.KTF10", "TP.KTF12")]
    if any(v is None or not (1 < v < 200) for v in core):
        print(f"[evds] UYARI: son hafta değerleri anormal {core} — yazılmadı")
        return 0
    prev = next(((d, v) for d, v in reversed(rows[:-1]) if d <= last_d - dt.timedelta(days=6)), rows[-2])

    def chg(code):
        a, b = last.get(code), prev[1].get(code)
        return round(a - b, 2) if a is not None and b is not None else None

    data = {
        "_aciklama": ("TCMB haftalık ağırlıklı ortalama TL faizleri (akım). Oranlar YILLIK BİLEŞİK (efektif). "
                      "kredi.aylik = (1+E)^(1/12)-1; mevduat.basit = gün vadeli basit yıllık eşdeğer."),
        "_kaynak": SOURCES,
        "updated": dt.date.today().isoformat(),
        "hafta": last_d.isoformat(),
        "oncekiHafta": prev[0].isoformat(),
        "mevduat": {},
        "kredi": {},
        "seri": [],
    }
    for code, (k_, label, days) in DEPOSIT.items():
        e = last[code]
        if e is None:
            continue
        data["mevduat"][k_] = {"etiket": label, "yillikBilesik": e, "basit": round(simple(e, days), 2),
                               "basitGun": days, "degisim": chg(code), "seri": code}
    for code, (k_, label) in LOAN.items():
        e = last[code]
        if e is None:
            continue
        data["kredi"][k_] = {"etiket": label, "yillikBilesik": e, "aylik": round(monthly(e), 2),
                             "degisim": chg(code), "seri": code}
    for d, v in rows[-52:]:
        data["seri"].append({"hafta": d.isoformat(), "mevduat3ay": v["TP.TRY.MT02"], "mevduat1ay": v["TP.TRY.MT01"],
                             "ihtiyac": v["TP.KTF10"], "konut": v["TP.KTF12"], "tasit": v["TP.KTF11"]})
    old = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    if old.get("hafta") == data["hafta"] and old.get("seri") == data["seri"]:
        print(f"[evds] değişiklik yok (son hafta {data['hafta']})")
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    m, c = data["mevduat"], data["kredi"]
    print(f"[evds] GÜNCELLENDİ: hafta {data['hafta']} · mevduat 3ay %{m['ay3']['yillikBilesik']} "
          f"(basit %{m['ay3']['basit']}) · ihtiyaç %{c['ihtiyac']['yillikBilesik']} (aylık %{c['ihtiyac']['aylik']}) "
          f"· konut %{c['konut']['yillikBilesik']} (aylık %{c['konut']['aylik']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
