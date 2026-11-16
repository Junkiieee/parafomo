#!/usr/bin/env python3
"""Instagram kaydırmalı slayt (carousel) üreticisi — "Para hikâyeleri" karakterleriyle 1080x1350 JPEG'ler.

Neden (2026-11-17): Reels erişimi 0–2; Socialinsider 2025'te carousel en yüksek etkileşim oranlı biçim; Instagram'ın
en güçlü sinyali "gönderme". Her hikâyenin slayt hâli kaydedilmeye/gönderilmeye uygun, yazıyla okunur olmalı.

  python3 scripts/anim/carousel.py public/social/carousel/<slug>/slaytlar.json
  → public/social/carousel/<slug>/1.jpg … n.jpg (yayın: scripts/instagram-carousel.py <slug>)

slaytlar.json: {"tema": "gece", "slaytlar": [{"baslik": ["…", "*vurgu*"], "metin": "…", "karakterler": [{"k": "yuzluk",
"ifade": "korkmus", "x": 540, "y": 760, "olcek": 0.9}], "dekor": [{"d": "sepet", "x": 540, "y": 800, "olcek": 1.6}],
"sayi": {"deger": "887", "birim": "₺", "not": "aynı sepet"}, "cubuk": {...}, "kaynak": "…", "alt": "kaydır →"}]}
"""
import html
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, "engines"))
import hikaye_kit as kit  # noqa: E402

CHROME = "/root/.cache/ms-playwright/chromium_headless_shell-1148/chrome-linux/headless_shell"
W, H = 1080, 1350
TEMA = {"gece": "radial-gradient(120% 70% at 50% 40%, #1f4134 0%, #10261f 45%, #08110e 100%)",
        "alacakaranlik": "linear-gradient(180deg, #14213d 0%, #23305a 45%, #5b3d63 75%, #9c4f2c 100%)",
        "dram": "radial-gradient(110% 60% at 50% 38%, #18262c 0%, #0b1216 55%, #050709 100%)"}
E = html.escape


def vurgula(t):
    return "".join(f'<b class="vz">{E(p[1:-1])}</b>' if p.startswith("*") and p.endswith("*") else E(p)
                   for p in re.split(r"(\*[^*]+\*)", t or ""))


def slayt_html(s, tema, no, toplam):
    parca = []
    for i, c in enumerate(s.get("karakterler", [])):
        size = 600 * float(c.get("olcek", 0.8))
        parca.append(f'<div class="k" style="left:{c.get("x", 540) - size / 2:.0f}px;top:{c.get("y", 760) - size / 2:.0f}px;'
                     f'width:{size:.0f}px;height:{size:.0f}px"><svg viewBox="0 0 600 600" width="100%" height="100%">'
                     f'{kit.karakter(c["k"], c.get("ifade", "normal"), f"c{no}{i}")}</svg></div>')
    for i, d in enumerate(s.get("dekor", [])):
        size = 200 * float(d.get("olcek", 1))
        parca.append(f'<div class="k" style="left:{d.get("x", 540) - size / 2:.0f}px;top:{d.get("y", 800) - size / 2:.0f}px;'
                     f'width:{size:.0f}px;height:{size:.0f}px"><svg viewBox="0 0 200 200" width="100%" height="100%">'
                     f'{kit.dekor(d["d"], f"d{no}{i}")}</svg></div>')
    if s.get("sayi"):
        sy = s["sayi"]
        parca.append(f'<div class="sayi" style="top:{sy.get("y", 380)}px">{E(str(sy["deger"]))}<span>{E(sy.get("birim", ""))}</span>'
                     f'{"<div class=not>" + E(sy["not"]) + "</div>" if sy.get("not") else ""}</div>')
    if s.get("cubuk"):
        c = s["cubuk"]
        mx = max(float(c["a"]["deger"]), float(c["b"]["deger"]))
        for k, (t, x) in enumerate((("a", 330), ("b", 750))):
            o = c[t]
            h = 420 * float(o["deger"]) / mx
            parca.append(f'<div class="cubuk" style="left:{x - 110}px"><div class="cd">{E(o.get("yazi", str(o["deger"])))}</div>'
                         f'<div class="cb" style="height:{h:.0f}px;background:{"#4fa3e0" if k == 0 else "#ffb547"}"></div>'
                         f'<div class="ce">{E(o["etiket"])}</div></div>')
    baslik = "<br>".join(vurgula(x) for x in s.get("baslik", []))
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><style>
@font-face {{ font-family: InterP; src: url('file://{ROOT}/public/fonts/inter-latin.woff2'); font-weight: 400 700;
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+2000-206F, U+20AC, U+20BA; }}
@font-face {{ font-family: InterP; src: url('file://{ROOT}/public/fonts/inter-latin-ext.woff2'); font-weight: 400 700;
  unicode-range: U+0100-02BA, U+1E00-1EFF, U+20A0-20C0; }}
@font-face {{ font-family: AntonP; src: url('file://{ROOT}/assets/fonts/Anton-Regular.ttf'); }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {W}px; height: {H}px; overflow: hidden; }}
body {{ background: {TEMA.get(tema, TEMA['gece'])}; color: #fff; font-family: InterP, sans-serif; position: relative; }}
.b {{ position: absolute; top: 110px; left: 70px; right: 70px; text-align: center; font-weight: 700; font-size: 84px;
  line-height: 1.06; letter-spacing: -2px; text-shadow: 0 6px 30px rgba(0,0,0,.45); }}
.b.kanca {{ font-family: AntonP, sans-serif; font-weight: 400; font-size: 130px; letter-spacing: 1px; text-transform: uppercase; }}
.vz {{ color: #ffb547; }}
.m {{ position: absolute; left: 80px; right: 80px; bottom: 210px; text-align: center; font-weight: 600; font-size: 46px; line-height: 1.3; }}
.k {{ position: absolute; }}
.sayi {{ position: absolute; left: 0; right: 0; text-align: center; font-family: AntonP, sans-serif; font-size: 200px; line-height: 1; }}
.sayi span {{ font-size: 96px; color: #ffb547; margin-left: 14px; }}
.sayi .not {{ font-family: InterP, sans-serif; font-weight: 700; font-size: 44px; margin-top: 10px; }}
.cubuk {{ position: absolute; top: 330px; width: 220px; height: 620px; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; }}
.cubuk .cb {{ width: 180px; border-radius: 18px 18px 6px 6px; }}
.cubuk .cd {{ font-family: AntonP, sans-serif; font-size: 72px; margin-bottom: 12px; }}
.cubuk .ce {{ font-weight: 700; font-size: 40px; margin-top: 14px; color: #f4c26b; }}
.kaynak {{ position: absolute; left: 60px; right: 60px; bottom: 120px; text-align: center; font-weight: 600; font-size: 28px; color: rgba(255,255,255,.75); }}
.alt {{ position: absolute; left: 0; right: 0; bottom: 48px; text-align: center; font-weight: 700; font-size: 32px; color: #ffb547; }}
.marka {{ position: absolute; left: 60px; bottom: 50px; font-family: AntonP, sans-serif; font-size: 34px; letter-spacing: 3px; color: rgba(255,255,255,.75); }}
.no {{ position: absolute; right: 60px; bottom: 50px; font-weight: 700; font-size: 30px; color: rgba(255,255,255,.75); }}
</style></head><body>
<div class="b{' kanca' if s.get('kanca') else ''}">{baslik}</div>
{''.join(parca)}
{f'<div class="m">{vurgula(s["metin"])}</div>' if s.get("metin") else ''}
{f'<div class="kaynak">{E(s["kaynak"])}</div>' if s.get("kaynak") else ''}
{f'<div class="alt">{E(s["alt"])}</div>' if s.get("alt") else ''}
<div class="marka">PARAFOMO</div><div class="no">{no}/{toplam}</div>
</body></html>"""


def main():
    spec_p = sys.argv[1]
    spec = json.load(open(spec_p, encoding="utf-8"))
    out = os.path.dirname(os.path.abspath(spec_p))
    sl = spec["slaytlar"]
    from PIL import Image
    for i, s in enumerate(sl, 1):
        hp = os.path.join(out, f".s{i}.html")
        open(hp, "w", encoding="utf-8").write(slayt_html(s, spec.get("tema", "gece"), i, len(sl)))
        png = os.path.join(out, f".s{i}.png")
        subprocess.run(["nice", "-n", "19", CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                        "--allow-file-access-from-files", f"--window-size={W},{H}", "--virtual-time-budget=3000",
                        f"--screenshot={png}", "file://" + hp], capture_output=True, timeout=120)
        Image.open(png).convert("RGB").save(os.path.join(out, f"{i}.jpg"), quality=90, optimize=True)
        os.remove(png)
        os.remove(hp)
        print("slayt", i, "tamam")


if __name__ == "__main__":
    main()
