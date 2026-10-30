"""Uzun-form (16:9) video hattının ortak sabitleri ve yardımcıları.

Shorts hattından (shorts-build-v4.py) bilinçli olarak AYRI: dikey varsayımlar orada sabit kodlu,
burada her şey 1920x1080 için. Marka sesi Orus (parafomo-shorts-preferences).
"""
import base64
import hashlib
import json
import os
import subprocess
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "public", "social", "longform")
WORK = "/root/.cache/parafomo/longform"          # TTS önbelleği + ara dosyalar (repo dışı)
MUSIC_DIR = "/root/parafomo-media/music"
SA_JSON = "/root/.config/parafomo/ga-sa.json"

W, H, FPS = 1920, 1080, 30

# Marka paleti (logo/renk paleti.png) + vurgu renkleri
BG = (15, 19, 22)
BG2 = (22, 28, 33)
PANEL = (28, 36, 42)
LINE = (52, 64, 72)
BRAND = (43, 177, 148)       # #2BB194
LIGHT = (99, 212, 145)       # #63D491
DEEP = (30, 107, 127)        # #1E6B7F
GOLD = (255, 201, 77)        # rakam vurgusu
RED = (227, 18, 11)          # "BELLİ OLDU" / uyarı bloğu (Economist kırmızısı)
WHITE = (244, 246, 245)
MUTED = (154, 165, 161)

FONT_DIR = os.path.join(ROOT, "assets", "fonts")
ANTON = os.path.join(FONT_DIR, "Anton-Regular.ttf")
OSWALD = os.path.join(FONT_DIR, "Oswald.ttf")
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

VOICE = "tr-TR-Chirp3-HD-Orus"
RATE = 1.08          # uzun-formda Shorts'tan (1.15) biraz sakin


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path])
    return float(r.stdout.strip())


_tok = None


def _google_token():
    global _tok
    if not _tok:
        from google.oauth2 import service_account
        import google.auth.transport.requests as gt
        creds = service_account.Credentials.from_service_account_file(
            SA_JSON, scopes=["https://www.googleapis.com/auth/cloud-platform"])
        creds.refresh(gt.Request())
        _tok = creds.token
    return _tok


def tts(text, voice=VOICE, rate=RATE):
    """Metni seslendir → önbellekteki mp3 yolu. Aynı metin+ses+hız tekrar üretilmez
    (QA yeniden-render'ında ses değişmez, ücret tekrar etmez)."""
    os.makedirs(os.path.join(WORK, "tts"), exist_ok=True)
    key = hashlib.sha1(f"{voice}|{rate}|{text}".encode()).hexdigest()[:16]
    out = os.path.join(WORK, "tts", f"{key}.mp3")
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        return out
    body = json.dumps({"input": {"text": text},
                       "voice": {"languageCode": "tr-TR", "name": voice},
                       "audioConfig": {"audioEncoding": "MP3", "speakingRate": rate,
                                       "sampleRateHertz": 48000}}).encode()
    req = urllib.request.Request("https://texttospeech.googleapis.com/v1/text:synthesize",
                                 data=body, method="POST",
                                 headers={"Authorization": f"Bearer {_google_token()}",
                                          "Content-Type": "application/json"})
    resp = json.load(urllib.request.urlopen(req, timeout=60))
    with open(out, "wb") as f:
        f.write(base64.b64decode(resp["audioContent"]))
    return out


def tr_num(x, dec=0):
    """1234.5 → '1.234,5' (Türkçe biçim)."""
    s = f"{x:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")
