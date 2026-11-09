#!/usr/bin/env python3
"""ParaFOMO — Search Console fırsat analizi (2026-11-09, R24). Mantık Suganthans-GSC-MCP (Apache-2.0) analizlerinden
uyarlandı; MCP sunucusu kurmadan, mevcut servis hesabıyla (scripts/gsc-sitemap.py client()).

Üç rapor (son 28 gün, GSC ~2 gün gecikmeli):
  1. YAKIN FIRSAT  — 4-20. sıradaki sorgu+sayfa, gösterimi yüksek: başlık/iç link/içerikle ilk 3'e itilebilir
  2. YAMYAMLAŞMA   — aynı sorguda ≥2 sayfamız gösterim alıyor: biri ötekini yiyor (birleştir / ayır / kanonik)
  3. DÜŞÜŞ         — önceki 28 güne göre tık/gösterimi belirgin düşen sayfalar (içerik çürümesi / sıra kaybı)
Çıktı: stdout metni + --json dosyası (sabah CEO raporu bunu okur).
"""
import argparse, collections, datetime as dt, importlib.util, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location("g", os.path.join(ROOT, "scripts", "gsc-sitemap.py"))
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
SITE = getattr(g, "SITE", None) or "sc-domain:parafomo.com"


def q(svc, s, e, dims, n=5000):
    rows, start = [], 0
    while True:
        r = svc.searchanalytics().query(siteUrl=SITE, body={"startDate": str(s), "endDate": str(e), "dimensions": dims,
                                                            "rowLimit": n, "startRow": start}).execute().get("rows", [])
        rows += r
        if len(r) < n:
            return rows
        start += n


def short(u):
    return u.replace("https://parafomo.com", "") or "/"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="")
    ap.add_argument("--top", type=int, default=12)
    a = ap.parse_args()
    svc = g.client()
    end = dt.date.today() - dt.timedelta(days=2)
    s1 = end - dt.timedelta(days=27); e0 = s1 - dt.timedelta(days=1); s0 = e0 - dt.timedelta(days=27)

    qp = q(svc, s1, end, ["query", "page"])
    # 1) yakın fırsat: sıra 4-20, gösterim ≥ 15; potansiyel = gösterim × (ilk-3 TO ~%10 − mevcut TO)
    yakin = []
    for r in qp:
        pos, imp, clk = r["position"], r["impressions"], r["clicks"]
        if 4 <= pos <= 20 and imp >= 15:
            pot = imp * max(0.0, 0.10 - clk / imp)
            yakin.append({"sorgu": r["keys"][0], "sayfa": short(r["keys"][1]), "sira": round(pos, 1),
                          "gosterim": int(imp), "tik": int(clk), "potansiyel_tik": round(pot, 1)})
    yakin.sort(key=lambda x: -x["potansiyel_tik"])

    # 2) yamyamlaşma: aynı sorguda ≥2 sayfa, her biri ≥5 gösterim, sorgu toplamı ≥20
    by_q = collections.defaultdict(list)
    for r in qp:
        if r["impressions"] >= 5:
            by_q[r["keys"][0]].append(r)
    yamyam = []
    for qq, rs in by_q.items():
        if len(rs) >= 2 and sum(x["impressions"] for x in rs) >= 20:
            rs.sort(key=lambda x: -x["impressions"])
            yamyam.append({"sorgu": qq, "toplam_gosterim": int(sum(x["impressions"] for x in rs)),
                           "sayfalar": [{"sayfa": short(x["keys"][1]), "gosterim": int(x["impressions"]),
                                         "sira": round(x["position"], 1)} for x in rs[:4]]})
    yamyam.sort(key=lambda x: -x["toplam_gosterim"])

    # 3) düşüş: sayfa bazında önceki 28 gün vs son 28 gün
    now = {r["keys"][0]: r for r in q(svc, s1, end, ["page"])}
    prev = {r["keys"][0]: r for r in q(svc, s0, e0, ["page"])}
    dusus = []
    for p, r0 in prev.items():
        r1 = now.get(p, {"clicks": 0, "impressions": 0, "position": 0})
        dc, di = r1["clicks"] - r0["clicks"], r1["impressions"] - r0["impressions"]
        if (r0["clicks"] >= 4 and r1["clicks"] <= r0["clicks"] * 0.6) or (r0["impressions"] >= 150 and r1["impressions"] <= r0["impressions"] * 0.5):
            dusus.append({"sayfa": short(p), "tik": f"{int(r0['clicks'])}→{int(r1['clicks'])}",
                          "gosterim": f"{int(r0['impressions'])}→{int(r1['impressions'])}",
                          "sira": f"{r0['position']:.0f}→{r1['position']:.0f}" if r1.get("position") else "kayıp", "_d": dc * 10 + di / 10})
    dusus.sort(key=lambda x: x["_d"])
    for d in dusus:
        d.pop("_d")

    out = {"donem": f"{s1}..{end}", "yakin_firsat": yakin[:a.top], "yamyamlasma": yamyam[:a.top], "dusus": dusus[:a.top]}
    print(f"GSC FIRSAT RAPORU {out['donem']}")
    print("\n1) YAKIN FIRSAT (4-20. sıra; potansiyel = ilk 3'e çıkarsa ek tık)")
    for x in out["yakin_firsat"]:
        print(f"  +{x['potansiyel_tik']:>5}  p{x['sira']:<5} {x['gosterim']:>4} gös  {x['sorgu'][:48]:<48} {x['sayfa']}")
    print("\n2) YAMYAMLAŞMA (aynı sorguda birden çok sayfamız)")
    for x in out["yamyamlasma"]:
        print(f"  {x['toplam_gosterim']:>4} gös  {x['sorgu'][:50]}")
        for s in x["sayfalar"]:
            print(f"        p{s['sira']:<5} {s['gosterim']:>4}  {s['sayfa']}")
    print("\n3) DÜŞÜŞ (önceki 28 gün → son 28 gün)")
    for x in out["dusus"]:
        print(f"  tık {x['tik']:<8} gös {x['gosterim']:<10} sıra {x['sira']:<7} {x['sayfa']}")
    if a.json:
        json.dump(out, open(a.json, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
