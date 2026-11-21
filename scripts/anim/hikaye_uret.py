#!/usr/bin/env python3
"""Otomatik "Para hikâyesi" üreticisi (2026-11-17, Kaan: "otomatik bir sistem istiyorum", "senaryolar çok önemli").

Akış: doğrulanmış VERİ PAKETİ (sitenin veri dosyalarından, o anki rakamlarla) → Claude senaryo yazar (senaryo kitabı +
duygu tasarımı kuralları, hikaye motoru şeması) → OTOMATİK KONTROL LİSTESİ (kanca, "Ama", soru, döngü, kelime, yalnız
paketteki rakamlar, geçerli karakter/sahne) → hata varsa düzeltme turu → anim_build (hikaye motoru) → kuyruk + panel.

  /root/.venvs/parafomo/bin/python scripts/anim/hikaye_uret.py [--paket asgari-altin] [--kuru] [--kuyruk]
                                    [--max-bekleyen N] [--sadece-yeni-veri [--yokla]]
    --kuru    yalnız senaryoyu üret ve kontrol et (render yok)
    --kuyruk  render sonrası kuyruğa ekle (kuyruk.py ekle) ve panele senaryo kartı yaz
    --max-bekleyen N   hikâye şeridinde N+ video yayın bekliyorsa LLM'e gitmeden 0 ile çık (resmî veri yeni geldiyse
                       yine üretir: o video bugüne tarihlenip sırayı atlar). kuyruk.py uret 2 verir (denetim video-3).
    --sadece-yeni-veri yalnız resmî veri yeni geldiyse üret (sec() → "yeni veri"); değilse hiçbir şey yapmadan 0.
                       Gündüz event-short.py çağırır: açıklama günü hikâyesi aynı gün 19:00'a yetişsin (video-7).
    --yokla   (--sadece-yeni-veri ile) üretmeden yalnız yokla: 'YENI_VERI {"paket": …, "olay": …}' ya da 'YENI_VERI_YOK'

Link (denetim video-2, 2026-11-18): "link" alanı LLM'e bırakılmaz, paketin doğrulanmış linki yazılır; açıklama ve
sabit yorumdaki parafomo.com/… adresleri sitede açılmıyorsa (scripts/lib/funnel.py) o linke çevrilir; kontrol
listesi geçersiz adres kalırsa senaryoyu reddeder. Geçmiş (hikaye-gecmis.json: paket/aile/olay/başlık) yalnız video
BAŞARIYLA çizildikten sonra yazılır (video-10: render çökünce konu ve "yeni veri" tetiği yanıyordu).
"""
import argparse
import datetime as dt
import json
import os
import re
import signal
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "lib"))
sys.path.insert(0, os.path.join(HERE, "engines"))
import funnel  # noqa: E402
import hikaye_kit  # noqa: E402

PY = "/root/.venvs/parafomo/bin/python"
DATA = os.path.join(ROOT, "data")
GECMIS = "/root/parafomo-data/dash/hikaye-gecmis.json"
PLAN = "/root/parafomo-data/dash/plan.json"
TREND = "/root/parafomo-data/trend/yt-trend.json"   # scripts/learn/yt_trend.py (günlük YouTube trend radarı)
TREND_IG = "/root/parafomo-data/trend/ig-trend.json"   # scripts/learn/ig_trend.py (günlük Instagram radarı)
TAHMIN = re.compile(r"devalüasyon|olası|tahmin|çökecek|çöküş|uçacak|düşecek|yükselecek|patlayacak|olacak mı|kriz geliyor", re.I)


def trend_tazele():
    """YouTube ve Instagram radarları 20 saatten eskiyse yenile (Kaan 2026-11-17: her gün araştırıp video hazırla).
    Instagram radarı YouTube kanallarından yeni hesap keşfettiği için YouTube'dan sonra çalışır. Hata hattı bozmaz."""
    for dosya, betik in ((TREND, "yt_trend.py"), (TREND_IG, "ig_trend.py")):
        try:
            if os.path.exists(dosya) and dt.datetime.now().timestamp() - os.path.getmtime(dosya) < 20 * 3600:
                continue
            subprocess.run([PY, os.path.join(ROOT, "scripts", "learn", betik)], timeout=300, check=False)
        except Exception as e:
            print(f"[hikaye] {betik} atlandı: {e}")
    try:   # biçim radarı: patlayanların kapakları tek sayfada (sabah rutini Pzt/Prş inceler)
        subprocess.run([PY, os.path.join(ROOT, "scripts", "learn", "format_sheet.py")], timeout=180, check=False)
    except Exception as e:
        print(f"[hikaye] format_sheet atlandı: {e}")


def trend_satirlari(n=5):
    """Son radar: önce küçük kanalda patlayanlar, sonra en çok izlenenler (siyasi olanlar zaten ayıklı)."""
    try:
        d = json.load(open(TREND, encoding="utf-8"))
        if dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(d["tarih"]) > dt.timedelta(days=3):
            return []
    except (OSError, ValueError, KeyError):
        return []
    out, gor = [], set()
    for x in d.get("patlayan_kucuk", []) + d.get("en_cok", []):
        if x.get("siyasi") or x["baslik"] in gor:
            continue
        gor.add(x["baslik"])
        if TAHMIN.search(x["baslik"]):   # kur/fiyat tahmini ve kriz kehaneti: markaya aykırı
            continue
        nokta = lambda n: f"{n:,}".replace(",", ".")
        ab = nokta(x["abone"]) if x.get("abone") is not None else "?"
        out.append(f'"{x["baslik"]}" ({nokta(x["izlenme"])} izlenme, {ab} aboneli kanal, {x["sure"]} sn)')
        if len(out) >= n:
            break
    return out
KARAKTER = sorted(hikaye_kit.KARAKTER)
DEKOR = ["simit", "ekmek", "cay", "sepet", "deste"]
IFADE = ["normal", "mutlu", "endiseli", "saskin", "uzgun", "korkmus"]
YASAK = ["peki ya", "inanamayacaksınız", "sonuna kadar izle", "bu videoda", "merhaba", "hadi başlayalım", "abone ol",
         "etiketle", "kaydet", "paylaş", "kesin kazandırır", "hemen al", "hemen sat", "yatırım tavsiyesi"]


AYLAR_TR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def yil_de(y):
    """Yıl + bulunma eki, okunuşa göre: 2024'te, 2026'da, 2027'de."""
    return f"{y}'" + {0: "de", 1: "de", 2: "de", 3: "te", 4: "te", 5: "te", 6: "da", 7: "de", 8: "de", 9: "da"}[y % 10]


def j(p):
    return json.load(open(os.path.join(DATA, p), encoding="utf-8"))


def fmt(n, d=0):
    s = f"{n:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


# ---------------------------------------------------------------- doğrulanmış veri paketleri
def tufe_zincir(bas, son=None):
    m = sorted(j("tufe-aylik.json")["months"], key=lambda x: x["ay"])
    son = son or m[-1]["ay"]
    k = 1.0
    for x in m:
        if bas < x["ay"] <= son:
            k *= 1 + x["aylik"] / 100
    return k, son


def paketler():
    out = []
    tufe = {x["ay"]: x for x in j("tufe-aylik.json")["months"]}
    alt = j("altin-getiri.json")
    gram_yil = {y["year"]: y["gram_tl_end"] for y in alt["yearly"]}
    gram_simdi = alt["gram_tl_now"]
    tarih = alt["updated"][:10]
    gumus_ytd = j("gumus-getiri.json")["ytd"]["return_tl_pct"]
    # "her zaman böyle olmaz" satırı: hikâyenin kendi kahramanından (altın) bir karşı örnek — altının enflasyona yenildiği
    # son yıl (2022: altın %40,5, TÜFE %64,3). Gümüşe atlamak hikâyeyi bölüyordu (2026-11-17, #42). Yoksa gümüş.
    gram_getiri = {y["year"]: y["return_tl_pct"] for y in alt["yearly"]}
    yenik = [y for y in sorted(gram_getiri) if f"{y}-12" in tufe and gram_getiri[y] < tufe[f"{y}-12"]["yillik"]]
    if yenik:
        y = yenik[-1]
        ters = (f"Her yıl böyle olmadı: {yil_de(y)} gram altın %{fmt(gram_getiri[y], 1)} arttı, fiyatlar %{fmt(tufe[f'{y}-12']['yillik'], 1)} "
                f"(Aralık yıllık TÜFE); o yıl altın enflasyona yenildi. Geçmiş, geleceğin garantisi değildir")
    else:
        ters = (f"Her zaman böyle olmaz: gümüş 2026 başından bu yana TL bazında %{fmt(abs(gumus_ytd), 1)} "
                f"{'düştü' if gumus_ytd < 0 else 'yükseldi'} ({tarih}); geçmiş, geleceğin garantisi değildir")
    asg = {g["yil"]: g["net"] for g in j("asgari-ucret.json")["gecmis"]}
    # 1) asgari ücretin gram altın karşılığı
    satir = [f"Ocak {y} net asgari ücret {fmt(asg[y])} TL; {y - 1} yıl sonu gram altın {fmt(gram_yil[y - 1])} TL → {fmt(asg[y] / gram_yil[y - 1], 2)} gram"
             for y in sorted(asg) if (y - 1) in gram_yil]
    son_asg = max(asg)
    satir.append(f"Bugün ({tarih}): net asgari ücret {fmt(asg[son_asg])} TL; gram altın {fmt(gram_simdi, 1)} TL → {fmt(asg[son_asg] / gram_simdi, 2)} gram")
    out.append({"id": "asgari-altin", "aile": "asgari-altin", "olay": str(son_asg), "link": "/altin-kac-gram/",
                "konu": "Asgari ücretin gram altın karşılığı yıllar içinde nasıl değişti",
                "kalip": "dram", "tema": "dram", "veri": satir,
                "kaynak": "Asgari ücret: Resmî Gazete (sitedeki asgari ücret verisi); gram altın: ons × USDTRY (Yahoo), yıl sonu"})
    # 1b) "saatte kaç lira" (YouTube radarı 2026-11-18: "Döner ustası saatte kaç lira alıyor?" 84 bin, küçük kanal).
    # Saat ücreti = aylık / 225 (haftalık 45 saat; Asgari Ücret Yönetmeliği). Yalnız resmî net asgari ücretle.
    yillar_s = [y for y in sorted(asg) if y >= son_asg - 2]
    saat = {y: asg[y] / 225 for y in yillar_s}
    out.append({"id": "asgari-saatlik", "aile": "asgari-saatlik", "olay": str(son_asg), "link": "/asgari-ucret-hesaplama/",
                "konu": "Asgari ücretli saatte kaç lira kazanıyor? Bir saatin, bir dakikanın değeri",
                "kalip": "merak", "tema": "gece",
                "veri": [f"{y} net asgari ücret {fmt(asg[y], 2)} TL → saatte {fmt(saat[y], 2)} TL (aylık / 225 saat)" for y in yillar_s]
                        + [f"{son_asg}: dakikada yaklaşık {fmt(saat[son_asg] / 60, 2)} TL; haftalık 45 saatte {fmt(saat[son_asg] * 45)} TL",
                           "225 saat: haftalık 45 saatlik yasal çalışma süresinden aylık hesap (Asgari Ücret Yönetmeliği)",
                           f"ÖRNEK karakter: asgari ücretle çalışan biri kendi saat ücretini ilk kez hesaplıyor",
                           f"Ocak {son_asg + 1} asgari ücreti henüz açıklanmadı (genelde Aralık sonu); tahmin verme"],
                "kaynak": "Net asgari ücret: Resmî Gazete (sitedeki asgari ücret verisi); saat ücreti = aylık / 225"})
    # 2) yüzlüğün alım gücü (TÜFE)
    for bas in (2021, 2022, 2023):   # 2019 = 1. bölüm (yuzlukten-11-lira-kaldi)
        k, son = tufe_zincir(f"{bas}-12")
        if k <= 1.01:
            continue
        yillik = [f"{y}: %{fmt(tufe[f'{y}-12']['yillik'], 2)}" for y in range(bas + 1, 2026) if f"{y}-12" in tufe]
        out.append({"id": f"yuzluk-{bas}", "aile": "yuzluk", "link": "/enflasyon-hesaplama/",
                    "konu": f"{bas} sonundaki 100 liranın bugünkü alım gücü",
                    "kalip": "merak", "tema": "gece",
                    "veri": [f"{bas} Aralık sonu → {son}: fiyatlar {fmt(k, 2)} katı (TÜFE aylık zincir)",
                             f"{bas} sonunda 100 TL'ye alınan sepet bugün yaklaşık {fmt(100 * k)} TL",
                             f"{bas} sonunun 100 TL'sinin bugünkü alım gücü yaklaşık {fmt(100 / k, 1)} TL",
                             "Aralık ayları yıllık TÜFE: " + ", ".join(yillik)],
                    "kaynak": "TÜİK TÜFE (sitedeki aylık TÜFE verisi)"})
    # 3) emekli zammı senaryosu (zam2027 mantığı)
    period = ["2026-07", "2026-08", "2026-09", "2026-10", "2026-11", "2026-12"]
    bilinen = [p for p in period if p in tufe]
    cum = 1.0
    for p in bilinen:
        cum *= 1 + tufe[p]["aylik"] / 100
    son3 = sorted(tufe.values(), key=lambda x: x["ay"])[-3:]
    varsay = round(sum(x["aylik"] for x in son3) / 3, 2)   # src/data/zam2027.ts ile aynı: ASSUME = toFixed(2)
    kalan = len(period) - len(bilinen)
    ay_ad = {"2026-11": "Kasım (3 Aralık'ta açıklanır)", "2026-12": "Aralık (Ocak başında açıklanır)"}
    bekleyen = [ay_ad.get(x, x) for x in period if x not in bilinen]
    bekleyen_satir = ("Henüz bilinmeyen enflasyon: " + " ve ".join(bekleyen) + "; kesin oran ancak ikisi de açıklanınca belli olur"
                      if bekleyen else "Altı ayın enflasyonu da açıklandı; oran kesinleşti")
    proj = cum * (1 + varsay / 100) ** kalan - 1
    taban = j("emekli-memur.json")["enDusukEmekliAyligi"]["tutar"]
    out.append({"id": "emekli-zam", "aile": "emekli", "olay": bilinen[-1], "link": "/emekli-zammi-hesaplama/",
                "konu": "Ocak 2027 emekli zammı: kesinleşen kısım ve ne kadar olabilir",
                "kalip": "merak", "tema": "alacakaranlik",
                "veri": [f"Temmuz–{['Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık'][len(bilinen)-1]} 2026 birikimli enflasyon (kesin): %{fmt((cum - 1) * 100, 2)}",
                         f"Kalan {kalan} ay için aylık %{fmt(varsay, 2)} varsayımıyla Ocak 2027 SSK/Bağ-Kur zammı tahmini: %{fmt(proj * 100, 2)}",
                         f"En düşük emekli aylığı (Temmuz 2026'dan beri, kanunla): {fmt(taban)} TL",
                         f"Yalnız enflasyon farkıyla en düşük aylık yaklaşık {fmt(taban * (1 + proj))} TL olur (senaryo)",
                         bekleyen_satir,
                         "Refah payı ve seyyanen zam için resmî karar yok (17 Kasım 2026)"],
                "kaynak": "TÜİK TÜFE; Resmî Gazete Temmuz 2026; sitedeki emekli zammı hesaplayıcısı", "siyaset_notu": True})
    # 4) altın mı enflasyon mu (yıl sonu → bugün)
    for bas in (2020, 2022, 2023):
        if bas not in gram_yil:
            continue
        k, son = tufe_zincir(f"{bas}-12")
        a = gram_simdi / gram_yil[bas]
        out.append({"id": f"altin-enflasyon-{bas}", "aile": "altin-enflasyon", "link": "/altin-getiri/",
                    "konu": f"{bas} sonunda altına konan 100 lira enflasyonu yendi mi",
                    "kalip": "vs", "tema": "gece",
                    "veri": [f"{bas} yıl sonu gram altın {fmt(gram_yil[bas])} TL → {tarih} {fmt(gram_simdi, 1)} TL ({fmt(a, 2)} katı)",
                             f"{bas} sonunda altına konan 100 TL bugün yaklaşık {fmt(100 * a)} TL",
                             f"Aynı dönemde fiyatlar {fmt(k, 2)} katı (TÜFE, {son}'e kadar): enflasyona yetişmek için {fmt(100 * k)} TL lazım",
                             ters],
                    "kaynak": "Gram altın: ons × USDTRY (Yahoo); TÜFE: TÜİK"})
    # 4b) "10 yıl önce 10 bin lira X'e koysaydın?" (YouTube radarı 2026-11-21: "10 Yıl Önce 10 Bin Liralık Nvidia Hissesi
    #     Alsaydın?" 120 bin izlenme, 4,6 bin aboneli kanal). Yalnız sitenin getiri verisi (Yahoo aylık kapanış, 10 yıllık dönem).
    #     Repoda 10 yıllık TÜFE serisi yok → enflasyon kıyası YAPILMAZ, rakamlar nominal TL olarak etiketlenir.
    on_yil = []
    for dosya, ad, then_k, now_k in (("altin-getiri.json", "gram altın", "gram_tl_then", "gram_tl_now"),
                                     ("dolar-getiri.json", "dolar", "usdtry_then", "usdtry_now"),
                                     ("euro-getiri.json", "euro", "eurtry_then", "eurtry_now"),
                                     ("bist-getiri.json", "BIST 100", "bist_then", "bist_now"),
                                     ("gumus-getiri.json", "gram gümüş", "gram_tl_then", "gram_tl_now")):
        try:
            p = next(x for x in j(dosya)["periods"] if x.get("years") == 10)
            on_yil.append((ad, p[then_k], p[now_k], p[now_k] / p[then_k]))
        except (OSError, ValueError, KeyError, StopIteration, ZeroDivisionError):
            continue
    if len(on_yil) >= 4:
        on_yil.sort(key=lambda r: -r[3])
        out.append({"id": "on-yil-10-bin", "aile": "on-yil", "link": "/altin-getiri/",
                    "konu": "10 yıl önce 10 bin lirayı altına, dolara, euroya ya da borsaya koysaydın bugün ne olurdu",
                    "kalip": "vs", "tema": "gece",
                    "veri": [f"10 yıl önce {ad}: {fmt(a, 2)} → {int(tarih[8:10])} {AYLAR_TR[int(tarih[5:7]) - 1]} {tarih[:4]}: {fmt(b, 2)} "
                             f"→ 10.000 TL o tarihte yaklaşık {fmt(10000 * k)} TL ({fmt(k, 1)} katı; metinde 'bugün' deme, tarihi söyle)" for ad, a, b, k in on_yil]
                            + [f"Sıralama: " + " > ".join(r[0] for r in on_yil),
                               "Rakamlar nominal TL; aynı 10 yılda fiyatlar da çok arttı (enflasyon bu hesapta yok, 'kazanç' deme, 'TL karşılığı' de)",
                               "ÖRNEK karakter: 10 yıl önce elinde 10 bin lira olan biri bugün hangi seçimin ne ettiğini görüyor",
                               "Geçmiş, geleceğin garantisi değildir; bu bir örnek hesaptır, yatırım tavsiyesi değildir"],
                    "kaynak": "Yahoo Finance aylık kapanış (sitedeki getiri sayfaları); nominal TL"})
    # 5) para kıssası (veri yok: ders + örnek hesap)
    # 6) kredi kartı asgari ödeme tuzağı (resmî azami oran + BDDK asgari ödeme; örnek hesap burada yapılır)
    kk = j("kredi-karti-faiz.json")
    t0 = kk["tl"][0]
    vergi = 1.30   # faize %15 KKDF + %15 BSMV

    def kademe(x):
        return "üstü" if x["ust"] is None else fmt(x["ust"]) + " TL'ye kadar"
    B, ay, toplam, borc0 = 20000.0, 0, 0.0, 20000
    while B > 100 and ay < 600:
        od = B * kk["asgari"]["alt"] / 100
        toplam += od
        B = (B - od) * (1 + t0["akdi"] / 100 * vergi)
        ay += 1
    toplam += B
    ilk_faiz = borc0 * (1 - kk["asgari"]["alt"] / 100) * t0["akdi"] / 100 * vergi
    out.append({"id": "kredi-karti-asgari", "aile": "kredi-karti", "olay": kk["gecerli"], "link": "/kredi-karti-faiz-hesaplama/",
                "konu": "Kredi kartında yalnız asgari ödersen borç kaç ayda biter, kaça mal olur", "kalip": "kissa", "tema": "dram",
                "veri": [f"Kredi kartı TL azami akdi faiz ({kk['gecerli']}'den): limiti {fmt(t0['ust'])} TL'ye kadar kartta aylık %{fmt(t0['akdi'], 2)}; "
                         + "; ".join(f"{kademe(x)} %{fmt(x['akdi'], 2)}" for x in kk["tl"][1:])
                         + f" (gecikme faizi +0,30 puan)",
                         f"Faize %15 KKDF + %15 BSMV eklenir: aylık %{fmt(t0['akdi'], 2)} fiilen %{fmt(t0['akdi'] * vergi, 2)} olur",
                         f"Asgari ödeme: limiti {fmt(kk['asgari']['esik'])} TL altındaki kartta dönem borcunun %{kk['asgari']['alt']}'si, üstünde %{kk['asgari']['ust']}'ı ({kk['asgari']['kaynak']})",
                         f"ÖRNEK HESAP: {fmt(borc0)} TL borç, yeni harcama yok, her ay yalnız asgari ödeme → borç yaklaşık {ay} ayda biter, toplam yaklaşık {fmt(toplam)} TL ödenir ({fmt(toplam - borc0)} TL faiz+vergi)",
                         f"ÖRNEK HESAP: ilk ay asgari ({fmt(borc0 * kk['asgari']['alt'] / 100)} TL) ödenince kalan borca yaklaşık {fmt(ilk_faiz)} TL faiz+vergi işler",
                         "ÖRNEK HESAP: aynı borç dönem sonunda tamamen ödenirse faiz 0 TL",
                         "Bu bir örnektir; bankanın oranı azami oranın altında olabilir"],
                "kaynak": f"TCMB azami kredi kartı faizi; {kk['asgari']['kaynak']}; KKDF/BSMV %15"})
    # 7) kira artış tavanı (12 aylık TÜFE ortalaması)
    kr = j("kira-artis-2026.json")
    ornek_kira = 20000
    out.append({"id": "kira-tavan", "aile": "kira", "olay": kr["guncelAy"], "link": "/kira-artis-orani-hesaplama/",
                "konu": f"{kr['guncelAy']} kira zammı: ev sahibi en fazla ne kadar artırabilir", "kalip": "merak", "tema": "gece",
                "veri": [f"{kr['guncelAy']}'da yenilenen kira sözleşmelerinde yasal artış tavanı %{fmt(kr['guncelOran'], 2)} (12 aylık TÜFE ortalaması, TÜİK)",
                         f"ÖRNEK: {fmt(ornek_kira)} TL kira en fazla {fmt(ornek_kira * (1 + kr['guncelOran'] / 100))} TL olabilir",
                         "Önceki aylar: " + ", ".join(f"{g['ay']} %{fmt(g['oran'], 2)}" for g in kr["gecmis"][1:4]),
                         f"Yıllık enflasyon ({['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'][int(sorted(tufe)[-1][5:])]} 2026): %{fmt(tufe[sorted(tufe)[-1]]['yillik'], 2)}; tavan 12 aylık ORTALAMAya bakar, enflasyon düşerken yıllık orandan yüksek kalır",
                         f"Sonraki tavan {kr['sonrakiAciklama']} tarihinde açıklanır",
                         "Dayanak: Türk Borçlar Kanunu md. 344 (konut ve çatılı iş yeri)"],
                "kaynak": "TÜİK TÜFE 12 aylık ortalama; TBK md. 344"})
    # 8) 5 yıl önce dolar mı altın mı (ve son 1 yılın dönemeci)
    dl = j("dolar-getiri.json")
    dp = {x["label"]: x for x in dl["periods"]}
    ap_ = {x["label"]: x for x in alt["periods"]}
    if "5 yıl" in dp and "5 yıl" in ap_ and "1 yıl" in dp and "1 yıl" in ap_:
        k5, son = tufe_zincir("2021-11")
        out.append({"id": "dolar-altin-5y", "aile": "dolar-altin", "link": "/altin-dolar-borsa/",
                    "konu": "5 yıl önce 100 lirayı dolara mı altına mı koymalıydın", "kalip": "vs", "tema": "gece",
                    "veri": [f"5 yıl önce (Kasım 2021) dolara konan 100 TL bugün yaklaşık {fmt(100 * (1 + dp['5 yıl']['return_tl_pct'] / 100))} TL",
                             f"5 yıl önce gram altına konan 100 TL bugün yaklaşık {fmt(100 * (1 + ap_['5 yıl']['return_tl_pct'] / 100))} TL",
                             f"Kasım 2021 sonu → {son}: fiyatlar {fmt(k5, 2)} katı (TÜFE); alım gücünü korumak için yaklaşık {fmt(100 * k5)} TL gerekirdi",
                             f"Son 1 yıl: dolar %{fmt(dp['1 yıl']['return_tl_pct'], 1)}, gram altın %{fmt(ap_['1 yıl']['return_tl_pct'], 1)} kazandırdı; yıllık enflasyon %{fmt(tufe[sorted(tufe)[-1]]['yillik'], 2)} ({sorted(tufe)[-1]})",
                             "Geçmiş getiri, geleceğin garantisi değildir"],
                    "kaynak": f"Yahoo Finance (USDTRY ve ons×USDTRY, aylık kapanış, {tarih}); TÜİK TÜFE"})
    # 8b) 10 yıl önce alsaydın (2026-11-19 trend: "10 Yıl Önce 10 Bin Liralık … Alsaydın? (2016 → 2026)" 3,9 bin aboneli
    #     kanalda 3 günde 101 bin izlenme). Aynı aile → 5 yıllıkla sırayla döner. TÜFE dosyası 2020-11'den başladığı için
    #     10 yıllık enflasyon satırı YOK (uydurma rakam olmasın).
    bp = {x["label"]: x for x in j("bist-getiri.json")["periods"]}
    if "10 yıl" in dp and "10 yıl" in ap_ and "10 yıl" in bp:
        y10 = int(tarih[:4]) - 10
        out.append({"id": "dolar-altin-10y", "aile": "dolar-altin", "link": "/altin-dolar-borsa/",
                    "konu": f"10 yıl önce ({y10}) 10 bin lirayı dolara, altına ya da borsaya koysaydın", "kalip": "vs", "tema": "gece",
                    "veri": [f"{y10}'da dolara konan 10.000 TL bugün yaklaşık {fmt(10000 * (1 + dp['10 yıl']['return_tl_pct'] / 100))} TL",
                             f"{y10}'da gram altına konan 10.000 TL bugün yaklaşık {fmt(10000 * (1 + ap_['10 yıl']['return_tl_pct'] / 100))} TL",
                             f"{y10}'da BIST 100 endeksine konan 10.000 TL bugün yaklaşık {fmt(10000 * (1 + bp['10 yıl']['return_tl_pct'] / 100))} TL (endeks, temettü hariç)",
                             f"Son 1 yıl: dolar %{fmt(dp['1 yıl']['return_tl_pct'], 1)}, gram altın %{fmt(ap_['1 yıl']['return_tl_pct'], 1)}, BIST 100 %{fmt(bp['1 yıl']['return_tl_pct'], 1)}",
                             "Geçmiş getiri, geleceğin garantisi değildir; bu bir yatırım tavsiyesi değildir"],
                    "kaynak": f"Yahoo Finance (USDTRY, ons×USDTRY, XU100; aylık kapanış, {tarih})"})
    # 9) evde bakım maaşı (sitenin en güçlü arama nişi: "2027 evde bakım maaşı ne kadar olacak", 28 günde 1.313 gösterim)
    #    Formül src/data/zam2027.ts + evde-bakim-maasi.astro ile AYNI: 10.000 × memur aylık katsayısı; Ocak'ta memur zammı kadar artar.
    em_ = j("emekli-memur.json")
    kats = em_["memurKatsayi"]["aylikKatsayi"]
    tutar = round(10000 * kats, 2)
    fark = max(0.0, (1 + proj) / 1.07 - 1)            # TS_H2_2026 = %7
    memur_zam = (1 + fark) * 1.05 - 1                  # TS_H1_2027 = %5
    gecmis_k = [("Temmuz 2024", 0.907796), ("Ocak 2025", 1.012556), ("Temmuz 2025", 1.170211), ("Ocak 2026", 1.387871)]
    out.append({"id": "sosyal-evde-bakim", "aile": "sosyal", "olay": bilinen[-1], "link": "/evde-bakim-maasi/",
                "konu": "Evde bakım maaşı Ocak 2027'de ne kadar olacak", "kalip": "merak", "tema": "alacakaranlik",
                "veri": [f"Evde bakım maaşı Temmuz–Aralık 2026: {fmt(tutar, 2)} TL (10.000 × memur aylık katsayısı {str(kats).replace('.', ',')})",
                         f"Ocak 2027 tahmini: yaklaşık {fmt(tutar * (1 + memur_zam))} TL (memur zammı tahmini %{fmt(memur_zam * 100, 2)})",
                         f"Memur zammı tahmini = %5 toplu sözleşme × enflasyon farkı %{fmt(fark * 100, 2)} (6 aylık enflasyon tahmini %{fmt(proj * 100, 2)}, %7'yi aşan kısım)",
                         "Geçmiş: " + " → ".join(f"{a} {fmt(10000 * k)} TL" for a, k in gecmis_k) + f" → Temmuz 2026 {fmt(tutar)} TL",
                         bekleyen_satir,
                         "Kesin tutar Ocak başında memur katsayısı ilan edilince belli olur",
                         "Şartlar ve gelir sınırı sitedeki evde bakım maaşı sayfasında"],
                "kaynak": "2828 s. Kanun ek md. 7; HMB memur katsayı genelgeleri; TÜİK TÜFE; 2027 1. yarı toplu sözleşme %5"})
    # 10) "Aynı maaşı alıyoruz…" (Kaan'ın bulduğu tür, 1,46 M izlenme): aynı asgari ücret, biri nakit biri altın. ÖRNEK hesap,
    #     veriden: 2024'ten başlar (2023'te Temmuz ara zammı yıllık veride yok); her yılın birikimi o yılın sonunda altına çevrilir.
    yil_simdi, ay_simdi = int(tarih[:4]), int(tarih[5:7])
    yillar = list(range(2024, yil_simdi + 1))
    if all(y in asg for y in yillar) and all(y in gram_yil for y in yillar[:-1]):
        nakit, gram, satirlar = 0.0, 0.0, []
        for y in yillar:
            ay_say = 12 if y < yil_simdi else ay_simdi
            bir = ay_say * 0.10 * asg[y]
            fiyat = gram_yil[y] if y < yil_simdi else gram_simdi
            nakit += bir; gram += bir / fiyat
            satirlar.append(f"{y}: {ay_say} ay × {fmt(asg[y] * 0.10)} TL = {fmt(bir)} TL birikim, {'yıl sonu' if y < yil_simdi else 'bugünkü'} gram altın {fmt(fiyat)} TL")
        deger = gram * gram_simdi
        toplam_ay = sum(12 if y < yil_simdi else ay_simdi for y in yillar)
        out.append({"id": "ayni-maas-altin", "aile": "ayni-maas", "link": "/altin-getiri/",
                    "konu": "Aynı maaşı alan iki kişi: biri birikimini nakit tuttu, diğeri altına çevirdi", "kalip": "vs", "tema": "gece",
                    "veri": ["Net asgari ücret: " + ", ".join(f"{yil_de(y)} {fmt(asg[y])} TL" for y in yillar) + " (Resmî Gazete)",
                             f"ÖRNEK: iki kişi Ocak 2024'ten beri her ay maaşının %10'unu kenara koyuyor ({toplam_ay} ay)",
                             *satirlar,
                             f"Nakit tutan: toplam yaklaşık {fmt(nakit)} TL",
                             f"Her yıl sonunda altına çeviren: toplam yaklaşık {fmt(gram, 1)} gram, {int(tarih[8:10])} {AYLAR_TR[ay_simdi - 1]} fiyatıyla yaklaşık {fmt(deger)} TL "
                             "(video günler sonra yayınlanır, altın oynar: metinde 'bugün' deme, bu tarihi söyle)",
                             f"Aradaki fark yaklaşık {fmt(deger - nakit)} TL",
                             f"Farkın büyük kısmı 2025'ten: gram altın 2025'te {fmt(gram_yil[2024])} TL'den {fmt(gram_yil[2025])} TL'ye çıktı ({fmt(gram_yil[2025] / gram_yil[2024], 2)} katı)",
                             ters],
                    "kaynak": "Asgari ücret: Resmî Gazete; gram altın: ons × USDTRY (Yahoo), yıl sonu; ÖRNEK hesap, yatırım tavsiyesi değildir"})
    out.append({"id": "kissa-bilesik", "aile": "kissa", "link": "",
                "konu": "Bileşik faizin gücü: iki kardeşin kumbarası (kıssa)", "kalip": "kissa", "tema": "alacakaranlik",
                "veri": ["ÖRNEK HESAP: her ay 1.000 TL, aylık %3 getiri: 12 ayda yaklaşık 14.192 TL (12.000 TL yatırım)",
                         "ÖRNEK HESAP: aynı düzen 24 ayda yaklaşık 34.426 TL (24.000 TL yatırım)",
                         "Bu bir örnektir; gerçek getiri ürün ve döneme göre değişir"],
                "kaynak": "Örnek hesap (aylık bileşik); gerçek ürün getirisi değildir"})
    return out


# ---------------------------------------------------------------- senaryo isteği
SEMA = """{
 "slug": "kucuk-harf-tireli-baslik",
 "title": "YouTube başlığı (Türkçe arama ifadesi + merak, en çok 80 karakter, sonuna #Shorts EKLEME)",
 "description": "2-4 cümle açıklama + 'Kaynak: …' satırı + 'Kendi hesabını yap: parafomo.com/…' (varsa)",
 "tags": ["5-7 Türkçe etiket"],
 "lines": [{"id": "s0", "say": "seslendirme metni (rakamlar okunacağı gibi: 'yüzde 5', '23 bin 552')", "cap": "altyazı (rakamlar: '%5', '23.552')"}],
 "data": {
  "tema": "gece | alacakaranlik | dram",
  "kanca": ["1. SATIR", "2. SATIR (toplam en çok 5 kelime, BÜYÜK HARF)"],
  "vurgu": ["altyazıda renklenecek 6-10 anahtar kelime (rakamlar zaten renklenir)"],
  "scenes": [ {"line": "s0", "...": "her satıra bir sahne"} ]
 },
 "comment": "Sabit yorum: 1 açık uçlu soru + kaynak + varsa site linki (etiketle/kaydet/paylaş YOK)",
 "link": "/varsa-ilgili-sayfa/"
}"""

SAHNE = f"""Sahne alanları (hepsi isteğe bağlı, sahne başına 1-3 öğe; sahne = satır):
- "oyuncular": [{{"id": "a", "k": KARAKTER, "ifade": IFADE, "x": 200-880, "y": 800-1100, "olcek": 0.5-1.0, "giris": "yok|zipla|sol|sag|alt",
   "olaylar": [{{"kelime": "satırdaki bir kelime", "ifade": IFADE, "eylem": "kucul|erit|titre|zipla|git", "deger": 0.4-0.9}}]}}]
- "baslik": ["üst başlık 1. satır", "2. satır"] (kısa)
- "etiket": "küçük hap etiket (yıl, 'Örnek', 'Bugün' gibi)"
- "sayi": {{"deger": sayı, "bas": başlangıç (isteğe bağlı), "birim": "₺|%|gram", "kelime": "sayının geçtiği kelime", "y": 450-650, "not": "kısa açıklama", "say": true}}
- "vs": {{"sol": {{"k": KARAKTER, "etiket": "…", "deger": "…"}}, "sag": {{…}}}}
- "cubuk": {{"a": {{"etiket": "…", "deger": sayı}}, "b": {{"etiket": "…", "deger": sayı}}, "birim": "…", "not": "…"}}
- "liste": {{"sol": {{"baslik": "AYŞE", "kalemler": ["Aynı maaş", "~Altın"]}}, "sag": {{"baslik": "MERT", "kalemler": ["…"]}}, "kelime": "çizginin geldiği kelime", "y": 300}}
   (iki kişiyi karşılaştıran defter listesi; sütun başına 2-5 kısa kalem, her biri en çok 14 harf; "~" ile başlayan kalemin üstü çizilir;
   iki karakter isteğe bağlı, liste altında y 1100-1150, olcek 0.55; vs yerine kalem kalem farkı anlatırken kullan)
- "dekor": [{{"d": DEKOR, "adet": 1-24, "kalan": sayı (isteğe bağlı, kelimede soluklaşır), "kelime": "…", "x": 540, "y": 1000-1150, "olcek": 0.3-2}}]
- "kaynak": "Kaynak: … (rakamlı sahnelerde ZORUNLU)"
- "soru": true (yalnız soru satırında: yorum balonu)
KARAKTER = {KARAKTER}  (yuzluk = gözlü 100 TL, dolar = yeşil dolar, yuzde = % karakteri, altin = altın para, zarf = maaş zarfı,
ev = kiralık ev, enflasyon = aç mor canavar (kötü karakter), kumbara = kumbara,
kadin = genç çalışan kadın, erkek = genç çalışan erkek, emekli = emekli amca (gözlüklü), evsahibi = ev sahibi / patron (takım elbise))
IFADE = {IFADE} · DEKOR = {DEKOR}"""

KURALLAR = """SENARYO KİTABI (uymazsan senaryo reddedilir):
1. İlk satır (s0) SORU DEĞİL, İDDİA: en fazla 9 kelime, tek ve belirli merak boşluğu, sessizde de anlaşılır. İlk sahnede karakter zaten olayın içinde.
2. Kanca kartı (data.kanca) en çok 5 kelime ve s0 ile AYNI vaadi verir.
3. İlk "Ama…" s1 ya da s2'de. Her geçiş "ama" ya da "bu yüzden" mantığında; "ve sonra" yok.
4. Kancanın cevabı videonun ortasında; %65-75'te ikinci dönemeç ("Asıl şaşırtıcı olan…"); cevaptan sonra en çok 2 satır.
5. Rakam: YALNIZ aşağıdaki VERİ PAKETİNDEKİ rakamlar; cümle başına en çok 1, video başına 3-5; seste yuvarlanabilir ("yaklaşık"); örnekse "örnek" de.
   Altyazıda rakamı rakamla yaz ("22.843 TL", "%12,86"); "~" işareti KULLANMA, "yaklaşık" yaz.
6. 8-11 satır, toplam 75-105 kelime; cümleler ortalama 5-8, hiçbiri 12 kelimeden uzun. Doğal konuşma Türkçesi, "sen" dili; fiil sonda, sürpriz cümle sonunda.
7. Duygu yolu: merak → (şaşkınlık / haksızlık / nostalji) → KONTROL. Hüzün ya da korkuyla bitme; son 2 satır izleyiciye kontrol hissi verir.
8. Sondan bir önceki satır tek, açık uçlu, hikâyeye bağlı bir SORU (yorum için). "Etiketle, kaydet, paylaş, abone ol" YOK.
9. Son satır ilk satıra bağlanır (döngü): ilk satırdaki anahtar ifadeyi tekrar eder ya da ona akar.
10. Yatırım tavsiyesi YOK (al/sat, hedef fiyat, tahmin yok); karşılaştırmada "geçmiş, geleceğin garantisi değil". Siyaset YOK: kişi, parti, hükümet, kurum yorumu yok; yalnız rakam ve tarih.
11. Kalıp ifadeler yasak: "peki ya", "inanamayacaksınız", "bu videoda", "merhaba", "hadi başlayalım", "sonuna kadar izle".
12. Rakamlı her sahnede "kaynak" alanı; örnek hesaplarda "etiket": "Örnek".
13. Uygunsa hikâyeyi İNSANLARLA kur (kadin, erkek, emekli, evsahibi): gündelik bir para ikilemi (aynı maaşı alan iki
    iş arkadaşı, kiracı ve ev sahibi, emekli). Para karakterleri (yuzluk, altin, zarf…) o zaman sahne nesnesi ya da
    kötü karakter (enflasyon) olur. Kaynak: 2026 sonbaharında küçük TR kanallarında 1+ milyon izlenen 2D para
    hikâyelerinin hepsi insan merkezli.
14. Başlıkta bir RAKAM olsun ve kalıplardan biri: "[X] ne kadar olacak/kazanır?", "Aynı maaş, farklı son: …",
    "[X]: 2020 vs bugün", "[X] neden hep [Y]? Cevap …". Soru satırı izleyiciyi gruba koysun ("Sen hangisisin: …?")."""


def ig_satirlari(n=5):
    """Instagram radarı: takip edilen para hesaplarında hesabın ortancasının çok üstüne çıkan Reels (kanca cümlesiyle)."""
    try:
        d = json.load(open(TREND_IG, encoding="utf-8"))
        if dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(d["tarih"]) > dt.timedelta(days=3):
            return []
    except (OSError, ValueError, KeyError):
        return []
    nokta = lambda x: f"{x:,}".replace(",", ".")
    return [f'Instagram @{x["hesap"]} ({nokta(x["takipci"] or 0)} takipçi): "{x["kanca"]}" ({nokta(x["izlenme"])} izlenme, '
            f'hesabın ortancasının {str(x["kat"]).replace(".", ",")} katı)' for x in d.get("patlayan", [])[:n] if not TAHMIN.search(x["kanca"])]


def trend_blok():
    t = trend_satirlari() + ig_satirlari()
    if not t:
        return ""
    return ("\nBU HAFTA TÜRKÇE PARA VİDEOLARINDA PATLAYANLAR (YouTube Shorts ve Instagram Reels radarı, son 7-10 gün). "
            "Yalnız AÇI ve BAŞLIK KALIBI ilhamı: "
            "başlıklarını, rakamlarını, iddialarını ve karakterlerini KOPYALAMA; tahmin ve siyaset yok. Kendi VERİ PAKETİNLE "
            "uygun düşen bir açı (ikilem, merak, o zaman/şimdi, kim kazanır) seç:\n- " + "\n- ".join(t) + "\n")


def istem(p, gecmis_basliklar, duzeltme=""):
    return f"""Sen Parafomo'nun "Para hikâyeleri" senaristisin: Türkçe, 35-50 saniyelik, düz vektör karakterli animasyon Shorts/Reels.
Kaan'ın beğendiği tarz: yüzü olan karakter, ilk saniyede merak, rakamlar çizimle, izleyiciye soruyla biten kısa hikâye.

KONU: {p['konu']}
KALIP: {p['kalip']} (merak = mekanizma açıklayıcı; dram = para karakteri birinci ağızdan konuşur; vs = kim kazanır;
ozaman = o zaman/şimdi; efsane = yanlış inanışı yıkar; kissa = kısa ders hikâyesi, karakterlerle)
TEMA: {p['tema']}

VERİ PAKETİ (doğrulanmış; BAŞKA RAKAM KULLANMA):
- """ + "\n- ".join(p["veri"]) + f"""
Kaynak: {p['kaynak']}
Sitedeki ilgili sayfa (açıklama ve "link" alanında kullan): {('parafomo.com' + p['link']) if p.get('link') else 'yok'}
{trend_blok()}
{KURALLAR}

{SAHNE}

Son bölümlerin başlıkları (aynı olay ve sonu tekrarlama): {"; ".join(gecmis_basliklar[-6:]) or "yok"}
{duzeltme}
ÇIKTI: YALNIZ geçerli JSON (açıklama, kod bloğu işareti yok), şu şemada:
{SEMA}"""


# ---------------------------------------------------------------- otomatik kontrol listesi
def _norm(s):
    s = s.replace("İ", "i").replace("I", "ı").lower()
    return unicodedata.normalize("NFC", s)


def sayilar(metin):
    """Metindeki rakam grupları (binlik nokta/ondalık virgül normalize)."""
    out = set()
    for m in re.findall(r"\d[\d.,]*", metin):
        m = m.strip(".,")
        if not m:
            continue
        out.add(m.replace(".", "").replace(",", "."))
    return out


def kontrol(spec, p):
    hata = []
    L = spec.get("lines") or []
    if not 8 <= len(L) <= 12:
        hata.append(f"satır sayısı {len(L)} (8-11 olmalı)")
    toplam = sum(len(l.get("say", "").split()) for l in L)
    if not 70 <= toplam <= 115:
        hata.append(f"toplam {toplam} kelime (75-105 olmalı)")
    for l in L:
        for cumle in re.split(r"[.!?]", l.get("say", "")):
            if len(cumle.split()) > 13:
                hata.append(f"uzun cümle ({len(cumle.split())} kelime): {cumle.strip()[:60]}")
    if L:
        s0 = L[0].get("say", "")
        if "?" in s0:
            hata.append("ilk satır soru olmamalı (iddia)")
        if len(s0.split()) > 10:
            hata.append(f"ilk satır {len(s0.split())} kelime (en çok 9)")
        if not any(_norm(l.get("say", "")).startswith("ama") for l in L[1:4]):
            hata.append("ilk 'Ama…' satırı s1-s3 arasında olmalı")
        if not any("?" in l.get("say", "") for l in L[-3:]):
            hata.append("son 3 satırda açık uçlu soru yok")
        ilk = {w for w in re.findall(r"\w+", _norm(s0)) if len(w) > 3}
        son = {w for w in re.findall(r"\w+", _norm(L[-1].get("say", ""))) if len(w) > 3}
        if len(ilk & son) < 1:
            hata.append("son satır ilk satıra bağlanmıyor (döngü)")
    if any("~" in l.get("cap", "") for l in L):
        hata.append("altyazıda '~' var: 'yaklaşık' yaz")
    tum = " ".join(l.get("say", "") + " " + l.get("cap", "") for l in L)
    for y in YASAK:
        if y in _norm(tum):
            hata.append(f"yasak ifade: {y}")
    izinli = set()
    for v in p["veri"] + [p["konu"]]:
        izinli |= sayilar(v)
    for n in sayilar(tum):
        if n in izinli:
            continue
        try:
            f = float(n)
        except ValueError:
            continue
        if f <= 12 or 1990 <= f <= 2035:   # küçük sayılar ve yıllar serbest
            continue
        yakin = any(abs(f - float(x)) / max(abs(float(x)), 1) < 0.03 for x in izinli if re.fullmatch(r"[\d.]+", x))
        if not yakin:
            hata.append(f"pakette olmayan rakam: {n}")
    d = spec.get("data") or {}
    if d.get("tema") not in ("gece", "alacakaranlik", "dram"):
        hata.append("tema geçersiz")
    k = d.get("kanca") or []
    if not k or sum(len(x.split()) for x in k) > 6:
        hata.append("kanca kartı boş ya da 6 kelimeden uzun")
    ids = {l.get("id") for l in L}
    for sc in d.get("scenes") or []:
        if sc.get("line") not in ids:
            hata.append(f"sahne satırı yok: {sc.get('line')}")
        for o in sc.get("oyuncular", []):
            if o.get("k") not in KARAKTER:
                hata.append(f"geçersiz karakter: {o.get('k')}")
            if o.get("ifade", "normal") not in IFADE:
                hata.append(f"geçersiz ifade: {o.get('ifade')}")
        for t in ("sol", "sag"):
            if sc.get("vs") and sc["vs"].get(t, {}).get("k") not in KARAKTER:
                hata.append("vs karakteri geçersiz")
        for dk in sc.get("dekor", []):
            if dk.get("d") not in DEKOR:
                hata.append(f"geçersiz dekor: {dk.get('d')}")
    if not d.get("scenes"):
        hata.append("sahne yok")
    for alan in ("description", "comment", "link"):   # sitede açılmayan adres (#41 '/asgari-ucret/' 404 dersi)
        metin = spec.get(alan) or ""
        kotu = funnel.gecersiz_linkler(metin, ROOT) if alan != "link" else \
            ([metin] if metin and funnel.sayfa_yolu(metin, ROOT) is None else [])
        for x in kotu:
            hata.append(f"{alan}: sitede olmayan adres {x} (yalnız VERİ PAKETİNDEKİ sayfayı kullan)")
    return hata


def link_duzelt(spec, p):
    """LLM'in yazdığı link/adresleri DETERMİNİSTİK düzelt: 'link' = paketin doğrulanmış linki (paket linksizse LLM'inki
    yalnız sitede açılıyorsa kalır); açıklama/yorumdaki geçersiz parafomo.com/… adresleri o linke (yoksa konu aracına)
    çevrilir. Böylece düzeltme turu (LLM çağrısı) harcanmaz."""
    pl = p.get("link") or ""
    if pl and funnel.sayfa_yolu(pl, ROOT):
        spec["link"] = pl
    elif spec.get("link") and not funnel.sayfa_yolu(spec["link"], ROOT):
        print(f"[hikaye] link sitede açılmıyor, çıkarıldı: {spec['link']}")
        spec.pop("link", None)
    yedek = funnel.tam_url(funnel.sayfa_yolu(spec["link"], ROOT)) if spec.get("link") else \
        funnel.tool_url_for(spec.get("slug", ""), spec.get("title", ""), ROOT)
    for alan in ("description", "comment"):
        if isinstance(spec.get(alan), str):
            spec[alan], degisen = funnel.linkleri_duzelt(spec[alan], yedek, ROOT)
            if degisen:
                print(f"[hikaye] {alan}: geçersiz adres düzeltildi {', '.join(degisen)} → {yedek}")
    return spec


def hikaye_bekleyen():
    """Hikâye şeridinde yayın bekleyen video sayısı (kuyruk.py ile aynı sayım; KUYRUK_DATA'ya uyar)."""
    try:
        import kuyruk
        return kuyruk.bekleyen(kuyruk.load(), hikaye=True)
    except Exception as ex:
        print(f"[hikaye] kuyruk okunamadı ({type(ex).__name__}: {ex}) — tavan uygulanmadı")
        return 0


def calistir(cmd, timeout):
    """Render alt sürecini kendi süreç grubunda çalıştır; zaman aşımında BÜTÜN grubu sonlandır (anim_build/node
    çocukları öksüz kalıp render kilidini tutmasın — denetim video-10). subprocess.TimeoutExpired yükseltir."""
    pr = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        out, err = pr.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        for sig, bekle in ((signal.SIGTERM, 15), (signal.SIGKILL, 30)):
            try:
                os.killpg(pr.pid, sig)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                pr.communicate(timeout=bekle)
                break
            except subprocess.TimeoutExpired:
                continue
        raise
    return subprocess.CompletedProcess(cmd, pr.returncode, out, err)


ONCELIK = ["altin-enflasyon", "sosyal", "ayni-maas", "kredi-karti", "kira", "dolar-altin", "kissa", "asgari-altin", "yuzluk", "emekli"]


def sec(P, gecmis):
    """Konu seçimi: (1) resmî verisi değişmiş aile (olay: yeni TÜFE ayı, yeni kira tavanı, yeni asgari ücret, yeni kart faizi)
    öne geçer; (2) yoksa en uzun süredir kullanılmayan AİLE (aynı ailenin yıl varyantları art arda gelmesin);
    (3) aile içinde en uzun süredir kullanılmayan paket."""
    aile_t, paket_t, olay = gecmis.get("aileler", {}), gecmis.get("paketler", {}), gecmis.get("olay", {})
    tetik = [p for p in P if p.get("olay") and olay.get(p["id"]) not in (None, p["olay"])]
    if tetik:
        return sorted(tetik, key=lambda p: ONCELIK.index(p["aile"]) if p["aile"] in ONCELIK else 99)[0], "yeni veri"
    aileler = sorted({p["aile"] for p in P}, key=lambda a: (aile_t.get(a, ""), ONCELIK.index(a) if a in ONCELIK else 99))
    secilen = aileler[0]
    return sorted([p for p in P if p["aile"] == secilen], key=lambda p: paket_t.get(p["id"], ""))[0], "sıra"


def yerlesim_duzelt(spec):
    """Render öncesi DETERMİNİSTİK yerleşim (hf check 'text_occluded' dersi, 2026-11-17): karakter yazılarının (100, %, MAAŞ)
    üstüne opak bir şey binmesin; karakter/dekor başlığa, sayıya, soru balonuna, altyazıya taşmasın. LLM'e bırakılmaz.
    Çizim sırası (hikaye.py): başlık → hap → dekor → oyuncular → sayı → vs → çubuk → kaynak → soru balonu."""
    d = spec["data"]
    for i, sc in enumerate(d.get("scenes", [])):
        if i == 0 and d.get("kanca"):   # açılışta kanca kartı başlık yerinde; ikisi üst üste biner (hf content_overlap, 2026-11-18)
            sc.pop("baslik", None)
        if sc.get("cubuk") and sc.get("vs"):
            sc.pop("vs")
        if sc.get("tablo"):   # tablo kartı tek başına (2026-11-17)
            for k in ("oyuncular", "dekor", "sayi", "soru", "vs", "cubuk", "baslik"):
                sc.pop(k, None)
            continue
        if sc.get("cubuk") or sc.get("vs"):   # grafik/vs sahnesi kendi başına (vs kendi karakterlerini çizer)
            for k in ("oyuncular", "dekor", "sayi", "soru"):
                sc.pop(k, None)
            continue
        if sc.get("sayi"):
            sc["sayi"]["y"] = min(max(int(sc["sayi"].get("y", 470)), 460), 520)
        soru = bool(sc.get("soru"))
        ust = 470 if (sc.get("baslik") or (i == 0 and d.get("kanca"))) else 250
        if sc.get("sayi"):
            ust = max(ust, 870)
        oy = (sc.get("oyuncular") or [])[:3]
        if soru and len(oy) == 3:
            oy = [oy[0], oy[2]]
        n = len(oy)
        if n >= 3 or soru:   # 3 karakterde ya da soru balonunda dekora yer yok (karakterin arkasında kalıyordu)
            sc.pop("dekor", None)
        yan = n == 1 and bool(sc.get("dekor"))   # tek karakter + dekor: yan yana (dekor solda, karakter sağda), üst üste değil
        alt = 1050 if (soru and n <= 1) else 1300
        if n:
            serit = {1: [760 if yan else 540], 2: [300, 780] if soru else [320, 760], 3: [220, 540, 860]}[n]
            en = {1: 400 if yan else 520, 2: 330 if soru else 400, 3: 300}[n]
            for k, o in enumerate(oy):
                size = max(180.0, min(600 * float(o.get("olcek", 0.8)), en, alt - ust))
                x = 540.0 if (n == 1 and soru) else (serit[k] if (n > 1 or yan) else min(max(float(o.get("x", 540)), 300.0), 780.0))
                y = min(max(float(o.get("y", 1000)), ust + size / 2), alt - size / 2)
                o.update({"x": round(x), "y": round(y), "olcek": round(size / 600, 3)})
                for ev in o.get("olaylar", []):   # 'git' başka karakterin/öğenin üstüne gitmesin: kendi şeridinde kalır
                    if "x" in ev or "y" in ev:
                        ev["x"] = round(x) if (n > 1 or soru or yan) else round(min(max(float(ev.get("x", x)), 300.0), 780.0))
                        ev["y"] = round(min(max(float(ev.get("y", y)), ust + size / 2), alt - size / 2))
            sc["oyuncular"] = oy
        else:
            sc.pop("oyuncular", None)
        # dekor ızgarası başlığın altında, altyazının üstünde; genişlik: yan yana sahnede sol yarı, 2 karakterde aradaki boşluk
        gen = 400 if yan else (200 if n == 2 else 1000)
        for dk in sc.get("dekor", []):
            adet = max(1, int(dk.get("adet", 1)))
            sut = min(adet, int(dk.get("sutun", 6)))
            satir = (adet + sut - 1) // sut
            boy = min(200 * float(dk.get("olcek", 0.5)), (1300 - ust) / (satir * 1.08), gen / (sut * 1.08))
            yuk = satir * boy * 1.08
            dk["olcek"] = round(boy / 200, 3)
            dk["y"] = round(min(max(float(dk.get("y", 1150)), ust + yuk / 2), 1300 - yuk / 2))
            dk["x"] = 300 if yan else 540
    return spec


def json_ayikla(t):
    t = t.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    i, k = t.find("{"), t.rfind("}")
    return json.loads(t[i:k + 1])


def slugla(s):
    s = _norm(s)
    tr = str.maketrans("çğıöşüâî", "cgiosuai")
    s = re.sub(r"[^a-z0-9]+", "-", s.translate(tr)).strip("-")
    return s[:60].strip("-")


def main():
    from llm import call
    ap = argparse.ArgumentParser()
    ap.add_argument("--paket", default="")
    ap.add_argument("--kuru", action="store_true")
    ap.add_argument("--kuyruk", action="store_true")
    ap.add_argument("--model", default="opus")
    ap.add_argument("--max-bekleyen", type=int, default=0)
    ap.add_argument("--sadece-yeni-veri", action="store_true")
    ap.add_argument("--yokla", action="store_true")
    a = ap.parse_args()
    a.sadece_yeni_veri = a.sadece_yeni_veri or a.yokla
    gecmis = {}
    try:
        gecmis = json.load(open(GECMIS, encoding="utf-8"))
    except (OSError, ValueError):
        pass
    if not a.sadece_yeni_veri:   # gündüz yoklamasında radarlar yenilenmez (ucuz kalsın); üretilecekse aşağıda
        trend_tazele()
    P = paketler()
    if a.paket:
        P = [p for p in P if p["id"] == a.paket] or sys.exit(f"paket yok: {a.paket}")
    p, neden = sec(P, gecmis)
    if a.yokla:   # event-short.py: ağ/LLM yok, yalnız karar satırı
        print("YENI_VERI " + json.dumps({"paket": p["id"], "olay": p.get("olay", "")}, ensure_ascii=False)
              if neden == "yeni veri" else "YENI_VERI_YOK")
        return 0
    if a.sadece_yeni_veri and neden != "yeni veri":
        print("[hikaye] yeni resmî veri yok — üretim yok"); return 0
    if a.max_bekleyen and neden != "yeni veri":
        n = hikaye_bekleyen()
        if n >= a.max_bekleyen:
            print(f"[hikaye] hikâye şeridinde {n} video yayın bekliyor (tavan {a.max_bekleyen}) — bu gece yeni hikâye yok"
                  f" (sıradaki olurdu: {p['id']})")
            return 0
    if a.sadece_yeni_veri:
        trend_tazele()
    print(f"[hikaye] paket: {p['id']} ({neden}) · {p['konu']} · kalıp {p['kalip']}")
    duzeltme, spec, hatalar = "", None, ["başlamadı"]
    for tur in range(3):
        ok, text, kind = call(istem(p, gecmis.get("basliklar", []), duzeltme), model=a.model, effort="medium",
                              timeout=600, tag="hikaye")
        if not ok:
            sys.exit(f"[hikaye] LLM çağrısı başarısız: {kind}")
        try:
            spec = json_ayikla(text)
        except Exception as ex:
            duzeltme = f"ÖNCEKİ ÇIKTI GEÇERSİZ JSON ({ex}). Yalnız JSON yaz."
            continue
        link_duzelt(spec, p)
        hatalar = kontrol(spec, p)
        print(f"[hikaye] tur {tur + 1}: {len(hatalar)} sorun", "; ".join(hatalar[:6]))
        if not hatalar:
            break
        duzeltme = ("ÖNCEKİ SENARYO KONTROL LİSTESİNDEN GEÇEMEDİ. Şunları düzelt, gerisini koru:\n- " + "\n- ".join(hatalar) +
                    "\nÖnceki senaryo:\n" + json.dumps(spec, ensure_ascii=False)[:6000])
    if hatalar:
        sys.exit(f"[hikaye] kontrol listesi geçilemedi: {hatalar}")
    slug = slugla(spec.get("slug") or spec["title"])
    spec.update({"slug": slug, "format": "para_hikayesi", "style": "isometric", "scene": "generic.js", "short": True,
                 "engine": "hikaye", "lead": 0.05, "series": "Para Hikâyeleri", "skin": "iso"})
    spec["title"] = re.sub(r"\s*#shorts\s*$", "", spec["title"], flags=re.I)[:85]
    yerlesim_duzelt(spec)
    sp = os.path.join(ROOT, "public", "social", "scenarios", f"{slug}.anim.json")
    json.dump(spec, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[hikaye] senaryo: {sp}")
    if a.kuru:
        print(json.dumps(spec["lines"], ensure_ascii=False, indent=1)); return 0
    mp4 = os.path.join(ROOT, "public", "social", f"short-{slug}.mp4")
    for deneme in range(2):
        try:
            r = calistir(["nice", "-n", "19", PY, os.path.join(HERE, "anim_build.py"), sp, "--engine", "hikaye",
                           "--yedeksiz"], 3600)   # izometriğe sessizce düşmesin: hata aşağıdaki kurtarmaya gelsin (2026-11-18/19 gece)
        except subprocess.TimeoutExpired:
            sys.exit("[hikaye] render 3600 sn'de bitmedi (süreç grubu sonlandırıldı) — geçmiş yazılmadı, konu yine sırada")
        if r.returncode == 0 and os.path.exists(mp4):
            break
        hata = (r.stderr or "") + (r.stdout or "")
        sahne = sorted({int(x) for x in re.findall(r"#s(\d+)", hata)})
        if deneme == 0 and "text_occluded" in hata and sahne:   # tek kurtarma: örten sahnelerden karakter/dekoru çıkar
            for i in sahne:
                if i < len(spec["data"]["scenes"]):
                    for k in ("oyuncular", "dekor", "soru"):
                        spec["data"]["scenes"][i].pop(k, None)
            json.dump(spec, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"[hikaye] örtüşme: sahne {sahne} sadeleştirildi, yeniden çiziliyor")
            continue
        sys.exit(f"[hikaye] render başarısız: {hata[-600:]}")
    meta = json.load(open(os.path.join(ROOT, "public", "social", f"short-{slug}.json"), encoding="utf-8"))
    if meta.get("teknik") != "hikaye":
        sys.exit("[hikaye] motor başarısız (izometriğe düştü) — kuyruğa eklenmedi: "
                 + ((r.stdout or "").strip().splitlines() or [""])[-1][:300])
    # Geçmiş ANCAK video çizildikten sonra: render çökerse paket/aile "kullanıldı" sayılmaz, "yeni veri" tetiği yanmaz
    # (2026-11-18 00:41: sosyal-evde-bakim işaretlendi, render düştü, ancak sabah elle kurtarıldı).
    try:   # render uzun sürebilir: bu arada elle koşan başka bir üretimin yazdığı geçmiş ezilmesin → taze oku
        gecmis = json.load(open(GECMIS, encoding="utf-8"))
    except (OSError, ValueError):
        pass
    simdi = dt.datetime.now().isoformat(timespec="seconds")
    gecmis.setdefault("paketler", {})[p["id"]] = simdi
    gecmis.setdefault("aileler", {})[p["aile"]] = simdi
    if p.get("olay"):
        gecmis.setdefault("olay", {})[p["id"]] = p["olay"]
    gecmis.setdefault("basliklar", []).append(spec["title"])
    os.makedirs(os.path.dirname(GECMIS), exist_ok=True)
    json.dump(gecmis, open(GECMIS + ".tmp", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(GECMIS + ".tmp", GECMIS)
    print(f"[hikaye] ✅ video: {mp4}")
    if a.kuyruk:
        tarih = []   # resmî veri yeni geldiyse (TÜFE, kira tavanı…) bugün 19:00'da çıksın; değilse 19:00 şeridinde sırasını bekler
        if neden == "yeni veri":
            tarih = ["--tarih", dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).date().isoformat()]
        subprocess.run([PY, os.path.join(HERE, "kuyruk.py"), "ekle", slug, "--title", spec["title"] + " #Shorts",
                        "--style", "hikaye", "--format", "para_hikayesi"] + tarih, check=False)
        try:   # panel senaryo kartı
            plan = json.load(open(PLAN, encoding="utf-8"))
            plan.setdefault("senaryolar", []).insert(0, {
                "id": slug[:20], "baslik": spec["title"], "kalip": p["kalip"], "sure": f"{(meta.get('timeline') or [{'t1': 0}])[-1].get('t1', 0) + 1.5:.0f} sn",
                "kanca_karti": " ".join(spec["data"].get("kanca", [])), "satirlar": [l["say"] for l in spec["lines"]],
                "gorsel": "Otomatik üretildi (hikaye motoru).", "kaynak": p["veri"] + [p["kaynak"]],
                "duygu": "Kitaptaki duygu yolu: merak → şaşkınlık/haksızlık/nostalji → kontrol"})
            plan["senaryolar"] = plan["senaryolar"][:12]
            json.dump(plan, open(PLAN + ".tmp", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            os.replace(PLAN + ".tmp", PLAN)
            k = json.load(open("/root/parafomo-data/dash/senaryo-kararlar.json", encoding="utf-8")) \
                if os.path.exists("/root/parafomo-data/dash/senaryo-kararlar.json") else {}
            k[slug[:20]] = {"durum": "uretildi", "zaman": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                            "not": "Gece otomatik üretildi ve kontrol listesinden geçti; kuyrukta."}
            json.dump(k, open("/root/parafomo-data/dash/senaryo-kararlar.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        except Exception as ex:   # panel yazılamazsa üretim yine geçerli
            print("[hikaye] panel kartı yazılamadı:", ex)
    return 0


if __name__ == "__main__":
    sys.exit(main())
