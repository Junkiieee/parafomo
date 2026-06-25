#!/usr/bin/env python3
"""
ParaFOMO — Yeni halka arzı Instagram'a postlar (olay-tetiklemeli).

data/halka-arz.json'da tarihi+fiyatı belli, daha önce postlanmamış arzları
bulur. halka-arz-card.py'nin ürettiği kartı (GitHub raw URL) IG'ye yayınlar.
dedup: logs/halka-arz-posted.txt (postlanan BİST kodları, satır satır).

Modlar:
  --list            : postlanabilir YENİ kodları yazdırır (orkestrasyon kullanır)
  --code BETAE      : o kartı postlar (kart zaten üretilmiş+push'lanmış olmalı),
                      başarılıysa kodu posted.txt'e ekler
  --code BETAE --dry: caption+URL göster, yayınlama
"""
import os
import re
import sys
import json
import time
import urllib.parse
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "halka-arz.json")
POSTED = os.path.join(ROOT, "logs", "halka-arz-posted.txt")
ENV_FILE = os.path.expanduser("~/.config/parafomo/instagram.env")
RAW = "https://raw.githubusercontent.com/Junkiieee/parafomo/main/public/social"
API = "https://graph.facebook.com/v21.0"

HASHTAGS = ("#halkaarz #borsa #bist #borsaistanbul #yatırım #hisse #parafomo")


def items():
    return json.load(open(DATA, encoding="utf-8"))["items"]


def posted_codes():
    if not os.path.exists(POSTED):
        return set()
    return {l.strip().upper() for l in open(POSTED) if l.strip()}


def is_postable(it):
    return bool(it.get("price")) and bool(it.get("start")) and \
        it.get("status") != "Tamamlandı" and bool(it.get("bist_code"))


def new_codes():
    done = posted_codes()
    out = []
    for it in items():
        code = (it.get("bist_code") or "").upper()
        if is_postable(it) and code and code not in done and code not in out:
            out.append(code)
    return out


def find(code):
    for it in items():
        if (it.get("bist_code") or "").upper() == code.upper():
            return it
    return None


def clean(s):
    return re.sub(r"\s*\*+\s*$", "", (s or "").strip()).strip()


def parse_num(s):
    m = re.findall(r"[\d.,]+", str(s or ""))
    if not m:
        return None
    try:
        return float(m[0].replace(".", "").replace(",", "."))
    except ValueError:
        return None


def offer_size(lot, price):
    lv, pv = parse_num(lot), parse_num(price)
    if not lv or not pv:
        return None
    t = lv * pv
    f = lambda n, d=0: f"{n:,.{d}f}".replace(",", "§").replace(".", ",").replace("§", ".")
    if t >= 1e9:
        return "~" + f(t / 1e9, 2) + " Milyar TL"
    if t >= 1e6:
        return "~" + f(t / 1e6, 0) + " Milyon TL"
    return f(t, 0) + " TL"


def build_caption(it):
    co = clean(it.get("company"))
    code = (it.get("bist_code") or "").upper()
    size = offer_size(it.get("lot"), it.get("price"))
    head = f"🚀 Yeni halka arz: {co} ({code}) Borsa İstanbul yolunda!"
    lines = []
    if clean(it.get("date_text")):
        lines.append(f"📅 Tarih: {clean(it.get('date_text'))}")
    if clean(it.get("price")):
        lines.append(f"💰 Fiyat: {clean(it.get('price'))}")
    if clean(it.get("distribution")):
        lines.append(f"⚖️ Dağıtım: {clean(it.get('distribution'))}")
    if size:
        lines.append(f"📊 Arz büyüklüğü: {size}")
    if clean(it.get("lot")):
        lines.append(f"🔢 Lot: {clean(it.get('lot'))}")
    body = "\n".join(lines)
    cta = "Halka arz takviminin tamamı → parafomo.com/halka-arz"
    tags = HASHTAGS + (f" #{code.lower()}" if code else "")
    return "\n\n".join([head, body, cta, tags])


def load_env():
    env = {}
    for ln in open(ENV_FILE):
        ln = ln.strip()
        if ln and not ln.startswith("#") and "=" in ln:
            k, v = ln.split("=", 1)
            env[k] = v
    return env


def http_post(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
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
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "parafomo-ig/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def record(code):
    os.makedirs(os.path.dirname(POSTED), exist_ok=True)
    with open(POSTED, "a") as f:
        f.write(code.upper() + "\n")


def post(code, dry=False):
    it = find(code)
    if not it:
        sys.exit(f"[ha] {code} bulunamadı")
    img_url = f"{RAW}/halka-arz-{code.upper()}.jpg"
    caption = build_caption(it)
    print(f"[ha] {it.get('company')} ({code})")
    print(f"[ha] URL: {img_url}")
    print(f"[ha] ----- caption -----\n{caption}\n[ha] -----------------")
    if dry:
        print("[ha] --dry: yayınlanmadı.")
        return
    if not url_ok(img_url):
        sys.exit(f"[ha] HATA: görsel canlı değil ({img_url}).")
    env = load_env()
    ig_id, token = env["IG_BUSINESS_ACCOUNT_ID"], env["IG_PAGE_TOKEN"]
    cont = http_post(f"{API}/{ig_id}/media", {
        "image_url": img_url, "caption": caption, "access_token": token})
    if "id" not in cont:
        sys.exit(f"[ha] HATA (konteyner): {json.dumps(cont, ensure_ascii=False)}")
    time.sleep(4)
    pub = http_post(f"{API}/{ig_id}/media_publish", {
        "creation_id": cont["id"], "access_token": token})
    if "id" not in pub:
        sys.exit(f"[ha] HATA (yayın): {json.dumps(pub, ensure_ascii=False)}")
    print(f"[ha] ✅ YAYINLANDI! media_id={pub['id']}")
    record(code)


def main():
    args = sys.argv[1:]
    if "--list" in args:
        for c in new_codes():
            print(c)
        return
    if "--code" in args:
        code = args[args.index("--code") + 1]
        post(code, dry="--dry" in args)
        return
    # argümansız: yeni kodları listele
    codes = new_codes()
    print("Yeni postlanabilir kodlar:", ", ".join(codes) if codes else "(yok)")


if __name__ == "__main__":
    main()
