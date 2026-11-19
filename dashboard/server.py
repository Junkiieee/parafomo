"""
Parafomo Panel v2 — dashboard.parafomo.com (2026-11-16).

Kaan: "sade bir dashboard: planlanan Instagram ve YouTube içerikleri + web sitesinde ne yapıldı/yapılacak;
kontrol panelden; telefonda uygulama gibi." → PWA (ana ekrana eklenir) + uygulama içi şifreli giriş.

Giriş: DASHBOARD_PASSWORD (~/.config/parafomo/dashboard.env, repo DIŞI) → 180 günlük HttpOnly oturum çerezi.
Oturumlar yalnız SHA-256 özetiyle saklanır. Yazan uçlar ayrıca `X-Dash: 1` başlığı ister (CSRF).

Veri (hepsi repo DIŞI, /root/parafomo-data/dash/):
  plan.json      kanal planları + web yapılacak/yapıldı + Kaan'dan beklenenler (Claude günceller: dashboard/panel.py)
  kpi.json       metrikler (dashboard/collect.py; bu sunucu 3 saatte bir arka planda çalıştırır)
  kontrol.json   aç/kapa anahtarları (scripts/anim/kuyruk.py ve scripts/daily-content.sh okur)
  istekler.json  Kaan'ın panelden yazdıkları (+ görseller uploads/)
  kararlar.json  plan onayları · gorevler.json Kaan'ın "yaptım" işaretleri · oturumlar.json
Video kuyruğu /root/parafomo-data/onay/kuyruk.json — yazma yalnız scripts/anim/kuyruk.py üzerinden.

Servis: systemd parafomo-dashboard (127.0.0.1:8792, Caddy arkasında). Kod değişince: systemctl restart parafomo-dashboard
"""
import base64
import datetime as dt
import hashlib
import hmac
import json
import os
import re
import secrets
import subprocess
import threading
import time

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

ROOT = "/root/parafomo"
HERE = os.path.dirname(os.path.abspath(__file__))
DASH = "/root/parafomo-data/dash"
KUYRUK = "/root/parafomo-data/onay/kuyruk.json"
OTO = "/root/parafomo-data/onay/oto.json"
DEFTER = os.path.join(ROOT, "agent", "plan", "defter-plan.json")
LF_DIR = os.path.join(ROOT, "public", "social", "longform")
SOCIAL = os.path.realpath(os.path.join(ROOT, "public", "social"))
PY = "/root/.venvs/parafomo/bin/python"
ENV = os.path.expanduser("~/.config/parafomo/dashboard.env")
COOKIE = "pf_panel"
OTURUM_GUN = 180
TR = dt.timezone(dt.timedelta(hours=3))   # TSİ (yaz saati yok)
KPI_YAS = 3 * 3600

KONTROLLER = [
    ("video_uretim", "Gece video üretimi", "Her gece yeni videolar hazırlanır."),
    ("hikaye_uretim", "Para hikâyeleri (otomatik)", "Her gece bir Para hikâyesi otomatik yazılır, kontrol edilir ve 19:00'da çıkar."),
    ("oto_onay", "Onaysız yayın", "Açıkken hazır videolar senin onayını beklemeden çıkar. Kapalıyken her video burada onayını bekler."),
    ("youtube", "YouTube yayını", "Hazır videolar yayın saatlerinde YouTube'a çıkar."),
    ("instagram", "Instagram paylaşımı", "Aynı videolar Instagram Reels (ve Facebook) olarak da paylaşılır."),
    ("web_icerik", "Web: yeni içerik", "Hafta içi her sabah siteye yeni yazı/sayfa eklenir."),
]

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
_lock = threading.Lock()
_cache = {}


# ---------------------------------------------------------------- yardımcılar
def oku(path, varsayilan):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return varsayilan


def yaz(path, veri):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def onbellek(anahtar, sure, fn):
    with _lock:
        hit = _cache.get(anahtar)
        if hit and time.time() - hit[0] < sure:
            return hit[1]
    val = fn()
    with _lock:
        _cache[anahtar] = (time.time(), val)
    return val


def simdi():
    return dt.datetime.now(TR)


def dash(ad):
    return os.path.join(DASH, ad)


def olay(eylem, **veri):
    """Her panel eylemi eylemler.jsonl'a: Claude'un bekçisi (dashboard/panel.py bekle) bunu dinler → anında tepki."""
    satir = json.dumps({"zaman": simdi().isoformat(timespec="seconds"), "eylem": eylem, **veri}, ensure_ascii=False)
    with _lock:
        with open(dash("eylemler.jsonl"), "a", encoding="utf-8") as f:
            f.write(satir + "\n")


def claude_durumu():
    b = oku(dash("bekci.json"), {})
    yas = time.time() - b.get("zaman", 0)
    return {"cevrimici": yas < 900, "son": dt.datetime.fromtimestamp(b["zaman"], TR).isoformat(timespec="seconds") if b.get("zaman") else None}


# ---------------------------------------------------------------- giriş / oturum
_hatalar = {}


def _sifre():
    for line in open(ENV, encoding="utf-8"):
        if line.startswith("DASHBOARD_PASSWORD="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("şifre tanımlı değil")


def _ozet(tok):
    return hashlib.sha256(tok.encode()).hexdigest()


def _ip(req):
    xff = req.headers.get("x-forwarded-for", "")
    return xff.split(",")[-1].strip() if xff else (req.client.host if req.client else "?")


def oturum(req: Request):
    tok = req.cookies.get(COOKIE, "")
    if not tok:
        raise HTTPException(401, "giriş gerekli")
    with _lock:
        s = oku(dash("oturumlar.json"), {})
        v = s.get(_ozet(tok))
        if not v or v.get("bitis", 0) < time.time():
            raise HTTPException(401, "oturum bitti")
        if time.time() - v.get("goruldu", 0) > 3600:
            v["goruldu"] = time.time()
            yaz(dash("oturumlar.json"), s)


def koruma(req: Request):
    oturum(req)
    if req.headers.get("x-dash") != "1":
        raise HTTPException(403, "eksik başlık")


class GirisIn(BaseModel):
    sifre: str


@app.post("/api/giris")
def giris(body: GirisIn, req: Request, resp: Response):
    ip, t = _ip(req), time.time()
    with _lock:
        ipde = [x for x in _hatalar.get(ip, []) if t - x < 900]
        hepsi = [x for x in _hatalar.get("*", []) if t - x < 3600]
    if len(ipde) >= 5 or len(hepsi) >= 30:
        raise HTTPException(429, "Çok fazla deneme. 15 dakika sonra tekrar dene.")
    if not hmac.compare_digest(body.sifre.encode(), _sifre().encode()):
        with _lock:
            _hatalar[ip] = ipde + [t]
            _hatalar["*"] = hepsi + [t]
        time.sleep(1)
        raise HTTPException(401, "Şifre yanlış.")
    tok = secrets.token_urlsafe(32)
    with _lock:
        s = {k: v for k, v in oku(dash("oturumlar.json"), {}).items() if v.get("bitis", 0) > t}
        s[_ozet(tok)] = {"acildi": t, "bitis": t + OTURUM_GUN * 86400, "goruldu": t,
                         "cihaz": req.headers.get("user-agent", "")[:120]}
        yaz(dash("oturumlar.json"), s)
    resp.set_cookie(COOKIE, tok, max_age=OTURUM_GUN * 86400, httponly=True, secure=True, samesite="lax", path="/")
    return {"ok": True}


@app.post("/api/cikis")
def cikis(req: Request, resp: Response):
    tok = req.cookies.get(COOKIE, "")
    if tok:
        with _lock:
            s = oku(dash("oturumlar.json"), {})
            s.pop(_ozet(tok), None)
            yaz(dash("oturumlar.json"), s)
    resp.delete_cookie(COOKIE, path="/")
    return {"ok": True}


# ---------------------------------------------------------------- metrikler (arka planda tazelenir)
_toplaniyor = threading.Event()


def kpi_tazele(zorla=False):
    p = dash("kpi.json")
    yas = time.time() - os.path.getmtime(p) if os.path.exists(p) else 1e9
    if _toplaniyor.is_set() or (not zorla and yas < KPI_YAS):
        return False

    def is_():
        try:
            subprocess.run(["nice", "-n", "19", PY, os.path.join(HERE, "collect.py")], cwd=ROOT,
                           capture_output=True, timeout=900)
        except Exception:   # noqa: BLE001 — bir sonraki istekte yeniden denenir
            pass
        finally:
            _toplaniyor.clear()
    _toplaniyor.set()
    threading.Thread(target=is_, daemon=True).start()
    return True


# ---------------------------------------------------------------- kontrol anahtarları
def oto_bitis():
    return oku(OTO, {}).get("bitis", "")


def kontrol_durum():
    k = oku(dash("kontrol.json"), {})
    out = []
    for anahtar, ad, aciklama in KONTROLLER:
        if anahtar == "oto_onay":
            b = oto_bitis()
            acik = bool(b) and simdi().date().isoformat() <= b
            ek = f" Şu an {dt.date.fromisoformat(b).strftime('%d.%m.%Y')} tarihine kadar açık." if acik else ""
            out.append({"anahtar": anahtar, "ad": ad, "aciklama": aciklama + ek, "acik": acik})
        else:
            out.append({"anahtar": anahtar, "ad": ad, "aciklama": aciklama, "acik": bool(k.get(anahtar, True))})
    return out


def acik_mi(anahtar):
    return next((x["acik"] for x in kontrol_durum() if x["anahtar"] == anahtar), True)


# ---------------------------------------------------------------- içerik (YouTube + Instagram)
def yayin_saatleri():
    """kuyruk.sh yayinla cron satırlarından TSİ yayın saatleri (cron sunucuda UTC)."""
    def bul():
        try:
            txt = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=10).stdout
        except Exception:   # noqa: BLE001
            txt = ""
        out = []
        for line in txt.splitlines():
            if "kuyruk.sh yayinla" in line and not line.lstrip().startswith("#"):
                p = line.split()
                if p[0].isdigit() and p[1].isdigit():
                    out.append(((int(p[1]) + 3) % 24, int(p[0])))
        return sorted(out) or [(13, 0), (19, 0)]
    return onbellek("saatler", 600, bul)


def temiz_baslik(t):
    return re.sub(r"\s*#shorts\s*$", "", t or "", flags=re.I).strip()


def video_ozet(it, yt=None, ig=None):
    mp4 = it.get("mp4") or ""
    return {"no": it["no"], "baslik": temiz_baslik(it.get("title")), "durum": it.get("status"),
            "motor": it.get("teknik") or it.get("style"), "defter": it.get("style") == "defter",
            "tarih": it.get("yayin_tarihi"), "video": bool(mp4 and os.path.exists(mp4)),
            "yt": it.get("youtube_id"), "ig": it.get("ig_permalink"), "yayinlandi": it.get("published"),
            "oy": it.get("kaan"), "hata": it.get("error"),
            "izlenme": (yt or {}).get("izlenme"), "begeni": (yt or {}).get("begeni"),
            "ig_erisim": (ig or {}).get("reach")}


def icerik(kpi):
    q = oku(KUYRUK, {"items": []})
    items = q.get("items", [])
    ytv = kpi.get("youtube", {}).get("videolar", {})
    igr = kpi.get("instagram", {}).get("reeller", {})
    now = simdi()
    bugun = now.date()
    uretim = acik_mi("video_uretim")
    oto = acik_mi("oto_onay")
    defter = oku(DEFTER, {}).get("secimler", {})
    kuyrukta = " ".join(it["slug"] for it in items)

    # kuyruk.py yayinla mantığının birebir benzetimi: tarihi o gün olan önce, sonra onay sırası
    onayli = [it for it in items if it.get("status") == "onaylandi"]
    alinan, yuvalar = set(), []
    for g in range(8):
        gun = bugun + dt.timedelta(days=g)
        gs = gun.isoformat()
        for i, (h, m) in enumerate(yayin_saatleri()):
            t = dt.datetime(gun.year, gun.month, gun.day, h, m, tzinfo=TR)
            if t <= now:
                continue
            sira = [it for it in onayli if it["no"] not in alinan and (it.get("yayin_tarihi") or "") <= gs]
            if sira:
                it = sorted(sira, key=lambda x: ((x.get("yayin_tarihi") or "") != gs, x.get("approved", "")))[0]
                alinan.add(it["no"])
                yuvalar.append({"zaman": t.isoformat(), "video": video_ozet(it)})
                continue
            plan = defter.get(gs)
            if i == 0 and plan and plan.get("yuva") == "short" and plan.get("id", "#") not in kuyrukta:
                yuvalar.append({"zaman": t.isoformat(), "video": None,
                                "not": f"Ekonomi Defteri: {plan.get('baslik', '')} (hazırlanacak)"})
            elif uretim:
                yuvalar.append({"zaman": t.isoformat(), "video": None,
                                "not": "Gece üretilecek" + ("" if oto else " · onayını bekleyecek")})
            else:
                yuvalar.append({"zaman": t.isoformat(), "video": None, "not": "Boş (üretim kapalı)"})
    sinir = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=10)).isoformat()
    yayinda = sorted([it for it in items if it.get("status") == "yayinlandi" and it.get("published", "") >= sinir],
                     key=lambda it: it.get("published", ""), reverse=True)[:12]
    sorun_sinir = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=3)).isoformat()
    return {
        "saatler": [f"{h:02d}:{m:02d}" for h, m in yayin_saatleri()],
        "yuvalar": yuvalar,
        "bekleyen": [video_ozet(it) for it in items if it.get("status") == "bekliyor"],
        "sorunlu": [video_ozet(it) for it in items if it.get("status") == "hata" and it.get("created", "") >= sorun_sinir],
        "yayinlanan": [video_ozet(it, ytv.get(it.get("youtube_id")), igr.get(it.get("ig_media_id"))) for it in yayinda],
        "uzun": uzun_videolar(kpi, defter),
    }


def uzun_videolar(kpi, defter):
    ytv = kpi.get("youtube", {}).get("videolar", {})
    now = dt.datetime.now(dt.timezone.utc)
    out, slugs = [], []
    for f in sorted(os.listdir(LF_DIR)) if os.path.isdir(LF_DIR) else []:
        if not f.endswith(".meta.json"):
            continue
        m = oku(os.path.join(LF_DIR, f), {})
        slug = f[:-len(".meta.json")]
        slugs.append(slug)
        pa = m.get("publish_at")
        zaman = dt.datetime.fromisoformat(pa.replace("Z", "+00:00")) if pa else None
        gelecek = bool(zaman and zaman > now and m.get("privacy") != "public")
        out.append({"slug": slug, "baslik": m.get("title", slug), "zaman": zaman.isoformat() if zaman else None,
                    "durum": "planlandi" if gelecek else ("yayinda" if m.get("video_id") else "hazir"),
                    "yt": m.get("video_id"), "izlenme": ytv.get(m.get("video_id"), {}).get("izlenme"),
                    "kapak": os.path.exists(os.path.join(LF_DIR, f"{slug}-thumb.jpg"))})
    bugun = simdi().date().isoformat()
    for gun, p in sorted(defter.items()):
        if p.get("yuva") == "uzun" and gun > bugun and not any(p.get("id", "#") in s for s in slugs):
            out.append({"slug": "", "baslik": f"Ekonomi Defteri: {p.get('baslik', '')}",
                        "zaman": f"{gun}T12:00:00+03:00", "durum": "hazirlanacak", "yt": None, "izlenme": None, "kapak": False})
    out.sort(key=lambda x: x["zaman"] or "", reverse=True)
    return out[:6]


# ---------------------------------------------------------------- web
def git(*args):
    try:
        return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True, timeout=20).stdout
    except Exception:   # noqa: BLE001
        return ""


def web_otomatik():
    def hesapla():
        yeni, gun = [], ""
        for line in git("log", "--since=21 days ago", "--diff-filter=A", "--name-only", "--format=@@%ad",
                        "--date=short", "--", "src/content/blog", "src/pages").splitlines():
            line = line.strip()
            if line.startswith("@@"):
                gun = line[2:]
                continue
            if not line:
                continue
            m = re.match(r"src/content/blog/(.+)\.mdx?$", line)
            if m:
                yol = os.path.join(ROOT, line)
                baslik = m.group(1)
                if os.path.exists(yol):
                    tm = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', open(yol, encoding="utf-8").read(4000), re.M)
                    baslik = tm.group(1) if tm else baslik
                    yeni.append({"tarih": gun, "baslik": f"Yeni yazı: {baslik}", "link": f"/blog/{m.group(1)}/", "oto": True})
                continue
            m = re.match(r"src/pages/([a-z0-9-]+)\.astro$", line)
            if m and m.group(1) not in ("index", "404") and os.path.exists(os.path.join(ROOT, line)):
                yeni.append({"tarih": gun, "baslik": f"Yeni sayfa: /{m.group(1)}/", "link": f"/{m.group(1)}/", "oto": True})
        oto = sum(1 for s in git("log", "--since=7 days ago", "--format=%s").splitlines()
                  if re.search(r"otomatik|tazeleme|^fiyat:|^halka-arz:|^kira|^evds|^veri:", s, re.I))
        return {"yeni": yeni, "oto_guncelleme_7g": oto}
    return onbellek("web_oto", 600, hesapla)


def web_bolumu(plan):
    w = plan.get("web", {})
    o = web_otomatik()
    elle = w.get("yapildi", [])
    linkler = {x.get("link") for x in elle}
    yapildi = elle + [x for x in o["yeni"] if x["link"] not in linkler]
    yapildi.sort(key=lambda x: x.get("tarih", ""), reverse=True)
    return {"yapilacak": w.get("yapilacak", []), "yapildi": yapildi[:25], "oto_guncelleme_7g": o["oto_guncelleme_7g"]}


# ---------------------------------------------------------------- durum
def hedefler(plan, kpi):
    """GA4'e bağlı hedeflere seri kırılması uyarısı (plan.json'a dokunmadan; metni collect.py yazar).
    17 Kasım'dan beri GA4 yalnız çerez onaylıları sayıyor: o hedefin çubuğu trafik değil onay oranı gösterir."""
    notu = (kpi.get("web") or {}).get("ga4_not")
    return [{**h, "uyari": notu} if notu and str(h.get("kpi", "")).startswith("web.ziyaret") else h
            for h in plan.get("hedefler", [])]


@app.get("/api/durum")
def durum(req: Request):
    oturum(req)
    kpi_tazele()
    kpi = oku(dash("kpi.json"), {})
    plan = oku(dash("plan.json"), {})
    kararlar = oku(dash("kararlar.json"), {})
    kanallar = {}
    for ad, k in plan.get("kanallar", {}).items():
        kr = kararlar.get(ad, {})
        kanallar[ad] = {**k, "onay": kr if kr.get("surum") == k.get("surum") else None}
    gorev_d = oku(dash("gorevler.json"), {})
    return {
        "simdi": simdi().isoformat(timespec="seconds"),
        "kpi": {k: kpi.get(k) for k in ("guncellendi", "hatalar", "web", "youtube", "instagram", "kayit")},
        "toplaniyor": _toplaniyor.is_set(),
        "gunluk": plan.get("gunluk"),
        "kanallar": kanallar,
        "icerik": icerik(kpi),
        "web": web_bolumu(plan),
        "kontrol": kontrol_durum(),
        "gorevler": [{**g, "yaptim": gorev_d.get(g.get("id"), {}).get("zaman")} for g in (plan.get("gorevler") or plan.get("kaan", []))],
        "hedefler": hedefler(plan, kpi),
        "gelir": plan.get("gelir", []),
        "fikirler": plan.get("fikirler", []),
        "harcamalar": [{**h, "karar": oku(dash("harcama-kararlar.json"), {}).get(h.get("id"))} for h in plan.get("harcamalar", [])],
        "istekler": list(reversed(oku(dash("istekler.json"), [])))[:30],
        "claude": claude_durumu(),
        "senaryolar": [{**x, "karar": oku(dash("senaryo-kararlar.json"), {}).get(x.get("id"))} for x in plan.get("senaryolar", [])],
    }


@app.post("/api/yenile")
def yenile(req: Request):
    koruma(req)
    p = dash("kpi.json")
    if os.path.exists(p) and time.time() - os.path.getmtime(p) < 600:
        return {"ok": True, "basladi": False, "not": "Sayılar 10 dakikadan yeni."}
    return {"ok": True, "basladi": kpi_tazele(zorla=True)}


# ---------------------------------------------------------------- video eylemleri
EYLEM = {"onayla": "onayla", "cikar": "reddet", "begen": "begen", "begenme": "begenme"}


@app.post("/api/video/{no}/{eylem}")
def video_eylem(no: int, eylem: str, req: Request):
    koruma(req)
    if eylem not in EYLEM:
        raise HTTPException(404, "bilinmeyen eylem")
    q = oku(KUYRUK, {"items": []})
    it = next((x for x in q.get("items", []) if x.get("no") == no), None)
    if not it:
        raise HTTPException(404, "video yok")
    r = subprocess.run([PY, os.path.join(ROOT, "scripts", "anim", "kuyruk.py"), EYLEM[eylem], str(no)],
                       cwd=ROOT, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise HTTPException(500, "kuyruk güncellenemedi")
    olay(eylem, no=no, slug=it.get("slug"), baslik=temiz_baslik(it.get("title")))
    yeni = next((x for x in oku(KUYRUK, {"items": []}).get("items", []) if x.get("no") == no), it)
    return {"ok": True, "durum": yeni.get("status"), "oy": yeni.get("kaan")}


def _mp4(no):
    it = next((x for x in oku(KUYRUK, {"items": []}).get("items", []) if x.get("no") == no), None)
    p = os.path.realpath((it or {}).get("mp4") or "")
    if not (it and p.startswith(SOCIAL + os.sep) and p.endswith(".mp4") and os.path.exists(p)):
        raise HTTPException(404, "video dosyası yok")
    return p


@app.get("/api/video/{no}.mp4")
def video_dosya(no: int, req: Request):
    oturum(req)
    return FileResponse(_mp4(no), media_type="video/mp4", headers={"Cache-Control": "private, max-age=3600"})


@app.get("/api/video/{no}.jpg")
def video_kapak(no: int, req: Request):
    oturum(req)
    p = _mp4(no)
    out = dash(f"kapak/{no}.jpg")
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(p):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        subprocess.run(["nice", "-n", "19", "ffmpeg", "-y", "-loglevel", "error", "-ss", "2", "-i", p, "-frames:v", "1",
                        "-vf", "scale=360:-2", "-q:v", "5", out], capture_output=True, timeout=60)
        if not os.path.exists(out):
            raise HTTPException(404, "kapak üretilemedi")
    return FileResponse(out, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=3600"})


@app.get("/api/uzun/{slug}.jpg")
def uzun_kapak(slug: str, req: Request):
    oturum(req)
    if not re.fullmatch(r"[a-z0-9-]+", slug):
        raise HTTPException(404, "yok")
    p = os.path.join(LF_DIR, f"{slug}-thumb.jpg")
    if not os.path.exists(p):
        raise HTTPException(404, "yok")
    return FileResponse(p, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=86400"})


# ---------------------------------------------------------------- kontrol / plan / görev / istek
class KontrolIn(BaseModel):
    anahtar: str
    acik: bool


@app.post("/api/kontrol")
def kontrol_yaz(body: KontrolIn, req: Request):
    koruma(req)
    if body.anahtar not in {k for k, _, _ in KONTROLLER}:
        raise HTTPException(404, "bilinmeyen anahtar")
    with _lock:
        if body.anahtar == "oto_onay":
            bugun = simdi().date()
            eski = oto_bitis()
            if body.acik:
                yeni = max(eski or "", (bugun + dt.timedelta(days=30)).isoformat())
            else:
                yeni = (bugun - dt.timedelta(days=1)).isoformat()
            yaz(OTO, {**oku(OTO, {}), "bitis": yeni, "panel": simdi().isoformat(timespec="seconds")})
        else:
            k = oku(dash("kontrol.json"), {})
            k[body.anahtar] = body.acik
            k["_degisti"] = simdi().isoformat(timespec="seconds")
            yaz(dash("kontrol.json"), k)
    olay("kontrol", anahtar=body.anahtar, acik=body.acik)
    return {"ok": True, "kontrol": kontrol_durum()}


@app.post("/api/plan/{kanal}/onayla")
def plan_onayla(kanal: str, req: Request):
    koruma(req)
    k = oku(dash("plan.json"), {}).get("kanallar", {}).get(kanal)
    if not k:
        raise HTTPException(404, "plan yok")
    with _lock:
        kr = oku(dash("kararlar.json"), {})
        kr[kanal] = {"surum": k.get("surum"), "durum": "onaylandi", "zaman": simdi().isoformat(timespec="seconds")}
        yaz(dash("kararlar.json"), kr)
    olay("plan_onay", kanal=kanal, surum=k.get("surum"))
    return {"ok": True}


@app.post("/api/senaryo/{sid}/onayla")
def senaryo_onayla(sid: str, req: Request):
    koruma(req)
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,20}", sid) or not any(x.get("id") == sid for x in oku(dash("plan.json"), {}).get("senaryolar", [])):
        raise HTTPException(404, "senaryo yok")
    with _lock:
        k = oku(dash("senaryo-kararlar.json"), {})
        k[sid] = {"durum": "onaylandi", "zaman": simdi().isoformat(timespec="seconds")}
        yaz(dash("senaryo-kararlar.json"), k)
    olay("senaryo_onay", id=sid)
    return {"ok": True}


@app.post("/api/harcama/{hid}/{karar}")
def harcama_karar(hid: str, karar: str, req: Request):
    koruma(req)
    if karar not in ("onayla", "reddet") or not any(h.get("id") == hid for h in oku(dash("plan.json"), {}).get("harcamalar", [])):
        raise HTTPException(404, "harcama yok")
    with _lock:
        k = oku(dash("harcama-kararlar.json"), {})
        k[hid] = {"durum": "onaylandi" if karar == "onayla" else "reddedildi", "zaman": simdi().isoformat(timespec="seconds")}
        yaz(dash("harcama-kararlar.json"), k)
    olay("harcama", id=hid, karar=karar)
    return {"ok": True}


@app.post("/api/gorev/{gid}/yaptim")
def gorev_yaptim(gid: str, req: Request):
    koruma(req)
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,20}", gid):
        raise HTTPException(404, "yok")
    with _lock:
        g = oku(dash("gorevler.json"), {})
        g[gid] = {"zaman": simdi().isoformat(timespec="seconds")}
        yaz(dash("gorevler.json"), g)
    olay("gorev_yaptim", gorev=gid)
    return {"ok": True}


class IstekIn(BaseModel):
    metin: str
    gorsel: str | None = None   # data:image/...;base64,...


GORSEL_TUR = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


@app.post("/api/istek")
def istek(body: IstekIn, req: Request):
    koruma(req)
    metin = body.metin.strip()[:4000]
    if not metin and not body.gorsel:
        raise HTTPException(400, "boş istek")
    dosya = None
    with _lock:
        lst = oku(dash("istekler.json"), [])
        iid = max([x.get("id", 0) for x in lst] or [0]) + 1
        if body.gorsel:
            m = re.match(r"data:(image/(?:jpeg|png|webp));base64,(.+)$", body.gorsel, re.S)
            if not m:
                raise HTTPException(400, "görsel türü desteklenmiyor (jpg/png/webp)")
            ham = base64.b64decode(m.group(2), validate=False)
            if len(ham) > 8 * 1024 * 1024:
                raise HTTPException(413, "görsel 8 MB'den büyük")
            dosya = f"{iid}.{GORSEL_TUR[m.group(1)]}"
            os.makedirs(dash("yuklenen"), exist_ok=True)
            with open(dash(f"yuklenen/{dosya}"), "wb") as f:
                f.write(ham)
        lst.append({"id": iid, "zaman": simdi().isoformat(timespec="seconds"), "metin": metin, "gorsel": dosya,
                    "durum": "yeni", "cevap": ""})
        yaz(dash("istekler.json"), lst)
    olay("istek", id=iid, metin=metin[:300], gorsel=bool(dosya))
    return {"ok": True, "id": iid}


@app.get("/api/istek/{iid}/gorsel")
def istek_gorsel(iid: int, req: Request):
    oturum(req)
    it = next((x for x in oku(dash("istekler.json"), []) if x.get("id") == iid), None)
    if not it or not it.get("gorsel"):
        raise HTTPException(404, "yok")
    p = dash(f"yuklenen/{it['gorsel']}")
    ext = it["gorsel"].rsplit(".", 1)[-1]
    tur = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "application/octet-stream")
    return FileResponse(p, media_type=tur, headers={"Cache-Control": "private, max-age=86400"})


# ---------------------------------------------------------------- statik (veri içermez → girişsiz)
STATIK = {"app.js": "application/javascript", "app.css": "text/css", "sw.js": "application/javascript",
          "manifest.webmanifest": "application/manifest+json", "icon-192.png": "image/png",
          "icon-512.png": "image/png", "icon-maskable.png": "image/png", "apple-touch-icon.png": "image/png",
          "logo.png": "image/png"}
CSP = ("default-src 'self'; img-src 'self' data: blob:; media-src 'self'; style-src 'self'; script-src 'self'; "
       "connect-src 'self'; manifest-src 'self'; worker-src 'self'; base-uri 'none'; form-action 'self'; "
       "frame-ancestors 'none'")


@app.get("/")
def index():
    return FileResponse(os.path.join(HERE, "index.html"),
                        headers={"Cache-Control": "no-cache", "Content-Security-Policy": CSP})


@app.get("/{ad}")
def statik(ad: str):
    if ad not in STATIK:
        return JSONResponse({"detail": "yok"}, status_code=404)
    h = {"Cache-Control": "no-cache"}
    if ad == "sw.js":
        h["Service-Worker-Allowed"] = "/"
    return FileResponse(os.path.join(HERE, ad), media_type=STATIK[ad], headers=h)
