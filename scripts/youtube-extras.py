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

Tekrar koruması (denetim sosyal-2, 2026-11-18): yapılan adımlar meta'ya "yt_extras" olarak yazılır
({video_id, playlist, comment, ts}); aynı video için ikinci koşu listeye yeniden eklemez, yorumu yeniden atmaz
(--force ile yeniden yapar). Yorumdaki ve "link"teki parafomo.com adresleri sitede açılmıyorsa
(scripts/lib/funnel.py) blog/araç sayfasına çevrilir (#41 '/asgari-ucret/' 404 dersi).

Kullanım: python3 scripts/youtube-extras.py <slug> [--format <key>] [--no-comment] [--force] [--dry]
"""
import os
import re
import sys
import json
import argparse
import datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "lib"))
import funnel  # noqa: E402
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
    # olay sonucu (scripts/event-short.py) — seri kimliği: "rakam açıklanınca ilk burada" (abone vaadi)
    "event_result": "Açıklandı: Faiz, Enflasyon ve Zamlar",
    # karakterli haftalık seri (scripts/anim/kits/defter.js)
    "ekonomi_defteri": "Ekonomi Defteri",
    # 2026-11-17: karakterli kısa animasyon hikâyeler (scripts/anim/engines/hikaye.py, otomatik hat hikaye_uret.py)
    "para_hikayesi": "Para Hikâyeleri",
}
DEFAULT_PL = "ParaFOMO Shorts"
PLAYLIST_DESC = {
    "Para Hikâyeleri": "Paranın başına gelenler: eriyen yüzlük, şişip küçülen maaş zarfı, enflasyon canavarı... "
                       "Resmî rakamlarla (TÜİK, Resmî Gazete, TCMB) 40 saniyelik animasyon hikâyeler. Yatırım tavsiyesi değildir.",
}

BLOG_DIR = os.path.join(ROOT, "src", "content", "blog")


def funnel_comment(slug, meta=None):
    """Sabit yorum: blog shortsa YAZIYA, viralse ana sayfaya link (huni + backlink).
    Olay sonucu videosu (meta.link): ilgili hesaplama sayfası + seri vaadi (abone dönüşümü %0,07 — RC 10-28)."""
    meta = meta or {}
    link = meta.get("link")
    if link and funnel.sayfa_yolu(link, ROOT) is None:   # sitede açılmayan link yoruma girmesin
        print(f"[i] link sitede açılmıyor, yorumda kullanılmadı: {link}", file=sys.stderr)
        link = None
    if meta.get("comment"):   # bölüme özel yorum (Ekonomi Defteri, Para hikâyeleri)
        yedek, _ = funnel.huni_url(slug, meta.get("title", ""), link or "", ROOT)
        text, degisen = funnel.linkleri_duzelt(meta["comment"], yedek, ROOT)
        if degisen:
            print(f"[i] yorumdaki geçersiz adres düzeltildi: {', '.join(degisen)} → {yedek}", file=sys.stderr)
        return text
    if link:
        url = link if link.startswith("http") else "https://parafomo.com/" + link.lstrip("/")
        return (f"🧮 Kendi rakamını hesapla (ücretsiz): {url}\n\n"
                "🔔 Faiz kararı, enflasyon, kira ve emekli zammı açıklanır açıklanmaz rakamı ilk burada gör — "
                "ABONE OL, bildirimi aç.")
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
                          "description": PLAYLIST_DESC.get(title, f"ParaFOMO — {title}. Günlük finans Shorts'ları.")},
              "status": {"privacyStatus": "public"}}).execute()
    cache[title] = resp["id"]; _save_pl_cache(cache)
    return resp["id"], title


def add_to_playlist(yt, playlist_id, video_id):
    yt.playlistItems().insert(
        part="snippet",
        body={"snippet": {"playlistId": playlist_id,
                          "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute()


def post_comment(yt, video_id, text):
    return yt.commentThreads().insert(
        part="snippet",
        body={"snippet": {"videoId": video_id,
                          "topLevelComment": {"snippet": {"textOriginal": text}}}}).execute()


def kaydet(meta_path, durum):
    """Taze oku + yalnız yt_extras alanını yaz (IG/FB'nin alanları ezilmesin)."""
    try:
        cur = json.load(open(meta_path, encoding="utf-8"))
        cur["yt_extras"] = durum
        json.dump(cur, open(meta_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[i] meta'ya yt_extras yazılamadı: {str(e)[:90]}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--format", default="")
    ap.add_argument("--no-comment", action="store_true")
    ap.add_argument("--force", action="store_true", help="yapılmış adımları da yeniden yap")
    ap.add_argument("--dry", action="store_true", help="YouTube'a dokunmadan liste + yorumu yazdır")
    args = ap.parse_args()

    meta_path = os.path.join(OUT_DIR, f"short-{args.slug}.json")
    if not os.path.exists(meta_path):
        print(f"[i] meta yok: {meta_path}", file=sys.stderr); return 0
    meta = json.load(open(meta_path, encoding="utf-8"))
    video_id = meta.get("video_id")
    fmt = args.format or meta.get("format", "")
    if args.dry:
        print(f"[dry] liste: {PLAYLIST_TITLES.get(fmt, DEFAULT_PL)} · video_id: {video_id or '-'} · "
              f"yapılmış: {meta.get('yt_extras') or '-'}\n[dry] yorum:\n{funnel_comment(args.slug, meta)}")
        return 0
    if not video_id:
        print("[i] video_id yok (yükleme yapılmamış?) — ekstralar atlanıyor", file=sys.stderr); return 0
    durum = meta.get("yt_extras") or {}
    if args.force or durum.get("video_id") != video_id:   # yeni yükleme (ya da zorla) → baştan
        durum = {}
    durum["video_id"] = video_id
    yap_liste = not durum.get("playlist")
    yap_yorum = not args.no_comment and not durum.get("comment")
    if not (yap_liste or yap_yorum):
        print(f"[i] ekstralar zaten yapılmış ({durum.get('ts', '?')}) — atlandı (yeniden: --force)", file=sys.stderr)
        return 0

    try:
        yt = get_service()
    except Exception as e:
        print(f"[i] YouTube servisi kurulamadı: {str(e)[:90]}", file=sys.stderr); return 0

    # 1) oynatma listesi
    if not yap_liste:
        print(f"[i] Oynatma listesi zaten eklendi ({durum['playlist']}) — atlandı", file=sys.stderr)
    else:
        try:
            pid, title = ensure_playlist(yt, fmt)
            add_to_playlist(yt, pid, video_id)
            durum["playlist"] = pid
            print(f"[+] Oynatma listesine eklendi: '{title}' ({pid})", file=sys.stderr)
        except Exception as e:
            msg = str(e)
            scope_hint = " → youtube-reauth.py ile force-ssl yetkisi gerekiyor" if "insufficient" in msg.lower() or "403" in msg else ""
            print(f"[i] Oynatma listesi atlandı: {msg[:120]}{scope_hint}", file=sys.stderr)

    # 2) abone CTA yorumu
    if yap_yorum:
        try:
            r = post_comment(yt, video_id, funnel_comment(args.slug, meta))
            durum["comment"] = (r or {}).get("id") or True
            print("[+] Abone CTA yorumu atıldı (sabitlemeyi Studio'dan yapabilirsin)", file=sys.stderr)
        except Exception as e:
            print(f"[i] Yorum atılamadı: {str(e)[:120]}", file=sys.stderr)
    elif not args.no_comment:
        print("[i] Yorum zaten atıldı — atlandı", file=sys.stderr)

    durum["ts"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    kaydet(meta_path, durum)
    return 0


if __name__ == "__main__":
    # YAYIN DURDURMA BAYRAĞI (Kaan 2026-10-30): diğer yayıncılarla aynı — dosya varsa yalnız ONAYLI_YAYIN=1 ile
    # (kuyruk.py yayinla bunu verir). Denetim sosyal-2: bu betik bayrağı hiç okumayan tek yayıncıydı.
    if os.path.exists("/root/parafomo-data/PUBLISH_PAUSED") and "--dry" not in sys.argv and os.environ.get("ONAYLI_YAYIN") != "1":
        print("[durduruldu] /root/parafomo-data/PUBLISH_PAUSED var — ekstralar yapılmadı.", file=sys.stderr); sys.exit(0)
    sys.exit(main())
