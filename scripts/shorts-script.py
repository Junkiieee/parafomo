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


# En çok izlenen videoların görsel yöntemi: her beat'e İÇERİKLE EŞLEŞEN görsel
# ({type,query}) → jenerik stok yerine somut/gerçek imge. Bu vocab shorts-build.py'nin
# (viral-visuals.py) çözdüğü tiplerle birebir aynıdır; "chart" hariç (blog hattında
# gerçek veri yok → grafik üretilemez, çıkarıldı).
ALLOWED_TYPES = {"person", "place", "building", "logo", "gold", "object", "concept", "scene"}
VISUAL_GUIDE = """Görsel tipleri ve "query" kuralı (görsel motoru buna göre kaynak seçer):
- "person": gerçek kişi → query = TAM ÖZEL AD (ör. "Recep Tayyip Erdoğan", "Jerome Powell").
- "place"/"building": gerçek yer/kurum → query = özel ad (ör. "Borsa İstanbul", "Türkiye Cumhuriyet Merkez Bankası").
- "logo": marka/şirket → query = "<Şirket> logo".
- "gold": altın → query İNGİLİZCE (ör. "gold bullion bars", "gold coins").
- "object": gerçek nesne → query İNGİLİZCE isim (ör. "credit card", "turkish lira banknotes").
- "concept"/"scene": soyut/sahne stok video → query İNGİLİZCE (ör. "inflation money losing value", "stock market chart screen", "bank counter customer").
KURAL: hook ve beat'in ana öznesi gerçek kişi/yer/marka ise MUTLAKA person/place/logo kullan (stok değil). Her görsel o beat'in İÇERİĞİYLE birebir örtüşsün. Emin değilsen concept/scene + net İngilizce sahne."""


PROMPT = """Sen bir Türk finans kanalı (ParaFOMO) için VİRAL YouTube Shorts senaryosu yazıyorsun.
Aşağıdaki blog yazısından 40-45 saniyelik, akıcı, KONUŞMA dilinde bir senaryo çıkar.
İzleyiciyi İLK 2 SANİYEDE durduracak bir KANCA şart.

KANCA AÇISI: %(angle_name)s
%(angle_guide)s

Kurallar:
- hook: ilk 2 saniyede durduran KISA cümle (en fazla 9 kelime), yukarıdaki açıya UYGUN. Merak/şaşkınlık uyandırsın; tıklama tuzağı değil, doğru.
- beats: tam 3 madde. Her biri yazının bir ana fikrini anlatan, tek başına anlaşılır, akıcı Türkçe cümle (12-20 kelime). Kopuk ifade YOK.
- cta: kısa; önce ileriye dönük bir MERAK cümlesi, sonra KANALA ABONE çağrısı ("abone ol" geçsin) + kısa bir sebep. "parafomo.com" de geçsin.
- broll: konuyla ilgili 4 adet İngilizce stok video arama terimi (yedek; örn. "stock market chart", "turkish lira money").
- visuals: TAM 5 görsel — sırayla [hook, beat1, beat2, beat3, cta]. Her biri {"type","query"} ve o segmentin İÇERİĞİYLE ÖRTÜŞSÜN.
- Sade, net; uydurma rakam YOK. Yazıda olmayan sayı verme.

%(visual_guide)s

SADECE şu JSON'u döndür, başka HİÇBİR şey yazma (markdown, ``` , açıklama YOK):
{"hook": "...", "beats": ["...", "...", "..."], "cta": "...", "broll": ["...","...","...","..."],
 "visuals": [{"type":"...","query":"..."},{"type":"...","query":"..."},{"type":"...","query":"..."},{"type":"...","query":"..."},{"type":"...","query":"..."}]}

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
                       "angle_name": angle_name, "angle_guide": angle_guide,
                       "visual_guide": VISUAL_GUIDE}
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
        visuals = data.get("visuals", [])
    except Exception as e:
        print(f"HATA: JSON ayrıştırılamadı ({e}). Çıktı: {out[:200]}"); return 1
    if not hook or len(beats) < 3 or not cta:
        print("HATA: eksik alan"); return 1

    # Beat-başına eşleşen görseller (en çok izlenen videoların yöntemi). 5 segmente
    # hizalı "type|query". Eksik/geçersizse o segment yedek b-roll'a düşer (build tarafı).
    vis_lines = []
    for v in visuals[:5]:
        t = (v.get("type") or "").strip().lower()
        q = (v.get("query") or "").strip()
        vis_lines.append(f"{t}|{q}" if (t in ALLOWED_TYPES and q) else "")
    while len(vis_lines) < 5:
        vis_lines.append("")

    items = [hook] + beats + [cta]
    block = "shorts:\n" + "".join(f"  - {yaml_q(x)}\n" for x in items)
    if broll:
        block += "shorts_broll:\n" + "".join(f"  - {yaml_q(x)}\n" for x in broll)
    if any(vis_lines):
        block += "shorts_visuals:\n" + "".join(f"  - {yaml_q(x)}\n" for x in vis_lines)

    # frontmatter'a ekle (varsa eski shorts:/shorts_broll:/shorts_visuals: bloklarını temizle)
    front = re.sub(r'^shorts:\n(?:  - .*\n)+', '', front, flags=re.MULTILINE)
    front = re.sub(r'^shorts_broll:\n(?:  - .*\n)+', '', front, flags=re.MULTILINE)
    front = re.sub(r'^shorts_visuals:\n(?:  - .*\n)+', '', front, flags=re.MULTILINE)
    front = front.rstrip("\n") + "\n" + block
    open(path, "w", encoding="utf-8").write(f"---{front}---{body}")
    n_vis = sum(1 for x in vis_lines if x)
    print(f"[+] {args.slug}: senaryo kaydedildi ({len(items)} satır + {len(broll)} broll + {n_vis}/5 eşleşen görsel)")
    print(f"    kanca: {hook}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
