#!/usr/bin/env python3
"""Panel verisini güncelleme aracı (Claude'un sabah rutini + istek işleme). Veri repo DIŞI: /root/parafomo-data/dash/

  python3 dashboard/panel.py istekler [--hepsi]                 Kaan'ın panelden yazdıkları (varsayılan: bitmemişler)
  python3 dashboard/panel.py istek <id> --durum okundu|yapiliyor|yapildi|yapilmayacak [--cevap "…"]
  python3 dashboard/panel.py gunluk "madde 1" "madde 2" …       İçerik sekmesinin üstündeki günlük not (bugünün tarihiyle)
  python3 dashboard/panel.py yapildi "başlık" [--link /yol/] [--tarih YYYY-MM-DD] [--is <W-id>]
                                                                 Web → Yapıldı listesine ekle (geçmiş zamanla yaz: "…yönlendirildi");
                                                                 --is: o Yapılacak işini de kapatır (tek kayıt). Aynı gün aynı
                                                                 başlık/link varsa yenisi eklenmez, eskisi güncellenir.
  python3 dashboard/panel.py yapildi-sil "başlıktan parça" [--tarih YYYY-MM-DD] [--hepsi]   yanlış/yinelenen kaydı sil
  python3 dashboard/panel.py is <W-id> --durum sirada|yapiliyor|yapildi [--baslik "…"] [--link /yol/]
                                                                 Web → Yapılacak işinin durumu (yapildi → listeden çıkar,
                                                                 Yapıldı'ya --baslik ile, yoksa işin başlığıyla taşır)
  python3 dashboard/panel.py gorev-kapat <G-id>                  Kaan görevini kapat (doğruladıktan sonra; gorevler + eski kaan)
  python3 dashboard/panel.py deneme <F-id> [--basla YYYY-MM-DD|bugun] [--olcut "ölçü hedef"] [--bitis YYYY-MM-DD]
                                         [--sonuc "…"] [--durum sirada|deneniyor|durdu|sonuc|calisiyor]
                                                                 Deneme kaydı: başlangıç, başarı ölçütü, bitiş (varsayılan
                                                                 başlangıç + 14 gün); deneniyor'a geçince başlangıç bugündür
  python3 dashboard/panel.py denemeler                           denemeler: gün X/14, ölçütü/başlangıcı eksik, süresi dolan
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
DENEME_GUN = 14   # sabah.md D: "2 haftada tutmayanı durdur"


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


def _yapildi_bul(w, tarih, baslik=None, link=None, is_id=None):
    """Aynı gün aynı işe (is), aynı linke ya da aynı başlığa ait Yapıldı kaydı."""
    for x in w.get("yapildi", []):
        if x.get("tarih") == tarih and ((is_id and x.get("is") == is_id) or (link and x.get("link") == link)
                                        or (baslik and x.get("baslik") == baslik)):
            return x
    return None


def _yapildi_ekle(w, tarih, baslik, link="", is_id=None):
    """Yapıldı'ya ekle; aynı gün aynı kayıt varsa yenisini eklemek yerine onu güncelle (yinelenen satır olmasın)."""
    yeni = {"tarih": tarih, "baslik": baslik, **({"link": link} if link else {}), **({"is": is_id} if is_id else {})}
    x = _yapildi_bul(w, tarih, baslik, link, is_id)
    if x:
        x.update(yeni)
        return "güncellendi (aynı gün aynı kayıt vardı)"
    w.setdefault("yapildi", []).insert(0, yeni)
    w["yapildi"] = w["yapildi"][:60]
    return "eklendi"


def main():
    ap = argparse.ArgumentParser()
    alt = ap.add_subparsers(dest="komut", required=True)
    a = alt.add_parser("istekler"); a.add_argument("--hepsi", action="store_true")
    a = alt.add_parser("istek"); a.add_argument("id", type=int)
    a.add_argument("--durum", required=True, choices=["okundu", "yapiliyor", "yapildi", "yapilmayacak"])
    a.add_argument("--cevap", default=None)
    a = alt.add_parser("gunluk"); a.add_argument("maddeler", nargs="+")
    a = alt.add_parser("yapildi"); a.add_argument("baslik"); a.add_argument("--link", default="")
    a.add_argument("--tarih", default=None); a.add_argument("--is", dest="is_id", default=None)
    a = alt.add_parser("yapildi-sil"); a.add_argument("parca"); a.add_argument("--tarih", default=None)
    a.add_argument("--hepsi", action="store_true")
    a = alt.add_parser("is"); a.add_argument("id"); a.add_argument("--durum", required=True, choices=["sirada", "yapiliyor", "yapildi"])
    a.add_argument("--baslik", default=None); a.add_argument("--link", default="")
    a = alt.add_parser("gorev-kapat"); a.add_argument("id")
    a = alt.add_parser("deneme"); a.add_argument("id"); a.add_argument("--basla", default=None)
    a.add_argument("--olcut", default=None); a.add_argument("--bitis", default=None); a.add_argument("--sonuc", default=None)
    a.add_argument("--durum", default=None, choices=["sirada", "deneniyor", "durdu", "sonuc", "calisiyor"])
    alt.add_parser("denemeler")
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
        if a.is_id:   # aynı çağrıda Yapılacak işini kapat (eskiden `is … yapildi` + `yapildi` iki kayıt bırakıyordu)
            if not any(i.get("id") == a.is_id for i in w.get("yapilacak", [])):
                print(f"uyarı: {a.is_id} Yapılacak listesinde yok (zaten kapalı olabilir); kayıt yine de yazılıyor")
            w["yapilacak"] = [i for i in w.get("yapilacak", []) if i.get("id") != a.is_id]
        durum = _yapildi_ekle(w, a.tarih or bugun(), a.baslik, a.link, a.is_id)
        yaz("plan.json", plan); print(durum); return 0

    if a.komut == "yapildi-sil":
        w = plan.setdefault("web", {})
        hedef = [x for x in w.get("yapildi", []) if a.parca.lower() in x.get("baslik", "").lower()
                 and (not a.tarih or x.get("tarih") == a.tarih)]
        if not hedef:
            print("eşleşen kayıt yok"); return 1
        if len(hedef) > 1 and not a.hepsi:
            print(f"{len(hedef)} kayıt eşleşti (hepsini silmek için --hepsi):")
            for x in hedef:
                print("  ", x.get("tarih"), x.get("baslik", "")[:100])
            return 1
        w["yapildi"] = [x for x in w["yapildi"] if not any(x is h for h in hedef)]
        for x in hedef:
            print("silindi:", x.get("tarih"), x.get("baslik", "")[:100])
        yaz("plan.json", plan); return 0

    if a.komut == "is":
        w = plan.setdefault("web", {})
        x = next((i for i in w.get("yapilacak", []) if i.get("id") == a.id), None)
        if not x:
            print("yok:", a.id); return 1
        if a.durum == "yapildi":
            w["yapilacak"] = [i for i in w["yapilacak"] if i.get("id") != a.id]
            # --baslik yoksa işin (emir kipindeki) başlığı yazılır; aynı gün `yapildi --is <id>` gelirse onu günceller
            print(_yapildi_ekle(w, bugun(), a.baslik or x["baslik"], a.link, a.id))
        else:
            x["durum"] = a.durum
        yaz("plan.json", plan); print("güncellendi:", a.id, a.durum); return 0

    if a.komut == "gorev-kapat":
        # Görevler panel v2'de plan["gorevler"]de (server.py böyle okur); eski plan["kaan"] de temizlenir
        silinen = []
        for anahtar in ("gorevler", "kaan"):
            if anahtar in plan:
                silinen += [f"{anahtar}: {g.get('baslik', '')}" for g in plan[anahtar] if g.get("id") == a.id]
                plan[anahtar] = [g for g in plan[anahtar] if g.get("id") != a.id]
        if not silinen:
            print("yok:", a.id); return 1
        yaz("plan.json", plan)
        for s in silinen:
            print("kapatıldı:", a.id, "·", s)
        return 0

    if a.komut == "deneme":
        f = next((x for x in plan.get("fikirler", []) if x.get("id") == a.id), None)
        if not f:
            print("yok:", a.id); return 1
        if a.basla:
            f["baslangic"] = bugun() if a.basla == "bugun" else dt.date.fromisoformat(a.basla).isoformat()
        if a.durum:
            if a.durum == "deneniyor" and not f.get("baslangic"):
                f["baslangic"] = bugun()
            f["durum"] = a.durum
        if a.olcut is not None:
            f["olcut"] = a.olcut.strip()
        if a.sonuc is not None:
            f["sonuc"] = a.sonuc.strip()
        if a.bitis:
            f["bitis"] = dt.date.fromisoformat(a.bitis).isoformat()
        elif f.get("baslangic") and not f.get("bitis"):
            f["bitis"] = (dt.date.fromisoformat(f["baslangic"]) + dt.timedelta(days=DENEME_GUN)).isoformat()
        yaz("plan.json", plan)
        print("güncellendi:", a.id, f.get("durum"), "·", f.get("baslangic") or "başlangıç yok", "→", f.get("bitis") or "-",
              "·", f.get("olcut") or "ÖLÇÜT YOK")
        return 0

    if a.komut == "denemeler":
        bg = dt.date.fromisoformat(bugun())
        acik = [f for f in plan.get("fikirler", []) if f.get("durum") == "deneniyor"]
        print(f"{len(acik)} deneme sürüyor (sabah.md: en çok 5 eşzamanlı; süresi dolana sonuç yaz, durdur ya da kalıcı yap)")
        for f in acik:
            notlar = []
            if f.get("baslangic"):
                gun = (bg - dt.date.fromisoformat(f["baslangic"])).days + 1
                bitis = dt.date.fromisoformat(f.get("bitis") or (dt.date.fromisoformat(f["baslangic"])
                                                                 + dt.timedelta(days=DENEME_GUN)).isoformat())
                notlar.append(f"gün {gun}/{(bitis - dt.date.fromisoformat(f['baslangic'])).days}")
                if bg > bitis:
                    notlar.append(f"SÜRESİ DOLDU ({bitis}) → sonuç yaz")
            else:
                notlar.append("BAŞLANGIÇ YOK")
            if not f.get("olcut"):
                notlar.append("ÖLÇÜT YOK")
            print(f"  {f.get('id'):<4} {' · '.join(notlar):<40} {f.get('baslik', '')[:70]}")
        return 0

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
