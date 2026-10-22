#!/usr/bin/env python3
"""ParaFOMO — FIRSAT MOTORU: "çok aranan + tıklanabilir" sorguları bulur, sıralar, eyleme çevirir.

Neden (2026-10-14 teşhisi): site ayda ~7K gösterim alıyor. Her sorguda 1. sıra olsak bile bu, günde
~60 ziyaretçi eder. Sorun sıralamadan önce KONU SEÇİMİ. 143 yazının 36'sı az aranan ABD makro haberi.
Talep radarı (demand_miner) "sorgu var mı" diyordu ama "kaç kişi arıyor" demiyordu: Autocomplete'in
"altın fiyatı ne zaman düşer" gibi önerilerinin Trends hacmi ~0 çıktı.

Akış:
  1) Aday sorgular: GSC (28g, sorgu+sayfa) · Autocomplete boşlukları (demand-gaps.json) ·
     mevsimsel takvim (bu ay + 2 ay) · HEAD_TERMS (bilinen büyük finans araç/veri sorguları).
  2) Kümele: aynı niyetli varyantlar tek satır (token kökü örtüşmesi).
  3) Hacim: Google Trends (TR, son 12 ay) → ÇAPA = "mevduat faizi" = 100 olacak şekilde ölçeklenir.
     Trends grup içinde 0-100 normalize ettiği için her istekte çapa + 4 aday; oran = aday/çapa.
     Önbellek 21 gün (data/learning/trends-cache.json) → haftada ~15 istek, 429 riski düşük.
  4) Skor = hacim × niyet (araç sorgusu ↑, Google'ın kendi cevap verdiği fiyat sorgusu ↓) × erişilebilirlik
     (mevcut GSC sırası). Eylem: CTR düzelt / güçlendir / yeniden kur / YENİ araç-veri sayfası / YENİ yazı.

Çıktı: data/learning/opportunities.json → brief §9c + haftalık/günlük koşu konu seçimi.
Trends düşerse: önbellekteki değerlerle devam eder; hiç değer yoksa GSC-temelli sıralama yazar.

Kullanım: /root/.venvs/parafomo/bin/python scripts/learn/opportunity_finder.py [--verbose] [--max-fetch N]
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

OUT = os.path.join(lib.DATA, "opportunities.json")
CACHE = os.path.join(lib.DATA, "trends-cache.json")
GAPS = os.path.join(lib.DATA, "demand-gaps.json")
SEASONAL = os.path.join(lib.ROOT, "data", "tr-seasonal-seo.json")
GSC_SITE = "sc-domain:parafomo.com"
GSC_SCOPE = ["https://www.googleapis.com/auth/webmasters.readonly"]

ANCHOR = "mevduat faizi"      # orta hacimli, yıl boyu istikrarlı; ölçek: çapa = 100
TIMEFRAME = "today 12-m"      # mevsimsel zirveleri (Ocak emekli zammı, Aralık asgari ücret) kaçırmamak için
CACHE_DAYS = 21
DEFAULT_MAX_FETCH = 64        # tek koşuda Trends'e sorulacak en fazla yeni sorgu (16 istek)

# Türkiye'de bilinen büyük finans araç/veri sorguları — sitede karşılığı olmayan dev talebi görmek için.
HEAD_TERMS = [
    "kredi hesaplama", "konut kredisi hesaplama", "ihtiyaç kredisi hesaplama", "taşıt kredisi hesaplama",
    "mevduat faizi hesaplama", "net maaş hesaplama", "brütten nete maaş hesaplama", "kıdem tazminatı hesaplama",
    "ihbar tazminatı hesaplama", "işsizlik maaşı hesaplama", "emekli zammı", "memur zammı", "asgari ücret",
    "kira artış oranı", "enflasyon oranı", "halka arz takvimi", "halka arz", "bono hesaplama",
    "eurobond", "bes", "fon getirileri", "temettü takvimi", "bist 100", "gram altın", "çeyrek altın",
    "altın hesaplama", "altın fiyatları", "dolar kuru", "euro kuru", "bitcoin", "kdv hesaplama",
    "gelir vergisi hesaplama", "vergi dilimi", "mtv hesaplama", "emlak vergisi", "veraset vergisi",
    "damga vergisi hesaplama", "kredi kartı asgari ödeme", "bileşik faiz hesaplama", "faiz kararı",
    "yeniden değerleme oranı", "trafik cezası sorgulama", "pasaport harcı", "ehliyet harcı",
    "doğum izni hesaplama", "yıllık izin hesaplama", "kira gelir vergisi", "altın mı dolar mı",
    # genişletme 2026-10-15 (Kaan: "tüm kelimelerde siteyi güçlendir") — TR finans araç/veri/rehber evreni
    "kredi kartı faiz hesaplama", "kredi yapılandırma", "kredi notu", "findeks", "erken kapama hesaplama",
    "kredi faiz oranları", "konut kredisi faiz oranları", "ihtiyaç kredisi faiz oranları", "taşıt kredisi faiz oranları",
    "mevduat faiz oranları", "en yüksek mevduat faizi", "vadeli mevduat", "repo faizi", "tefas",
    "para piyasası fonu", "altın fonu", "hisse senedi nasıl alınır", "temettü hesaplama", "lot hesaplama",
    "bedelsiz sermaye artırımı", "bedelli sermaye artırımı", "halka arz sonuçları", "spk onayı",
    "döviz hesaplama", "altın kaç gram", "22 ayar bilezik", "cumhuriyet altını", "ons altın",
    "gümüş fiyatları", "bitcoin kaç tl", "kripto vergi", "stopaj", "stopaj hesaplama",
    "fazla mesai hesaplama", "agi hesaplama", "brüt asgari ücret", "asgari ücret 2027", "memur maaşı",
    "emekli maaşı", "bayram ikramiyesi", "en düşük emekli maaşı", "emekli maaş hesaplama", "emeklilik hesaplama",
    "ne zaman emekli olurum", "sgk prim borcu", "bağkur borcu", "tazminat hesaplama", "kira artışı",
    "tapu harcı hesaplama", "noter ücreti", "araç muayene ücreti", "değer artış kazancı",
    "veraset ve intikal vergisi", "kurumlar vergisi", "geçici vergi", "beyanname", "vergi borcu sorgulama",
    "enflasyon hesaplama", "enflasyon farkı hesaplama", "tüfe", "yi üfe", "reel getiri hesaplama",
    "faiz hesaplama", "yüzde hesaplama", "dolar endeksi", "abd faiz kararı", "ppk",
    # genişletme 2026-10-22 (haftalık koşu Trends ölçümü)
    "emekli promosyon", "fed faiz kararı", "enflasyon beklentisi", "ek gösterge", "sgk hizmet dökümü",
    "emeklilik yaşı", "katılım hesabı", "kredi kartı faiz oranı", "çocuk parası",
]

STOP = set("mı mi mu mü ne nasıl kaç kadar için ile ve veya da de bu şu o en çok hangi "
           "nedir olacak oldu olur yılı yili ayı ayi son dakika".split())
ASCII = str.maketrans("şŞıİğĞüÜöÖçÇâî", "sSiIgGuUoOcCai")
YEARS = {str(y) for y in range(2024, 2031)}

TOOL_WORDS = ("hesaplama", "hesapla", "orani", "takvimi", "tablosu", "getiri", "sorgulama", "simulasyon")
INSTANT_WORDS = ("fiyati", "fiyatlari", "kuru", "kac tl", "bugun", "canli", "anlik", "son dakika")
BLOCK_WORDS = ("music", "awards", "vmas", "malta", "muhasebe kaydi", "lisesi", "russell")   # gürültü
BLOCK_EXACT = {"yatirim", "borsa", "doviz", "faiz", "altin"}   # tek kelimelik genel sorgu — kazanılamaz, niyet belirsiz
# niyeti anlık fiyat olan ama "fiyatı" demeyen sorgular (Google kur/fiyat kutusu gösterir)
PRICE_HEADS = ("gram altin", "ceyrek altin", "dolar kuru", "euro kuru", "bitcoin", "bist 100", "ons altin")


def ascii_low(s):
    return s.lower().translate(ASCII)


def stems(q):
    toks = [t for t in re.findall(r"[a-z0-9]+", ascii_low(q)) if t not in STOP and t not in YEARS and len(t) > 1]
    return frozenset(t[:5] for t in toks)


# ----------------------------------------------------------------- adaylar

def gsc_queries():
    """{query: {impr, clicks, pos, page}} — son 28 gün, her sorgu için en çok gösterim alan sayfa."""
    creds = lib.ga_credentials(GSC_SCOPE)
    if creds is None:
        return {}
    from googleapiclient.discovery import build
    sc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    end = dt.date.today()
    body = {"startDate": (end - dt.timedelta(days=28)).isoformat(), "endDate": end.isoformat(),
            "dimensions": ["query", "page"], "rowLimit": 5000}
    rows = sc.searchanalytics().query(siteUrl=GSC_SITE, body=body).execute().get("rows", [])
    out = {}
    for r in rows:
        q, page = r["keys"]
        if "parafomo" in q:
            continue
        o = out.setdefault(q, {"impr": 0, "clicks": 0, "_pw": 0.0, "page": page, "_best": 0})
        o["impr"] += r["impressions"]
        o["clicks"] += r["clicks"]
        o["_pw"] += r["position"] * r["impressions"]
        if r["impressions"] > o["_best"]:
            o["_best"], o["page"] = r["impressions"], page
    for o in out.values():
        o["pos"] = round(o.pop("_pw") / max(o["impr"], 1), 1)
        o.pop("_best")
        o["page"] = re.sub(r"^https?://[^/]+", "", o["page"]).rstrip("/") or "/"
    return out


def autocomplete_queries():
    try:
        g = json.load(open(GAPS, encoding="utf-8"))
    except Exception:
        return []
    qs = list(g.get("uncovered_top", []))
    for s in g.get("seeds", []):
        qs.append(s["seed"])
        qs += [x["q"] for x in s.get("suggestions", [])[:5]]
    return qs


SUBPAGE_SKIP = {"halka-arz"}
# Kökü sayfa slug'ında geçmeyen ama kanonik sayfası belli sorgular (2026-10-22: "memur maaşı" YENI_YAZI görünüyordu).
# Sayfa henüz yoksa sorgu "sitede yok" sayılır (YENI_ARAC/YENI_YAZI).
SYNONYMS = {
    "emeklilik hesaplama": "/emeklilik-hesaplama",
    "katılım hesabı": "/blog/katilim-hesabi-nedir",
    "ek gösterge": "/blog/ek-gosterge-nedir",
    "memur maaşı": "/memur-zammi-hesaplama",
    "trafik cezası sorgulama": "/trafik-cezalari-hesaplama",
    "çocuk parası": "/dogum-yardimi",
    "sgk prim borcu": "/vergi-borcu-sorgulama",
    "bağkur borcu": "/bagkur-primi-hesaplama",
    "emekli maaşı": "/en-dusuk-emekli-maasi",
    "emekli promosyon": "/emekli-promosyonu",
    "ne zaman emekli olurum": "/emeklilik-hesaplama",
    "emeklilik yaşı": "/emeklilik-hesaplama",
    "sgk hizmet dökümü": "/emeklilik-hesaplama",
}


def seasonal_queries(today):
    try:
        d = json.load(open(SEASONAL, encoding="utf-8"))
    except Exception:
        return {}
    months = {(today.month + k - 1) % 12 + 1 for k in range(3)}
    out = {}
    for t in d.get("takvim", []):
        if t.get("ay") in months:
            for q in t.get("sorgular", []):
                out[q] = t.get("sayfa")
    return out


def site_pages():
    """[(url, stem-set)] — astro sayfaları + blog yazıları."""
    pages = []
    pdir = os.path.join(lib.ROOT, "src", "pages")
    for f in os.listdir(pdir):
        if f.endswith(".astro") and f not in ("index.astro", "404.astro"):
            pages.append(("/" + f[:-6], stems(f[:-6].replace("-", " "))))
        elif os.path.isdir(os.path.join(pdir, f)) and f not in ("blog", "kategori", "portfoy"):
            pages.append(("/" + f, stems(f.replace("-", " "))))
            # dinamik route alt sayfaları (/altin-fiyatlari/ceyrek-altin) — build çıktısından; halka arz şirket adları gürültü
            ddir = os.path.join(lib.ROOT, "dist", f)
            if f not in SUBPAGE_SKIP and os.path.isdir(ddir):
                for sub in sorted(os.listdir(ddir)):
                    if os.path.isfile(os.path.join(ddir, sub, "index.html")):
                        pages.append((f"/{f}/{sub}", stems(sub.replace("-", " "))))
    if os.path.isdir(lib.BLOG):
        for f in os.listdir(lib.BLOG):
            if f.endswith((".md", ".mdx")):
                s = f.rsplit(".", 1)[0]
                pages.append((f"/blog/{s}", stems(s.replace("-", " "))))
    return pages


def match_page(q, pages):
    st = stems(q)
    if not st:
        return None
    best, url, extra = 0.0, None, 99
    for u, ps in pages:
        if not ps:
            continue
        sc = len(st & ps) / len(st)
        ex = len(ps - st)  # sorguda olmayan kök sayısı: az olan daha tam eşleşme ("kredi hesaplama" → /kredi-hesaplama)
        # eşitlikte: araç/veri sayfası (blog değil) > sorguya en birebir sayfa
        better = sc > best or (sc == best and url is not None and (
            (url.startswith("/blog/") and not u.startswith("/blog/")) or
            (url.startswith("/blog/") == u.startswith("/blog/") and ex < extra)))
        if better:
            best, url, extra = sc, u, ex
    return url if best >= 0.67 else None


def cluster(cands):
    """cands: {query: meta} → [{rep, variants, meta...}] — token kökü kümesi eşit/çok örtüşen sorgular tek küme."""
    groups = []
    for q in sorted(cands, key=lambda x: (-cands[x].get("impr", 0), len(x))):
        st = stems(q)
        if not st:
            continue
        for g in groups:
            j = len(st & g["stems"]) / len(st | g["stems"])
            if j >= 0.75:
                g["variants"].append(q)
                break
        else:
            groups.append({"rep": q, "stems": st, "variants": [q]})
    return groups


# ----------------------------------------------------------------- Trends

def load_cache():
    try:
        c = json.load(open(CACHE, encoding="utf-8"))
        if c.get("anchor") == ANCHOR and c.get("timeframe") == TIMEFRAME:
            return c
    except Exception:
        pass
    return {"anchor": ANCHOR, "timeframe": TIMEFRAME, "q": {}}


def trends_term(q):
    """Gelecek yıl içeren sorgunun Trends geçmişi olmaz ("asgari ücret 2027 zam oranı" Ekim'de 0, Aralık'ta
    zirve) → geçen yılın eşdeğeriyle ölç ("… 2026 …"). Talep yıllık tekrar ettiği için iyi bir vekil."""
    this = dt.date.today().year
    return re.sub(r"\b(20[2-3]\d)\b", lambda m: str(int(m.group(1)) - 1) if int(m.group(1)) > this else m.group(1), q)


def trends_fetch(queries, cache, verbose=False):
    """Önbellekte taze olmayan sorguları çapa ile 4'erli gruplarda sorar. Değer = 12 ay ort. / çapa × 100."""
    try:
        from pytrends.request import TrendReq
    except ImportError:
        print("[firsat] UYARI: pytrends yok — yalnız önbellek/GSC")
        return 0
    py = TrendReq(hl="tr-TR", tz=-180, timeout=(10, 30))
    fetched, fails = 0, 0
    for i in range(0, len(queries), 4):
        batch = queries[i:i + 4]
        terms = {q: trends_term(q) for q in batch}
        if len(set(terms.values())) < len(terms):   # vekil terimler çakışırsa orijinali kullan
            terms = {q: q for q in batch}
        try:
            py.build_payload([ANCHOR] + list(terms.values()), geo="TR", timeframe=TIMEFRAME)
            df = py.interest_over_time()
        except Exception as e:
            fails += 1
            print(f"[firsat] Trends hata ({fails}): {str(e)[:120]}")
            if fails >= 3:
                break
            time.sleep(30 * fails)
            continue
        today = dt.date.today().isoformat()
        if df is None or df.empty:
            for q in batch:   # Trends veri eşiğinin altı = çok düşük hacim
                cache["q"][q] = {"idx": 0.0, "recent": 0.0, "peak": 0.0, "date": today}
        else:
            a = float(df[ANCHOR].mean()) or 1e-9
            for q in batch:
                s = df[terms[q]] if terms[q] in df else None
                if s is None:
                    continue
                cache["q"][q] = {
                    "idx": round(float(s.mean()) / a * 100, 1),
                    "recent": round(float(s.tail(4).mean()) / a * 100, 1),   # son 4 hafta
                    "peak": round(float(s.max()) / a * 100, 1),
                    "peak_week": str(s.idxmax().date()),
                    "date": today,
                }
                if terms[q] != q:
                    cache["q"][q]["vekil"] = terms[q]
        fetched += len(batch)
        if verbose:
            print("  " + " · ".join(f"{q}={cache['q'].get(q, {}).get('idx')}" for q in batch))
        time.sleep(4)
    return fetched


def fresh(entry):
    try:
        return (dt.date.today() - dt.date.fromisoformat(entry["date"])).days <= CACHE_DAYS
    except Exception:
        return False


# ----------------------------------------------------------------- skor + eylem

def expected_ctr(pos):
    return 0.28 if pos <= 1.5 else 0.15 if pos <= 3 else 0.07 if pos <= 6 else 0.03 if pos <= 10 else 0.01


def intent_factor(q):
    a = ascii_low(q)
    if any(w in a for w in INSTANT_WORDS) or any(a.startswith(h) for h in PRICE_HEADS):
        return 0.4, "fiyat/anlık (Google kendi cevaplar, tık az)"
    if any(w in a for w in TOOL_WORDS):
        return 1.3, "araç/veri niyeti"
    return 1.0, "bilgi"


def competition_factor(q, vol):
    """Dev baş terimde (≤2 kelime, çok yüksek hacim) ilk sayfa büyük sitelere kilitli → yeni domain için düşük."""
    if vol is not None and vol >= 200 and len(stems(q)) <= 2:
        return 0.4
    return 1.0


_TITLE_CACHE = {}


def page_title_stems(page):
    """Sayfanın <title> + <h1> kökleri — önce build çıktısı (dist/<slug>/index.html), yoksa .astro'daki title=."""
    if not page:
        return frozenset()
    path = re.sub(r"^https?://[^/]+", "", page).strip("/")
    if path in _TITLE_CACHE:
        return _TITLE_CACHE[path]
    text = ""
    html_f = os.path.join(lib.ROOT, "dist", path, "index.html")
    astro_f = os.path.join(lib.ROOT, "src", "pages", path + ".astro")
    try:
        if os.path.exists(html_f):
            h = open(html_f, encoding="utf-8").read()
            text = " ".join(re.findall(r"<title>(.*?)</title>", h, re.S)[:1] + re.findall(r"<h1[^>]*>(.*?)</h1>", h, re.S)[:1])
        elif os.path.exists(astro_f):
            a = open(astro_f, encoding="utf-8").read()
            text = " ".join(re.findall(r'title=[{`"]+([^`"}]+)', a)[:1] + re.findall(r"<h1[^>]*>(.*?)</h1>", a, re.S)[:1])
    except OSError:
        pass
    st = stems(re.sub(r"<[^>]+>|\$\{[^}]*\}", " ", text))
    _TITLE_CACHE[path] = st
    return st


_AGE_CACHE = {}


def page_age_days(page):
    """Sayfa kaç gündür yayında — dosyanın git'e ilk eklendiği gün (bulunamazsa None)."""
    path = re.sub(r"^https?://[^/]+", "", page or "").strip("/")
    if path in _AGE_CACHE:
        return _AGE_CACHE[path]
    cands = ([f"src/content/blog/{path[5:]}.md", f"src/content/blog/{path[5:]}.mdx"] if path.startswith("blog/")
             else [f"src/pages/{path}.astro", f"src/pages/{path}/index.astro", f"src/pages/{path}"])
    age = None
    for c in cands:
        if os.path.exists(os.path.join(lib.ROOT, c)):
            try:
                out = subprocess.run(["git", "-C", lib.ROOT, "log", "--diff-filter=A", "--format=%cs", "--", c],
                                     capture_output=True, text=True, timeout=20).stdout.split()
                age = (dt.date.today() - dt.date.fromisoformat(out[-1])).days if out else 0  # commit yok = bugün
            except Exception:
                age = None
            break
    _AGE_CACHE[path] = age
    return age


def otorite(rep, g, page):
    """Sayfa var + (GSC'de sorgu yok ya da sıra >40) + başlık/H1 sorgunun TÜM köklerini zaten içeriyor
    → sorun başlık değil site otoritesi (2026-10-15 haftalık teşhis: hesaplayıcılar baş sorgularda p57-100)."""
    if not page or (g and g["pos"] <= 40):
        return False
    q = stems(rep)
    return bool(q) and q <= page_title_stems(page)


def decide(rep, g, page, kind_tool):
    age = page_age_days(page) if page else None
    if page and not g and age is not None and age < 28:
        return "BEKLE", 0.2, f"sayfa {age} gündür yayında — indeks ve sıra oturmadan görev üretme"
    if otorite(rep, g, page):
        where = f"sıra {g['pos']}" if g else "bu sorguda gösterim yok"
        return "OTORITE", 0.3, (f"{where} ama başlık/H1 sorguyu zaten içeriyor → sorun on-page değil, site otoritesi; "
                                "başlık görevi YAPMA — uzun kuyruk / gelecek yıl (2027) açısıyla ya da iç+dış linkle gir")
    if g:
        pos, impr, clicks = g["pos"], g["impr"], g["clicks"]
        if pos <= 10 and impr >= 30 and clicks / impr < expected_ctr(pos) * 0.5:
            return "CTR", 1.0, f"sıra {pos} ama tık {clicks}/{impr} → başlık+açıklamayı sorgunun cevabına göre yenile"
        if pos <= 10 and impr >= 20:
            return "KORU", 1.0, f"sıra {pos} — ilk sayfada; tazelik + iç link yeter"
        if pos <= 10:
            return "GUCLENDIR", 0.8, f"sıra {pos} ama yalnız {impr} gösterim → ana varyantta görünmüyoruz; başlığı baş sorguya göre kur"
        if pos <= 30:
            return "GUCLENDIR", 0.7, f"sıra {pos} → sayfayı sorguya göre derinleştir (tablo/SSS/güncel veri) + iç link"
        return "YENIDEN_KUR", 0.35, f"sıra {pos} → sayfa sorguyu karşılamıyor; niyete göre yeniden kur ya da ayrı sayfa aç"
    if page:
        return "GUCLENDIR", 0.4, "sayfa var ama bu sorguda gösterim yok → başlık/H1/içerik bu sorguyu hedeflemiyor"
    if kind_tool:
        return "YENI_ARAC", 0.35, "sitede karşılığı yok → hesaplama/veri sayfası"
    return "YENI_YAZI", 0.3, "sitede karşılığı yok → rehber yazı"


def main():
    verbose = "--verbose" in sys.argv
    max_fetch = DEFAULT_MAX_FETCH
    if "--max-fetch" in sys.argv:
        max_fetch = int(sys.argv[sys.argv.index("--max-fetch") + 1])
    today = dt.date.today()

    try:
        gsc = gsc_queries()
    except Exception as e:
        print(f"[firsat] UYARI: GSC alınamadı: {e}")
        gsc = {}
    seasonal = seasonal_queries(today)

    cands = {}
    for q, m in gsc.items():
        if m["impr"] >= 8:
            cands[q] = {"impr": m["impr"], "src": "gsc"}
    for q in autocomplete_queries():
        cands.setdefault(q, {"src": "autocomplete"})
    for q in seasonal:
        cands.setdefault(q, {"src": "mevsimsel"})
    for q in HEAD_TERMS:
        cands.setdefault(q, {"src": "bas-terim"})
    cands = {q: m for q, m in cands.items()
             if not any(b in ascii_low(q) for b in BLOCK_WORDS) and ascii_low(q).strip() not in BLOCK_EXACT}
    groups = cluster(cands)

    cache = load_cache()
    # Trends'e her kümenin temsilcisini sor (en kısa/en çok gösterimli varyant); önce GSC'li ve baş terimler
    need = [g["rep"] for g in groups if g["rep"] != ANCHOR and not fresh(cache["q"].get(g["rep"], {}))]
    need.sort(key=lambda q: (cands[q]["src"] not in ("gsc", "bas-terim", "mevsimsel"), -cands[q].get("impr", 0)))
    n = trends_fetch(need[:max_fetch], cache, verbose) if need else 0
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    pages = site_pages()
    rows = []
    for g in groups:
        rep = g["rep"]
        tr = cache["q"].get(rep)
        # küme GSC toplamı (aynı niyetin tüm varyantları)
        gv = [gsc[v] for v in g["variants"] if v in gsc]
        gm = None
        if gv:
            impr = sum(x["impr"] for x in gv)
            gm = {"impr": impr, "clicks": sum(x["clicks"] for x in gv),
                  "pos": round(sum(x["pos"] * x["impr"] for x in gv) / max(impr, 1), 1),
                  "page": max(gv, key=lambda x: x["impr"])["page"]}
        page = (gm or {}).get("page") or seasonal.get(rep)
        if not page and rep in SYNONYMS:
            # kanonik sayfa tanımlı: varsa o, yoksa "sitede yok" (kök eşlemesi yanıltıyor: katılım → katılınır)
            page = SYNONYMS[rep] if any(u == SYNONYMS[rep] for u, _ in pages) else None
        elif not page:
            page = match_page(rep, pages)
        f_int, why_int = intent_factor(rep)
        action, reach, note = decide(rep, gm, page, f_int != 1.0)
        vol = 100.0 if rep == ANCHOR else (tr["idx"] if tr else None)
        f_comp = competition_factor(rep, vol)
        if f_comp < 1:
            note += " · dev baş terim: büyük siteler kilitli, uzun-kuyruk varyantlarla gir"
        # Trends yoksa GSC gösterimini kaba hacim vekili say (çapa ~ ayda birkaç bin gösterim varsayımı YOK —
        # bu satırlar ayrı işaretlenir, sıralamada Trends'li satırların altında kalır)
        score = round(vol * f_int * reach * f_comp, 1) if vol is not None else None
        rows.append({
            "q": rep, "varyant": g["variants"][1:6], "kaynak": cands[rep]["src"],
            "hacim": vol, "son4h": tr.get("recent") if tr else None,
            "zirve": tr.get("peak") if tr else None, "zirve_hafta": tr.get("peak_week") if tr else None,
            "vekil": tr.get("vekil") if tr else None,
            "gsc": gm, "sayfa": page, "niyet": why_int, "eylem": action, "not": note, "skor": score,
        })

    scored = sorted([r for r in rows if r["skor"] is not None and r["eylem"] not in ("KORU", "BEKLE")],
                    key=lambda r: -r["skor"])
    top = [r for r in scored if (r["hacim"] or 0) >= 5][:30]
    low = sorted([r for r in rows if r["hacim"] is not None and r["hacim"] < 2], key=lambda r: r["q"])
    data = {
        "_aciklama": (f"hacim = Google Trends TR 12 ay ortalaması, '{ANCHOR}' = 100 (göreli; 0 = Trends eşiğinin "
                      "altı, çok az aranıyor). skor = hacim × niyet × erişilebilirlik (mevcut sıra). "
                      "eylem: CTR/GUCLENDIR/YENIDEN_KUR/OTORITE/YENI_ARAC/YENI_YAZI. OTORITE = başlık zaten "
                      "eşleşiyor, sıra otorite kilidinde → on-page görev üretme."),
        "generated_utc": lib.iso(),
        "anchor": ANCHOR,
        "trends_fetched": n,
        "aday_sayisi": len(rows),
        "firsatlar": top,
        "tum_firsatlar": [r for r in scored if (r["hacim"] or 0) >= 5],   # anahtar kelime haritası (tamamı)
        "koru": sorted([r for r in rows if r["eylem"] == "KORU" and r["hacim"]], key=lambda r: -r["hacim"])[:10],
        "bekle": sorted([{"q": r["q"], "sayfa": r["sayfa"], "hacim": r["hacim"]} for r in rows if r["eylem"] == "BEKLE"],
                        key=lambda r: -(r["hacim"] or 0)),
        "dusuk_talep": [r["q"] for r in low][:60],
        "trends_yok": [r["q"] for r in rows if r["hacim"] is None][:40],
    }
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[firsat] {len(rows)} küme · Trends {n} yeni sorgu · {len(top)} fırsat · {len(low)} düşük talep → {OUT}")
    if verbose:
        for r in top[:20]:
            print(f"  {r['skor']:>7} {r['eylem']:<12} {r['q']} (hacim {r['hacim']}, sayfa {r['sayfa']}, gsc {r['gsc']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
