#!/usr/bin/env python3
"""Açıklama günü kartı — LLM'SİZ (biçim kataloğu #9).

Neden: 3 Kasım'da event-short.py senaryo yazdıramadı (LLM haftalık kotası doldu) ve enflasyon günü videosuz geçti.
Zam izlenmesinin büyük kısmı açıklama günlerinde. Bu betik TÜFE açıklanınca senaryoyu YALNIZ veri dosyalarından
(data/tufe-aylik.json, data/emekli-memur.json) kurar: "<Ay> enflasyonu açıklandı" + emekli zammı (tahmin/kesin)
+ Ocak tablosu. Hesap src/data/zam2027.ts ile AYNI (kalan aylar = son 3 ayın ortalaması; memur = %5 × enflasyon farkı).
Rakam üreten tek yer veri; metin şablon. Seslendirme rakamları yazıyla okur (tr_oku).

Kullanım: python3 scripts/anim/aciklama_karti.py            # üret (render) → son satır "RENDER_OK <slug>"
          python3 scripts/anim/aciklama_karti.py --dry      # yalnız senaryoyu yazdır
Çağıran: scripts/event-short.py (tuik olayında LLM hattı başarısız olursa yedek).
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = "/root/.venvs/parafomo/bin/python"
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
PERIOD = ["2026-07", "2026-08", "2026-09", "2026-10", "2026-11", "2026-12"]   # Ocak 2027 zammının dönemi
TS_H2_2026, TS_H1_2027 = 0.07, 0.05                                          # 8. Dönem Toplu Sözleşme
BIRLER = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
ONLAR = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]


def _uc(n):
    y, o, b = n // 100, (n // 10) % 10, n % 10
    s = ("" if y == 0 else ("yüz" if y == 1 else BIRLER[y] + " yüz"))
    return " ".join(x for x in (s, ONLAR[o], BIRLER[b]) if x)


def tr_oku(n):
    """Tam sayıyı Türkçe okur: 33857 → 'otuz üç bin sekiz yüz elli yedi'."""
    n = int(round(n))
    if n == 0:
        return "sıfır"
    parca = []
    for deger, ad in ((10 ** 6, "milyon"), (1000, "bin"), (1, "")):
        k = n // deger
        n %= deger
        if k == 0:
            continue
        if deger == 1000 and k == 1:
            parca.append("bin")
        else:
            parca.append((_uc(k) + (" " + ad if ad else "")).strip())
    return " ".join(parca)


def tr_yuzde_oku(x):
    """12.86 → 'yüzde on iki virgül seksen altı' · 2.5 → 'yüzde iki virgül elli'."""
    tam, kes = f"{x:.2f}".split(".")
    s = "yüzde " + tr_oku(int(tam))
    if kes != "00":
        s += " virgül " + (("sıfır " + tr_oku(int(kes))) if kes.startswith("0") else tr_oku(int(kes)))
    return s


def nokta(n):
    return f"{int(round(n)):,}".replace(",", ".")


def virgul(x):
    return f"{x:.2f}".replace(".", ",")


def hesap():
    tufe = {m["ay"]: m for m in json.load(open(os.path.join(ROOT, "data", "tufe-aylik.json")))["months"]}
    son = sorted(tufe)[-1]
    bilinen = [p for p in PERIOD if p in tufe]
    if not bilinen or son not in PERIOD:
        sys.exit(f"[kart] son TÜFE ayı {son} Ocak 2027 dönemi dışında — betik güncellenmeli (Temmuz 2027 dönemi)")
    cum = 1.0
    for p in bilinen:
        cum *= 1 + tufe[p]["aylik"] / 100
    son3 = [tufe[k]["aylik"] for k in sorted(tufe)[-3:]]
    varsay = round(sum(son3) / 3, 2)
    kalan = len(PERIOD) - len(bilinen)
    ssk = cum * (1 + varsay / 100) ** kalan - 1
    memur = (1 + max(0.0, (1 + ssk) / (1 + TS_H2_2026) - 1)) * (1 + TS_H1_2027) - 1
    return {"ay": son, "aylik": tufe[son]["aylik"], "yillik": tufe[son]["yillik"], "ssk": ssk, "memur": memur,
            "kesin": kalan == 0, "varsay": varsay, "kalan": kalan, "cum": cum - 1}


def senaryo(h):
    ay_ad = AYLAR[int(h["ay"][5:]) - 1]
    et = "kesin" if h["kesin"] else "tahmini"
    ssk_p, mem_p = h["ssk"] * 100, h["memur"] * 100
    taban = json.load(open(os.path.join(ROOT, "data", "emekli-memur.json")))["enDusukEmekliAyligi"]["tutar"]
    satir = [[nokta(b), nokta(b * (1 + h["ssk"])), nokta(b * (1 + h["memur"]))] for b in range(25000, 55000, 5000)]
    ornek_s, ornek_m = 30000 * (1 + h["ssk"]), 30000 * (1 + h["memur"])
    not_ = ("Temmuz–Aralık 2026 TÜFE (kesin)" if h["kesin"]
            else f"Tahmin: açıklanan aylar + kalan {h['kalan']} ay için aylık %{virgul(h['varsay'])}")
    tablo = {"baslik": f"Ocak 2027 {'zamlı' if h['kesin'] else 'tahmini'} aylık (TL)",
             "sutunlar": ["Bugün", "SSK/Bağ-Kur", "Memur emek."], "satirlar": satir, "vurgu": 1, "kelime": "Örneğin", "not": not_}
    son_satir = ("Bu oran kesinleşti; zamlı aylık Ocak'ta yatar." if h["kesin"]
                 else "Kesin oran Aralık enflasyonuyla Ocak başında belli olur.")
    lines = [
        {"id": "s0", "say": f"{ay_ad} enflasyonu açıklandı: aylık {tr_yuzde_oku(h['aylik'])}.",
         "cap": f"{ay_ad} enflasyonu açıklandı: aylık %{virgul(h['aylik'])}."},
        {"id": "s1", "say": f"Bu yüzden SSK ve Bağ-Kur emekli zammı {et} {tr_yuzde_oku(ssk_p)}.",
         "cap": f"Bu yüzden SSK ve Bağ-Kur emekli zammı {et} %{virgul(ssk_p)}."},
        {"id": "s2", "say": f"Memur emeklisinde {tr_yuzde_oku(mem_p)}.", "cap": f"Memur emeklisinde %{virgul(mem_p)}."},
        {"id": "s3", "say": f"Örneğin otuz bin lira alan SSK emeklisi, yaklaşık {tr_oku(ornek_s)} lira alır. "
                            f"Memur emeklisiyse {tr_oku(ornek_m)}.",
         "cap": f"Örneğin 30.000 TL alan SSK emeklisi, yaklaşık {nokta(ornek_s)} TL alır. Memur emeklisiyse {nokta(ornek_m)} TL."},
        {"id": "s4", "say": "En düşük aylık için ayrı yasal karar gerekir. " + son_satir,
         "cap": "En düşük aylık için ayrı yasal karar gerekir. " + son_satir},
        {"id": "s5", "say": "Senin maaşın tabloda hangi satırda?", "cap": "Senin maaşın tabloda hangi satırda?"},
    ]
    kaynak = "Kaynak: TÜİK TÜFE; 8. Dönem Toplu Sözleşme; parafomo hesabı" + ("" if h["kesin"] else " (tahmin)")
    emk = lambda ifade, y=1085, olcek=0.6, giris="yok": [{"id": "a", "k": "emekli", "ifade": ifade, "x": 540, "y": y, "olcek": olcek, "giris": giris}]
    scenes = [
        {"line": "s0", "etiket": f"{ay_ad} {h['ay'][:4]} · TÜİK", "sayi": {"deger": h["aylik"], "bas": 0, "birim": "%", "kelime": "aylık",
                                                                         "y": 520, "not": f"yıllık %{virgul(h['yillik'])}", "say": True},
         "oyuncular": emk("saskin", giris="zipla"), "kaynak": "Kaynak: TÜİK"},
        {"line": "s1", "etiket": "SSK ve Bağ-Kur", "sayi": {"deger": round(ssk_p, 2), "bas": 0, "birim": "%", "kelime": et if not h["kesin"] else "kesin",
                                                           "y": 520, "not": "Temmuz–Aralık enflasyonu" + ("" if h["kesin"] else " (tahmin)"), "say": True},
         "oyuncular": emk("mutlu"), "kaynak": kaynak},
        {"line": "s2", "etiket": "Memur emeklisi", "sayi": {"deger": round(mem_p, 2), "bas": 0, "birim": "%", "kelime": "Memur", "y": 520,
                                                           "not": "toplu sözleşme %5 + enflasyon farkı", "say": True},
         "oyuncular": emk("normal"), "kaynak": kaynak},
        {"line": "s3", "etiket": "Tablo", "tablo": tablo, "kaynak": kaynak},
        {"line": "s4", "etiket": f"En düşük aylık: {nokta(taban)} TL", "oyuncular": emk("endiseli", y=1000, olcek=0.8)},
        {"line": "s5", "tablo": dict(tablo, hemen=True), "kaynak": kaynak, "soru": True},
    ]
    slug = f"{AYLAR[int(h['ay'][5:]) - 1].lower().replace('ı', 'i').replace('ş', 's')}-enflasyonu-aciklandi-emekli-zammi-ocak-2027-tablosu"
    title = f"{ay_ad} enflasyonu açıklandı: emekli zammı %{virgul(ssk_p)} ({'kesin' if h['kesin'] else 'tahmin'}) Ocak 2027 tablosu"
    desc = (f"TÜİK {ay_ad} {h['ay'][:4]} enflasyonu: aylık %{virgul(h['aylik'])}, yıllık %{virgul(h['yillik'])}. "
            f"Ocak 2027 emekli zammı {et}: SSK ve Bağ-Kur %{virgul(ssk_p)}, memur emeklisi %{virgul(mem_p)}. "
            f"Tablo bugünkü aylığa göre Ocak 2027 tutarını gösterir (ör. 30.000 TL → SSK {nokta(ornek_s)} TL). "
            + ("" if h["kesin"] else f"Kalan {h['kalan']} ay için aylık %{virgul(h['varsay'])} varsayıldı; kesin oran Ocak başında belli olur. ")
            + "\nKaynak: TÜİK TÜFE; 8. Dönem Toplu Sözleşme; parafomo hesabı\nKendi aylığınla hesapla: parafomo.com/emekli-zammi-hesaplama/")
    return {"slug": slug, "title": title, "description": desc,
            "tags": ["emekli zammı 2027", "enflasyon açıklandı", f"{ay_ad.lower()} enflasyonu", "ssk bağkur zammı", "memur emeklisi zammı", "parafomo"],
            "lines": lines,
            "comment": "Senin maaşın tabloda hangi satırda? Kaynak: TÜİK TÜFE, 8. Dönem Toplu Sözleşme. Kendi aylığınla hesapla: parafomo.com/emekli-zammi-hesaplama/",
            "link": "/emekli-zammi-hesaplama/", "format": "para_hikayesi", "style": "isometric", "scene": "generic.js",
            "short": True, "engine": "hikaye", "lead": 0.05, "series": "Para Hikâyeleri", "skin": "iso",
            "data": {"tema": "gece", "kanca": [f"{ay_ad.upper()} ENFLASYONU", "AÇIKLANDI"],
                     "vurgu": ["emekli", "zammı", "Memur", "tablo", et], "scenes": scenes}}


def main():
    h = hesap()
    spec = senaryo(h)
    if "--dry" in sys.argv:
        print(json.dumps({k: spec[k] for k in ("slug", "title", "lines")}, ensure_ascii=False, indent=1))
        return 0
    sp = os.path.join(ROOT, "public", "social", "scenarios", f"{spec['slug']}.anim.json")
    json.dump(spec, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    r = subprocess.run(["nice", "-n", "19", PY, os.path.join(ROOT, "scripts", "anim", "anim_build.py"), sp, "--engine", "hikaye"],
                       cwd=ROOT, capture_output=True, text=True, timeout=3000)
    print(r.stdout[-600:], r.stderr[-400:])
    meta_p = os.path.join(ROOT, "public", "social", f"short-{spec['slug']}.json")
    if r.returncode != 0 or not os.path.exists(meta_p) or json.load(open(meta_p, encoding="utf-8")).get("teknik") != "hikaye":
        print("[kart] render başarısız ya da motor yedeğe düştü")
        return 2
    print(f"RENDER_OK {spec['slug']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
