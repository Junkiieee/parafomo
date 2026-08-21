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


# Konu → İLGİLİ ARAÇ SAYFASI eşlemesi (huni iyileştirme). Blog olmayan viral Short'un
# funnel linki jenerik ana sayfa yerine konuya uygun interaktif araca gider → izleyici
# değerli bir sayfaya iner (jenerik ana sayfadan daha iyi landing). Retention'ı ve hashtag
# arama bloğunu ETKİLEMEZ — ayrı funnel/UTM yüzeyi.
_TOOL_MAP = [
    ("kdv", "/kdv-hesaplama"),
    ("altın", "/altin-hesaplama"), ("altin", "/altin-hesaplama"), ("gram", "/altin-hesaplama"),
    ("asgari", "/asgari-ucret-hesaplama"),
    ("net maaş", "/net-maas-hesaplama"), ("net maas", "/net-maas-hesaplama"),
    ("maaş", "/net-maas-hesaplama"), ("maas", "/net-maas-hesaplama"),
    ("kıdem", "/kidem-tazminati-hesaplama"), ("kidem", "/kidem-tazminati-hesaplama"),
    ("tazminat", "/kidem-tazminati-hesaplama"),
    ("kira", "/kira-artis-orani-hesaplama"),
    ("kredi", "/kredi-hesaplama"), ("taksit", "/kredi-hesaplama"),
    ("bileşik", "/bilesik-faiz-hesaplama"), ("bilesik", "/bilesik-faiz-hesaplama"),
    ("mevduat", "/mevduat-faizi-hesaplama"),
    ("enflasyon", "/enflasyon-takvimi"), ("tüfe", "/enflasyon-takvimi"), ("tufe", "/enflasyon-takvimi"),
    ("tcmb", "/tcmb-faiz-takvimi"),
    ("fed", "/fed-faiz-takvimi"), ("fomc", "/fed-faiz-takvimi"),
    ("halka arz", "/halka-arz"), ("ipo", "/halka-arz"),
]


def tool_url_for(slug, title=""):
    """Blog olmayan Short için konuya en uygun araç sayfası URL'i (yoksa ana sayfa)."""
    hay = f"{slug} {title}".lower()
    for kw, path in _TOOL_MAP:
        if kw in hay:
            return f"https://parafomo.com{path}"
    return "https://parafomo.com/ekonomik-takvim"


def with_utm(url):
    """Huni linkine UTM etiketi ekle → GA4 'YouTube→site' trafiğini Direct'ten AYIRIR.
    Ölçüm olmadan huninin çalışıp çalışmadığı bilinemez (24K izlenme → siteye ~0)."""
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}utm_source=youtube&utm_medium=shorts&utm_campaign=funnel"


# Konu → hashtag eşlemesi. IG'de KANITLANDI (08-06-2 / 08-08-2): konuya-duyarlı niş
# etiketler jenerik geniş bloktan daha iyi keşif havuzu hedefler. Aynı ders YouTube
# Shorts açıklamasına taşındı — her videoya aynı statik #finans #para... bloğu yerine
# slug/başlıktan türeyen konu etiketleri (Shorts ARAMA/keşif yüzeyi; retention'ı etkilemez).
_TAG_MAP = [
    ("altın", ["#altın", "#gramaltın"]), ("gram-altin", ["#altın", "#gramaltın"]),
    ("dolar", ["#dolar", "#döviz"]), ("döviz", ["#döviz"]), ("euro", ["#euro"]),
    ("fed", ["#fed", "#faiz"]), ("faiz", ["#faiz", "#merkezbankası"]),
    ("tcmb", ["#tcmb", "#faiz"]), ("enflasyon", ["#enflasyon", "#tüfe"]),
    ("tüfe", ["#enflasyon", "#tüfe"]), ("kira", ["#kira", "#kiraartışı"]),
    ("kredi", ["#kredi"]), ("mevduat", ["#mevduat", "#faiz"]),
    ("kıdem", ["#kıdemtazminatı", "#tazminat"]), ("tazminat", ["#tazminat"]),
    ("borsa", ["#borsa", "#bist100"]), ("bist", ["#borsa", "#bist100"]),
    ("hisse", ["#hissesenedi", "#borsa"]), ("temettü", ["#temettü", "#borsa"]),
    ("etf", ["#etf", "#yatırımfonu"]), ("fon", ["#yatırımfonu"]),
    ("tahvil", ["#tahvil"]), ("eurobond", ["#eurobond", "#döviz"]),
    ("bitcoin", ["#bitcoin", "#kripto"]), ("kripto", ["#kripto"]),
    ("bes", ["#bes", "#emeklilik"]), ("emeklilik", ["#emeklilik"]),
    ("tasarruf", ["#tasarruf", "#birikim"]), ("bütçe", ["#bütçe", "#tasarruf"]),
    ("nfp", ["#abdekonomisi", "#fed"]), ("gdp", ["#ekonomi"]), ("pmi", ["#ekonomi"]),
]


def topic_hashtags(slug, title=""):
    """Slug + başlıktan konuya-duyarlı hashtag üret (jenerik statik blok yerine)."""
    text = (slug + " " + (title or "")).lower()
    tags = ["#parafomo", "#finans"]
    for key, tg in _TAG_MAP:
        if key in text:
            for t in tg:
                if t not in tags:
                    tags.append(t)
    # Konu az sinyal verdiyse birkaç geniş etiketle tamamla (asla boş kalmasın).
    for filler in ["#ekonomi", "#yatırım", "#para"]:
        if len(tags) >= 8:
            break
        if filler not in tags:
            tags.append(filler)
    return " ".join(tags[:9])


def with_funnel(description, slug, title=""):
    """Açıklamaya siteye yönlendiren altbilgi + abone CTA + konu hashtag'leri ekle (huni)."""
    base = site_url_for(slug)
    is_article = "parafomo.com/blog/" in base
    # Blog değilse: jenerik ana sayfa yerine konuya uygun interaktif araç sayfası (daha iyi landing + huni).
    if not is_article:
        base = tool_url_for(slug, title)
    url = with_utm(base)
    is_tool = "/hesaplama" in base or "-takvimi" in base or "/halka-arz" in base
    if is_article:
        lead = "📖 Konunun tam rehberi (ücretsiz):"
    elif is_tool:
        lead = "🧮 İlgili ücretsiz hesaplama/veri aracı:"
    else:
        lead = "📊 Günlük altın/dolar/borsa analizleri:"
    footer = (f"\n\n———\n{lead}\n👉 {url}\n\n"
              "🔔 Kaçırmamak için ABONE OL — her gün yeni finans içeriği.\n\n"
              + topic_hashtags(slug, title))
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
            "description": with_funnel(meta["description"], args.slug, meta.get("title", "")),
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
