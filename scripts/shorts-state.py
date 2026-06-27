#!/usr/bin/env python3
"""
ParaFOMO — Shorts otomasyon durumu (kuyruk + ses rotasyonu).

Durum dosyası: logs/shorts-state.json (gitignore'lu) → {"done": [...], "voice_index": N}
Her gün 2 Shorts yayınlanır: biri EN YENİ (o günkü blog yazısıyla senkron),
biri EN ESKİ işlenmemiş yazı (backlog'u eritir). İkisi ortada buluşunca doğal
olarak günde 1'e iner. Her işte FARKLI ses (VOICES listesinde sırayla döner).

Komutlar:
  next [newest|oldest]   → "<slug>\t<voice>"  (işlenecek yazı yoksa boş)
                           varsayılan: oldest (geriye dönük uyumluluk)
  commit <slug>          → slug'ı done'a ekle, voice_index'i artır
"""
import os
import re
import sys
import json
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG = os.path.join(ROOT, "src", "content", "blog")
STATE = os.path.join(ROOT, "logs", "shorts-state.json")

# günlük rotasyon — Chirp3-HD sesleri (kadın/erkek karışık); her gün biri kullanılır.
# Amaç: kullanıcı her sesi tek tek dinleyip karar versin → henüz DENENMEMİŞ 24 ses sırada.
# Denenip BEĞENİLMEYEN (bir daha kullanılmayacak): Despina, Leda, Aoede, Puck — 2026-06-26.
# Denenip kullanılmaya devam edenler (rotasyon dışı, beğenildi): Orus, Schedar.
VOICES = [
    "tr-TR-Chirp3-HD-Achernar",
    "tr-TR-Chirp3-HD-Achird",
    "tr-TR-Chirp3-HD-Algenib",
    "tr-TR-Chirp3-HD-Algieba",
    "tr-TR-Chirp3-HD-Alnilam",
    "tr-TR-Chirp3-HD-Autonoe",
    "tr-TR-Chirp3-HD-Callirrhoe",
    "tr-TR-Chirp3-HD-Charon",
    "tr-TR-Chirp3-HD-Enceladus",
    "tr-TR-Chirp3-HD-Erinome",
    "tr-TR-Chirp3-HD-Fenrir",
    "tr-TR-Chirp3-HD-Gacrux",
    "tr-TR-Chirp3-HD-Iapetus",
    "tr-TR-Chirp3-HD-Kore",
    "tr-TR-Chirp3-HD-Laomedeia",
    "tr-TR-Chirp3-HD-Pulcherrima",
    "tr-TR-Chirp3-HD-Rasalgethi",
    "tr-TR-Chirp3-HD-Sadachbia",
    "tr-TR-Chirp3-HD-Sadaltager",
    "tr-TR-Chirp3-HD-Sulafat",
    "tr-TR-Chirp3-HD-Umbriel",
    "tr-TR-Chirp3-HD-Vindemiatrix",
    "tr-TR-Chirp3-HD-Zephyr",
    "tr-TR-Chirp3-HD-Zubenelgenubi",
]


def load():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {"done": [], "voice_index": 0}


def save(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(s, open(STATE, "w"), ensure_ascii=False, indent=2)


def articles_by_date():
    out = []
    for f in glob.glob(os.path.join(BLOG, "*.md")):
        raw = open(f, encoding="utf-8").read()
        front = raw.split("---", 2)[1] if "---" in raw else ""
        if re.search(r'^draft:\s*true', front, re.MULTILINE):
            continue
        m = re.search(r'^pubDate:\s*(\S+)', front, re.MULTILINE)
        date = m.group(1) if m else "9999-99-99"
        out.append((date, os.path.basename(f)[:-3]))
    return [slug for _, slug in sorted(out)]


def main():
    if len(sys.argv) < 2:
        print("kullanım: shorts-state.py next|commit <slug>"); return 1
    cmd = sys.argv[1]
    s = load()
    if cmd == "next":
        # konum: oldest (varsayılan, backlog) | newest (güncel blog yazısı)
        where = sys.argv[2] if len(sys.argv) > 2 else "oldest"
        done = set(s["done"])
        queue = [slug for slug in articles_by_date() if slug not in done]
        if not queue:
            return 0  # kuyruk boş
        slug = queue[-1] if where == "newest" else queue[0]
        print(f"{slug}\t{VOICES[s['voice_index'] % len(VOICES)]}")
        return 0
    if cmd == "commit":
        slug = sys.argv[2]
        if slug not in s["done"]:
            s["done"].append(slug)
        s["voice_index"] = s.get("voice_index", 0) + 1
        save(s)
        print(f"[+] commit: {slug} (toplam {len(s['done'])}, sıradaki ses index {s['voice_index']})")
        return 0
    print("bilinmeyen komut"); return 1


if __name__ == "__main__":
    sys.exit(main())
