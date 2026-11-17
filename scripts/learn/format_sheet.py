#!/usr/bin/env python3
"""Video biçimi radarı: haftanın patlayan videolarının kapaklarını tek bir kontakt sayfasında toplar.

Neden (Kaan 2026-11-17: "web YouTube Instagram için ayrıca video biçimleri de araştırılsın, farklı animasyonlar neler
eklenebilir, bunlar önemli"): radarlar NE konuşulduğunu bulur; bu sayfa NASIL anlatıldığını (çizgi hikâye, tablo kartı,
o zaman/şimdi kartı, konuşan kafa, skeç…) gösterir. Sabah rutini Pazartesi ve Perşembe bu sayfaya bakar, biçimleri
agent/plan/format-katalogu.md'ye işler ve haftada bir yeni biçimi motora ekler.

Girdi: /root/parafomo-data/trend/yt-trend.json + ig-trend.json (gece hikaye_uret.py yeniler).
Çıktı (repo DIŞI): /root/parafomo-data/trend/format/<tarih>.jpg + <tarih>.json (sıra → kaynak, izlenme, başlık, url).
Kullanım: python3 scripts/learn/format_sheet.py [--n 24]
"""
import argparse
import datetime as dt
import io
import json
import os
import urllib.request

from PIL import Image, ImageDraw, ImageFont

DIR = "/root/parafomo-data/trend"
OUT = os.path.join(DIR, "format")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def adaylar(n):
    out = []
    try:
        ig = json.load(open(os.path.join(DIR, "ig-trend.json"), encoding="utf-8"))
        out += [{"kaynak": "IG @" + x["hesap"], "izlenme": x["izlenme"], "baslik": x["kanca"], "url": x["url"], "kapak": x.get("kapak")}
                for x in ig.get("patlayan", []) + ig.get("en_cok", [])]
    except (OSError, ValueError):
        pass
    try:
        yt = json.load(open(os.path.join(DIR, "yt-trend.json"), encoding="utf-8"))
        out += [{"kaynak": "YT " + x["kanal"][:18], "izlenme": x["izlenme"], "baslik": x["baslik"], "url": x["url"], "kapak": x.get("kapak")}
                for x in yt.get("patlayan_kucuk", []) + yt.get("en_cok", [])]
    except (OSError, ValueError):
        pass
    gor, sec = set(), []
    for x in sorted(out, key=lambda x: -x["izlenme"]):
        if x["url"] in gor or not x.get("kapak"):
            continue
        gor.add(x["url"])
        sec.append(x)
    return sec[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=24)
    a = ap.parse_args()
    sec = adaylar(a.n)
    if not sec:
        print("[format] aday yok (radar dosyaları boş ya da eski)"); return 1
    W, H, SUT = 270, 480, 6
    satir = (len(sec) + SUT - 1) // SUT
    sayfa = Image.new("RGB", (W * SUT, (H + 70) * satir), (12, 18, 16))
    d = ImageDraw.Draw(sayfa)
    f1, f2 = ImageFont.truetype(FONT, 18), ImageFont.truetype(FONT, 14)
    for i, x in enumerate(sec):
        cx, cy = (i % SUT) * W, (i // SUT) * (H + 70)
        try:
            req = urllib.request.Request(x["kapak"], headers={"User-Agent": "Mozilla/5.0"})
            im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=20).read())).convert("RGB")
            oran = max(W / im.width, H / im.height)
            im = im.resize((int(im.width * oran), int(im.height * oran)))
            sol, ust = (im.width - W) // 2, (im.height - H) // 2
            sayfa.paste(im.crop((sol, ust, sol + W, ust + H)), (cx, cy))
        except Exception:
            d.rectangle((cx, cy, cx + W - 2, cy + H), outline=(80, 80, 80))
        d.text((cx + 6, cy + H + 4), f"#{i + 1} {x['izlenme']:,}".replace(",", "."), font=f1, fill=(255, 190, 70))
        d.text((cx + 6, cy + H + 28), x["kaynak"][:28], font=f2, fill=(220, 230, 225))
        d.text((cx + 6, cy + H + 48), x["baslik"][:32], font=f2, fill=(160, 175, 170))
    os.makedirs(OUT, exist_ok=True)
    gun = dt.date.today().isoformat()
    sayfa.save(os.path.join(OUT, f"{gun}.jpg"), quality=82)
    json.dump([{k: x[k] for k in ("kaynak", "izlenme", "baslik", "url")} for x in sec],
              open(os.path.join(OUT, f"{gun}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[format] {len(sec)} kapak → {os.path.join(OUT, gun + '.jpg')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
