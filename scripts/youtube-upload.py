#!/usr/bin/env python3
"""
ParaFOMO — YouTube Shorts yükleyici.

shorts-build.py'nin ürettiği public/social/short-<slug>.json metasını okur ve
videoyu YouTube'a yükler. OAuth refresh-token ~/.config/parafomo/youtube_oauth.json'da.

Kullanım:
  python3 scripts/youtube-upload.py <slug> [--privacy unlisted|private|public]
Çıktı: yüklenen videonun URL'si (+ meta json'a video_id yazılır).
"""
import os
import sys
import json
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "public", "social")
BLOG_DIR = os.path.join(ROOT, "src", "content", "blog")
OAUTH = "/root/.config/parafomo/youtube_oauth.json"
CATEGORY_EDUCATION = "27"


def site_url_for(slug):
    """Slug bir blog yazısıysa o yazıya, değilse (viral standalone) ana sayfaya link.
    HUNİ: her Short izleyicisini siteye çeker + bağlamsal backlink üretir."""
    if os.path.exists(os.path.join(BLOG_DIR, f"{slug}.md")):
        return f"https://parafomo.com/blog/{slug}/"
    return "https://parafomo.com"


def with_utm(url):
    """Huni linkine UTM etiketi ekle → GA4 'YouTube→site' trafiğini Direct'ten AYIRIR.
    Ölçüm olmadan huninin çalışıp çalışmadığı bilinemez (24K izlenme → siteye ~0)."""
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}utm_source=youtube&utm_medium=shorts&utm_campaign=funnel"


def with_funnel(description, slug):
    """Açıklamaya siteye yönlendiren altbilgi + abone CTA ekle (huni)."""
    url = with_utm(site_url_for(slug))
    is_article = "parafomo.com/blog/" in url
    lead = "📖 Konunun tam rehberi (ücretsiz):" if is_article else "📊 Günlük altın/dolar/borsa analizleri:"
    footer = (f"\n\n———\n{lead}\n👉 {url}\n\n"
              "🔔 Kaçırmamak için ABONE OL — her gün yeni finans içeriği.\n\n"
              "#finans #para #yatırım #ekonomi #borsa #altın #dolar")
    return (description[:4900 - len(footer)] + footer)


def get_service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    cfg = json.load(open(OAUTH))
    creds = Credentials(
        token=None,
        refresh_token=cfg["refresh_token"],
        client_id=cfg["client_id"],
        client_secret=cfg["client_secret"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def set_shorts_thumbnail(yt, vid, video_path):
    """Shorts kapak karesini AÇIKÇA ayarla (2026-07 özelliği).

    Kapak, swipe-player'da GÖRÜNMEZ ama kanal grid'i, arama, abonelik feed'i ve
    ana sayfa Shorts rafında görünür → keşfedilebilirliği (dolayısıyla izlenmeyi)
    etkiler. Varsayılan kapak çoğu zaman rastgele/bulanık bir orta kare olur; v5.1
    ile frame-0 zaten tam-parlak, kalın kanca metinli tasarlanmış kare → onu kapak
    yaparak grid/arama/abonelik yüzeylerini kontrol ediyoruz.

    Non-fatal: kanal custom-thumbnail'a uygun değilse (doğrulanmamış) veya kare
    çıkarılamazsa yükleme akışı KIRILMAZ, sadece uyarı basılır.
    """
    import subprocess, tempfile
    try:
        from googleapiclient.http import MediaFileUpload
        cover = os.path.join(tempfile.gettempdir(), f"cover-{vid}.jpg")
        # 0.35sn: hook metni tam çizilmiş, hâlâ ilk saniye içinde (v5.1 fade'siz açılış).
        r = subprocess.run(
            ["ffmpeg", "-y", "-ss", "0.35", "-i", video_path,
             "-frames:v", "1", "-q:v", "2", cover],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        if r.returncode != 0 or not os.path.exists(cover):
            print("    [kapak] kare çıkarılamadı — atlanıyor (non-fatal)")
            return
        yt.thumbnails().set(
            videoId=vid, media_body=MediaFileUpload(cover, mimetype="image/jpeg")
        ).execute()
        print("    [kapak] custom Shorts thumbnail ayarlandı (frame-0 kanca karesi)")
    except Exception as e:
        # 403 (doğrulanmamış kanal / özellik yok) dahil her hata non-fatal.
        print(f"    [kapak] ayarlanamadı (non-fatal): {str(e)[:140]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--privacy", default="unlisted",
                    choices=["public", "unlisted", "private"])
    args = ap.parse_args()

    meta_path = os.path.join(OUT_DIR, f"short-{args.slug}.json")
    if not os.path.exists(meta_path):
        print(f"HATA: meta yok: {meta_path} (önce shorts-build.py çalıştır)"); return 1
    meta = json.load(open(meta_path, encoding="utf-8"))
    video = meta["file"]
    if not os.path.exists(video):
        print(f"HATA: video yok: {video}"); return 1

    from googleapiclient.http import MediaFileUpload
    yt = get_service()
    body = {
        "snippet": {
            "title": meta["title"][:100],
            "description": with_funnel(meta["description"], args.slug),
            "tags": meta.get("tags", []),
            "categoryId": CATEGORY_EDUCATION,
            "defaultLanguage": "tr",
        },
        "status": {
            "privacyStatus": args.privacy,
            "selfDeclaredMadeForKids": False,
        },
    }
    print(f"[*] Yükleniyor: {meta['title']}  ({args.privacy})")
    media = MediaFileUpload(video, chunksize=-1, resumable=True, mimetype="video/mp4")
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"    %{int(status.progress()*100)}")
    vid = resp["id"]
    url = f"https://youtube.com/shorts/{vid}"
    print(f"[+] YÜKLENDI: {url}")
    # Kapak karesini açıkça ayarla (keşfedilebilirlik — grid/arama/abonelik yüzeyleri).
    set_shorts_thumbnail(yt, vid, video)
    meta["video_id"] = vid
    meta["youtube_url"] = url
    json.dump(meta, open(meta_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
