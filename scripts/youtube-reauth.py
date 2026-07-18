#!/usr/bin/env python3
"""
ParaFOMO — YouTube yeniden yetkilendirme (force-ssl scope; oynatma listesi + yorum için).

Mevcut token yalnız youtube.upload yetkisinde. Oynatma listesi ve yorum API'leri
youtube.force-ssl ister. Bu betik, mevcut client_id/secret ile YENİ bir refresh_token
alır (upload + force-ssl birlikte → yükleme de çalışmaya devam eder). google_auth_oauthlib
GEREKMEZ; saf urllib + manuel kod yapıştırma.

google_auth_oauthlib kurulu olmayan headless sunucu için 2 adımlı manuel akış:

  1) URL üret:
       python3 scripts/youtube-reauth.py url
     Çıkan bağlantıyı TARAYICINDA aç, ParaFOMO YouTube hesabıyla izin ver.
     Tarayıcı http://localhost/?code=XXXX... adresine yönlenir (sayfa açılmaz, NORMAL).
     Adres çubuğundaki  code=  değerini KOPYALA.

  2) Kodu değiştir:
       python3 scripts/youtube-reauth.py exchange "<KOD>"
     → youtube_oauth.json yeni refresh_token ile güncellenir (eskisi .bak'a yedeklenir).

NOT: OAuth client'ında "http://localhost" yetkili yönlendirme URI'si olmalı (Desktop
app tipinde varsayılan vardır). "redirect_uri_mismatch" alırsan --redirect ile kayıtlı
bir URI ver veya Google Cloud Console'da http://localhost ekle.
"""
import os
import sys
import json
import argparse
import urllib.parse
import urllib.request

OAUTH = "/root/.config/parafomo/youtube_oauth.json"
SCOPES = ("https://www.googleapis.com/auth/youtube.upload "
          "https://www.googleapis.com/auth/youtube.force-ssl "
          "https://www.googleapis.com/auth/youtube.readonly "
          "https://www.googleapis.com/auth/yt-analytics.readonly")
AUTH_EP = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_EP = "https://oauth2.googleapis.com/token"


def _cfg():
    return json.load(open(OAUTH))


def cmd_url(redirect):
    cfg = _cfg()
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": redirect,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
    }
    print("\n1) Şu bağlantıyı tarayıcında aç ve izin ver:\n")
    print(AUTH_EP + "?" + urllib.parse.urlencode(params))
    print("\n2) Yönlendirme sonrası adres çubuğundaki code= değerini kopyala, sonra:")
    print('   python3 scripts/youtube-reauth.py exchange "<KOD>"\n')


def cmd_exchange(code, redirect):
    cfg = _cfg()
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "redirect_uri": redirect,
        "grant_type": "authorization_code",
    }).encode()
    try:
        resp = json.load(urllib.request.urlopen(
            urllib.request.Request(TOKEN_EP, data=data), timeout=30))
    except urllib.error.HTTPError as e:
        print(f"HATA: token değişimi başarısız: {e.read().decode()[:300]}")
        return 1
    rt = resp.get("refresh_token")
    if not rt:
        print(f"HATA: refresh_token gelmedi. Yanıt: {json.dumps(resp)[:300]}")
        print("(İpucu: prompt=consent ile yeniden dene; Google bazen refresh_token'ı yalnız ilk onayda verir.)")
        return 1
    # yedekle + yaz
    if os.path.exists(OAUTH):
        os.replace(OAUTH, OAUTH + ".bak")
    cfg["refresh_token"] = rt
    json.dump(cfg, open(OAUTH, "w"), ensure_ascii=False, indent=2)
    print(f"[+] Yeni refresh_token kaydedildi. Scope: {resp.get('scope','?')}")
    print("    Artık youtube-extras.py (oynatma listesi + yorum) çalışır.")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["url", "exchange"])
    ap.add_argument("code", nargs="?", default="")
    ap.add_argument("--redirect", default="http://localhost")
    args = ap.parse_args()
    if args.cmd == "url":
        cmd_url(args.redirect); return 0
    if not args.code:
        print("kullanım: youtube-reauth.py exchange \"<KOD>\""); return 1
    return cmd_exchange(args.code, args.redirect)


if __name__ == "__main__":
    sys.exit(main())
