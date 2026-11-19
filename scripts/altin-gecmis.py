#!/usr/bin/env python3
"""Altın fiyat arşivi — data/altin-fiyat.json'daki GERÇEK kotasyonu günlük olarak data/altin-fiyat-gecmis.json'a ekler.

Neden (denetim 2026-11-19, seo-8): altın türü sayfaları (/altin-fiyatlari/<tür>/) %84-86 aynı metindi ve tarihli fiyat
aramaları ("15 ekim 22 ayar bilezik gram fiyatı", "1 yıl önce gram altın fiyatı") gösterim alıyordu, ama sitede geçmiş
fiyat yoktu. Bu arşiv her türün kendi "son günler" tablosunu besler.

Kurallar:
  - YALNIZ gerçek kaynak kotasyonu arşivlenir: _kaynak "finans.truncgil.com" ile başlamıyorsa (ör. Yahoo ile ölçeklenmiş
    yedek snapshot) o gün YAZILMAZ — türetilmiş rakam gerçek fiyat gibi saklanmaz.
  - Gün anahtarı kotasyonun TSİ tarihi; gün içindeki son çalışma o günün kaydını ezer (≈ günün son fiyatı).
  - Hafta sonu/tatil kaydı kaynak ne verdiyse odur; uydurma doldurma yok. En çok TUT gün tutulur.
  - İçerik değişmediyse dosyaya dokunulmaz (git gürültüsü yok); yazım atomik (geçici dosya + rename).
Çağıran: prices-refresh.sh (gün içi, Pzt–Cmt) ve daily-content.sh, altin-fiyat.py'den hemen sonra.
Kullanım: python3 scripts/altin-gecmis.py [--dry-run]     Çıkış kodu daima 0 (veri hattını bozmaz).
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "altin-fiyat.json")
OUT = os.path.join(ROOT, "data", "altin-fiyat-gecmis.json")
TUT = 400  # gün


def main():
    dry = "--dry-run" in sys.argv
    try:
        d = json.load(open(SRC, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"[altin-gecmis] kaynak okunamadı ({e}) — atlandı")
        return 0
    kaynak = str(d.get("_kaynak", ""))
    if not kaynak.startswith("finans.truncgil.com"):
        print(f"[altin-gecmis] kaynak gerçek kotasyon değil ({kaynak[:60]}) — bugün arşive yazılmadı")
        return 0
    gun, saat = str(d.get("guncellenme", ""))[:10], str(d.get("guncellenme", ""))[11:16]
    if len(gun) != 10:
        print("[altin-gecmis] guncellenme alanı yok — atlandı")
        return 0
    fiyat = {}
    for k in d.get("kalemler", []):
        a, s = k.get("alis"), k.get("satis")
        if isinstance(a, (int, float)) or isinstance(s, (int, float)):
            fiyat[k["key"]] = [a, s]
    if not fiyat:
        print("[altin-gecmis] kalem yok — atlandı")
        return 0
    try:
        arsiv = json.load(open(OUT, encoding="utf-8"))
    except (OSError, ValueError):
        arsiv = {}
    gunler = arsiv.get("gunler", {})
    yeni_kayit = {"saat": saat, "fiyat": fiyat}
    if gunler.get(gun) == yeni_kayit:
        print(f"[altin-gecmis] {gun} değişmedi")
        return 0
    gunler[gun] = yeni_kayit
    gunler = dict(sorted(gunler.items())[-TUT:])
    out = {
        "_aciklama": "Günlük altın fiyat arşivi (scripts/altin-gecmis.py). gunler[YYYY-MM-DD] = o günün son gerçek "
                     "kotasyonu (TSİ saat), fiyat[tür] = [alış, satış]; ons USD, diğerleri TL. Yalnız finans.truncgil.com "
                     "kotasyonu; Yahoo ile ölçeklenmiş yedek değerler arşive girmez.",
        "gunler": gunler,
    }
    if dry:
        print(f"[altin-gecmis] --dry-run: {gun} {saat} · {len(fiyat)} tür · arşivde {len(gunler)} gün (yazılmadı)")
        return 0
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(OUT), prefix=".altin-gecmis.", suffix=".json")
    # Gün başına tek satır: git farkı her gün yalnız bir satır değişir (dosya 400 günde ~400 satır kalır).
    satirlar = [f'  {json.dumps(g)}: {json.dumps(v, ensure_ascii=False, separators=(",", ":"))}' for g, v in gunler.items()]
    metin = ("{\n " + json.dumps("_aciklama") + ": " + json.dumps(out["_aciklama"], ensure_ascii=False)
             + ',\n "gunler": {\n' + ",\n".join(satirlar) + "\n }\n}\n")
    json.loads(metin)  # biçim bozuksa yazma (istisna → dosyaya dokunulmaz)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(metin)
    os.replace(tmp, OUT)
    print(f"[altin-gecmis] {gun} {saat} yazıldı · {len(fiyat)} tür · arşivde {len(gunler)} gün")
    return 0


if __name__ == "__main__":
    sys.exit(main())
