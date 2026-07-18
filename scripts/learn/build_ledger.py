#!/usr/bin/env python3
"""
ParaFOMO — İçerik defteri (ledger) üreticisi.

Yayınlanan HER içeriği ve öğrenmeye yarayan niteliklerini mevcut artefaktlardan
türetir → data/learning/content-ledger.jsonl (idempotent, her çalışmada baştan yazar).

Kaynaklar (publisher'ları değiştirmeye gerek yok — nitelikler zaten diskte):
  • YouTube Shorts : public/social/short-*.json sidecar (format, voice, video_id, slug)
                     + logs/viral-times.csv (slot_idx, format, yayın zamanı) join
  • Instagram      : Graph API /{ig}/media (id, caption, timestamp) → caption ile sınıflandır
  • Blog           : src/content/blog/*.md (slug, pubDate)

Kayıt şeması:
  {"id","channel","subtype","slug","published_utc","attrs":{...},"refs":{...}}
"""
import os
import csv
import glob
import json
import sys
import urllib.request
import urllib.parse
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402


def split_voice(v):
    """'google:tr-TR-Chirp3-HD-Charon' → ('google','tr-TR-Chirp3-HD-Charon')."""
    if not v:
        return None, None
    if ":" in v:
        eng, voice = v.split(":", 1)
        return eng, voice
    return None, v


def load_viral_csv():
    """slug → {slot_idx, format, published_utc, url}"""
    out = {}
    path = os.path.join(lib.LOGS, "viral-times.csv")
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            slug = row.get("slug")
            if not slug:
                continue
            out[slug] = {
                "slot_idx": row.get("slot_idx"),
                "format": row.get("format"),
                "published_utc": row.get("yayin_utc"),
                "url": row.get("youtube_url"),
            }
    return out


def youtube_items():
    viral = load_viral_csv()
    rows = []
    for path in sorted(glob.glob(os.path.join(lib.SOCIAL, "short-*.json"))):
        try:
            m = json.load(open(path, encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        slug = m.get("slug") or os.path.basename(path)[len("short-"):-len(".json")]
        vid = m.get("video_id")
        if not vid:
            continue  # yüklenmemiş → metrik yok, atla
        eng, voice = split_voice(m.get("voice"))
        v = viral.get(slug, {})
        subtype = "viral" if slug in viral else "daily-short"
        if v.get("published_utc"):
            published = lib.iso(lib.parse_dt(v["published_utc"]))
        else:
            import datetime as _dt
            published = lib.iso(_dt.datetime.fromtimestamp(
                os.path.getmtime(path), _dt.timezone.utc))
        rows.append({
            "id": lib.cid("youtube", vid),
            "channel": "youtube",
            "subtype": subtype,
            "slug": slug,
            "published_utc": published,
            "attrs": {
                "format": m.get("format") or v.get("format"),
                "voice": voice,
                "engine": eng,
                "slot_idx": v.get("slot_idx"),
            },
            "refs": {"video_id": vid, "url": m.get("youtube_url") or v.get("url"), "media_id": None},
        })
    return rows


def classify_ig(caption):
    c = (caption or "").lower()
    if "halka arz" in c or "#halkaarz" in c:
        return "halka-arz"
    if "spk" in c or "onay" in c and "halka" in c:
        return "spk-onay"
    if "altın" in c or "gram altın" in c or "#altin" in c:
        return "altin"
    if "bist" in c or "borsa istanbul" in c or "kapanış" in c or "açılış" in c:
        return "bist"
    return "other"


def instagram_items(limit=200):
    env = lib.load_env(lib.IG_ENV)
    ig = env.get("IG_BUSINESS_ACCOUNT_ID")
    tok = env.get("IG_PAGE_TOKEN")
    if not (ig and tok):
        print("[ig] kimlik yok, atlandı", file=sys.stderr)
        return []
    api = "https://graph.facebook.com/v21.0"
    fields = "id,caption,media_type,permalink,timestamp"
    url = f"{api}/{ig}/media?" + urllib.parse.urlencode(
        {"fields": fields, "limit": 50, "access_token": tok})
    rows = []
    fetched = 0
    while url and fetched < limit:
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                d = json.load(r)
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            print(f"[ig] media listesi hata: {e}", file=sys.stderr)
            break
        for m in d.get("data", []):
            sub = classify_ig(m.get("caption"))
            rows.append({
                "id": lib.cid("instagram", m["id"]),
                "channel": "instagram",
                "subtype": sub,
                "slug": None,
                "published_utc": lib.iso(lib.parse_dt(m.get("timestamp"))),
                "attrs": {"subtype": sub, "media_type": m.get("media_type")},
                "refs": {"media_id": m["id"], "permalink": m.get("permalink")},
            })
            fetched += 1
        url = d.get("paging", {}).get("next")
    return rows


def blog_items():
    import re
    rows = []
    for path in glob.glob(os.path.join(lib.BLOG, "*.md")):
        raw = open(path, encoding="utf-8").read()
        front = raw.split("---", 2)[1] if raw.count("---") >= 2 else ""
        if re.search(r"^draft:\s*true", front, re.MULTILINE):
            continue
        slug = os.path.basename(path)[:-3]
        md = re.search(r"^pubDate:\s*['\"]?(\S+?)['\"]?\s*$", front, re.MULTILINE)
        rows.append({
            "id": lib.cid("blog", slug),
            "channel": "web",
            "subtype": "blog",
            "slug": slug,
            "published_utc": lib.iso(lib.parse_dt(md.group(1))) if md else None,
            "attrs": {},
            "refs": {"url": f"https://parafomo.com/blog/{slug}/"},
        })
    return rows


def main():
    rows = []
    rows += youtube_items()
    rows += instagram_items()
    rows += blog_items()
    lib.write_jsonl(lib.LEDGER, rows)
    by = {}
    for r in rows:
        by[r["channel"]] = by.get(r["channel"], 0) + 1
    print(f"[+] ledger yazıldı: {len(rows)} kayıt -> {lib.LEDGER}  {by}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
