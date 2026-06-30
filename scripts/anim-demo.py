#!/usr/bin/env python3
"""
ParaFOMO — Kinetik motion-graphics DEMO sahnesi (stok görsel YOK).

Markalı arka plan + kinetik başlık + 0'dan sayan rakam + kendini çizen grafik
+ altyazı. Tamamen PIL+numpy ile kare kare üretilir, ffmpeg ile mp4'e dizilir.
CPU'da çalışır, ücretsiz. Amaç: "animasyonlu anlatım yapılabilir mi?" sorusunu
somut göstermek.

Kullanım: python3 scripts/anim-demo.py
Çıktı:    demos/anim-demo.mp4
"""
import os
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "assets", "fonts")
TMP = "/tmp/anim_frames"
OUT = os.path.join(ROOT, "demos", "anim-demo.mp4")

W, H = 1080, 1920
FPS = 30
T = 7.0
N = int(T * FPS)

INK = (16, 19, 22)
INK2 = (9, 12, 14)
BRAND = (43, 177, 148)
LIGHT = (99, 212, 145)
WHITE = (245, 248, 247)
MUTE = (150, 168, 164)

ANTON = os.path.join(FONTS, "Anton-Regular.ttf")
OSWALD = os.path.join(FONTS, "Oswald.ttf")


def F(path, size):
    return ImageFont.truetype(path, size)


# ---------- easing ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_cubic(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_out_back(x):
    x = clamp(x)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def appear(t, t0, dur=0.45):
    """0→1 yumuşak giriş (zamanı t0'da başlar)."""
    return ease_out_cubic((t - t0) / dur)


# ---------- arka plan (numpy gradyan + sürüklenen parıltı + grid) ----------
def background(t):
    yy = np.linspace(0, 1, H)[:, None]
    top = np.array(INK, dtype=float)
    bot = np.array(INK2, dtype=float)
    base = top * (1 - yy) + bot * yy            # (H,1,3) yayılacak
    img = np.repeat(base[:, None, :], W, axis=1)  # (H,W,3)

    # yavaş sürüklenen radyal marka parıltısı
    cx = W * (0.5 + 0.18 * math.sin(t * 0.6))
    cy = H * (0.34 + 0.05 * math.cos(t * 0.5))
    xs = np.arange(W)[None, :]
    ys = np.arange(H)[:, None]
    d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    glow = np.clip(1 - d / 760.0, 0, 1)[:, :, None] ** 2
    img = img + glow * (np.array(BRAND, float) * 0.45)

    img = np.clip(img, 0, 255).astype("uint8")
    pim = Image.fromarray(img, "RGB").convert("RGBA")

    # hafif kayan dikey grid (finans/veri hissi)
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    off = int((t * 18) % 90)
    for x in range(-off, W, 90):
        gd.line([(x, 0), (x, H)], fill=(255, 255, 255, 8), width=1)
    for y in range(-off, H, 90):
        gd.line([(0, y), (W, y)], fill=(255, 255, 255, 6), width=1)
    pim.alpha_composite(grid)
    return pim


# ---------- grafik verisi (yükselen seri) ----------
rng = np.random.default_rng(7)
_steps = np.clip(rng.normal(1.0, 0.6, 40), -0.2, None)
SERIES = np.cumsum(np.concatenate([[0], _steps]))
SERIES = SERIES / SERIES.max()


def draw_chart(draw, box, reveal):
    x0, y0, x1, y1 = box
    n = len(SERIES)
    cut = clamp(reveal) * (n - 1)
    k = int(cut)
    pts = []
    for i in range(min(k + 1, n)):
        px = x0 + (x1 - x0) * (i / (n - 1))
        py = y1 - (y1 - y0) * SERIES[i]
        pts.append((px, py))
    if k + 1 < n and cut > k:
        frac = cut - k
        i0, i1 = k, k + 1
        px = x0 + (x1 - x0) * ((i0 + frac) / (n - 1))
        val = SERIES[i0] + (SERIES[i1] - SERIES[i0]) * frac
        py = y1 - (y1 - y0) * val
        pts.append((px, py))
    if len(pts) < 2:
        return
    # alt dolgu
    fill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fill)
    poly = pts + [(pts[-1][0], y1), (pts[0][0], y1)]
    fd.polygon(poly, fill=(*BRAND, 60))
    draw._image.alpha_composite(fill)
    # çizgi
    draw.line(pts, fill=(*LIGHT, 255), width=9, joint="curve")
    # uç parıltısı + nokta
    ex, ey = pts[-1]
    draw.ellipse([ex - 26, ey - 26, ex + 26, ey + 26], fill=(*LIGHT, 70))
    draw.ellipse([ex - 13, ey - 13, ex + 13, ey + 13], fill=WHITE)


def text_center(draw, cx, y, s, font, fill, anchor="mm"):
    draw.text((cx, y), s, font=font, fill=fill, anchor=anchor)


def frame(i):
    t = i / FPS
    img = background(t)
    d = ImageDraw.Draw(img)

    # global outro fade
    g = 1.0
    if t > 6.5:
        g = 1 - clamp((t - 6.5) / 0.5)

    def A(x):  # alpha helper 0..255 with global
        return int(clamp(x) * 255 * g)

    # üst marka pill
    a = appear(t, 0.15)
    if a > 0:
        pill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill)
        pf = F(OSWALD, 38)
        label = "PARAFOMO"
        tw = pd.textlength(label, font=pf)
        bx = (W - (tw + 130)) / 2
        pd.rounded_rectangle([bx, 130, bx + tw + 130, 200], radius=35,
                             fill=(255, 255, 255, int(16 * a)),
                             outline=(*BRAND, int(220 * a)), width=2)
        pd.ellipse([bx + 34, 157, bx + 60, 183], fill=(*LIGHT, int(255 * a)))
        pd.text((bx + 78, 165), label, font=pf, fill=(255, 255, 255, int(235 * a)),
                anchor="lm")
        img.alpha_composite(Image.blend(Image.new("RGBA", (W, H)), pill, g))

    # kinetik başlık ENFLASYON (yüksel + fade) + büyüyen alt çizgi
    a = appear(t, 0.35, 0.6)
    if a > 0:
        rise = int((1 - ease_out_cubic((t - 0.35) / 0.6)) * 60)
        hf = F(ANTON, 188)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        ld.text((W / 2, 430 + rise), "ENFLASYON", font=hf, fill=(*WHITE, A(a)),
                anchor="mm")
        img.alpha_composite(lay)
        uw = ease_out_cubic((t - 0.7) / 0.7)
        if uw > 0:
            half = 250 * uw
            d.rounded_rectangle([W / 2 - half, 548, W / 2 + half, 562], radius=7,
                                fill=(*BRAND, A(1)))

    # alt başlık
    a = appear(t, 0.95)
    if a > 0:
        d.text((W / 2, 628), "TÜRKİYE · 2024 YIL SONU", font=F(OSWALD, 44),
               fill=(*MUTE, A(a)), anchor="mm")

    # büyük sayan rakam %0 → %64.3
    a = appear(t, 1.15)
    if a > 0:
        prog = ease_out_cubic((t - 1.2) / 2.6)
        val = 64.3 * prog
        pop = 1.0
        if 3.7 < t < 4.1:
            pop = 1 + 0.06 * (1 - (t - 3.7) / 0.4)
        size = int(330 * pop)
        nf = F(ANTON, size)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        ld.text((W / 2, 880), f"%{val:.1f}", font=nf, fill=(*LIGHT, A(a)), anchor="mm")
        img.alpha_composite(lay)

    # kendini çizen grafik
    if t > 1.4:
        reveal = (t - 1.5) / 3.0
        cl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(cl)
        draw_chart(cd, (150, 1120, 930, 1500), reveal)
        img.alpha_composite(Image.blend(Image.new("RGBA", (W, H)), cl, g))

    # altyazı (kinetik fade)
    a = appear(t, 4.0)
    if a > 0:
        cap = "Fiyatlar bir yılda yüzde 64 arttı"
        cf = F(OSWALD, 54)
        tw = d.textlength(cap, font=cf)
        d.rounded_rectangle([(W - tw) / 2 - 36, 1632, (W + tw) / 2 + 36, 1716],
                            radius=20, fill=(8, 11, 13, A(0.55 * a)))
        d.text((W / 2, 1674), cap, font=cf, fill=(*WHITE, A(a)), anchor="mm")

    # vignette
    vg = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vg)
    vd.ellipse([-260, -360, W + 260, H + 360], fill=70)
    vg = vg.filter(ImageFilter.GaussianBlur(180))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 150))
    dark.putalpha(Image.eval(vg, lambda v: 150 - v if v < 150 else 0))
    img.alpha_composite(dark)

    return img.convert("RGB")


def main():
    os.makedirs(TMP, exist_ok=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    for f in os.listdir(TMP):
        os.remove(os.path.join(TMP, f))
    print(f"[*] {N} kare üretiliyor ({T}sn @ {FPS}fps)...")
    for i in range(N):
        frame(i).save(f"{TMP}/f{i:04d}.png")
        if i % 30 == 0:
            print(f"    {i}/{N}")
    print("[*] ffmpeg ile birleştiriliyor...")
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{TMP}/f%04d.png",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    OUT], check=True, capture_output=True)
    print(f"[+] {OUT}")


if __name__ == "__main__":
    main()
