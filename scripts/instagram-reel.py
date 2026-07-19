#!/usr/bin/env python3
"""
ParaFOMO — Instagram Reels yayıncısı (Shorts mp4'ünü Reel olarak paylaşır).

IG feed görselleri 57 gönderiye 3 takipçi getirdi → Reels'e pivot. Aynı Shorts
videosunu Reel olarak yayınlar (organik erişim feed'den kat kat yüksek).

Video barındırma (TOKEN GEREKTİRMEZ): repo public olduğu için mp4, ayrı bir
`media` dalına git plumbing ile force-push edilir → raw.githubusercontent üzerinden
anında herkese açık URL. IG oradan çeker. Her yayında dal tek dosyaya sıfırlanır
(eski Reel zaten IG'ye alınmıştır → geçmiş şişmez).

Akış: mp4 barındır → Reels container oluştur (media_type=REELS) → status FINISHED
olana kadar bekle → media_publish → reel_id + permalink meta json'a yazılır.

Kullanım: python3 scripts/instagram-reel.py <slug> [--no-publish] [--caption-file F]
Kimlik: ~/.config/parafomo/instagram.env (IG_BUSINESS_ACCOUNT_ID, IG_PAGE_TOKEN)
"""
import os
import re
import sys
import json
import time
import argparse
import subprocess
import urllib.parse
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "public", "social")
BLOG_DIR = os.path.join(ROOT, "src", "content", "blog")
IG_ENV = os.path.expanduser("~/.config/parafomo/instagram.env")
API = "https://graph.facebook.com/v21.0"
REPO_RAW = "https://raw.githubusercontent.com/Junkiieee/parafomo/media"

# Türkçe finans erişim etiketleri (IG en fazla 30; keşfet için geniş+niş karışık)
HASHTAGS = ("#parafomo #finans #para #yatırım #borsa #ekonomi #altın #dolar "
            "#kriptopara #bitcoin #tasarruf #bist100 #faiz #enflasyon #bes "
            "#temettü #hisse #finansalözgürlük #paratüyoları #ekonomihaber")


def load_env():
    env = {}
    for ln in open(IG_ENV, encoding="utf-8"):
        ln = ln.strip()
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def host_video(mp4, name):
    """mp4'ü `media` dalına force-push et → raw URL. Token gerektirmez (SSH push)."""
    blob = subprocess.check_output(["git", "-C", ROOT, "hash-object", "-w", mp4]).decode().strip()
    tree_input = f"100644 blob {blob}\t{name}\n"
    tree = subprocess.run(["git", "-C", ROOT, "mktree"], input=tree_input.encode(),
                          capture_output=True, check=True).stdout.decode().strip()
    commit = subprocess.check_output(
        ["git", "-C", ROOT, "commit-tree", tree, "-m", f"media: {name}"]).decode().strip()
    subprocess.run(["git", "-C", ROOT, "push", "-f", "origin", f"{commit}:refs/heads/media"],
                   check=True, capture_output=True)
    url = f"{REPO_RAW}/{urllib.parse.quote(name)}"
    # raw'ın yayılmasını bekle (kısa)
    for _ in range(10):
        try:
            req = urllib.request.Request(url, method="HEAD")
            if urllib.request.urlopen(req, timeout=15).status == 200:
                return url
        except Exception:
            pass
        time.sleep(2)
    return url  # yine de dene


def site_link(slug):
    if os.path.exists(os.path.join(BLOG_DIR, f"{slug}.md")):
        return f"parafomo.com/blog/{slug}"
    return "parafomo.com"


def _clean(text):
    """YouTube artığını temizle: #Shorts, hashtag satırları, URL/'Daha fazlası' satırları."""
    out = []
    for ln in (text or "").splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.lower().startswith("#") or "http" in s.lower():
            continue
        if s.lower().startswith(("daha fazlası", "detaylar", "detaylı")):
            continue
        out.append(s)
    return " ".join(out).strip()


def build_caption(meta, slug):
    title = re.sub(r"#\w+\s*$", "", meta.get("title", "")).strip()  # sondaki #Shorts vs
    desc = _clean(meta.get("description", ""))
    hook = title or desc[:80]
    body = desc if desc and desc != title else ""
    cta = (f"\n\n📲 Tam rehber (ücretsiz): {site_link(slug)}\n"
           f"🔔 Günlük altın · dolar · borsa · faiz → TAKİP ET @parafomo")
    cap = f"{hook}\n\n{body}{cta}\n\n{HASHTAGS}"
    return cap[:2100]  # IG caption sınırı 2200


def graph_post(path, data):
    body = urllib.parse.urlencode(data).encode()
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(
            f"{API}/{path}", data=body), timeout=60))
    except urllib.error.HTTPError as e:
        return {"__error__": e.read().decode()[:400]}


def graph_get(path, params):
    url = f"{API}/{path}?" + urllib.parse.urlencode(params)
    try:
        return json.load(urllib.request.urlopen(url, timeout=30))
    except urllib.error.HTTPError as e:
        return {"__error__": e.read().decode()[:400]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--no-publish", action="store_true", help="container oluştur ama yayınlama")
    ap.add_argument("--caption-file", default="")
    args = ap.parse_args()

    env = load_env()
    ig = env.get("IG_BUSINESS_ACCOUNT_ID")
    tok = env.get("IG_PAGE_TOKEN")
    if not (ig and tok):
        print("HATA: IG kimliği eksik (instagram.env)"); return 1

    meta_path = os.path.join(OUT_DIR, f"short-{args.slug}.json")
    if not os.path.exists(meta_path):
        print(f"HATA: meta yok: {meta_path}"); return 1
    meta = json.load(open(meta_path, encoding="utf-8"))
    mp4 = meta.get("file") or os.path.join(OUT_DIR, f"short-{args.slug}.mp4")
    if not os.path.exists(mp4):
        print(f"HATA: mp4 yok: {mp4}"); return 1

    if args.caption_file and os.path.exists(args.caption_file):
        caption = open(args.caption_file, encoding="utf-8").read().strip()
    else:
        caption = build_caption(meta, args.slug)

    print(f"[*] Video barındırılıyor (media dalı)...")
    video_url = host_video(mp4, f"{args.slug}.mp4")
    print(f"[+] URL: {video_url}")

    print(f"[*] Reels container oluşturuluyor...")
    cont = graph_post(f"{ig}/media", {
        "media_type": "REELS", "video_url": video_url,
        "caption": caption, "share_to_feed": "true", "access_token": tok})
    if "__error__" in cont or "id" not in cont:
        print(f"HATA: container oluşmadı: {cont.get('__error__', cont)}"); return 2
    cid = cont["id"]
    print(f"[+] container: {cid}")

    # işlenmeyi bekle (video transcode) — FINISHED olana dek
    print("[*] Video işleniyor (bekleniyor)...")
    status = None
    for i in range(40):  # ~5 dk
        st = graph_get(cid, {"fields": "status_code", "access_token": tok})
        status = st.get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            print(f"HATA: IG işleme hatası: {st}"); return 2
        time.sleep(8)
    if status != "FINISHED":
        print(f"HATA: işleme zaman aşımı (son durum: {status})"); return 2
    print("[+] İşleme tamam.")

    if args.no_publish:
        print("[i] --no-publish → yayınlanmadı."); return 0

    pub = graph_post(f"{ig}/media_publish", {"creation_id": cid, "access_token": tok})
    if "__error__" in pub or "id" not in pub:
        print(f"HATA: yayınlanamadı: {pub.get('__error__', pub)}"); return 2
    reel_id = pub["id"]
    perma = graph_get(reel_id, {"fields": "permalink", "access_token": tok}).get("permalink", "")
    print(f"[+] REEL YAYINLANDI: {perma or reel_id}")
    meta["ig_reel_id"] = reel_id
    meta["ig_reel_permalink"] = perma
    json.dump(meta, open(meta_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
