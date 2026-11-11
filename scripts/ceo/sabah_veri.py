#!/usr/bin/env python3
"""ParaFOMO — sabah CEO raporu VERİ toplayıcı (2026-11-09, Kaan: "her sabah sitenin gelişimi, eksik yerleri, verimliliği").

Her sabah Claude oturumu bunu çalıştırır, çıkan /root/parafomo-data/ceo/<gün>.md dosyasını okur, üzerine yorum +
yeni fikirler + Kaan'ın sıralı görevlerini yazar. Bölümler birbirinden bağımsız: biri çökerse "HATA" yazılır, gerisi sürer.

Araçlar (repo dışı, /root/seo-tools): lychee 0.24.2 (kırık link), lhci 0.15.1 (hız), sdv (Adobe JSON-LD doğrulayıcı),
/root/video-lab/seo/venv-geo (GEO puanı, haftada bir). Repo içi: scripts/seo/gsc_firsat.py, scripts/bots/cf_bots.py.
"""
import datetime as dt, json, os, subprocess, sys, traceback

ROOT = "/root/parafomo"
OUTDIR = "/root/parafomo-data/ceo"
PY = "/root/.venvs/parafomo/bin/python"
TOOLS = "/root/seo-tools"
CHROME = "/root/.cache/ms-playwright/chromium_headless_shell-1148/chrome-linux/headless_shell"
BUGUN = dt.date.today()
HAFTA_GUNU = BUGUN.weekday()   # 0 = Pazartesi
AI_KAYNAK = ("chatgpt", "openai", "perplexity", "gemini", "copilot", "claude", "deepseek", "grok", "you.com")


def sh(cmd, timeout=900, cwd=ROOT, env=None):
    r = subprocess.run(["nice", "-n", "19"] + cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                       env={**os.environ, **(env or {})})
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def ga4():
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
    from google.oauth2 import service_account
    c = BetaAnalyticsDataClient(credentials=service_account.Credentials.from_service_account_file(
        os.path.expanduser("~/.config/parafomo/ga-sa.json")))
    P = "properties/542292605"

    def rep(s, e):
        r = c.run_report(RunReportRequest(property=P, date_ranges=[DateRange(start_date=s, end_date=e)],
                                          dimensions=[Dimension(name="sessionSource")],
                                          metrics=[Metric(name="sessions"), Metric(name="activeUsers")], limit=100))
        out = {}
        for row in r.rows:
            out[row.dimension_values[0].value] = int(row.metric_values[0].value)
        return out
    a, b = rep("7daysAgo", "yesterday"), rep("14daysAgo", "8daysAgo")
    grp = lambda d: {
        "google": d.get("google", 0), "dogrudan": d.get("(direct)", 0),
        "yapay_zeka": sum(v for k, v in d.items() if any(x in k for x in AI_KAYNAK)),
        "sosyal": sum(v for k, v in d.items() if any(x in k for x in ("facebook", "instagram", "youtube", "t.co", "x.com"))),
        "diger_arama": sum(v for k, v in d.items() if any(x in k for x in ("bing", "yandex", "duckduckgo", "yahoo"))),
        "toplam": sum(d.values())}
    ga, gb = grp(a), grp(b)
    lines = ["| Kaynak | Son 7 gün | Önceki 7 gün |", "|---|---|---|"]
    for k in ("toplam", "google", "yapay_zeka", "dogrudan", "sosyal", "diger_arama"):
        lines.append(f"| {k} | {ga[k]} | {gb[k]} |")
    ai = sorted(((k, v) for k, v in a.items() if any(x in k for x in AI_KAYNAK)), key=lambda x: -x[1])
    lines.append(f"\nYapay zekâ kaynakları (7g): {', '.join(f'{k} {v}' for k, v in ai) or 'yok'}")
    return "\n".join(lines)


def gsc_hafta():
    import importlib.util
    spec = importlib.util.spec_from_file_location("g", f"{ROOT}/scripts/gsc-sitemap.py")
    g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
    svc = g.client(); site = getattr(g, "SITE", None) or "sc-domain:parafomo.com"
    end = BUGUN - dt.timedelta(days=2)
    lines = ["| Hafta | Tık | Gösterim | Ort. sıra |", "|---|---|---|---|"]
    for w in range(4, 0, -1):
        e = end - dt.timedelta(days=7 * (w - 1)); s = e - dt.timedelta(days=6)
        r = svc.searchanalytics().query(siteUrl=site, body={"startDate": str(s), "endDate": str(e)}).execute().get("rows", [{}])[0]
        lines.append(f"| {s:%d.%m}–{e:%d.%m} | {r.get('clicks', 0):.0f} | {r.get('impressions', 0):.0f} | {r.get('position', 0):.1f} |")
    return "\n".join(lines)


def gsc_firsat():
    js = f"{OUTDIR}/gsc-firsat-{BUGUN}.json"
    code, out = sh([PY, f"{ROOT}/scripts/seo/gsc_firsat.py", "--top", "8", "--json", js], timeout=600)
    return "```\n" + out.strip()[-4000:] + "\n```"


def linkler():
    if not os.path.isdir(f"{ROOT}/dist"):
        return "dist/ yok (build yapılmamış)"
    code, out = sh([f"{TOOLS}/bin/lychee", "--offline", "--no-progress", "--root-dir", f"{ROOT}/dist", "dist/**/*.html"], timeout=900)
    ozet = [l for l in out.splitlines() if any(k in l for k in ("Total", "Errors", "Successful", "✗", "[ERR]", "ERROR"))][:25]
    res = "İç linkler (dist/, çevrimdışı):\n```\n" + "\n".join(ozet) + "\n```"
    if HAFTA_GUNU == 6:   # Pazar: dış linkler (ağ, yavaş)
        code, out = sh([f"{TOOLS}/bin/lychee", "--no-progress", "--cache", "--max-concurrency", "8", "--timeout", "20",
                        "--exclude", "parafomo\\.com", "--accept", "200..=299,403,429", "dist/**/*.html"], timeout=2400)
        hata = [l for l in out.splitlines() if l.startswith("[") and ("ERR" in l or "4" in l[:6] or "5" in l[:6])][:30]
        res += "\nDış linkler (haftalık):\n```\n" + "\n".join(hata or ["kırık dış link yok"]) + "\n```"
    return res


def yapisal_veri():
    code, out = sh(["node", f"{TOOLS}/sdv/validate.mjs", f"{ROOT}/dist"], timeout=900, cwd=f"{TOOLS}/sdv")
    return "```\n" + "\n".join(out.strip().splitlines()[:25]) + "\n```"


def hiz():
    # video render kilidini bekle: render sırasında ölçüm 2 çekirdekte LCP'yi ikiye katlıyor (2026-11-11: 2,9 sn → 5,0 sn)
    code, out = sh(["flock", "-w", "1200", "/tmp/shorts_frames.lock", f"{TOOLS}/lhci/node_modules/.bin/lhci", "autorun", f"--config={TOOLS}/lhci/lighthouserc.json"],
                   timeout=1500, cwd=f"{TOOLS}/lhci", env={"CHROME_PATH": CHROME})
    m = json.load(open(f"{TOOLS}/lhci/reports/manifest.json"))
    lines = ["| Sayfa | Perf | SEO | Erişilebilirlik | LCP | CLS |", "|---|---|---|---|---|---|"]
    for r in m:
        s = r["summary"]; a = json.load(open(r["jsonPath"]))["audits"]
        path = "/" + r["url"].split("/", 3)[-1]
        lines.append(f"| {path} | {s['performance']:.2f} | {s['seo']:.2f} | {s['accessibility']:.2f} | "
                     f"{a['largest-contentful-paint']['numericValue'] / 1000:.1f}s | {a['cumulative-layout-shift']['numericValue']:.3f} |")
    return "\n".join(lines) + "\n(laboratuvar ölçümü: yavaş mobil simülasyonu, 2 çekirdekli sunucu — eğilim için)"


def botlar():
    d = "/root/parafomo-data/bots"
    if not os.path.isdir(d) or not os.listdir(d):
        return "Arşiv boş — Cloudflare Zone·Analytics·Read izni bekleniyor (Kaan görevi)."
    code, out = sh([PY, f"{ROOT}/scripts/bots/cf_bots.py", "report", "--days", "7"], timeout=300)
    return "```\n" + out.strip()[:4000] + "\n```"


def geo():
    if HAFTA_GUNU != 0:
        return "(haftalık — Pazartesi ölçülür)"
    rows = []
    for u in ("https://parafomo.com/", "https://parafomo.com/altin-fiyatlari/", "https://parafomo.com/kira-artis-orani-hesaplama/",
              "https://parafomo.com/evde-bakim-maasi/"):
        code, out = sh(["/root/video-lab/seo/venv-geo/bin/geo", "audit", "--url", u, "--format", "text", "--no-plugins"],
                       timeout=300, cwd=OUTDIR)
        sc = next((l.strip() for l in out.splitlines() if "/100" in l and "[" in l and "█" in l), "?")
        ls = out.splitlines()
        i = next((k for k, l in enumerate(ls) if "PRIORITY NEXT STEPS" in l), len(ls))
        nxt = [l.strip() for l in ls[i + 1:i + 6] if l.strip()[:2].rstrip(".").isdigit()][:3]
        rows.append(f"- {u.replace('https://parafomo.com', '') or '/'}: {sc.split(']')[-1].strip()} — " + " | ".join(nxt))
    return "\n".join(rows)


def resmi_gazete():
    code, out = sh([PY, f"{ROOT}/scripts/watch/resmi_gazete.py", "--gun", "3"], timeout=300)
    return "```\n" + out.strip()[-3000:] + "\n```\n(⚑ varsa: metni aç, doğrula, ilgili data/*.json'u güncelle — betik rakam değiştirmez)"


def build_denetim():
    d = json.load(open(f"{ROOT}/data/learning/seo-audit.json"))
    lab = {k: v.get("label", k) for k, v in d.get("codes", {}).items()}
    by = ", ".join(f"{lab.get(k, k)} {n}" for k, n in sorted(d.get("by_code", {}).items(), key=lambda x: -x[1]))
    c = d.get("counts", {})
    return f"{d.get('generated', '?')[:16]} · {d.get('pages', '?')} sayfa · KRİTİK {c.get('KRİTİK', 0)} · UYARI {c.get('UYARI', 0)} · BİLGİ {c.get('BİLGİ', 0)}\nDağılım: {by}"


def kaan_gorevleri():
    t = open(f"{ROOT}/agent/plan/user-tasks.md").read()
    items = [l for l in t.splitlines() if l[:3].strip().rstrip(".").isdigit() and "**" in l]
    return "\n".join(items) or "açık görev yok"


BOLUMLER = [("Trafik (GA4, 7g vs önceki 7g)", ga4), ("Google arama (GSC, haftalık)", gsc_hafta),
            ("SEO fırsatları (GSC)", gsc_firsat), ("Botlar (Cloudflare)", botlar), ("Resmî Gazete bekçisi", resmi_gazete), ("GEO puanı", geo),
            ("Kırık linkler", linkler), ("Yapısal veri (JSON-LD)", yapisal_veri), ("Hız (Lighthouse CI)", hiz),
            ("Build SEO denetimi", build_denetim), ("Kaan'ın açık görevleri (user-tasks.md)", kaan_gorevleri)]


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    only = set(sys.argv[1:])
    parts = [f"# ParaFOMO sabah verisi — {BUGUN}\n"]
    for ad, fn in BOLUMLER:
        if only and not any(o.lower() in ad.lower() for o in only):
            continue
        t0 = dt.datetime.now()
        try:
            body = fn()
        except Exception as e:
            body = f"HATA: {type(e).__name__}: {e}\n```\n{traceback.format_exc()[-800:]}\n```"
        parts.append(f"## {ad}  _( {(dt.datetime.now() - t0).seconds} sn)_\n{body}\n")
        print(f"[ceo] {ad}: {(dt.datetime.now() - t0).seconds} sn", flush=True)
    fn = f"{OUTDIR}/{BUGUN}.md"
    open(fn, "w").write("\n".join(parts))
    print(f"[ceo] ✅ {fn}")


if __name__ == "__main__":
    main()
