#!/usr/bin/env python3
"""Panel verisini güncelleme aracı (Claude'un sabah rutini + istek işleme). Veri repo DIŞI: /root/parafomo-data/dash/

  python3 dashboard/panel.py istekler [--hepsi]                 Kaan'ın panelden yazdıkları (varsayılan: bitmemişler)
  python3 dashboard/panel.py istek <id> --durum okundu|yapiliyor|yapildi|yapilmayacak [--cevap "…"]
  python3 dashboard/panel.py gunluk "madde 1" "madde 2" …       İçerik sekmesinin üstündeki günlük not (bugünün tarihiyle)
  python3 dashboard/panel.py yapildi "başlık" [--link /yol/] [--tarih YYYY-MM-DD]   Web → Yapıldı listesine ekle
  python3 dashboard/panel.py is <W-id> --durum sirada|yapiliyor|yapildi            Web → Yapılacak işinin durumu
                                                                 (yapildi → listeden çıkar, Yapıldı'ya taşır)
  python3 dashboard/panel.py gorev-kapat <K-id>                  Kaan görevini kapat (doğruladıktan sonra)
  python3 dashboard/panel.py durum                               kararlar, kontrol anahtarları, "yaptım" işaretleri, dinleyici
  python3 dashboard/panel.py plan-not <kanal> "…"                onaylanan planın altına Claude notu (panelde görünür)
  python3 dashboard/panel.py bekle [--aralik 600]                DİNLEYİCİ (Kaan 2026-11-16: "10 dakikada bir"): panelde yeni
                                                                 eylem olana kadar 10 dakikada bir bakar; olunca olayları basıp
                                                                 çıkar. Claude arka planda çalıştırır, işleyince yeniden başlatır.
"""
import argparse
import datetime as dt
import json
import os
import sys
import time

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
    a = alt.add_parser("plan-not"); a.add_argument("kanal"); a.add_argument("metin")
    a = alt.add_parser("bekle"); a.add_argument("--aralik", type=float, default=600)
    a = ap.parse_args()

    if a.komut == "bekle":
        return bekle(a.aralik)

    if a.komut == "plan-not":
        kr = oku("kararlar.json", {})
        if a.kanal not in kr:
            print("bu kanal için onay yok:", a.kanal); return 1
        kr[a.kanal]["not"] = a.metin.strip()
        yaz("kararlar.json", kr); print("not yazıldı"); return 0

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
        b = oku("bekci.json", {})
        print("dinleyici:", f"son yoklama {int(time.time() - b['zaman'])} sn önce ({b.get('durum')})" if b.get("zaman") else "hiç çalışmadı")
        return 0
    return 1


def bekle(aralik):
    """Panelde yeni eylem olana kadar `aralik` saniyede bir bak; olunca olayları bas ve çık."""
    log, ofs_p = p("eylemler.jsonl"), p("bekci-ofset")
    try:
        ofs = int(open(ofs_p, encoding="utf-8").read().strip())
    except (OSError, ValueError):
        ofs = os.path.getsize(log) if os.path.exists(log) else 0   # ilk çalıştırma: geçmişi atla
    while True:
        boyut = os.path.getsize(log) if os.path.exists(log) else 0
        if boyut < ofs:      # dosya kısaldıysa baştan oku
            ofs = 0
        if boyut > ofs:
            with open(log, encoding="utf-8") as f:
                f.seek(ofs)
                yeni = f.read()
                ofs = f.tell()
            with open(ofs_p, "w", encoding="utf-8") as f:
                f.write(str(ofs))
            yaz("bekci.json", {"zaman": time.time(), "durum": "olay"})
            print("Panelde yeni eylem var:")
            for satir in yeni.splitlines():
                print(" ", satir)
            return 0
        yaz("bekci.json", {"zaman": time.time(), "durum": "dinliyor"})
        time.sleep(aralik)


if __name__ == "__main__":
    sys.exit(main())
