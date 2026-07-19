#!/usr/bin/env python3
"""
ParaFOMO — Instagram/Meta token yenileme (instagram_manage_insights ekler).

Mevcut IG_PAGE_TOKEN'da insights izni yok → reach/kaydetme/paylaşma metrikleri
alınamıyor (#10). Bu betik, YENİ ve insights içeren bir uzun-ömürlü SAYFA token'ı
üretir. google_auth_oauthlib GEREKMEZ; saf urllib.

2 adımlı manuel akış (headless sunucu için):

  1) Gerekli izin listesini + yönergeyi gör:
       python3 scripts/instagram-reauth.py scopes

  2) developers.facebook.com → Tools → Graph API Explorer'da (uygulaman seçili)
     "Generate Access Token" ile o izinleri onayla; çıkan KISA ömürlü USER token'ı
     kopyala, sonra:
       python3 scripts/instagram-reauth.py exchange "<KISA_USER_TOKEN>"
     → betik: uzun-ömürlü user token'a çevirir → sayfa token'ını çeker →
       insights iznini DOĞRULAR → instagram.env'i günceller (eskisi .bak'a).

NOT: instagram_manage_insights, Business tipi uygulamada uygulamanın
admin/developer/tester'ı VE varlık sahibi olan hesap için App Review olmadan
(Development modda) verilebilir. ParaFOMO hesabı bu koşulu sağlıyor.
"""
import os
import sys
import json
import urllib.parse
import urllib.request
import urllib.error

ENV = os.path.expanduser("~/.config/parafomo/instagram.env")
GRAPH = "https://graph.facebook.com/v21.0"

# content_publish + comments + insights hepsi bir arada → mevcut yayın hattı da çalışmaya devam eder
NEEDED = [
    "instagram_basic",
    "instagram_manage_insights",     # ← asıl eklenen
    "instagram_manage_comments",
    "instagram_content_publish",
    "pages_show_list",
    "pages_read_engagement",
    "business_management",
]


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


def cmd_scopes():
    env = load_env()
    print("\n1) Aç: https://developers.facebook.com/tools/explorer/")
    print(f"2) Sağ üstte uygulamanı seç (App ID {env.get('IG_APP_ID','?')}).")
    print("3) 'Generate Access Token' / 'Get User Access Token' → şu izinleri İŞARETLE:\n")
    for s in NEEDED:
        print(f"     - {s}")
    print("\n4) Onayla (Instagram hesabıyla giriş). Çıkan KISA ömürlü token'ı kopyala, sonra:")
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
    page = next((p for p in pages if p["id"] == want_page), pages[0])
    page_token = page["access_token"]
    print(f"[2/4] Sayfa token'ı alındı: {page['name']} ({page['id']}).")

    # 3) insights iznini DOĞRULA
    dbg = _get(f"{GRAPH}/debug_token?" + urllib.parse.urlencode({
        "input_token": page_token, "access_token": f"{app_id}|{app_secret}"}))
    scopes = dbg.get("data", {}).get("scopes", [])
    if "instagram_manage_insights" not in scopes:
        print("HATA: yeni token'da da instagram_manage_insights YOK.")
        print("      Graph API Explorer'da bu izni İŞARETLEDİĞİNDEN emin ol; varsa")
        print("      uygulama App Review / Development-mode varlık sahipliğini kontrol et.")
        print(f"      Gelen izinler: {', '.join(scopes)}")
        return 1
    print("[3/4] Doğrulandı: instagram_manage_insights VAR.")

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
    open(ENV, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(f"[4/4] instagram.env güncellendi (eski → {ENV}.bak).")
    print("      Artık metrics_instagram.py reach/kaydetme/paylaşma çekebilir.")
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
