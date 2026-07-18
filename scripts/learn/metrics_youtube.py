#!/usr/bin/env python3
"""
ParaFOMO — YouTube Shorts metrik toplayıcı.

Ledger'daki youtube kayıtlarının video_id'lerini alır, YouTube API'den performans
çeker ve data/learning/metrics.jsonl'a zaman-serisi olarak ekler.

İki katman:
  • Data API (videos.list part=statistics) → viewCount, likeCount, commentCount
  • Analytics API (reports.query) → averageViewPercentage (RETENTION = asıl kalite
    sinyali, abone sayısından bağımsız), averageViewDuration

Kimlik: ~/.config/parafomo/youtube_oauth.json. Gerekli scope:
  youtube.readonly + yt-analytics.readonly
Mevcut token yalnız 'upload' ise refresh 'invalid_scope' ile döner → bu script
kanalı ATLAR (boru hattını durdurmaz) ve re-auth talimatını basar.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
REAUTH_MSG = (
    "[yt] YouTube metrikleri için re-auth gerekli. Mevcut token yalnız 'upload' "
    "yetkisine sahip. Çöz: youtube-reauth.py'yi youtube.readonly + "
    "yt-analytics.readonly scope'larıyla çalıştır."
)


def chunked(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def main():
    items = [r for r in lib.read_jsonl(lib.LEDGER) if r["channel"] == "youtube"]
    vids = [r["refs"]["video_id"] for r in items if r["refs"].get("video_id")]
    if not vids:
        print("[yt] ledger'da video yok"); return 0

    creds = lib.youtube_credentials(SCOPES)
    if creds is None:
        print("[yt] youtube_oauth.json yok, atlandı"); return 0

    from googleapiclient.discovery import build
    from google.auth.exceptions import RefreshError

    stats = {}      # vid -> {views,likes,comments}
    try:
        yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
        for batch in chunked(vids, 50):
            r = yt.videos().list(part="statistics", id=",".join(batch)).execute()
            for it in r.get("items", []):
                s = it["statistics"]
                stats[it["id"]] = {
                    "views": int(s.get("viewCount", 0)),
                    "likes": int(s.get("likeCount", 0)),
                    "comments": int(s.get("commentCount", 0)),
                }
    except RefreshError:
        print(REAUTH_MSG); return 0
    except Exception as e:
        print(f"[yt] Data API hata: {type(e).__name__}: {str(e)[:200]}"); return 0

    # Analytics: retention (per-video), tek sorgu (video boyutu + filtre)
    retention = {}  # vid -> {avg_view_pct, avg_view_sec}
    try:
        ya = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
        # başlangıç: en eski yayın tarihi (yoksa 90 gün)
        dates = [lib.parse_dt(r.get("published_utc")) for r in items if r.get("published_utc")]
        dates = [d for d in dates if d]
        start = (min(dates).date().isoformat() if dates
                 else (lib.now_utc().date().replace(day=1)).isoformat())
        end = lib.now_utc().date().isoformat()
        for batch in chunked(vids, 200):
            rep = ya.reports().query(
                ids="channel==MINE",
                startDate=start, endDate=end,
                dimensions="video",
                metrics="views,averageViewPercentage,averageViewDuration",
                filters="video==" + ",".join(batch),
                maxResults=200,
            ).execute()
            headers = [h["name"] for h in rep.get("columnHeaders", [])]
            for row in rep.get("rows", []):
                rec = dict(zip(headers, row))
                vid = rec.get("video")
                if vid:
                    retention[vid] = {
                        "avg_view_pct": rec.get("averageViewPercentage"),
                        "avg_view_sec": rec.get("averageViewDuration"),
                    }
    except RefreshError:
        print("[yt] Analytics scope yok — retention atlandı (sadece izlenme/beğeni)")
    except Exception as e:
        print(f"[yt] Analytics hata (retention atlandı): {type(e).__name__}: {str(e)[:150]}")

    rows = []
    fetched = lib.iso()
    for r in items:
        vid = r["refs"].get("video_id")
        if not vid or vid not in stats:
            continue
        m = dict(stats[vid])
        m.update(retention.get(vid, {}))
        rows.append({"id": r["id"], "channel": "youtube", "fetched_utc": fetched, "metrics": m})
    lib.append_jsonl(lib.METRICS, rows)
    print(f"[+] yt metrik eklendi: {len(rows)} video "
          f"({'retention VAR' if retention else 'retention YOK'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
