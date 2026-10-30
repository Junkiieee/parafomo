#!/usr/bin/env python3
"""Uzun-form videoyu YouTube'a yükle / yayına al.

    python3 scripts/longform/lf_upload.py upload <slug> [--privacy private|unlisted|public] [--at ISO8601]
    python3 scripts/longform/lf_upload.py publish <slug>     # gizliyi herkese aç + sabit yorum + oynatma listesi

upload: başlık, açıklama (özet + tıklanabilir site linki UTM'li + bölüm zaman damgaları + kaynak), etiketler,
        özel kapak (1280x720, lf_scenes.thumbnail), Türkçe altyazı (SRT), abonelere bildirim yalnız public'te.
Varsayılan GİZLİ: Kaan izleyip onaylamadan herkese açılmaz (ilk denemeler için). --at verilirse zamanlanmış
yayın (YouTube private + publishAt ister).
Yetki: youtube_oauth.json force-ssl (youtube-extras ile aynı token).
"""
import argparse
import importlib.util
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lf_common import OUT_DIR, ROOT  # noqa: E402

PLAYLIST = "Rehber Videoları: Zamlar, Vergiler ve Hesaplar"


def _extras():
    spec = importlib.util.spec_from_file_location("yt_extras", os.path.join(ROOT, "scripts", "youtube-extras.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def utm(url, slug):
    url = url if url.startswith("http") else "https://parafomo.com/" + url.lstrip("/")
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}utm_source=youtube&utm_medium=longform&utm_campaign={slug}"


def description(meta):
    slug = meta["slug"]
    parts = [meta.get("description", "").strip()]
    links = []
    if meta.get("link"):
        links.append(f"🧮 Kendi rakamını hesapla (ücretsiz): {utm(meta['link'], slug)}")
    if meta.get("source"):
        links.append(f"📖 Kaynaklı tam rehber: {utm(meta['source'], slug)}")
    if links:
        parts.append("\n".join(links))
    if meta.get("chapters_valid") and meta.get("chapters"):
        parts.append("Bölümler:\n" + "\n".join(meta["chapters"]))
    parts.append("Rakamlar resmî kaynaklara (TÜİK, Resmî Gazete, Gelir İdaresi) dayanır; bilgilendirme amaçlıdır, "
                 "yatırım veya vergi tavsiyesi değildir.")
    parts.append("🔔 Zam, vergi ve faiz rakamları açıklanır açıklanmaz burada: ABONE OL, bildirimi aç.")
    tags = ["#parafomo", "#2027zamları", "#vergi"] if "2027" in meta["title"] else ["#parafomo", "#finans"]
    parts.append(" ".join(tags[:3]))
    return "\n\n".join(p for p in parts if p)[:4900]


def load_meta(slug):
    p = os.path.join(OUT_DIR, f"{slug}.meta.json")
    return p, json.load(open(p, encoding="utf-8"))


def upload(a):
    from googleapiclient.http import MediaFileUpload
    path, meta = load_meta(a.slug)
    ex = _extras()
    yt = ex.get_service()
    status = {"privacyStatus": a.privacy, "selfDeclaredMadeForKids": False}
    if a.at:
        status.update({"privacyStatus": "private", "publishAt": a.at})
    body = {"snippet": {"title": meta["title"][:100], "description": description(meta),
                        "tags": meta.get("tags", [])[:15], "categoryId": "27",
                        "defaultLanguage": "tr", "defaultAudioLanguage": "tr"},
            "status": status}
    print(f"[lf-up] yükleniyor: {meta['title']} ({status['privacyStatus']}{' @ ' + a.at if a.at else ''})")
    req = yt.videos().insert(part="snippet,status", body=body, notifySubscribers=(a.privacy == "public"),
                             media_body=MediaFileUpload(meta["file"], chunksize=8 * 1024 * 1024,
                                                        resumable=True, mimetype="video/mp4"))
    resp = None
    while resp is None:
        st, resp = req.next_chunk()
        if st:
            print(f"    %{int(st.progress() * 100)}")
    vid = resp["id"]
    meta.update({"video_id": vid, "youtube_url": f"https://youtu.be/{vid}", "privacy": status["privacyStatus"]})
    json.dump(meta, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[lf-up] ✅ {meta['youtube_url']}")
    try:
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(meta["thumbnail"], mimetype="image/jpeg")).execute()
        print("[lf-up] kapak ayarlandı")
    except Exception as e:
        print(f"[lf-up] kapak ayarlanamadı (non-fatal): {str(e)[:160]}")
    if meta.get("srt") and os.path.exists(meta["srt"]):
        try:
            yt.captions().insert(part="snippet",
                                 body={"snippet": {"videoId": vid, "language": "tr", "name": "Türkçe",
                                                   "isDraft": False}},
                                 media_body=MediaFileUpload(meta["srt"], mimetype="application/octet-stream")).execute()
            print("[lf-up] Türkçe altyazı eklendi")
        except Exception as e:
            print(f"[lf-up] altyazı eklenemedi (non-fatal): {str(e)[:160]}")
    return 0


def publish(a):
    path, meta = load_meta(a.slug)
    ex = _extras()
    yt = ex.get_service()
    vid = meta["video_id"]
    yt.videos().update(part="status", body={"id": vid, "status": {"privacyStatus": "public",
                                                                  "selfDeclaredMadeForKids": False}}).execute()
    print(f"[lf-up] herkese açık: {meta['youtube_url']}")
    try:
        ex.PLAYLIST_TITLES["longform"] = PLAYLIST
        pid, title = ex.ensure_playlist(yt, "longform")
        for i in range(3):  # yeni açılan listede ilk ekleme 409 "aborted" verebiliyor
            try:
                ex.add_to_playlist(yt, pid, vid)
                break
            except Exception:
                if i == 2:
                    raise
                import time
                time.sleep(10)
        print(f"[lf-up] oynatma listesi: {title}")
    except Exception as e:
        print(f"[lf-up] oynatma listesi atlandı: {str(e)[:160]}")
    try:
        text = ex.funnel_comment(a.slug, {"link": utm(meta["link"], a.slug)} if meta.get("link") else None)
        yt.commentThreads().insert(part="snippet", body={"snippet": {"videoId": vid, "topLevelComment": {
            "snippet": {"textOriginal": text}}}}).execute()
        print("[lf-up] yönlendirme yorumu eklendi (sabitlemeyi Studio'dan yap — API desteklemiyor)")
    except Exception as e:
        print(f"[lf-up] yorum atlandı: {str(e)[:160]}")
    meta["privacy"] = "public"
    json.dump(meta, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return 0


VENV_PY = "/root/.venvs/parafomo/bin/python"


def main():
    try:
        import googleapiclient  # noqa: F401
    except ImportError:  # sistem python'u → Google kütüphaneleri proje venv'inde
        if os.path.exists(VENV_PY) and sys.executable != VENV_PY:
            os.execv(VENV_PY, [VENV_PY] + sys.argv)
        raise
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("upload")
    u.add_argument("slug")
    u.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    u.add_argument("--at", default="", help="zamanlanmış yayın, ör. 2026-11-03T12:00:00Z")
    u.add_argument("--dry", action="store_true")
    p = sub.add_parser("publish")
    p.add_argument("slug")
    a = ap.parse_args()
    if a.cmd == "upload" and a.dry:
        print(description(load_meta(a.slug)[1]))
        return 0
    return upload(a) if a.cmd == "upload" else publish(a)


if __name__ == "__main__":
    sys.exit(main())
