#!/usr/bin/env python3
"""Panel metrikleri (dashboard.parafomo.com, 2026-11-16) → /root/parafomo-data/dash/kpi.json

Üç kanal: web (Search Console + GA4), YouTube (kanal + video), Instagram (hesap + reel).
Panel sunucusu bunu 3 saatte bir arka planda çalıştırır (parafomo venv'i: Google kütüphaneleri burada).
Her bölüm bağımsız: biri hata verirse "hatalar" listesine yazılır, gerisi sürer. Anahtar/URL hatalara yazılmaz.

  /root/.venvs/parafomo/bin/python dashboard/collect.py
"""
import datetime as dt
import importlib.util
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = "/root/parafomo"
OUT = "/root/parafomo-data/dash"
KUYRUK = "/root/parafomo-data/onay/kuyruk.json"
LF_DIR = os.path.join(ROOT, "public", "social", "longform")
sys.path.insert(0, os.path.join(ROOT, "scripts", "learn"))


def hata(e):
    return f"{type(e).__name__}: {str(e)[:160]}"


def web():
    spec = importlib.util.spec_from_file_location("g", f"{ROOT}/scripts/gsc-sitemap.py")
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    svc = g.client()
    site = getattr(g, "SITE", None) or "sc-domain:parafomo.com"
    today = dt.date.today()
    rows = svc.searchanalytics().query(siteUrl=site, body={
        "startDate": str(today - dt.timedelta(days=70)), "endDate": str(today), "dimensions": ["date"]}).execute().get("rows", [])
    by = {r["keys"][0]: r for r in rows}
    end = max(dt.date.fromisoformat(k) for k in by)   # GSC 2-3 gün geriden gelir: haftayı verinin bittiği güne daya

    def hafta(e):
        ds = [str(e - dt.timedelta(days=i)) for i in range(7)]
        return {"bitis": str(e),
                "tik": round(sum(by.get(d, {}).get("clicks", 0) for d in ds)),
                "gosterim": round(sum(by.get(d, {}).get("impressions", 0) for d in ds))}
    haftalar = [hafta(end - dt.timedelta(days=7 * k)) for k in range(8)][::-1]
    out = {"haftalar": haftalar, "son": haftalar[-1], "onceki": haftalar[-2]}

    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import DateRange, Filter, FilterExpression, Metric, RunReportRequest
    from google.oauth2 import service_account
    c = BetaAnalyticsDataClient(credentials=service_account.Credentials.from_service_account_file(
        os.path.expanduser("~/.config/parafomo/ga-sa.json")))
    yalniz_site = FilterExpression(filter=Filter(field_name="hostName", string_filter=Filter.StringFilter(
        match_type=Filter.StringFilter.MatchType.ENDS_WITH, value="parafomo.com")))

    def oturum(s, e):
        r = c.run_report(RunReportRequest(property="properties/542292605", date_ranges=[DateRange(start_date=s, end_date=e)],
                                          metrics=[Metric(name="sessions")], dimension_filter=yalniz_site))
        return int(r.rows[0].metric_values[0].value) if r.rows else 0
    out["ziyaret_7g"] = oturum("7daysAgo", "yesterday")
    out["ziyaret_onceki"] = oturum("14daysAgo", "8daysAgo")
    return out


def youtube(video_ids):
    import lib
    from googleapiclient.discovery import build
    creds = lib.youtube_credentials(["https://www.googleapis.com/auth/youtube.readonly",
                                     "https://www.googleapis.com/auth/yt-analytics.readonly"])
    if creds is None:
        raise RuntimeError("YouTube yetkisi yok")
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    ya = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    st = yt.channels().list(part="statistics", mine=True).execute()["items"][0]["statistics"]
    out = {"abone": int(st.get("subscriberCount", 0)), "video_sayisi": int(st.get("videoCount", 0))}
    end = dt.date.today() - dt.timedelta(days=2)   # Analytics ~2 gün gecikmeli: tam günlerle karşılaştır
    rows = ya.reports().query(ids="channel==MINE", startDate=str(end - dt.timedelta(days=55)), endDate=str(end),
                              metrics="views,subscribersGained,subscribersLost", dimensions="day").execute().get("rows", [])
    by = {r[0]: r for r in rows}

    def hafta(e):
        ds = [str(e - dt.timedelta(days=i)) for i in range(7)]
        return {"bitis": str(e), "izlenme": sum(by.get(d, [0, 0])[1] for d in ds),
                "abone": sum(by.get(d, [0, 0, 0])[2] - by.get(d, [0, 0, 0, 0])[3] for d in ds)}
    haftalar = [hafta(end - dt.timedelta(days=7 * k)) for k in range(8)][::-1]
    out.update({"haftalar": haftalar, "son": haftalar[-1], "onceki": haftalar[-2]})
    vids = {}
    ids = [v for v in video_ids if v]
    for i in range(0, len(ids), 50):
        for v in yt.videos().list(part="statistics", id=",".join(ids[i:i + 50])).execute().get("items", []):
            s = v["statistics"]
            vids[v["id"]] = {"izlenme": int(s.get("viewCount", 0)), "begeni": int(s.get("likeCount", 0))}
    out["videolar"] = vids
    return out


def instagram(media_ids):
    env = {}
    for line in open(os.path.expanduser("~/.config/parafomo/instagram.env"), encoding="utf-8"):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            env[k] = v
    base = "https://graph.facebook.com/v21.0/"

    def get(path, **params):
        params["access_token"] = env["IG_PAGE_TOKEN"]
        with urllib.request.urlopen(base + path + "?" + urllib.parse.urlencode(params), timeout=30) as r:
            return json.load(r)
    u = get(env["IG_BUSINESS_ACCOUNT_ID"], fields="followers_count,media_count")
    out = {"takipci": u.get("followers_count"), "paylasim": u.get("media_count"), "reeller": {}}
    for mid in [m for m in media_ids if m]:
        try:
            r = get(f"{mid}/insights", metric="reach,views,saved,shares")
            out["reeller"][mid] = {m["name"]: m["values"][0]["value"] for m in r.get("data", [])}
        except Exception:   # silinmiş/erişilemeyen medya: atla
            pass
    return out


def kayit():
    """Site kayıtları (Kaan 2026-11-17: "asıl istediğim kaydolmaları"): zam alarmı + bülten + portföy üyeliği.
    Veritabanı salt-okunur açılır; kişisel veri çekilmez, yalnız sayılar."""
    import sqlite3
    con = sqlite3.connect("file:/root/parafomo-data/portfolio.db?mode=ro", uri=True)
    try:
        rows = con.execute("select status, coalesce(source, '') from newsletter_subscribers "
                           "where coalesce(source, '') not like 'rc-e2e%'").fetchall()
        uye = con.execute("select count(*) from users").fetchone()[0]
        hafta = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)).strftime("%Y-%m-%d")
        yeni7 = con.execute("select count(*) from newsletter_subscribers where created_at >= ? "
                            "and coalesce(source, '') not like 'rc-e2e%'", (hafta,)).fetchone()[0]
    finally:
        con.close()
    zam = lambda s: "zam-alarmi:" in s
    out = {"zam_onayli": sum(1 for st, s in rows if st == "confirmed" and zam(s)),
           "bulten_onayli": sum(1 for st, s in rows if st == "confirmed" and not zam(s)),
           "bekleyen": sum(1 for st, _ in rows if st == "pending"), "yeni_7g": yeni7, "uye": uye}
    out["onayli"] = sum(1 for st, _ in rows if st == "confirmed")
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    q = {"items": []}
    try:
        q = json.load(open(KUYRUK, encoding="utf-8"))
    except (OSError, ValueError):
        pass
    son = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)).isoformat()
    yayinda = [it for it in q["items"] if it.get("status") == "yayinlandi" and it.get("published", "") >= son]
    lf_ids = []
    for f in sorted(os.listdir(LF_DIR)) if os.path.isdir(LF_DIR) else []:
        if f.endswith(".meta.json"):
            try:
                m = json.load(open(os.path.join(LF_DIR, f), encoding="utf-8"))
                if m.get("video_id"):
                    lf_ids.append(m["video_id"])
            except (OSError, ValueError):
                pass
    kpi = {"guncellendi": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "hatalar": []}
    for ad, fn in (("web", web),
                   ("youtube", lambda: youtube([it.get("youtube_id") for it in yayinda] + lf_ids)),
                   ("instagram", lambda: instagram([it.get("ig_media_id") for it in yayinda])),
                   ("kayit", kayit)):
        try:
            kpi[ad] = fn()
        except Exception as e:   # noqa: BLE001 — bölüm bağımsız
            kpi["hatalar"].append(f"{ad}: {hata(e)}")
    p = os.path.join(OUT, "kpi.json")
    eski = {}
    try:
        eski = json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        pass
    for ad in ("web", "youtube", "instagram", "kayit"):   # bir bölüm çöktüyse son iyi değeri koru (eski diye işaretli)
        if ad not in kpi and ad in eski:
            kpi[ad] = {**eski[ad], "eski": True}
    tmp = p + ".tmp"
    json.dump(kpi, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, p)
    # günlük tarihçe (günde bir satır; aynı gün yeniden yazılır)
    h = os.path.join(OUT, "kpi-gecmis.jsonl")
    satir = {"gun": dt.date.today().isoformat(),
             "google_tik_7g": kpi.get("web", {}).get("son", {}).get("tik"),
             "ziyaret_7g": kpi.get("web", {}).get("ziyaret_7g"),
             "yt_abone": kpi.get("youtube", {}).get("abone"),
             "yt_izlenme_7g": kpi.get("youtube", {}).get("son", {}).get("izlenme"),
             "ig_takipci": kpi.get("instagram", {}).get("takipci")}
    rows = []
    try:
        rows = [json.loads(x) for x in open(h, encoding="utf-8") if x.strip()]
    except (OSError, ValueError):
        pass
    rows = [r for r in rows if r.get("gun") != satir["gun"]] + [satir]
    with open(h + ".tmp", "w", encoding="utf-8") as f:
        f.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows[-400:]))
    os.replace(h + ".tmp", h)
    print(json.dumps({k: kpi.get(k) for k in ("guncellendi", "hatalar")}, ensure_ascii=False))
    print("web:", kpi.get("web", {}).get("son"), "ziyaret", kpi.get("web", {}).get("ziyaret_7g"))
    print("youtube: abone", kpi.get("youtube", {}).get("abone"), "son hafta", kpi.get("youtube", {}).get("son"))
    print("instagram: takipçi", kpi.get("instagram", {}).get("takipci"), "reel sayısı", len(kpi.get("instagram", {}).get("reeller", {})))


if __name__ == "__main__":
    main()
