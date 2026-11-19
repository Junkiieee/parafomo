#!/usr/bin/env python3
"""Huni linkleri: videodan siteye giden adresin TEK kaynağı (2026-11-18 denetimi, video-2).

Neden: #41'in açıklaması, "link" alanı ve sabit yorumu 404 veren parafomo.com/asgari-ucret/ adresini taşıyordu.
LLM linki kendisi yazıyordu; ne üretimde (hikaye_uret.py) ne yayında (youtube-upload, youtube-extras, facebook-reel,
instagram-reel) kontrol ediliyordu. Burada:

  sayfa_yolu(link)            → link sitede açılan bir sayfaya mı gidiyor? kanonik yol ('/x/') | None
                                (worker/index.js REDIRECTS anahtarıysa yönlendirmenin HEDEFİ döner)
  tool_url_for(slug, title)   → konuya en uygun araç sayfası (eski youtube-upload.py eşlemesi; yoksa araç merkezi)
  huni_url(slug, title, link) → (url, tür): geçerli açık link > blog yazısı > konu aracı
  linkleri_duzelt(metin, yedek) → metindeki geçersiz parafomo.com/… adreslerini yedek adresle değiştirir
  gecersiz_linkler(metin)     → metindeki geçersiz parafomo.com/… adresleri (üretim kontrol listesi için)

Yalnız dosya sistemine bakar (src/pages, src/content/blog, public, worker/index.js); ağa çıkmaz.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = "https://parafomo.com"

# Konu → İLGİLİ ARAÇ SAYFASI eşlemesi (huni iyileştirme). Blog olmayan Short'un funnel linki jenerik ana sayfa
# yerine konuya uygun interaktif araca gider. Retention'ı ve hashtag arama bloğunu ETKİLEMEZ.
# Önce özgül konular (ilk eşleşen kazanır). Yollar '/' ile biter: site kanonik URL'i (301 zinciri yok).
_TOOL_MAP = [
    ("kdv", "/kdv-hesaplama/"),
    ("doğum yardım", "/dogum-yardimi/"), ("vergi borcu", "/vergi-borcu-sorgulama/"), ("gecikme zammı", "/vergi-borcu-sorgulama/"),
    ("evde bakım", "/evde-bakim-maasi/"), ("engelli", "/engelli-maasi/"), ("65 yaş", "/engelli-maasi/"),
    ("emekli", "/emekli-zammi-hesaplama/"), ("memur", "/memur-zammi-hesaplama/"),
    ("bayram ikramiye", "/bayram-ikramiyesi/"),
    ("mtv", "/mtv-hesaplama/"), ("motorlu taşıt", "/mtv-hesaplama/"),
    ("emlak vergisi", "/emlak-vergisi-hesaplama/"), ("tapu", "/tapu-harci-hesaplama/"),
    ("yeniden değerleme", "/yeniden-degerleme-orani/"), ("zam oranı", "/yeniden-degerleme-orani/"),
    ("pasaport", "/pasaport-ehliyet-harci/"), ("ehliyet", "/pasaport-ehliyet-harci/"), ("harç", "/pasaport-ehliyet-harci/"),
    ("trafik ceza", "/trafik-cezalari-hesaplama/"), ("muayene", "/arac-muayene-ucreti/"),
    ("damga vergisi", "/damga-vergisi-hesaplama/"), ("noter", "/noter-ucretleri/"),
    ("gelir vergisi", "/gelir-vergisi-hesaplama/"), ("vergi dilim", "/vergi-dilimi-hesaplama/"),
    ("konut kredi", "/konut-kredisi-hesaplama/"), ("ev kredi", "/konut-kredisi-hesaplama/"),
    ("ihtiyaç kredi", "/ihtiyac-kredisi-hesaplama/"), ("taşıt kredi", "/tasit-kredisi-hesaplama/"),
    ("araç kredi", "/tasit-kredisi-hesaplama/"),
    # 2026-11-18 (denetim video-2): kredi kartı konuları '/asgari-ucret-hesaplama/' (#20 "Asgari ödeme tuzağı") ya da
    # araç merkezine (#21 gecikme faizi, #22 nakit avans, #30 ekstre) düşüyordu → 'asgari' ve 'kredi'den ÖNCE.
    ("asgari ödeme", "/kredi-karti-faiz-hesaplama/"), ("asgari odeme", "/kredi-karti-faiz-hesaplama/"),
    ("kredi kart", "/kredi-karti-faiz-hesaplama/"), ("nakit avans", "/kredi-karti-faiz-hesaplama/"),
    ("gecikme faiz", "/kredi-karti-faiz-hesaplama/"), ("akdi faiz", "/kredi-karti-faiz-hesaplama/"),
    ("ekstre", "/kredi-karti-faiz-hesaplama/"),
    ("bilezik", "/altin-fiyatlari/22-ayar-bilezik/"), ("çeyrek", "/altin-fiyatlari/ceyrek-altin/"),
    ("cumhuriyet altın", "/altin-fiyatlari/cumhuriyet-altini/"), ("altın kaç gram", "/altin-kac-gram/"),
    ("altın", "/altin-hesaplama/"), ("altin", "/altin-hesaplama/"), ("gram", "/altin-hesaplama/"),
    ("gümüş", "/gumus-getiri/"), ("gumus", "/gumus-getiri/"),
    ("asgari", "/asgari-ucret-hesaplama/"),
    ("işsizlik", "/issizlik-maasi-hesaplama/"), ("issizlik", "/issizlik-maasi-hesaplama/"),
    ("işsizlik ödeneği", "/issizlik-maasi-hesaplama/"), ("işten çıkar", "/issizlik-maasi-hesaplama/"),
    ("ihbar", "/ihbar-tazminati-hesaplama/"), ("yıllık izin", "/yillik-izin-hesaplama/"),
    ("net maaş", "/net-maas-hesaplama/"), ("net maas", "/net-maas-hesaplama/"),
    ("maaş", "/net-maas-hesaplama/"), ("maas", "/net-maas-hesaplama/"),
    ("kıdem", "/kidem-tazminati-hesaplama/"), ("kidem", "/kidem-tazminati-hesaplama/"),
    ("tazminat", "/kidem-tazminati-hesaplama/"),
    ("kira", "/kira-artis-orani-hesaplama/"),
    ("kredi", "/kredi-hesaplama/"), ("taksit", "/kredi-hesaplama/"),
    ("bileşik", "/bilesik-faiz-hesaplama/"), ("bilesik", "/bilesik-faiz-hesaplama/"),
    ("mevduat", "/mevduat-faizi-hesaplama/"),
    ("enflasyon", "/enflasyon-hesaplama/"), ("tüfe", "/enflasyon-hesaplama/"), ("tufe", "/enflasyon-hesaplama/"),
    ("eriyor", "/enflasyon-hesaplama/"), ("alım gücü", "/enflasyon-hesaplama/"),
    ("tcmb", "/tcmb-faiz-takvimi/"),
    ("fed", "/fed-faiz-takvimi/"), ("fomc", "/fed-faiz-takvimi/"),
    ("halka arz", "/halka-arz/"), ("ipo", "/halka-arz/"),
    ("dolar", "/dolar-getiri/"), ("euro", "/euro-getiri/"), ("bitcoin", "/bitcoin-getiri/"),
    ("borsa", "/bist-getiri/"), ("bist", "/bist-getiri/"),
]
HUB = "/hesaplama-araclari/"

_RED_CACHE = {}


def _redirects(root=ROOT):
    """worker/index.js REDIRECTS sözlüğü {'/eski/': '/yeni/' | 'https://…'} (dosya okunamazsa boş)."""
    if root in _RED_CACHE:
        return _RED_CACHE[root]
    out = {}
    try:
        src = open(os.path.join(root, "worker", "index.js"), encoding="utf-8").read()
        m = re.search(r"const\s+REDIRECTS\s*=\s*\{(.*?)\n\};", src, re.S)
        if m:
            for k, v in re.findall(r"'(/[^']*)'\s*:\s*'([^']+)'", m.group(1)):
                out[k] = v
    except OSError:
        pass
    _RED_CACHE[root] = out
    return out


def _blog_var(root, slug):
    """Yazı repoda var ve taslak değil mi (draft: true yazılar build'e girmez → 404)."""
    for ext in (".md", ".mdx"):
        p = os.path.join(root, "src", "content", "blog", slug + ext)
        if os.path.isfile(p):
            try:
                head = open(p, encoding="utf-8").read(4000)
            except OSError:
                return True
            fm = re.match(r"^---\s*\n(.*?)\n---", head, re.S)
            return not (fm and re.search(r"^draft:\s*true\s*$", fm.group(1), re.M))
    return False


def _yol_ayikla(link):
    """'https://www.parafomo.com/x?utm' | 'parafomo.com/x' | '/x' | 'x/' → '/x/' ; başka alan adı → None."""
    s = (link or "").strip()
    if not s:
        return None
    m = re.match(r"^(?:https?://)?(?:www\.)?parafomo\.com(?=[/?#]|$)", s, re.I)
    if m:
        s = s[m.end():]
    elif re.match(r"^[a-z][a-z0-9+.-]*://", s, re.I) or re.match(r"^[\w-]+(\.[\w-]+)+(/|$)", s):
        return None   # başka alan adı (app.parafomo.com dahil) huni sayfası değil
    s = re.split(r"[?#]", s, maxsplit=1)[0]
    if not s.startswith("/"):
        s = "/" + s
    son = s.rsplit("/", 1)[-1]
    if not s.endswith("/") and "." not in son:
        s += "/"   # worker da sonda '/' olmayanı 301 ile '/'li adrese götürür
    return re.sub(r"/{2,}", "/", s)


def sayfa_yolu(link, root=ROOT, _derin=0):
    """Link sitede açılan bir sayfaya gidiyorsa kanonik yolu ('/x/'), yönlendirmeyse hedefini, yoksa None."""
    yol = _yol_ayikla(link)
    if not yol:
        return None
    if yol == "/":
        return "/"
    hedef = _redirects(root).get(yol)
    if hedef:
        if hedef.startswith("http"):
            return hedef
        return sayfa_yolu(hedef, root, _derin + 1) if _derin < 3 else None
    parca = [p for p in yol.strip("/").split("/") if p]
    pages = os.path.join(root, "src", "pages")
    if "." in parca[-1]:   # statik dosya (public/) ya da üretilen dosya (pages/robots.txt.ts)
        ok = os.path.isfile(os.path.join(root, "public", *parca)) or \
            os.path.isfile(os.path.join(pages, *parca[:-1], parca[-1] + ".ts"))
        return yol if ok else None
    if parca[0] == "blog":
        if len(parca) == 1 or (len(parca) == 2 and _blog_var(root, parca[1])):
            return yol
        return None
    if os.path.isfile(os.path.join(pages, *parca[:-1], parca[-1] + ".astro")) or \
            os.path.isfile(os.path.join(pages, *parca, "index.astro")):
        return yol
    d = os.path.join(pages, *parca[:-1])
    if len(parca) > 1 and os.path.isdir(d) and any(f.startswith("[") and f.endswith(".astro") for f in os.listdir(d)):
        return yol   # dinamik rota (altin-fiyatlari/[tur], halka-arz/[slug]); parametre build'de belli olur
    return None


def tam_url(yol):
    return yol if yol.startswith("http") else SITE + yol


def _samanlik(slug, title=""):
    # slug tireleri boşluk: çok kelimeli anahtarlar ("kredi kart", "asgari odeme") slug'da da eşleşsin
    return f"{(slug or '').replace('-', ' ')} {title or ''}".replace("İ", "i").replace("I", "ı").lower()


def tool_url_for(slug, title="", root=ROOT):
    """Blog olmayan Short için konuya en uygun araç sayfası URL'i (yoksa araç merkezi).
    Sayfa henüz yoksa (yeni araç geliştiriliyor) o eşleşme atlanır → açıklamada 404 link olmaz."""
    hay = _samanlik(slug, title)
    for kw, path in _TOOL_MAP:
        if kw in hay and sayfa_yolu(path, root):
            return SITE + path
    return SITE + HUB


def blog_url(slug, root=ROOT):
    return f"{SITE}/blog/{slug}/" if slug and _blog_var(root, slug) else ""


def huni_url(slug, title="", link="", root=ROOT):
    """(url, tür) — tür: 'link' (senaryonun geçerli açık hedefi) | 'blog' | 'arac'. Geçersiz link sessizce düşer."""
    if link:
        y = sayfa_yolu(link, root)
        if y:
            return tam_url(y), ("blog" if "/blog/" in y else "link")
    b = blog_url(slug, root)
    if b:
        return b, "blog"
    return tool_url_for(slug, title, root), "arac"


# parafomo.com adresi: önünde harf/nokta/@ yok (app.parafomo.com, ajan@parafomo.com eşleşmez)
_LINK_RE = re.compile(r"(?<![\w.@/-])(?:https?://)?(?:www\.)?parafomo\.com(/[^\s<>\"'()\[\]{}]*)?", re.I)
_SON_NOKTALAMA = ".,;:!?…»”’"


def _eslesmeler(metin):
    for m in _LINK_RE.finditer(metin or ""):
        tam = m.group(0)
        kuyruk = ""
        while tam and tam[-1] in _SON_NOKTALAMA:   # cümle sonu noktalaması linke dahil değil
            kuyruk = tam[-1] + kuyruk
            tam = tam[:-1]
        yield m.start(), m.start() + len(tam), tam, kuyruk


def gecersiz_linkler(metin, root=ROOT):
    """Metindeki sitede açılmayan parafomo.com/… adresleri (sırayla, tekrarsız)."""
    out = []
    for _, _, tam, _ in _eslesmeler(metin):
        if sayfa_yolu(tam, root) is None and tam not in out:
            out.append(tam)
    return out


def linkleri_duzelt(metin, yedek_url, root=ROOT):
    """Metindeki geçersiz parafomo.com/… adreslerini yedek_url ile değiştir → (yeni metin, değişen adresler).
    Yazım biçimi korunur: 'https://…' tam URL olarak, 'parafomo.com/…' şemasız yazılır. Geçerli adreslere dokunmaz."""
    if not metin:
        return metin, []
    yedek = (yedek_url or SITE + "/").split("?")[0]
    sema_siz = re.sub(r"^https?://", "", yedek)
    parcalar, degisen, i = [], [], 0
    for bas, son, tam, _ in _eslesmeler(metin):
        if sayfa_yolu(tam, root) is not None:
            continue
        parcalar.append(metin[i:bas])
        parcalar.append(yedek if tam.lower().startswith("http") else sema_siz)
        degisen.append(tam)
        i = son
    if not degisen:
        return metin, []
    parcalar.append(metin[i:])
    return "".join(parcalar), degisen


if __name__ == "__main__":   # hızlı kontrol: python3 scripts/lib/funnel.py /asgari-ucret/ parafomo.com/zam …
    import sys
    for a in sys.argv[1:]:
        print(f"{a} → {sayfa_yolu(a)}")
