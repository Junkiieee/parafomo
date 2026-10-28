#!/usr/bin/env python3
"""
ParaFOMO — Viral Shorts senaryo üreticisi (6 format, blog'dan bağımsız).

Bir FORMAT + opsiyonel KONU alır, `claude -p` ile viral odaklı bir senaryo
üretir ve shorts-build.py'nin --scenario modunun beklediği JSON'u yazar:
  public/social/scenarios/<slug>.json
Her beat, görsel motoruna ({type, query}) bir görsel isteği taşır → senaryo
ile ekrandaki görsel ÖRTÜŞÜR (Trump → gerçek Trump fotoğrafı, altın → külçe).

Formatlar (havuz):
  comparison       Karşılaştırma yarışı (altın/dolar/borsa/mevduat kim kazandırdı)
  myth             Mit yıkma ("bunu yanlış biliyorsun")
  shock_number     Sayı şoku (çarpıcı tek istatistik)
  news_reaction    Güncel olay/kişiye tepki (konu verilmeli/seçilir)
  single_concept   Tek kavram + metafor (karmaşığı tek cümlede)
  backtest_return  Geri-dönük getiri ("X TL Y önce Z'ye koysaydın...")

Kullanım:
  python3 scripts/viral-script.py --format myth
  python3 scripts/viral-script.py --format news_reaction --topic "Trump yeni gümrük tarifeleri"
Çıkış: 0 başarı (stdout son satırı = yazılan json yolu), 1 hata.
"""
import os
import re
import sys
import json
import time
import argparse
import subprocess
import datetime
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
from llm import call as llm_call  # tek LLM kapısı: yalın çağrı + hata sınıfı + kota durumu

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCEN_DIR = os.path.join(ROOT, "public", "social", "scenarios")

# market-history.py (tireli) → modül olarak yükle (geçmiş veri; gerekince)
def _load_mh():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "market_history", os.path.join(os.path.dirname(os.path.abspath(__file__)), "market-history.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

# Gerçek veri gerektiren formatlar
DATA_FORMATS = {"backtest_return", "comparison"}


def build_market_context(fmt, instrument, amount, rng):
    """(facts_block, chart_payload) → veri formatları için gerçek rakam + grafik verisi."""
    mh = _load_mh()
    if fmt == "backtest_return":
        d = mh.backtest(instrument, amount, rng, "1mo")
        facts = (
            "GERÇEK VERİLER (Yahoo Finance — AYNEN kullan, BAŞKA rakam uydurma):\n"
            f"- Enstrüman: {d['label']}\n"
            f"- {amount} TL'yi geçen yıl bu zamanlar {d['label']}'a koysaydın bugün ~{d['end_value']} TL olurdu\n"
            f"- Yaklaşık getiri: %{d['pct']} (dönem {d['x'][0]} → {d['x'][-1]})\n"
            f"Senaryoda {amount} TL, ~{d['end_value']} TL ve %{d['pct']} sayılarını kullan; 'yaklaşık' de.")
        chart = {"kind": "line", "label": d["label"], "unit": d["unit"], "points": d["points"],
                 "x": d["x"], "amount": amount, "end_value": d["end_value"], "pct": d["pct"]}
        return facts, chart
    if fmt == "comparison":
        c = mh.compare(rng, "1mo")
        lines = "\n".join(f"- {i['name']}: %{i['pct']}" for i in c["items"])
        winner = c["items"][0]["name"] if c["items"] else ""
        facts = (
            "GERÇEK VERİLER (Yahoo Finance, son 1 yıl getirileri — AYNEN kullan, sıralamayı bozma):\n"
            f"{lines}\n"
            f"Kazanan: {winner}. Bu rakamları ve doğru sıralamayı kullan; başka rakam uydurma.")
        chart = {"kind": "bars", "title": "Bu Yıl Kim Kazandırdı?",
                 "items": [{"name": i["name"], "pct": i["pct"]} for i in c["items"]]}
        return facts, chart
    return "", None

# Görsel tipi sözlüğü — üreticiye DOĞRU kaynak-hizalı tip seçtirir.
VISUAL_GUIDE = """Görsel tipleri ve "query" kuralı (görsel motoru buna göre kaynak seçer):
- "person": gerçek kişi → query = TAM ÖZEL AD (ör. "Donald Trump", "Recep Tayyip Erdoğan", "Elon Musk"). Wikimedia'dan gerçek fotoğraf gelir.
- "place" / "building": gerçek yer → query = özel ad. TÜRK kurumlarını GERÇEK adıyla kullan: "Central Bank of the Republic of Turkey" (TCMB), "Borsa İstanbul", "Grand Bazaar Istanbul", "Istanbul Levent skyline"; yabancılar için "Federal Reserve building" vb.
- "logo": marka/şirket → query = "<Şirket> logo".
- "gold": altın görseli → query İNGİLİZCE (ör. "gold bullion bars", "gold coins", "gold bracelet jewelry").
- "object": EVRENSEL gerçek nesne → query İNGİLİZCE isim (ör. "calculator", "wallet", "piggy bank", "receipt paper", "smartphone banking app", "house keys").
- "concept" / "scene": YALNIZ gerçekten soyut fikirler için (kayıp, risk, zaman, belirsizlik) → ekranda markalı animasyon KARTINA dönüşür (stok video gelmez); query İngilizce kısa terim.
YASAK görseller (Türk izleyiciye yabancı/yanıltıcı): YABANCI banknot/para destesi, yabancı market fiyat etiketi, yabancı bayrak/bina; kişi/kurum belirsizse genel "building/people" yerine ilgili Türk kurumunu ya da evrensel nesneyi seç.
ÖNEMLİ: hook ve konunun ana öznesi gerçek bir kişi/yer/marka ise MUTLAKA person/place/logo kullan (stok değil). Her beat'in görseli o beat'in İÇERİĞİYLE birebir örtüşsün; 5 beat'in en az 2'si somut (person/place/logo/gold/object/chart) olsun."""

# shock_number kazanan kalıbı (izlenme verisi 2026-10-09: kira-getirisi-%3 954, 5.000-ton-altın 935,
# çeyrek-%10 924 izl. — format medyanı ~500): kanca = günlük birimde TEK rakam; beat 1 = o rakamın
# izleyicinin yapabileceği HESABI; beat 2 = gizli kesinti/çarpan; beat 3 = cebe sonuç.
SHOCK_EXAMPLES = """Kazanan kalıp (kelimesi kelimesine kopyalama; YAPIYI al, konuyu tazele):
  • Kanca: "İstanbul dairesinin kira getirisi yaklaşık yüzde üç."
    1. cümle: "6 milyon TL daire, ayda 15 bin TL kira — yılda 180 bin TL, yani yüzde 3."
    2. cümle: "Bakım, vergi, boş kalma dönemi çıkınca net getiri yüzde 1-2'de kalıyor."
  • Kanca: "Türklerin evinde yaklaşık 5.000 ton altın uyuyor."
    1. cümle: "Bu rakam, Merkez Bankası'nın resmi altın rezervinin yaklaşık üç katı."
  • Kanca: "Çeyrek altını bozduğunda yüzde on para uçuyor."
    1. cümle: "Çeyrek fiyatı gram değil — darphane primi ve işçilikle şişirilmiş bir rakam."
Ortak DNA: kanca rakamı izleyicinin parasına/evine/altınına dokunur; 1. cümle o rakamın HESABINI
izleyicinin kafadan doğrulayabileceği sade bir aritmetikle verir; rakam "yaklaşık" ile dürüstçe söylenir.
RAKAM KAYNAĞI ZORUNLU: kancadaki rakam ya (a) senaryodaki sade bir hesaptan çıkmalı ya da (b) bilinen
resmi/kurumsal bir kaynağa (TCMB, TÜİK, SGK, GİB, BDDK, Dünya Altın Konseyi, Borsa İstanbul vb.)
dayanmalı. Emin olmadığın, kaynağını gösteremeyeceğin rakamı KULLANMA — başka bir konu seç."""

SHOCK_SOURCE_FIELD = (',\n "number_source":{"number":"<kancadaki rakam, aynen>","calc":"<rakamın hesabı, '
                      'ör. 180.000/6.000.000 = %3; hesap yoksa boş>","source":"<kurum/veri adı + dönem, '
                      'ör. TCMB Konut Fiyat Endeksi Ağu 2026; hesaptan çıkıyorsa \'senaryodaki hesap\'>"}')

# "kaynak" diye geçemeyecek muğlak ifadeler
_VAGUE_SRC = ("tahmin", "genel bilgi", "yaygın", "bilinen", "uzman", "araştırmalar", "kaynak yok",
              "internet", "çeşitli", "bilinmiyor", "varsayım")


def check_number_source(data):
    """shock_number senaryosunda rakamın hesap/kaynak satırı var mı? → (ok, neden)."""
    ns = data.get("number_source")
    if not isinstance(ns, dict):
        return False, "number_source alanı yok"
    num = str(ns.get("number") or "").strip()
    calc = str(ns.get("calc") or "").strip()
    src = str(ns.get("source") or "").strip()
    if not num or not re.search(r"\d|bir|iki|üç|dört|beş|altı|yedi|sekiz|dokuz|on|yüz|bin", num.lower()):
        return False, "number_source.number boş/rakamsız"
    has_calc = bool(re.search(r"\d.*[=/×x*÷+\-].*\d", calc))
    src_l = src.lower()
    # kurum adı varsa ("Dünya Altın Konseyi tahmini") muğlak kelime tek başına reddettirmez
    named = re.search(r"\b[A-ZÇĞİÖŞÜ]{3,}\b|Konseyi|Bankası|Kurumu|Borsa|Bakanlığı|Hazine|Yahoo", src)
    has_src = (len(src) >= 6 and "senaryodaki hesap" not in src_l   # 'hesap' diyorsa calc dolu olmalı
               and (named or not any(v in src_l for v in _VAGUE_SRC)))
    if not (has_calc or has_src):
        return False, f"rakam kaynaksız (calc='{calc[:60]}', source='{src[:60]}')"
    return True, ""


FORMATS = {
    "comparison": {
        "category": "KARŞILAŞTIRMA",
        "guide": "Karşılaştırma yarışı. Hook: 'Altın mı, dolar mı, borsa mı, mevduat mı?' tarzı bir yarış sorusu. 3 beat: araçları tek tek kıyasla, sayısal/karşılaştırmalı konuş. Sonunda net bir kazanan ya da çıkarım. Görseller: her araç için gold/concept(dollar)/concept(stock market)/concept(bank).",
    },
    "myth": {
        "category": "MİT",
        "guide": "Mit yıkma. Hook: yaygın ama YANLIŞ bir finans inancını söyle ('Bankada para tutmak güvenli sanıyorsun.'). 3 beat: neden yanlış olduğunu, gerçeği ve doğrusunu anlat. Hafif kışkırtıcı ama doğru. Görseller içerikle örtüşsün.",
    },
    "shock_number": {
        "category": "ŞOK VERİ",
        "guide": "Sayı şoku. Hook: çarpıcı TEK istatistik/oran ('Türkiye'de her 100 kişiden 80'i...'). 3 beat: sayının anlamı, sebebi, izleyici için sonucu. Rakamı net telaffuz et (ekranda otomatik rozet çıkar). Görseller içerikle örtüşsün.\n" + SHOCK_EXAMPLES,
    },
    "news_reaction": {
        "category": "GÜNCEL",
        "guide": "Güncel olay/kişiye tepki. Hook: olayı/kişiyi söyle ve finansal soruyu sor. 3 beat: olayın piyasaya/altına/dolara/borsaya etkisini sade anlat. Spekülasyon değil, mekanizma. Olayın SONUCUNU (faizi artırdı/indirdi/sabit tuttu, açıklanan rakam) başlıkta ve metinde ASLA iddia etme — video açıklamadan önce yayınlanıyor; 'karar bugün', 'hangi yönde çıkarsa cebine ne olur' çerçevesi kullan. Hook görseli ana kişi/kurum (person/place/logo) OLMALI.",
    },
    # Olay SONRASI (resmî rakam elde): scripts/event-short.py çağırır, --facts + --must ile.
    # news_reaction'ın tersine sonucu SÖYLER — ama yalnız KESİN VERİLER bloğundaki rakamla.
    "event_result": {
        "category": "AÇIKLANDI",
        "guide": "Resmî sonuç AÇIKLANDI — izleyici bunu YouTube'da arıyor ('… açıklandı', '… belli oldu'). "
                 "Hook: sonucu ve EN ÖNEMLİ rakamı doğrudan söyle (soru değil, düz cümle: 'Ekim enflasyonu yüzde 2,5 çıktı.'). "
                 "3 beat: (1) rakamın anlamı + bir önceki dönemle kıyas, (2) izleyicinin cebine etkisi (kira, maaş, "
                 "kredi, MTV, emekli zammı — KESİN VERİLER'de ne varsa), (3) sıradaki tarih/izleyicinin yapacağı şey. "
                 "YALNIZ 'KESİN VERİLER' bloğundaki rakamları kullan; yeni rakam, tahmin, yuvarlama YOK; ondalıkta "
                 "virgül kullan. title: insanların YouTube'da aradığı kalıp — kurum/olay adı (TCMB, Fed, TÜİK, asgari ücret, "
                 "emekli zammı) + ay/yıl + 'açıklandı/belli oldu' + ana rakam; bu kelimeler İLK 40 karakterde (ör. 'TCMB Ekim "
                 "faiz kararı açıklandı: %36', 'Ekim enflasyonu açıklandı: yıllık %32,1', '2027 asgari ücret belli oldu: "
                 "net 33.500 TL'). Hook görseli kurum (TÜİK/TCMB/Fed binası ya da logosu: place/logo/building).",
    },
    "single_concept": {
        "category": "KAVRAM",
        "guide": "Tek kavram + metafor. Hook: kavramı merak uyandıran biçimde sor ('Eurobond aslında ne?'). 3 beat: kavramı GÜNLÜK bir metaforla tek tek aç, jargon yok. Görseller kavramı somutlaştırsın (object/concept).",
    },
    "backtest_return": {
        "category": "GETİRİ",
        "guide": "Geri-dönük getiri. Hook: 'X TL'yi Y önce Z'ye koysaydın bugün ne olurdu?' 3 beat: senaryoyu ve sonucu adım adım ver; net bir sonuç sayısı söyle (uydurma değil, makul/yaklaşık olduğunu ima et). Görseller: gold/money/concept(chart).",
    },
}

PROMPT = """Sen bir Türk finans kanalı (ParaFOMO) için VİRAL YouTube Shorts senaryosu yazıyorsun.
28-33 saniyelik (KISA ve YOĞUN), akıcı, KONUŞMA dilinde, izleyiciyi ilk 2 saniyede durduran bir
senaryo üret. Tamamlanma oranı Shorts sıralamasının #1 sinyali: 20-35 sn videolar en yüksek
tamamlanmayı alır; her cümle bir işe yarasın, dolgu/tekrar YOK, hedefin üstüne taşma.

İZLEYİCİ: enflasyondan yorulmuş, finansı karmaşık bulan, birikimini korumak isteyen Türk.
SES: net, dürüst, hafif iddialı bir arkadaş — abartı ve pazarlama dili YOK, güven veren sadelik var.

FORMAT: %(fmt_name)s
%(fmt_guide)s
%(topic_line)s
%(avoid_block)s%(facts_block)s
%(chart_instruction)s
Kurallar:
- hook: EN FAZLA 7 kelime. ŞİMDİKİ ZAMAN + İDDİALI DÜZ CÜMLE (bold-claim) tercih et — SORU kancası
  ("...mı?") daha zayıf tutuyor; kaçınılmaz değilse soru sorma, iddiayı DÜZ söyle. Şu kalıplardan
  BİRİNİ kullan (kelimesi kelimesine kopyalama, konuya uyarla):
    • Çarpıcı sayı:   "100 lira 3 ayda 74 liraya düştü."
    • Sezgi-dışı:     "Faiz kazandırmıyor, seni fakirleştiriyor."
    • Açık döngü:     "Bankanın sana söylemediği tek şey var."
    • Sen-dili + kayıp: "Paran sen fark etmeden eriyor."
  YASAK klişeler (kullanma): "işte gerçek", "şoke etti", "kötü haber", "bunu yanlış biliyorsun",
  "inanılmaz", "herkes kaçırıyor", "aman dikkat". Tıklama tuzağı değil: söz verdiğini içerikte KARŞILA.
- HOOK GÖRSEL-METİN ZITLIĞI (pattern-interrupt + merak boşluğu): hook beat'inin GÖRSELİ, hook METNİNİN
  söylediğiyle bilerek ÇELİŞSİN. Yani ekranda çekici/beklenen olumlu yüzeyi göster (parlak altın bilezik,
  yeni bir ev, dolu bir cüzdan, yükselen grafik) ama metin kaybı/miti söylesin ("Bu seni zengin etmez."):
  göz "güzel" görürken kulak "tehlike" duyar → ilk 1-2 saniyede kaydırmayı keser. Bu yüzden hook görselinin
  "query"si, hook metninin OLUMSUZ iddiasının aksine POZİTİF/İSTENEN nesneyi betimlesin.
  İSTİSNA: hook'un öznesi gerçek bir kişi/yer/marka ise (özellikle news_reaction) ZITLIK YAPMA — o kişiyi/
  kurumu birebir göster (person/place/logo). Zıtlık yalnız gold/object/concept görselli hook'lar için.
  point beat'lerinin görselleri her zaman içerikle ÖRTÜŞSÜN (zıtlık sadece hook'ta).
- 3 beat YÜKSELEREK ilerlesin (izleyiciyi sonuna kadar tutacak akış):
    beat 1: kancadaki merakı DERİNLEŞTİR — neden/nasıl olduğunu, yeni bir bilgiyle aç.
            KÖPRÜ: kancanın açtığı döngüye HEMEN somut bir ödül-kırıntısı ver (izleyici 1. saniyede
            "cevap geliyor" hissetsin), açıklamayı sona saklama; boşlukta bekletme = kaydırma.
    beat 2: gerilim/çelişki — "ama" ile beklenmedik bir dönüş ya da çarpıcı bir rakam getir.
    beat 3: ÖDÜL — net çıkarım + izleyicinin cebine dokunan somut sonuç/eylem.
  Her beat 11-15 kelime (KISA tut — toplam süreyi 33 sn'nin altında bırak), tek başına anlaşılır,
  akıcı Türkçe; kopuk ifade yok.
- SOMUT konuş: soyut laf ("faiz eriyor") yerine günlük çapa kullan (market arabası, kira, 100 bin TL,
  bir yıl önce vs bugün). Jargonu günlük dile çevir; teknik terim kullanırsan hemen sadeleştir.
- cta: kısa. Önce ileriye dönük bir MERAK cümlesi (HER SEFERİNDE FARKLI ifade et; kalıplaşma),
  sonra abone çağrısı + net bir SEBEP/vaat ("her gün 60 saniyede tek net analiz" gibi, bunu da döndür).
  "abone ol" ifadesi mutlaka geçsin ama aynı cümleyi tekrarlama.
- title: kancadan FARKLI olsun (aynı cümleyi tekrarlama), merak boşluğu taşısın, <70 karakter,
  klişe içermesin; tıklanınca içerik sözü tutsun. ÖNEMLİ: Shorts akışı başlığı ~40 karakterde
  KESER — bu yüzden en çarpıcı kelimeyi/konu anahtarını (altın, dolar, faiz, emeklilik vb.) İLK
  40 karaktere yerleştir; merak/çengeli başa koy, açıklayıcı kısmı sona bırak. Soru değil,
  iddialı/net cümle tercih et.
- Sade, net, abartısız; değer ver. Yanlış/uydurma rakam verme; tahmini ifadeleri "yaklaşık/olası" diye ver.
- Her segmente bir "visual" ekle.
%(visual_guide)s

SADECE şu JSON'u döndür, başka HİÇBİR şey yazma (markdown, ```, açıklama YOK):
{"title":"<Türkçe, çarpıcı, <70 karakter>","description":"<1-2 cümle özet>","tags":["...","...","..."],
 "segments":[
  {"kind":"hook","eyebrow":"%(eyebrow)s","spoken":"...","visual":{"type":"...","query":"..."}},
  {"kind":"point","spoken":"...","visual":{"type":"...","query":"..."}},
  {"kind":"point","spoken":"...","visual":{"type":"...","query":"..."}},
  {"kind":"point","spoken":"...","visual":{"type":"...","query":"..."}},
  {"kind":"cta","spoken":"...","visual":{"type":"...","query":"..."}}
 ]%(extra_field)s}
"""

ALLOWED_TYPES = {"person", "place", "building", "logo", "gold", "object",
                 "concept", "scene", "broll", "map", "chart"}


def slugify(s):
    s = unicodedata.normalize("NFKD", s)
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")
    s = s.translate(tr).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:60] or "viral"


def load_recent_titles(out_dir, limit=45):
    """Son üretilen senaryoların başlıklarını (yeni→eski) döndür — tekrar önleme için."""
    try:
        files = [os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.endswith(".json")]
    except FileNotFoundError:
        return []
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    titles = []
    for p in files[:limit]:
        try:
            t = (json.load(open(p, encoding="utf-8")).get("title") or "").strip()
        except Exception:
            continue
        if t:
            titles.append(t)
    return titles


# Başlık benzerliği için: anlamsız/çok geçen kelimeleri ele, öz kelime kümesi çıkar.
_STOP = {"mi", "mu", "mı", "mü", "ne", "ile", "ve", "bir", "bu", "için", "olur",
         "olurdu", "koysaydin", "kac", "sen", "ama", "gibi", "daha", "cok", "ise",
         "diye", "iste", "gercek", "gercegi", "yapacak", "anlama", "geliyor"}


def _tokens(s):
    s = s.lower().translate(str.maketrans("çğıöşü", "cgiosu"))
    return {w for w in re.findall(r"[a-z0-9]+", s) if len(w) > 2 and w not in _STOP}


def search_hint(fmt):
    """YouTube araması kanal izlenmesinin ~%21'i (RC 10-28). agent/brief.py her sabah bizi bulduran arama terimlerini
    data/learning/yt-search-terms.json'a yazar; konu serbestken üretici bu kalıplara yaslanabilsin. Dosya yoksa boş."""
    try:
        d = json.load(open(os.path.join(ROOT, "data", "learning", "yt-search-terms.json"), encoding="utf-8"))
        terms = [t[0] for t in d.get("terms", [])][:12]
    except Exception:
        return ""
    if not terms:
        return ""
    strong = fmt == "single_concept"
    return ("\nYOUTUBE ARAMASI: kanala gelen izlenmenin ~%21'i aramadan. Son 28 günde bizi bulduran aramalar: "
            + ", ".join(terms) + ". " + ("Bu formatta konuyu MÜMKÜNSE bu aramalardan birinin AYNI niyetinden seç "
            "(ör. 'X nedir' → X'i tek kavramla anlat) ve aranan ifadeyi başlığın İLK 40 karakterine koy."
            if strong else "Konu bu aramalardan birinin niyetine uyuyorsa aranan ifadeyi başlığın ilk 40 karakterine koy; "
            "uymuyorsa zorlama — tema ekseni öncelikli."))


def has_number(text, num):
    """Metinde rakam var mı? '2,55' ↔ 2.55 / %2,55 / yüzde 2,55; binlikli '28.075' ↔ 28075 de kabul."""
    n = (num or "").strip().lstrip("%").strip()
    if not n:
        return True
    alts = {n, n.replace(",", "."), n.replace(".", ",")}
    alts |= {a.replace(".", "") for a in list(alts) if re.fullmatch(r"\d{1,3}(\.\d{3})+", a)}
    # ondalıktaki sondaki sıfır: '28,90' ↔ '28,9' · '36,00' ↔ '36'
    alts |= {re.sub(r"[,.]$", "", re.sub(r"0+$", "", a)) for a in list(alts) if re.search(r"[,.]\d*0$", a)}
    for a in alts:
        if re.search(r"(?<![\d.,])" + re.escape(a) + r"(?![\d])", text or ""):
            return True
    return False


def most_similar(title, recent, thresh=0.5):
    """title son başlıklardan birine yeterince benziyorsa o başlığı döndür (Jaccard)."""
    a = _tokens(title)
    if not a:
        return ""
    best, best_j = "", 0.0
    for t in recent:
        b = _tokens(t)
        if not b:
            continue
        j = len(a & b) / len(a | b)
        if j > best_j:
            best, best_j = t, j
    return best if best_j >= thresh else ""


# Günlük konu kümesi kapısı (V3, 2026-10-24): aynı gün aynı kümeden iki video → biri akışı alıyor,
# diğeri 0-13 izlenme (V2: dolar 5000 ×2 → 13 vs 554; 10-21 altın ×3). Kök = ascii-katlanmış kelime öneki.
CLUSTERS = {
    "altın": ("altin", "gram", "ceyrek", "cumhuriyet", "ziynet", "bilezik", "ons", "gumus"),
    "döviz": ("dolar", "euro", "doviz", "sterlin"),
    "borsa": ("borsa", "bist", "hisse", "halka", "temettu", "tefas", "fon"),
    "kripto": ("kripto", "bitcoin", "btc", "ethereum"),
    "faiz": ("faiz", "mevduat", "tcmb", "merkez", "fed", "ppk", "vadesiz", "vadeli"),
    "kredi": ("kredi", "kart", "borc", "findeks", "taksit"),
    "vergi": ("vergi", "kdv", "stopaj", "harc", "mtv", "beyanname"),
    "maaş": ("emekli", "maas", "zam", "memur", "asgari", "kidem", "sgk"),
}
_TR_MONTHS = {"ocak": 1, "subat": 2, "mart": 3, "nisan": 4, "mayis": 5, "haziran": 6, "temmuz": 7,
              "agustos": 8, "eylul": 9, "ekim": 10, "kasim": 11, "aralik": 12}


def _fold(s):
    return s.lower().translate(str.maketrans("çğıöşüâî", "cgiosuai"))


def clusters_of(text):
    """Metindeki kümeler, ilk geçiş sırasıyla (ilki = ana varlık)."""
    out = []
    for w in re.findall(r"[a-z0-9]+", _fold(text)):
        for c, roots in CLUSTERS.items():
            if c not in out and any(w.startswith(r) for r in roots):
                out.append(c)
    return out


def main_cluster(text):
    cs = clusters_of(text)
    return cs[0] if cs else ""


def _planned_blog_topic(today):
    """Bugün daily-content'in yazacağı (→ Blog→Short 11:00) kuyruk konusu; tarihi gelmemiş 📅 satır atlanır."""
    try:
        lines = open(os.path.join(ROOT, "agent", "plan", "content-queue.md"), encoding="utf-8").read().splitlines()
    except Exception:
        return ""
    if today.weekday() >= 5:  # blog yazısı Pzt-Cum
        return ""
    for ln in lines:
        if not ln.startswith("- [ ]"):
            continue
        m = re.search(r"📅\s*(\d{1,2})\s+(\w+)", ln)
        if m:
            mon = _TR_MONTHS.get(_fold(m.group(2)))
            if mon and (mon, int(m.group(1))) > (today.month, today.day):
                continue
        t = re.search(r"\*\*(.+?)\*\*", ln)
        return t.group(1) if t else ln[5:120]
    return ""


def todays_clusters(today=None):
    """Bugün (UTC) diğer hatların ürettiği/planladığı videoların konu kümeleri → {küme: [kaynak, ...]}."""
    today = today or datetime.datetime.now(datetime.timezone.utc).date()
    social = os.path.join(ROOT, "public", "social")
    items = []
    for d in (social, os.path.join(social, "scenarios")):
        try:
            names = os.listdir(d)
        except FileNotFoundError:
            continue
        for f in names:
            p = os.path.join(d, f)
            if not f.endswith(".json") or (d == social and not f.startswith("short-")):
                continue
            if datetime.datetime.fromtimestamp(os.path.getmtime(p), datetime.timezone.utc).date() != today:
                continue
            try:
                title = json.load(open(p, encoding="utf-8")).get("title") or ""
            except Exception:
                title = ""
            items.append((f[:-5].removeprefix("short-"), title or f[:-5].replace("-", " ")))
    real_today = datetime.datetime.now(datetime.timezone.utc).date()
    blog = _planned_blog_topic(today) if today == real_today else ""  # kuyruk yalnız bugünü bilir
    if blog:
        items.append(("blog-kuyruğu: " + blog[:60], blog))
    out = {}
    for src, text in items:
        c = main_cluster(text)
        if c and src not in out.setdefault(c, []):
            out[c].append(src)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", required=True, choices=list(FORMATS))
    ap.add_argument("--topic", default="")
    ap.add_argument("--facts", default="",
                    help="event_result: resmî rakamlar (prompt'a KESİN VERİLER olarak girer)")
    ap.add_argument("--must", default="",
                    help="event_result: başlık+metinde MUTLAKA geçmesi gereken rakamlar, '|' ile (ör. '2,55|32,87')")
    ap.add_argument("--link", default="",
                    help="huni linki (ör. /kira-artis-orani-hesaplama/) — YouTube açıklamasına gider")
    ap.add_argument("--slug", default="")
    ap.add_argument("--instrument", default="gold", choices=["gold", "usd", "bist"],
                    help="backtest_return için enstrüman")
    ap.add_argument("--amount", type=int, default=10000)
    ap.add_argument("--range", default="1y")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--out-dir", default=SCEN_DIR)
    ap.add_argument("--dry-run", action="store_true",
                    help="senaryoyu dosyaya yazma, JSON'u stdout'a bas (izole deneme)")
    ap.add_argument("--clusters", action="store_true",
                    help="LLM çağırmadan bugünün dolu konu kümelerini yazdır (kapı testi)")
    ap.add_argument("--today", default="", help="--clusters için gün (YYYY-MM-DD, varsayılan bugün UTC)")
    args = ap.parse_args()

    busy = todays_clusters(datetime.date.fromisoformat(args.today) if args.today else None)
    if args.clusters:
        print(json.dumps(busy, ensure_ascii=False, indent=1))
        return 0

    fmt = FORMATS[args.format]
    # KAZANAN DNA (2026-08 izlenme analizi): en çok izlenen 8 videonun HEPSİ altın
    # ve/veya kayıp-korkusu temalı (takı altını, 5000 ton altın, "paran eriyor",
    # "banka seni değil kendini korur"). Konu serbestse üretimi bu eksene yasla;
    # tazelik "kaçınılacak başlıklar" listesiyle korunur.
    WINNING_THEMES = (
        "Öncelikli tema ekseni (izlenme verisi bunları ödüllendiriyor — bu eksenden "
        "TAZE bir açı seç): (a) ALTIN gerçekleri — çeyrek/ziynet/gram/kasa/takı altını, "
        "işçilik payı, altını atıl tutmanın maliyeti; (b) KAYIP-KORKUSU/karşıt görüş — "
        "'paran sessizce eriyor', 'banka seni değil kendini korur', 'maaşın artıyor ama "
        "serveti nerede', 'güvende sandığın araç aslında kaybettiriyor'; (c) OTORİTE DELME "
        "— uzman/fon/kurum neden yetersiz kaldı; (d) GERÇEK-VERİ ŞOKU — kendi güncel veri "
        "sayfalarımızdaki çarpıcı rakamlar: son 10 yılda altın TL bazında dolardan ~3.6 KAT "
        "fazla kazandırdı (altın ~%5450 vs dolar ~%1509); '10.000 TL'yi 10 yıl önce dolara "
        "çevirseydin bugün ~160 bin TL, ama altına koysaydın ~550 bin TL' gibi somut "
        "kur-vs-altın kıyasları izleyiciyi çarpar. Sıkıcı 'X nedir' tanımından KAÇIN.")
    topic_line = (f"KONU (bu konuyu işle): {args.topic}" if args.topic
                  else "KONU: Türk yatırımcısının ilgisini çekecek TAZE bir konuyu SEN seç.\n" + WINNING_THEMES
                  + search_hint(args.format))

    # Veri formatları: gerçek geçmiş veriyi çek, prompt'a göm, grafiği hazırla
    facts_block, chart_instruction, chart_payload = "", "", None
    if args.format in DATA_FORMATS:
        try:
            facts_block, chart_payload = build_market_context(
                args.format, args.instrument, args.amount, args.range)
            chart_instruction = (
                'SONUCU/KARŞILAŞTIRMAYI açıkladığın TEK bir point beat\'inin visual.type\'ını '
                '"chart" yap (query="getiri grafiği"); o beat ekranda grafiği gösterecek. '
                'Diğer beat\'lerde normal görsel (gold/concept/person) kullan.')
        except Exception as e:
            print(f"UYARI: piyasa verisi alınamadı ({str(e)[:70]}) — grafiksiz devam", file=sys.stderr)
    musts = [m.strip() for m in args.must.split("|") if m.strip()]
    if args.facts:
        facts_block += ("KESİN VERİLER (resmî kaynak, açıklandı — YALNIZ bunları kullan; başka rakam uydurma, "
                        "yuvarlama yapma, ondalıkta virgül kullan):\n" + args.facts.strip() + "\n"
                        + (f"Başlıkta VE metinde şu rakam(lar) birebir geçmeli: {', '.join(musts)}\n" if musts else ""))
    if args.format == "event_result" and not args.facts:
        print("HATA: event_result --facts ister (resmî rakam olmadan sonuç videosu üretilmez)", file=sys.stderr)
        return 1

    # Tekrar önleme: son üretilen başlıkları prompt'a "bunları TEKRARLAMA" olarak göm.
    recent_titles = load_recent_titles(args.out_dir)
    retry_notes = []   # event_result: reddedilen denemenin eksik rakamları (sonraki prompt'a)

    def build_prompt(extra_avoid=()):
        titles = list(dict.fromkeys(recent_titles + list(extra_avoid)))
        if args.format == "event_result":
            # Konu olayın kendisi: "son videoları tekrarlama" listesi burada ters teper (sabah önizlemesi
            # aynı olayı işledi diye sonuç videosu konusunu değiştirmemeli). Ret nedeni varsa onu söyle.
            note = (("ÖNCEKİ DENEME REDDEDİLDİ — zorunlu rakam eksikti: " + "; ".join(retry_notes) + "\n\n")
                    if retry_notes else "")
            return PROMPT % {
                "fmt_name": args.format, "fmt_guide": fmt["guide"], "topic_line": topic_line,
                "avoid_block": note, "facts_block": facts_block,
                "chart_instruction": chart_instruction, "visual_guide": VISUAL_GUIDE,
                "eyebrow": fmt["category"], "extra_field": "",
            }
        if titles:
            lst = "\n".join(f"- {t}" for t in titles[:45])
            avoid_block = (
                "SON ÜRETİLEN VİDEOLAR (aşağıdaki başlıklar zaten yayınlandı). "
                "Bunları ne KONU ne de AÇI olarak TEKRARLAMA; aynı konuyu farklı "
                "kelimelerle yeniden anlatmak da yasak. Listede OLMAYAN, tamamen "
                "farklı ve TAZE bir konu/açı seç:\n" + lst + "\n\n")
        else:
            avoid_block = ""
        if busy and not args.topic:
            avoid_block += (
                "BUGÜN kanalın diğer videoları şu konu kümelerini zaten işliyor: "
                + ", ".join(sorted(busy)) + ". Aynı gün aynı kümeden ikinci video akışta "
                "birbirini yiyor — bu kümelerin DIŞINDAN bir konu seç.\n\n")
        return PROMPT % {
            "fmt_name": args.format, "fmt_guide": fmt["guide"], "topic_line": topic_line,
            "avoid_block": avoid_block, "facts_block": facts_block,
            "chart_instruction": chart_instruction, "visual_guide": VISUAL_GUIDE,
            "eyebrow": fmt["category"],
            "extra_field": SHOCK_SOURCE_FIELD if args.format == "shock_number" else "",
        }

    print(f"[*] viral senaryo üretiliyor: format={args.format} topic={args.topic or '(serbest)'} "
          f"(kaçınılan başlık: {len(recent_titles)})", file=sys.stderr)

    # LLM çağrısı scripts/lib/llm.py kapısından geçer: auth/kota hatası ASLA içerik olmaz,
    # sert limitte (session/weekly) anında döner — boşuna 4×90 sn beklenmez.
    MAX_TRIES, WAIT = 4, 60

    def one_shot(prompt):
        """Tek LLM çağrısı → (data|None, transient_bool, ham_çıktı_ya_da_hata_türü)."""
        ok, out, kind = llm_call(prompt, model=args.model, effort="medium", timeout=300,
                                 tries=2, tag="viral-script")
        if not ok:
            return None, kind == "transient", kind
        m = re.search(r"\{.*\}", out, re.DOTALL)
        if not m:
            return None, False, out
        try:
            return json.loads(m.group(0)), False, out
        except Exception as e:
            print(f"UYARI: JSON ayrıştırılamadı ({e}): {out[:160]}", file=sys.stderr)
            return None, False, out

    data, extra_avoid, out = None, [], ""
    for attempt in range(1, MAX_TRIES + 1):
        d, transient, out = one_shot(build_prompt(extra_avoid))
        if d is not None:
            title = (d.get("title") or "").strip()
            if args.format == "event_result":
                # Yanlış/eksik rakamlı "açıklandı" videosu = yanıltıcı içerik → yayınlanmaz.
                alltext = title + " " + " ".join(str(s.get("spoken", "")) for s in (d.get("segments") or []))
                miss = [m for m in musts if not has_number(alltext, m)]
                if musts and not has_number(title, musts[0]):
                    miss.insert(0, f"{musts[0]} (başlıkta)")
                if miss:
                    print(f"UYARI: sonuç senaryosu zorunlu rakam(lar)ı içermiyor: {miss} "
                          f"(deneme {attempt}/{MAX_TRIES})", file=sys.stderr)
                    retry_notes.append(", ".join(miss))
                    continue
                data = d
                break
            if args.format == "shock_number":
                ok_src, why = check_number_source(d)
                if not ok_src:
                    # yanıltıcı başlık = platform kırmızı çizgisi → kaynaksız rakam yayınlanmaz
                    print(f"UYARI: senaryo reddedildi — {why} (deneme {attempt}/{MAX_TRIES})",
                          file=sys.stderr)
                    if title:
                        extra_avoid.append(title)
                    continue
            dup = most_similar(title, recent_titles + extra_avoid)
            if dup and attempt < MAX_TRIES:
                print(f"UYARI: '{title}' son videolara çok benziyor (≈ '{dup}') — "
                      f"yeni konu isteniyor (deneme {attempt}/{MAX_TRIES})", file=sys.stderr)
                extra_avoid.append(title)
                continue
            clash = main_cluster(title + " " + str((d.get("segments") or [{}])[0].get("spoken", "")))
            if clash in busy and not args.topic and args.format not in DATA_FORMATS:
                if attempt < MAX_TRIES:
                    print(f"UYARI: '{title}' bugünkü dolu kümeye düşüyor ({clash}: {busy[clash][0]}) — "
                          f"farklı küme isteniyor (deneme {attempt}/{MAX_TRIES})", file=sys.stderr)
                    extra_avoid.append(title)
                    continue
                print(f"UYARI: küme çakışması kaldı ({clash}) — üretim sürüyor", file=sys.stderr)
            data = d
            break
        if attempt < MAX_TRIES and transient:
            print(f"UYARI: senaryo alınamadı (deneme {attempt}/{MAX_TRIES}), "
                  f"{WAIT}sn sonra tekrar. Çıktı: {out[:160]}", file=sys.stderr)
            time.sleep(WAIT)
            continue
        break

    if data is None:
        print(f"HATA: senaryo üretilemedi ({MAX_TRIES} deneme). Çıktı: {out[:200]}",
              file=sys.stderr); return 1

    # doğrulama
    segs = data.get("segments", [])
    if len(segs) != 5:
        print(f"HATA: 5 segment bekleniyor, {len(segs)} geldi", file=sys.stderr); return 1
    kinds = [s.get("kind") for s in segs]
    if kinds != ["hook", "point", "point", "point", "cta"]:
        print(f"HATA: segment sırası hatalı: {kinds}", file=sys.stderr); return 1
    for s in segs:
        v = s.get("visual") or {}
        if not s.get("spoken") or not v.get("query") or v.get("type") not in ALLOWED_TYPES:
            print(f"HATA: eksik/yanlış segment: {json.dumps(s, ensure_ascii=False)[:160]}",
                  file=sys.stderr); return 1
    if not data.get("title"):
        print("HATA: title yok", file=sys.stderr); return 1
    # Gündem videosu karar/veri AÇIKLANMADAN önce üretilir (news-daily sabah) → sonucu iddia eden
    # başlık/metin uydurmadır (2026-10-22: TCMB %36'ya indirdi, başlık "faizi sabit tuttu" dedi).
    if args.format == "news_reaction":
        outcome = re.compile(r"sabit (tuttu|bıraktı)|(indirdi|düşürdü|artırdı|arttırdı|yükseltti)\b", re.I)
        hit = [t for t in [data["title"]] + [s["spoken"] for s in segs] if outcome.search(t)]
        if hit:
            print(f"HATA: news_reaction sonucu iddia ediyor (olay henüz açıklanmamış olabilir): {hit[0][:120]}",
                  file=sys.stderr); return 1

    # gerçek veri grafiğini chart-tipli beat'e iliştir (claude koymadıysa son point'e zorla)
    if chart_payload:
        chart_segs = [s for s in segs if (s.get("visual") or {}).get("type") == "chart"]
        if not chart_segs:
            segs[3]["visual"] = {"type": "chart", "query": "getiri grafiği"}
            chart_segs = [segs[3]]
        for s in chart_segs:
            s["visual"]["chart"] = chart_payload

    # SEAMLESS-LOOP (2026-09-02, exp 2026-09-02-1): faceless Short'ta izleyiciye
    # "video bitti" diyen fiziksel süreklilik ipucu yok → kapanış görselini açılış
    # görseliyle özdeşleştirince Short loop'landığında kanca 2. kez izlenir, retention
    # >%100'e çıkabilir (kanıtlı outlier: stagflasyon-nedir %162, bankandaki-250-bin %95).
    # Deterministik + tek-değişken: cta beat'inin görseli = hook beat'inin görseli.
    # Hook chart ise loop'a sokma (grafik kapanışı istemeyiz), aksi halde birebir kopyala.
    hook_v = segs[0].get("visual") or {}
    if hook_v.get("type") in ALLOWED_TYPES and hook_v.get("type") != "chart":
        segs[4]["visual"] = {"type": hook_v["type"], "query": hook_v["query"]}

    slug = args.slug or slugify(data["title"])
    scenario = {
        "slug": slug,
        "title": data["title"].strip(),
        "category": fmt["category"],
        "format": args.format,
        "description": data.get("description", "").strip(),
        "tags": list(dict.fromkeys([t.strip() for t in (data.get("tags") or [])[:6]
                                     if t.strip()] + ["parafomo"])),
        "segments": segs,
    }
    if args.link:
        scenario["link"] = args.link
    if data.get("number_source"):
        ns = data["number_source"]
        scenario["number_source"] = ns
        src_line = " · ".join(x for x in (str(ns.get("calc") or "").strip(),
                                          str(ns.get("source") or "").strip()) if x)
        scenario["description"] = (scenario["description"] + f"\nKaynak/hesap: {src_line}").strip()
    if args.dry_run:
        print(json.dumps(scenario, ensure_ascii=False, indent=2))
        return 0
    os.makedirs(args.out_dir, exist_ok=True)
    path = os.path.join(args.out_dir, f"{slug}.json")
    json.dump(scenario, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[+] senaryo: {path}", file=sys.stderr)
    print(f"    kanca: {segs[0]['spoken']}", file=sys.stderr)
    print(path)   # stdout: çağıran betik için yol
    return 0


if __name__ == "__main__":
    sys.exit(main())
