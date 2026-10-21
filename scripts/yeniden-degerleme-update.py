#!/usr/bin/env python3
"""Yİ-ÜFE serisi + yeniden değerleme oranı → data/yeniden-degerleme.json.

Yeniden değerleme oranı (VUK mük. 298/B) = Ekim ayı itibarıyla Yİ-ÜFE'nin "on iki aylık
ortalamalara göre" değişimi; Kasım sonunda VUK tebliğiyle ilan edilir ve ERTESİ yılın vergi,
harç ve cezalarına uygulanır. /yeniden-degerleme-orani, /mtv-hesaplama, /emlak-vergisi-hesaplama,
/pasaport-ehliyet-harci, /trafik-cezalari-hesaplama, /vergi-dilimi-, /gelir-vergisi-hesaplama ve
canlı blog yazıları (scripts/live-posts.py) bu dosyadan beslenir.

Kaynaklar (en yeni ayı veren kazanır; eşitse EVDS):
  1) TCMB EVDS TP.TUFE1YI.T1 — Yİ-ÜFE ENDEKS seviyeleri (2003=100). 12 aylık ortalama TÜİK'in
     yöntemiyle birebir: 2024-10 %43,93 · 2025-10 %25,49 · 2026-09 %27,81 (TÜİK bülteni) — 2026-10-18.
  2) TCMB "Üretici Fiyatları" HTML tablosu (yıllık/aylık %, 2 ondalık). Endeks yoksa oran,
     YILLIK değişimlerin önceki yıl endeks ağırlıklı ortalamasıyla hesaplanır (hata ≤0,005 puan).
     Eski yöntem (aylıklardan endeks kurmak) 24 adımda yuvarlama biriktirip %27,83 veriyordu.

Hedef yıl (oranın UYGULANACAĞI yıl): Haziran-Aralık verisi → ertesi yıl, Ocak-Mayıs → bu yıl.
Oran Ekim verisinde kesinleşir ve Kasım-Ocak zam sezonu boyunca ana hedef kalır. (Eski kural
Kasım verisi gelince 2028'e atlıyordu → Aralık'ta MTV/harç sayfaları 2027 yerine 2028 tahmini
gösterecekti.) Hedef değişirken eski yılın oranı `gecmis`e otomatik arşivlenir.

El/ajan alanları (hedef yıl değişene kadar korunur):
  tebligOrani     — VUK tebliğindeki resmî oran (Kasım sonu; sayfalar tebliği önceliklendirir)
  uygulananOrani  — MTV/harç/damga vergisinde Cumhurbaşkanı kararıyla uygulanan oran (2026: %18,95)
Ağ/ayıklama hatasında mevcut dosyaya dokunmaz, 0 döner. "GÜNCELLENDİ" basarsa veri değişti.
"""
import datetime as dt
import glob
import html
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "yeniden-degerleme.json")
ENDEKS_OUT = os.path.join(REPO, "data", "yiufe-endeks.json")  # değer artışı endekslemesi (/deger-artis-kazanci-hesaplama)
TUIK_CALS = os.path.join(REPO, "data", "tuik-enflasyon-*.json")
URL = ("https://www.tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Istatistikler/"
       "Enflasyon+Verileri/Uretici+Fiyatlari")
EVDS = "https://evds3.tcmb.gov.tr/igmevdsms-dis/"
EVDS_SERIES = "TP.TUFE1YI.T1"
EVDS_ENV = os.path.expanduser("~/.config/parafomo/evds.env")


def _next_key(k):
    y, mo = int(k[:4]), int(k[5:])
    return f"{y + 1}-01" if mo == 12 else f"{y}-{mo + 1:02d}"


def fetch_tcmb_table():
    """{YYYY-MM: {yillik, aylik}} — TCMB HTML tablosu."""
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


def evds_key():
    try:
        raw = open(EVDS_ENV, encoding="utf-8").read()
    except OSError:
        return None
    m = re.search(r"EVDS_API_KEY\s*=\s*['\"]?([^'\"\s]+)", raw)
    return m.group(1) if m else (raw.strip() or None)


def fetch_evds_levels(start_year):
    """{YYYY-MM: endeks} — EVDS Yİ-ÜFE (2003=100). Anahtar yoksa {}."""
    k = evds_key()
    if not k:
        return {}
    end = dt.date.today()
    url = (f"{EVDS}series={EVDS_SERIES}&startDate=01-01-{start_year}"
           f"&endDate=01-{end.month:02d}-{end.year}&type=json")
    req = urllib.request.Request(url, headers={"key": k, "User-Agent": "parafomo-yiufe/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        items = json.loads(r.read().decode("utf-8", "replace")).get("items", [])
    col = EVDS_SERIES.replace(".", "_")
    out = {}
    for it in items:
        v = it.get(col)
        if v in (None, "", "null"):
            continue
        y, mo = it["Tarih"].split("-")
        out[f"{int(y)}-{int(mo):02d}"] = float(v)
    return out


def _consecutive(keys):
    return all(b == _next_key(a) for a, b in zip(keys, keys[1:]))


def avg12_from_levels(levels, upto):
    """TÜİK yöntemi: son 12 ayın endeks ortalaması / önceki 12 ayın ortalaması − 1."""
    keys = sorted(k for k in levels if k <= upto)[-24:]
    if len(keys) < 24 or keys[-1] != upto or not _consecutive(keys):
        return None
    return round(sum(levels[k] for k in keys[12:]) / sum(levels[k] for k in keys[:12]) * 100 - 100, 2)


def avg12_from_changes(months, upto):
    """Endeks yokken: yıllık değişimlerin, önceki yılın (aylıklardan kurulan) endeks ağırlıklı ortalaması.
    Σ I(t-12)·(1+y_t) / Σ I(t-12) − 1 — yıllık % 2 ondalıkla yayımlandığı için hata ≤0,005 puan."""
    keys = sorted(k for k in months if k <= upto)[-24:]
    if len(keys) < 24 or keys[-1] != upto or not _consecutive(keys):
        return None
    prev, last = keys[:12], keys[12:]
    w, v = [], 100.0
    for i, k in enumerate(prev):
        if i:
            v *= 1 + months[k]["aylik"] / 100
        w.append(v)
    num = sum(wi * (1 + months[k]["yillik"] / 100) for wi, k in zip(w, last))
    return round(num / sum(w) * 100 - 100, 2)


def next_release(today):
    dates = []
    for p in glob.glob(TUIK_CALS):
        try:
            dates += [r["date"] for r in json.load(open(p, encoding="utf-8"))["releases"]]
        except Exception:
            pass
    for d in sorted(dates):
        if d > today.isoformat():
            return d
    y, m = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
    return f"{y}-{m:02d}-03"


def hedef_for(son_ay):
    yil, ay_no = int(son_ay[:4]), int(son_ay[5:])
    return yil + 1 if ay_no >= 6 else yil


def write_endeks(levels):
    """Yİ-ÜFE endeks seviyeleri (2003=100) — GVK mük. md.81 endekslemesi için. Yalnız değişince yazar."""
    if len(levels) < 120:
        return
    seri = {k: round(levels[k], 2) for k in sorted(levels)}
    old = {}
    if os.path.exists(ENDEKS_OUT):
        old = json.load(open(ENDEKS_OUT, encoding="utf-8"))
    if old.get("seri") == seri:
        return
    with open(ENDEKS_OUT, "w", encoding="utf-8") as f:
        json.dump({"_aciklama": "Yİ-ÜFE aylık endeks (2003=100), TCMB EVDS TP.TUFE1YI.T1. Değer artışı kazancında maliyet, "
                   "iktisap ayından önceki ay ile satış ayından önceki ay arasındaki artış %10+ ise endekslenir.",
                   "_kaynak": f"{EVDS} {EVDS_SERIES}", "updated": dt.date.today().isoformat(),
                   "sonAy": max(seri), "seri": seri}, f, ensure_ascii=False, indent=0)
        f.write("\n")
    print(f"[yd] endeks yazıldı: {min(seri)}..{max(seri)} ({len(seri)} ay)")


def main():
    try:
        table = fetch_tcmb_table()
    except Exception as e:
        print(f"[yd] UYARI: TCMB tablosu çekilemedi: {e}")
        table = {}
    if table:
        bad = [k for k, m in table.items() if not (-15 < m["aylik"] < 40 and -20 < m["yillik"] < 250)]
        if bad:
            print(f"[yd] UYARI: TCMB tablosunda şüpheli değerler {bad[:3]} — tablo kullanılmadı")
            table = {}
    try:
        levels = fetch_evds_levels(2005)
    except Exception as e:
        print(f"[yd] UYARI: EVDS çekilemedi: {e}")
        levels = {}
    write_endeks(levels)
    if not table and not levels:
        print("[yd] UYARI: iki kaynak da yok — yazılmadı")
        return 0

    son_table = max(table) if table else ""
    son_evds = max(levels) if levels else ""
    son_ay = max(son_table, son_evds)
    hedef_yil = hedef_for(son_ay)
    oran_ay = min(son_ay, f"{hedef_yil - 1}-10")       # oranı belirleyen son ay
    kesin = oran_ay == f"{hedef_yil - 1}-10"

    ort_evds = avg12_from_levels(levels, oran_ay) if levels else None
    ort_tab = avg12_from_changes(table, oran_ay) if table else None
    ort, kaynak = (ort_evds, "evds-endeks") if ort_evds is not None else (ort_tab, "tcmb-tablo")
    if ort is None or not (0 < ort < 200):
        print(f"[yd] UYARI: 12 aylık ortalama hesaplanamadı (oran ayı {oran_ay}) — yazılmadı")
        return 0
    if ort_evds is not None and ort_tab is not None and abs(ort_evds - ort_tab) > 0.02:
        print(f"[yd] UYARI: kaynaklar ayrışıyor (EVDS %{ort_evds} / tablo %{ort_tab}) — EVDS kullanıldı")

    # Aylık/yıllık % serisi: tablo esas; tablonun gerisinde kalan aylar EVDS endeksinden türetilir.
    months = dict(table)
    for k in sorted(levels):
        if k in months:
            continue
        y, mo = int(k[:4]), int(k[5:])
        prev_m = f"{y - 1}-12" if mo == 1 else f"{y}-{mo - 1:02d}"
        prev_y = f"{y - 1}-{mo:02d}"
        if prev_m in levels and prev_y in levels:
            months[k] = {"aylik": round((levels[k] / levels[prev_m] - 1) * 100, 2),
                         "yillik": round((levels[k] / levels[prev_y] - 1) * 100, 2)}
    if son_ay not in months:
        print(f"[yd] UYARI: {son_ay} için aylık/yıllık değişim yok — yazılmadı")
        return 0

    old = {}
    if os.path.exists(OUT):
        old = json.load(open(OUT, encoding="utf-8"))
    same_target = old.get("hedefYil") == hedef_yil
    gecmis = list(old.get("gecmis") or [])
    # Hedef yıl değiştiyse kapanan turun oranını geçmişe arşivle (ajan zaten eklemediyse)
    oy = old.get("hedefYil")
    if oy and not same_target and old.get("ekimVerisiGeldi") and not any(g.get("uygulamaYili") == oy for g in gecmis):
        gecmis.insert(0, {
            "uygulamaYili": oy,
            "oran": old.get("tebligOrani") or old.get("onikiAyOrt"),
            "uygulanan": old.get("uygulananOrani"),
            "not": "VUK tebliği (otomatik arşiv)" if old.get("tebligOrani") else
                   "Ekim Yİ-ÜFE ile hesaben kesinleşen oran (otomatik arşiv; tebliğ numarasını ekle)",
        })
        gecmis.sort(key=lambda g: -g.get("uygulamaYili", 0))

    keys = sorted(months, reverse=True)[:48]
    data = {
        "_aciklama": ("Yİ-ÜFE yıllık/aylık % değişim + yeniden değerleme oranı. hedefYil = oranın uygulanacağı "
                      "yıl; onikiAyOrt = sonAy itibarıyla 12 aylık ortalamalara göre değişim (sonAy en fazla "
                      "hedefYil-1 Ekim'idir; Ekim'de kesinleşir). veriSonAy = elimizdeki en yeni Yİ-ÜFE ayı. "
                      "tebligOrani: VUK tebliğindeki resmî oran; uygulananOrani: MTV/harç/damga vergisinde "
                      "Cumhurbaşkanı kararıyla uygulanan oran (ikisi de elle/ajan doğrulamasıyla yazılır)."),
        "_kaynak": URL,
        "_kaynakEvds": f"{EVDS} {EVDS_SERIES}",
        "updated": old.get("updated") or dt.date.today().isoformat(),
        "hesapKaynagi": kaynak,
        "sonAy": oran_ay,
        "veriSonAy": son_ay,
        "yiufeYillik": months[son_ay]["yillik"],
        "yiufeAylik": months[son_ay]["aylik"],
        "onikiAyOrt": ort,
        "hedefYil": hedef_yil,
        "ekimVerisiGeldi": kesin,
        "tebligOrani": old.get("tebligOrani") if same_target else None,
        "uygulananOrani": old.get("uygulananOrani") if same_target else None,
        "sonrakiAciklama": next_release(dt.date.today()),
        "gecmis": gecmis,
        "months": [{"ay": k, **months[k]} for k in keys],
    }
    ignore = {"updated", "sonrakiAciklama", "_aciklama", "_kaynak", "_kaynakEvds"}
    if {k: v for k, v in old.items() if k not in ignore} == {k: v for k, v in data.items() if k not in ignore}:
        print(f"[yd] değişiklik yok (veri {son_ay}, oran ayı {oran_ay}, 12 ay ort %{ort}, {kaynak})")
        if old.get("sonrakiAciklama") != data["sonrakiAciklama"]:
            old["sonrakiAciklama"] = data["sonrakiAciklama"]
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump(old, f, ensure_ascii=False, indent=1)
                f.write("\n")
        return 0
    data["updated"] = dt.date.today().isoformat()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    durum = "KESİNLEŞTİ" if kesin else "tahmin"
    print(f"[yd] GÜNCELLENDİ: veri {son_ay} (yıllık %{months[son_ay]['yillik']} aylık %{months[son_ay]['aylik']}) "
          f"→ {hedef_yil} oranı %{ort} [{durum}, {oran_ay} itibarıyla, {kaynak}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
