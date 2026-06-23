#!/usr/bin/env python3
"""
ParaFOMO — Reels (dikey video) PROTOTİP üretici.

Bir blog yazısının frontmatter'ından (title, category, faq) markalı dikey
1080x1920 slaytlar üretir ve ffmpeg ile yumuşak geçişli bir MP4 (H.264/AAC-uyumlu,
IG Reels formatı) oluşturur. Slaytlar: giriş başlığı → 3 SSS slaytı → kapanış CTA.

Kullanım: python3 scripts/reel-demo.py <slug>
Çıktı:   public/social/reel-<slug>.mp4
"""
import os
import re
import sys
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG = os.path.join(ROOT, "src", "content", "blog")
WORDMARK = os.path.join(ROOT, "public", "parafomo-wordmark.png")
OUT_DIR = os.path.join(ROOT, "public", "social")
TMP = "/tmp/reel_frames"

W, H = 1080, 1920
M = 96
INK = (18, 20, 23)
DEEP = (30, 107, 127)
BRAND = (43, 177, 148)
LIGHT = (99, 212, 145)
GREY = (95, 105, 115)
WHITE = (255, 255, 255)

SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


def fnt(p, s):
    return ImageFont.truetype(p, s)


def vgrad(w, h, c1, c2):
    base = Image.new("RGB", (w, h), c1)
    top = Image.new("RGB", (w, h), c2)
    mask = Image.new("L", (w, h))
    md = mask.load()
    for y in range(h):
        v = int(255 * (y / h))
        for x in range(w):
            md[x, y] = v
    base.paste(top, (0, 0), mask)
    return base


def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = wd
    if cur:
        lines.append(cur)
    return lines


def base_canvas():
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    # üst gradyan bant
    band = vgrad(W, 12, DEEP, LIGHT)
    img.paste(band, (0, 0))
    # köşe glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W - 360, -260, W + 220, 320], fill=(99, 212, 145, 34))
    gd.ellipse([-220, H - 320, 360, H + 240], fill=(43, 177, 148, 26))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    return img


def footer(img, d):
    d.line([M, H - 150, W - M, H - 150], fill=(228, 232, 234), width=2)
    if os.path.exists(WORDMARK):
        wm = Image.open(WORDMARK).convert("RGBA")
        th = 52
        wm = wm.resize((int(wm.width * th / wm.height), th), Image.LANCZOS)
        img.paste(wm, (M, H - 122), wm)
    d.text((W - M, H - 96), "@parafomo", font=fnt(SANS_B, 32), fill=BRAND, anchor="rm")


def slide_intro(title, category, path):
    img = base_canvas()
    d = ImageDraw.Draw(img)
    cat = (category or "Finans").upper()
    cf = fnt(SANS_B, 34)
    tw = d.textlength(cat, font=cf)
    d.rounded_rectangle([M, 360, M + tw + 56, 360 + 64], radius=32, fill=BRAND)
    d.text((M + 28, 392), cat, font=cf, fill=WHITE, anchor="lm")
    # başlık
    for size in range(94, 55, -3):
        f = fnt(SERIF_B, size)
        lines = wrap(d, title, f, W - 2 * M)
        if len(lines) <= 5:
            break
    y = 500
    for ln in lines:
        d.text((M, y), ln, font=f, fill=INK); y += int(size * 1.18)
    d.text((M, y + 40), "kaydır →", font=fnt(SANS, 38), fill=GREY)
    footer(img, d)
    img.save(path)


def slide_faq(idx, q, a, path):
    img = base_canvas()
    d = ImageDraw.Draw(img)
    d.text((M, 320), f"SORU {idx}", font=fnt(SANS_B, 36), fill=BRAND)
    # soru
    for size in range(70, 43, -3):
        qf = fnt(SERIF_B, size)
        ql = wrap(d, q, qf, W - 2 * M)
        if len(ql) <= 4:
            break
    y = 400
    for ln in ql:
        d.text((M, y), ln, font=qf, fill=INK); y += int(size * 1.16)
    # ayraç
    y += 30
    d.line([M, y, M + 120, y], fill=BRAND, width=6); y += 50
    # cevap (kısalt)
    a = a.strip()
    if len(a) > 300:
        a = a[:297].rsplit(" ", 1)[0] + "…"
    af = fnt(SANS, 44)
    for ln in wrap(d, a, af, W - 2 * M):
        d.text((M, y), ln, font=af, fill=(55, 62, 70)); y += 60
    footer(img, d)
    img.save(path)


def slide_outro(path):
    img = base_canvas()
    d = ImageDraw.Draw(img)
    d.text((W // 2, 620), "Devamı ve", font=fnt(SANS, 52), fill=GREY, anchor="mm")
    d.text((W // 2, 700), "tüm rehberler", font=fnt(SANS, 52), fill=GREY, anchor="mm")
    d.text((W // 2, 830), "parafomo.com", font=fnt(SERIF_B, 92), fill=INK, anchor="mm")
    cf = fnt(SANS_B, 40)
    txt = "Takip et  @parafomo"
    tw = d.textlength(txt, font=cf)
    d.rounded_rectangle([(W - tw) // 2 - 40, 960, (W + tw) // 2 + 40, 960 + 84],
                        radius=42, fill=BRAND)
    d.text((W // 2, 1002), txt, font=cf, fill=WHITE, anchor="mm")
    d.text((W // 2, 1130), "parana akıl kat.", font=fnt(SANS, 40), fill=GREY, anchor="mm")
    footer(img, d)
    img.save(path)


def fm(front, key):
    m = re.search(rf'^{key}:\s*"?(.*?)"?\s*$', front, re.MULTILINE)
    return m.group(1).strip() if m else ""


def parse_faq(front):
    out = []
    for m in re.finditer(r'-\s*q:\s*"?(.*?)"?\s*\n\s*a:\s*"?(.*?)"?\s*(?=\n\s*-\s*q:|\n[a-zA-Z]|\Z)',
                         front, re.DOTALL):
        out.append((m.group(1).strip(), m.group(2).strip()))
    return out


def main():
    if len(sys.argv) < 2:
        print("kullanım: reel-demo.py <slug>"); return 1
    slug = sys.argv[1]
    path = os.path.join(BLOG, f"{slug}.md")
    raw = open(path, encoding="utf-8").read()
    front = raw.split("---", 2)[1]
    title = fm(front, "title")
    category = fm(front, "category")
    faq = parse_faq(front)[:3]

    os.makedirs(TMP, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    frames = []
    slide_intro(title, category, f"{TMP}/00.png"); frames.append((f"{TMP}/00.png", 3.5))
    for i, (q, a) in enumerate(faq, 1):
        p = f"{TMP}/{i:02d}.png"
        slide_faq(i, q, a, p); frames.append((p, 5.0))
    slide_outro(f"{TMP}/99.png"); frames.append((f"{TMP}/99.png", 3.5))

    # her slaytı yumuşak zoom + beyaza fade ile klibe çevir
    clips = []
    for n, (img, dur) in enumerate(frames):
        clip = f"{TMP}/clip{n}.mp4"
        fps = 30
        nf = int(dur * fps)
        vf = (f"scale=1080:1920,zoompan=z='min(zoom+0.0006,1.08)':d={nf}:"
              f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps},"
              f"fade=t=in:st=0:d=0.4:color=white,"
              f"fade=t=out:st={dur-0.4:.2f}:d=0.4:color=white,format=yuv420p")
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-t", str(dur), "-i", img,
                        "-vf", vf, "-c:v", "libx264", "-r", str(fps), "-pix_fmt", "yuv420p",
                        clip], check=True, capture_output=True)
        clips.append(clip)

    lst = f"{TMP}/list.txt"
    with open(lst, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    out = os.path.join(OUT_DIR, f"reel-{slug}.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    out], check=True, capture_output=True)
    dur = sum(d for _, d in frames)
    sz = os.path.getsize(out) / 1024
    print(f"[+] Reels üretildi: {out}  ({dur:.0f}s, {sz:.0f} KB)")
    # önizleme kareleri
    for n in (0, 1, len(frames) - 1):
        Image.open(frames[n][0]).save(f"{TMP}/preview_{n}.png")
    print(f"[+] Önizleme kareleri: {TMP}/preview_*.png")


if __name__ == "__main__":
    sys.exit(main())
