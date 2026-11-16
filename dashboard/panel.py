#!/usr/bin/env python3
"""Panel verisini güncelleme aracı (Claude'un sabah rutini + istek işleme). Veri repo DIŞI: /root/parafomo-data/dash/

  python3 dashboard/panel.py istekler [--hepsi]                 Kaan'ın panelden yazdıkları (varsayılan: bitmemişler)
  python3 dashboard/panel.py istek <id> --durum okundu|yapiliyor|yapildi|yapilmayacak [--cevap "…"]
  python3 dashboard/panel.py gunluk "madde 1" "madde 2" …       İçerik sekmesinin üstündeki günlük not (bugünün tarihiyle)
  python3 dashboard/panel.py yapildi "başlık" [--link /yol/] [--tarih YYYY-MM-DD]   Web → Yapıldı listesine ekle
  python3 dashboard/panel.py is <W-id> --durum sirada|yapiliyor|yapildi            Web → Yapılacak işinin durumu
                                                                 (yapildi → listeden çıkar, Yapıldı'ya taşır)
  python3 dashboard/panel.py gorev-kapat <K-id>                  Kaan görevini kapat (doğruladıktan sonra)
  python3 dashboard/panel.py durum                               kararlar, kontrol anahtarları, "yaptım" işaretleri
"""
import argparse
import datetime as dt
import json
import os
import sys

DASH = "/root/parafomo-data/dash"
TR = dt.timezone(dt.timedelta(hours=3))


def p(ad):
    return os.path.join(DASH, ad)


def oku(ad, varsayilan):
    try:
        with open(p(ad), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return varsayilan


def yaz(ad, veri):
    tmp = p(ad) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p(ad))


def bugun():
    return dt.datetime.now(TR).date().isoformat()


def main():
    ap = argparse.ArgumentParser()
    alt = ap.add_subparsers(dest="komut", required=True)
    a = alt.add_parser("istekler"); a.add_argument("--hepsi", action="store_true")
    a = alt.add_parser("istek"); a.add_argument("id", type=int)
    a.add_argument("--durum", required=True, choices=["okundu", "yapiliyor", "yapildi", "yapilmayacak"])
    a.add_argument("--cevap", default=None)
    a = alt.add_parser("gunluk"); a.add_argument("maddeler", nargs="+")
    a = alt.add_parser("yapildi"); a.add_argument("baslik"); a.add_argument("--link", default="")
    a.add_argument("--tarih", default=None)
    a = alt.add_parser("is"); a.add_argument("id"); a.add_argument("--durum", required=True, choices=["sirada", "yapiliyor", "yapildi"])
    a = alt.add_parser("gorev-kapat"); a.add_argument("id")
    alt.add_parser("durum")
    a = ap.parse_args()

    if a.komut == "istekler":
        lst = oku("istekler.json", [])
        acik = [x for x in lst if a.hepsi or x.get("durum") in ("yeni", "okundu", "yapiliyor")]
        if not acik:
            print("açık istek yok")
        for x in acik:
            g = f"  [görsel: {p('yuklenen/' + x['gorsel'])}]" if x.get("gorsel") else ""
            print(f"#{x['id']} {x['durum']:<12} {x['zaman']}{g}\n   {x.get('metin', '')}")
            if x.get("cevap"):
                print(f"   → cevap: {x['cevap']}")
        return 0

    if a.komut == "istek":
        lst = oku("istekler.json", [])
        x = next((i for i in lst if i.get("id") == a.id), None)
        if not x:
            print("yok:", a.id); return 1
        x["durum"] = a.durum
        if a.cevap is not None:
            x["cevap"] = a.cevap.strip()
        x["guncellendi"] = dt.datetime.now(TR).isoformat(timespec="seconds")
        yaz("istekler.json", lst); print("güncellendi:", a.id, a.durum); return 0

    plan = oku("plan.json", {})
    if a.komut == "gunluk":
        plan["gunluk"] = {"tarih": bugun(), "maddeler": [m.strip() for m in a.maddeler if m.strip()]}
        yaz("plan.json", plan); print("günlük not yazıldı"); return 0

    if a.komut == "yapildi":
        w = plan.setdefault("web", {})
        w.setdefault("yapildi", []).insert(0, {"tarih": a.tarih or bugun(), "baslik": a.baslik, **({"link": a.link} if a.link else {})})
        w["yapildi"] = w["yapildi"][:60]
        yaz("plan.json", plan); print("eklendi"); return 0

    if a.komut == "is":
        w = plan.setdefault("web", {})
        x = next((i for i in w.get("yapilacak", []) if i.get("id") == a.id), None)
        if not x:
            print("yok:", a.id); return 1
        if a.durum == "yapildi":
            w["yapilacak"] = [i for i in w["yapilacak"] if i.get("id") != a.id]
            w.setdefault("yapildi", []).insert(0, {"tarih": bugun(), "baslik": x["baslik"]})
        else:
            x["durum"] = a.durum
        yaz("plan.json", plan); print("güncellendi:", a.id, a.durum); return 0

    if a.komut == "gorev-kapat":
        once = len(plan.get("kaan", []))
        plan["kaan"] = [g for g in plan.get("kaan", []) if g.get("id") != a.id]
        yaz("plan.json", plan); print("kapatıldı" if len(plan["kaan"]) < once else "yok"); return 0

    if a.komut == "durum":
        print("kararlar:", json.dumps(oku("kararlar.json", {}), ensure_ascii=False))
        print("kontrol:", json.dumps(oku("kontrol.json", {}), ensure_ascii=False))
        print("görev işaretleri:", json.dumps(oku("gorevler.json", {}), ensure_ascii=False))
        sonlar = []
        try:
            sonlar = open(p("eylemler.jsonl"), encoding="utf-8").read().splitlines()[-10:]
        except OSError:
            pass
        print("son panel eylemleri:"); [print("  ", s) for s in sonlar]
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
