#!/usr/bin/env python3
"""
ParaFOMO — Shorts senaryosu üretici (Claude headless).

Bir blog yazısını okur, `claude -p` ile konuşma diline/40-45sn'ye optimize bir
YouTube Shorts senaryosu üretir ve yazının frontmatter'ına KALICI yazar:
  shorts:        [kanca, vuruş1, vuruş2, vuruş3, CTA]
  shorts_broll:  [4 İngilizce stok-video arama terimi]

Zaten `shorts:` varsa atlar (--force ile yeniden üretir).
Kullanım: python3 scripts/shorts-script.py <slug> [--force]
Çıkış kodu: 0 başarı, 1 hata (çağıran auto-FAQ'e düşebilir).
"""
import os
import re
import sys
import json
import argparse
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG = os.path.join(ROOT, "src", "content", "blog")

PROMPT = """Sen bir Türk finans kanalı için YouTube Shorts senaryosu yazıyorsun.
Aşağıdaki blog yazısından 40-45 saniyelik, akıcı, KONUŞMA dilinde bir senaryo çıkar.

Kurallar:
- hook: ilk 2 saniyede izleyiciyi durduran, merak uyandıran KISA cümle (en fazla 9 kelime). Soru veya çarpıcı ifade.
- beats: tam 3 madde. Her biri yazının bir ana fikrini anlatan, tek başına anlaşılır, akıcı Türkçe cümle (12-20 kelime). Kopuk ifade YOK.
- cta: izleyiciyi siteye/takibe çağıran kısa cümle. "parafomo.com" geçsin.
- broll: konuyla ilgili 4 adet İngilizce stok video arama terimi (örn. "stock market chart", "turkish lira money").
- Sade, net, abartısız. Tıklama tuzağı değil, değer ver.

SADECE şu JSON'u döndür, başka HİÇBİR şey yazma (markdown, ``` , açıklama YOK):
{"hook": "...", "beats": ["...", "...", "..."], "cta": "...", "broll": ["...","...","...","..."]}

--- YAZI ---
Başlık: %(title)s
Kategori: %(category)s

%(body)s
"""


def yaml_q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').strip() + '"'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--model", default="claude-sonnet-4-6")
    args = ap.parse_args()

    path = os.path.join(BLOG, f"{args.slug}.md")
    if not os.path.exists(path):
        print(f"HATA: yazı yok: {path}"); return 1
    raw = open(path, encoding="utf-8").read()
    parts = raw.split("---", 2)
    if len(parts) < 3:
        print("HATA: frontmatter ayrıştırılamadı"); return 1
    front, body = parts[1], parts[2]

    if re.search(r'^shorts:\s*$', front, re.MULTILINE) and not args.force:
        print(f"[i] {args.slug}: shorts: zaten var, atlanıyor (--force ile yenile)")
        return 0

    title = (re.search(r'^title:\s*"?(.*?)"?\s*$', front, re.M) or [None, ""])[1]
    category = (re.search(r'^category:\s*"?(.*?)"?\s*$', front, re.M) or [None, ""])[1]
    body_txt = re.sub(r'\s+\n', '\n', body).strip()[:3500]

    prompt = PROMPT % {"title": title, "category": category, "body": body_txt}
    print(f"[*] {args.slug}: claude -p ile senaryo üretiliyor...")
    try:
        r = subprocess.run(["claude", "-p", prompt, "--model", args.model],
                           capture_output=True, text=True, timeout=180)
        out = r.stdout.strip()
    except Exception as e:
        print(f"HATA: claude çağrısı başarısız: {e}"); return 1

    m = re.search(r'\{.*\}', out, re.DOTALL)
    if not m:
        print(f"HATA: JSON bulunamadı. Çıktı: {out[:200]}"); return 1
    try:
        data = json.loads(m.group(0))
        hook = data["hook"].strip()
        beats = [b.strip() for b in data["beats"]][:3]
        cta = data["cta"].strip()
        broll = [b.strip() for b in data.get("broll", [])][:4]
    except Exception as e:
        print(f"HATA: JSON ayrıştırılamadı ({e}). Çıktı: {out[:200]}"); return 1
    if not hook or len(beats) < 3 or not cta:
        print("HATA: eksik alan"); return 1

    items = [hook] + beats + [cta]
    block = "shorts:\n" + "".join(f"  - {yaml_q(x)}\n" for x in items)
    if broll:
        block += "shorts_broll:\n" + "".join(f"  - {yaml_q(x)}\n" for x in broll)

    # frontmatter'a ekle (varsa eski shorts:/shorts_broll: bloklarını temizle)
    front = re.sub(r'^shorts:\n(?:  - .*\n)+', '', front, flags=re.MULTILINE)
    front = re.sub(r'^shorts_broll:\n(?:  - .*\n)+', '', front, flags=re.MULTILINE)
    front = front.rstrip("\n") + "\n" + block
    open(path, "w", encoding="utf-8").write(f"---{front}---{body}")
    print(f"[+] {args.slug}: senaryo kaydedildi ({len(items)} satır + {len(broll)} broll)")
    print(f"    kanca: {hook}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
