#!/usr/bin/env python3
"""
ParaFOMO — Web (GA4 + GSC) metrik toplayıcı.

Blog sayfası performansını çeker, blog slug'larına eşler → metrics.jsonl.
Ayrıca konu-önericisi için arama sorgularını data/learning/web-queries.json'a yazar
(en çok gösterilen + 'fırsat' sorguları = çok gösterim / az tıklama / 4-20. sıra).

Kimlik: ~/.config/parafomo/ga-sa.json (weekly-report.py ile aynı servis hesabı).
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

GSC_SITE = "sc-domain:parafomo.com"
GA4_PROPERTY = "542292605"
WINDOW = 28
GSC_SCOPE = ["https://www.googleapis.com/auth/webmasters.readonly"]
GA4_SCOPE = ["https://www.googleapis.com/auth/analytics.readonly"]


def slug_from_path(path):
    # /blog/<slug>/ veya https://parafomo.com/blog/<slug>/
    if "/blog/" not in path:
        return None
    tail = path.split("/blog/", 1)[1]
    return tail.strip("/").split("/")[0] or None


def ga4_pages():
    creds = lib.ga_credentials(GA4_SCOPE)
    if creds is None:
        return {}
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
    client = BetaAnalyticsDataClient(credentials=creds)
    req = RunReportRequest(
        property=f"properties/{GA4_PROPERTY}",
        date_ranges=[DateRange(start_date=f"{WINDOW}daysAgo", end_date="today")],
        dimensions=[Dimension(name="pagePath")],
        metrics=[Metric(name="screenPageViews"), Metric(name="activeUsers"),
                 Metric(name="userEngagementDuration")],
        limit=500,
    )
    out = {}
    for row in client.run_report(req).rows:
        slug = slug_from_path(row.dimension_values[0].value)
        if not slug:
            continue
        pv = float(row.metric_values[0].value or 0)
        us = float(row.metric_values[1].value or 0)
        eng = float(row.metric_values[2].value or 0)
        d = out.setdefault(slug, {"pageviews": 0, "users": 0, "eng_sec": 0})
        d["pageviews"] += pv
        d["users"] += us
        d["eng_sec"] += eng
    return out


def gsc():
    creds = lib.ga_credentials(GSC_SCOPE)
    if creds is None:
        return {}, {"top": [], "opportunity": []}
    from googleapiclient.discovery import build
    import datetime as dt
    sc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    end = dt.date.today()
    start = end - dt.timedelta(days=WINDOW)

    def query(dimensions, limit=500):
        body = {"startDate": start.isoformat(), "endDate": end.isoformat(),
                "dimensions": dimensions, "rowLimit": limit}
        return sc.searchanalytics().query(siteUrl=GSC_SITE, body=body).execute().get("rows", [])

    pages = {}
    for r in query(["page"]):
        slug = slug_from_path(r["keys"][0])
        if slug:
            pages[slug] = {"clicks": int(r.get("clicks", 0)),
                           "impressions": int(r.get("impressions", 0)),
                           "position": round(r.get("position", 0), 1)}
    qs = query(["query"], 200)
    top = sorted(qs, key=lambda x: -x["impressions"])[:15]
    opp = [q for q in qs
           if q["impressions"] >= 5 and 4 <= q["position"] <= 20
           and (q["clicks"] / max(q["impressions"], 1)) < 0.05]
    fmt = lambda q: {"query": q["keys"][0], "impressions": int(q["impressions"]),
                     "clicks": int(q["clicks"]), "position": round(q["position"], 1)}
    return pages, {"top": [fmt(q) for q in top],
                   "opportunity": [fmt(q) for q in sorted(opp, key=lambda x: -x["impressions"])[:12]]}


def main():
    try:
        ga = ga4_pages()
    except Exception as e:
        print(f"[web] GA4 hata: {type(e).__name__}: {str(e)[:150]}"); ga = {}
    try:
        gpages, queries = gsc()
    except Exception as e:
        print(f"[web] GSC hata: {type(e).__name__}: {str(e)[:150]}")
        gpages, queries = {}, {"top": [], "opportunity": []}

    ledger = {r["slug"]: r for r in lib.read_jsonl(lib.LEDGER) if r["channel"] == "web" and r.get("slug")}
    slugs = set(ga) | set(gpages)
    rows = []
    fetched = lib.iso()
    for slug in slugs:
        if slug not in ledger:
            continue
        m = {}
        m.update(ga.get(slug, {}))
        m.update(gpages.get(slug, {}))
        if m:
            rows.append({"id": lib.cid("blog", slug), "channel": "web",
                         "fetched_utc": fetched, "metrics": m})
    lib.append_jsonl(lib.METRICS, rows)

    qpath = os.path.join(lib.DATA, "web-queries.json")
    json.dump({"generated_utc": fetched, **queries}, open(qpath, "w"),
              ensure_ascii=False, indent=2)
    print(f"[+] web metrik eklendi: {len(rows)} sayfa · "
          f"{len(queries['top'])} sorgu, {len(queries['opportunity'])} fırsat -> web-queries.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
