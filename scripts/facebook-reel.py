#!/usr/bin/env python3
"""
ParaFOMO — Facebook Reels yayıncısı: günlük Shorts mp4'ünü Parafomo sayfasına Reel koyar.

Neden: YouTube kitlemizin %68'i 35-54 yaş = Türkiye'de Facebook'un çekirdek kitlesi; FB
sayfası 0 takipçi, hiç paylaşım yok. Her gün zaten dikey bir Short üretiyoruz → aynı video
FB Reel olur. Yerel dosyadan yüklenir (IG'deki gibi barındırma/media dalı GEREKMEZ).

Akış (Graph API v21.0 · Reels Publishing API — 2026-10 dokümanıyla doğrulandı):
  1) POST /{page_id}/video_reels  upload_phase=start           → video_id + upload_url
  2) POST rupload.facebook.com/video-upload/v21.0/{video_id}   gövde = mp4 baytları
     (Authorization: OAuth <token> · offset: 0 · file_size: <bayt>)
  3) POST /{page_id}/video_reels  upload_phase=finish · video_state=PUBLISHED · description
  4) GET  /{video_id}?fields=status  ~3 dk'ya kadar yoklar; bitmediyse "processing" yazar.

İzin yoksa (pages_manage_posts · Graph #10/#190/#2xx) tek satır uyarı + exit 0 → video
hattı asla kırılmaz; Kaan izni verince (instagram-reauth.py) DEĞİŞİKLİK GEREKMEDEN
çalışmaya başlar. Diğer hatalar da tek satır + exit 0 (--strict ile exit 2).

Kullanım: python3 scripts/facebook-reel.py <slug> [--dry] [--root PATH] [--strict]
  --dry     ağa YAZMAZ, hiçbir dosyaya dokunmaz: açıklamayı + planlanan çağrıları basar,
            mp4'ü doğrular, izni salt-okunur (debug_token) kontrol eder.
  --root    repo kökü (vars.: $PARAFOMO_ROOT, yoksa bu betiğin reposu). mp4'ler gitignore'lu.
Girdi : public/social/short-<slug>.json (title, description, format, file)
Çıktı : aynı json'a fb_reel_id · fb_reel_url · fb_reel_status (idempotent: id varsa atlar)
        logs/fb-status.json {"ts","ok","reason","last","kind"} — günlük sağlık kontrolü okur.
Kimlik: ~/.config/parafomo/instagram.env (IG_PAGE_ID, IG_PAGE_TOKEN; IG_APP_ID/SECRET yalnız
        izin kontrolü için). Token/sır ASLA yazdırılmaz. facebook-post.py ortak yardımcıları
        buradan alır.
"""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
ENV_FILE = os.path.expanduser("~/.config/parafomo/instagram.env")
GRAPH_VERSION = "v21.0"   # IG betikleriyle aynı. Meta: v21.0 2027-01-21'e kadar → toplu yükselt.
API = f"https://graph.facebook.com/{GRAPH_VERSION}"
RUPLOAD = f"https://rupload.facebook.com/video-upload/{GRAPH_VERSION}"
SITE = "https://parafomo.com"
UTM = "utm_source=facebook&utm_medium=social&utm_campaign={campaign}"
PERM_LINE = ("[fb] atlandı: Facebook paylaşım izni yok (pages_manage_posts) — "
             "Kaan: python3 scripts/instagram-reauth.py scopes")
POLL_BUDGET = 170           # finish sonrası en çok ~3 dk yokla, sonra "processing" yazıp çık
POLL_EVERY = 8
REEL_MIN_S, REEL_MAX_S = 3, 90   # Reels API: 9:16, 3-90 sn, en az 540x960

# FB'ye özgü konu soruları (yönetici/vergi konuları 35-54 kitlesinde yoğun). Önce bunlar,
# sonra instagram-reel.py'nin TOPIC_Q listesi; "acil durum fonu" IG'de "fon" sorusuna düşüyordu.
FB_TOPIC_Q = [
    ("acil durum", "Acil durum fonun kaç aylık giderini karşılıyor?"),
    ("emekli zam", "Sence bu zam emekliyi rahatlatır mı?"),
    ("sgk", "SGK işlemlerinde en çok neye takılıyorsun?"),
    ("vergi", "Vergi konusunda en çok neyi merak ediyorsun?"),
    ("kira", "Bu yıl kiran ne kadar arttı?"),
    ("asgari", "Asgari ücret artışı bütçeni nasıl etkiliyor?"),
]
GENERIC_TAGS = {"finans", "yatırım", "yatirim", "para", "ekonomi", "parafomo",
                "shorts", "short", "youtubeshorts", "reels"}

_SECRETS = set()
_IG = None


def say(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------- ortam / güvenlik
def resolve_root(arg=""):
    return os.path.abspath(os.path.expanduser(arg or os.environ.get("PARAFOMO_ROOT") or REPO_ROOT))


def load_env(path=ENV_FILE):
    env = {}
    try:
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if "=" in ln and not ln.startswith("#"):
                    k, v = ln.split("=", 1)
                    env[k.strip()] = v.strip()
    except OSError:
        return {}
    for k, v in env.items():          # çıktıdan silinecek sırlar
        if v and len(v) >= 8 and ("TOKEN" in k or "SECRET" in k):
            _SECRETS.add(v)
    return env


def scrub(text):
    """Ekrana/loga gidecek metinden token/sırları sil, tek satıra indir."""
    s = str(text)
    for sec in _SECRETS:
        s = s.replace(sec, "***")
    return re.sub(r"\s+", " ", s).strip()


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json_atomic(path, data, trailing_newline=True):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    try:
        mode = os.stat(path).st_mode & 0o777
    except OSError:
        mode = 0o644
    fd, tmp = tempfile.mkstemp(prefix=".fb-tmp-", suffix=".json", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            if trailing_newline:
                fh.write("\n")
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_status(root, ok, reason, last, kind):
    """logs/fb-status.json — her GERÇEK koşuda (dry hariç) yazılır."""
    try:
        write_json_atomic(os.path.join(root, "logs", "fb-status.json"), {
            "ts": now_iso(), "ok": bool(ok), "reason": scrub(reason)[:300],
            "last": last, "kind": kind})
    except Exception as e:
        say(f"[fb] uyarı: logs/fb-status.json yazılamadı ({type(e).__name__})")


def fail(root, last, reason, strict, kind="reel", dry=False):
    """İzin-dışı hata: tek satır, durum dosyası, exit 0 (--strict: 2)."""
    say(f"[fb] HATA: {scrub(reason)[:240]}")
    if not dry:
        write_status(root, False, reason, last, kind)
    return 2 if strict else 0


def perm_skip(root, last, err, kind="reel"):
    say(PERM_LINE)
    write_status(root, False, f"izin yok: {err_text(err)}", last, kind)
    return 0


# ---------------------------------------------------------------- Graph API
def _send(req, timeout):
    """HTTP isteği → (yanıt, None) | (None, hata). İstisna fırlatmaz."""
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
        try:
            return (json.loads(raw) if raw.strip() else {}), None
        except ValueError:
            return None, {"message": f"JSON olmayan yanıt: {raw[:120]}"}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            body = json.loads(raw)
        except ValueError:
            body = {}
        body = body if isinstance(body, dict) else {}
        err = body.get("error") if isinstance(body.get("error"), dict) else {}
        dbg = body.get("debug_info") if isinstance(body.get("debug_info"), dict) else {}  # rupload
        return None, {
            "http": e.code, "code": err.get("code"), "subcode": err.get("error_subcode"),
            "message": err.get("message") or dbg.get("message") or raw[:200] or f"HTTP {e.code}",
            "retriable": e.code >= 500 or bool(err.get("is_transient")) or bool(dbg.get("retriable")),
        }
    except Exception as e:            # URLError, zaman aşımı, SSL, bağlantı koptu…
        return None, {"network": True, "retriable": True,
                      "message": f"ağ hatası ({type(e).__name__}: {e})"}


def graph_post(path, data, token, timeout=60):
    body = urllib.parse.urlencode({**data, "access_token": token}).encode()
    return _send(urllib.request.Request(f"{API}/{path}", data=body, method="POST"), timeout)


def graph_get(path, params, token, timeout=30):
    qs = urllib.parse.urlencode({**params, "access_token": token})
    return _send(urllib.request.Request(f"{API}/{path}?{qs}"), timeout)


def is_perm_error(err):
    """#10 izin · #190 token geçersiz/süresi dolmuş · #200-299 izin ailesi · mesajda izin adı."""
    try:
        code = int(err.get("code"))
    except (TypeError, ValueError):
        code = None
    msg = (err.get("message") or "").lower()
    return code in (10, 102, 190) or (code is not None and 200 <= code <= 299) \
        or "pages_manage_posts" in msg


def err_text(err):
    code, msg = err.get("code"), str(err.get("message") or "?")
    return scrub(f"(#{code}) {msg}" if code and not msg.startswith("(#") else msg)[:240]


def perm_status(env):
    """Salt-okunur izin kontrolü (debug_token, uygulama token'ıyla) → (True|False|None, not)."""
    app_id, secret, tok = env.get("IG_APP_ID"), env.get("IG_APP_SECRET"), env.get("IG_PAGE_TOKEN")
    if not (app_id and secret and tok):
        return None, "kontrol edilemedi: instagram.env'de IG_APP_ID/IG_APP_SECRET/IG_PAGE_TOKEN yok"
    res, err = graph_get("debug_token", {"input_token": tok}, f"{app_id}|{secret}")
    if err:
        return None, f"kontrol edilemedi: {err_text(err)}"
    data = (res or {}).get("data") or {}
    if not data.get("is_valid"):
        return False, "sayfa token'ı GEÇERSİZ"
    has = "pages_manage_posts" in (data.get("scopes") or [])
    return has, "pages_manage_posts VAR" if has else "pages_manage_posts YOK"


# ---------------------------------------------------------------- içerik
def ig_mod():
    """instagram-reel.py yardımcıları (_clean, TOPIC_Q, FORMAT_Q, TOPIC_TAGS) — tek kaynak."""
    global _IG
    if _IG is None:
        spec = importlib.util.spec_from_file_location(
            "parafomo_instagram_reel", os.path.join(SCRIPT_DIR, "instagram-reel.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _IG = mod
    return _IG


def read_frontmatter(path):
    """Blog .md frontmatter → dict (PyYAML; yoksa/bozuksa basit regex yedeği)."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.S)
    if not m:
        return {}
    front = m.group(1)
    try:
        import yaml
        d = yaml.safe_load(front)
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    d = {}
    for key in ("title", "description"):
        mm = re.search(rf'^{key}:\s*"?(.*?)"?\s*$', front, re.M)
        if mm:
            d[key] = mm.group(1).strip()
    mm = re.search(r"^tags:\s*\[(.*?)\]", front, re.M | re.S)
    if mm:
        d["tags"] = [t.strip().strip("\"'") for t in mm.group(1).split(",") if t.strip()]
    d["draft"] = bool(re.search(r"^draft:\s*true\s*$", front, re.M))
    return d


def blog_post_path(root, slug):
    return os.path.join(root, "src", "content", "blog", f"{slug}.md")


def published_post(root, slug):
    """Yazı repoda var ve taslak değilse frontmatter'ı, değilse None."""
    p = blog_post_path(root, slug)
    if not os.path.isfile(p):
        return None
    fm = read_frontmatter(p)
    return None if fm.get("draft") is True else fm


def site_url(slug, campaign, has_blog):
    q = UTM.format(campaign=campaign)
    return f"{SITE}/blog/{slug}/?{q}" if has_blog else f"{SITE}/?{q}"


def clean_title(title):
    return re.sub(r"(?:\s*#\w+)+\s*$", "", title or "").strip()   # sondaki #Shorts #altın…


def _norm(s):
    return re.sub(r"\W+", " ", (s or "").lower()).strip()


def context_text(desc, title, max_sent=2, soft=240, hard=400):
    """Açıklamadan 1-2 cümle bağlam (YouTube artığı #/URL/'Daha fazlası' satırları atılır)."""
    text = ig_mod()._clean(desc)
    sents = [s.strip() for s in re.split(r"(?<=[.!?…])\s+", text) if s.strip()]
    tn, out = _norm(title), []
    for s in sents:
        if _norm(s) and _norm(s) in tn:          # başlığın tekrarı
            continue
        if out and len(" ".join(out + [s])) > soft:
            break
        out.append(s)
        if len(out) >= max_sent:
            break
    txt = " ".join(out)
    if len(txt) > hard:
        txt = txt[:hard].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return txt


def pick_question(slug, title="", fmt=""):
    """Konuya özgü yorum sorusu (jenerik 'ne düşünüyorsun' daha az yorum çeker)."""
    ig = ig_mod()
    t = title or ""
    hay = f"{slug.replace('-', ' ')} {t.lower()} {t.replace('I', 'ı').replace('İ', 'i').lower()}"
    for key, q in FB_TOPIC_Q + list(ig.TOPIC_Q):
        if key in hay:
            return q
    return ig.FORMAT_Q.get((fmt or "").strip()) or "Sen ne düşünüyorsun?"


def _hashtag(t):
    s = re.sub(r"[\s\-_'’.]+", "", str(t).strip().lower())
    return re.sub(r"[^0-9a-zçğıöşü]", "", s)       # 'İ'.lower()'ın birleşik noktası da düşer


def pick_hashtags(meta, slug, title, post_tags=None):
    """En çok 3: 2 konu etiketi (video etiketleri → yazı etiketleri → IG konu haritası) + marka."""
    cands = []
    for t in list(meta.get("tags") or []) + list(post_tags or []):
        if isinstance(t, str) and len(t.split()) <= 2:
            h = _hashtag(t)
            if 3 <= len(h) <= 20 and h not in GENERIC_TAGS:
                cands.append("#" + h)
    hay = f"{slug.replace('-', ' ')} {(title or '').lower()}"
    for kw, tags in ig_mod().TOPIC_TAGS.items():
        if kw in hay:
            cands.extend(tags)
    out = []
    for h in cands + ["#finans", "#yatırım"]:
        if h not in out and h.lstrip("#") not in ("parafomo",):
            out.append(h)
        if len(out) == 2:
            break
    return " ".join(out + ["#parafomo"])


def build_description(meta, slug, root):
    """Kanca (başlık) · 1-2 cümle bağlam · konu sorusu · site linki (UTM) · ≤3 etiket."""
    title = clean_title(meta.get("title", ""))
    ctx = context_text(meta.get("description", ""), title)
    if not title:
        title, ctx = ctx, ""
    post = published_post(root, slug)
    has_blog = post is not None
    url = site_url(slug, "reel", has_blog)
    link = (meta.get("link") or "").strip()   # olay sonucu Short'u → ilgili hesaplama sayfası (event-short.py)
    if link and not has_blog:
        base = link if link.startswith("http") else f"{SITE}/{link.lstrip('/')}"
        url = f"{base}{'&' if '?' in base else '?'}{UTM.format(campaign='reel')}"
    lead = "Tamamı" if has_blog else ("Kendi rakamını hesapla" if link else "Daha fazlası")
    parts = [title, ctx, f"💬 {pick_question(slug, title, meta.get('format'))}",
             f"{lead}: {url}",
             pick_hashtags(meta, slug, title, (post or {}).get("tags"))]
    return "\n\n".join(p for p in parts if p), url, has_blog


# ---------------------------------------------------------------- video
def resolve_mp4(meta, root, slug):
    cands = []
    f = meta.get("file")
    if f:
        cands.append(f if os.path.isabs(f) else os.path.join(root, f))
    cands.append(os.path.join(root, "public", "social", f"short-{slug}.mp4"))
    for c in cands:
        if os.path.isfile(c) and os.path.getsize(c) > 0:
            return c
    return None


def probe(mp4):
    """ffprobe → {w, h, dur, fps} | None (ffprobe yoksa sessizce atlanır)."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height,r_frame_rate:format=duration", "-of", "json", mp4],
            capture_output=True, text=True, timeout=30)
        d = json.loads(out.stdout or "{}")
        st = (d.get("streams") or [{}])[0]
        num, _, den = (st.get("r_frame_rate") or "0/1").partition("/")
        return {"w": int(st.get("width") or 0), "h": int(st.get("height") or 0),
                "dur": float((d.get("format") or {}).get("duration") or 0),
                "fps": round(float(num) / float(den or 1), 2) if float(den or 1) else 0}
    except Exception:
        return None


def spec_notes(info):
    if not info:
        return ["ffprobe yok/okunamadı — Reels sınırları kontrol edilmedi"]
    notes = []
    if info["dur"] and not (REEL_MIN_S <= info["dur"] <= REEL_MAX_S + 0.5):
        notes.append(f"süre {info['dur']:.1f} sn — Reels {REEL_MIN_S}-{REEL_MAX_S} sn dışında")
    if info["w"] and info["h"]:
        if info["w"] < 540 or info["h"] < 960:
            notes.append(f"çözünürlük {info['w']}x{info['h']} < 540x960")
        if abs(info["w"] / info["h"] - 9 / 16) > 0.02:
            notes.append(f"en-boy {info['w']}x{info['h']} 9:16 değil")
    if info["fps"] and not (23.9 <= info["fps"] <= 60.1):
        notes.append(f"{info['fps']} fps — Reels 24-60 ister")
    return notes


def get_status(video_id, tok):
    res, _ = graph_get(video_id, {"fields": "status"}, tok)
    return (res or {}).get("status") or {}


def classify(st):
    """status nesnesi → ('published' | 'processing' | 'error', ayrıntı)."""
    vs = str(st.get("video_status") or "").lower()
    phases = {k: (st.get(k) or {}) for k in ("uploading_phase", "processing_phase", "publishing_phase")}
    for name, ph in phases.items():
        if str(ph.get("status") or "").lower() == "error":
            e = ph.get("errors") or ph.get("error") or {}
            e = e[0] if isinstance(e, list) and e else e
            return "error", f"{name}: {e.get('message') if isinstance(e, dict) else e}"
    if vs in ("error", "upload_failed", "expired"):
        return "error", f"video_status={vs}"
    pub = phases["publishing_phase"]
    if str(pub.get("publish_status") or "").lower() == "published" or \
            (vs == "ready" and str(pub.get("status") or "").lower() in ("complete", "completed")):
        return "published", vs or "ready"
    return "processing", f"video_status={vs or '?'}"


def upload(video_id, upload_url, mp4, size, tok):
    """Yerel mp4 → rupload. Koparsa FB'nin aldığı bayttan sürdürür (en çok 3 deneme)."""
    p = urllib.parse.urlparse(upload_url or "")
    url = upload_url if (p.scheme == "https" and p.hostname == "rupload.facebook.com") \
        else f"{RUPLOAD}/{video_id}"                   # token yalnız FB'nin yükleme sunucusuna gider
    with open(mp4, "rb") as fh:
        blob = fh.read()
    offset, err = 0, None
    for attempt in range(3):
        req = urllib.request.Request(url, data=blob[offset:], method="POST", headers={
            "Authorization": f"OAuth {tok}", "offset": str(offset), "file_size": str(size),
            "Content-Type": "application/octet-stream"})
        res, err = _send(req, timeout=300)
        if not err and (res or {}).get("success") in (True, "true"):
            return None
        err = err or {"message": f"beklenmeyen yükleme yanıtı: {str(res)[:120]}"}
        if not err.get("retriable") or attempt == 2:
            break
        time.sleep(3 * (attempt + 1))
        up = get_status(video_id, tok).get("uploading_phase") or {}
        offset = int(up.get("bytes_transfered") or up.get("bytes_transferred") or 0)  # sic (Meta)
        if offset >= size:
            return None
    return err


def update_meta(path, fields):
    """Taze oku + yalnız kendi alanlarımızı yaz (başka betiklerin alanları ezilmez)."""
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    cur = json.loads(raw)
    cur.update(fields)
    write_json_atomic(path, cur, trailing_newline=raw.endswith("\n"))


# ---------------------------------------------------------------- akış
def dry_report(root, meta_path, mp4, size, info, desc, url, has_blog, env, already):
    say("[fb] DRY — ağa hiçbir şey yazılmaz, dosyalara dokunulmaz")
    say(f"[fb] meta : {meta_path}")
    spec = f" · {info['w']}x{info['h']} · {info['dur']:.1f} sn · {info['fps']:g} fps" if info else ""
    notes = spec_notes(info)
    say(f"[fb] mp4  : {mp4} — {size:,} bayt ({size / 1e6:.2f} MB){spec}"
        f"{' ✓ Reels sınırları içinde' if info and not notes else ''}")
    for n in notes:
        say(f"[fb] UYARI: {n}")
    say(f"[fb] link : {url}  ({'blog yazısı var' if has_blog else 'blog yazısı yok → ana sayfa'})")
    say(f"[fb] ----- açıklama ({len(desc)} karakter) -----")
    say(desc)
    say("[fb] -----------------------------------")
    pid = env.get("IG_PAGE_ID") or "<IG_PAGE_ID>"
    say("[fb] planlanan çağrılar:")
    say(f"  1) POST {API}/{pid}/video_reels  upload_phase=start")
    say(f"  2) POST {RUPLOAD}/<video_id>  (Authorization: OAuth *** · offset: 0 · "
        f"file_size: {size} · gövde = mp4 baytları; yanıttaki upload_url önceliklidir)")
    say(f"  3) POST {API}/{pid}/video_reels  upload_phase=finish video_id=<video_id> "
        "video_state=PUBLISHED description=<yukarıdaki>")
    say(f"  4) GET  {API}/<video_id>?fields=status  ({POLL_EVERY} sn arayla, en çok ~{POLL_BUDGET} sn)")
    say(f"  5) yaz: {os.path.relpath(meta_path, root)} ← fb_reel_id, fb_reel_url, fb_reel_status"
        " · logs/fb-status.json")
    if already:
        say(f"[fb] not  : zaten yayında (fb_reel_id={already}) → gerçek koşu ATLAR")
    has, note = perm_status(env)
    tail = (" → gerçek koşu sessizce atlar (Kaan: python3 scripts/instagram-reauth.py scopes)"
            if has is False else "")
    say(f"[fb] izin : {note}{tail}")
    return 0


def run(a, root):
    slug = a.slug.strip().strip("/")
    meta_path = os.path.join(root, "public", "social", f"short-{slug}.json")
    if not os.path.isfile(meta_path):
        return fail(root, slug, f"meta yok: {meta_path}", a.strict, dry=a.dry)
    with open(meta_path, encoding="utf-8") as fh:
        meta = json.load(fh)
    env = load_env()
    page_id, tok = env.get("IG_PAGE_ID"), env.get("IG_PAGE_TOKEN")

    already = str(meta.get("fb_reel_id") or "")
    if already and not a.dry:                          # idempotent: bir video = bir Reel
        cur = meta.get("fb_reel_status") or "?"
        if tok and cur != "published":                 # "processing" kaldıysa durumu tazele
            state, _ = classify(get_status(already, tok))
            if state != cur and state != "processing":
                update_meta(meta_path, {"fb_reel_status": state})
                cur = state
        say(f"[fb] atlandı: zaten yayında → {meta.get('fb_reel_url') or already} (durum: {cur})")
        write_status(root, True, f"zaten yayında ({cur})", slug, "reel")
        return 0

    mp4 = resolve_mp4(meta, root, slug)
    if not mp4:
        return fail(root, slug, f"mp4 yok/boş: {meta.get('file') or slug}", a.strict, dry=a.dry)
    size = os.path.getsize(mp4)
    info = probe(mp4)
    desc, url, has_blog = build_description(meta, slug, root)
    if a.dry:
        return dry_report(root, meta_path, mp4, size, info, desc, url, has_blog, env, already)

    if not (page_id and tok):
        return fail(root, slug, "kimlik eksik: instagram.env'de IG_PAGE_ID / IG_PAGE_TOKEN yok", a.strict)
    if info and info["dur"] and not (REEL_MIN_S <= info["dur"] <= REEL_MAX_S + 0.5):
        return fail(root, slug, f"video {info['dur']:.1f} sn — Reels {REEL_MIN_S}-{REEL_MAX_S} sn sınırı dışında",
                    a.strict)
    for n in spec_notes(info):
        say(f"[fb] uyarı: {n}")

    # 1) yükleme oturumu (izin yoksa burada döner → çıktı tek satır)
    res, err = graph_post(f"{page_id}/video_reels", {"upload_phase": "start"}, tok)
    if err:
        return perm_skip(root, slug, err) if is_perm_error(err) else \
            fail(root, slug, f"başlatılamadı: {err_text(err)}", a.strict)
    video_id = str((res or {}).get("video_id") or "")
    if not video_id:
        return fail(root, slug, f"başlatma yanıtında video_id yok: {scrub(res)[:120]}", a.strict)

    # 2) yerel dosyayı yükle
    say(f"[fb] Reel yükleniyor: {slug} ({size / 1e6:.1f} MB) → video_id={video_id}")
    err = upload(video_id, (res or {}).get("upload_url"), mp4, size, tok)
    if err:
        return perm_skip(root, slug, err) if is_perm_error(err) else \
            fail(root, slug, f"yükleme başarısız (video_id={video_id}): {err_text(err)}", a.strict)

    # 3) yayınla — yanıt ağda kaybolursa aynı video_id ile bir kez daha (çift Reel oluşmaz)
    fin = {"upload_phase": "finish", "video_id": video_id, "video_state": "PUBLISHED", "description": desc}
    res, err = graph_post(f"{page_id}/video_reels", fin, tok, timeout=120)
    if err and err.get("network"):
        time.sleep(5)
        res, err = graph_post(f"{page_id}/video_reels", fin, tok, timeout=120)
    if err:
        if is_perm_error(err):
            return perm_skip(root, slug, err)
        pub = get_status(video_id, tok).get("publishing_phase") or {}
        if str(pub.get("status") or "").lower() in ("", "not_started", "error") and \
                str(pub.get("publish_status") or "").lower() != "published":
            return fail(root, slug, f"yayınlanamadı (video_id={video_id}): {err_text(err)}", a.strict)
        say(f"[fb] uyarı: finish hata döndü ama yayın ilerliyor ({err_text(err)})")
    elif not ((res or {}).get("success") or (res or {}).get("post_id")):
        return fail(root, slug, f"beklenmeyen finish yanıtı: {scrub(res)[:120]}", a.strict)

    # 4) işlenmeyi yokla (en çok ~3 dk)
    say("[fb] işleniyor (yoklanıyor)...")
    deadline = time.time() + POLL_BUDGET
    while True:
        state, detail = classify(get_status(video_id, tok))
        if state != "processing" or time.time() + POLL_EVERY > deadline:
            break
        time.sleep(POLL_EVERY)
    if state == "error":
        return fail(root, slug, f"FB işleme hatası (video_id={video_id}): {detail}", a.strict)

    fields = {"fb_reel_id": video_id, "fb_reel_url": f"https://www.facebook.com/reel/{video_id}",
              "fb_reel_status": state}
    if (res or {}).get("post_id"):
        fields["fb_reel_post_id"] = str(res["post_id"])
    update_meta(meta_path, fields)
    say(f"[fb] ✅ REEL YAYINLANDI: {fields['fb_reel_url']} (durum: {state}"
        f"{' — FB işlemeyi sürdürüyor' if state == 'processing' else ''})")
    write_status(root, True, "yayınlandı" if state == "published" else f"yayınlandı, işleniyor ({detail})",
                 slug, "reel")
    return 0


def main(argv=None):
    try:
        sys.stdout.reconfigure(errors="backslashreplace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Shorts mp4'ünü Facebook sayfasına Reel olarak yayınlar.")
    ap.add_argument("slug")
    ap.add_argument("--dry", action="store_true", help="ağa/dosyaya yazma; açıklama + planı göster")
    ap.add_argument("--root", default="", help="repo kökü (vars.: $PARAFOMO_ROOT ya da betiğin reposu)")
    ap.add_argument("--strict", action="store_true", help="izin-dışı hatalarda exit 2")
    a = ap.parse_args(argv)
    root = resolve_root(a.root)
    try:
        return run(a, root)
    except Exception as e:                       # beklenmeyen her şey: tek satır, hat kırılmaz
        return fail(root, a.slug, f"beklenmeyen hata: {type(e).__name__}: {e}", a.strict, dry=a.dry)


if __name__ == "__main__":
    # YAYIN DURDURMA BAYRAĞI (Kaan 2026-10-30): dosya varsa hiçbir şey yayınlanmaz (--dry serbest)
    import os as _os, sys as _sys
    if _os.path.exists("/root/parafomo-data/PUBLISH_PAUSED") and "--dry" not in _sys.argv:
        print("[durduruldu] /root/parafomo-data/PUBLISH_PAUSED var — yayın yapılmadı."); _sys.exit(0)
    sys.exit(main())
