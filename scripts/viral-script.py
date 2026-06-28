#!/usr/bin/env python3
"""
ParaFOMO — Viral Shorts senaryo üreticisi (6 format, blog'dan bağımsız).

Bir FORMAT + opsiyonel KONU alır, `claude -p` ile viral odaklı bir senaryo
üretir ve shorts-build.py'nin --scenario modunun beklediği JSON'u yazar:
  public/social/scenarios/<slug>.json
Her beat, görsel motoruna ({type, query}) bir görsel isteği taşır → senaryo
ile ekrandaki görsel ÖRTÜŞÜR (Trump → gerçek Trump fotoğrafı, altın → külçe).

Formatlar (havuz):
  comparison       Karşılaştırma yarışı (altın/dolar/borsa/mevduat kim kazandırdı)
  myth             Mit yıkma ("bunu yanlış biliyorsun")
  shock_number     Sayı şoku (çarpıcı tek istatistik)
  news_reaction    Güncel olay/kişiye tepki (konu verilmeli/seçilir)
  single_concept   Tek kavram + metafor (karmaşığı tek cümlede)
  backtest_return  Geri-dönük getiri ("X TL Y önce Z'ye koysaydın...")

Kullanım:
  python3 scripts/viral-script.py --format myth
  python3 scripts/viral-script.py --format news_reaction --topic "Trump yeni gümrük tarifeleri"
Çıkış: 0 başarı (stdout son satırı = yazılan json yolu), 1 hata.
"""
import os
import re
import sys
import json
import argparse
import subprocess
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCEN_DIR = os.path.join(ROOT, "public", "social", "scenarios")

# market-history.py (tireli) → modül olarak yükle (geçmiş veri; gerekince)
def _load_mh():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "market_history", os.path.join(os.path.dirname(os.path.abspath(__file__)), "market-history.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

# Gerçek veri gerektiren formatlar
DATA_FORMATS = {"backtest_return", "comparison"}


def build_market_context(fmt, instrument, amount, rng):
    """(facts_block, chart_payload) → veri formatları için gerçek rakam + grafik verisi."""
    mh = _load_mh()
    if fmt == "backtest_return":
        d = mh.backtest(instrument, amount, rng, "1mo")
        facts = (
            "GERÇEK VERİLER (Yahoo Finance — AYNEN kullan, BAŞKA rakam uydurma):\n"
            f"- Enstrüman: {d['label']}\n"
            f"- {amount} TL'yi geçen yıl bu zamanlar {d['label']}'a koysaydın bugün ~{d['end_value']} TL olurdu\n"
            f"- Yaklaşık getiri: %{d['pct']} (dönem {d['x'][0]} → {d['x'][-1]})\n"
            f"Senaryoda {amount} TL, ~{d['end_value']} TL ve %{d['pct']} sayılarını kullan; 'yaklaşık' de.")
        chart = {"kind": "line", "label": d["label"], "unit": d["unit"], "points": d["points"],
                 "x": d["x"], "amount": amount, "end_value": d["end_value"], "pct": d["pct"]}
        return facts, chart
    if fmt == "comparison":
        c = mh.compare(rng, "1mo")
        lines = "\n".join(f"- {i['name']}: %{i['pct']}" for i in c["items"])
        winner = c["items"][0]["name"] if c["items"] else ""
        facts = (
            "GERÇEK VERİLER (Yahoo Finance, son 1 yıl getirileri — AYNEN kullan, sıralamayı bozma):\n"
            f"{lines}\n"
            f"Kazanan: {winner}. Bu rakamları ve doğru sıralamayı kullan; başka rakam uydurma.")
        chart = {"kind": "bars", "title": "Bu Yıl Kim Kazandırdı?",
                 "items": [{"name": i["name"], "pct": i["pct"]} for i in c["items"]]}
        return facts, chart
    return "", None

# Görsel tipi sözlüğü — üreticiye DOĞRU kaynak-hizalı tip seçtirir.
VISUAL_GUIDE = """Görsel tipleri ve "query" kuralı (görsel motoru buna göre kaynak seçer):
- "person": gerçek kişi → query = TAM ÖZEL AD (ör. "Donald Trump", "Recep Tayyip Erdoğan", "Elon Musk"). Wikimedia'dan gerçek fotoğraf gelir.
- "place" / "building": gerçek yer → query = özel ad (ör. "Borsa İstanbul", "Federal Reserve building").
- "logo": marka/şirket → query = "<Şirket> logo".
- "gold": altın görseli → query İNGİLİZCE (ör. "gold bullion bars", "gold coins").
- "object": gerçek nesne → query İNGİLİZCE isim.
- "concept" / "scene": soyut/sahne stok video → query İNGİLİZCE arama terimi (ör. "inflation money cash", "stock market chart screen", "istanbul city skyline night", "bank counter money").
ÖNEMLİ: hook ve konunun ana öznesi gerçek bir kişi/yer/marka ise MUTLAKA person/place/logo kullan (stok değil). Her beat'in görseli o beat'in İÇERİĞİYLE birebir örtüşsün."""

FORMATS = {
    "comparison": {
        "category": "KARŞILAŞTIRMA",
        "guide": "Karşılaştırma yarışı. Hook: 'Altın mı, dolar mı, borsa mı, mevduat mı?' tarzı bir yarış sorusu. 3 beat: araçları tek tek kıyasla, sayısal/karşılaştırmalı konuş. Sonunda net bir kazanan ya da çıkarım. Görseller: her araç için gold/concept(dollar)/concept(stock market)/concept(bank).",
    },
    "myth": {
        "category": "MİT",
        "guide": "Mit yıkma. Hook: yaygın ama YANLIŞ bir finans inancını söyle ('Bankada para tutmak güvenli sanıyorsun.'). 3 beat: neden yanlış olduğunu, gerçeği ve doğrusunu anlat. Hafif kışkırtıcı ama doğru. Görseller içerikle örtüşsün.",
    },
    "shock_number": {
        "category": "ŞOK VERİ",
        "guide": "Sayı şoku. Hook: çarpıcı TEK istatistik/oran ('Türkiye'de her 100 kişiden 80'i...'). 3 beat: sayının anlamı, sebebi, izleyici için sonucu. Rakamı net telaffuz et (ekranda otomatik rozet çıkar). Görseller içerikle örtüşsün.",
    },
    "news_reaction": {
        "category": "GÜNCEL",
        "guide": "Güncel olay/kişiye tepki. Hook: olayı/kişiyi söyle ve finansal soruyu sor. 3 beat: olayın piyasaya/altına/dolara/borsaya etkisini sade anlat. Spekülasyon değil, mekanizma. Hook görseli ana kişi/kurum (person/place/logo) OLMALI.",
    },
    "single_concept": {
        "category": "KAVRAM",
        "guide": "Tek kavram + metafor. Hook: kavramı merak uyandıran biçimde sor ('Eurobond aslında ne?'). 3 beat: kavramı GÜNLÜK bir metaforla tek tek aç, jargon yok. Görseller kavramı somutlaştırsın (object/concept).",
    },
    "backtest_return": {
        "category": "GETİRİ",
        "guide": "Geri-dönük getiri. Hook: 'X TL'yi Y önce Z'ye koysaydın bugün ne olurdu?' 3 beat: senaryoyu ve sonucu adım adım ver; net bir sonuç sayısı söyle (uydurma değil, makul/yaklaşık olduğunu ima et). Görseller: gold/money/concept(chart).",
    },
}

PROMPT = """Sen bir Türk finans kanalı (ParaFOMO) için VİRAL YouTube Shorts senaryosu yazıyorsun.
40-45 saniyelik, akıcı, KONUŞMA dilinde, izleyiciyi ilk 2 saniyede durduran bir senaryo üret.

FORMAT: %(fmt_name)s
%(fmt_guide)s
%(topic_line)s
%(facts_block)s
%(chart_instruction)s
Kurallar:
- hook: en fazla 9 kelime; merak/şaşkınlık/FOMO uyandıran KISA cümle. Tıklama tuzağı değil, doğru.
- 3 beat: her biri 12-20 kelime, tek başına anlaşılır, akıcı Türkçe. Kopuk ifade yok.
- cta: kısa, "parafomo.com" geçsin, takibe çağırsın.
- Sade, net, abartısız; değer ver. Yanlış/uydurma rakam verme; tahmini ifadeleri "yaklaşık/olası" diye ver.
- Her segmente bir "visual" ekle.
%(visual_guide)s

SADECE şu JSON'u döndür, başka HİÇBİR şey yazma (markdown, ```, açıklama YOK):
{"title":"<Türkçe, çarpıcı, <70 karakter>","description":"<1-2 cümle özet>","tags":["...","...","..."],
 "segments":[
  {"kind":"hook","eyebrow":"%(eyebrow)s","spoken":"...","visual":{"type":"...","query":"..."}},
  {"kind":"point","spoken":"...","visual":{"type":"...","query":"..."}},
  {"kind":"point","spoken":"...","visual":{"type":"...","query":"..."}},
  {"kind":"point","spoken":"...","visual":{"type":"...","query":"..."}},
  {"kind":"cta","spoken":"...","visual":{"type":"...","query":"..."}}
 ]}
"""

ALLOWED_TYPES = {"person", "place", "building", "logo", "gold", "object",
                 "concept", "scene", "broll", "map", "chart"}


def slugify(s):
    s = unicodedata.normalize("NFKD", s)
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")
    s = s.translate(tr).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:60] or "viral"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", required=True, choices=list(FORMATS))
    ap.add_argument("--topic", default="")
    ap.add_argument("--slug", default="")
    ap.add_argument("--instrument", default="gold", choices=["gold", "usd", "bist"],
                    help="backtest_return için enstrüman")
    ap.add_argument("--amount", type=int, default=10000)
    ap.add_argument("--range", default="1y")
    ap.add_argument("--model", default="claude-sonnet-4-6")
    ap.add_argument("--out-dir", default=SCEN_DIR)
    args = ap.parse_args()

    fmt = FORMATS[args.format]
    topic_line = (f"KONU (bu konuyu işle): {args.topic}" if args.topic
                  else "KONU: Türk yatırımcısının ilgisini çekecek bir konuyu SEN seç (güncel/evergreen).")

    # Veri formatları: gerçek geçmiş veriyi çek, prompt'a göm, grafiği hazırla
    facts_block, chart_instruction, chart_payload = "", "", None
    if args.format in DATA_FORMATS:
        try:
            facts_block, chart_payload = build_market_context(
                args.format, args.instrument, args.amount, args.range)
            chart_instruction = (
                'SONUCU/KARŞILAŞTIRMAYI açıkladığın TEK bir point beat\'inin visual.type\'ını '
                '"chart" yap (query="getiri grafiği"); o beat ekranda grafiği gösterecek. '
                'Diğer beat\'lerde normal görsel (gold/concept/person) kullan.')
        except Exception as e:
            print(f"UYARI: piyasa verisi alınamadı ({str(e)[:70]}) — grafiksiz devam", file=sys.stderr)

    prompt = PROMPT % {
        "fmt_name": args.format, "fmt_guide": fmt["guide"], "topic_line": topic_line,
        "facts_block": facts_block, "chart_instruction": chart_instruction,
        "visual_guide": VISUAL_GUIDE, "eyebrow": fmt["category"],
    }

    print(f"[*] viral senaryo üretiliyor: format={args.format} topic={args.topic or '(serbest)'}",
          file=sys.stderr)
    try:
        r = subprocess.run(["claude", "-p", prompt, "--model", args.model],
                           capture_output=True, text=True, timeout=180)
        out = r.stdout.strip()
    except Exception as e:
        print(f"HATA: claude çağrısı başarısız: {e}", file=sys.stderr); return 1

    m = re.search(r"\{.*\}", out, re.DOTALL)
    if not m:
        print(f"HATA: JSON bulunamadı. Çıktı: {out[:200]}", file=sys.stderr); return 1
    try:
        data = json.loads(m.group(0))
    except Exception as e:
        print(f"HATA: JSON ayrıştırılamadı ({e}). Çıktı: {out[:200]}", file=sys.stderr); return 1

    # doğrulama
    segs = data.get("segments", [])
    if len(segs) != 5:
        print(f"HATA: 5 segment bekleniyor, {len(segs)} geldi", file=sys.stderr); return 1
    kinds = [s.get("kind") for s in segs]
    if kinds != ["hook", "point", "point", "point", "cta"]:
        print(f"HATA: segment sırası hatalı: {kinds}", file=sys.stderr); return 1
    for s in segs:
        v = s.get("visual") or {}
        if not s.get("spoken") or not v.get("query") or v.get("type") not in ALLOWED_TYPES:
            print(f"HATA: eksik/yanlış segment: {json.dumps(s, ensure_ascii=False)[:160]}",
                  file=sys.stderr); return 1
    if not data.get("title"):
        print("HATA: title yok", file=sys.stderr); return 1

    # gerçek veri grafiğini chart-tipli beat'e iliştir (claude koymadıysa son point'e zorla)
    if chart_payload:
        chart_segs = [s for s in segs if (s.get("visual") or {}).get("type") == "chart"]
        if not chart_segs:
            segs[3]["visual"] = {"type": "chart", "query": "getiri grafiği"}
            chart_segs = [segs[3]]
        for s in chart_segs:
            s["visual"]["chart"] = chart_payload

    slug = args.slug or slugify(data["title"])
    scenario = {
        "slug": slug,
        "title": data["title"].strip(),
        "category": fmt["category"],
        "format": args.format,
        "description": data.get("description", "").strip(),
        "tags": list(dict.fromkeys([t.strip() for t in (data.get("tags") or [])[:6]
                                     if t.strip()] + ["parafomo"])),
        "segments": segs,
    }
    os.makedirs(args.out_dir, exist_ok=True)
    path = os.path.join(args.out_dir, f"{slug}.json")
    json.dump(scenario, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[+] senaryo: {path}", file=sys.stderr)
    print(f"    kanca: {segs[0]['spoken']}", file=sys.stderr)
    print(path)   # stdout: çağıran betik için yol
    return 0


if __name__ == "__main__":
    sys.exit(main())
