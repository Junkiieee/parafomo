#!/usr/bin/env python3
"""Aylık kira artış oranını (12 aylık TÜFE ortalaması) güncelle → data/kira-artis-2026.json.

Neden: veri 2026-08-13'te elle girilmiş, Eylül ve Ekim oranları hiç eklenmemişti; "ekim 2026 kira
artış oranı" talebin zirvesindeyken /kira-artis-orani-hesaplama "Ağustos 2026 %31,9" gösteriyordu.

Kaynak: TEDB aylık duyurusu (URL kalıbı sabit: /duyurular/<yıl>-<ay>-ayi-konut-ve-isyeri-kira-artis-orani).
Ay adı = UYGULAMA ayı (Ekim 2026 oranı = 5 Ekim'de açıklanan Eylül TÜFE'sinin 12 aylık ortalaması).
Güvenlik: oran 0-150 arasında ve önceki aydan en fazla 5 puan farklı değilse yazılmaz.

Kullanım: python3 scripts/kira-artis-update.py      # bu ayın oranı yoksa çek; "GÜNCELLENDİ" basar
Ağ/ayıklama hatasında mevcut JSON'a dokunmaz, 0 döner.
"""
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "kira-artis-2026.json")
TUIK = os.path.join(REPO, "data", "tuik-enflasyon-2026.json")
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
ASCII = str.maketrans("şŞıİğĞüÜöÖçÇ", "sSiIgGuUoOcC")
URL = "https://www.tedb.org.tr/duyurular/{yil}-{ay}-ayi-konut-ve-isyeri-kira-artis-orani"


def fetch_rate(yil, ay_idx):
    slug = AYLAR[ay_idx].translate(ASCII).lower()
    req = urllib.request.Request(URL.format(yil=yil, ay=slug), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        page = r.read().decode("utf-8", "replace")
    text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page)))
    m = re.search(r"kira artış oranı yüzde (\d{1,3}[,.]\d{1,2})", text, re.I)
    return float(m.group(1).replace(",", ".")) if m else None


def next_release(today):
    try:
        for r in json.load(open(TUIK))["releases"]:
            if r["date"] > today.isoformat():
                return r["date"]
    except Exception:
        pass
    y, m = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
    return f"{y}-{m:02d}-03"  # TÜİK genelde ~3'ü; takvim dosyası yoksa tahmin


def main():
    today = dt.date.today()
    data = json.load(open(DATA, encoding="utf-8"))
    label = f"{AYLAR[today.month - 1]} {today.year}"
    if data.get("guncelAy") == label:
        print(f"[kira] {label} zaten güncel (%{data['guncelOran']})")
        return 0
    try:
        rate = fetch_rate(today.year, today.month - 1)
    except Exception as e:
        print(f"[kira] UYARI: kaynak çekilemedi ({e}) — {label} henüz açıklanmamış olabilir")
        return 0
    if rate is None:
        print(f"[kira] {label} oranı sayfada bulunamadı — açıklanmamış olabilir")
        return 0
    prev = data.get("guncelOran")
    if not (0 < rate < 150) or (prev and abs(rate - prev) > 5):
        print(f"[kira] UYARI: şüpheli oran %{rate} (önceki %{prev}) — yazılmadı")
        return 0
    data["guncelAy"] = label
    data["guncelOran"] = rate
    data["sonrakiAciklama"] = next_release(today)
    data["gecmis"] = [{"ay": label, "oran": rate}] + [g for g in data.get("gecmis", []) if g["ay"] != label]
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[kira] GÜNCELLENDİ: {label} %{rate}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
