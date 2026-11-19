#!/usr/bin/env python3
"""
ParaFOMO — Instagram Reels yayıncısı (Shorts mp4'ünü Reel olarak paylaşır).

IG feed görselleri 57 gönderiye 3 takipçi getirdi → Reels'e pivot. Aynı Shorts
videosunu Reel olarak yayınlar (organik erişim feed'den kat kat yüksek).

Video barındırma (TOKEN GEREKTİRMEZ): repo public olduğu için mp4, ayrı bir
`media` dalına git plumbing ile force-push edilir → raw.githubusercontent üzerinden
anında herkese açık URL. IG oradan çeker. Her yayında dal tek dosyaya sıfırlanır
(eski Reel zaten IG'ye alınmıştır → geçmiş şişmez). Commit GEÇİCİ bir bare repoda
kurulur ve remote URL'ine itilir (denetim repo-2, 2026-11-18): eskiden blob ana
repoya yazılıyor, refs/remotes/origin/media reflog'u her mp4'ü 90 gün tutuyordu.

Korumalar (denetim sosyal-1/2/4, 2026-11-18): meta'da ig_reel_id varsa yeniden
paylaşmaz (--force); günlük sınır okunamazsa yayınlamaz (çıkış 4); barındırma
başarısızsa çıkış 3; link sitede açılmıyorsa kullanılmaz (scripts/lib/funnel.py);
etiketler kelime başında eşleşir ("altındaysan" altın etiketi getirmez).

Akış: mp4 barındır → Reels container oluştur (media_type=REELS) → status FINISHED
olana kadar bekle → media_publish → reel_id + permalink meta json'a yazılır.

Kullanım: python3 scripts/instagram-reel.py <slug> [--no-publish] [--caption-file F] [--force] [--dry]
  --dry: ağa ve git'e dokunmadan caption'ı yazdırır.
Kimlik: ~/.config/parafomo/instagram.env (IG_BUSINESS_ACCOUNT_ID, IG_PAGE_TOKEN)
"""
import os
import re
import sys
import json
import time
import argparse
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "lib"))
import funnel  # noqa: E402
from meta_graph import API  # noqa: E402  (sürüm tek yerde: scripts/lib/meta_graph.py)
OUT_DIR = os.path.join(ROOT, "public", "social")
BLOG_DIR = os.path.join(ROOT, "src", "content", "blog")
IG_ENV = os.path.expanduser("~/.config/parafomo/instagram.env")
REPO_RAW = "https://raw.githubusercontent.com/Junkiieee/parafomo/media"
MEDIA_REMOTE = os.environ.get("PARAFOMO_MEDIA_REMOTE", "")   # boşsa origin'in URL'i (test: yerel bare repo yolu)

# Türkçe finans erişim etiketleri. Her gönderiye AYNI blok yerine KONUYA-DUYARLI
# set: küçük hesap dev hashtag havuzunda sıralanamaz → videonun kendi niş
# havuzunu hedefle. Ayrıca aynı bloğun tekrarı IG'de otomasyon/spam sinyali.
CORE_TAGS = ["#parafomo", "#finans", "#para", "#yatırım", "#borsa", "#ekonomi"]
DISCOVERY_TAGS = ["#paratüyoları", "#ekonomihaber", "#finansalözgürlük"]
TOPIC_TAGS = {
    "altın": ["#altın", "#gramaltın", "#altınyatırımı", "#çeyrekaltın"],
    "dolar": ["#dolar", "#dolartl", "#döviz", "#kur"],
    "euro": ["#euro", "#döviz", "#eurotl"],
    "bitcoin": ["#bitcoin", "#kripto", "#kriptopara", "#btc"],
    "kripto": ["#kripto", "#kriptopara", "#bitcoin"],
    "ethereum": ["#ethereum", "#kripto", "#altcoin"],
    "stablecoin": ["#stablecoin", "#kripto", "#usdt"],
    "nft": ["#nft", "#kripto", "#dijitalvarlık"],
    "fed": ["#fed", "#faiz", "#dolar", "#abdekonomisi"],
    "faiz": ["#faiz", "#merkezbankası", "#mevduat"],
    "tcmb": ["#tcmb", "#faiz", "#merkezbankası"],
    "merkez banka": ["#merkezbankası", "#faiz", "#parapolitikası"],
    "enflasyon": ["#enflasyon", "#tüfe", "#zam"],
    "tüfe": ["#enflasyon", "#tüfe", "#alımgücü"],
    "tüik": ["#enflasyon", "#tüik", "#tüfe"],
    "bist": ["#bist100", "#borsaistanbul", "#hisse"],
    "borsa": ["#borsa", "#bist100", "#hissesenedi"],
    "hisse": ["#hisse", "#hissesenedi", "#borsa"],
    "temettü": ["#temettü", "#temettühisseleri", "#pasifgelir"],
    "etf": ["#etf", "#endeksfonu", "#pasifyatırım"],
    "endeks fon": ["#endeksfonu", "#etf", "#pasifyatırım"],
    "fon": ["#yatırımfonu", "#tefas", "#fon"],
    "eurobond": ["#eurobond", "#dolarfaizi", "#sabitgetiri"],
    "tahvil": ["#tahvil", "#hazinebonosu", "#sabitgetiri"],
    "repo": ["#repo", "#kısavade", "#faiz"],
    "mevduat": ["#mevduat", "#vadelimevduat", "#tasarruf"],
    "tasarruf": ["#tasarruf", "#parabiriktirme", "#bütçe"],
    "bütçe": ["#bütçe", "#parayönetimi", "#tasarruf"],
    "emeklilik": ["#emeklilik", "#bes", "#uzunvade"],
    "bes": ["#bes", "#bireyselemeklilik", "#emeklilik"],
    "kredi": ["#kredi", "#borç", "#kredikartı"],
    "borç": ["#borç", "#borçtankurtulma", "#kredikartı"],
    "nfp": ["#nfp", "#abdekonomisi", "#ekonomiveri"],
    "issizlik": ["#işsizlik", "#abdekonomisi", "#nfp"],
    "portföy": ["#portföy", "#varlıkdağılımı", "#yatırımstratejisi"],
    "pasif gelir": ["#pasifgelir", "#finansalözgürlük"],
    "finansal özgür": ["#finansalözgürlük", "#fire", "#pasifgelir"],
    "bileşik faiz": ["#bileşikfaiz", "#uzunvadeyatırım"],
    "halka arz": ["#halkaarz", "#ipo", "#borsa"],
    "döviz": ["#döviz", "#dolar", "#kur"],
    "konut": ["#konut", "#gayrimenkul", "#emlak"],
    # 2026-11-18 (denetim sosyal-4): 2027 zam sezonu içeriği (emekli, asgari ücret, kira, vergi…) jenerik bloğa düşüyordu.
    "emekli": ["#emeklimaaşı", "#emeklizammı", "#ssk", "#bağkur"],
    "refah": ["#refahpayı", "#emeklizammı"],
    "memur": ["#memurmaaşı", "#memurzammı"],
    "asgari": ["#asgariücret", "#asgariücret2027"],
    "maaş": ["#maaş", "#netmaaş"],
    "maas": ["#maaş", "#netmaaş"],
    "kira": ["#kiraartışı", "#kiracı"],
    "vergi": ["#vergi", "#gelirvergisi"],
    "zam": ["#zam", "#2027zam"],
    "zamm": ["#zam", "#2027zam"],          # zammı, zammına (kısa 'zam' anahtarı 'zaman'a takılmasın diye ayrı)
    "kara cuma": ["#karacuma", "#indirim"],
}


def _kucuk(s):
    """Türkçe küçük harf (İ→i, I→ı) + tire boşluk (slug'daki kelimeler ayrı sayılsın)."""
    return (s or "").replace("İ", "i").replace("I", "ı").lower().replace("-", " ")


_KISA_EK = r"(?:'?(?:[ıiuü]n?|[ae]|[dt][ae]n?|l[ae]r\w{0,3}))?"   # fonu, fonlar, etfler, zamlar (zaman DEĞİL)


def kw_konum(kw, metin, ek=True):
    """Anahtar metinde KELİME BAŞINDA geçiyorsa konumu, yoksa None. ek=True: Türkçe ek serbest (4+ harfli anahtarda en
    çok 4 harf: altını, kiracı, vergisiz; kısa anahtarda yalnız yaygın ekler); ek=False: yalnız tam kelime.
    Eskiden düz alt dizeydi: açıklamadaki 'altındaysan' emekli Reel'ine altın etiketleri getirdi (2026-11-18)."""
    son = (r"\w{0,4}" if len(kw) >= 4 else _KISA_EK) if ek else ""
    m = re.search(rf"(?<!\w){re.escape(kw)}{son}(?!\w)", metin)
    return m.start() if m else None


def kw_eslesir(kw, metin, ek=True):
    return kw_konum(kw, metin, ek) is not None


def build_hashtags(slug="", title="", desc=""):
    """2026 IG: 3-5 HİPER-İLGİLİ etiket > uzun jenerik liste. Mosseri: hashtag
    erişimi ARTIRMAZ (arama/bağlam içindir) ve 5'ten fazlası 'düşük-niyet' sinyali
    verip erişimi baskılayabilir. Bu yüzden niş-önce, en fazla 4 konu etiketi + #parafomo (marka hep sonda).
    Konu sırası: slug/başlıkta ÖNCE geçen konu önde ("Asgari ücret kaç gram altın" → asgari, sonra altın); her konudan
    önce 2 etiket alınır ki tek konu dört yeri de kaplamasın. Açıklama yalnız tam kelimeyle ve en sonda sayılır."""
    prim = _kucuk(f"{slug} {title}")   # asıl konu (slug/başlık)
    sec = _kucuk(desc)                  # tali (açıklamada geçenler)
    eslesen = []
    for i, kw in enumerate(TOPIC_TAGS):
        k = kw_konum(kw, prim, True)
        if k is not None:
            eslesen.append((0, k, i, kw))
            continue
        k = kw_konum(kw, sec, False)
        if k is not None:
            eslesen.append((1, k, i, kw))
    eslesen.sort()
    tags = []
    for dilim in (slice(0, 2), slice(2, None)):
        for *_, kw in eslesen:
            for t in TOPIC_TAGS[kw][dilim]:
                if t not in tags and t != "#parafomo":
                    tags.append(t)
    tags = tags[:4]
    for t in CORE_TAGS:                         # niş azsa 4'e kadar core ile doldur
        if len(tags) >= 4:
            break
        if t not in tags and t != "#parafomo":
            tags.append(t)
    return " ".join(tags + ["#parafomo"])      # marka etiketi her zaman (eskiden 5'e kırpılınca düşüyordu)


def load_env():
    env = {}
    for ln in open(IG_ENV, encoding="utf-8"):
        ln = ln.strip()
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def _git_env():
    """Geçici bare repoda commit-tree için kimlik: ana reponun user.name/email'i (genel git kimliği yok)."""
    env = dict(os.environ)
    for k, anahtar, yedek in (("NAME", "user.name", "parafomo-media"), ("EMAIL", "user.email", "media@parafomo.com")):
        try:
            v = subprocess.run(["git", "-C", ROOT, "config", anahtar], capture_output=True, text=True, timeout=10).stdout.strip()
        except Exception:
            v = ""
        env[f"GIT_AUTHOR_{k}"] = env[f"GIT_COMMITTER_{k}"] = v or yedek
    return env


def media_push(mp4, name):
    """mp4'ü tek dosyalık commit olarak `media` dalına force-push et. Başarı → True; hata → mesaj basar, False.
    Commit geçici bir bare repoda kurulur: ana reponun nesne deposuna ve origin/media reflog'una mp4 girmez."""
    tmp = None
    try:
        remote = MEDIA_REMOTE or subprocess.run(["git", "-C", ROOT, "remote", "get-url", "origin"], capture_output=True,
                                                text=True, check=True, timeout=30).stdout.strip()
        tmp = tempfile.mkdtemp(prefix="parafomo-media-")
        subprocess.run(["git", "init", "--bare", "-q", tmp], capture_output=True, check=True, timeout=60)
        env = _git_env()

        def g(*args, inp=None, timeout=120):
            return subprocess.run(["git", "--git-dir", tmp, *args], input=inp, env=env, capture_output=True,
                                  check=True, timeout=timeout).stdout.decode().strip()
        blob = g("hash-object", "-w", mp4)
        tree = g("mktree", inp=f"100644 blob {blob}\t{name}\n".encode())
        commit = g("commit-tree", tree, "-m", f"media: {name}")
        g("push", "-f", "-q", remote, f"{commit}:refs/heads/media", timeout=300)
        return True
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        print(f"HATA: barındırma git adımı başarısız ({' '.join(str(c) for c in e.cmd[3:5])}): {err.strip()[-400:]}")
    except subprocess.TimeoutExpired as e:
        print(f"HATA: barındırma zaman aşımı ({e.timeout} sn): {' '.join(str(c) for c in e.cmd[3:5])}")
    except OSError as e:
        print(f"HATA: barındırma başarısız: {type(e).__name__}: {e}")
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    return False


def host_video(mp4, name):
    """mp4'ü `media` dalına force-push et → raw URL. Token gerektirmez (SSH push). Başarısızsa None."""
    if not media_push(mp4, name):
        return None
    url = f"{REPO_RAW}/{urllib.parse.quote(name)}"
    # raw'ın yayılmasını bekle (kısa)
    for _ in range(10):
        try:
            req = urllib.request.Request(url, method="HEAD")
            if urllib.request.urlopen(req, timeout=15).status == 200:
                return url
        except Exception:
            pass
        time.sleep(2)
    return url  # yine de dene


def site_link(slug):
    if os.path.exists(os.path.join(BLOG_DIR, f"{slug}.md")):
        return f"parafomo.com/blog/{slug}/"
    return "parafomo.com"


def meta_link(meta):
    link = (meta.get("link") or "").strip()
    if not link:
        return ""
    if funnel.sayfa_yolu(link, ROOT) is None:   # 2026-11-18: #41 '/asgari-ucret/' 404 → caption'a girmesin
        print(f"[i] link sitede açılmıyor, caption'da kullanılmadı: {link}")
        return ""
    return link.replace("https://", "") if link.startswith("http") else "parafomo.com/" + link.lstrip("/")


def _clean(text):
    """YouTube artığını temizle: #Shorts, hashtag satırları, URL/'Daha fazlası' satırları."""
    out = []
    for ln in (text or "").splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.lower().startswith("#") or "http" in s.lower():
            continue
        if s.lower().startswith(("daha fazlası", "detaylar", "detaylı")):
            continue
        out.append(s)
    return " ".join(out).strip()


# Formata göre YORUM tetikleyen soru — jenerik "ne düşünüyorsun" yerine konuya
# özgü soru çok daha fazla yorum çeker (erişim sinyali). IG önizlemede ilk 1-2
# satır görünür; bu yüzden soru artık EN ÜSTE, görünür bölgeye taşındı.
FORMAT_Q = {
    "backtest_return": "Sen bu parayı nereye koyardın — altın mı, dolar mı, borsa mı?",
    "comparison": "Sence uzun vadede hangisi kazandırır?",
    "myth": "Sen de böyle mi biliyordun?",
    "news_reaction": "Sence piyasa buna nasıl tepki verir?",
    "single_concept": "Bunu daha önce biliyor muydun?",
    "shock_number": "Bu rakam seni şaşırttı mı?",
    "ekonomi_defteri": "Defterin sonraki sayfasında hangi konuyu görelim?",
}

# Blog Reels'inde viral "format" alanı yok → hepsi jenerik soruya düşüyordu
# (kapalı-döngü dersi: jenerik soru zayıf). slug/başlık anahtarına göre KONUYA
# ÖZGÜ soru = daha çok yorum (08-07-3 pattern'ini en yüksek-hacimli Reel'e taşır).
# Sıra önemli: ilk eşleşen kazanır, spesifikten genele.
TOPIC_Q = [
    ("altın",      "Portföyünde altın var mı, yüzde kaç?"),
    ("dolar",      "Sen dolar mı tutuyorsun, TL mi?"),
    ("euro",       "Euro mu dolar mı — hangisi cebine göre?"),
    ("bist",       "BIST'te misin, yoksa uzak mı duruyorsun?"),
    ("borsa",      "Borsaya para koyar mıydın, neden?"),
    ("hisse",      "Portföyünde kaç farklı hisse var?"),
    ("etf",        "ETF mi tek hisse mi — sen ne tercih edersin?"),
    ("fon",        "Sen fon mu alırsın, direkt mi?"),
    ("faiz",       "Faiz kararı senin bütçeni nasıl etkiliyor?"),
    ("enflasyon",  "Enflasyona karşı paranı nasıl koruyorsun?"),
    ("mevduat",    "Paran mevduatta mı duruyor?"),
    ("emeklilik",  "Emeklilik için bir kenara para koyuyor musun?"),
    ("bes",        "BES'in var mı — sence mantıklı mı?"),
    ("kripto",     "Kripton var mı, yoksa uzak mı duruyorsun?"),
    ("bitcoin",    "Bitcoin: balon mu, gelecek mi?"),
    ("tasarruf",   "Ayda gelirinin yüzde kaçını biriktiriyorsun?"),
    ("butce",      "Sen bütçe tutuyor musun?"),
    ("bütçe",      "Sen bütçe tutuyor musun?"),
    ("kredi",      "Kredi kartı borcu senin için sorun mu?"),
    ("eurobond",   "Dolar bazlı yatırım yapıyor musun?"),
    ("temettü",    "Temettü hisselerin var mı?"),
    ("gayrimenkul","Ev mi hisse mi — sence hangisi kazandırır?"),
    ("konut",      "Ev mi hisse mi — sence hangisi kazandırır?"),
]


def topic_question(slug="", title=""):
    hay = f"{slug} {title}".lower()
    for key, q in TOPIC_Q:
        if key in hay:
            return q
    return "Sen ne düşünüyorsun? 👇"


def build_caption(meta, slug):
    title = re.sub(r"#\w+\s*$", "", meta.get("title", "")).strip()  # sondaki #Shorts vs
    hedef = meta_link(meta) or site_link(slug)
    desc, degisen = funnel.linkleri_duzelt(_clean(meta.get("description", "")), "https://" + hedef, ROOT)
    if degisen:
        print(f"[i] açıklamadaki geçersiz adres düzeltildi: {', '.join(degisen)} → {hedef}")
    hook = title or desc[:80]
    body = desc if desc and desc != title else ""
    q = FORMAT_Q.get((meta.get("format") or "").strip()) or topic_question(slug, title)
    # Erişim sinyali: yorum + kaydetme, beğeniden daha güçlü sıralama sinyalidir.
    # Soruyu görünür ilk bloğa al (yorum), kaydet/takip/link altta.
    # 2026-11-17: Instagram açık "kaydet/paylaş/etiketle/takip et" çağrılarını etkileşim tuzağı sayıp takipçi dışı
    # erişimi düşürebiliyor (creators.instagram.com, Meta engagement-bait); açık uçlu soru serbest → yalnız soru + bilgi.
    cta = f"📲 Tam rehber (ücretsiz): {hedef}"
    body_block = f"{body}\n\n" if body else ""
    cap = f"{hook}\n\n💬 {q}\n\n{body_block}{cta}\n\n{build_hashtags(slug, title, desc)}"
    return cap[:2100]  # IG caption sınırı 2200


def graph_post(path, data):
    body = urllib.parse.urlencode(data).encode()
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(
            f"{API}/{path}", data=body), timeout=60))
    except urllib.error.HTTPError as e:
        return {"__error__": e.read().decode()[:400]}


def graph_get(path, params):
    url = f"{API}/{path}?" + urllib.parse.urlencode(params)
    try:
        return json.load(urllib.request.urlopen(url, timeout=30))
    except urllib.error.HTTPError as e:
        return {"__error__": e.read().decode()[:400]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--no-publish", action="store_true", help="container oluştur ama yayınlama")
    ap.add_argument("--caption-file", default="")
    ap.add_argument("--force", action="store_true", help="meta'da ig_reel_id olsa da yeniden paylaş")
    ap.add_argument("--dry", action="store_true", help="ağa/git'e dokunmadan caption'ı yazdır")
    args = ap.parse_args()

    if args.dry:
        mp = os.path.join(OUT_DIR, f"short-{args.slug}.json")
        if not os.path.exists(mp):
            print(f"HATA: meta yok: {mp}"); return 1
        m = json.load(open(mp, encoding="utf-8"))
        print(f"[dry] ig_reel_id: {m.get('ig_reel_id') or '-'}\n[dry] caption:\n{build_caption(m, args.slug)}")
        return 0
    env = load_env()
    ig = env.get("IG_BUSINESS_ACCOUNT_ID")
    tok = env.get("IG_PAGE_TOKEN")
    if not (ig and tok):
        print("HATA: IG kimliği eksik (instagram.env)"); return 1

    meta_path = os.path.join(OUT_DIR, f"short-{args.slug}.json")
    if not os.path.exists(meta_path):
        print(f"HATA: meta yok: {meta_path}"); return 1
    meta = json.load(open(meta_path, encoding="utf-8"))
    # ÇİFT PAYLAŞIM KORUMASI (denetim sosyal-2): kuyruk yeniden denerse ya da elle tekrar çalıştırılırsa aynı Reel
    # ikinci kez çıkmasın (günlük 1 Reel sınırını da yer).
    if meta.get("ig_reel_id") and not args.force:
        print(f"[i] zaten IG'de: {meta.get('ig_reel_permalink') or meta['ig_reel_id']} — yeniden paylaşmak için --force")
        return 0
    mp4 = meta.get("file") or os.path.join(OUT_DIR, f"short-{args.slug}.mp4")
    if not os.path.exists(mp4):
        print(f"HATA: mp4 yok: {mp4}"); return 1

    if args.caption_file and os.path.exists(args.caption_file):
        caption = open(args.caption_file, encoding="utf-8").read().strip()
    else:
        caption = build_caption(meta, args.slug)

    # Günlük üst sınır (2026-10-30, video-yon.md V3): IG'de günde 5-7 gönderi erişimi 0-3'e düşürüyordu → TR günü
    # içinde en çok IG_REELS_PER_DAY Reel. Fazlası yalnız YouTube/FB'de kalır (çıkış 0: hattı bozmaz).
    # 2026-11-17: 2 → 1. Araştırma: son 27 Reel'in toplam erişimi 40, her biri ilk 3 sn testinde eleniyor;
    # az ama güçlü test (19:00 Para hikâyesi IG'ye, 21:00 videosu yalnız YouTube/FB).
    cap = int(env.get("IG_REELS_PER_DAY") or os.environ.get("IG_REELS_PER_DAY") or 1)
    lst = graph_get(f"{ig}/media", {"fields": "timestamp,media_product_type", "limit": "15", "access_token": tok})
    if "__error__" in lst and not args.no_publish:   # sınır okunamadı → güvenli taraf: yayınlama (eskiden 0 sayıp paylaşırdı)
        print(f"HATA: günlük Reel sayısı okunamadı, sınır aşılmasın diye yayınlanmadı: {lst['__error__'][:300]}")
        return 4
    import datetime as _dt
    tr_today = (_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(hours=3)).date()
    def _tr_day(ts):
        return (_dt.datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S") + _dt.timedelta(hours=3)).date()
    today_n = sum(1 for m in lst.get("data", []) if m.get("media_product_type") == "REELS" and _tr_day(m["timestamp"]) == tr_today)
    if today_n >= cap and not args.no_publish:
        print(f"[i] IG günlük Reel sınırı dolu ({today_n}/{cap}) — bu video yalnız YouTube/FB'de. Atlandı.")
        return 0

    print(f"[*] Video barındırılıyor (media dalı)...")
    video_url = host_video(mp4, f"{args.slug}.mp4")
    if not video_url:
        print("HATA: video barındırılamadı (media dalı) — Reel paylaşılmadı"); return 3
    print(f"[+] URL: {video_url}")

    print(f"[*] Reels container oluşturuluyor...")
    # Kapak karesi: varsayılan İLK kare, v4 açılış punch-in zoom'unun ortasına denk
    # gelip kanca metnini yarım/bulanık gösteriyor. Profil ızgarası kapağı IG'de
    # profil→takip ve Reels-sekmesi tıklamasının en güçlü sürücüsü. thumb_offset ile
    # kanca metninin TAM oturduğu ~1.3sn'lik kareyi kapak seç (punch-in'den sonra).
    cont = graph_post(f"{ig}/media", {
        "media_type": "REELS", "video_url": video_url, "thumb_offset": "1300",
        "caption": caption, "share_to_feed": "true", "access_token": tok})
    if "__error__" in cont or "id" not in cont:
        print(f"HATA: container oluşmadı: {cont.get('__error__', cont)}"); return 2
    cid = cont["id"]
    print(f"[+] container: {cid}")

    # işlenmeyi bekle (video transcode) — FINISHED olana dek
    print("[*] Video işleniyor (bekleniyor)...")
    status = None
    for i in range(40):  # ~5 dk
        st = graph_get(cid, {"fields": "status_code", "access_token": tok})
        status = st.get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            print(f"HATA: IG işleme hatası: {st}"); return 2
        time.sleep(8)
    if status != "FINISHED":
        print(f"HATA: işleme zaman aşımı (son durum: {status})"); return 2
    print("[+] İşleme tamam.")

    if args.no_publish:
        print("[i] --no-publish → yayınlanmadı."); return 0

    pub = graph_post(f"{ig}/media_publish", {"creation_id": cid, "access_token": tok})
    if "__error__" in pub or "id" not in pub:
        print(f"HATA: yayınlanamadı: {pub.get('__error__', pub)}"); return 2
    reel_id = pub["id"]
    perma = graph_get(reel_id, {"fields": "permalink", "access_token": tok}).get("permalink", "")
    print(f"[+] REEL YAYINLANDI: {perma or reel_id}")
    meta["ig_reel_id"] = reel_id
    meta["ig_reel_permalink"] = perma

    # Erken YORUM tohumu (2026-08-13): yeni yayınlanan Reel'e bir engagement sorusu düş.
    # Erken yorumlar beğeniden güçlü bir erişim sinyali; hesabın kendi ilk yorumu sohbeti
    # başlatır + izleyiciye yanıt hedefi verir. Caption'a DOKUNMAZ (açık deneyleri confound
    # etmez — ayrı yüzey) ve link EKLEMEZ (caption'da zaten var; aşırı-link spam sinyalinden
    # kaçın). Başarısızsa yalnızca log — yayın akışı asla kırılmaz.
    seeds = [
        "Sen hangisini yapıyorsun? 👇 Merak ettim, yorumda yazar mısın?",
        "Bunu daha önce biliyor muydun? 👇 Dürüst ol 😄",
        "Katılıyor musun, katılmıyor musun? 👇 Sebebini de yaz.",
    ]
    seed = seeds[sum(ord(c) for c in args.slug) % len(seeds)]
    # 2026-11-17: KAPALI (IG_SEED_COMMENT=1 ile açılır). 31 Reel'de tek yorum bizim tohumdu; Meta tekrar eden
    # kopyala-yapıştır yorumların dağıtımını düşürüyor (transparency.meta.com, lowering distribution).
    if (env.get("IG_SEED_COMMENT") or os.environ.get("IG_SEED_COMMENT")) != "1":
        seed = None
    try:
        if seed is None:
            raise RuntimeError("tohum yorum kapalı")
        cm = graph_post(f"{reel_id}/comments", {"message": seed, "access_token": tok})
        if "id" in cm:
            print(f"[+] İlk yorum tohumu eklendi: {cm['id']}")
            meta["ig_seed_comment_id"] = cm["id"]
        else:
            print(f"[i] İlk yorum atlandı: {cm.get('__error__', cm)}")
    except Exception as e:
        print(f"[i] İlk yorum atlandı (istisna): {str(e)[:80]}")

    # taze oku + yalnız kendi alanlarımızı yaz (yükleme sürerken başka betiğin yazdığı alanlar ezilmesin)
    cur = json.load(open(meta_path, encoding="utf-8"))
    cur.update({k: meta[k] for k in ("ig_reel_id", "ig_reel_permalink", "ig_seed_comment_id") if k in meta})
    json.dump(cur, open(meta_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    # YAYIN DURDURMA BAYRAĞI (Kaan 2026-10-30): dosya varsa hiçbir şey yayınlanmaz (--dry serbest)
    import os as _os, sys as _sys
    if _os.path.exists("/root/parafomo-data/PUBLISH_PAUSED") and "--dry" not in _sys.argv and _os.environ.get("ONAYLI_YAYIN") != "1":
        print("[durduruldu] /root/parafomo-data/PUBLISH_PAUSED var — yayın yapılmadı."); _sys.exit(0)
    sys.exit(main())
