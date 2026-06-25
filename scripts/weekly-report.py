#!/usr/bin/env python3
"""
ParaFOMO — Haftalık GSC + GA4 trafik özeti.

Google Search Console (arama görünürlüğü) + GA4 (site trafiği) verisini çeker,
Türkçe bir rapor üretir (docs/analytics-report.md) ve istenirse Telegram'a özet
gönderir. Servis hesabı anahtarı repo dışıdır (~/.config/parafomo/ga-sa.json).

Öne çıkan: "fırsat sorguları" = GSC'de çok gösterilen ama az tıklanan / 5-20.
sırada olan aramalar → içerik/başlık iyileştirme hedefi.

Kullanım:
  /root/.venvs/parafomo/bin/python scripts/weekly-report.py            # rapor yaz
  /root/.venvs/parafomo/bin/python scripts/weekly-report.py --telegram # + Telegram
"""
import logging
import os
import sys
from datetime import date, timedelta

# google-auth (>=2.40) servis hesabı için "Regional Access Boundary" lookup'ı dener;
# bu ortamda yapılandırılmadığı için FAILED_PRECONDITION ile döner ve her çağrıda
# stderr'e zararsız bir WARNING basar. Lookup non-fatal (rapor yine üretiliyor),
# bu yüzden ilgili Google logger'larını ERROR seviyesine çekip gürültüyü susturuyoruz.
logging.getLogger("google.auth").setLevel(logging.ERROR)
logging.getLogger("google.oauth2").setLevel(logging.ERROR)

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Dimension, Metric, OrderBy,
)

KEY = os.path.expanduser("~/.config/parafomo/ga-sa.json")
GSC_SITE = "sc-domain:parafomo.com"
GA4_PROPERTY = "542292605"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_MD = os.path.join(ROOT, "docs", "analytics-report.md")

GSC_SCOPE = ["https://www.googleapis.com/auth/webmasters.readonly"]
GA4_SCOPE = ["https://www.googleapis.com/auth/analytics.readonly"]


# ------------------------------- GSC -------------------------------

def gsc_client():
    creds = service_account.Credentials.from_service_account_file(KEY, scopes=GSC_SCOPE)
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def gsc_query(sc, start, end, dimensions=None, row_limit=25):
    body = {"startDate": start.isoformat(), "endDate": end.isoformat(), "rowLimit": row_limit}
    if dimensions:
        body["dimensions"] = dimensions
    return sc.searchanalytics().query(siteUrl=GSC_SITE, body=body).execute().get("rows", [])


def gsc_section(sc, start, end, prev_start, prev_end):
    lines = ["## 🔍 Google Arama (Search Console)", ""]
    cur = gsc_query(sc, start, end)
    prev = gsc_query(sc, prev_start, prev_end)
    c = cur[0] if cur else {}
    p = prev[0] if prev else {}
    cc, ci = int(c.get("clicks", 0)), int(c.get("impressions", 0))
    pc, pi = int(p.get("clicks", 0)), int(p.get("impressions", 0))
    lines.append(f"- **Tıklama:** {cc}  (önceki hafta {pc}, {delta(cc, pc)})")
    lines.append(f"- **Gösterim:** {ci}  (önceki hafta {pi}, {delta(ci, pi)})")
    ctr = (cc / ci * 100) if ci else 0
    lines.append(f"- **Ortalama CTR:** %{ctr:.1f}")
    lines.append("")

    queries = gsc_query(sc, start, end, ["query"], 100)
    lines.append("**En çok gösterilen sorgular:**")
    if not queries:
        lines.append("- (henüz veri yok — yeni site, birkaç hafta sürer)")
    for q in sorted(queries, key=lambda x: -x["impressions"])[:10]:
        lines.append(f"- `{q['keys'][0]}` — gös {int(q['impressions'])}, tık {int(q['clicks'])}, "
                     f"sıra {q['position']:.1f}")
    lines.append("")

    # Fırsat sorguları: çok gösterilen, az tıklanan, 4-20. sırada
    opp = [q for q in queries
           if q["impressions"] >= 5 and q["position"] >= 4 and q["position"] <= 20
           and (q["clicks"] / q["impressions"]) < 0.05]
    lines.append("**🎯 Fırsat sorguları** (çok gösterim, düşük tıklama, 4-20. sıra → başlık/içerik iyileştir):")
    if not opp:
        lines.append("- (henüz belirgin fırsat yok)")
    for q in sorted(opp, key=lambda x: -x["impressions"])[:8]:
        lines.append(f"- `{q['keys'][0]}` — gös {int(q['impressions'])}, sıra {q['position']:.1f}")
    lines.append("")

    pages = gsc_query(sc, start, end, ["page"], 100)
    lines.append("**En çok tıklanan sayfalar:**")
    top_pages = sorted(pages, key=lambda x: -x["clicks"])[:8]
    if not any(int(p["clicks"]) for p in top_pages):
        lines.append("- (henüz tıklama yok)")
    else:
        for p in top_pages:
            if int(p["clicks"]) == 0:
                continue
            path = p["keys"][0].replace("https://parafomo.com", "")
            lines.append(f"- {path} — tık {int(p['clicks'])}, gös {int(p['impressions'])}")
    lines.append("")
    return lines, (cc, ci)


# ------------------------------- GA4 -------------------------------

def ga4_client():
    creds = service_account.Credentials.from_service_account_file(KEY, scopes=GA4_SCOPE)
    return BetaAnalyticsDataClient(credentials=creds)


def ga4_report(client, dims, mets, days=7, limit=10, order_metric=None):
    req = RunReportRequest(
        property=f"properties/{GA4_PROPERTY}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
        dimensions=[Dimension(name=d) for d in dims],
        metrics=[Metric(name=m) for m in mets],
        limit=limit,
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name=order_metric), desc=True)]
        if order_metric else None,
    )
    return client.run_report(req)


def ga4_section(client):
    lines = ["## 📊 Site Trafiği (GA4 — son 7 gün)", ""]
    tot = ga4_report(client, [], ["activeUsers", "screenPageViews", "sessions"], days=7, limit=1)
    if tot.rows:
        mv = tot.rows[0].metric_values
        lines.append(f"- **Kullanıcı:** {mv[0].value}  ·  **Görüntüleme:** {mv[1].value}  ·  **Oturum:** {mv[2].value}")
    else:
        lines.append("- (henüz trafik yok)")
    lines.append("")

    pages = ga4_report(client, ["pagePath"], ["screenPageViews", "activeUsers"],
                       days=7, limit=8, order_metric="screenPageViews")
    lines.append("**En çok görüntülenen sayfalar:**")
    if not pages.rows:
        lines.append("- (veri yok)")
    for row in pages.rows:
        lines.append(f"- {row.dimension_values[0].value} — görüntüleme {row.metric_values[0].value}, "
                     f"kullanıcı {row.metric_values[1].value}")
    lines.append("")

    chan = ga4_report(client, ["sessionDefaultChannelGroup"], ["sessions", "activeUsers"],
                      days=7, limit=8, order_metric="sessions")
    lines.append("**Trafik kaynağı (kanal):**")
    if not chan.rows:
        lines.append("- (veri yok)")
    for row in chan.rows:
        lines.append(f"- {row.dimension_values[0].value} — oturum {row.metric_values[0].value}, "
                     f"kullanıcı {row.metric_values[1].value}")
    lines.append("")
    return lines


def delta(cur, prev):
    if prev == 0:
        return "yeni" if cur else "—"
    pct = (cur - prev) / prev * 100
    arrow = "▲" if pct >= 0 else "▼"
    return f"{arrow}%{abs(pct):.0f}"


def post_telegram(text):
    """.env'den bot token + chat id okuyup özet gönder."""
    env = {}
    try:
        with open(os.path.join(ROOT, ".env")) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    except OSError:
        print("[!] .env okunamadı, Telegram atlandı")
        return
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat = env.get("TELEGRAM_CHAT_ID")
    if not (token and chat):
        print("[!] Telegram token/chat yok, atlandı")
        return
    import urllib.request
    import urllib.parse
    data = urllib.parse.urlencode({
        "chat_id": chat, "text": text, "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
    try:
        urllib.request.urlopen(req, timeout=15)
        print("[+] Telegram'a gönderildi")
    except Exception as e:
        print(f"[!] Telegram gönderilemedi: {e}")


def main():
    today = date.today()
    end = today
    start = today - timedelta(days=7)
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=7)

    header = [
        "# ParaFOMO — Haftalık Trafik Raporu",
        "",
        f"> Üretim: {today.isoformat()} · `scripts/weekly-report.py` · Dönem: {start} → {end}",
        "",
    ]
    body = []
    summary_metrics = (0, 0)
    try:
        sc = gsc_client()
        gsc_lines, summary_metrics = gsc_section(sc, start, end, prev_start, prev_end)
        body += gsc_lines
    except Exception as e:
        body += [f"## 🔍 Google Arama\n\n- [HATA] GSC çekilemedi: {e}\n"]
    try:
        ga = ga4_client()
        body += ga4_section(ga)
    except Exception as e:
        body += [f"## 📊 Site Trafiği\n\n- [HATA] GA4 çekilemedi: {e}\n"]

    report = "\n".join(header + body)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[+] Rapor yazıldı -> {OUT_MD}")

    if "--telegram" in sys.argv:
        cc, ci = summary_metrics
        tg = (f"<b>📈 ParaFOMO haftalık özet</b>\n"
              f"Dönem: {start} → {end}\n\n"
              f"🔍 Arama: {cc} tıklama, {ci} gösterim\n"
              f"Tam rapor: docs/analytics-report.md")
        post_telegram(tg)


if __name__ == "__main__":
    sys.exit(main())
