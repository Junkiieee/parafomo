#!/usr/bin/env python3
"""
ParaFOMO — yeni blog yazısını Facebook sayfasına LİNK gönderisi olarak paylaşır.

Facebook'ta link TIKLANIR (Shorts/IG'nin aksine) → siteye doğrudan trafik; 35-54 yaş
kitlemizin ana mecrası. Önizleme kartını (görsel/başlık/açıklama) FB sayfanın og
etiketlerinden kendisi kurar → önce yazının CANLI olmasını bekler (404'ü önbelleğe almasın).

Akış: yazı canlı mı (HTTP 200, en çok --wait sn) → POST /{page_id}/feed
      message = başlık + açıklama + konu sorusu · link = /blog/<slug>/?utm_…&utm_campaign=post
      → logs/fb-posts.json'a slug → post id (idempotent: aynı yazı iki kez gitmez).

İzin yoksa (pages_manage_posts) tek satır uyarı + exit 0 — izin gelince değişiklik gerekmez.
Diğer hatalar tek satır + exit 0 (--strict ile 2). Durum: logs/fb-status.json (dry hariç).

Kullanım: python3 scripts/facebook-post.py [<slug> | --latest] [--dry] [--root PATH]
                                           [--wait SN] [--strict]
  slug verilmezse / --latest: docs/daily-log.md'deki en yeni "Yayınlanan yazı".
  --dry: ağa yazmaz, dosyalara dokunmaz; mesajı + planlanan çağrıyı + izni gösterir.
Ortak yardımcılar (env, Graph, izin, durum dosyası) facebook-reel.py'den gelir.
"""
import argparse
import importlib.util
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIVE_EVERY = 15


def _load_fb():
    spec = importlib.util.spec_from_file_location(
        "parafomo_facebook_reel", os.path.join(SCRIPT_DIR, "facebook-reel.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fb = None


def say(msg):
    print(msg, flush=True)


def latest_slug(root):
    """daily-log.md: "Yayınlanan yazı" + /blog/ içeren İLK satır (post-telegram.sh ile aynı)."""
    try:
        with open(os.path.join(root, "docs", "daily-log.md"), encoding="utf-8") as fh:
            for ln in fh:
                if "Yayınlanan yazı" in ln:
                    m = re.search(r"\(/blog/([^)/\s]+)/?\)", ln)
                    if m:
                        return m.group(1)
    except OSError:
        pass
    return ""


def build_message(post, slug):
    title = str(post.get("title") or slug).strip()
    desc = str(post.get("description") or "").strip()
    parts = [title]
    if desc and fb._norm(desc) != fb._norm(title):
        parts.append(desc)
    parts.append(f"💬 {fb.pick_question(slug, title)}")
    return "\n\n".join(parts)


def posts_path(root):
    return os.path.join(root, "logs", "fb-posts.json")


def load_posted(root):
    try:
        with open(posts_path(root), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def http_code(url):
    req = urllib.request.Request(url, headers={"User-Agent": "parafomo-fb/1.0",
                                               "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None


def wait_live(url, wait):
    deadline = time.time() + max(0, wait)
    while True:
        code = http_code(url)
        if code == 200:
            return True, code
        if time.time() + LIVE_EVERY > deadline:
            return False, code
        time.sleep(LIVE_EVERY)


def run(a, root):
    slug = (a.slug or "").strip().strip("/")
    if a.latest or not slug:
        slug = latest_slug(root)
        if not slug:
            return fb.fail(root, "?", "docs/daily-log.md'den yazı slug'ı çıkarılamadı",
                           a.strict, kind="post", dry=a.dry)
    post_file = fb.blog_post_path(root, slug)
    if not os.path.isfile(post_file):
        return fb.fail(root, slug, f"yazı yok: {post_file}", a.strict, kind="post", dry=a.dry)
    post = fb.read_frontmatter(post_file)
    if post.get("draft") is True:
        return fb.fail(root, slug, "yazı taslak (draft: true) — paylaşılmadı", a.strict,
                       kind="post", dry=a.dry)
    message = build_message(post, slug)
    link = fb.site_url(slug, "post", True)
    live_url = f"{fb.SITE}/blog/{slug}/"
    done = load_posted(root).get(slug)
    env = fb.load_env()
    page_id, tok = env.get("IG_PAGE_ID"), env.get("IG_PAGE_TOKEN")

    if a.dry:
        say("[fb] DRY — ağa hiçbir şey yazılmaz, dosyalara dokunulmaz")
        say(f"[fb] yazı : {post_file}")
        say(f"[fb] link : {link}")
        code = http_code(live_url)
        say(f"[fb] canlı: HTTP {code} {'✓' if code == 200 else '✗ (gerçek koşu en çok --wait sn bekler)'}"
            f" — {live_url}")
        say(f"[fb] ----- mesaj ({len(message)} karakter) -----")
        say(message)
        say("[fb] ----------------------------------")
        say(f"[fb] planlanan çağrı: POST {fb.API}/{page_id or '<IG_PAGE_ID>'}/feed  "
            "message=<yukarıdaki> link=<yukarıdaki>  (önizleme kartı og etiketlerinden)")
        say(f"[fb] sonra yaz: logs/fb-posts.json ← {{\"{slug}\": \"<post_id>\"}} · logs/fb-status.json")
        if done:
            say(f"[fb] not  : zaten paylaşılmış (post id {done}) → gerçek koşu ATLAR")
        has, note = fb.perm_status(env)
        tail = (" → gerçek koşu sessizce atlar (Kaan: python3 scripts/instagram-reauth.py scopes)"
                if has is False else "")
        say(f"[fb] izin : {note}{tail}")
        return 0

    if done:
        say(f"[fb] atlandı: zaten paylaşılmış → https://www.facebook.com/{done}")
        fb.write_status(root, True, "zaten paylaşılmış", slug, "post")
        return 0
    if not (page_id and tok):
        return fb.fail(root, slug, "kimlik eksik: instagram.env'de IG_PAGE_ID / IG_PAGE_TOKEN yok",
                       a.strict, kind="post")
    # Salt-okunur ön kontrol: izin kesin yoksa canlılık beklemeden çık (bilinmiyorsa dene).
    has, note = fb.perm_status(env)
    if has is False:
        say(fb.PERM_LINE)
        fb.write_status(root, False, f"izin yok: {note}", slug, "post")
        return 0
    live, code = wait_live(live_url, a.wait)
    if not live:
        return fb.fail(root, slug, f"yazı henüz canlı değil (HTTP {code}): {live_url} — sonra tekrar dene",
                       a.strict, kind="post")

    res, err = fb.graph_post(f"{page_id}/feed", {"message": message, "link": link}, tok)
    if err:
        if fb.is_perm_error(err):
            return fb.perm_skip(root, slug, err, kind="post")
        return fb.fail(root, slug, f"paylaşılamadı: {fb.err_text(err)}", a.strict, kind="post")
    post_id = str((res or {}).get("id") or "")
    if not post_id:
        return fb.fail(root, slug, f"yanıtta gönderi id yok: {fb.scrub(res)[:120]}", a.strict, kind="post")
    posted = load_posted(root)                  # taze oku (arada başka koşu yazmış olabilir)
    posted[slug] = post_id
    fb.write_json_atomic(posts_path(root), posted)
    say(f"[fb] ✅ PAYLAŞILDI: https://www.facebook.com/{post_id}")
    fb.write_status(root, True, "paylaşıldı", slug, "post")
    return 0


def main(argv=None):
    global fb
    try:
        sys.stdout.reconfigure(errors="backslashreplace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Blog yazısını Facebook sayfasına link gönderisi olarak paylaşır.")
    ap.add_argument("slug", nargs="?", default="", help="blog slug'ı (yoksa daily-log'daki en yeni)")
    ap.add_argument("--latest", action="store_true", help="daily-log.md'deki en yeni yazı")
    ap.add_argument("--dry", action="store_true", help="ağa/dosyaya yazma; mesaj + planı göster")
    ap.add_argument("--root", default="", help="repo kökü (vars.: $PARAFOMO_ROOT ya da betiğin reposu)")
    ap.add_argument("--wait", type=int, default=600, help="yazının canlı olmasını en çok kaç sn bekle")
    ap.add_argument("--strict", action="store_true", help="izin-dışı hatalarda exit 2")
    a = ap.parse_args(argv)
    try:
        fb = _load_fb()
    except Exception as e:
        print(f"[fb] HATA: facebook-reel.py yüklenemedi: {type(e).__name__}: {e}", flush=True)
        return 2 if a.strict else 0
    root = fb.resolve_root(a.root)
    try:
        return run(a, root)
    except Exception as e:                      # beklenmeyen her şey: tek satır, hat kırılmaz
        return fb.fail(root, a.slug or "?", f"beklenmeyen hata: {type(e).__name__}: {e}", a.strict,
                       kind="post", dry=a.dry)


if __name__ == "__main__":
    # YAYIN DURDURMA BAYRAĞI (Kaan 2026-10-30): dosya varsa hiçbir şey yayınlanmaz (--dry serbest)
    import os as _os, sys as _sys
    if _os.path.exists("/root/parafomo-data/PUBLISH_PAUSED") and "--dry" not in _sys.argv and _os.environ.get("ONAYLI_YAYIN") != "1":
        print("[durduruldu] /root/parafomo-data/PUBLISH_PAUSED var — yayın yapılmadı."); _sys.exit(0)
    sys.exit(main())
