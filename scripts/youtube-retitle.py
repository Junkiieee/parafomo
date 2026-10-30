#!/usr/bin/env python3
"""YouTube arama başlık turu (roadmap R3 / week T26).

İzlenmenin ~%19-21'i YouTube aramasından geliyor. Bu betik son N günün en çok izlenen videolarını listeler ve
aranan kalıplarla (data/learning/yt-search-terms.json) eşleşmeyi gösterir; yeni başlıkları ajan/insan yazar
(videonun söylediğiyle birebir, abartısız, konu + yıl/ay ilk 40 karakterde) ve --apply ile uygulanır.

  python3 scripts/youtube-retitle.py --dry [--days 60] [--top 20] [--out agent/state/yt-retitle-candidates.json]
  python3 scripts/youtube-retitle.py --apply PLAN.json --baseline agent/memory/yt-retitle-YYYY-MM.json --search-share 18.8

PLAN.json: [{"id": "...", "title": "yeni başlık"}, ...]. Uygulamadan ÖNCE baz (eski başlık + izlenme + arama payı)
baseline dosyasına yazılır; videos.update part=snippet, categoryId/tags/description/defaultLanguage geri gönderilir.
Kota: videos.update 50 birim/video.
"""
import argparse
import datetime as dt
import importlib.util
import json
import sys

# force-ssl kapsamlı servis (upload kapsamı channels/videos.list okuyamaz)
spec = importlib.util.spec_from_file_location("yu", "scripts/youtube-extras.py")
yu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(yu)


def recent_videos(yt, days):
    ch = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    ids, token = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=token).execute()
        stop = False
        for it in r["items"]:
            pub = dt.datetime.fromisoformat(it["contentDetails"]["videoPublishedAt"].replace("Z", "+00:00"))
            if pub < since:
                stop = True
                continue
            ids.append(it["contentDetails"]["videoId"])
        token = r.get("nextPageToken")
        if stop or not token:
            break
    vids = []
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="snippet,statistics", id=",".join(ids[i:i + 50])).execute()
        for v in r["items"]:
            vids.append({"id": v["id"], "title": v["snippet"]["title"], "published": v["snippet"]["publishedAt"][:10],
                         "views": int(v["statistics"].get("viewCount", 0))})
    return sorted(vids, key=lambda v: -v["views"])


def search_terms():
    try:
        return [t for t, _ in json.load(open("data/learning/yt-search-terms.json", encoding="utf-8"))["terms"]]
    except Exception:
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--days", type=int, default=60)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--out", default="agent/state/yt-retitle-candidates.json")
    ap.add_argument("--apply")
    ap.add_argument("--baseline")
    ap.add_argument("--search-share", type=float, help="YouTube araması payı % (28g, brief §1b) — baz için")
    a = ap.parse_args()
    yt = yu.get_service()

    if a.apply:
        if not a.baseline:
            sys.exit("--apply için --baseline gerekli")
        plan = json.load(open(a.apply, encoding="utf-8"))
        bad = [p for p in plan if not p.get("title") or len(p["title"]) > 100]
        if bad:
            sys.exit(f"geçersiz başlık: {bad}")
        base = {"tarih": dt.date.today().isoformat(), "yt_search_share_28g": a.search_share, "videos": []}
        items = {}
        for i in range(0, len(plan), 50):
            r = yt.videos().list(part="snippet,statistics", id=",".join(p["id"] for p in plan[i:i + 50])).execute()
            items.update({v["id"]: v for v in r["items"]})
        for p in plan:
            v = items[p["id"]]
            base["videos"].append({"id": p["id"], "eski": v["snippet"]["title"], "yeni": p["title"],
                                   "views_at_change": int(v["statistics"].get("viewCount", 0))})
        json.dump(base, open(a.baseline, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"baz yazıldı → {a.baseline}")
        ok = 0
        for p in plan:
            sn = items[p["id"]]["snippet"]
            if sn["title"] == p["title"]:
                continue
            body = {"id": p["id"], "snippet": {"title": p["title"], "description": sn.get("description", ""),
                                               "categoryId": sn["categoryId"], "tags": sn.get("tags", []),
                                               "defaultLanguage": sn.get("defaultLanguage", "tr")}}
            try:
                yt.videos().update(part="snippet", body=body).execute()
                ok += 1
                print(f"✓ {p['id']}: {sn['title']!r} → {p['title']!r}")
            except Exception as e:  # tek video hatası turu durdurmasın
                print(f"✗ {p['id']}: {e}")
        print(f"güncellendi: {ok}/{len(plan)}")
        return

    terms = search_terms()
    vids = recent_videos(yt, a.days)[:a.top]
    for v in vids:
        low = v["title"].lower()
        v["eslesen_arama"] = [t for t in terms if t in low]
    json.dump(vids, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for v in vids:
        print(f"{v['views']:>6} {v['published']} {v['id']} {v['title']}  {v['eslesen_arama'] or ''}")
    print(f"→ {a.out}")


if __name__ == "__main__":
    main()
