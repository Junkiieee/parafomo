#!/usr/bin/env python3
"""Yayın kimliklerinin sağlık kontrolü — SALT OKUNUR (denetim sosyal-6, 2026-11-18).

Neden: IG sayfa token'ının veri erişimi ve YouTube refresh token'ı sessizce bozulabilir; bozulunca yayın hattı
(kuyruk.py yayinla) ancak o akşam hata verir. Graph API sürümü (scripts/lib/meta_graph.py) Meta takvimine göre
kapanır. Bu betik önceden haber verir:

  - Instagram/Facebook: debug_token (uygulama token'ıyla, GET) → geçerli mi, gerekli izinler var mı, veri erişiminin
    ve token'ın bitişine kaç gün kaldı.
  - YouTube: refresh token ile erişim token'ı alınır, channels.list(mine=True) okunur; verilen izinler (upload,
    force-ssl) kontrol edilir.
  - Graph sürümü: bilinen kapanış tarihine UYARI_GUN'den az kaldıysa.

Sorun varsa agent/notify.py alert --key token-saglik (günde en çok bir e-posta) + logs/token-health.json.
Token/sır ASLA yazdırılmaz.

  /root/.venvs/parafomo/bin/python scripts/token-health.py [--dry] [--kanal ig|yt|hepsi]
    --dry   kontrol eder ve yazdırır; dosya yazmaz, e-posta göndermez
Çıkış: 0 sağlıklı · 1 uyarı var · 2 kontrol edilemedi (ağ/kimlik dosyası)
Önerilen zamanlama: scripts/maintenance.sh içinde Pazartesi (date +%u = 1).
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "lib"))
from meta_graph import API, GRAPH_VERSION  # noqa: E402

IG_ENV = os.path.expanduser("~/.config/parafomo/instagram.env")
YT_OAUTH = os.path.expanduser("~/.config/parafomo/youtube_oauth.json")
OUT = os.path.join(ROOT, "logs", "token-health.json")
NOTIFY = os.path.join(ROOT, "agent", "notify.py")
UYARI_GUN = 21
# Meta Graph API sürüm kapanışları (developers.facebook.com/docs/graph-api/changelog; facebook-reel.py notu)
GRAPH_KAPANIS = {"v21.0": "2027-01-21"}
IG_IZIN = ["instagram_basic", "instagram_content_publish", "pages_manage_posts", "pages_read_engagement",
           "instagram_manage_insights"]
YT_IZIN = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]


def simdi():
    return dt.datetime.now(dt.timezone.utc)


def env_oku(p):
    e = {}
    for line in open(p, encoding="utf-8"):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.strip().split("=", 1)
            e[k] = v.strip().strip('"')
    return e


def gun_kaldi(ts):
    """Unix zaman damgası → kalan gün (0 / yok = süresiz → None)."""
    if not ts:
        return None
    return round((dt.datetime.fromtimestamp(int(ts), dt.timezone.utc) - simdi()).total_seconds() / 86400, 1)


def ig_kontrol():
    """→ (sonuç sözlüğü, sorunlar listesi). Ağ hatası 'kontrol edilemedi' sorunudur."""
    sorun = []
    try:
        e = env_oku(IG_ENV)
    except OSError as ex:
        return {"ok": None}, [f"IG: {IG_ENV} okunamadı ({type(ex).__name__})"]
    app_id, secret, tok = e.get("IG_APP_ID"), e.get("IG_APP_SECRET"), e.get("IG_PAGE_TOKEN")
    if not (app_id and secret and tok):
        return {"ok": None}, ["IG: instagram.env'de IG_APP_ID / IG_APP_SECRET / IG_PAGE_TOKEN eksik"]
    q = urllib.parse.urlencode({"input_token": tok, "access_token": f"{app_id}|{secret}"})
    try:
        with urllib.request.urlopen(f"{API}/debug_token?{q}", timeout=30) as r:
            d = (json.load(r) or {}).get("data") or {}
    except urllib.error.HTTPError as ex:
        try:
            msg = json.loads(ex.read().decode()).get("error", {}).get("message", "")
        except Exception:
            msg = ""
        return {"ok": None}, [f"IG: debug_token HTTP {ex.code} {msg[:120]}"]
    except Exception as ex:
        return {"ok": None}, [f"IG: debug_token okunamadı ({type(ex).__name__})"]
    izinler = d.get("scopes") or []
    eksik = [s for s in IG_IZIN if s not in izinler]
    veri_gun, tok_gun = gun_kaldi(d.get("data_access_expires_at")), gun_kaldi(d.get("expires_at"))
    if not d.get("is_valid"):
        sorun.append("IG: sayfa token'ı GEÇERSİZ — yeniden yetkilendir: scripts/instagram-reauth.py")
    if eksik:
        sorun.append(f"IG: eksik izin(ler): {', '.join(eksik)} — scripts/instagram-reauth.py")
    for ad, g in (("veri erişimi", veri_gun), ("token", tok_gun)):
        if g is not None and g < UYARI_GUN:
            sorun.append(f"IG: {ad} {g} gün içinde bitiyor — scripts/instagram-reauth.py ile yenile")
    return {"ok": not sorun, "tur": d.get("type"), "gecerli": bool(d.get("is_valid")), "eksik_izin": eksik,
            "veri_erisimi_gun": veri_gun, "token_gun": tok_gun}, sorun


def yt_kontrol():
    try:
        cfg = json.load(open(YT_OAUTH, encoding="utf-8"))
    except (OSError, ValueError) as ex:
        return {"ok": None}, [f"YouTube: {YT_OAUTH} okunamadı ({type(ex).__name__})"]
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError as ex:
        return {"ok": None}, [f"YouTube: google kitaplıkları yok ({ex}) — venv python ile çalıştır"]
    # scopes=None: yenileme isteği kapsam göndermez → token'a VERİLMİŞ bütün izinler döner (invalid_scope olmaz)
    cr = Credentials(token=None, refresh_token=cfg.get("refresh_token"), client_id=cfg.get("client_id"),
                     client_secret=cfg.get("client_secret"), token_uri="https://oauth2.googleapis.com/token")
    try:
        cr.refresh(Request())
    except Exception as ex:
        m = str(ex)
        neden = "refresh token GEÇERSİZ/iptal (invalid_grant)" if "invalid_grant" in m else f"{type(ex).__name__}: {m[:120]}"
        return {"ok": False}, [f"YouTube: {neden} — yeniden yetkilendir: scripts/youtube-reauth.py url"]
    verilen = sorted(getattr(cr, "granted_scopes", None) or [])
    sorun = []
    eksik = [s.rsplit("/", 1)[-1] for s in YT_IZIN if verilen and s not in verilen]
    if eksik:
        sorun.append(f"YouTube: eksik izin(ler): {', '.join(eksik)} — scripts/youtube-reauth.py url")
    try:
        yt = build("youtube", "v3", credentials=cr, cache_discovery=False)
        n = len(yt.channels().list(part="id", mine=True).execute().get("items", []))
        if not n:
            sorun.append("YouTube: token geçerli ama kanal bulunamadı (yanlış hesap?)")
    except Exception as ex:
        sorun.append(f"YouTube: channels.list başarısız ({type(ex).__name__}: {str(ex)[:120]})")
    return {"ok": not sorun, "izinler": [s.rsplit("/", 1)[-1] for s in verilen], "eksik_izin": eksik}, sorun


def graph_kontrol():
    son = GRAPH_KAPANIS.get(GRAPH_VERSION)
    if not son:
        return {"surum": GRAPH_VERSION, "kapanis": None}, []
    kalan = (dt.date.fromisoformat(son) - simdi().date()).days
    sorun = []
    if kalan < UYARI_GUN:
        sorun.append(f"Meta Graph {GRAPH_VERSION} {son} tarihinde kapanıyor ({kalan} gün) — scripts/lib/meta_graph.py'de "
                     "sürümü yükselt; önce META_GRAPH_VERSION=v2X.0 ile instagram-reel/facebook-reel --dry dene")
    return {"surum": GRAPH_VERSION, "kapanis": son, "kalan_gun": kalan}, sorun


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--kanal", choices=["ig", "yt", "hepsi"], default="hepsi")
    a = ap.parse_args()
    sonuc, sorunlar = {"ts": simdi().isoformat(timespec="seconds")}, []
    adimlar = [("graph", graph_kontrol)]
    if a.kanal in ("ig", "hepsi"):
        adimlar.append(("instagram", ig_kontrol))
    if a.kanal in ("yt", "hepsi"):
        adimlar.append(("youtube", yt_kontrol))
    for ad, fn in adimlar:
        r, s = fn()
        sonuc[ad] = r
        sorunlar += s
        durum = "✅" if not s else ("⚠️" if r.get("ok") is not None or ad == "graph" else "❓")
        print(f"[token] {durum} {ad}: {json.dumps(r, ensure_ascii=False)}")
    for s in sorunlar:
        print(f"[token] ⚠️ {s}")
    sonuc["sorunlar"] = sorunlar
    if a.dry:
        print("[token] --dry: dosya yazılmadı, e-posta gönderilmedi")
    else:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT + ".tmp", "w", encoding="utf-8") as f:
            json.dump(sonuc, f, ensure_ascii=False, indent=1)
        os.replace(OUT + ".tmp", OUT)
        if sorunlar:
            try:
                subprocess.run([sys.executable, NOTIFY, "alert", "--key", "token-saglik",
                                "--subject", "parafomo: yayın kimliği uyarısı (IG/YouTube/Graph)",
                                "--body", "\n".join(sorunlar) + "\n\nAyrıntı: logs/token-health.json"],
                               cwd=ROOT, timeout=60, check=False)
            except Exception as ex:
                print(f"[token] uyarı gönderilemedi: {type(ex).__name__}")
    if any(sonuc.get(k, {}).get("ok") is None for k in ("instagram", "youtube") if k in sonuc):
        return 2
    return 1 if sorunlar else 0


if __name__ == "__main__":
    sys.exit(main())
