#!/usr/bin/env python3
"""
ParaFOMO — YouTube abone-büyütme ekstraları (yükleme SONRASI, best-effort).

Yüklenen Short için:
  1) Format'a göre PUBLIC oynatma listesini bulur/oluşturur ve videoyu ekler
     (kanalda "seri" hissi → abone sebebi).
  2) Videoya abone-CTA yorumu atar (kanal sahibi yorumu; sabitlemeyi YouTube API
     desteklemez → gerekirse Studio'dan elle sabitlenir).

GEREKSİNİM: youtube_oauth.json'ın scope'u youtube.force-ssl olmalı. Mevcut token
sadece youtube.upload ise API 403 verir → `youtube-reauth.py` ile yeniden yetkilendir.
Bu betik hata olsa da 0 döner (pipeline'ı düşürmez); durum stderr'e yazılır.

Kullanım: python3 scripts/youtube-extras.py <slug> [--format <key>] [--no-comment]
"""
import os
import re
import sys
import json
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "public", "social")
OAUTH = "/root/.config/parafomo/youtube_oauth.json"
PL_CACHE = "/root/.config/parafomo/youtube_playlists.json"   # {format: playlist_id}
SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"

# format → oynatma listesi başlığı (kanaldaki seri)
PLAYLIST_TITLES = {
    "comparison": "Karşılaştırma: Kim Kazandırdı?",
    "myth": "Finans Mitleri",
    "shock_number": "Şok Veriler",
    "news_reaction": "Piyasa Gündemi",
    "single_concept": "60 Saniyede Kavram",
    "backtest_return": "Geri Dönük Getiri",
}
DEFAULT_PL = "ParaFOMO Shorts"

BLOG_DIR = os.path.join(ROOT, "src", "content", "blog")


def funnel_comment(slug):
    """Sabit yorum: blog shortsa YAZIYA, viralse ana sayfaya link (huni + backlink)."""
    if os.path.exists(os.path.join(BLOG_DIR, f"{slug}.md")):
        url = f"https://parafomo.com/blog/{slug}/"
        return (f"📖 Bu videonun tam yazısı (ücretsiz rehber):\n👉 {url}\n\n"
                "🔔 Her gün finans için ABONE OL!")
    return ("👉 Her gün altın, dolar, borsa ve halka arz analizleri burada. "
            "Kaçırmamak için ABONE OL! 📊 Detaylar: https://parafomo.com")


def get_service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    cfg = json.load(open(OAUTH))
    creds = Credentials(
        token=None, refresh_token=cfg["refresh_token"],
        client_id=cfg["client_id"], client_secret=cfg["client_secret"],
        token_uri="https://oauth2.googleapis.com/token", scopes=[SCOPE])
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def _load_pl_cache():
    if os.path.exists(PL_CACHE):
        try:
            return json.load(open(PL_CACHE))
        except Exception:
            return {}
    return {}


def _save_pl_cache(d):
    os.makedirs(os.path.dirname(PL_CACHE), exist_ok=True)
    json.dump(d, open(PL_CACHE, "w"), ensure_ascii=False, indent=2)


def ensure_playlist(yt, fmt):
    title = PLAYLIST_TITLES.get(fmt, DEFAULT_PL)
    cache = _load_pl_cache()
    if title in cache:
        return cache[title], title
    # mevcut oynatma listelerinde ara
    req = yt.playlists().list(part="snippet", mine=True, maxResults=50)
    while req is not None:
        resp = req.execute()
        for it in resp.get("items", []):
            if it["snippet"]["title"] == title:
                cache[title] = it["id"]; _save_pl_cache(cache)
                return it["id"], title
        req = yt.playlists().list_next(req, resp)
    # yoksa oluştur (public)
    resp = yt.playlists().insert(
        part="snippet,status",
        body={"snippet": {"title": title,
                          "description": f"ParaFOMO — {title}. Günlük finans Shorts'ları."},
              "status": {"privacyStatus": "public"}}).execute()
    cache[title] = resp["id"]; _save_pl_cache(cache)
    return resp["id"], title


def add_to_playlist(yt, playlist_id, video_id):
    yt.playlistItems().insert(
        part="snippet",
        body={"snippet": {"playlistId": playlist_id,
                          "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute()


def post_comment(yt, video_id, text):
    yt.commentThreads().insert(
        part="snippet",
        body={"snippet": {"videoId": video_id,
                          "topLevelComment": {"snippet": {"textOriginal": text}}}}).execute()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--format", default="")
    ap.add_argument("--no-comment", action="store_true")
    args = ap.parse_args()

    meta_path = os.path.join(OUT_DIR, f"short-{args.slug}.json")
    if not os.path.exists(meta_path):
        print(f"[i] meta yok: {meta_path}", file=sys.stderr); return 0
    meta = json.load(open(meta_path, encoding="utf-8"))
    video_id = meta.get("video_id")
    if not video_id:
        print("[i] video_id yok (yükleme yapılmamış?) — ekstralar atlanıyor", file=sys.stderr); return 0

    try:
        yt = get_service()
    except Exception as e:
        print(f"[i] YouTube servisi kurulamadı: {str(e)[:90]}", file=sys.stderr); return 0

    fmt = args.format or meta.get("format", "")
    # 1) oynatma listesi
    try:
        pid, title = ensure_playlist(yt, fmt)
        add_to_playlist(yt, pid, video_id)
        print(f"[+] Oynatma listesine eklendi: '{title}' ({pid})", file=sys.stderr)
    except Exception as e:
        msg = str(e)
        scope_hint = " → youtube-reauth.py ile force-ssl yetkisi gerekiyor" if "insufficient" in msg.lower() or "403" in msg else ""
        print(f"[i] Oynatma listesi atlandı: {msg[:120]}{scope_hint}", file=sys.stderr)

    # 2) abone CTA yorumu
    if not args.no_comment:
        try:
            post_comment(yt, video_id, funnel_comment(args.slug))
            print("[+] Abone CTA yorumu atıldı (sabitlemeyi Studio'dan yapabilirsin)", file=sys.stderr)
        except Exception as e:
            print(f"[i] Yorum atılamadı: {str(e)[:120]}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
