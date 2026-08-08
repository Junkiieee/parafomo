#!/usr/bin/env python3
"""
ParaFOMO — senaryo → TAM MANİM dönüştürücü.

viral-script.py'nin ürettiği bir senaryo JSON'unu alır, her segmentin görselini
Manim sahnesine çevirir → tamamı özgün, tek tutarlı Manim dilinde (STOK YOK) bir
"sadece-manim" varyantı üretir. Normal hattan AYRI, ek video için.

Kural:
- Segmentte veri (chart payload) varsa → Manim `backtest` (büyüyen eğri + count-up).
- Değilse → Manim `concept` kartı: konuşmadan türeyen büyük anahtar kelime + marka dokusu.
- Tema tüm video için tek (tutarlılık); gün gün döner (çeşitlilik).

Kullanım: python scripts/manimify.py <senaryo.json>   → stdout SON satırı = yeni json yolu
"""
import os, re, sys, json, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCEN_DIR = os.path.join(ROOT, "public", "social", "scenarios")

# Konuşmadaki finans kavramı → (TR anahtar kelime, arka plan sembolü). Öncelik sırası.
CONCEPT_KW = [
    (("düş", "çöküş", "zarar", "kayb", "riskli", "dalgalan", "batır"), ("Risk", "%")),
    (("gram altın", "külçe", "altın", " ons"), ("Altın", "₺")),
    (("dolar", "euro", "sterlin", "döviz", "kur ", "parite"), ("Dolar", "$")),
    (("borsa", "hisse", "bist", "endeks", "temettü"), ("Borsa", "%")),
    (("enflasyon", "zam", "pahalı", "fiyat art"), ("Enflasyon", "%")),
    (("faiz", "merkez bankas", "tcmb", "fed", "politika faiz"), ("Faiz", "%")),
    (("mevduat", "banka", "kredi", "hesap"), ("Mevduat", "₺")),
    (("kripto", "bitcoin", "ethereum", "coin"), ("Kripto", "₿")),
    (("konut", "kira", "gayrimenkul", "emlak", "daire", "ev "), ("Konut", "₺")),
    (("maaş", "asgari ücret", "gelir", "kazanç"), ("Maaş", "₺")),
    (("tasarruf", "biriktir", "birikim", "kumbara"), ("Tasarruf", "₺")),
    (("vergi", "stopaj", "beyanname"), ("Vergi", "₺")),
    (("emekli", "emeklilik", "bes"), ("Emeklilik", "₺")),
]
THEMES = ["slate", "light", "dark"]


def concept_kw(spoken, title):
    t = " " + (spoken or "").lower() + " "
    for keys, kw in CONCEPT_KW:
        if any(k in t for k in keys):
            return kw
    # kavram yoksa: başlıktan ilk anlamlı kelime, yoksa 'Para'
    w = re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü]{4,}", title or "")
    return ((w[0].capitalize() if w else "Para"), "₺")


def has_chart(visual):
    v = visual or {}
    ch = v.get("chart")
    return isinstance(ch, dict) and (ch.get("amount") or ch.get("end_value") or ch.get("pct"))


def main():
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
        print("HATA: senaryo yolu gerekli", file=sys.stderr); return 1
    sc = json.load(open(sys.argv[1], encoding="utf-8"))
    theme = THEMES[datetime.datetime.now(datetime.timezone.utc).timetuple().tm_yday % len(THEMES)]
    title = sc.get("title", "")

    for seg in sc.get("segments", []):
        spoken = seg.get("spoken", "")
        vis = seg.get("visual") or {}
        if has_chart(vis):
            seg["visual"] = {"type": "manim", "scene": "backtest", "theme": theme,
                             "title": vis.get("title") or "", "chart": vis["chart"]}
        elif seg.get("kind") == "cta":
            seg["visual"] = {"type": "manim", "scene": "concept", "theme": theme,
                             "keyword": "ParaFOMO", "sub": "abone ol, kaçırma", "glyph": "₺"}
        else:
            kw, glyph = concept_kw(spoken, title)
            seg["visual"] = {"type": "manim", "scene": "concept", "theme": theme,
                             "keyword": kw, "glyph": glyph}

    # yeni slug + dosya (çakışmasın)
    base = sc.get("slug", "viral")
    sc["slug"] = f"{base}-m"
    os.makedirs(SCEN_DIR, exist_ok=True)
    out = os.path.join(SCEN_DIR, f"{sc['slug']}.json")
    json.dump(sc, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[manimify] tema={theme}, {len(sc.get('segments', []))} segment → {sc['slug']}",
          file=sys.stderr)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
