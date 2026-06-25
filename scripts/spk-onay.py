#!/usr/bin/env python3
"""
ParaFOMO — SPK haftalık bülteninden YENİ halka arz onaylarını yakalayıp
Instagram'a (toplu) duyuru postu üretir.

Akış: SPK ana sayfasından en güncel bülten PDF'ini bul -> "İlk Halka Arzlar"
bölümünden şirketleri çek -> her şirketi halkarz ile eşleştir (logo, fiyat) ->
1 şirketse tek kart, 2+ ise tek TOPLU kart -> IG'ye postla.
dedup: logs/spk-bulten-posted.txt (bülten no, her bülten 1 kez).

Modlar:
  --build         : en güncel bülten YENİyse kartı üretir, 'NEW <no> <img>' yazar;
                    değilse 'NONE' yazar
  --post [--dry]  : en güncel bülten kartını postlar (üretilmiş+push'lanmış olmalı),
                    başarılıysa bülten no'yu kaydeder
  --info          : en güncel bülten + eşleşen şirketleri gösterir (tanı)

Bağımlılık: pypdf + Pillow (venv). LLM/token yok.
"""
import os
import re
import sys
import json
import time
import difflib
import subprocess
import urllib.parse
import urllib.request
import urllib.error
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
DATA = os.path.join(ROOT, "data", "halka-arz.json")
OUT_DIR = os.path.join(ROOT, "public", "social")
POSTED = os.path.join(ROOT, "logs", "spk-bulten-posted.txt")
ENV_FILE = os.path.expanduser("~/.config/parafomo/instagram.env")
LOGO_CACHE = "/root/.cache/parafomo/halka-arz-logos"
PDF_CACHE = "/root/.cache/parafomo/spk"
WORDMARK = os.path.join(ROOT, "public", "parafomo-wordmark.png")
RAW = "https://raw.githubusercontent.com/Junkiieee/parafomo/main/public/social"
API = "https://graph.facebook.com/v21.0"
FONT_DIR = "/usr/share/fonts/truetype/dejavu"
UA = {"User-Agent": "Mozilla/5.0 (ParaFOMO)"}

W, H = 1080, 1350
NAVY_TOP, NAVY_BOT = (10, 28, 56), (14, 40, 74)
WHITE, SOFT, TEAL, TEAL_LT = (238, 243, 250), (150, 170, 196), (43, 177, 148), (99, 212, 145)
HASHTAGS = "#halkaarz #spk #borsa #bist #borsaistanbul #yatırım #hisse #parafomo"


def F(n, s):
    return ImageFont.truetype(os.path.join(FONT_DIR, n), s)


def get(url, binary=False, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    data = urllib.request.urlopen(req, timeout=timeout).read()
    return data if binary else data.decode("utf-8", "ignore")


# ---------- bülten tespiti ----------
def latest_bulletin():
    """SPK ana sayfasından en güncel bülten (no, pdf_url)."""
    h = get("https://spk.gov.tr/")
    best = None
    for m in re.finditer(r'href="([^"]*?/(\d{4})-(\d+)\.pdf)"', h):
        url, yr, no = m.group(1), int(m.group(2)), int(m.group(3))
        if not url.startswith("http"):
            url = "https://spk.gov.tr" + url
        key = (yr, no)
        if best is None or key > best[0]:
            best = (key, url)
    if not best:
        return None, None
    (yr, no), url = best
    return f"{yr}/{no}", url


def bulletin_pdf(num, url):
    os.makedirs(PDF_CACHE, exist_ok=True)
    p = os.path.join(PDF_CACHE, num.replace("/", "-") + ".pdf")
    if not (os.path.exists(p) and os.path.getsize(p) > 10000):
        open(p, "wb").write(get(url, binary=True, timeout=40))
    return p


def extract_companies(pdf_path):
    r = PdfReader(pdf_path)
    txt = "\n".join(pg.extract_text() or "" for pg in r.pages)
    low = txt.lower()
    i = low.find("lk halka arz")
    if i < 0:
        return []
    region = re.sub(r"\s+", " ", txt[i:i + 1600])
    j = region.find("Bedelsiz")
    body = region[j + 8:] if j >= 0 else region
    names = re.findall(
        r"([A-ZİĞÜŞÖÇ][A-Za-zİığüşöçĞÜŞÖÇ\.\s]+?A[\.]?Ş)\s+\d{1,3}(?:\.\d{3}){2,}", body)
    return [re.sub(r"\s+", " ", n).strip() for n in names]


# ---------- halkarz eşleştirme ----------
TRMAP = str.maketrans("İıŞşĞğÜüÖöÇç", "IiSsGgUuOoCc")
STOP = {"anonim", "sirketi", "sirket", "sanayi", "ticaret", "tic", "san",
        "ve", "as", "a", "s", "holding", "grubu"}


def norm(s):
    s = re.sub(r"\([^)]*\)", " ", s or "")          # parantezleri at "(Orzax)"
    s = s.translate(TRMAP).lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    toks = [t for t in s.split() if t and t not in STOP]
    return " ".join(toks)


def match_halkarz(name, items):
    target = norm(name)
    best, bestr = None, 0.0
    for it in items:
        r = difflib.SequenceMatcher(None, target, norm(it.get("company", ""))).ratio()
        if r > bestr:
            best, bestr = it, r
    return best if bestr >= 0.6 else None


def batch():
    num, url = latest_bulletin()
    if not num:
        return None
    pdf = bulletin_pdf(num, url)
    names = extract_companies(pdf)
    items = json.load(open(DATA, encoding="utf-8"))["items"]
    comps = []
    for n in names:
        it = match_halkarz(n, items)
        comps.append({"name": n, "item": it})
    return {"num": num, "url": url, "companies": comps}


def already_posted(num):
    if not os.path.exists(POSTED):
        return False
    return num.strip() in {l.strip() for l in open(POSTED)}


def record(num):
    os.makedirs(os.path.dirname(POSTED), exist_ok=True)
    with open(POSTED, "a") as f:
        f.write(num.strip() + "\n")


def img_name(num):
    return f"spk-onay-{num.replace('/', '-')}.jpg"


# ---------- yardımcılar (fiyat/logo) ----------
def clean(s):
    return re.sub(r"\s*\*+\s*$", "", (s or "").strip()).strip()


def fetch_logo(it):
    if not it:
        return None
    code = (it.get("bist_code") or it.get("slug") or "x")
    os.makedirs(LOGO_CACHE, exist_ok=True)
    cache = os.path.join(LOGO_CACHE, re.sub(r"[^A-Za-z0-9-]", "", code) + ".img")
    if os.path.exists(cache) and os.path.getsize(cache) > 1000:
        return cache
    link = it.get("link")
    if not link:
        return None
    try:
        h = get(link, timeout=20)
    except Exception:
        return None
    m = re.search(r'<img[^>]*class="[^"]*slogo[^"]*"[^>]*>', h) or \
        re.search(r'<img[^>]*wp-post-image[^>]*>', h)
    if not m:
        return None
    s = re.search(r'src="([^"]+)"', m.group(0))
    if not s:
        return None
    try:
        open(cache, "wb").write(get(s.group(1), binary=True, timeout=20))
        return cache
    except Exception:
        return None


def display_name(c):
    it = c["item"]
    nm = clean(it.get("company")) if it else c["name"]
    nm = re.sub(r"\([^)]*\)", "", nm).strip()       # "(Orzax)" gibi önekleri at
    return nm


def price_of(c):
    return clean(c["item"].get("price")) if c["item"] else ""


# ---------- görsel ----------
def vgrad(w, h, top, bot):
    base = Image.new("RGB", (w, h), top)
    tl = Image.new("RGB", (w, h), bot)
    mask = Image.new("L", (w, h))
    md = mask.load()
    for y in range(h):
        v = int(255 * (y / max(1, h - 1)) ** 1.15)
        for x in range(w):
            md[x, y] = v
    base.paste(tl, (0, 0), mask)
    return base


def paste_logo(img, logo_path, x, y, sz):
    try:
        lg = Image.open(logo_path).convert("RGB")
        badge = Image.new("RGB", (sz, sz), (255, 255, 255))
        inner = sz - 16
        lg.thumbnail((inner, inner))
        badge.paste(lg, ((sz - lg.width) // 2, (sz - lg.height) // 2))
        mask = Image.new("L", (sz, sz), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, sz, sz], radius=sz // 5, fill=255)
        img.paste(badge, (x, y), mask)
        return True
    except Exception:
        return False


def render_multi(b):
    comps = b["companies"]
    img = vgrad(W, H, NAVY_TOP, NAVY_BOT).convert("RGBA")
    d = ImageDraw.Draw(img)
    f_badge = F("DejaVuSans-Bold.ttf", 30)
    f_title = F("DejaVuSans-Bold.ttf", 52)
    f_sub = F("DejaVuSans.ttf", 30)
    f_name = F("DejaVuSans-Bold.ttf", 34)
    f_price = F("DejaVuSans-Bold.ttf", 36)
    f_foot = F("DejaVuSans.ttf", 28)

    d.rectangle([0, 0, W, 14], fill=TEAL)
    badge = "SPK ONAYI"
    bb = d.textbbox((0, 0), badge, font=f_badge)
    bw = bb[2] - bb[0]
    d.rounded_rectangle([(W - bw - 60) // 2, 64, (W + bw + 60) // 2, 122], radius=29, fill=TEAL)
    d.text(((W - bw) // 2, 75), badge, font=f_badge, fill=(8, 22, 44))

    title = f"Bu Hafta {len(comps)} Halka Arz Onaylandı"
    for i, ln in enumerate(_wrap(d, title, f_title, W - 140)[:2]):
        tb = d.textbbox((0, 0), ln, font=f_title)
        d.text(((W - (tb[2] - tb[0])) // 2, 150 + i * 60), ln, font=f_title, fill=WHITE)
    sub = f"SPK Bülteni {b['num']}"
    sbb = d.textbbox((0, 0), sub, font=f_sub)
    d.text(((W - (sbb[2] - sbb[0])) // 2, 272), sub, font=f_sub, fill=TEAL_LT)

    top = 340
    avail = H - top - 150
    rh = min(150, avail // max(1, len(comps)))
    lsz = min(96, rh - 24)
    for i, c in enumerate(comps):
        cy = top + i * rh
        d.line([(70, cy), (W - 70, cy)], fill=(255, 255, 255, 26), width=1)
        midy = cy + rh // 2
        lp = fetch_logo(c["item"])
        tx = 70
        if lp and paste_logo(img, lp, 70, midy - lsz // 2, lsz):
            tx = 70 + lsz + 28
        name = display_name(c)
        for j, ln in enumerate(_wrap(d, name, f_name, W - tx - 230)[:2]):
            d.text((tx, midy - (28 if len(_wrap(d, name, f_name, W - tx - 230)) > 1 else 16) + j * 38),
                   ln, font=f_name, fill=WHITE)
        pr = price_of(c)
        if pr:
            pb = d.textbbox((0, 0), pr, font=f_price)
            d.text((W - 70 - (pb[2] - pb[0]), midy - 22), pr, font=f_price, fill=TEAL_LT)
    d.line([(70, top + len(comps) * rh), (W - 70, top + len(comps) * rh)],
           fill=(255, 255, 255, 26), width=1)

    note = "Talep tarihleri belli oldukça ayrıca paylaşacağız."
    nb = d.textbbox((0, 0), note, font=f_foot)
    d.text(((W - (nb[2] - nb[0])) // 2, H - 170), note, font=f_foot, fill=SOFT)
    if os.path.exists(WORDMARK):
        wm = Image.open(WORDMARK).convert("RGBA")
        ww = 200
        wm = wm.resize((ww, int(wm.height * ww / wm.width)))
        img.alpha_composite(wm, ((W - ww) // 2, H - 128))
    handle = "@parafomo · parafomo.com"
    hb = d.textbbox((0, 0), handle, font=f_foot)
    d.text(((W - (hb[2] - hb[0])) // 2, H - 70), handle, font=f_foot, fill=TEAL)
    return img.convert("RGB")


def _wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textbbox((0, 0), t, font=font)[2] <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def build_card(b):
    """Kartı üretir, basename döndürür. 1 şirket -> detaylı tek kart, 2+ -> toplu."""
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, img_name(b["num"]))
    comps = b["companies"]
    if len(comps) == 1 and comps[0]["item"] and comps[0]["item"].get("slug"):
        # detaylı tek kart: halka-arz-card.py --type onay -> kopyala
        slug = comps[0]["item"]["slug"]
        subprocess.run([sys.executable, os.path.join(SCRIPTS, "halka-arz-card.py"),
                        "--slug", slug, "--type", "onay"], check=True)
        key = re.sub(r"[^A-Za-z0-9-]", "", slug)
        src = os.path.join(OUT_DIR, f"halka-arz-{key}-onay.jpg")
        Image.open(src).save(out, "JPEG", quality=90)
    else:
        render_multi(b).save(out, "JPEG", quality=90)
    Image.open(out).save(os.path.join(OUT_DIR, "spk-onay-preview.jpg"), "JPEG", quality=90)
    return os.path.basename(out)


def build_caption(b):
    comps = b["companies"]
    if len(comps) == 1:
        c = comps[0]
        nm = display_name(c)
        pr = price_of(c)
        head = f"📢 SPK onayladı! {nm} halka arz yolunda."
        if pr:
            head += f" Pay fiyatı {pr}."
        body = "Talep tarihleri belli oldukça ayrıca paylaşacağız."
    else:
        head = f"📢 SPK bu hafta {len(comps)} halka arzı onayladı! (Bülten {b['num']})"
        lst = []
        for c in comps:
            pr = price_of(c)
            lst.append(f"• {display_name(c)}" + (f" — {pr}" if pr else ""))
        body = "\n".join(lst) + "\n\nTalep tarihleri belli oldukça ayrıca paylaşacağız."
    cta = "Halka arz takvimi → parafomo.com/halka-arz"
    return "\n\n".join([head, body, cta, HASHTAGS])


# ---------- IG ----------
def load_env():
    env = {}
    for ln in open(ENV_FILE):
        ln = ln.strip()
        if ln and not ln.startswith("#") and "=" in ln:
            k, v = ln.split("=", 1)
            env[k] = v
    return env


def http_post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"error": {"message": f"HTTP {e.code}"}}


def url_ok(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def do_post(dry=False):
    b = batch()
    if not b or not b["companies"]:
        print("[spk] bültende halka arz onayı yok."); return
    if already_posted(b["num"]):
        print(f"[spk] {b['num']} zaten postlanmış."); return
    img_url = f"{RAW}/{img_name(b['num'])}"
    caption = build_caption(b)
    print(f"[spk] bülten {b['num']} | {len(b['companies'])} şirket")
    print(f"[spk] URL: {img_url}")
    print(f"[spk] ----- caption -----\n{caption}\n[spk] -----------------")
    if dry:
        print("[spk] --dry: yayınlanmadı."); return
    if not url_ok(img_url):
        sys.exit(f"[spk] HATA: görsel canlı değil ({img_url}).")
    env = load_env()
    ig_id, token = env["IG_BUSINESS_ACCOUNT_ID"], env["IG_PAGE_TOKEN"]
    cont = http_post(f"{API}/{ig_id}/media", {
        "image_url": img_url, "caption": caption, "access_token": token})
    if "id" not in cont:
        sys.exit(f"[spk] HATA (konteyner): {json.dumps(cont, ensure_ascii=False)}")
    time.sleep(4)
    pub = http_post(f"{API}/{ig_id}/media_publish", {
        "creation_id": cont["id"], "access_token": token})
    if "id" not in pub:
        sys.exit(f"[spk] HATA (yayın): {json.dumps(pub, ensure_ascii=False)}")
    print(f"[spk] ✅ YAYINLANDI! media_id={pub['id']}")
    record(b["num"])


def main():
    args = sys.argv[1:]
    if "--info" in args:
        b = batch()
        if not b:
            print("bülten bulunamadı"); return
        print(f"Bülten: {b['num']}  ({'POSTLANMIŞ' if already_posted(b['num']) else 'YENİ'})")
        for c in b["companies"]:
            it = c["item"]
            print(f"  • {c['name']}  -> halkarz: {it.get('company') if it else 'EŞLEŞMEDİ'}"
                  f"  | fiyat: {price_of(c) or '?'}  | logo: {'var' if fetch_logo(it) else 'yok'}")
        return
    if "--build" in args:
        b = batch()
        if not b or not b["companies"] or already_posted(b["num"]):
            print("NONE"); return
        name = build_card(b)
        print(f"NEW {b['num']} {name}")
        return
    if "--post" in args:
        do_post(dry="--dry" in args)
        return
    print("Kullanım: --info | --build | --post [--dry]")


if __name__ == "__main__":
    main()
