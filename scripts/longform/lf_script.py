#!/usr/bin/env python3
"""Uzun-form senaryo üretici: doğrulanmış blog yazısı (+ veri JSON) → bölümlü senaryo JSON.

    python3 scripts/longform/lf_script.py --post 2027-zamlari-yeniden-degerleme-orani-rehberi \
        --slug lf-2027-zamlari --link /yeniden-degerleme-orani/ [--data data/yeniden-degerleme.json] \
        [--minutes 7] [--angle "oran açıklandı: ..."] [--dry]

Kaynak = sitede canlı, kaynaklı yazı (live-posts şablonları resmî veriden üretir). Senaryodaki HER sayı
kaynakta geçmek zorunda (sayı kapısı); geçmezse model hatalarıyla birlikte bir kez daha yazdırılır.
Başlık+kapak birlikte denetlenir (lf_package.lint) — kapak başlığı tekrar etmez, ≤4 kelime.

Çıktı: public/social/longform/<slug>.script.json
{slug,title,description,tags,link,thumbnail:{top,big,bottom},chapters:[{title,beats:[{say,show}]}]}
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
from lf_common import OUT_DIR, ROOT  # noqa: E402
import lf_package  # noqa: E402

KINDS = {
    "title": '{"kind":"title","badge":"(ops. 1-2 kelime: TAHMİN / BELLİ OLDU)","headline":"≤7 kelime","sub":"≤10 kelime"}',
    "chapter": '{"kind":"chapter"}  ← her bölümün (1. hariç) İLK beat\'i; başlık bölüm adından gelir',
    "bigstat": '{"kind":"bigstat","label":"≤6 kelime","value":"%27,81 | 7.349 TL","note":"≤12 kelime","badge":"ops."}',
    "compare": '{"kind":"compare","label":"≤6 kelime","before_label":"2026","before":"5.750 TL","after_label":"2027","after":"7.349 TL","note":"ops."}',
    "table": '{"kind":"table","title":"≤6 kelime","cols":["Kalem","2026","2027"],"rows":[["…","…","…"]],"note":"ops. kaynak/uyarı"}  (≤6 satır)',
    "bars": '{"kind":"bars","title":"…","items":[{"label":"2023","value":122.93,"text":"%122,9"}],"highlight":"2027"}  (≤8 öğe, value SAYI)',
    "steps": '{"kind":"steps","title":"…","lines":["2026 tutarı: 5.750 TL","× 1,2781","= 7.349 TL"]}  (≤5 satır; sonuç "=" ile başlar)',
    "bullets": '{"kind":"bullets","title":"…","items":["≤8 kelime", "…"]}  (≤4 madde)',
    "timeline": '{"kind":"timeline","title":"…","items":[{"date":"3 Kasım","text":"≤6 kelime","hot":true}]}  (≤5)',
    "quote": '{"kind":"quote","text":"kanun/resmî metinden kısa alıntı","source":"Kanun adı md. X"}',
    "layers": '{"kind":"layers","title":"X\'in anatomisi","total_label":"…","total":"40.874,63 TL","items":[{"label":"Net maaş","value":28075.5,"text":"28.075,50 TL","note":"cebine giren","hot":true}]}  (patlatılmış görünüm: bir bütünü katmanlarına ayırır; 3-6 katman, value SAYI, toplam = katmanların toplamı; en güçlü görsel — bir tutarın içinde ne olduğunu göstermek için kullan)',
    "cta": '{"kind":"cta","headline":"≤6 kelime","url":"parafomo.com/…","sub":"Link açıklamada"}',
}

PROMPT = """Sen ParaFOMO'nun (Türkçe kişisel finans kanalı, 35-54 yaş ağırlıklı izleyici) uzun-form YouTube
senaryo yazarısın. Aşağıdaki KAYNAK yazıdan yaklaşık {minutes} dakikalık, 16:9, yüz göstermeyen bir
anlatım videosu yaz. Ekranda yalnızca veriden çizilen hareketli grafikler var (stok görüntü yok); ses
tek bir anlatıcı (TTS). {angle}

KURALLAR
1. SAYI KAPISI: Kullandığın HER sayı (tutar, oran, tarih günü, kanun no) KAYNAK'ta aynen geçmeli. Yeni
   hesap yapma, yuvarlama yapma (kaynakta "≈7.349 TL" varsa 7.349 kullan). Emin değilsen sayısız söyle.
   Kaynakta "tahmin" denen rakamı kesinmiş gibi sunma.
2. İLK 15 SANİYE (1. bölüm, ilk 2-3 beat): başlığın vaadini hemen doğrula, kapanmamış bir soru aç,
   karşılığın videoda olduğunu kanıtla (ör. somut bir tutar). "Merhaba", kanal tanıtımı, "abone ol"
   YOK. 1. beat show türü "title" ya da "bigstat".
3. Her bölüm sonunda bir sonraki bölüme merak köprüsü kur (ör. "ama asıl sürpriz emlak vergisinde").
4. Beat = 1-3 kısa konuşma cümlesi (≤ 280 karakter) + ekranda TEK görsel (show). Ekran konuşulanı
   birebir göstermeli. Arka arkaya aynı tür en fazla 2 kez; türleri çeşitlendir.
5. Konuşma dili: "sen" hitabı, kısa cümle, günlük Türkçe. Sayıları RAKAMLA yaz ama birim konuşma
   dilinde: "7.349 lira", "yüzde 27,81" (konuşmada "TL" ve "%" YAZMA; ekranda (show) "TL" ve "%" kullan).
   Kısaltmaları ilk geçişte aç: "Yurt İçi Üretici Fiyat Endeksi, yani üretici enflasyonu". "VUK" yerine
   "Vergi Usul Kanunu". Parantez, madde işareti, emoji yok.
6. Tek çağrı, en sonda: son bölüm kısa bir özet + "bilgilendirme amaçlıdır" notu + cta beat'i
   (hesaplayıcı linki açıklamada + abone ol). Ortada abone isteme.
7. Uzunluk: toplam konuşma metni yaklaşık {chars} karakter (±%15). {chapters} bölüm; her bölüm 3-9 beat.
8. Başlık (title): ≤60 karakter, aranan ifade başta ("2027 yeniden değerleme oranı", "2027 MTV" gibi),
   somut sayı içersin, en fazla 2 BÜYÜK HARF kelime, abartı/clickbait yok (YouTube yanıltıcı meta = ban riski).
9. Kapak (thumbnail): top (1-2 kelime) + big (tek sayı ya da 1 kelime) + bottom (1-3 kelime). Kapaktaki
   kelimeler başlıktaki kelimeleri TEKRAR ETMESİN — kapak başlığın söylemediğini söylesin. Toplam ≤5 kelime.
10. description: 2 kısa paragraf (ne öğrenecek + kaynak resmî veri), sayılar kaynaktan. Link/hashtag YAZMA
    (otomatik eklenir). tags: 8-12 arama ifadesi.

SHOW TÜRLERİ (JSON biçimi):
{kinds}

ÇIKTI: YALNIZCA geçerli JSON (açıklama, ``` yok):
{{"title":"…","description":"…","tags":["…"],"thumbnail":{{"top":"…","big":"…","bottom":"…"}},
 "chapters":[{{"title":"bölüm adı (≤4 kelime, açıklamadaki zaman damgası olur)","beats":[{{"say":"…","show":{{…}}}}]}}]}}
{feedback}
KAYNAK YAZI ({src_name}):
<<<
{source}
>>>
{data_block}"""


# ───────────────────────── sayı kapısı ─────────────────────────

NUM = re.compile(r"\d+(?:[.,]\d+)*")


def canon(tok):
    """'5.750'→5750, '27,81'→27.81, '1,2781'→1.2781, '2.907.136'→2907136."""
    t = tok
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", t):
        t = t.replace(".", "").replace(",", ".")
    elif "," in t and "." not in t:
        t = t.replace(",", ".")
    try:
        return round(float(t), 4)
    except ValueError:
        return None


def allowed_numbers(text):
    s = set()
    for tok in NUM.findall(text):
        v = canon(tok)
        if v is None:
            continue
        s.add(v)
        if v < 200:  # yüzdeler → çarpan (5.750 × 1,2781 gösterimi için)
            s.add(round(1 + v / 100, 4))
            s.add(round(1 + v / 100, 2))
            s.add(round(v, 1))
    s.update(range(0, 13))          # sıra/sayaç, aylar
    s.update(range(2015, 2031))     # yıllar
    return s


def numbers_in(obj):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("kind", "n", "hot"):
                continue
            if k == "value" and isinstance(v, (int, float)):
                out.append(round(float(v), 4))
                continue
            out += numbers_in(v)
    elif isinstance(obj, list):
        for v in obj:
            out += numbers_in(v)
    elif isinstance(obj, str):
        for tok in NUM.findall(obj):
            v = canon(tok)
            if v is not None:
                out.append(v)
    return out


def validate(sc, allowed, minutes):
    errs = []
    for k in ("title", "description", "chapters", "thumbnail"):
        if k not in sc:
            errs.append(f"'{k}' alanı yok")
    if errs:
        return errs
    chs = sc["chapters"]
    if not 4 <= len(chs) <= 9:
        errs.append(f"bölüm sayısı {len(chs)} (4-9 olmalı)")
    total = 0
    for ci, ch in enumerate(chs):
        bs = ch.get("beats", [])
        if not bs:
            errs.append(f"bölüm {ci + 1} boş")
            continue
        if ci > 0 and (bs[0].get("show") or {}).get("kind") != "chapter":
            errs.append(f"bölüm {ci + 1} ilk beat'i 'chapter' değil")
        for bi, b in enumerate(bs):
            say = b.get("say", "")
            total += len(say)
            kind = (b.get("show") or {}).get("kind")
            if kind not in KINDS:
                errs.append(f"b{ci + 1}.{bi + 1}: geçersiz show türü {kind!r}")
            if len(say) > 320:
                errs.append(f"b{ci + 1}.{bi + 1}: konuşma {len(say)} karakter (≤280)")
            if re.search(r"\bTL\b|%", say):
                errs.append(f"b{ci + 1}.{bi + 1}: konuşmada 'TL'/'%' var — 'lira'/'yüzde' yaz")
    target = minutes * 60 * 13.0
    if not 0.7 * target <= total <= 1.3 * target:
        errs.append(f"toplam konuşma {total} karakter (hedef ≈{int(target)})")
    bad = sorted({v for v in numbers_in({"t": sc.get("title"), "d": sc.get("description"),
                                          "th": sc.get("thumbnail"), "c": chs}) if v not in allowed})
    if bad:
        errs.append("KAYNAKTA OLMAYAN SAYILAR: " + ", ".join(str(b) for b in bad[:15]) +
                    " — bunları kaynaktaki rakamlarla değiştir ya da sayısız söyle")
    errs += [f"paket: {m}" for m in lf_package.lint(sc["title"], sc["thumbnail"], blocking_only=True)]
    return errs


def parse_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    a, b = text.find("{"), text.rfind("}")
    return json.loads(text[a:b + 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", required=True, help="src/content/blog/<post>.md slug'ı")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--link", default="", help="açıklamadaki birincil site linki (yol)")
    ap.add_argument("--data", action="append", default=[], help="ek veri JSON (kaynak sayılarına eklenir)")
    ap.add_argument("--minutes", type=float, default=8.5)  # ≥8 dk: video ortası reklam
    ap.add_argument("--angle", default="", help="ek yönlendirme (ör. 'oran açıklandı, BELLİ OLDU çerçevesi')")
    ap.add_argument("--model", default="opus")
    ap.add_argument("--dry", action="store_true", help="istemi yazdır, model çağırma")
    a = ap.parse_args()

    src_path = os.path.join(ROOT, "src", "content", "blog", a.post + ".md")
    source = open(src_path, encoding="utf-8").read()
    source = re.sub(r"^#.*\n", "", source, flags=re.M)  # şablon yorum satırları
    data_block, data_txt = "", ""
    for p in a.data:
        txt = open(os.path.join(ROOT, p) if not os.path.isabs(p) else p, encoding="utf-8").read()
        data_txt += txt
        data_block += f"\nEK VERİ ({os.path.basename(p)}):\n<<<\n{txt[:6000]}\n>>>\n"
    allowed = allowed_numbers(source + data_txt)
    chars = int(a.minutes * 60 * 13.0)
    n_ch = max(4, min(8, round(a.minutes)))
    angle = f"\nYÖNLENDİRME: {a.angle}\n" if a.angle else ""

    from llm import call  # scripts/lib/llm.py
    feedback, sc, errs = "", None, []
    for attempt in range(3):
        prompt = PROMPT.format(minutes=a.minutes, angle=angle, chars=chars, chapters=f"{n_ch-1}-{n_ch+1}",
                               kinds="\n".join(f"- {k}: {v}" for k, v in KINDS.items()),
                               feedback=feedback, src_name=a.post, source=source, data_block=data_block)
        if a.dry:
            print(prompt)
            return 0
        ok, text, kind = call(prompt, model=a.model, effort="high", timeout=1200, tag="longform-script")
        if not ok:
            print(f"[lf-script] model çağrısı başarısız: {kind}")
            return 2
        try:
            sc = parse_json(text)
        except Exception as e:
            errs = [f"JSON çözümlenemedi: {e}"]
        else:
            errs = validate(sc, allowed, a.minutes)
        if not errs:
            break
        print(f"[lf-script] deneme {attempt + 1}: {len(errs)} sorun → yeniden yazdırılıyor")
        for e in errs[:12]:
            print("   -", e)
        feedback = ("\nÖNCEKİ TASLAĞIN SORUNLARI (hepsini düzelt, gerisini koru):\n- " + "\n- ".join(errs[:20])
                    + ("\nÖNCEKİ TASLAK:\n" + json.dumps(sc, ensure_ascii=False) if sc else "") + "\n")
    if errs:
        print("[lf-script] HATA: 3 denemede geçerli senaryo çıkmadı")
        return 3
    sc.update({"slug": a.slug, "link": a.link, "source": f"/blog/{a.post}/"})
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"{a.slug}.script.json")
    json.dump(sc, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    n_beats = sum(len(c["beats"]) for c in sc["chapters"])
    n_chars = sum(len(b["say"]) for c in sc["chapters"] for b in c["beats"])
    print(f"[lf-script] ✅ {out} — {len(sc['chapters'])} bölüm, {n_beats} beat, {n_chars} karakter")
    print(f"[lf-script] başlık: {sc['title']}")
    for m in lf_package.lint(sc["title"], sc["thumbnail"]):
        print(f"[lf-script] paket notu: {m}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
