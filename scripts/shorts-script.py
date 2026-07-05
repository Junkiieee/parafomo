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

# Kanca açıları — blog konusunu düz "nedir" yerine VİRAL bir çerçeveye sokar.
# İzlenme verisi (2026-07): mit/şok kancaları eğitici anlatımın 5-10 katı açılış yapıyor.
# NOT: backtest/karşılaştırma açıları GERÇEK piyasa verisi ister (viral-script.py'de var);
# blog hattında uydurma rakam olmasın diye buraya ALINMADI. "şok-sayı" yalnız YAZININ
# İÇİNDEKİ rakamları kullanır (bileşik faiz örneği vb.), piyasa getirisi uydurmaz.
ANGLES = {
    "myth": ("MİT YIKMA",
        "Hook, yaygın ama YANLIŞ/eksik bir finans inancını çürütsün "
        "(\"...güvenli/kârlı sanıyorsun ama...\"). Beat'ler: neden yanlış → gerçek → doğrusu. "
        "Hafif kışkırtıcı ama DOĞRU; yazının bilgisine dayan."),
    "shock_number": ("ŞOK VERİ",
        "Hook, YAZIDA geçen çarpıcı TEK bir rakam/oran/kat olsun "
        "(\"100 TL, X yılda Y TL olur\"). Beat'ler: rakamın anlamı → sebebi → izleyiciye sonucu. "
        "SADECE yazıdaki rakamları kullan, piyasa getirisi UYDURMA."),
    "curiosity": ("MERAK",
        "Hook, kavramı merak uyandıran çarpıcı bir SORUYLA açsın "
        "(\"Eurobond aslında ne işe yarar?\"). Beat'ler: kavramı GÜNLÜK bir metaforla aç, jargon yok."),
}

# Konu → açı seçimi (deterministik; --angle ile ezilir). Slug/başlık/kategori üzerinden.
MYTH_HINTS = ("banka", "mevduat", "guvenli", "güvenli", "risk", "kredi", "borc", "borç",
              "enflasyon", "koru", "kaybet", "eriyor", "tuzak", "yanlis", "yanlış")
SHOCK_HINTS = ("bilesik", "bileşik", "faiz", "getiri", "kazanc", "kazanç", "temettu", "temettü",
               "pasif-gelir", "kat", "bin", "milyon", "yuzde", "yüzde", "50-30-20", "butce", "bütçe")


def pick_angle(slug, title, category):
    hay = f"{slug} {title} {category}".lower()
    if any(h in hay for h in MYTH_HINTS):
        return "myth"
    if any(h in hay for h in SHOCK_HINTS):
        return "shock_number"
    return "curiosity"


PROMPT = """Sen bir Türk finans kanalı (ParaFOMO) için VİRAL YouTube Shorts senaryosu yazıyorsun.
Aşağıdaki blog yazısından 40-45 saniyelik, akıcı, KONUŞMA dilinde bir senaryo çıkar.
İzleyiciyi İLK 2 SANİYEDE durduracak bir KANCA şart.

KANCA AÇISI: %(angle_name)s
%(angle_guide)s

Kurallar:
- hook: ilk 2 saniyede durduran KISA cümle (en fazla 9 kelime), yukarıdaki açıya UYGUN. Merak/şaşkınlık uyandırsın; tıklama tuzağı değil, doğru.
- beats: tam 3 madde. Her biri yazının bir ana fikrini anlatan, tek başına anlaşılır, akıcı Türkçe cümle (12-20 kelime). Kopuk ifade YOK.
- cta: kısa; önce ileriye dönük bir MERAK cümlesi, sonra KANALA ABONE çağrısı ("abone ol" geçsin) + kısa bir sebep. "parafomo.com" de geçsin.
- broll: konuyla ilgili 4 adet İngilizce stok video arama terimi (örn. "stock market chart", "turkish lira money").
- Sade, net; uydurma rakam YOK. Yazıda olmayan sayı verme.

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
    ap.add_argument("--angle", choices=list(ANGLES), default="",
                    help="kanca açısı (boş: konudan otomatik seç)")
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

    angle = args.angle or pick_angle(args.slug, title, category)
    angle_name, angle_guide = ANGLES[angle]
    prompt = PROMPT % {"title": title, "category": category, "body": body_txt,
                       "angle_name": angle_name, "angle_guide": angle_guide}
    print(f"[*] {args.slug}: claude -p ile senaryo üretiliyor... (açı: {angle})")
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
