#!/usr/bin/env python3
"""
ParaFOMO Ajanı v2 — BRIEF (token'sız durum özeti; ajanın tek bağlam kaynağı).

Eski digest ~90 KB'tı (her gece ~30K token sadece okumak için) ve aynı bilgiyi
3-4 kez tekrar ediyordu. Brief odaklıdır: skor kartı, sağlık, plan, bahisler,
dersler, fırsatlar. Detay gerekiyorsa ajan kendisi hedefli sorgu yapar.

Yan etkiler (kasıtlı):
  - agent/state/kpi.json            → e-postanın KPI satırı
  - agent/memory/kpi-daily.jsonl     → günlük KPI zaman serisi (tarihe göre tekil)

Kullanım: /root/.venvs/parafomo/bin/python agent/brief.py --mode daily|weekly
"""
import datetime as dt
import importlib.util
import json
import time
import logging
import os
import re
import statistics
import subprocess
import sys
from collections import defaultdict

logging.getLogger("google.auth").setLevel(logging.ERROR)
logging.getLogger("googleapiclient").setLevel(logging.ERROR)

ROOT = "/root/parafomo"
AG = os.path.join(ROOT, "agent")
STATE = os.path.join(AG, "state")
MEM = os.path.join(AG, "memory")
PLAN = os.path.join(AG, "plan")
LEARN = os.path.join(ROOT, "data", "learning")
sys.path.insert(0, AG)

TODAY = dt.date.today()
MODE = "weekly" if "--mode" in sys.argv and sys.argv[sys.argv.index("--mode") + 1] == "weekly" else "daily"
WEEKS = 8 if MODE == "weekly" else 4
KPI = {}


def out(s=""):
    print(s)


def section(title, fn):
    out(f"## {title}")
    try:
        fn()
    except Exception as e:
        out(f"_(alınamadı: {type(e).__name__}: {str(e)[:160]})_")
    out()


def _dash():
    spec = importlib.util.spec_from_file_location("dashboard", os.path.join(ROOT, "scripts", "dashboard.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


DASH = None
GA = None
SC = None


def clients():
    global DASH, GA, SC
    if DASH is None:
        DASH = _dash()
    if GA is None:
        try:
            GA = DASH.ga4_client()
        except Exception:
            GA = False
    if SC is None:
        try:
            SC = DASH.gsc_client()
        except Exception:
            SC = False
    return DASH, GA, SC


def ga_report(dims, start, end, metrics=("activeUsers",), limit=500, dim_filter=None):
    from google.analytics.data_v1beta.types import (RunReportRequest, DateRange, Dimension,
                                                    Metric, FilterExpression, Filter)
    _, ga, _ = clients()
    if not ga:
        raise RuntimeError("GA4 istemcisi yok")
    kw = dict(property=f"properties/{DASH.GA4_PROPERTY}",
              date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
              dimensions=[Dimension(name=d) for d in dims],
              metrics=[Metric(name=m) for m in metrics], limit=limit)
    if dim_filter:
        name, value = dim_filter
        kw["dimension_filter"] = FilterExpression(filter=Filter(
            field_name=name, string_filter=Filter.StringFilter(value=value)))
    res = ga.run_report(RunReportRequest(**kw))
    return [([d.value for d in r.dimension_values], [float(m.value) for m in r.metric_values]) for r in res.rows]


def gsc(dims, start, end, limit=1000):
    _, _, sc = clients()
    if not sc:
        raise RuntimeError("GSC istemcisi yok")
    return DASH.gsc_daily(sc, start, end, dims, limit)


# ------------------------------------------------------------------ 1) skor kartı
def sec_scorecard():
    # GA4: ISO hafta × kanal
    start = TODAY - dt.timedelta(weeks=WEEKS, days=TODAY.weekday())
    ga_rows = ga_report(["isoYearIsoWeek", "sessionDefaultChannelGroup"], start, TODAY)
    wk = defaultdict(lambda: defaultdict(int))
    for (w, ch), (u,) in ga_rows:
        wk[w][ch or "(other)"] += int(u)
    # GSC: günlük → ISO hafta
    g_rows = gsc(["date"], start, TODAY)
    gw = defaultdict(lambda: [0, 0])
    last_gsc_day = None
    for r in g_rows:
        d = dt.date.fromisoformat(r["keys"][0])
        iy, iw, _ = d.isocalendar()
        key = f"{iy}{iw:02d}"
        gw[key][0] += int(r["clicks"])
        gw[key][1] += int(r["impressions"])
        last_gsc_day = max(last_gsc_day or d, d)
    # YouTube: yayın haftası → video sayısı + medyan izlenme
    yv = yt_videos()
    yw = defaultdict(list)
    for v in yv:
        if v["date"]:
            iy, iw, _ = dt.date.fromisoformat(v["date"]).isocalendar()
            yw[f"{iy}{iw:02d}"].append(v["views"])
    weeks = sorted(set(list(wk.keys()) + list(gw.keys())))[-(WEEKS + 1):]
    cur_iy, cur_iw, _ = TODAY.isocalendar()
    cur = f"{cur_iy}{cur_iw:02d}"
    out("| ISO hafta | Gerçek erişim (Direct hariç) | Organic Search | GSC tık | GSC gös | Yeni video | Video medyan izl. |")
    out("|---|---|---|---|---|---|---|")
    for w in weeks:
        ch = wk.get(w, {})
        real = sum(v for k, v in ch.items() if k != "Direct")
        org = ch.get("Organic Search", 0)
        c, i = gw.get(w, [0, 0])
        vids = yw.get(w, [])
        med = int(statistics.median(vids)) if vids else "-"
        tag = " (kısmi)" if w == cur else ""
        out(f"| {w}{tag} | {real} | {org} | {c} | {i} | {len(vids)} | {med} |")
    out(f"\n_GSC verisi {last_gsc_day} gününe kadar (Google ~2-3 gün gecikmeli). Kısmi haftayı tam haftayla kıyaslama. "
        f"Video medyanı = o hafta yayınlanan videoların BUGÜNKÜ izlenmesi (eski haftalar avantajlı)._")


def sec_kpi_snapshot():
    """Kayan pencere KPI'ları (kısmi-hafta artefaktı yok) → kpi.json + kpi-daily.jsonl."""
    y = TODAY - dt.timedelta(days=1)
    def ga_window(days):
        rows = ga_report(["sessionDefaultChannelGroup"], TODAY - dt.timedelta(days=days), y)
        return {r[0][0]: int(r[1][0]) for r in rows}
    g7, g28 = ga_window(7), ga_window(28)
    gl = TODAY - dt.timedelta(days=3)  # GSC gecikmesi
    def gsc_window(days):
        rows = gsc(["date"], gl - dt.timedelta(days=days - 1), gl)
        return sum(int(r["clicks"]) for r in rows), sum(int(r["impressions"]) for r in rows)
    c7, i7 = gsc_window(7)
    c28, i28 = gsc_window(28)
    yt = {}
    for _ in range(2):  # YouTube API ara sıra geçici hata veriyor → KPI'ya null düşmesin
        try:
            _, yt = DASH.yt_section()
        except Exception:
            yt = {}
        if yt:
            break
        time.sleep(5)
    snap = {"date": TODAY.isoformat(),
            "real_7d": sum(v for k, v in g7.items() if k != "Direct"),
            "direct_7d": g7.get("Direct", 0),
            "organic_search_7d": g7.get("Organic Search", 0),
            "real_28d": sum(v for k, v in g28.items() if k != "Direct"),
            "ai_assistant_28d": g28.get("AI Assistant", 0),
            "organic_social_28d": g28.get("Organic Social", 0),
            "gsc_clicks_7d": c7, "gsc_impr_7d": i7, "gsc_clicks_28d": c28, "gsc_impr_28d": i28,
            "yt_subs": yt.get("subs"), "yt_views": yt.get("views"), "yt_videos": yt.get("videos")}
    KPI.update(snap)
    os.makedirs(STATE, exist_ok=True)
    json.dump(snap, open(os.path.join(STATE, "kpi.json"), "w", encoding="utf-8"), ensure_ascii=False)
    hist = os.path.join(MEM, "kpi-daily.jsonl")
    rows = []
    if os.path.exists(hist):
        rows = [json.loads(l) for l in open(hist, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r.get("date") != snap["date"]] + [snap]
    with open(hist, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    # bugün vs 7 gün önce
    prev = next((r for r in reversed(rows[:-1]) if r["date"] <= (TODAY - dt.timedelta(days=7)).isoformat()), None)
    def d(k):
        if not prev or prev.get(k) is None or snap.get(k) is None:
            return ""
        diff = snap[k] - prev[k]
        return f" ({'+' if diff >= 0 else ''}{diff} / 7g)"
    out(f"- **Gerçek erişim (Direct hariç), son 7 gün:** {snap['real_7d']}{d('real_7d')} · "
        f"Organic Search {snap['organic_search_7d']} · Direct {snap['direct_7d']} · hedef 7000/hafta "
        f"(%{snap['real_7d'] / 70:.1f})")
    out(f"- **Son 28 gün:** gerçek erişim {snap['real_28d']} · AI asistan {snap['ai_assistant_28d']} · "
        f"Organic Social {snap['organic_social_28d']}")
    out(f"- **GSC (gecikmeli, {gl} dahil):** 7g {c7} tık / {i7} gös{d('gsc_clicks_7d')} · 28g {c28} tık / {i28} gös")
    if yt:
        out(f"- **YouTube:** {yt.get('subs')} abone{d('yt_subs')} · {yt.get('views'):,} toplam izlenme{d('yt_views')} · "
            f"{yt.get('videos')} video")



# ------------------------------------------------------------------ 1b) kanal + dağıtım
def _kpi_merge(fields):
    """Bugünün KPI satırına kanal metriklerini ekle (kpi.json + kpi-daily.jsonl)."""
    if not fields:
        return
    KPI.update(fields)
    try:
        json.dump(KPI, open(os.path.join(STATE, "kpi.json"), "w", encoding="utf-8"), ensure_ascii=False)
    except Exception:
        pass
    hist = os.path.join(MEM, "kpi-daily.jsonl")
    if not os.path.exists(hist):
        return
    rows = [json.loads(l) for l in open(hist, encoding="utf-8") if l.strip()]
    for r in rows:
        if r.get("date") == TODAY.isoformat():
            r.update(fields)
    with open(hist, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _meta_env():
    env = {}
    try:
        for ln in open(os.path.expanduser("~/.config/parafomo/instagram.env"), encoding="utf-8"):
            if "=" in ln and not ln.lstrip().startswith("#"):
                k, v = ln.strip().split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return env


def sec_channels():
    """Darboğazı doğru kanalda görmek için (RC 2026-10-28): YouTube arama payı + abone dönüşümü, IG/FB takipçi,
    Discover/News, Google'ın gizlediği uzun-kuyruk sorgu payı, geri dönen ziyaretçi, paylaşım butonu trafiği,
    olay sonucu Short'ları. Tümü kpi-daily.jsonl'a da yazılır (haftalık koşu trendi görür)."""
    import urllib.parse
    import urllib.request
    y = TODAY - dt.timedelta(days=1)
    s28 = TODAY - dt.timedelta(days=28)
    f, lines = {}, []
    # YouTube (28g) — trafik kaynağı + abone dönüşümü
    try:
        sys.path.insert(0, os.path.join(ROOT, "scripts", "learn"))
        import lib as _lib
        from googleapiclient.discovery import build
        yc = _lib.youtube_credentials(["https://www.googleapis.com/auth/youtube.readonly",
                                       "https://www.googleapis.com/auth/yt-analytics.readonly"])
        ya = build("youtubeAnalytics", "v2", credentials=yc, cache_discovery=False)

        def q(**kw):
            return ya.reports().query(ids="channel==MINE", startDate=s28.isoformat(), endDate=y.isoformat(),
                                      **kw).execute().get("rows") or []
        tot = q(metrics="views,subscribersGained,subscribersLost")
        src = {r[0]: r[1] for r in q(metrics="views", dimensions="insightTrafficSourceType")}
        v, sg, sl = (tot[0] if tot else [0, 0, 0])
        allv = sum(src.values()) or 1
        f.update({"yt_views_28d": int(v), "yt_subs_gained_28d": int(sg),
                  "yt_subs_per_1k": round(sg / max(v, 1) * 1000, 2),
                  "yt_search_share": round(src.get("YT_SEARCH", 0) / allv * 100, 1),
                  "yt_shorts_feed_share": round(src.get("SHORTS", 0) / allv * 100, 1)})
        lines.append(f"- **YouTube (28g):** {int(v):,} izlenme · +{int(sg)} / −{int(sl)} abone → "
                     f"**{f['yt_subs_per_1k']} abone / 1000 izlenme** · kaynak: Shorts akışı %{f['yt_shorts_feed_share']}"
                     f" · **YouTube araması %{f['yt_search_share']}** · dış link %{round(src.get('EXT_URL', 0) / allv * 100, 1)}")
        terms = q(metrics="views", dimensions="insightTrafficSourceDetail",
                  filters="insightTrafficSourceType==YT_SEARCH", sort="-views", maxResults=15)
        if terms:
            lines.append("- **YouTube'da bizi bulduran aramalar (28g, izlenme)** — video konusu/başlığı bu kalıplardan: "
                         + " · ".join(f"{t[0]} {int(t[1])}" for t in terms))
            try:  # gece viral senaryo üreticisi (viral-script.py) konu seçerken okur
                json.dump({"generated": TODAY.isoformat(), "terms": [[t[0], int(t[1])] for t in terms]},
                          open(os.path.join(LEARN, "yt-search-terms.json"), "w", encoding="utf-8"), ensure_ascii=False)
            except Exception:
                pass
    except Exception as e:
        lines.append(f"- YouTube kanal metrikleri alınamadı: {type(e).__name__}")
    # Instagram + Facebook takipçi
    env = _meta_env()
    tok = env.get("IG_PAGE_TOKEN")

    def graph(obj, fields):
        u = f"https://graph.facebook.com/v21.0/{obj}?" + urllib.parse.urlencode({"fields": fields, "access_token": tok})
        return json.load(urllib.request.urlopen(u, timeout=20))
    meta = []
    try:
        ig = graph(env["IG_BUSINESS_ACCOUNT_ID"], "followers_count,media_count")
        f.update({"ig_followers": ig.get("followers_count"), "ig_media": ig.get("media_count")})
        meta.append(f"Instagram {ig.get('followers_count')} takipçi / {ig.get('media_count')} gönderi")
    except Exception as e:
        meta.append(f"Instagram okunamadı ({type(e).__name__})")
    try:
        fb = graph(env["IG_PAGE_ID"], "followers_count,fan_count")
        f["fb_followers"] = fb.get("followers_count")
        st = {}
        try:
            st = json.load(open(os.path.join(ROOT, "logs", "fb-status.json"), encoding="utf-8"))
        except Exception:
            pass
        perm = "paylaşım AÇIK" if st.get("ok") else "paylaşım izni YOK (pages_manage_posts — Kaan görevi)"
        meta.append(f"Facebook sayfası {fb.get('followers_count')} takipçi · {perm}")
    except Exception as e:
        meta.append(f"Facebook okunamadı ({type(e).__name__})")
    lines.append("- **Sosyal:** " + " · ".join(meta))
    # GSC: Discover / Google News / gizli uzun-kuyruk payı (28g)
    try:
        _, _, sc = clients()
        site = DASH.GSC_SITE

        def gq(body):
            body = {"startDate": s28.isoformat(), "endDate": y.isoformat(), **body}
            return sc.searchanalytics().query(siteUrl=site, body=body).execute().get("rows", [])
        disc = gq({"type": "discover"})
        news = gq({"type": "googleNews"})
        web = gq({"type": "web"})
        withq = gq({"type": "web", "dimensions": ["query"], "rowLimit": 25000})
        tc = sum(r["clicks"] for r in web)
        qc = sum(r["clicks"] for r in withq)
        di = int(sum(r["impressions"] for r in disc)); dc = int(sum(r["clicks"] for r in disc))
        ni = int(sum(r["impressions"] for r in news))
        f.update({"discover_impr_28d": di, "discover_clicks_28d": dc, "gnews_impr_28d": ni,
                  "gsc_hidden_click_share": round((tc - qc) / max(tc, 1) * 100, 1)})
        lines.append(f"- **Google yüzeyleri (28g):** Discover {di} gös / {dc} tık · Google News {ni} gös · "
                     f"tıkların **%{f['gsc_hidden_click_share']}**'i Google'ın gizlediği nadir (uzun-kuyruk) sorgulardan "
                     f"→ büyüme baş sorgudan değil, sayfa × uzun-kuyruk yüzeyinden geliyor")
    except Exception as e:
        lines.append(f"- GSC yüzey metrikleri alınamadı: {type(e).__name__}")
    # GA4: geri dönen ziyaretçi + sosyal kaynak + paylaş butonu
    try:
        nv = {r[0][0]: int(r[1][0]) for r in ga_report(["newVsReturning"], s28, y)}
        soc = sorted(((r[0][0], int(r[1][0])) for r in ga_report(["sessionSource"], s28, y,
                      dim_filter=("sessionDefaultChannelGroup", "Organic Social"))), key=lambda x: -x[1])
        sh = sorted(((r[0][0], int(r[1][0])) for r in ga_report(["sessionSource"], s28, y,
                     dim_filter=("sessionCampaignName", "share"))), key=lambda x: -x[1])
        f.update({"returning_28d": nv.get("returning", 0), "share_visits_28d": sum(v for _, v in sh)})
        lines.append(f"- **Sadakat + paylaşım (28g):** geri dönen {nv.get('returning', 0)} / yeni {nv.get('new', 0)} · "
                     f"Organic Social kaynakları: " + (", ".join(f"{k} {v}" for k, v in soc[:5]) or "yok")
                     + " · paylaş butonundan gelen: " + (", ".join(f"{k} {v}" for k, v in sh[:5]) or "henüz yok"))
    except Exception as e:
        lines.append(f"- GA4 sadakat/sosyal alınamadı: {type(e).__name__}")
    # Olay sonucu Short'ları
    try:
        st = json.load(open(os.path.join(ROOT, "logs", "event-shorts.json"), encoding="utf-8"))
        last = sorted(((k, v) for k, v in st.items() if not k.startswith("_") and v.get("status") != "skip"),
                      key=lambda kv: kv[1].get("ts", ""))[-4:]
        if not last:
            raise ValueError("kayıt yok")
        lines.append("- **Olay sonucu Short'ları** (scripts/event-short.py): " + " · ".join(
            f"{k} {v.get('status')}" + (f" {v.get('youtube_url')}" if v.get("youtube_url") else "") for k, v in last))
    except Exception:
        lines.append("- **Olay sonucu Short'ları** (scripts/event-short.py): henüz yok — ilk olay: Fed 28 Ekim / TÜİK 3 Kasım")
    _kpi_merge(f)
    out("\n".join(lines))


# ------------------------------------------------------------------ 4) plan (sıkıştırılmış) + yol haritası
TR_AY = {a: i + 1 for i, a in enumerate(["ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz",
                                         "ağustos", "eylül", "ekim", "kasım", "aralık"])}


def _due_date(label):
    """'(B.. — TARİHLİ, 29 Ekim sabahı)' → date; tarih yoksa None. Yıl: geçmiş ay ise gelecek yıl."""
    m = re.search(r"(\d{1,2})\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)(?:\s+(\d{4}))?",
                  label)
    if not m:
        return None
    d, mo = int(m.group(1)), TR_AY[m.group(2).lower()]
    yr = int(m.group(3)) if m.group(3) else (TODAY.year + 1 if mo < TODAY.month - 2 else TODAY.year)
    try:
        return dt.date(yr, mo, d)
    except ValueError:
        return None


def sec_week():
    """week.md — biten görevlerin uzun metni tek satıra iner (brief'in ~%20'si eski görev metniydi);
    üstte kuyruk derinliği: yapılabilir görev yoksa ajan roadmap.md'den iş çeker (boş koşu yok)."""
    p = os.path.join(PLAN, "week.md")
    if not os.path.exists(p):
        out("(plan yok — haftalık koşu oluşturmalı)")
        return
    lines = open(p, encoding="utf-8").read().rstrip().splitlines()
    # görev blokları: "- [ ] ..." satırı + ardından gelen girintili devam satırları
    blocks, i = [], 0
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"^- \[([ xX-])\] (.*)$", ln)
        if not m:
            blocks.append(("text", ln, [])); i += 1
            continue
        cont = []
        i += 1
        while i < len(lines) and lines[i].startswith("  ") and not re.match(r"^- \[", lines[i]):
            cont.append(lines[i]); i += 1
        blocks.append((m.group(1), ln, cont))
    res, open_now, open_later, open_unknown = [], [], [], []
    for state, ln, cont in blocks:
        if state == "text":
            res.append(ln)
            continue
        body = ln[6:] + " " + " ".join(c.strip() for c in cont)
        tid = (re.match(r"([A-Z][A-Za-z]*-?[A-Za-z0-9]*\d[A-Za-z0-9]*)", body) or [None])[0]
        if state in "xX-":
            title = (re.search(r"\*\*(.+?)\*\*", body) or [None, ""])[1]
            result = body.split("→", 1)[1].strip() if "→" in body else ""
            result = re.split(r"\s+·\s+commit|\s+—\s+\*\*", result)[0][:150]
            res.append(f"- [{state}] {tid or ''} — **{title}**" + (f" → {result}" if result else ""))
            continue
        paren = (re.match(r"[A-Z][\w-]*\s*\(([^)]*)\)", body) or [None, ""])[1]
        day_month = re.search(r"\d{1,2}\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)", paren)
        dated = "TARİHLİ" in paren or bool(day_month)
        due = _due_date(paren) if dated else None
        if not dated or (due and due <= TODAY):
            open_now.append(tid or body[:30])
        elif due:
            open_later.append(f"{tid} ({due:%d.%m})")
        else:
            open_unknown.append(tid or body[:30])
        res.append(ln)
        res.extend(cont)
    head = (f"**Kuyruk derinliği:** bugün yapılabilir {len(open_now)} görev ({', '.join(open_now) or '—'}) · "
            f"tarihi gelmemiş {len(open_later)} ({', '.join(open_later) or '—'})"
            + (f" · koşullu {len(open_unknown)} ({', '.join(open_unknown)})" if open_unknown else ""))
    if not open_now:
        head += ("\n**⚠️ KUYRUK BOŞ → boş koşu YAPMA:** `agent/plan/roadmap.md` (§4c) içinden en üstteki uygun açık maddeyi "
                 "`T<n>` olarak week.md kuyruğuna ekle ve uçtan uca yap (daily.md adım 4).")
    out(head + "\n")
    out("\n".join(res))


def sec_roadmap():
    p = os.path.join(PLAN, "roadmap.md")
    if not os.path.exists(p):
        out("(roadmap.md yok)")
        return
    lines = open(p, encoding="utf-8").read().splitlines()
    todo = [l for l in lines if re.match(r"^- \[ \] ", l)]
    done = [l for l in lines if re.match(r"^- \[[xX-]\] ", l)]
    out(f"{len(todo)} açık · {len(done)} kapalı madde. Açık maddeler (öncelik sırası; ayrıntı dosyada):")
    for l in todo[:14]:
        t = re.sub(r"\s+", " ", l)
        out(t[:230] + ("…" if len(t) > 230 else ""))


# ------------------------------------------------------------------ bahis metrikleri
def _path(url):
    return url.replace("https://parafomo.com", "").replace("http://parafomo.com", "") or "/"


def sec_bet_metrics():
    import bets as B
    act = [r for r in B.load() if r.get("status") == "active" and r.get("pages")]
    if not act:
        out("(sayfa desenli aktif bahis yok — `bets.py set-pages` ile tanımla)")
        return
    end = TODAY - dt.timedelta(days=3)
    rows7 = gsc(["page"], end - dt.timedelta(days=6), end, 1000)
    rows28 = gsc(["page"], end - dt.timedelta(days=27), end, 1000)
    sitemap = []
    try:
        import urllib.request
        req = urllib.request.Request("https://parafomo.com/sitemap-0.xml",
                                     headers={"User-Agent": "Mozilla/5.0 (parafomo-agent)"})  # Cloudflare python UA'yı 403'lüyor
        xml = urllib.request.urlopen(req, timeout=20).read().decode()
        sitemap = [_path(u) for u in re.findall(r"<loc>([^<]+)</loc>", xml)]
    except Exception:
        pass
    for r in act:
        rx = re.compile(r["pages"])
        def agg(rows):
            hit = [x for x in rows if rx.search(_path(x["keys"][0]))]
            return (sum(int(x["clicks"]) for x in hit), sum(int(x["impressions"]) for x in hit), hit)
        c7, i7, _ = agg(rows7)
        c28, i28, hit28 = agg(rows28)
        live = [u for u in sitemap if rx.search(u)]
        seen = {_path(x["keys"][0]).rstrip("/") for x in hit28}
        out(f"- **{r['id']}** `{r['pages']}` → 7g **{c7} tık / {i7} gös** · 28g {c28} tık / {i28} gös · "
            f"sitemap'te {len(live)} sayfa, 28g'de gösterim alan {len(seen)} sayfa · hedef: {r['target']}")
        for x in sorted(hit28, key=lambda x: (-x["clicks"], -x["impressions"]))[:5]:
            out(f"  - {_path(x['keys'][0])} — {int(x['clicks'])} tık · {int(x['impressions'])} gös · poz {x['position']:.1f}")
        if MODE == "weekly" and live:
            sec_indexing([u for u in live if u.rstrip("/") not in seen][:12])


def sec_indexing(paths):
    """Gösterim almayan bahis sayfalarının Google indeks durumu (URL Inspection API)."""
    _, _, sc = clients()
    if not sc or not paths:
        return
    from collections import Counter
    states = Counter()
    sample = []
    for pth in paths:
        try:
            res = sc.urlInspection().index().inspect(body={
                "inspectionUrl": "https://parafomo.com" + pth, "siteUrl": DASH.GSC_SITE}).execute()
            st = res.get("inspectionResult", {}).get("indexStatusResult", {}).get("coverageState", "?")
        except Exception as e:
            st = f"hata: {str(e)[:40]}"
        states[st] += 1
        if len(sample) < 4:
            sample.append(f"{pth} → {st}")
    out(f"  - İndeks (gösterimsiz {len(paths)} sayfa): " + " · ".join(f"{k}: {v}" for k, v in states.items()))
    for x in sample:
        out(f"    - {x}")

# ------------------------------------------------------------------ YouTube
def yt_videos():
    led = {}
    p = os.path.join(LEARN, "content-ledger.jsonl")
    for line in open(p, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            if r.get("channel") == "youtube":
                led[r["id"]] = r
    latest = {}
    for line in open(os.path.join(LEARN, "metrics.jsonl"), encoding="utf-8"):
        if '"youtube' not in line:
            continue
        r = json.loads(line)
        if r.get("channel") != "youtube":
            continue
        k = r["id"]
        if k not in latest or r["fetched_utc"] > latest[k]["fetched_utc"]:
            latest[k] = r
    vids = []
    for k, L in led.items():
        m = (latest.get(k) or {}).get("metrics", {})
        vids.append({"date": (L.get("published_utc") or "")[:10], "subtype": L.get("subtype") or "?",
                     "format": (L.get("attrs") or {}).get("format") or "-",
                     "views": int(m.get("views") or 0), "avd": m.get("avg_view_pct"),
                     "slug": (L.get("slug") or "")[:48]})
    return vids


def sec_youtube():
    vids = yt_videos()
    since = (TODAY - dt.timedelta(days=45)).isoformat()
    recent = [v for v in vids if v["date"] >= since]
    by = defaultdict(list)
    for v in recent:
        key = v["format"] if v["subtype"] == "viral" else (v["subtype"] + ("/manim" if v["slug"].endswith("-m") else ""))
        by[key].append(v)
    out("Son 45 gün, tür/format bazında (medyan izlenme · medyan izlenme-oranı AVD%):")
    out("| Tür/format | n | medyan izl. | medyan AVD% |")
    out("|---|---|---|---|")
    for k, vs in sorted(by.items(), key=lambda kv: -statistics.median([x["views"] for x in kv[1]])):
        avds = [x["avd"] for x in vs if x["avd"]]
        out(f"| {k} | {len(vs)} | {int(statistics.median([x['views'] for x in vs]))} | "
            f"{(round(statistics.median(avds)) if avds else '-')} |")
    try:
        h = json.load(open(os.path.join(LEARN, "hook-retention.json"), encoding="utf-8"))
        g = h.get("gate_by_format") or {}
        if g:
            out("\n65% AVD algoritma kapısı (hook_retention): " + " · ".join(
                f"{k} %{int(v.get('gate_pass_share', 0) * 100)} (n={v.get('n')})" for k, v in g.items()))
    except Exception:
        pass
    qa_p = os.path.join(ROOT, "logs", "video-qa.jsonl")
    if os.path.exists(qa_p):
        cutoff = (TODAY - dt.timedelta(days=7)).isoformat()
        recs = [json.loads(l) for l in open(qa_p, encoding="utf-8") if l.strip()]
        recs = [r for r in recs if r.get("ts", "") >= cutoff and not r.get("slug", "").startswith("zz-")]
        fixed = [(r["slug"], k, v) for r in recs for k, v in (r.get("bad") or {}).items()]
        out(f"\nVideo kalite kapısı (7g): {len(recs)} kontrol, {len(fixed)} sahne marka kartıyla değiştirildi"
            + (" — örnekler: " + " · ".join(f"{s[:30]}#{k}: {v[:70]}" for s, k, v in fixed[:4]) if fixed else ""))
    n = 12 if MODE == "weekly" else 8
    out(f"\nSon {n} video:")
    for v in sorted(vids, key=lambda x: x["date"])[-n:]:
        out(f"- {v['date']} {v['subtype']}/{v['format']} · {v['views']} izl · AVD {v['avd'] if v['avd'] is not None else '-'} · {v['slug']}")


# ------------------------------------------------------------------ web fırsatları
def sec_web():
    end = TODAY - dt.timedelta(days=3)
    start = end - dt.timedelta(days=27)
    q = gsc(["query"], start, end, 1000)
    q.sort(key=lambda r: -r["impressions"])
    nq = 20 if MODE == "weekly" else 12
    out(f"**GSC sorguları (28g, gösterime göre ilk {nq}):**")
    out("| Sorgu | Gös | Tık | Poz |")
    out("|---|---|---|---|")
    for r in q[:nq]:
        out(f"| {r['keys'][0][:60]} | {int(r['impressions'])} | {int(r['clicks'])} | {r['position']:.1f} |")
    pg = gsc(["page"], start, end, 200)
    pg.sort(key=lambda r: (-r["clicks"], -r["impressions"]))
    out(f"\n**GSC sayfaları (28g, tıklamaya göre ilk 12):**")
    for r in pg[:12]:
        url = r["keys"][0].replace("https://parafomo.com", "") or "/"
        out(f"- {url} — {int(r['clicks'])} tık · {int(r['impressions'])} gös · poz {r['position']:.1f}")
    try:
        rows = ga_report(["sessionDefaultChannelGroup"], TODAY - dt.timedelta(days=28), TODAY - dt.timedelta(days=1))
        rows.sort(key=lambda r: -r[1][0])
        out("\n**GA4 kanal kırılımı (28g, kullanıcı):** " + " · ".join(f"{r[0][0]} {int(r[1][0])}" for r in rows))
        lp = ga_report(["landingPage"], TODAY - dt.timedelta(days=28), TODAY - dt.timedelta(days=1),
                       dim_filter=("sessionDefaultChannelGroup", "Organic Search"))
        lp.sort(key=lambda r: -r[1][0])
        out("**Organik giriş sayfaları (28g):** " + " · ".join(f"{r[0][0]} {int(r[1][0])}" for r in lp[:10]))
    except Exception as e:
        out(f"_(GA4 kırılımı alınamadı: {e})_")


# ------------------------------------------------------------------ diğer
def sec_calendar():
    events = []
    try:
        d = json.load(open(os.path.join(ROOT, "data", "economic-calendar.json"), encoding="utf-8"))
        for e in d.get("events", []):
            if e.get("date", "") >= TODAY.isoformat() and e.get("impact") in ("High", "Medium"):
                events.append((e["date"], e.get("region", ""), e.get("title", ""), e.get("impact")))
    except Exception:
        pass
    for fn, label in (("fomc-2026.json", "Fed FOMC kararı"), ("tcmb-2026.json", "TCMB PPK"),
                      ("tuik-enflasyon-2026.json", "TÜİK enflasyon")):
        try:
            d = json.load(open(os.path.join(ROOT, "data", fn), encoding="utf-8"))
            items = d.get("meetings") or d.get("releases") or d.get("dates") or d.get("events") or []
            for it in items:
                date = it if isinstance(it, str) else (it.get("decisionDate") or it.get("date")
                                                       or it.get("decision_date") or "")
                extra = f" ({it['covers']})" if isinstance(it, dict) and it.get("covers") else ""
                if date[:10] >= TODAY.isoformat():
                    events.append((date[:10], "", label + extra, "High"))
        except Exception:
            pass
    horizon = (TODAY + dt.timedelta(days=30 if MODE == "weekly" else 21)).isoformat()
    seen, seen_tcmb = set(), set()
    for date, reg, title, imp in sorted(events):
        if date > horizon or (date, title) in seen:
            continue
        if "TCMB" in title and "özet" not in title.lower():  # iki kaynakta aynı PPK kararı
            if date in seen_tcmb:
                continue
            seen_tcmb.add(date)
        seen.add((date, title))
        out(f"- {date} {reg} {title} ({imp})")
    if not seen:
        out("- (önümüzdeki 3 haftada kayıtlı olay yok)")


def sec_demand():
    """Talep radarı: mevsimsel takvim (bu+gelecek ay) + Autocomplete'te kapsanmayan sorgular."""
    try:
        d = json.load(open(os.path.join(ROOT, "data", "tr-seasonal-seo.json"), encoding="utf-8"))
        months = {TODAY.month, TODAY.month % 12 + 1}
        rows = [t for t in d.get("takvim", []) if t.get("ay") in months]
        if rows:
            out("**Mevsimsel pencere (bu ay + gelecek ay) — sayfa talepten 3-6 hafta önce hazır olmalı:**")
            for t in rows:
                sayfa = t.get("sayfa") or "⚠ SAYFA YOK"
                out(f"- Ay {t['ay']}: {t['konu']} → {sayfa} · sorgular: {', '.join(t['sorgular'][:3])}"
                    + (f" · {t['not']}" if t.get("not") else ""))
    except Exception as e:
        out(f"_(mevsimsel takvim okunamadı: {e})_")
    try:
        p = os.path.join(ROOT, "data", "learning", "demand-gaps.json")
        g = json.load(open(p, encoding="utf-8"))
        age = (TODAY - dt.date.fromisoformat(g["generated_utc"][:10])).days
        n = 25 if MODE == "weekly" else 12
        if age <= 10:
            out(f"\n**Autocomplete'te aranan ama sitede kapsanmayan sorgular (kaba eşleşme, {age}g önce):**")
            out(" · ".join(g.get("uncovered_top", [])[:n]) or "(yok)")
            out("_Konu seçerken önce talebi doğrula (GSC gösterimi / rakip sayısı); birden çok öneri aynı"
                " niyetse TEK güçlü sayfada topla._")
    except Exception:
        out("\n_(demand-gaps.json yok — scripts/learn/demand_miner.py üretir)_")


def sec_opportunities():
    """Fırsat listesi: Trends hacmi ("mevduat faizi" = 100) × niyet × mevcut sıra → eylem."""
    p = os.path.join(ROOT, "data", "learning", "opportunities.json")
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        out("_(opportunities.json yok — /root/.venvs/parafomo/bin/python scripts/learn/opportunity_finder.py)_")
        return
    age = (TODAY - dt.date.fromisoformat(d["generated_utc"][:10])).days
    out(f"_{age}g önce · hacim = Google Trends TR 12 ay ort., '{d.get('anchor')}' = 100 · skor = hacim × niyet ×"
        " erişilebilirlik. Konu/görev seçiminin ana kaynağı; hacim < 5 → yazı/sayfa açma._")
    out("_Eylemler: CTR (ilk sayfa, tık düşük → başlık) · GUCLENDIR (p11-40 → içerik derinleştir) · YENIDEN_KUR · "
        "**OTORITE** (sayfanın başlığı/H1'i sorguyu ZATEN içeriyor ama sıra >40 ya da gösterim yok → on-page/başlık görevi "
        "YAPMA; uzun kuyruk, gelecek yıl (2027) açısı veya iç/dış link ile gir) · YENI_ARAC / YENI_YAZI. "
        "28 günden yeni sayfalar listede yok (BEKLE)._")
    if age > 10:
        out("⚠ Liste bayat (>10g) — önce scripti çalıştır.")
    n = 25 if MODE == "weekly" else 12
    out("\n| skor | eylem | sorgu | hacim (son 4h / zirve) | sayfa | GSC 28g | not |")
    out("|---|---|---|---|---|---|---|")
    for r in d.get("firsatlar", [])[:n]:
        g = r.get("gsc")
        gs = f"sıra {g['pos']} · {g['clicks']}/{g['impr']}" if g else "—"
        vek = f" ≈{r['vekil']}" if r.get("vekil") else ""
        out(f"| {r['skor']} | {r['eylem']} | {r['q']}{vek} | {r['hacim']} ({r.get('son4h') or '—'} / {r.get('zirve') or '—'}) "
            f"| {r.get('sayfa') or '—'} | {gs} | {r['not']} |")
    if d.get("bekle"):
        out("\n**Yeni sayfalar — oturmasını bekle (görev üretme):** " + " · ".join(f"{r['q']} → {r['sayfa']}" for r in d["bekle"][:10]))
    if d.get("koru"):
        out("\n**İlk sayfadakiler (koru):** " + " · ".join(f"{r['q']} ({r['hacim']})" for r in d["koru"][:8]))
    if d.get("dusuk_talep"):
        k = 30 if MODE == "weekly" else 12
        out("\n**Düşük talep (hacim < 2 — bu sorgulara yazı açma):** " + " · ".join(d["dusuk_talep"][:k]))


def sec_seo():
    p = os.path.join(ROOT, "data", "learning", "seo-audit.json")
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        out("_(seo-audit.json yok — /root/.venvs/parafomo/bin/python scripts/seo-audit.py --google)_")
        return
    c, ix = d["counts"], d["index"]
    age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(d["generated"])).total_seconds() / 3600
    out(f"_{age:.0f} sa önce · {d['pages']} sayfa · KRİTİK {c['KRİTİK']} · UYARI {c['UYARI']} · BİLGİ {c['BİLGİ']} · "
        f"Google indeksi {ix['indexed']}/{ix['checked']} bakılan sayfa_")
    codes = d.get("codes", {})
    crit = [i for i in d["issues"] if i["sev"] == "KRİTİK"]
    for i in crit[:20]:
        out(f"- 🔴 **{codes.get(i['code'], {}).get('label', i['code'])}** — {i['path']} {i['detail']} → {codes.get(i['code'], {}).get('fix', '')}")
    groups = {}
    for i in d["issues"]:
        if i["sev"] == "UYARI":
            groups.setdefault(i["code"], []).append(i)
    for code, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        meta = codes.get(code, {})
        ex = ", ".join(f"{i['path']}" + (f" ({i['detail']})" if i["detail"] else "") for i in items[:4])
        out(f"- 🟡 {meta.get('label', code)}: **{len(items)}** sayfa — örn. {ex} → {meta.get('fix', '')}")


def sec_inventory():
    blog = os.path.join(ROOT, "src", "content", "blog")
    posts = []
    for f in os.listdir(blog):
        if not f.endswith((".md", ".mdx")):
            continue
        head = open(os.path.join(blog, f), encoding="utf-8").read(1500)
        t = re.search(r'^title:\s*"?(.*?)"?\s*$', head, re.M)
        d = re.search(r"^pubDate:\s*\"?([\d-]+)", head, re.M)
        posts.append(((d.group(1) if d else ""), f[:-3], t.group(1)[:70] if t else f))
    posts.sort()
    out(f"- Blog: {len(posts)} yazı. Son 6:")
    for d, s, t in posts[-6:]:
        out(f"  - {d} /blog/{s} — {t}")
    pages = sorted(p[:-6] for p in os.listdir(os.path.join(ROOT, "src", "pages"))
                   if p.endswith(".astro") and p not in ("index.astro", "404.astro"))
    out(f"- Veri/araç sayfaları ({len(pages)}): " + ", ".join("/" + p for p in pages))
    out(f"- Veri dosyaları: " + ", ".join(sorted(f for f in os.listdir(os.path.join(ROOT, "data")) if f.endswith(".json"))))


def cat(path, maxlines=None, empty="(yok)"):
    if not os.path.exists(path):
        out(empty)
        return
    lines = open(path, encoding="utf-8").read().rstrip().splitlines()
    if maxlines and len(lines) > maxlines:
        lines = lines[:maxlines] + [f"… (+{len(lines) - maxlines} satır, dosyanın tamamı: {os.path.relpath(path, ROOT)})"]
    out("\n".join(lines) if lines else empty)


def sec_content_queue():
    p = os.path.join(PLAN, "content-queue.md")
    if not os.path.exists(p):
        out("(yok)")
        return
    lines = open(p, encoding="utf-8").read().splitlines()
    todo = [l for l in lines if l.strip().startswith("- [ ]")]
    done = [l for l in lines if l.strip().startswith("- [x]")]
    out(f"{len(todo)} bekleyen konu (daily-content en üsttekini yazar), {len(done)} yazıldı.")
    for l in todo[:8]:
        out(l)


def sec_user_inputs():
    """Kaan'dan beklenen girdilerin GERÇEK durumu — ajan repo dışını ls'leyemez (headless izin)."""
    cfg = os.path.expanduser("~/.config/parafomo")
    music = os.path.join(os.path.dirname(ROOT), "parafomo-media", "music")
    n_music = len([f for f in os.listdir(music) if f.lower().endswith((".mp3", ".wav", ".m4a", ".ogg"))]) \
        if os.path.isdir(music) else 0
    def has(name):
        return "VAR ✅" if os.path.exists(os.path.join(cfg, name)) else "yok"
    out(f"Girdi durumu (otomatik): müzik klasörü {n_music} parça · claude.env {has('claude.env')} · "
        f"backup.env {has('backup.env')}")
    try:
        import sqlite3
        db = os.path.expanduser("~/parafomo-data/portfolio.db")
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        rows = dict(con.execute("SELECT status, COUNT(*) FROM newsletter_subscribers GROUP BY status").fetchall())
        users = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        con.close()
        out(f"Bülten aboneleri: onaylı {rows.get('confirmed', 0)} · bekleyen {rows.get('pending', 0)} · "
            f"çıkan {rows.get('unsubscribed', 0)} · portföy üyeleri {users}")
    except Exception as e:
        out(f"Bülten/üye sayısı okunamadı: {type(e).__name__}")
    out("")
    cat(os.path.join(PLAN, "user-tasks.md"))


def sec_runs():
    p = os.path.join(MEM, "runs.jsonl")
    if not os.path.exists(p):
        out("(henüz v2 koşusu yok)")
        return
    rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    n = 10 if MODE == "weekly" else 4
    for r in rows[-n:]:
        out(f"- {r.get('started', '')[:16]} {r.get('mode')} {r.get('model')} → **{r.get('outcome')}** · "
            f"${r.get('cost', '?')} · {r.get('turns', '?')} tur · {r.get('minutes', '?')} dk"
            + (f" · {r.get('message', '')[:100]}" if r.get("outcome") != "success" else ""))
    recent = [r for r in rows if r.get("started", "") >= (TODAY - dt.timedelta(days=7)).isoformat()]
    idle = [r for r in recent if r.get("mode") == "daily" and float(r.get("minutes") or 0) <= 5]
    if idle:
        out(f"- ⚠️ Son 7 günde {len(idle)} günlük koşu ≤5 dk sürdü (kuyruk boş kaldı) — boş koşu yerine roadmap.md'den iş çek")
    if MODE == "weekly":
        week = [r for r in rows if r.get("started", "") >= (TODAY - dt.timedelta(days=7)).isoformat()]
        tot = sum(float(r.get("cost") or 0) for r in week)
        out(f"- Son 7 gün ajan maliyeti (API-eşdeğeri): ${tot:.2f} · {len(week)} koşu")
    u = os.path.join(ROOT, "logs", "llm-usage.jsonl")
    if MODE == "weekly" and os.path.exists(u):
        agg = defaultdict(lambda: [0, 0.0])
        cutoff = (TODAY - dt.timedelta(days=7)).isoformat()
        for line in open(u, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("ts", "") >= cutoff:
                agg[r.get("tag") or "?"][0] += 1
                agg[r.get("tag") or "?"][1] += float(r.get("cost") or 0)
        if agg:
            out("- Script LLM çağrıları (7g): " + " · ".join(f"{k} {v[0]}× ${v[1]:.2f}" for k, v in sorted(agg.items())))


def sec_stash():
    r = subprocess.run(["git", "-C", ROOT, "stash", "list"], capture_output=True, text=True)
    st = [l for l in r.stdout.splitlines() if "agent-wip" in l]
    if st:
        out("Önceki kesik koşudan yarım iş stash'te (incele: `git stash show -p stash@{N}`; uygula ya da `git stash drop`):")
        for l in st[:3]:
            out(f"- {l}")
    else:
        out("(yok)")


def main():
    import health
    out(f"# ParaFOMO Brief — {TODAY} · mod: {MODE}")
    out("_Token'sız üretildi (agent/brief.py). Bu belge senin bağlamın; ham dosyaları ayrıca tarama._\n")
    section("1) KPI (kayan pencere — kısmi hafta artefaktı yok)", sec_kpi_snapshot)
    section("1b) Kanallar + dağıtım (darboğaz hangi kanalda? — haftalık skor kartına da gir)", sec_channels)
    section(f"2) Skor kartı — son {WEEKS} ISO hafta", sec_scorecard)
    section("3) Üretim sağlığı (önce bunu oku — kırmızı varsa ilk iş onu düzelt)",
            lambda: out(health.render(health.collect())))
    section("3b) SEO denetimi (scripts/seo-audit.py — KRİTİK varsa görevden önce düzelt)", sec_seo)
    section("4) Bu haftanın planı (agent/plan/week.md — biten görevler tek satır)", sec_week)
    section("4b) GÖREV MASASI — Kaan'ın kararları, notları, istekleri (dashboard.parafomo.com — ÖNCE BUNU UYGULA)",
            lambda: out(__import__("board").render_brief()))
    section("4c) Yol haritası (agent/plan/roadmap.md) — kuyruk boşsa iş BURADAN", sec_roadmap)
    section("5) Bahisler (agent/bets.py)", lambda: out(__import__("bets").render(__import__("bets").load(),
                                                                                show_all=MODE == "weekly")))
    section("5b) Bahis metrikleri (otomatik — GSC, gecikmeli)", sec_bet_metrics)
    section("6) Kalıcı dersler (agent/memory/learnings.md)", lambda: cat(os.path.join(MEM, "learnings.md")))
    section("7) Web: arama ve trafik verisi", sec_web)
    section("8) YouTube", sec_youtube)
    section("9) Takvim (yaklaşan yüksek/orta etkili olaylar)", sec_calendar)
    section("9b) Talep radarı (mevsimsel + Autocomplete boşlukları)", sec_demand)
    section("9c) FIRSAT LİSTESİ — aranma hacmi ölçülmüş sorgular (konu seçimi buradan)", sec_opportunities)
    section("10) İçerik envanteri", sec_inventory)
    section("11) Blog konu kuyruğu (agent/plan/content-queue.md)", sec_content_queue)
    section("12) Kullanıcı görevleri (agent/plan/user-tasks.md)", sec_user_inputs)
    section("13) Son ajan koşuları + maliyet", sec_runs)
    section("14) Yarım kalan iş", sec_stash)


if __name__ == "__main__":
    main()
