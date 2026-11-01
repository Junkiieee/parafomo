#!/usr/bin/env python3
"""Ekonomi Defteri konu seçici — veriyle (Kaan 2026-11-01: "bana sunma, sen seç ve paylaş").

    python3 scripts/anim/defter_konu.py plan [--hafta 2026-11-09] [--yaz]   # o haftanın Sal/Cum Short + Pazar uzun seçimi
    python3 scripts/anim/defter_konu.py liste                               # tüm havuzun puan tablosu

Havuz: agent/plan/defter-konular.json. Her konu için sinyaller:
  hacim  = Google Trends 12 ay ortalaması (çapa "mevduat faizi" = 100; fırsat motorunun önbelleği/çekicisi)
  ivme   = son 4 hafta Trends (mevsimsellik: Aralık'ta asgari ücret, Ocak'ta emekli zammı)
  yt     = YouTube arama önerisi sayısı (0-10; YouTube'da bu soruyu yazan var mı)
  tema   = o haftanın takvim temasına uyum (agent/plan/icerik-takvimi.json) → ×1,6
Skor = (ln(1+hacim) + 0,6·ln(1+ivme)) × (0,6 + 0,04·yt) × tema. Yapılmış konu o yuvaya tekrar seçilmez.
Kural: önce Pazar uzun bölüm seçilir; Cuma Short'u aynı konunun kısa versiyonudur (uzunun habercisi, Short'u
yapılmadıysa); Salı Short'u kalan en yüksek skor. Seçim agent/plan/defter-plan.json'a yazılır (--yaz).
"""
import argparse
import datetime as dt
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "learn"))
import opportunity_finder as OF  # noqa: E402

HAVUZ = os.path.join(ROOT, "agent", "plan", "defter-konular.json")
PLAN = os.path.join(ROOT, "agent", "plan", "defter-plan.json")
TAKVIM = os.path.join(ROOT, "agent", "plan", "icerik-takvimi.json")
YT_CACHE = os.path.join(ROOT, "data", "learning", "yt-suggest-cache.json")


def yt_suggest(terms):
    try:
        c = json.load(open(YT_CACHE, encoding="utf-8"))
    except Exception:
        c = {}
    today = dt.date.today()
    for q in terms:
        e = c.get(q)
        if e and (today - dt.date.fromisoformat(e["date"])).days <= 7:
            continue
        url = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode(
            {"client": "firefox", "ds": "yt", "hl": "tr", "gl": "tr", "q": q})
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=15) as r:
                sug = json.loads(r.read().decode("utf-8", "replace"))[1]
            c[q] = {"n": len(sug), "ornek": sug[:5], "date": today.isoformat()}
        except Exception as ex:
            print(f"[konu] YouTube önerisi alınamadı ({q}): {str(ex)[:80]}")
        time.sleep(1)
    os.makedirs(os.path.dirname(YT_CACHE), exist_ok=True)
    json.dump(c, open(YT_CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return c


def sinyaller(konular):
    terms = sorted({q for k in konular for q in k["ara"]})
    cache = OF.load_cache()
    eksik = [q for q in terms if not (q in cache["q"] and OF.fresh(cache["q"][q]))]
    if eksik:
        OF.trends_fetch(eksik, cache)
        json.dump(cache, open(OF.CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    yc = yt_suggest(terms)
    out = {}
    for k in konular:
        # niyet: fiyat/anlık sorgu (Google kendi cevaplar) anlatım videosu izletmez → ×0,4 (fırsat motoruyla aynı)
        # rekabet: dev baş terimde (≤2 kelime, hacim ≥200) ilk sıralar büyük sitelerin → ×0,4
        tr = [(cache["q"].get(q, {}), OF.intent_factor(q)[0] * OF.competition_factor(q, cache["q"].get(q, {}).get("idx")))
              for q in k["ara"]]
        out[k["id"]] = {"hacim": round(max((t.get("idx") or 0) * f for t, f in tr), 1),
                        "ivme": round(max((t.get("recent") or 0) * f for t, f in tr), 1),
                        "yt": max((yc.get(q, {}).get("n") or 0) for q in k["ara"])}
    return out


def hafta(gun):
    t = json.load(open(TAKVIM, encoding="utf-8"))
    ws = [w for w in t["weeks"] if w["start"] <= gun.isoformat()]
    return ws[-1] if ws else t["weeks"][0]


def ileri_tema(gun, hafta_say=5):
    t = json.load(open(TAKVIM, encoding="utf-8"))
    son = (gun + dt.timedelta(weeks=hafta_say)).isoformat()
    return " ".join((w["theme"] + " " + " ".join(w.get("topics", []))).lower()
                    for w in t["weeks"] if gun.isoformat() < w["start"] <= son)


def skor(k, s, tema_txt, ileri_txt=""):
    """tema_txt: bu haftanın teması (×1,6) · ileri_txt: sonraki 5 haftanın temaları (×1,3 — aramalar zirve
    yapmadan önce yayında olmak sıralamaya girmeyi kolaylaştırır)."""
    fit = 1.6 if any(x in tema_txt for x in k.get("tema", [])) else 1.3 if any(x in ileri_txt for x in k.get("tema", [])) else 1.0
    return round((math.log1p(s["hacim"]) + 0.6 * math.log1p(s["ivme"])) * (0.6 + 0.04 * s["yt"]) * fit, 2), fit


def load_plan():
    try:
        return json.load(open(PLAN, encoding="utf-8"))
    except Exception:
        return {"_not": "defter_konu.py çıktısı: tarih → yuva → konu (veriyle seçildi)", "secimler": {}}


def plan(a):
    H = json.load(open(HAVUZ, encoding="utf-8"))
    konular = H["konular"]
    pzt = dt.date.fromisoformat(a.hafta) if a.hafta else dt.date.today() + dt.timedelta(days=(7 - dt.date.today().weekday()) % 7)
    pzt -= dt.timedelta(days=pzt.weekday())
    w = hafta(pzt)
    tema = (w["theme"] + " " + " ".join(w.get("topics", []))).lower()
    ileri = ileri_tema(pzt)
    S = sinyaller(konular)
    P = load_plan()
    alinmis = {(v["yuva"], v["id"]) for v in P["secimler"].values()}
    def yapildi(k, yuva):
        return bool(k.get("yapildi", {}).get(yuva)) or (yuva, k["id"]) in alinmis
    rank = sorted(konular, key=lambda k: -skor(k, S[k["id"]], tema, ileri)[0])
    sal, cum, paz = (pzt + dt.timedelta(days=i) for i in (1, 4, 6))
    by_id = {k["id"]: k for k in konular}
    def dolu(g):   # bu yuva zaten seçildiyse (ya da elle doldurulduysa) o konu
        v = P["secimler"].get(g.isoformat())
        return by_id.get(v["id"]) if v else None
    uzun = dolu(paz) or next(k for k in rank if k.get("uzun") and not yapildi(k, "uzun"))
    cuma = dolu(cum) or (uzun if not yapildi(uzun, "short") else next(k for k in rank if not yapildi(k, "short")))
    sali = dolu(sal) or next(k for k in rank if not yapildi(k, "short") and k["id"] != cuma["id"])
    secim = {sal.isoformat(): ("short", sali), cum.isoformat(): ("short", cuma), paz.isoformat(): ("uzun", uzun)}
    print(f"Hafta {pzt} · tema: {w['theme']}")
    print(f"{'konu':<22}{'skor':>6}{'hacim':>8}{'ivme':>7}{'yt':>4}{'tema':>6}")
    for k in rank[:10]:
        s = S[k["id"]]; sk, fit = skor(k, s, tema, ileri)
        print(f"{k['id']:<22}{sk:>6}{s['hacim']:>8}{s['ivme']:>7}{s['yt']:>4}{('×%.1f' % fit).replace('.', ',') if fit > 1 else '':>6}")
    for g, (yuva, k) in secim.items():
        s = S[k["id"]]
        print(f"→ {g} {yuva:<5} {k['baslik']}  (hacim {s['hacim']}, ivme {s['ivme']}, YouTube önerisi {s['yt']})")
        if a.yaz and g not in P["secimler"]:
            P["secimler"][g] = {"yuva": yuva, "id": k["id"], "baslik": k["baslik"], "sinyal": s,
                                "skor": skor(k, s, tema, ileri)[0], "secildi": dt.date.today().isoformat()}
    if a.yaz:
        json.dump(P, open(PLAN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("yazıldı:", PLAN)
    return 0


def liste(a):
    konular = json.load(open(HAVUZ, encoding="utf-8"))["konular"]
    S = sinyaller(konular)
    tema = hafta(dt.date.today())["theme"].lower()
    for k in sorted(konular, key=lambda k: -skor(k, S[k["id"]], tema)[0]):
        s = S[k["id"]]
        print(f"{k['id']:<22}{skor(k, s, tema)[0]:>6}  hacim {s['hacim']:<7} ivme {s['ivme']:<7} yt {s['yt']:<3} {k['baslik']}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("plan"); p.add_argument("--hafta", default=""); p.add_argument("--yaz", action="store_true"); p.set_defaults(f=plan)
    p = sp.add_parser("liste"); p.set_defaults(f=liste)
    a = ap.parse_args()
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
