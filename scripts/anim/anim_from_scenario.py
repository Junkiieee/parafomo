#!/usr/bin/env python3
"""Shorts senaryosunu (public/social/scenarios/<slug>.json) izometrik animasyon parçasına çevirir.

    python3 scripts/anim/anim_from_scenario.py <senaryo.json> [--no-llm]
    → public/social/scenarios/<slug>.anim.json  (anim_build.py girdisi; son satır = yol)

Her bölüm (hook/point/cta) bir sahne olur: big_number · layers · bars · compare · steps · icon_text · cta.
Sahne seçimi + veri LLM'den (gece hazırlıkta; gündüz render sıfır token). SAYI KAPISI: sahne verisindeki
her rakam o bölümün konuşma metninde ya da senaryonun number_source alanında geçmeli — geçmezse geri
bildirimle bir kez daha sorulur, yine olmazsa o bölüm rakamsız ikon sahnesine düşer (asla uydurma rakam).
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "scripts", "lib"))

TYPES = {"big_number", "layers", "bars", "compare", "steps", "icon_text", "cta"}
ICONS = ["coins", "gold", "cash", "house", "car", "bank", "calendar", "chart", "percent", "card", "piggy"]

PROMPT = """Bir Türk finans kanalının (ParaFOMO) dikey kısa videosu kodla çizilmiş izometrik animasyonla
yapılacak. Senaryonun her BÖLÜMÜ için ekranda ne gösterileceğini seç. Yalnız JSON döndür.

SAHNE TÜRLERİ (data şeması):
- big_number: {"icon": İKON, "value": sayı, "unit": "₺"|"%"|"$"|"€"|"x"|"", "suffix": ""|"bin"|"milyon"|"milyar", "label": "≤34 krk açıklama"}
  → tek çarpıcı rakam (kanca için en iyisi).
- layers: {"total": {"label": "…", "value": sayı}, "parts": [{"label": "≤16 krk", "value": sayı, "hl": true|false}], "unit": "₺"}
  → bir tutarın parçalara ayrılışı (2-5 parça, parçaların toplamı total olmalı). En güçlü görsel; uygunsa kullan.
- bars: {"items": [{"label": "≤10 krk", "value": sayı}], "unit": "…", "suffix": "", "hl": vurgulanan sıra (0'dan)}
  → 2-6 değerin kıyası / zaman içinde değişimi.
- compare: {"a": {"label": "…", "value": sayı}, "b": {"label": "…", "value": sayı}, "unit": "…", "note": "≤18 krk, ör. '3,7 KAT'"}
  → iki şey karşı karşıya (önce/sonra, X mi Y mi).
- steps: {"items": ["≤18 krk", "≤18 krk", "≤18 krk"]}  → yapılacaklar / 3 adım (rakamsız bölümler için).
- icon_text: {"icon": İKON, "text": "≤7 kelime, en önemli 1-2 kelimeyi *yıldızla* vurgula"}  → rakamsız fikir.
- cta: {"l1": "≤16 krk", "l2": "≤16 krk", "sub": "≤30 krk (ör. 'NET MAAŞ HESAPLAMA · ÜCRETSİZ')"}  → SON bölüm her zaman bu.
İKON: coins (TL/para), gold (altın), cash (nakit/maaş), house (kira/konut), car (araba/MTV), bank (banka/faiz/mevduat),
calendar (tarih/ay), chart (borsa/getiri/artış), percent (enflasyon/oran/faiz), card (kredi kartı/borç), piggy (birikim).

KURALLAR:
1. Her bölüm için TAM BİR sahne, aynı sırada. Her sahnede "head": ekranın üstündeki kısa başlık (≤24 krk, o bölümün fikri, rakam tekrarı yok).
2. SAYI KAPISI: data'daki HER sayı, O BÖLÜMÜN konuşma metninde aynen geçmeli (ya da aşağıdaki KAYNAK satırında).
   Hesaplama, yuvarlama, uydurma YOK. "75 bin" → value 75, suffix "bin" ya da value 75000. "yüzde 30" → value 30, unit "%".
3. Uygun rakam yoksa icon_text ya da steps kullan. Art arda iki bölüm aynı türde olmasın (mümkünse).
4. İlk bölüm (kanca) görsel olarak en çarpıcı olsun: big_number, compare ya da layers.

KAYNAK: %(source)s
BÖLÜMLER:
%(segments)s

Çıktı: {"eyebrow": "≤22 krk üst etiket (ör. 'ŞOK VERİ', 'AÇIKLANDI')", "scenes": [{"type": "…", "head": "…", "data": {…}}, …]}
%(feedback)s"""


def tr_numbers(text):
    """Metindeki sayıları (Türkçe biçim) kümeye çevir: '1.000'→1000, '3,7'→3.7, '75 bin'→75 ve 75000."""
    out = set()
    for m in re.finditer(r"\d+(?:[.,]\d+)*(\s*(?:bin|milyon|milyar))?", text.lower()):
        raw = re.match(r"\d+(?:[.,]\d+)*", m.group(0)).group(0)
        if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", raw):
            v = float(raw.replace(".", "").replace(",", "."))
        elif "," in raw:
            v = float(raw.replace(".", "").replace(",", "."))
        elif re.fullmatch(r"\d+\.\d{1,2}", raw):
            v = float(raw)
        else:
            v = float(raw.replace(".", ""))
        out.add(v)
        mult = {"bin": 1e3, "milyon": 1e6, "milyar": 1e9}.get((m.group(1) or "").strip())
        if mult:
            out.add(v * mult)
    return out


def scene_numbers(sc):
    d = sc.get("data") or {}
    vals = []
    t = sc.get("type")
    if t == "big_number":
        vals.append(d.get("value"))
    elif t == "layers":
        vals += [p.get("value") for p in d.get("parts", [])]
        if d.get("total"):
            vals.append(d["total"].get("value"))
    elif t == "bars":
        vals += [x.get("value") for x in d.get("items", [])]
    elif t == "compare":
        vals += [d.get("a", {}).get("value"), d.get("b", {}).get("value")]
    # metin alanlarındaki rakamlar da kapıdan geçer (head, label, note, text…)
    texts = [sc.get("head", "")] + [str(v) for k, v in d.items() if isinstance(v, str)]
    for k in ("parts", "items"):
        for x in d.get(k, []) or []:
            texts.append(x.get("label", "") if isinstance(x, dict) else str(x))
    for k in ("a", "b", "total"):
        if isinstance(d.get(k), dict):
            texts.append(d[k].get("label", ""))
    return vals, " ".join(texts)


def check(scenes, segs, source):
    errs = []
    if len(scenes) != len(segs):
        return [f"{len(segs)} bölüm var, {len(scenes)} sahne döndü — sayılar eşit olmalı"]
    src = tr_numbers(source)
    for i, (sc, sg) in enumerate(zip(scenes, segs)):
        t = sc.get("type")
        if t not in TYPES:
            errs.append(f"bölüm {i + 1}: bilinmeyen tür '{t}'")
            continue
        if sg.get("kind") == "cta" and t != "cta":
            errs.append(f"bölüm {i + 1}: son (cta) bölüm 'cta' türünde olmalı")
        allowed = tr_numbers(sg.get("spoken", "")) | src
        vals, texts = scene_numbers(sc)
        for v in vals:
            if not isinstance(v, (int, float)):
                errs.append(f"bölüm {i + 1}: sayı alanı sayı değil ({v!r})")
                continue
            if not any(abs(v - a) <= 1e-6 * max(1, abs(a)) for a in allowed):
                errs.append(f"bölüm {i + 1}: {v} konuşmada/kaynakta yok (izinli: {sorted(allowed)[:12]})")
        for v in tr_numbers(texts):
            if v > 31 and not 2000 <= v <= 2035 and not any(abs(v - a) <= 1e-6 * max(1, abs(a)) for a in allowed):
                errs.append(f"bölüm {i + 1}: metindeki {v:g} konuşmada/kaynakta yok")
        if t == "layers":
            ps = sc["data"].get("parts", [])
            tot = (sc["data"].get("total") or {}).get("value")
            if tot and ps and abs(sum(p.get("value", 0) for p in ps) - tot) > 0.02 * tot:
                errs.append(f"bölüm {i + 1}: layers parçalarının toplamı total'e eşit değil")
    return errs


def guess_icon(text):
    t = text.lower()
    for keys, ic in ((("altın", "gram"), "gold"), (("kira", "konut", "ev "), "house"), (("mtv", "araç", "araba", "otomobil"), "car"),
                     (("mevduat", "faiz", "banka"), "bank"), (("enflasyon", "yüzde", "oran"), "percent"),
                     (("borsa", "hisse", "getiri", "bist"), "chart"), (("kredi kart", "borç"), "card"),
                     (("birikim", "tasarruf"), "piggy"), (("maaş", "ücret", "emekli"), "cash"), (("ocak", "tarih", "ay "), "calendar")):
        if any(k in t for k in keys):
            return ic
    return "coins"


def fallback(sg, i, n):
    """Kapıdan geçemeyen bölüm: rakamsız ikon sahnesi (konuşmanın ilk kelimeleri)."""
    if sg.get("kind") == "cta" or i == n - 1:
        return {"type": "cta", "head": "", "data": {"l1": "HER GÜN", "l2": "TEK NET HESAP", "sub": "PARAFOMO.COM · ÜCRETSİZ ARAÇLAR"}}
    words = re.sub(r"\d[\d.,]*", "", sg.get("spoken", "")).split()
    return {"type": "icon_text", "head": "", "data": {"icon": guess_icon(sg.get("spoken", "")), "text": " ".join(words[:6])}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario")
    ap.add_argument("--no-llm", action="store_true")
    a = ap.parse_args()
    scn = json.load(open(a.scenario, encoding="utf-8"))
    segs = scn["segments"]
    ns = scn.get("number_source") or {}
    source = " ".join(str(v) for v in ns.values()) if isinstance(ns, dict) else str(ns)
    seg_txt = "\n".join(f"{i + 1}. [{s.get('kind')}] {s.get('spoken', '')}" for i, s in enumerate(segs))
    out = None
    if not a.no_llm:
        from llm import call
        fb = ""
        for attempt in range(2):
            prompt = PROMPT.replace("%(source)s", source or "-").replace("%(segments)s", seg_txt).replace("%(feedback)s", fb)
            ok, text, kind = call(prompt,
                                  model="sonnet", effort="medium", timeout=300, tag="anim-scenes")
            if not ok:
                print(f"[anim-scn] LLM yok ({kind}) — yedek sahneler", file=sys.stderr)
                break
            m = re.search(r"\{.*\}", text, re.S)
            try:
                cand = json.loads(m.group(0)) if m else None
            except json.JSONDecodeError:
                cand = None
            if not cand or not isinstance(cand.get("scenes"), list):
                fb = "\nÖNCEKİ YANIT GEÇERSİZ JSON'DU. Yalnız JSON döndür."
                continue
            errs = check(cand["scenes"], segs, source)
            if not errs:
                out = cand
                break
            print("[anim-scn] kapı: " + " | ".join(errs[:6]), file=sys.stderr)
            fb = "\nÖNCEKİ DENEMEDEKİ HATALAR (düzelt):\n- " + "\n- ".join(errs[:10])
            if attempt == 1 and len(cand["scenes"]) == len(segs):   # son deneme: geçen sahneleri tut, kalanları yedeğe düşür
                bad = {int(re.match(r"bölüm (\d+)", e).group(1)) - 1 for e in errs if re.match(r"bölüm \d+", e)}
                cand["scenes"] = [fallback(sg, i, len(segs)) if i in bad else sc
                                  for i, (sc, sg) in enumerate(zip(cand["scenes"], segs))]
                if not check(cand["scenes"], segs, source):
                    out = cand
    if out is None:
        out = {"eyebrow": scn.get("category", "PARAFOMO"), "scenes": [fallback(sg, i, len(segs)) for i, sg in enumerate(segs)]}
    lines = [{"id": f"s{i}", "say": sg["spoken"], "cap": sg["spoken"]} for i, sg in enumerate(segs)]
    for i, sc in enumerate(out["scenes"]):
        sc["line"] = f"s{i}"
    piece = {"slug": scn["slug"], "title": scn["title"], "description": scn.get("description", ""), "tags": scn.get("tags", []),
             "format": scn.get("format", ""), "style": "isometric", "scene": "generic.js", "short": True,
             "data": {"eyebrow": (out.get("eyebrow") or scn.get("category") or "PARAFOMO").upper(), "scenes": out["scenes"]},
             "lines": lines}
    if scn.get("link"):
        piece["link"] = scn["link"]
    try:   # kaplama dönüşü (scripts/anim/skins.json): gün sırasıyla
        import datetime
        rot = json.load(open(os.path.join(HERE, "skins.json"), encoding="utf-8")).get("rotation") or ["iso"]
        piece["skin"] = os.environ.get("ANIM_SKIN") or rot[datetime.date.today().toordinal() % len(rot)]   # kuyruk.py deneyi stili verir
    except Exception:
        piece["skin"] = "iso"
    dst = os.path.join(os.path.dirname(os.path.abspath(a.scenario)), f"{scn['slug']}.anim.json")
    json.dump(piece, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("[anim-scn] " + " · ".join(s["type"] for s in out["scenes"]), file=sys.stderr)
    print(dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
