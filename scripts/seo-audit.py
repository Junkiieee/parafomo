#!/usr/bin/env python3
"""ParaFOMO — SÜREKLİ SEO DENETÇİSİ (Kaan, 2026-10-15: "sayfaların SEO'sunu sürekli kontrol eden mekanizma").

İki katman:
  1) STATİK (dist/ build çıktısı, ağsız, saniyeler): her sayfada title/description uzunluğu, kanonik, H1, robots,
     sitemap↔noindex tutarlılığı, JSON-LD geçerliliği, OG görseli, alt metni, kırık iç link, sonu '/' olmayan iç link
     (301 adımı), yetim sayfa (hiç iç link almıyor), tekrarlı title/description, ince içerik, yıl bayatlığı.
  2) GOOGLE (--google): Search Console URL Inspection — günde ≤BUDGET sayfa, önce yeni/indekslenmemiş/hiç
     bakılmamış olanlar (kota 2000/gün). Durum data/learning/seo-index.json'da birikir. Ayrıca canlı 200 kontrolü.

Çıktı: data/learning/seo-audit.json (panel + brief §3b + health.py okur). Kritik sayısı ARTARSA e-posta uyarısı.
Kullanım: python3 scripts/seo-audit.py [--google] [--budget 60] [--quiet]
  (Google katmanı servis hesabı ister → /root/.venvs/parafomo/bin/python ile çalıştır.)
"""
import datetime as dt
import html
import json
import os
import re
import subprocess
import sys
import urllib.request
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.environ.get("SEO_AUDIT_DIST", os.path.join(ROOT, "dist"))   # test için değiştirilebilir
OUT = os.environ.get("SEO_AUDIT_OUT", os.path.join(ROOT, "data", "learning", "seo-audit.json"))
IDX = os.path.join(ROOT, "data", "learning", "seo-index.json")
SITE = "https://parafomo.com"
GSC_SITE = "sc-domain:parafomo.com"
SKIP_PREFIX = ("/social/", "/og/", "/_astro/")
TODAY = dt.date.today()

SEV_ORDER = {"KRİTİK": 0, "UYARI": 1, "BİLGİ": 2}
CODES = {  # kod → (önem, açıklama, nasıl düzeltilir)
    "no_title": ("KRİTİK", "title yok", "BaseLayout'a title geçir"),
    "no_canonical": ("KRİTİK", "kanonik etiket yok", "BaseLayout canonical üretmeli"),
    "bad_canonical": ("KRİTİK", "kanonik kendi adresini göstermiyor", "canonical = https://parafomo.com/<yol>/"),
    "sitemap_noindex": ("KRİTİK", "sitemap'te ama noindex", "ya noindex'i kaldır ya sitemap'ten çıkar"),
    "no_h1": ("KRİTİK", "H1 yok", "sayfaya tek bir <h1> ekle"),
    "broken_link": ("KRİTİK", "kırık iç link (404)", "linki düzelt ya da worker REDIRECTS'e ekle"),
    "bad_jsonld": ("KRİTİK", "JSON-LD bozuk (parse edilemiyor)", "şema çıktısını düzelt"),
    "google_canonical": ("KRİTİK", "Google başka bir kanonik seçmiş", "kopya içerik/iç link tutarlılığını kontrol et"),
    "live_error": ("KRİTİK", "canlıda 200 dönmüyor", "deploy/worker'ı kontrol et"),
    "multi_h1": ("UYARI", "birden fazla H1", "tek H1 bırak, diğerlerini H2 yap"),
    "no_desc": ("UYARI", "meta description yok", "BaseLayout'a description geçir"),
    "desc_long": ("UYARI", "description 165 karakterden uzun (kesilir)", "ilk 150 karakterde cevabı ver"),
    "desc_short": ("UYARI", "description 70 karakterden kısa", "sorgunun cevabını + rakamı ekle"),
    "title_long": ("UYARI", "title 70 karakterden uzun (Google keser)", "baş sorguyu öne al, kuyruğu kısalt"),
    "title_short": ("UYARI", "title 20 karakterden kısa", "baş sorgu + yıl + fayda"),
    "dup_title": ("UYARI", "aynı title başka sayfada da var", "her sayfaya ayırt edici title"),
    "dup_desc": ("UYARI", "aynı description başka sayfada da var", "her sayfaya özgün description"),
    "orphan": ("UYARI", "yetim sayfa — hiçbir sayfadan iç link almıyor", "ilgili 2 sayfadan metin içi link ver"),
    "not_in_sitemap": ("UYARI", "indekslenebilir ama sitemap'te yok", "sitemap filtresini kontrol et"),
    "no_og_image": ("UYARI", "og:image yok", "image=\"/og/<slug>.png\" + og-images.py CARDS"),
    "og_missing_file": ("UYARI", "og:image dosyası dist'te yok", "og-images.py ile üret"),
    "not_indexed": ("UYARI", "14+ gündür yayında ama Google indekslememiş", "iç link ver, içeriği güçlendir, IndexNow/sitemap"),
    "year_stale": ("UYARI", "title'daki yıl eskimek üzere/eskidi", "yeni yılı title + içerikte güncelle"),
    "slash_link": ("BİLGİ", "sonu '/' olmayan iç link (301 adımı)", "href'i '/' ile bitir"),
    "img_no_alt": ("BİLGİ", "alt niteliği hiç olmayan görsel", "anlamlı alt ekle (dekoratifse alt=\"\")"),
    "thin": ("BİLGİ", "ince içerik (<250 kelime)", "SSS/tablo/açıklama ekle"),
    "index_unknown": ("BİLGİ", "Google henüz bilmiyor (yeni sayfa)", "bekle; 14 günü geçerse uyarıya döner"),
}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.desc, self.robots, self.canonical, self.og_image = None, None, "", None, None
        self.h1 = 0
        self.links, self.imgs_no_alt, self.jsonld = [], 0, []
        self._in_title = self._in_ld = self._skip = False
        self._buf, self.text = [], []

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            n, p = (a.get("name") or "").lower(), (a.get("property") or "").lower()
            if n == "description":
                self.desc = a.get("content") or ""
            elif n == "robots":
                self.robots = (a.get("content") or "").lower()
            elif p == "og:image":
                self.og_image = a.get("content")
        elif tag == "link" and (a.get("rel") or "").lower() == "canonical":
            self.canonical = a.get("href")
        elif tag == "h1":
            self.h1 += 1
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "img" and "alt" not in a and a.get("aria-hidden") != "true":   # alt="" = bilinçli dekoratif, sorun değil
            self.imgs_no_alt += 1
        elif tag == "script" and (a.get("type") or "") == "application/ld+json":
            self._in_ld, self._buf = True, []
        elif tag in ("script", "style", "nav", "footer", "header"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._in_ld:
            self.jsonld.append("".join(self._buf))
            self._in_ld = False
        elif tag in ("script", "style", "nav", "footer", "header"):
            self._skip = False

    def handle_data(self, d):
        if self._in_title:
            self.title = (self.title or "") + d
        elif self._in_ld:
            self._buf.append(d)
        elif not self._skip:
            self.text.append(d)


def page_path(f):
    rel = os.path.relpath(f, DIST).replace(os.sep, "/")
    return "/" if rel == "index.html" else "/" + rel[: -len("index.html")]


def worker_redirects():
    try:
        src = open(os.path.join(ROOT, "worker", "index.js"), encoding="utf-8").read()
        block = re.search(r"const REDIRECTS = \{(.*?)\};", src, re.S).group(1)
        return set(re.findall(r"'(/[^']*)'\s*:", block))
    except Exception:
        return set()


def resolve(href):
    """İç link mi? → (yol, sonu-slash-eksik-mi) ; dış/anchor → None."""
    href = html.unescape(href.strip())
    if href.startswith(SITE):
        href = href[len(SITE):] or "/"
    if not href.startswith("/") or href.startswith("//"):
        return None
    path = re.split(r"[?#]", href)[0] or "/"
    if path.startswith(SKIP_PREFIX) or "." in path.rsplit("/", 1)[-1]:
        return (path, False) if "." in path.rsplit("/", 1)[-1] else None
    return (path if path.endswith("/") else path + "/"), not path.endswith("/")


def exists(path):
    if path.endswith("/"):
        return os.path.exists(os.path.join(DIST, path.lstrip("/"), "index.html"))
    return os.path.exists(os.path.join(DIST, path.lstrip("/")))


def page_ages():
    """yol → yayında kaç gün (src dosyasının git'e ilk girişi). Tek git çağrısı."""
    out = subprocess.run(["git", "-C", ROOT, "log", "--diff-filter=A", "--name-only", "--format=@%cs", "--",
                          "src/pages", "src/content/blog"], capture_output=True, text=True, timeout=60).stdout
    first, day = {}, None
    for line in out.splitlines():
        if line.startswith("@"):
            day = line[1:]
        elif line.strip():
            first[line.strip()] = day          # log yeniden eskiye → son yazılan = ilk ekleniş
    ages = {}
    for f, d in first.items():
        if f.startswith("src/content/blog/"):
            p = "/blog/" + re.sub(r"\.mdx?$", "", f.split("/")[-1]) + "/"
        else:
            p = re.sub(r"(index)?\.astro$", "", f[len("src/pages"):])
            p = p if p.endswith("/") else p + "/"
        if d:
            ages[p] = (TODAY - dt.date.fromisoformat(d)).days
    return ages


def static_audit():
    redirects = worker_redirects()
    try:
        sm = set(re.findall(r"<loc>https://parafomo\.com(.*?)</loc>", open(os.path.join(DIST, "sitemap-0.xml"), encoding="utf-8").read()))
    except OSError:
        sm = set()
    pages, issues = {}, []
    files = [os.path.join(dp, f) for dp, _, fs in os.walk(DIST) for f in fs if f == "index.html"]
    for f in files:
        path = page_path(f)
        if path.startswith(SKIP_PREFIX) or path == "/404/":
            continue
        p = Page()
        p.feed(open(f, encoding="utf-8", errors="replace").read())
        words = len(re.findall(r"\w+", " ".join(p.text)))
        pages[path] = {"title": (p.title or "").strip(), "desc": (p.desc or "").strip(), "noindex": "noindex" in p.robots,
                       "canonical": p.canonical, "h1": p.h1, "links": p.links, "og": p.og_image, "words": words,
                       "imgs_no_alt": p.imgs_no_alt, "jsonld": p.jsonld}

    def add(code, path, detail=""):
        issues.append({"code": code, "sev": CODES[code][0], "path": path, "detail": detail})

    inbound = {pth: 0 for pth in pages}
    titles, descs = {}, {}
    broken = {}
    for path, d in pages.items():
        idx = not d["noindex"]
        if not d["title"]:
            add("no_title", path)
        elif idx and len(d["title"]) > 70:
            add("title_long", path, f"{len(d['title'])} karakter")
        elif idx and len(d["title"]) < 20:
            add("title_short", path, d["title"])
        if idx:
            if not d["desc"]:
                add("no_desc", path)
            elif len(d["desc"]) > 165:
                add("desc_long", path, f"{len(d['desc'])} karakter")
            elif len(d["desc"]) < 70:
                add("desc_short", path, f"{len(d['desc'])} karakter")
            if not d["canonical"]:
                add("no_canonical", path)
            elif d["canonical"] != SITE + path:
                add("bad_canonical", path, d["canonical"])
            if d["h1"] == 0:
                add("no_h1", path)
            elif d["h1"] > 1:
                add("multi_h1", path, f"{d['h1']} adet")
            if path not in sm:
                add("not_in_sitemap", path)
            if not d["og"]:
                add("no_og_image", path)
            elif d["og"].startswith(SITE) and not exists(d["og"][len(SITE):]):
                add("og_missing_file", path, d["og"][len(SITE):])
            if d["words"] < 250 and path != "/":
                add("thin", path, f"{d['words']} kelime")
            if d["title"]:
                titles.setdefault(d["title"], []).append(path)
            if d["desc"]:
                descs.setdefault(d["desc"], []).append(path)
            # yıl bayatlığı: Aralık-Ocak'ta title yalnız eski yılı taşıyorsa
            ys = set(re.findall(r"\b(20\d\d)\b", d["title"]))
            if ys and (TODAY.month == 12 and str(TODAY.year) in ys and str(TODAY.year + 1) not in ys
                       or TODAY.month <= 2 and str(TODAY.year - 1) in ys and str(TODAY.year) not in ys):
                add("year_stale", path, "title yılları: " + ", ".join(sorted(ys)))
        elif path in sm:
            add("sitemap_noindex", path)
        for raw in d["jsonld"]:
            try:
                json.loads(raw)
            except ValueError as e:
                add("bad_jsonld", path, str(e)[:80])
        if d["imgs_no_alt"]:
            add("img_no_alt", path, f"{d['imgs_no_alt']} görsel")
        seen_slash = False
        for href in d["links"]:
            r = resolve(href)
            if not r:
                continue
            tgt, no_slash = r
            if no_slash and not seen_slash:
                add("slash_link", path, href)
                seen_slash = True
            if tgt in redirects:
                continue
            if not exists(tgt):
                broken.setdefault(tgt, set()).add(path)
            elif tgt in inbound and tgt != path:
                inbound[tgt] += 1
    for tgt, srcs in broken.items():
        for src in sorted(srcs)[:5]:
            add("broken_link", src, f"→ {tgt}" + (f" (+{len(srcs) - 5} sayfa daha)" if len(srcs) > 5 and src == sorted(srcs)[4] else ""))
    for path, n in inbound.items():
        if n == 0 and path != "/" and not pages[path]["noindex"]:
            add("orphan", path)
    for t, ps in titles.items():
        if len(ps) > 1:
            for pth in ps:
                add("dup_title", pth, f"{len(ps)} sayfa: " + ", ".join(x for x in ps if x != pth)[:120])
    for t, ps in descs.items():
        if len(ps) > 1:
            for pth in ps:
                add("dup_desc", pth, f"{len(ps)} sayfa")
    return pages, issues


def google_layer(pages, issues, budget, ages):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    cred = service_account.Credentials.from_service_account_file(
        os.path.expanduser("~/.config/parafomo/ga-sa.json"), scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    svc = build("searchconsole", "v1", credentials=cred, cache_discovery=False)
    try:
        state = json.load(open(IDX, encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    cands = [p for p, d in pages.items() if not d["noindex"]]

    def prio(p):
        s = state.get(p)
        if not s:
            return (0, 0)                                   # hiç bakılmamış
        if s.get("verdict") != "PASS":
            return (1, s.get("checked", ""))                # indekste değil → sık bak
        if ages.get(p, 999) < 30:
            return (2, s.get("checked", ""))                # yeni sayfa
        return (3, s.get("checked", ""))                    # en eski kontrol önce
    done = 0
    for p in sorted(cands, key=prio)[:budget]:
        try:
            r = svc.urlInspection().index().inspect(body={"inspectionUrl": SITE + p, "siteUrl": GSC_SITE,
                                                          "languageCode": "tr"}).execute()
            i = r["inspectionResult"]["indexStatusResult"]
            state[p] = {"verdict": i.get("verdict"), "coverage": i.get("coverageState"), "lastCrawl": i.get("lastCrawlTime"),
                        "googleCanonical": i.get("googleCanonical"), "checked": TODAY.isoformat()}
            done += 1
        except Exception as e:
            print(f"[seo] URL Inspection durdu ({done} sayfa): {str(e)[:120]}")
            break
    json.dump(state, open(IDX, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for p, s in state.items():
        if p not in pages or pages[p]["noindex"]:
            continue
        gc = s.get("googleCanonical")
        if gc and gc.rstrip("/") != (SITE + p).rstrip("/"):
            issues.append({"code": "google_canonical", "sev": "KRİTİK", "path": p, "detail": gc})
        if s.get("verdict") != "PASS":
            age = ages.get(p)
            code = "not_indexed" if (age is None or age >= 14) else "index_unknown"
            issues.append({"code": code, "sev": CODES[code][0], "path": p,
                           "detail": f"{s.get('coverage')}" + (f" · {age} gündür yayında" if age is not None else "")})
    # canlı kontrol: bugün bakılanlar + yeni sayfalar (ucuz HEAD)
    live = [p for p in cands if ages.get(p, 999) < 30][:40]
    for p in live:
        try:
            req = urllib.request.Request(SITE + p, method="HEAD", headers={"User-Agent": "parafomo-seo-audit"})
            with urllib.request.urlopen(req, timeout=15) as r:
                if r.status != 200:
                    issues.append({"code": "live_error", "sev": "KRİTİK", "path": p, "detail": str(r.status)})
        except Exception as e:
            issues.append({"code": "live_error", "sev": "KRİTİK", "path": p, "detail": str(e)[:60]})
    return state, done


def main():
    quiet = "--quiet" in sys.argv
    budget = int(sys.argv[sys.argv.index("--budget") + 1]) if "--budget" in sys.argv else 60
    if not os.path.isdir(DIST):
        print("[seo] dist/ yok — önce npm run build")
        return 0
    pages, issues = static_audit()
    ages = page_ages()
    idx_state, inspected = ({}, 0)
    if "--google" in sys.argv:
        try:
            idx_state, inspected = google_layer(pages, issues, budget, ages)
        except Exception as e:
            print(f"[seo] Google katmanı atlandı: {str(e)[:160]}")
    if not idx_state:
        try:
            idx_state = json.load(open(IDX, encoding="utf-8"))
        except (OSError, ValueError):
            idx_state = {}
    issues.sort(key=lambda i: (SEV_ORDER[i["sev"]], i["code"], i["path"]))
    counts = {s: sum(1 for i in issues if i["sev"] == s) for s in SEV_ORDER}
    by_code = {}
    for i in issues:
        by_code[i["code"]] = by_code.get(i["code"], 0) + 1
    indexable = [p for p, d in pages.items() if not d["noindex"]]
    idx_pass = sum(1 for p in indexable if idx_state.get(p, {}).get("verdict") == "PASS")
    idx_known = sum(1 for p in indexable if p in idx_state)
    try:
        prev = json.load(open(OUT, encoding="utf-8"))
    except (OSError, ValueError):
        prev = {}
    data = {
        "_aciklama": "scripts/seo-audit.py — statik (dist) + Google URL Inspection denetimi. sev: KRİTİK/UYARI/BİLGİ.",
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "pages": len(pages), "indexable": len(indexable),
        "index": {"checked": idx_known, "indexed": idx_pass, "inspected_today": inspected},
        "counts": counts, "by_code": by_code,
        "codes": {k: {"sev": v[0], "label": v[1], "fix": v[2]} for k, v in CODES.items()},
        "issues": issues,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[seo] {len(pages)} sayfa · KRİTİK {counts['KRİTİK']} · UYARI {counts['UYARI']} · BİLGİ {counts['BİLGİ']} · "
          f"indeks {idx_pass}/{idx_known} bakılan ({inspected} bugün)")
    if not quiet:
        for i in issues:
            if i["sev"] == "KRİTİK":
                print(f"  KRİTİK {i['code']:<16} {i['path']} {i['detail']}")
    # kritik sayısı arttıysa e-posta (günde bir)
    if counts["KRİTİK"] > (prev.get("counts") or {}).get("KRİTİK", 0) and "--google" in sys.argv:
        crit = [f"- {i['code']}: {i['path']} {i['detail']}" for i in issues if i["sev"] == "KRİTİK"][:15]
        subprocess.run([sys.executable if os.path.exists(sys.executable) else "python3",
                        os.path.join(ROOT, "agent", "notify.py"), "alert", "--key", "seo-crit",
                        "--subject", f"⚠️ ParaFOMO SEO: {counts['KRİTİK']} kritik sorun",
                        "--body", "Denetim yeni kritik sorun buldu (panel → Üretim → SEO):\n\n" + "\n".join(crit)
                        + "\n\nGece ajanı brief §3b'den alıp düzeltir."], timeout=60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
