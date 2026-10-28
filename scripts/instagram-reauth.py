#!/usr/bin/env python3
"""
ParaFOMO — Meta token yenileme: TEK yeniden yetkilendirme iki kapıyı birden açar.

  • instagram_manage_insights → IG reach/kaydetme/paylaşma metrikleri (öğrenme döngüsü)
  • pages_manage_posts        → Facebook sayfasına Reel + link paylaşımı
                                 (scripts/facebook-reel.py · scripts/facebook-post.py)
Mevcut IG yayın izinleri korunur. Saf urllib; google_auth_oauthlib GEREKMEZ.

2 adımlı manuel akış (headless sunucu için):

  1) İzin listesi + yönerge (mevcut token'da olanlar ✓ işaretli):
       python3 scripts/instagram-reauth.py scopes

  2) developers.facebook.com → Tools → Graph API Explorer'da (uygulaman seçili)
     "Generate Access Token" ile izinleri onayla (sayfa seçiminde Parafomo'yu seç);
     çıkan KISA ömürlü USER token'ı kopyala, sonra:
       python3 scripts/instagram-reauth.py exchange "<KISA_USER_TOKEN>"
     → uzun-ömürlü user token → sayfa token'ı → izinleri DOĞRULAR → instagram.env
       güncellenir (eskisi .bak'a). Zorunlu izinlerden biri eksikse ya da istenenlerin
       (insights / pages_manage_posts) hiçbiri yoksa KAYDETMEZ.

NOT: Bu izinler Business tipi uygulamada, uygulamanın admin/developer/tester'ı VE varlık
sahibi olan hesap için App Review olmadan verilebilir. ParaFOMO hesabı bu koşulu sağlıyor.
"""
import os
import sys
import json
import urllib.parse
import urllib.request
import urllib.error

ENV = os.path.expanduser("~/.config/parafomo/instagram.env")
GRAPH = "https://graph.facebook.com/v21.0"

# content_publish + comments + insights + FB sayfa paylaşımı → mevcut yayın hattı da çalışmaya devam eder
NEEDED = [
    "instagram_basic",
    "instagram_manage_insights",     # IG metrikleri
    "instagram_manage_comments",
    "instagram_content_publish",
    "pages_show_list",
    "pages_read_engagement",
    "pages_manage_posts",            # FB sayfası: Reel + link gönderisi
    "pages_manage_engagement",       # FB yorumlarına yanıt (topluluk sinyali)
    "read_insights",                 # FB sayfa/Reel metrikleri (ölçüm)
    "business_management",
]
# Bunlar yoksa token KAYDEDİLMEZ (mevcut IG yayın hattı bozulmasın).
REQUIRED = ["instagram_basic", "instagram_content_publish", "pages_show_list", "pages_read_engagement"]
# Yeniden yetkilendirmenin amacı; en az biri gelmeli, yoksa yeni token bir şey kazandırmaz.
DESIRED = {
    "instagram_manage_insights": "IG reach/kaydetme/paylaşma metrikleri",
    "pages_manage_posts": "Facebook Reel + link paylaşımı (facebook-reel.py / facebook-post.py)",
    "read_insights": "Facebook sayfa/Reel erişim metrikleri",
    "pages_manage_engagement": "Facebook yorumlarına yanıt",
}


def load_env():
    env = {}
    for ln in open(ENV, encoding="utf-8"):
        ln = ln.strip()
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def _get(url):
    try:
        return json.load(urllib.request.urlopen(url, timeout=30))
    except urllib.error.HTTPError as e:
        return {"__error__": e.read().decode()[:400]}
    except Exception as e:
        return {"__error__": f"ağ hatası: {type(e).__name__}"}


def token_scopes(token, app_id, app_secret):
    """debug_token → geçerli token'ın izin listesi; okunamazsa None. (Token yazdırılmaz.)"""
    if not (token and app_id and app_secret):
        return None
    dbg = _get(f"{GRAPH}/debug_token?" + urllib.parse.urlencode({
        "input_token": token, "access_token": f"{app_id}|{app_secret}"}))
    data = dbg.get("data") or {}
    if "__error__" in dbg or not data:
        return None
    return list(data.get("scopes") or []) if data.get("is_valid") else []


def cmd_scopes():
    env = load_env()
    cur = token_scopes(env.get("IG_PAGE_TOKEN"), env.get("IG_APP_ID"), env.get("IG_APP_SECRET"))
    print("\n1) Aç: https://developers.facebook.com/tools/explorer/")
    print(f"2) Sağ üstte uygulamanı seç (App ID {env.get('IG_APP_ID','?')}).")
    print("3) 'Generate Access Token' / 'Get User Access Token' → şu izinleri İŞARETLE:\n")
    for s in NEEDED:
        mark = "" if cur is None else ("  ✓ mevcut token'da var" if s in cur else "  ← mevcut token'da YOK")
        print(f"     - {s}{mark}")
    print("\n4) Onayla (Facebook/Instagram hesabıyla giriş). Sayfa seçim ekranında Parafomo")
    print("   sayfasını ve @parafomo IG hesabını SEÇİLİ bırak (izinler seçili varlıklara verilir).")
    print("   Çıkan KISA ömürlü token'ı kopyala, sonra:")
    print('     python3 scripts/instagram-reauth.py exchange "<KISA_USER_TOKEN>"\n')


def cmd_exchange(short_token):
    env = load_env()
    app_id = env["IG_APP_ID"]
    app_secret = env["IG_APP_SECRET"]
    want_page = env.get("IG_PAGE_ID")

    # 1) kısa → uzun ömürlü USER token
    r = _get(f"{GRAPH}/oauth/access_token?" + urllib.parse.urlencode({
        "grant_type": "fb_exchange_token", "client_id": app_id,
        "client_secret": app_secret, "fb_exchange_token": short_token}))
    if "__error__" in r or "access_token" not in r:
        print(f"HATA: uzun-ömürlü user token alınamadı: {r.get('__error__', r)}")
        return 1
    long_user = r["access_token"]
    print("[1/4] Uzun-ömürlü user token alındı.")

    # 2) sayfa token'ını çek (uzun user token'dan gelen page token'ı süresizdir)
    pg = _get(f"{GRAPH}/me/accounts?" + urllib.parse.urlencode({
        "access_token": long_user, "fields": "id,name,access_token"}))
    if "__error__" in pg or not pg.get("data"):
        print(f"HATA: sayfa listesi alınamadı: {pg.get('__error__', pg)}")
        return 1
    pages = pg["data"]
    page = next((p for p in pages if p["id"] == want_page), None) if want_page else pages[0]
    if page is None:   # eskiden sessizce ilk sayfaya düşüyordu → yanlış sayfanın token'ı kaydedilebilirdi
        print("HATA: IG_PAGE_ID sayfası bu token'ın sayfa listesinde yok — KAYDEDİLMEDİ.")
        print("      İzin ekranındaki sayfa seçiminde Parafomo sayfasını işaretle.")
        print(f"      Gelen sayfalar: {', '.join(p.get('name', '?') for p in pages)}")
        return 1
    page_token = page["access_token"]
    print(f"[2/4] Sayfa token'ı alındı: {page['name']} ({page['id']}).")

    # 3) izinleri DOĞRULA: zorunlular tam + istenenlerden en az biri
    scopes = token_scopes(page_token, app_id, app_secret)
    if scopes is None:
        print("HATA: yeni token doğrulanamadı (debug_token) — KAYDEDİLMEDİ.")
        return 1
    miss_req = [s for s in REQUIRED if s not in scopes]
    gained = [s for s in DESIRED if s in scopes]
    if miss_req or not gained:
        if miss_req:
            print(f"HATA: zorunlu izin(ler) YOK: {', '.join(miss_req)} — KAYDEDİLMEDİ "
                  "(mevcut IG yayın hattı bozulmasın).")
        else:
            print(f"HATA: istenen izinlerin hiçbiri yok ({', '.join(DESIRED)}) — KAYDEDİLMEDİ "
                  "(yeni token bir şey kazandırmaz).")
        print("      Graph API Explorer'da izinleri İŞARETLEDİĞİNDEN ve sayfayı seçtiğinden emin ol;")
        print("      gerekirse uygulama rolünü / Development-mode varlık sahipliğini kontrol et.")
        print(f"      Gelen izinler: {', '.join(scopes) or '(yok / token geçersiz)'}")
        return 1
    print("[3/4] Doğrulandı: zorunlu izinler tam. İstenen izinler:")
    for s, use in DESIRED.items():
        print(f"      {'✓ VAR ' if s in scopes else '✗ YOK '} {s} — {use}")
    old = token_scopes(env.get("IG_PAGE_TOKEN"), app_id, app_secret)
    lost = sorted(set(old or []) - set(scopes))
    if lost:
        print(f"      Not: eski token'da olup yenisinde olmayan izinler: {', '.join(lost)}")
        if "instagram_manage_comments" in lost:
            print("      UYARI: instagram_manage_comments yok → IG Reel ilk-yorum tohumu atlanır.")

    # 4) instagram.env güncelle (yedekle)
    lines = open(ENV, encoding="utf-8").read().splitlines()
    out, seen = [], False
    for ln in lines:
        if ln.strip().startswith("IG_PAGE_TOKEN="):
            out.append(f"IG_PAGE_TOKEN={page_token}"); seen = True
        else:
            out.append(ln)
    if not seen:
        out.append(f"IG_PAGE_TOKEN={page_token}")
    os.replace(ENV, ENV + ".bak")
    fd = os.open(ENV, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)   # sır dosyası: yalnız sahibi okur
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"[4/4] instagram.env güncellendi (eski → {ENV}.bak).")
    if "instagram_manage_insights" in scopes:
        print("      Artık metrics_instagram.py reach/kaydetme/paylaşma çekebilir.")
    if "pages_manage_posts" in scopes:
        print("      Artık facebook-reel.py / facebook-post.py sayfaya paylaşır (hat değişikliği gerekmez).")
    missing = [s for s in DESIRED if s not in scopes]
    if missing:
        print(f"      Eksik kalan: {', '.join(missing)} → aynı akışla tekrar yetkilendirip ekleyebilirsin.")
    return 0


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("scopes", "exchange"):
        print("kullanım: instagram-reauth.py scopes | exchange \"<KISA_USER_TOKEN>\"")
        return 1
    if sys.argv[1] == "scopes":
        cmd_scopes(); return 0
    if len(sys.argv) < 3:
        print("kullanım: instagram-reauth.py exchange \"<KISA_USER_TOKEN>\""); return 1
    return cmd_exchange(sys.argv[2])


if __name__ == "__main__":
    sys.exit(main())
