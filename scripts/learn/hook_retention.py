#!/usr/bin/env python3
"""
ParaFOMO — Shorts KANCA (ilk-3sn) tutma ölçer.

Neden: genel averageViewPercentage bizim düşük-n kohortumuzda yüksek varyanslı →
hook/başlık edit deneyleri bugüne dek HEP 'inconclusive' kapandı (confound kök nedeni,
bkz. video-rnd.md 2026-09-25 bulgu #1). Bu script daha İZOLE bir sinyal çeker:
YouTube Analytics `elapsedVideoTimeRatio` retention eğrisini alıp videonun ilk ~3
saniyesindeki `audienceWatchRatio`'yu (= "izleyicinin kaçı 3sn'e kadar KALDI") verir.
Böylece hook-edit deneyleri nihayet ayrışabilir (genel retention yerine 3sn-hold'a bak).

Kaynak: developers.google.com/youtube/analytics/dimensions (elapsedVideoTimeRatio →
100 nokta 0.01..1.0; audienceWatchRatio = o ana kadar izlenme / toplam izlenme).

Çıktı: data/learning/hook-retention.json + konsol tablosu.
Kimlik + scope: metrics_youtube.py ile aynı (youtube.readonly + yt-analytics.readonly).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
OUT = os.path.join(lib.DATA, "hook-retention.json")
MAX_VIDEOS = 20  # en yeni N Short (maliyet: video başına 1 Analytics sorgusu)
HOLD_SEC = 3.0   # "swipe or stay" penceresi


def parse_duration(iso_dur):
    """PT#M#S → saniye."""
    m = re.match(r"PT(?:(\d+)M)?(?:(\d+)S)?", iso_dur or "")
    if not m:
        return None
    mins = int(m.group(1) or 0)
    secs = int(m.group(2) or 0)
    return mins * 60 + secs


def hold_at(rows, headers, target_ratio):
    """elapsedVideoTimeRatio eğrisinde target_ratio'ya EN YAKIN noktanın
    (audienceWatchRatio, relativeRetentionPerformance) çiftini döner.

    NOT: Shorts'ta audienceWatchRatio 1.0'ı AŞABİLİR (loop/yeniden-izleme →
    erken kısım kişi-başı >1 kez izlenir; yüksek = güçlü kanca + döngü sinyali).
    relativeRetentionPerformance ise 0-1 yüzdelik (benzer-uzunluk videolara göre)."""
    try:
        ri = headers.index("elapsedVideoTimeRatio")
        ai = headers.index("audienceWatchRatio")
    except ValueError:
        return None, None
    rri = headers.index("relativeRetentionPerformance") if "relativeRetentionPerformance" in headers else None
    best = None
    best_rel = None
    best_d = 1e9
    for row in rows:
        r = float(row[ri])
        d = abs(r - target_ratio)
        if d < best_d:
            best_d = d
            best = float(row[ai])
            best_rel = float(row[rri]) if rri is not None and row[rri] is not None else None
    return best, best_rel


def main():
    items = [r for r in lib.read_jsonl(lib.LEDGER) if r["channel"] == "youtube"]
    items = [r for r in items if r["refs"].get("video_id")]
    # en yeni önce
    items.sort(key=lambda r: r.get("published_utc") or "", reverse=True)
    items = items[:MAX_VIDEOS]
    if not items:
        print("[hook] ledger'da video yok"); return 0

    creds = lib.youtube_credentials(SCOPES)
    if creds is None:
        print("[hook] youtube_oauth.json yok, atlandı"); return 0

    from googleapiclient.discovery import build
    from google.auth.exceptions import RefreshError

    vids = [r["refs"]["video_id"] for r in items]

    # süreler (3sn → ratio dönüşümü için)
    durations = {}
    try:
        yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
        for i in range(0, len(vids), 50):
            batch = vids[i:i + 50]
            r = yt.videos().list(part="contentDetails", id=",".join(batch)).execute()
            for it in r.get("items", []):
                durations[it["id"]] = parse_duration(it["contentDetails"].get("duration"))
    except RefreshError:
        print("[hook] re-auth gerekli (yalnız upload scope); atlandı"); return 0
    except Exception as e:
        print(f"[hook] Data API hata: {type(e).__name__}: {str(e)[:150]}"); return 0

    dates = [lib.parse_dt(r.get("published_utc")) for r in items if r.get("published_utc")]
    dates = [d for d in dates if d]
    start = (min(dates).date().isoformat() if dates
             else (lib.now_utc().date().replace(day=1)).isoformat())
    end = lib.now_utc().date().isoformat()

    try:
        ya = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    except Exception as e:
        print(f"[hook] Analytics init hata: {type(e).__name__}: {str(e)[:150]}"); return 0

    results = []
    for r in items:
        vid = r["refs"]["video_id"]
        dur = durations.get(vid)
        if not dur or dur <= 0:
            continue
        target = min(HOLD_SEC / dur, 0.99)
        try:
            rep = ya.reports().query(
                ids="channel==MINE",
                startDate=start, endDate=end,
                dimensions="elapsedVideoTimeRatio",
                metrics="audienceWatchRatio,relativeRetentionPerformance",
                filters="video==" + vid,
            ).execute()
        except RefreshError:
            print("[hook] Analytics scope yok — atlandı"); return 0
        except Exception as e:
            # tek video düşse hat kırılmasın
            print(f"[hook] {vid} atlandı: {type(e).__name__}: {str(e)[:80]}")
            continue
        headers = [h["name"] for h in rep.get("columnHeaders", [])]
        rows = rep.get("rows", [])
        if not rows:
            continue
        hold3, rel3 = hold_at(rows, headers, target)
        if hold3 is None:
            continue
        results.append({
            "id": r["id"],
            "video_id": vid,
            "duration_sec": dur,
            "hold_3s": round(hold3, 3),               # 3sn izlenme/toplam-izlenme (loop ile >1 olabilir)
            "rel_perf_3s": round(rel3, 3) if rel3 is not None else None,  # 0-1 yüzdelik (akran kıyası)
            "published_utc": r.get("published_utc"),
        })

    if not results:
        print("[hook] retention eğrisi çekilemedi (veri yok / scope yok)"); return 0

    payload = {
        "fetched_utc": lib.iso(),
        "hold_sec": HOLD_SEC,
        "n": len(results),
        "median_hold_3s": round(sorted(x["hold_3s"] for x in results)[len(results) // 2], 3),
        "videos": results,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    results.sort(key=lambda x: x["hold_3s"], reverse=True)
    print(f"[+] hook-retention: {len(results)} video · medyan 3sn-hold "
          f"%{payload['median_hold_3s'] * 100:.0f}")
    print(f"    en iyi: {results[0]['id'][:40]} %{results[0]['hold_3s'] * 100:.0f}")
    print(f"    en kötü: {results[-1]['id'][:40]} %{results[-1]['hold_3s'] * 100:.0f}")
    print(f"    → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
