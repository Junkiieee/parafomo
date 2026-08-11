#!/usr/bin/env python3
"""
ParaFOMO — YouTube Shorts üretici (v3: B-roll + gerçek senkron karaoke + müzik).

v3 yenilikleri:
  - ARKA PLAN: Pexels ücretsiz dikey stok video (B-roll), konuya göre; koyu overlay
    + marka çerçevesi (eyebrow + footer wordmark) → "slayt" hissi yok.
  - SENKRON: faster-whisper ile üretilen sesin GERÇEK kelime zaman damgaları;
    bilinen senaryo metnine difflib ile hizalanır → altyazı tam senkron.
  - SES: Google Cloud TTS Chirp3-HD (edge fallback). --engine / --voice.
  - MÜZİK: bed + sidechain ducking (yoksa otomatik yumuşak pad).

Kullanım: python3 scripts/shorts-build.py <slug> [--engine google] [--voice tr-TR-Chirp3-HD-Kore]
Çıktı:    public/social/short-<slug>.mp4 (+ .json)
"""
import os
import re
import sys
import json
import shutil
import base64
import difflib
import argparse
import importlib.util
import subprocess
import urllib.request
import urllib.parse
from PIL import Image, ImageDraw, ImageFont

# viral-visuals.py (tireli dosya adı) → modül olarak yükle
_vv_spec = importlib.util.spec_from_file_location(
    "viral_visuals", os.path.join(os.path.dirname(os.path.abspath(__file__)), "viral-visuals.py"))
vv = importlib.util.module_from_spec(_vv_spec)
_vv_spec.loader.exec_module(vv)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG = os.path.join(ROOT, "src", "content", "blog")
WORDMARK = os.path.join(ROOT, "public", "parafomo-wordmark.png")
OUT_DIR = os.path.join(ROOT, "public", "social")
MUSIC = os.path.join(ROOT, "public", "social", "assets", "bed.mp3")
SA_JSON = "/root/.config/parafomo/ga-sa.json"
BROLL_CACHE = "/root/.cache/parafomo/broll"
TMP = "/tmp/shorts_frames"

W, H = 1080, 1920
M = 96
INK = (18, 20, 23)
BRAND = (43, 177, 148)
LIGHT = (99, 212, 145)
WHITE = (255, 255, 255)

SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONTSDIR = "/usr/share/fonts/truetype/liberation"
ASS_FONT = "Liberation Sans"

EDGE_VOICE = "tr-TR-EmelNeural"
GOOGLE_VOICE = "tr-TR-Chirp3-HD-Kore"
GOOGLE_RATE = 1.15  # daha hızlı/enerjik anlatım (donuk tonu canlandırmak için ↑ 2026-06-25)
EDGE_RATE = "+15%"
LEAD = 0.45
TAIL = 0.55
FPS = 30

# koyu B-roll üstünde okunan altyazı renkleri (&HAABBGGRR)
# v4: aktif kelime sarı highlight (TikTok/CapCut tipik), okunmamış beyaz.
C_SUNG = "&H004DE1FF"    # canlı sarı (aktif/okunan) — #FFE14D
C_UNSUNG = "&H00FFFFFF"  # beyaz (okunmamış)
C_OUTLINE = "&H00101012"  # koyu hale
C_SHADOW = "&HB0000000"

# konuya göre Pexels arama havuzu (İngilizce; finans B-roll her konuya uyar)
BROLL_POOL = ["stock market", "city skyline aerial", "money cash counting",
              "financial district night", "trading charts screen", "business people walking"]

# Türkçe sayı kelimeleri → rakam (ekran içi stat kartı için)
NUM_WORDS = {
    "sıfır": 0, "bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5, "altı": 6,
    "yedi": 7, "sekiz": 8, "dokuz": 9, "on": 10, "yirmi": 20, "otuz": 30,
    "kırk": 40, "elli": 50, "altmış": 60, "yetmiş": 70, "seksen": 80,
    "doksan": 90, "yüz": 100, "bin": 1000,
}


def fnt(p, s):
    return ImageFont.truetype(p, s)


# ---------- frontmatter / senaryo ----------

def fm(front, key):
    m = re.search(rf'^{key}:\s*"?(.*?)"?\s*$', front, re.MULTILINE)
    return m.group(1).strip() if m else ""


def parse_faq(front):
    out = []
    for m in re.finditer(
        r'-\s*q:\s*"?(.*?)"?\s*\n\s*a:\s*"?(.*?)"?\s*(?=\n\s*-\s*q:|\n[a-zA-Z]|\Z)',
        front, re.DOTALL):
        out.append((m.group(1).strip(), m.group(2).strip()))
    return out


def parse_list(front, key):
    m = re.search(rf'^{key}:\s*\n((?:\s*-\s*.*\n?)+)', front, re.MULTILINE)
    if not m:
        return []
    return [s.strip()[1:].strip().strip('"').strip("'")
            for s in m.group(1).splitlines() if s.strip().startswith("-")]


def parse_shorts(front):
    return parse_list(front, "shorts")


def first_sentences(text, n=2):
    return " ".join(re.split(r'(?<=[.!?])\s+', text.strip())[:n]).strip()


def build_segments(front):
    """[(kind, eyebrow, spoken), ...]"""
    title = fm(front, "title")
    category = (fm(front, "category") or "Finans").upper()
    custom = parse_shorts(front)
    segs = []
    if custom:
        hook, cta = custom[0], (custom[-1] if len(custom) > 2 else "Her gün yeni analiz için abone ol, kaçırma!")
        points = custom[1:-1] if len(custom) > 2 else custom[1:]
        segs.append(("hook", category, hook))
        for p in points[:4]:
            segs.append(("point", "", p))
        segs.append(("cta", "", cta))
        return title, segs
    faq = parse_faq(front)[:3]
    hk = re.sub(r'\s+', ' ', title).strip()
    segs.append(("hook", category, hk if hk.endswith(("?", ".", "!")) else hk + "."))
    for q, a in faq:
        segs.append(("point", "", f"{q.rstrip('?')}? {first_sentences(a,1)}"))
    segs.append(("cta", "", "Her gün yeni finans analizi için abone ol, paranı büyüt!"))
    return title, segs


# ---------- TTS ----------

_gtoken = None


def _google_token():
    global _gtoken
    if not _gtoken:
        from google.oauth2 import service_account
        import google.auth.transport.requests as gt
        creds = service_account.Credentials.from_service_account_file(
            SA_JSON, scopes=["https://www.googleapis.com/auth/cloud-platform"])
        creds.refresh(gt.Request())
        _gtoken = creds.token
    return _gtoken


def synth_google(text, out_mp3, voice):
    body = json.dumps({"input": {"text": text},
                       "voice": {"languageCode": "tr-TR", "name": voice},
                       "audioConfig": {"audioEncoding": "MP3", "speakingRate": GOOGLE_RATE}}).encode()
    req = urllib.request.Request("https://texttospeech.googleapis.com/v1/text:synthesize",
                                 data=body, method="POST",
                                 headers={"Authorization": f"Bearer {_google_token()}",
                                          "Content-Type": "application/json"})
    resp = json.load(urllib.request.urlopen(req, timeout=30))
    open(out_mp3, "wb").write(base64.b64decode(resp["audioContent"]))


def synth_edge(text, out_mp3, voice):
    subprocess.run([sys.executable, "-m", "edge_tts", "--voice", voice, "--rate", EDGE_RATE,
                    "--text", text, "--write-media", out_mp3], check=True, capture_output=True)


def make_synth(engine, gvoice, evoice):
    if engine in ("auto", "google"):
        try:
            synth_google("Merhaba.", "/tmp/_probe.mp3", gvoice)
            return (lambda t, o: synth_google(t, o, gvoice)), f"google:{gvoice}"
        except Exception as e:
            if engine == "google":
                raise
            print(f"[i] Google TTS yok ({str(e)[:80]}) → edge")
    return (lambda t, o: synth_edge(t, o, evoice)), f"edge:{evoice}"


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", path],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


# ---------- whisper hizalama ----------

_wmodel = None


def transcribe_words(audio):
    global _wmodel
    if _wmodel is None:
        from faster_whisper import WhisperModel
        _wmodel = WhisperModel("base", device="cpu", compute_type="int8")
    segs, _ = _wmodel.transcribe(audio, language="tr", word_timestamps=True)
    return [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]


def _norm(s):
    return re.sub(r'[^0-9a-zğüşıöçâî]', '', s.lower().replace("İ", "i").replace("I", "ı"))


def align_words(script_words, ww):
    """script kelimelerine whisper zaman damgalarını difflib ile aktarır."""
    a = [_norm(w) for w in script_words]
    b = [_norm(w) for w, _, _ in ww]
    times = [None] * len(script_words)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                times[i1 + k] = (ww[j1 + k][1], ww[j1 + k][2])
        elif i2 > i1:
            if j2 > j1:
                t0, t1 = ww[j1][1], ww[j2 - 1][2]
            elif j1 > 0:
                t0 = t1 = ww[j1 - 1][2]
            else:
                t0 = t1 = (ww[0][1] if ww else 0.0)
            n = i2 - i1
            step = (t1 - t0) / n if n else 0
            for k in range(n):
                times[i1 + k] = (t0 + step * k, t0 + step * (k + 1))
    last = 0.0
    for i in range(len(times)):
        if times[i] is None:
            times[i] = (last, last + 0.25)
        last = times[i][1]
    return [(script_words[i], times[i][0], times[i][1]) for i in range(len(script_words))]


# ---------- karaoke / ASS ----------

def chunk_words(words, max_chars, max_words):
    chunks, cur, ln = [], [], 0
    for w in words:
        add = len(w) + (1 if cur else 0)
        if cur and (ln + add > max_chars or len(cur) >= max_words):
            chunks.append(cur); cur, ln = [], 0; add = len(w)
        cur.append(w); ln += add
        if w.endswith((".", "!", "?")) and len(cur) >= 2:
            chunks.append(cur); cur, ln = [], 0
    if cur:
        chunks.append(cur)
    return chunks


def ts(t):
    cs = max(0, int(round(t * 100)))
    h, cs = divmod(cs, 360000); m, cs = divmod(cs, 6000); s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def ass_escape(s):
    return s.replace("\\", "\\\\").replace("{", "(").replace("}", ")")


def build_ass(events, path):
    """events: [(start, end, [(word, k_cs), ...], big)]"""
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Kar,{ASS_FONT},94,{C_SUNG},{C_UNSUNG},{C_OUTLINE},{C_SHADOW},1,0,0,0,100,100,0.5,0,1,8,5,5,84,84,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [head]
    for start, end, chunk, big, ypos in events:
        ktext = "".join(f"{{\\k{max(1,k)}}}{ass_escape(w)} " for w, k in chunk).strip()
        fs = "\\fs118" if big else ""
        # v4: overshoot "pop" — 84 → 106 → 100 (CapCut tipik enerjik giriş)
        pre = (f"{{\\an5\\pos(540,{ypos}){fs}\\fad(70,55)\\fscx84\\fscy84"
               f"\\t(0,90,\\fscx106\\fscy106)\\t(90,180,\\fscx100\\fscy100)}}")
        lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},Kar,,0,0,0,,{pre}{ktext}")
    open(path, "w", encoding="utf-8").write("\n".join(lines))


# ---------- içerik-eşlemeli görsel seçimi ----------
# Segmentin KONUŞMASINDAN geçen finans kavramını yakalayıp ona özgü İngilizce
# Pexels arama terimi döndürür → ekrandaki görsel anlatılanla örtüşür (sabit havuz
# round-robin'inin "konuyla alakasız" sorununu çözer). Öncelik sırası = liste sırası.
CONCEPT_QUERIES = [
    (("düş", "çöküş", "çöker", "zarar", "kayb", "kaybe", "riskli", "dalgalan", "sert iniş"),
     "stock market crash red falling chart"),
    (("gram altın", "külçe", "altın", " ons", "ons "), "stacked gold bars wealth"),
    (("dolar", "euro", "sterlin", "döviz", "kur ", "parite", "usd"),
     "foreign currency exchange dollar euro"),
    (("borsa", "hisse", "bist", "endeks", "pay senedi", "temettü"),
     "stock market trading screen candlestick"),
    (("enflasyon", "zam", "pahalı", "hayat pahalılığı", "fiyat art"),
     "rising prices inflation grocery shopping"),
    (("faiz", "merkez bankas", "tcmb", "fed", "politika faiz"),
     "central bank interest rate building"),
    (("mevduat", "banka", "kredi", "hesap"), "bank counter counting money"),
    (("kripto", "bitcoin", "ethereum", "btc", "coin", "blokzincir"),
     "bitcoin cryptocurrency trading"),
    (("konut", "ev ", " ev.", "kira", "gayrimenkul", "emlak", "daire"),
     "real estate houses city aerial"),
    (("maaş", "asgari ücret", "gelir", "kazanç"), "counting salary cash hands"),
    (("tasarruf", "biriktir", "birikim", "kumbara"), "saving coins jar money"),
    (("vergi", "stopaj", "beyanname"), "tax documents calculator"),
    (("emekli", "emeklilik", "bes"), "retirement savings planning"),
    (("petrol", "doğalgaz", "enerji", "varil"), "oil barrels energy industry"),
    (("fabrika", "sanayi", "üretim", "ihracat"), "factory industry production line"),
    (("bütçe", "harcama", "tasarruf plan"), "budget planning finance desk"),
]
CONCEPT_FALLBACK = "financial charts money city"


def content_query(spoken, fallback=None):
    """Konuşma metnindeki ilk (en öncelikli) finans kavramına göre İngilizce
    Pexels sorgusu döndürür; hiçbiri yoksa fallback (yoksa jenerik finans)."""
    t = " " + (spoken or "").lower() + " "
    for keys, q in CONCEPT_QUERIES:
        if any(k in t for k in keys):
            return q
    return fallback or CONCEPT_FALLBACK


# ---------- B-roll (Pexels) ----------

def pexels_broll(query, out_path):
    """Sorgu için Pexels+Pixabay'dan (beraber) dikey stok video (cache'li). Başarısızsa None.
    İki kaynağı vv.stock_video rotasyonla kullanır → daha çok çeşit + dayanıklılık."""
    os.makedirs(BROLL_CACHE, exist_ok=True)
    cache = os.path.join(BROLL_CACHE, re.sub(r'\W+', '_', query) + ".mp4")
    if os.path.exists(cache) and os.path.getsize(cache) > 10000:
        return cache
    if vv.stock_video(query, cache) and os.path.exists(cache) and os.path.getsize(cache) > 10000:
        return cache
    return None


# ---------- overlay (marka çerçevesi) ----------

def vgrad_alpha(w, h, a_top, a_bot):
    img = Image.new("L", (w, h))
    px = img.load()
    for y in range(h):
        v = int(a_top + (a_bot - a_top) * (y / h))
        for x in range(w):
            px[x, y] = v
    return img


def _wrap_fit(d, text, font_path, max_w, max_size, min_size=56, max_lines=4):
    """Metni max_w genişliğine sığacak EN BÜYÜK fontta sar. (font, satırlar, boyut)."""
    words = text.split()
    best = None
    for size in range(max_size, min_size - 1, -4):
        f = fnt(font_path, size)
        lines, cur, overflow = [], "", False
        for w in words:
            trial = (cur + " " + w).strip()
            if d.textlength(trial, font=f) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
                if d.textlength(w, font=f) > max_w:
                    overflow = True
        if cur:
            lines.append(cur)
        best = (f, lines, size)
        if not overflow and len(lines) <= max_lines:
            return best
    return best  # sığmasa bile min boyutta en iyi denemeyi ver


def draw_hook_card(img, d, text):
    """v5: açılış swipe-stop kartı — kanca metnini ÜST-MERKEZE büyük/kalın bas.
    2026 Shorts verisi (retention↔views ≈ 0): izlenmeyi ilk kare belirler, gövde
    değil. Metin overlay PNG'ye gömülü olduğundan sahnenin başından (0.20s fade)
    görünür; kancanın alt karaoke'si bastırılır (çift metin olmasın)."""
    ht = (text or "").strip().rstrip(".!").strip()
    if not ht:
        return
    max_w = W - 2 * 108
    f, lines, size = _wrap_fit(d, ht, SANS_B, max_w, 112)
    lh = int(size * 1.16)
    block_h = lh * len(lines)
    y0 = max(720, 900 - block_h // 2)   # rozet (y≈500) altında, dikey merkez civarı
    # okunabilirlik için yarı saydam koyu plaka
    plate_w = min(W - 120, max(d.textlength(ln, font=f) for ln in lines) + 96)
    px0 = (W - plate_w) // 2
    plate = Image.new("RGBA", (int(plate_w), block_h + 72), (8, 11, 13, 165))
    img.alpha_composite(plate, (int(px0), y0 - 36))
    # sol kenarda marka aksan çubuğu
    d.rectangle([px0, y0 - 36, px0 + 12, y0 + block_h + 36], fill=(*BRAND, 255))
    y = y0
    for ln in lines:
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2)):
            d.text((W // 2 + dx, y + dy), ln, font=f, fill=(6, 9, 11, 235), anchor="ma")
        d.text((W // 2, y), ln, font=f, fill=(*WHITE, 255), anchor="ma")
        y += lh


def make_overlay(kind, eyebrow, path, hook_text=None):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # genel hafif karartma
    img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 16, 70)))
    # üst & alt scrim (okunabilirlik)
    top = Image.new("RGBA", (W, 520), (8, 12, 14, 0))
    top.putalpha(vgrad_alpha(W, 520, 150, 0))
    img.alpha_composite(top, (0, 0))
    bot = Image.new("RGBA", (W, 620), (8, 12, 14, 0))
    bot.putalpha(vgrad_alpha(W, 620, 0, 175))
    img.alpha_composite(bot, (0, H - 620))
    d = ImageDraw.Draw(img)
    # üst marka bandı
    d.rectangle([0, 0, W, 10], fill=(*BRAND, 255))
    # (kategori/eyebrow chip kaldırıldı — kullanıcı isteği 2026-06-28: kategori adı yazılmasın)
    # footer
    if os.path.exists(WORDMARK):
        wm = Image.open(WORDMARK).convert("RGBA")
        # beyaza boya (koyu zemin için)
        r, g, b, al = wm.split()
        wm = Image.merge("RGBA", (Image.new("L", wm.size, 255), Image.new("L", wm.size, 255),
                                  Image.new("L", wm.size, 255), al))
        th = 54
        wm = wm.resize((int(wm.width * th / wm.height), th), Image.LANCZOS)
        img.alpha_composite(wm, (M, H - 120))
    d.text((W - M, H - 92), "@parafomo", font=fnt(SANS_B, 34), fill=(*LIGHT, 255), anchor="rm")
    if kind == "hook" and hook_text:
        draw_hook_card(img, d, hook_text)
    if kind == "cta":
        # YouTube abone-odaklı kart: kırmızı "ABONE OL" butonu (play üçgeni) + marka satırı.
        bf = fnt(SANS_B, 62)
        label = "ABONE OL"
        bw = d.textlength(label, font=bf)
        pad_l, tri_w, gap, pad_r = 60, 46, 32, 56
        box_w = int(pad_l + tri_w + gap + bw + pad_r)
        x0 = (W - box_w) // 2
        y0, bh = 1320, 126
        d.rounded_rectangle([x0, y0, x0 + box_w, y0 + bh], radius=30, fill=(237, 28, 36, 255))
        cy = y0 + bh // 2
        tx = x0 + pad_l
        d.polygon([(tx, cy - 27), (tx, cy + 27), (tx + tri_w, cy)], fill=WHITE)  # play üçgeni
        d.text((tx + tri_w + gap, cy), label, font=bf, fill=WHITE, anchor="lm")
        # marka + site satırı
        d.text((W // 2, y0 + bh + 66), "@parafomo   ·   parafomo.com",
               font=fnt(SANS_B, 42), fill=(*LIGHT, 255), anchor="mm")
    img.save(path)


# ---------- ekran içi stat kartı (sayı vurgusu) ----------

def _tr_word_num(tok):
    tok = re.sub(r'[^a-zğüşıöç]', '', tok.lower())
    for k, v in NUM_WORDS.items():
        if tok == k or tok.startswith(k):
            return v
    return None


def _grp(n):
    return format(int(n), ",").replace(",", ".")


def extract_stat(text):
    """Cümleden en çarpıcı tek sayıyı bul → kısa etiket (yoksa None)."""
    t = text.lower()
    m = re.search(r'%\s?(\d+)', text)
    if m:
        return f"%{m.group(1)}"
    m = re.search(r'yüzde\s+([a-zğüşıöç]+)', t)
    if m:
        n = _tr_word_num(m.group(1))
        if n is not None:
            return f"%{n}"
    m = re.search(r'([\d][\d.\s]*\d|\d)\s*(lira|tl|₺)', t)
    if m:
        digits = re.sub(r'\D', '', m.group(1))
        if digits:
            return f"{_grp(digits)} TL"
    m = re.search(r'(\d+)\s*kat', t)
    if m:
        return f"{m.group(1)}x"
    m = re.search(r'\b(\d{3,})\b', text)
    if m:
        return _grp(m.group(1))
    return None


def make_stat_badge(text, path):
    """Yuvarlak köşeli, marka renkli, büyük sayı rozeti üretir (animasyon make_clip'te)."""
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    fs = 180
    for fs in (180, 158, 136, 116, 98):
        f = fnt(SANS_B, fs)
        tw = probe.textlength(text, font=f)
        if tw <= 740:
            break
    f = fnt(SANS_B, fs)
    tw = probe.textlength(text, font=f)
    padx, pady = 74, 40
    w, h = int(tw + padx * 2), int(fs + pady * 2)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=42, fill=(11, 16, 18, 234),
                        outline=(*BRAND, 255), width=9)
    d.rounded_rectangle([14, 14, w - 15, 24], radius=6, fill=(*LIGHT, 230))
    d.text((w // 2, h // 2 + 6), text, font=f, fill=(*LIGHT, 255), anchor="mm")
    img.save(path)


COUNTUP_SCRIPT = os.path.join(ROOT, "scripts", "countup-overlay.py")


def _num(v):
    """'6.657 TL' / 6657.0 / '%21' → float. TR biçim (binlik '.', ondalık ',') temizlenir."""
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d,.\-]", "", str(v))
    if not s:
        return None
    s = s.replace(".", "").replace(",", ".") if "," in s else s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def make_countup(chart, tmpdir):
    """backtest_return chart payload'ından animasyonlu start→end sayaç kareleri üretir
    ("motion earns the pause" — en yüksek skorlu format payoff'unu görselleştirir).
    Başarısızsa None (canlı hat asla kırılmaz)."""
    try:
        start = _num(chart.get("amount"))
        end = _num(chart.get("end_value"))
        if end is None and start is not None:
            pct = _num(chart.get("pct"))
            if pct is not None:
                end = start * (1 + pct / 100.0)
        if start is None or end is None or start <= 0 or abs(end - start) < 1:
            return None
        r = subprocess.run(
            [sys.executable, COUNTUP_SCRIPT, "--start", f"{start:.0f}", "--end", f"{end:.0f}",
             "--suffix", " TL", "--label", "BUGÜN", "--cy", "600", "--size", "170",
             "--dur", "2.2", "--hold", "0.8", "--fps", str(FPS), "--out", tmpdir],
            capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and os.path.isdir(tmpdir) and os.listdir(tmpdir):
            return tmpdir
        print(f"[i] count-up atlandı: {(r.stderr or r.stdout or '').strip()[:80]}")
    except Exception as e:
        print(f"[i] count-up üretilemedi: {str(e)[:80]}")
    return None


MANIM_SCENES = os.path.join(ROOT, "scripts", "manim_scenes.py")


def manim_scene(visual, dur, out_path):
    """visual.type=='manim' segmenti için Manim animasyon arka planı render eder
    (backtest_return payoff'unu stok yerine tam-vektör animasyonla gösterir).
    Başarısızsa None → çağıran Pexels/renksiz fallback'e düşer (canlı hat kırılmaz)."""
    try:
        scene = visual.get("scene", "backtest")
        cmd = [sys.executable, MANIM_SCENES, "--scene", scene,
               "--theme", visual.get("theme", "slate"), "--dur", f"{dur:.2f}", "--out", out_path]
        # veri-eğrisi sahnesi: chart payload'ından start/end çöz (yoksa render etme)
        if scene == "backtest":
            chart = visual.get("chart") or {}
            start = _num(chart.get("amount")); end = _num(chart.get("end_value"))
            if end is None and start is not None:
                pct = _num(chart.get("pct"))
                if pct is not None:
                    end = start * (1 + pct / 100.0)
            if not start or not end or start <= 0 or abs(end - start) < 1:
                return None
            cmd += ["--start", f"{start:.0f}", "--end", f"{end:.0f}"]
        if scene == "bigstat" and _num(visual.get("end")) is not None:
            cmd += ["--end", f"{_num(visual.get('end')):.0f}"]
        # düz metin/veri parametreleri (sahneye göre kullanılır; boşları geçme)
        for key in ("title", "sub", "keyword", "stat", "items", "label", "glyph", "suffix"):
            v = visual.get(key)
            if v not in (None, ""):
                cmd += [f"--{key}", str(v)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 2000:
            return out_path
        print(f"[i] manim atlandı: {(r.stderr or r.stdout or '').strip()[-160:]}")
    except Exception as e:
        print(f"[i] manim üretilemedi: {str(e)[:100]}")
    return None


def _kenburns(motion, D):
    """v4: sahne başına değişen kamera hareketi (zoom-in/out + pan) — statik
    'her klip aynı zoom' hissini kırar. Pencereler 9:16 kilitli (distorsiyon yok)."""
    p = f"min(t/{D}\\,1)"
    if motion == "hook":   # açılış: güçlü zoom-in (enerji)
        return (f"crop=w='1296-320*{p}':h='2304-569*{p}':"
                f"x='(in_w-out_w)/2':y='(in_h-out_h)/2'")
    if motion == "rehook":
        # v4.3: ~%50 ikincil hook (2026 retention: her 10-15sn'de bir re-hook/pattern-
        # interrupt "boredom clock"u sıfırlar, drop-off eğrisini düzleştirir). Sürekli
        # Ken Burns yerine HIZLI punch-in: ilk ~0.55sn'de tam kadrajdan sıkı kadraja
        # dalar, sonra sabitlenir → ani zoom = belirgin pattern-interrupt (kesim hissi).
        pr = f"min(t/0.55\\,1)"
        return (f"crop=w='1296-396*{pr}':h='2304-704*{pr}':"   # 1296→900 / 2304→1600 (9:16 kilitli)
                f"x='(in_w-out_w)/2':y='(in_h-out_h)/2'")
    # v4.1 micro-cut: uzun segmentlerde (>5sn) tek sürekli Ken Burns = >5sn statik
    # blok (2026 retention: "5-saniye kuralı" — hiçbir blok görsel değişmeden 5sn
    # geçmesin). Sahneyi ~2.7sn'lik alt-fazlara böl; her faz taze wide→tight zoom,
    # faz sınırında kadraj wide'a SNAP eder = kesim hissi (pattern-interrupt).
    try:
        durf = float(D)
    except (TypeError, ValueError):
        durf = 0.0
    if durf > 5.0:
        n = max(2, round(durf / 2.7))      # ~2.7sn/faz → 8sn'de 3 kesim
        seg = durf / n
        pw = f"min(mod(t\\,{seg:.3f})/{seg:.3f}\\,1)"
        # v4.2: her faz taze wide→tight zoom + faz-parite ile YATAY kadraj yönü
        # alternasyonu (2026 retention: sadece zoom tekrarı değil, görsel değişimin
        # TÜRÜNÜ de değiştir). Çift faz soldan→merkeze, tek faz sağdan→merkeze pan
        # eder → her faz FARKLI çekim gibi durur, faz-sınırı snapi karşı tarafa atlar.
        s = f"(2*mod(floor(t/{seg:.3f})\\,2)-1)"           # faz0:-1, faz1:+1, ...
        xf = f"(in_w-out_w)*(0.5-{s}*0.3*(1-{pw}))"        # frac ∈ [0.2,0.8], merkeze yaklaşır
        return (f"crop=w='1296-316*{pw}':h='2304-562*{pw}':"
                f"x='{xf}':y='(in_h-out_h)/2'")
    m = motion % 5
    if m == 0:             # zoom-in
        w, h, x, y = f"1296-216*{p}", f"2304-384*{p}", "(in_w-out_w)/2", "(in_h-out_h)/2"
    elif m == 1:           # zoom-out
        w, h, x, y = f"1080+216*{p}", f"1920+384*{p}", "(in_w-out_w)/2", "(in_h-out_h)/2"
    elif m == 2:           # sağa pan (sabit hafif zoom)
        w, h, x, y = "1148", "2040", f"(in_w-out_w)*{p}", "(in_h-out_h)/2"
    elif m == 3:           # sola pan
        w, h, x, y = "1148", "2040", f"(in_w-out_w)*(1-{p})", "(in_h-out_h)/2"
    else:                  # yukarı pan
        w, h, x, y = "1148", "2040", "(in_w-out_w)/2", f"(in_h-out_h)*(1-{p})"
    return f"crop=w='{w}':h='{h}':x='{x}':y='{y}'"


def make_clip(broll, audio, overlay, dur, out_clip, badge=None, motion=0, countup_dir=None):
    delay = int(LEAD * 1000)
    D = f"{dur:.3f}"
    bt = LEAD          # rozet konuşma başlarken belirir
    BY = 500           # rozet üst-orta; altyazıların üstünde
    inputs = []
    idx = 1            # [0] = video (broll/color)
    if broll:
        # v4: değişken Ken Burns + sinematik vignette/kontrast (stok 'düz' hissini azaltır)
        inputs += ["-stream_loop", "-1", "-t", D, "-i", broll]
        fc = (f"[0:v]scale=1296:2304:force_original_aspect_ratio=increase,crop=1296:2304,"
              f"{_kenburns(motion, D)},scale=1080:1920,setsar=1,fps=30,"
              f"eq=saturation=1.06:brightness=-0.05:contrast=1.07,vignette=PI/4.5,"
              f"fade=t=in:st=0:d=0.20[bg];")
    else:
        inputs += ["-f", "lavfi", "-t", D, "-i", "color=c=0x14323C:s=1080x1920"]
        fc = "[0:v]fps=30,fade=t=in:st=0:d=0.20[bg];"
    inputs += ["-i", audio]; aud_idx = str(idx); idx += 1
    inputs += ["-loop", "1", "-t", D, "-i", overlay]; ov_idx = str(idx); idx += 1
    # count-up varken bileşik video ara-etiket [vc]'ye yazılır (sonra sayaç bindirilir).
    pre = "vc" if countup_dir else "v"
    if badge:
        inputs += ["-loop", "1", "-t", D, "-i", badge]; bdg_idx = str(idx); idx += 1
        fc += f"[bg][{ov_idx}:v]overlay=0:0[vb];"
        fc += (f"[{bdg_idx}:v]format=rgba,fade=t=in:st={bt:.2f}:d=0.30:alpha=1[bdg];"
               f"[vb][bdg]overlay=x=(W-w)/2:"
               f"y='{BY}+70*max(0\\,1-(t-{bt:.2f})/0.32)':"
               f"enable='gte(t\\,{bt:.2f})'[{pre}];")
    else:
        fc += f"[bg][{ov_idx}:v]overlay=0:0[{pre}];"
    if countup_dir:
        # backtest_return payoff: animasyonlu sayaç (start→end) sahnenin üstüne biner.
        # setpts ile konuşma başlarken (bt+0.15) girer; biter bitmez son kare donar.
        cst = bt + 0.15
        inputs += ["-framerate", str(FPS), "-i", os.path.join(countup_dir, "frame_%04d.png")]
        cu_idx = str(idx); idx += 1
        fc += (f"[{cu_idx}:v]format=rgba,setpts=PTS-STARTPTS+{cst:.2f}/TB[cu];"
               f"[vc][cu]overlay=0:0:eof_action=repeat[v];")
    fc += f"[{aud_idx}:a]adelay={delay}|{delay},apad=whole_dur={dur}[a]"
    subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-t", D, "-c:v", "libx264", "-r", str(FPS), "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-ar", "44100", out_clip],
                   check=True, capture_output=True)


def make_loop_tail(first_clip, out, dur=0.4):
    """Loop-friendly kapanış: ilk klibin açılış karesini kısa bir sessiz dilim olarak sona
    ekler. YouTube videoyu otomatik döngüye aldığında son kare ≈ ilk kare olur → sorunsuz
    loop, rewatch'i (tekrar-izlenme) artırır. 2026 Shorts retention araştırması: 'loopable
    ending' 3 tartışılmaz öğeden biri, rewatch'i besler. Başarısızsa None → hat asla kırılmaz."""
    try:
        png = f"{TMP}/loopstart.png"
        subprocess.run(["ffmpeg", "-y", "-i", first_clip, "-frames:v", "1", png],
                       check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-t", f"{dur:.2f}", "-i", png,
                        "-f", "lavfi", "-t", f"{dur:.2f}", "-i", "anullsrc=r=44100:cl=stereo",
                        "-vf", f"scale={W}:{H},setsar=1,fps={FPS},format=yuv420p",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                        "-ar", "44100", "-shortest", out], check=True, capture_output=True)
        return out if os.path.exists(out) else None
    except Exception as e:
        print(f"[i] loop-tail atlandı: {str(e)[:80]}")
        return None


def gen_pad(dur, path):
    inputs = []
    for f in (220.0, 277.16, 329.63, 164.81):
        inputs += ["-f", "lavfi", "-t", f"{dur:.2f}", "-i", f"sine=frequency={f}"]
    fc = ("[0:a][1:a][2:a][3:a]amix=inputs=4,tremolo=f=0.18:d=0.5,lowpass=f=520,"
          "highpass=f=70,aecho=0.6:0.5:120:0.3,volume=0.5,"
          f"afade=t=in:st=0:d=2,afade=t=out:st={max(0,dur-2):.2f}:d=2[a]")
    subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[a]",
                    "-c:a", "mp3", path], check=True, capture_output=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--scenario", default=None,
                    help="Bağımsız viral senaryo JSON'u (blog yerine). Beat başına görsel içerir.")
    ap.add_argument("--engine", default="auto", choices=["auto", "google", "edge"])
    ap.add_argument("--voice", default=None)
    ap.add_argument("--edge-voice", default=EDGE_VOICE)
    ap.add_argument("--no-music", action="store_true")
    ap.add_argument("--no-broll", action="store_true")
    args = ap.parse_args()

    # Kaynak: bağımsız viral senaryo JSON'u VEYA blog yazısı frontmatter'ı.
    front = ""
    scenario = None
    seg_visuals = []      # beat başına {type, query} veya None
    meta_desc = ""
    meta_tags = ["finans", "yatırım", "para", "ekonomi", "parafomo"]
    blog_link = True
    if args.scenario:
        scenario = json.load(open(args.scenario, encoding="utf-8"))
        title = scenario["title"]
        segs = [(s.get("kind", "point"), s.get("eyebrow", ""), s["spoken"])
                for s in scenario["segments"]]
        seg_visuals = [s.get("visual") for s in scenario["segments"]]
        broll_kw = None
        meta_desc = scenario.get("description", "")
        meta_tags = scenario.get("tags") or meta_tags
        blog_link = False
    else:
        path = os.path.join(BLOG, f"{args.slug}.md")
        if not os.path.exists(path):
            print(f"HATA: yazı yok: {path}"); return 1
        front = open(path, encoding="utf-8").read().split("---", 2)[1]
        title, segs = build_segments(front)
        broll_kw = parse_list(front, "shorts_broll") or BROLL_POOL
        seg_visuals = [None] * len(segs)
        meta_desc = fm(front, "description")
    synth, label = make_synth(args.engine, args.voice or GOOGLE_VOICE, args.edge_voice)
    print(f"[*] '{title}' → {len(segs)} segment, ses: {label}")

    os.makedirs(TMP, exist_ok=True); os.makedirs(OUT_DIR, exist_ok=True)
    for f in os.listdir(TMP):
        p = os.path.join(TMP, f)
        shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else os.remove(p)

    clips, events, tcur, credits = [], [], 0.0, []
    # v4.3 ikincil hook: ~orta beat'e mid-video pattern-interrupt (punch-in). Yeterli
    # beat varsa (>=4) uygula; hook (0) ve son/CTA beat'i (len-1) hariç, ortadaki beat.
    rehook_idx = (len(segs) // 2) if len(segs) >= 4 else -1
    for i, (kind, eyebrow, spoken) in enumerate(segs):
        aud = f"{TMP}/aud{i:02d}.mp3"
        ov = f"{TMP}/ov{i:02d}.png"
        synth(spoken, aud)
        ad = duration(aud)
        make_overlay(kind, eyebrow, ov, hook_text=(spoken if kind == "hook" else None))
        clip_dur = LEAD + ad + TAIL
        # B-roll: senaryo beat'inde görsel spec'i varsa onu çöz (Wikimedia/Pexels),
        # yoksa eski yol (shorts_broll anahtar kelimeleriyle Pexels).
        brollpath = f"{TMP}/broll{i:02d}.mp4"
        broll = None
        visual = seg_visuals[i] if i < len(seg_visuals) else None
        is_manim = bool(visual and visual.get("type") == "manim")
        if args.no_broll:
            broll = None
        elif is_manim:
            # Manim animasyon sahnesi arka plan olur; düşerse stok B-roll'e geri düş.
            broll = manim_scene(visual, clip_dur, brollpath)
            if broll is None:
                broll = pexels_broll(visual.get("query") or "financial data chart", brollpath)
        elif visual and visual.get("query"):
            # concept/scene (soyut stok) beat'lerinde görseli KONUŞMAYLA eşle;
            # person/place/logo/gold/object gibi spesifik tipler olduğu gibi kalır.
            v = visual
            if (v.get("type") or "").lower() in ("concept", "scene"):
                v = {**v, "query": content_query(spoken, v.get("query"))}
            broll, attr = vv.resolve(v, clip_dur, brollpath)
            if attr and attr.get("need_attribution") and attr.get("credit"):
                credits.append(attr["credit"])
        else:
            # blog yolu: sabit havuzu sırayla basmak yerine segmentin içeriğine eşle.
            query = content_query(spoken, broll_kw[i % len(broll_kw)] if broll_kw else None)
            broll = pexels_broll(query, brollpath) if query else None
        # ekran içi sayı vurgusu (CTA hariç) — finans Shorts'unda en yüksek etkili öğe.
        # chart/manim görselinde sayı zaten gösterilir → rozet eklenmez (çakışma olmasın).
        is_chart = bool(visual and visual.get("type") == "chart")
        stat = extract_stat(spoken) if (kind != "cta" and not is_chart and not is_manim) else None
        badge = None
        if stat:
            badge = f"{TMP}/badge{i:02d}.png"
            make_stat_badge(stat, badge)
        # backtest_return payoff (chart beat): statik grafik üstüne animasyonlu count-up sayaç.
        countup_dir = None
        if (scenario and scenario.get("format") == "backtest_return"
                and is_chart and isinstance((visual or {}).get("chart"), dict)):
            countup_dir = make_countup(visual["chart"], f"{TMP}/cu{i:02d}")
        clip = f"{TMP}/clip{i:02d}.mp4"
        # v4: sahne başına değişen hareket; Manim sahnesi kendi animasyonlu → Ken Burns kapalı
        # v4.3: orta beat (rehook_idx) → mid-video punch-in pattern-interrupt. Manim/count-up
        # beat'i kendi animasyonuna sahip → dokunma (rehook yalnız düz b-roll/color beat'te).
        if is_manim:
            motion = 0
        elif kind == "hook":
            motion = "hook"
        elif i == rehook_idx and not countup_dir:
            motion = "rehook"
        else:
            motion = i
        try:
            make_clip(broll, aud, ov, clip_dur, clip, badge=badge, motion=motion,
                      countup_dir=countup_dir)
        except subprocess.CalledProcessError:
            if countup_dir:   # sayaç hattı kırıldıysa asla videoyu düşürme — sayaçsız yeniden
                print("[i] count-up'lı klip başarısız → sayaçsız yeniden kur")
                make_clip(broll, aud, ov, clip_dur, clip, badge=badge, motion=motion)
            else:
                raise
        clips.append(clip)

        # gerçek senkron: whisper → hizala → karaoke chunk
        ww = transcribe_words(aud)
        words = [w for w in spoken.split() if re.search(r'\w', w)]
        aligned = align_words(words, ww) if ww else [(w, j * ad / max(1, len(words)),
                                                      (j + 1) * ad / max(1, len(words)))
                                                     for j, w in enumerate(words)]
        big = (kind == "hook")
        # altyazı alt kısımda; CTA'da alttaki parafomo.com/buton ile çakışmasın diye yukarıda
        ypos = 1330 if kind == "hook" else (1040 if kind == "cta" else 1450)
        mc, mw = (12, 3) if big else (18, 4)
        gstart = tcur + LEAD
        idx = 0
        # Kanca segmentinde alt karaoke YOK: metin zaten üst-merkezdeki büyük swipe-stop
        # kartında (draw_hook_card) statik gösteriliyor; karaoke = çift metin/kalabalık olurdu.
        for ch in ([] if kind == "hook" else chunk_words(words, mc, mw)):
            n = len(ch); part = aligned[idx:idx + n]; idx += n
            cstart = gstart + part[0][1]
            cend = gstart + part[-1][2] + 0.12
            kk = []
            for j, (w, st, en) in enumerate(part):
                nxt = part[j + 1][1] if j + 1 < n else en
                kk.append((w, max(1, int(round((nxt - st) * 100)))))
            events.append((cstart, cend, kk, big, ypos))
        tcur += clip_dur
        print(f"    [{kind:5}] {clip_dur:4.1f}sn  broll={'✓' if broll else '—'}"
              f"  stat={stat or '—':>7}  {spoken[:38]}")

    # Loop-friendly kapanış: ilk klibin açılış karesini ~0.4sn sona ekle → YouTube loop'unda
    # son kare ≈ ilk kare, sorunsuz döngü (rewatch artışı). Savunmacı: düşerse eklenmez.
    if len(clips) >= 2 and not args.no_broll:
        tail = make_loop_tail(clips[0], f"{TMP}/looptail.mp4")
        if tail:
            clips.append(tail)
            print("    [loop ] 0.4sn  açılış karesine dönüş (seamless loop)")

    lst = f"{TMP}/list.txt"
    open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))
    joined = f"{TMP}/joined.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                    "-ar", "44100", "-movflags", "+faststart", joined], check=True, capture_output=True)
    total = duration(joined)

    assf = f"{TMP}/cap.ass"; build_ass(events, assf)
    music = None
    if not args.no_music:
        if os.path.exists(MUSIC):
            music = MUSIC
        else:
            music = f"{TMP}/pad.mp3"; gen_pad(total + 1, music)
            print("[i] Gerçek müzik yok → geçici pad")

    out = os.path.join(OUT_DIR, f"short-{args.slug}.mp4")
    sub = f"subtitles={assf}:fontsdir={FONTSDIR}"
    if music:
        fc = (f"[0:v]{sub}[v];[1:a]volume=0.13[bed];"
              f"[bed][0:a]sidechaincompress=threshold=0.03:ratio=10:attack=15:release=350[d];"
              f"[0:a][d]amix=inputs=2:duration=first:dropout_transition=0[a]")
        subprocess.run(["ffmpeg", "-y", "-i", joined, "-stream_loop", "-1", "-i", music,
                        "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                        "-movflags", "+faststart", "-shortest", out], check=True, capture_output=True)
    else:
        subprocess.run(["ffmpeg", "-y", "-i", joined, "-vf", sub, "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", out],
                       check=True, capture_output=True)

    total = duration(out); sz = os.path.getsize(out) / 1024
    print(f"[+] Short: {out}  ({total:.0f}sn, {sz:.0f} KB)")
    if total > 60:
        print(f"[!] {total:.0f}sn > 60 — senaryoyu kısalt")

    tagline = " ".join("#" + t for t in meta_tags[:5]) or "#finans #yatırım"
    if blog_link:
        desc = f"{meta_desc}\n\nTüm yazı: https://parafomo.com/blog/{args.slug}/\n\n#Shorts {tagline}"
    else:
        desc = f"{meta_desc}\n\nDaha fazlası: https://parafomo.com\n\n#Shorts {tagline}"
    # CC-BY görseller için atıf (kamu malı / CC0 atıf gerektirmez, eklenmez)
    if credits:
        desc += "\n\nGörseller: " + " · ".join(dict.fromkeys(credits))
    meta = {"title": title[:90] + " #Shorts",
            "description": desc,
            "tags": meta_tags,
            "file": out, "slug": args.slug,
            "format": (scenario.get("format", "") if scenario else "")}
    json.dump(meta, open(os.path.join(OUT_DIR, f"short-{args.slug}.json"), "w",
                         encoding="utf-8"), ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
