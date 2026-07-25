#!/usr/bin/env python3
"""
ParaFOMO — DÜRÜST ÖLÇÜM PANOSU.

Tek soruya cevap verir: "Sistem işe yarıyor mu?"
Anlık kare değil TREND gösterir (son 8 hafta) ve otomasyonun kendi ürettiği
gürültüyü (Direct trafik ≈ sen + botlar) gerçek organik erişimden AYIRIR.

Kuzey yıldızı: 1000 ziyaretçi/gün = 7000/hafta. Pano her metriği bu hedefe
olan mesafeyle ve büyüme yönüyle ("büyüyor mu, düz mü, düşüyor mu") raporlar.

Bölümler:
  1) Organik trafik trendi (GA4)  — gerçek erişim büyüyor mu? Direct ayrı.
  2) Google arama trendi (GSC)    — tık/gösterim haftalık + en iyi sıra.
  3) YouTube motoru (Data API)    — toplam izlenme + siteye gerçek dönüşüm.
  4) DÜRÜST HÜKÜM                  — hedefe mesafe, darboğaz teşhisi, ne işe yarıyor.

Kimlik: ~/.config/parafomo/ga-sa.json (GSC+GA4), youtube_oauth.json (YT).

Kullanım:
  /root/.venvs/parafomo/bin/python scripts/dashboard.py
  /root/.venvs/parafomo/bin/python scripts/dashboard.py --telegram
"""
import logging
import os
import sys
from collections import defaultdict
from datetime import date, timedelta

logging.getLogger("google.auth").setLevel(logging.ERROR)
logging.getLogger("google.oauth2").setLevel(logging.ERROR)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "learn"))

KEY = os.path.expanduser("~/.config/parafomo/ga-sa.json")
YT_OAUTH = os.path.expanduser("~/.config/parafomo/youtube_oauth.json")
GSC_SITE = "sc-domain:parafomo.com"
GA4_PROPERTY = "542292605"
OUT_MD = os.path.join(ROOT, "docs", "dashboard.md")

WEEKS = 8
GOAL_DAILY = 1000
GOAL_WEEKLY = GOAL_DAILY * 7

GSC_SCOPE = ["https://www.googleapis.com/auth/webmasters.readonly"]
GA4_SCOPE = ["https://www.googleapis.com/auth/analytics.readonly"]
YT_SCOPE = ["https://www.googleapis.com/auth/youtube.readonly"]


# ----------------------------- yardımcı -----------------------------

def spark(values):
    """Sayı listesini minik bir kıvılcım-çizgisine çevir."""
    if not values:
        return ""
    blocks = "▁▂▃▄▅▆▇█"
    lo, hi = min(values), max(values)
    if hi == lo:
        return blocks[0] * len(values)
    return "".join(blocks[int((v - lo) / (hi - lo) * (len(blocks) - 1))] for v in values)


def trend_word(values):
    """Son 3 kovaya bakıp yönü Türkçe döndür."""
    tail = [v for v in values if v is not None][-3:]
    if len(tail) < 2:
        return "veri az"
    if tail[-1] > tail[0]:
        return "📈 artıyor"
    if tail[-1] < tail[0]:
        return "📉 düşüyor"
    return "➡️ düz"


def week_buckets(n=WEEKS):
    """Bugünden geriye n tam haftanın (pzt-paz) (baslangic,bitis) sınırları, eskiden yeniye."""
    today = date.today()
    # en yakın geçmiş pazartesi
    this_mon = today - timedelta(days=today.weekday())
    out = []
    for i in range(n, 0, -1):
        start = this_mon - timedelta(weeks=i)
        end = start + timedelta(days=6)
        out.append((start, end))
    return out


# ----------------------------- GA4 -----------------------------

def ga4_client():
    from google.oauth2 import service_account
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    creds = service_account.Credentials.from_service_account_file(KEY, scopes=GA4_SCOPE)
    return BetaAnalyticsDataClient(credentials=creds)


def ga4_weekly_channels(client, start, end):
    """isoYearWeek × kanal → activeUsers. {(hafta): {kanal: users}}"""
    from google.analytics.data_v1beta.types import (
        RunReportRequest, DateRange, Dimension, Metric,
    )
    req = RunReportRequest(
        property=f"properties/{GA4_PROPERTY}",
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
        dimensions=[Dimension(name="isoYearIsoWeek"), Dimension(name="sessionDefaultChannelGroup")],
        metrics=[Metric(name="activeUsers")],
        limit=500,
    )
    res = client.run_report(req)
    out = defaultdict(lambda: defaultdict(int))
    for row in res.rows:
        wk = row.dimension_values[0].value
        ch = row.dimension_values[1].value or "(other)"
        out[wk][ch] += int(row.metric_values[0].value)
    return out


def ga4_section(client):
    lines = ["## 1) Organik trafik trendi (GA4 — son 8 hafta)", ""]
    start = date.today() - timedelta(weeks=WEEKS)
    end = date.today()
    data = ga4_weekly_channels(client, start, end)
    weeks = sorted(data.keys())
    if not weeks:
        lines += ["- (henüz trafik yok)", ""]
        return lines, {"organic_last": 0, "direct_share": 0, "organic_series": []}

    organic_series, direct_series, total_series = [], [], []
    for wk in weeks:
        ch = data[wk]
        direct = ch.get("Direct", 0)
        total = sum(ch.values())
        organic = total - direct  # Direct dışı = gerçek erişim (arama+sosyal+referral)
        organic_series.append(organic)
        direct_series.append(direct)
        total_series.append(total)

    lines.append(f"| Hafta | Gerçek erişim (Direct hariç) | Direct (≈sen/bot) | Toplam |")
    lines.append(f"|---|---|---|---|")
    for wk, o, d, t in zip(weeks, organic_series, direct_series, total_series):
        lines.append(f"| {wk} | {o} | {d} | {t} |")
    lines.append("")
    lines.append(f"**Gerçek erişim trendi:** `{spark(organic_series)}`  {trend_word(organic_series)}")
    last_total = total_series[-1] or 1
    direct_share = direct_series[-1] / last_total * 100
    lines.append(f"**Son hafta Direct payı:** %{direct_share:.0f} "
                 f"(yüksekse trafik gerçek ziyaretçi değil, senin/botların erişimi)")
    lines.append("")

    # Son 4 hafta kanal kırılımı (gerçek erişim nereden geliyor?)
    lines.append("**Gerçek erişim kaynağı (son 4 hafta toplamı):**")
    agg = defaultdict(int)
    for wk in weeks[-4:]:
        for ch, u in data[wk].items():
            if ch != "Direct":
                agg[ch] += u
    if not agg:
        lines.append("- (Direct dışında hiç erişim yok — organik/sosyal/referral = 0)")
    for ch, u in sorted(agg.items(), key=lambda kv: -kv[1]):
        lines.append(f"- {ch}: {u} kullanıcı")
    lines.append("")
    return lines, {
        "organic_last": organic_series[-1],
        "direct_share": direct_share,
        "organic_series": organic_series,
    }


# ----------------------------- GSC -----------------------------

def gsc_client():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds = service_account.Credentials.from_service_account_file(KEY, scopes=GSC_SCOPE)
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def gsc_daily(sc, start, end, dimensions=None, row_limit=1000):
    body = {"startDate": start.isoformat(), "endDate": end.isoformat(), "rowLimit": row_limit}
    if dimensions:
        body["dimensions"] = dimensions
    return sc.searchanalytics().query(siteUrl=GSC_SITE, body=body).execute().get("rows", [])


def gsc_section(sc):
    lines = ["## 2) Google arama trendi (GSC — son 8 hafta)", ""]
    buckets = week_buckets()
    span_start = buckets[0][0]
    span_end = buckets[-1][1]
    rows = gsc_daily(sc, span_start, span_end, ["date"])
    by_date = {r["keys"][0]: r for r in rows}

    lines.append("| Hafta | Tıklama | Gösterim | CTR |")
    lines.append("|---|---|---|---|")
    click_series = []
    for (s, e) in buckets:
        clicks = imps = 0
        d = s
        while d <= e:
            r = by_date.get(d.isoformat())
            if r:
                clicks += int(r["clicks"])
                imps += int(r["impressions"])
            d += timedelta(days=1)
        ctr = (clicks / imps * 100) if imps else 0
        click_series.append(clicks)
        lines.append(f"| {s.isoformat()} | {clicks} | {imps} | %{ctr:.1f} |")
    lines.append("")
    lines.append(f"**Tıklama trendi:** `{spark(click_series)}`  {trend_word(click_series)}")
    lines.append("")

    # En iyi sıralanan sorgu — otorite darboğazının kanıtı
    q = gsc_daily(sc, span_start, span_end, ["query"], 1000)
    ranked = [x for x in q if x["impressions"] >= 3]
    best = sorted(ranked, key=lambda x: x["position"])[:8]
    lines.append("**En iyi sıralanan sorgular (gösterim≥3):**")
    if not best:
        lines.append("- (yeterli veri yok)")
    best_pos = 999
    for x in best:
        best_pos = min(best_pos, x["position"])
        lines.append(f"- `{x['keys'][0]}` — sıra {x['position']:.1f}, "
                     f"gös {int(x['impressions'])}, tık {int(x['clicks'])}")
    lines.append("")

    # Kıl-payı fırsatlar (sıra 4-20): otomasyonun gerçekten iyileştirebileceği tek yer
    opp = [x for x in q if 4 <= x["position"] <= 20 and x["impressions"] >= 5]
    lines.append("**🎯 Ulaşılabilir fırsatlar (sıra 4-20, gösterim≥5):**")
    if not opp:
        lines.append("- (YOK — hiçbir sorgu ilk 2 sayfada değil; bu = otorite darboğazı)")
    for x in sorted(opp, key=lambda x: -x["impressions"])[:8]:
        lines.append(f"- `{x['keys'][0]}` — sıra {x['position']:.1f}, gös {int(x['impressions'])}")
    lines.append("")
    return lines, {"clicks_last": click_series[-1], "best_pos": best_pos, "opportunities": len(opp)}


# ----------------------------- YouTube -----------------------------

def yt_section():
    lines = ["## 3) YouTube motoru", ""]
    if not os.path.exists(YT_OAUTH):
        lines += ["- (youtube_oauth.json yok)", ""]
        return lines, {}
    try:
        import json
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        cfg = json.load(open(YT_OAUTH))
        creds = Credentials(
            token=None, refresh_token=cfg["refresh_token"],
            client_id=cfg["client_id"], client_secret=cfg["client_secret"],
            token_uri="https://oauth2.googleapis.com/token", scopes=YT_SCOPE,
        )
        yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
        r = yt.channels().list(part="statistics", mine=True).execute()
        s = r["items"][0]["statistics"]
        subs = int(s.get("subscriberCount", 0))
        views = int(s.get("viewCount", 0))
        vids = int(s.get("videoCount", 0))
        lines.append(f"- **Abone:** {subs}  ·  **Toplam izlenme:** {views:,}  ·  **Video:** {vids}")
        lines.append(f"- İzlenme/abone dönüşümü: **{(subs/views*100 if views else 0):.2f}%** "
                     f"(izleyen kaç kişi abone/huniye giriyor)")
        lines.append("")
        return lines, {"subs": subs, "views": views, "videos": vids}
    except Exception as e:
        lines += [f"- (YouTube çekilemedi: {type(e).__name__}: {str(e)[:120]})",
                  "- (yalnız 'upload' scope'u varsa readonly re-auth gerekir)", ""]
        return lines, {}


# ----------------------------- HÜKÜM -----------------------------

def verdict(ga, gsc, yt):
    lines = ["## 4) 🎯 DÜRÜST HÜKÜM", ""]
    organic = ga.get("organic_last", 0)
    weekly_goal = GOAL_WEEKLY
    pct = organic / weekly_goal * 100
    lines.append(f"**Hedef:** {GOAL_DAILY} ziyaretçi/gün = {weekly_goal:,}/hafta gerçek erişim.")
    lines.append(f"**Gerçek durum:** son hafta **{organic}** gerçek ziyaretçi "
                 f"= hedefin **%{pct:.2f}**'si. Kalan: **{weekly_goal - organic:,}** kişi/hafta.")
    lines.append("")

    flags = []
    if ga.get("direct_share", 0) >= 50:
        flags.append(f"⚠️ Trafiğin %{ga['direct_share']:.0f}'i Direct — bu büyük ihtimalle "
                     f"sen + botlar, gerçek keşif değil. Çıplak sayıya güvenme.")
    if gsc.get("best_pos", 999) > 10:
        flags.append(f"🔴 **KÖK DARBOĞAZ:** en iyi sorgu bile {gsc['best_pos']:.0f}. sırada "
                     f"(1. sayfa = ilk 10). Hiçbir sayfa görünür değil → sorun içerik değil, "
                     f"**site otoritesi**. Daha çok yazı bunu ÇÖZMEZ.")
    if gsc.get("opportunities", 0) == 0:
        flags.append("🔴 Sıra 4-20 aralığında hiç sorgu yok → otomasyonun başlık/CTR ile "
                     "iyileştirebileceği bir hedef bile yok. Önce sıralama lazım.")
    org_series = ga.get("organic_series", [])
    if len([v for v in org_series if v]) >= 3 and trend_word(org_series).startswith("➡️"):
        flags.append("⚠️ Gerçek erişim haftalardır düz — mevcut otomasyon iğneyi oynatmıyor.")
    if yt.get("views", 0) > 1000 and organic <= 5:
        flags.append(f"💡 YouTube'da {yt['views']:,} izlenme var ama siteye ~0 akıyor. "
                     f"En büyük kullanılmayan kaldıraç: YouTube→site hunisi.")

    if flags:
        lines.append("**Teşhis:**")
        lines += [f"- {f}" for f in flags]
    else:
        lines.append("- Belirgin kırmızı bayrak yok; trend ve hedef mesafesine bak.")
    lines.append("")
    lines.append("**Özet:** Öğrenme döngüsü ses/format/slot optimize ediyor ama yukarıdaki "
                 "darboğaz oralarda değil. Sistemin 'kendi kendine öğrenip uygulaması' için "
                 "önce ölçülen darboğaza (otorite/dağıtım) yönlendirilmesi gerekir.")
    lines.append("")
    return lines


def post_telegram(text):
    env = {}
    try:
        for ln in open(os.path.join(ROOT, ".env")):
            ln = ln.strip()
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.split("=", 1)
                env[k.strip()] = v.strip()
    except OSError:
        return
    token, chat = env.get("TELEGRAM_BOT_TOKEN"), env.get("TELEGRAM_CHAT_ID")
    if not (token and chat):
        return
    import urllib.request, urllib.parse
    data = urllib.parse.urlencode({
        "chat_id": chat, "text": text, "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    try:
        urllib.request.urlopen(
            urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data),
            timeout=15)
        print("[+] Telegram'a gönderildi")
    except Exception as e:
        print(f"[!] Telegram gönderilemedi: {e}")


def main():
    header = [
        "# ParaFOMO — Dürüst Ölçüm Panosu",
        "",
        f"> Üretim: {date.today().isoformat()} · `scripts/dashboard.py` · "
        f"soru: *sistem işe yarıyor mu?*",
        "",
    ]
    body, ga, gsc, yt = [], {}, {}, {}
    try:
        lines, ga = ga4_section(ga4_client())
        body += lines
    except Exception as e:
        body += [f"## 1) Organik trafik\n\n- [HATA] GA4: {e}\n"]
    try:
        lines, gsc = gsc_section(gsc_client())
        body += lines
    except Exception as e:
        body += [f"## 2) Google arama\n\n- [HATA] GSC: {e}\n"]
    lines, yt = yt_section()
    body += lines
    body += verdict(ga, gsc, yt)

    report = "\n".join(header + body)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print(f"\n[+] Pano yazıldı -> {OUT_MD}")

    if "--telegram" in sys.argv:
        organic = ga.get("organic_last", 0)
        pct = organic / GOAL_WEEKLY * 100
        tg = (f"<b>🎯 ParaFOMO dürüst pano</b>\n"
              f"Son hafta gerçek erişim: <b>{organic}</b> (hedefin %{pct:.2f}'si)\n"
              f"En iyi Google sırası: {gsc.get('best_pos', '?')}\n"
              f"YouTube izlenme: {yt.get('views', '?'):,}\n"
              f"Tam pano: docs/dashboard.md")
        post_telegram(tg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
