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
import base64
import difflib
import argparse
import subprocess
import urllib.request
import urllib.parse
from PIL import Image, ImageDraw, ImageFont

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
GOOGLE_RATE = 1.05
EDGE_RATE = "+6%"
LEAD = 0.45
TAIL = 0.55
FPS = 30

# koyu B-roll üstünde okunan altyazı renkleri (&HAABBGGRR)
C_SUNG = "&H0063D463"    # açık yeşil (okunmuş/aktif)
C_UNSUNG = "&H00FFFFFF"  # beyaz (okunmamış)
C_OUTLINE = "&H00121712"  # koyu hale
C_SHADOW = "&HA0000000"

# konuya göre Pexels arama havuzu (İngilizce; finans B-roll her konuya uyar)
BROLL_POOL = ["stock market", "city skyline aerial", "money cash counting",
              "financial district night", "trading charts screen", "business people walking"]


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
        hook, cta = custom[0], (custom[-1] if len(custom) > 2 else "Tümü parafomo.com'da. Takip et!")
        points = custom[1:-1] if len(custom) > 2 else custom[1:]
        segs.append(("hook", category, hook))
        for i, p in enumerate(points[:4], 1):
            segs.append(("point", f"{i}", p))
        segs.append(("cta", "", cta))
        return title, segs
    faq = parse_faq(front)[:3]
    hk = re.sub(r'\s+', ' ', title).strip()
    segs.append(("hook", category, hk if hk.endswith(("?", ".", "!")) else hk + "."))
    for i, (q, a) in enumerate(faq, 1):
        segs.append(("point", f"{i}/{len(faq)}", f"{q.rstrip('?')}? {first_sentences(a,1)}"))
    segs.append(("cta", "", "Tüm detaylar parafomo.com'da. Takip et, paranı büyüt!"))
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
Style: Kar,{ASS_FONT},98,{C_SUNG},{C_UNSUNG},{C_OUTLINE},{C_SHADOW},1,0,0,0,100,100,0,0,1,7,4,5,70,70,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [head]
    for start, end, chunk, big, ypos in events:
        ktext = "".join(f"{{\\k{max(1,k)}}}{ass_escape(w)} " for w, k in chunk).strip()
        fs = "\\fs118" if big else ""
        pre = (f"{{\\an5\\pos(540,{ypos}){fs}\\fad(80,60)"
               f"\\t(0,120,\\fscx100\\fscy100)\\fscx92\\fscy92}}")
        lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},Kar,,0,0,0,,{pre}{ktext}")
    open(path, "w", encoding="utf-8").write("\n".join(lines))


# ---------- B-roll (Pexels) ----------

def pexels_broll(query, out_path):
    """Sorgu için dikey stok video indirir (cache'li). Başarısızsa None."""
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return None
    os.makedirs(BROLL_CACHE, exist_ok=True)
    cache = os.path.join(BROLL_CACHE, re.sub(r'\W+', '_', query) + ".mp4")
    if os.path.exists(cache) and os.path.getsize(cache) > 10000:
        return cache
    UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    try:
        url = ("https://api.pexels.com/videos/search?orientation=portrait&size=medium&per_page=8&query="
               + urllib.parse.quote(query))
        req = urllib.request.Request(url, headers={"Authorization": key, "User-Agent": UA})
        data = json.load(urllib.request.urlopen(req, timeout=20))
        vids = data.get("videos", [])
        if not vids:
            return None
        # 1080x1920'ye en yakın dikey dosyayı seç
        best = None
        for v in vids:
            for f in v["video_files"]:
                h = f.get("height") or 0
                w = f.get("width") or 0
                if h >= w and 1080 <= h <= 2200:
                    score = abs(h - 1920)
                    if best is None or score < best[0]:
                        best = (score, f["link"])
        if not best:
            f = max(vids[0]["video_files"], key=lambda f: f.get("height", 0))
            best = (0, f["link"])
        dreq = urllib.request.Request(best[1], headers={"User-Agent": UA})
        with urllib.request.urlopen(dreq, timeout=60) as r, open(cache, "wb") as o:
            o.write(r.read())
        return cache
    except Exception as e:
        print(f"[i] Pexels '{query}' alınamadı: {str(e)[:70]}")
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


def make_overlay(kind, eyebrow, path):
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
    # eyebrow chip
    if eyebrow:
        cf = fnt(SANS_B, 36)
        tw = d.textlength(eyebrow, font=cf)
        d.rounded_rectangle([M, 70, M + tw + 60, 70 + 70], radius=35, fill=(*BRAND, 255))
        d.text((M + 30, 105), eyebrow, font=cf, fill=WHITE, anchor="lm")
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
    if kind == "cta":
        d.text((W // 2, 1340), "parafomo.com", font=fnt(SERIF_B, 92), fill=WHITE, anchor="mm")
        bf = fnt(SANS_B, 44)
        txt = "Takip et  @parafomo"
        bw = d.textlength(txt, font=bf)
        d.rounded_rectangle([(W - bw) // 2 - 46, 1430, (W + bw) // 2 + 46, 1430 + 92],
                            radius=46, fill=(*BRAND, 255))
        d.text((W // 2, 1476), txt, font=bf, fill=WHITE, anchor="mm")
    img.save(path)


def make_clip(broll, audio, overlay, dur, out_clip):
    delay = int(LEAD * 1000)
    if broll:
        vin = ["-stream_loop", "-1", "-t", f"{dur:.3f}", "-i", broll]
        vsrc = ("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,fps=30,eq=saturation=1.08:brightness=-0.03[bg];")
        aud_idx, ov_idx = "1", "2"
    else:
        vin = ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "color=c=0x1E6B7F:s=1080x1920"]
        vsrc = "[0:v]fps=30[bg];"
        aud_idx, ov_idx = "1", "2"
    fc = (vsrc + f"[bg][{ov_idx}:v]overlay=0:0[v];"
          f"[{aud_idx}:a]adelay={delay}|{delay},apad=whole_dur={dur}[a]")
    subprocess.run(["ffmpeg", "-y", *vin, "-i", audio, "-loop", "1", "-t", f"{dur:.3f}",
                    "-i", overlay, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-t", f"{dur:.3f}", "-c:v", "libx264", "-r", str(FPS), "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-ar", "44100", out_clip],
                   check=True, capture_output=True)


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
    ap.add_argument("--engine", default="auto", choices=["auto", "google", "edge"])
    ap.add_argument("--voice", default=None)
    ap.add_argument("--edge-voice", default=EDGE_VOICE)
    ap.add_argument("--no-music", action="store_true")
    ap.add_argument("--no-broll", action="store_true")
    args = ap.parse_args()

    path = os.path.join(BLOG, f"{args.slug}.md")
    if not os.path.exists(path):
        print(f"HATA: yazı yok: {path}"); return 1
    front = open(path, encoding="utf-8").read().split("---", 2)[1]
    title, segs = build_segments(front)
    broll_kw = parse_list(front, "shorts_broll") or BROLL_POOL
    synth, label = make_synth(args.engine, args.voice or GOOGLE_VOICE, args.edge_voice)
    print(f"[*] '{title}' → {len(segs)} segment, ses: {label}")

    os.makedirs(TMP, exist_ok=True); os.makedirs(OUT_DIR, exist_ok=True)
    for f in os.listdir(TMP):
        os.remove(os.path.join(TMP, f))

    clips, events, tcur = [], [], 0.0
    for i, (kind, eyebrow, spoken) in enumerate(segs):
        aud = f"{TMP}/aud{i:02d}.mp3"
        ov = f"{TMP}/ov{i:02d}.png"
        synth(spoken, aud)
        ad = duration(aud)
        make_overlay(kind, eyebrow, ov)
        query = broll_kw[i % len(broll_kw)] if not args.no_broll else None
        broll = pexels_broll(query, f"{TMP}/broll{i:02d}.mp4") if query else None
        clip_dur = LEAD + ad + TAIL
        clip = f"{TMP}/clip{i:02d}.mp4"
        make_clip(broll, aud, ov, clip_dur, clip)
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
        mc, mw = (14, 3) if big else (22, 4)
        gstart = tcur + LEAD
        idx = 0
        for ch in chunk_words(words, mc, mw):
            n = len(ch); part = aligned[idx:idx + n]; idx += n
            cstart = gstart + part[0][1]
            cend = gstart + part[-1][2] + 0.12
            kk = []
            for j, (w, st, en) in enumerate(part):
                nxt = part[j + 1][1] if j + 1 < n else en
                kk.append((w, max(1, int(round((nxt - st) * 100)))))
            events.append((cstart, cend, kk, big, ypos))
        tcur += clip_dur
        print(f"    [{kind:5}] {clip_dur:4.1f}sn  broll={'✓' if broll else '—'}  {spoken[:42]}")

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
        fc = (f"[0:v]{sub}[v];[1:a]volume=0.10[bed];"
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

    meta = {"title": title[:90] + " #Shorts",
            "description": f"{fm(front,'description')}\n\nTüm yazı: https://parafomo.com/blog/{args.slug}/\n\n#Shorts #finans #yatırım #parafomo",
            "tags": ["finans", "yatırım", "para", "ekonomi", "parafomo"],
            "file": out, "slug": args.slug}
    json.dump(meta, open(os.path.join(OUT_DIR, f"short-{args.slug}.json"), "w",
                         encoding="utf-8"), ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
