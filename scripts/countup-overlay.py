#!/usr/bin/env python3
"""
ParaFOMO — Animasyonlu sayı sayacı (count-up) overlay üreticisi.

Neden: En yüksek skorlu Shorts formatımız `backtest_return` ("10.000 TL koysaydın
bugün X TL olurdu"). Araştırma (2026): ease-out ile hızlanıp yavaşlayarak HEDEF
sayıya "inen" animasyonlu sayaç, statik sayıya göre dikkat + hatırlamayı belirgin
artırıyor ("motion earns the pause"). Vanguard'ın animasyonlu "paran büyüyor"
zaman serisi → uzun-vade abonelikte +%32. Bu format tam da bu hareketle eşleşiyor.

Ne yapar: start→end arası, Türkçe biçimli (6.657 gibi), ₺/%/x son ekli, marka
sarısı (#FFE14D) Anton fontuyla, ŞEFFAF arka planlı bir PNG kare dizisi üretir.
İsteğe bağlı alt etiket (ör. "5 yılda") ve alfa'lı .mov (ffmpeg overlay için).

Kullanım:
  python3 scripts/countup-overlay.py --start 10000 --end 21000 --suffix " TL" \
      --label "5 YILDA" --dur 2.5 --out /tmp/countup

Çıktı: <out>/frame_%04d.png (RGBA) + <out>.mov (prores 4444, alfa) varsa ffmpeg.
Token harcamaz; ffmpeg/PIL. shorts-build-v4 payoff sahnesine overlay olarak takılır.
"""
import os
import sys
import shutil
import argparse
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANTON = os.path.join(ROOT, "assets", "fonts", "Anton-Regular.ttf")
OSWALD = os.path.join(ROOT, "assets", "fonts", "Oswald.ttf")

W, H = 1080, 1920
YELLOW = (255, 225, 77, 255)      # #FFE14D — marka aktif-vurgu sarısı
WHITE = (245, 248, 252, 255)
SHADOW = (6, 10, 14, 235)
LABEL_C = (200, 214, 230, 255)


def fmt_tr(n, decimals=0):
    """1234567.8 -> '1.234.568' / '1.234.567,8' (TR binlik '.', ondalık ',')."""
    s = f"{n:,.{decimals}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", size)


def draw_centered(draw, cy, text, fnt, fill, cx=W // 2):
    box = draw.textbbox((0, 0), text, font=fnt)
    tw, th = box[2] - box[0], box[3] - box[1]
    x, y = cx - tw / 2 - box[0], cy - th / 2 - box[1]
    # yumuşak gölge (her B-roll üstünde okunur kalsın)
    for dx, dy in ((0, 4), (4, 0), (3, 3), (-3, 3)):
        draw.text((x + dx, y + dy), text, font=fnt, fill=SHADOW)
    draw.text((x, y), text, font=fnt, fill=fill)
    return tw


def render(args):
    outdir = args.out.rstrip("/")
    if os.path.isdir(outdir):
        shutil.rmtree(outdir)
    os.makedirs(outdir, exist_ok=True)

    fps = args.fps
    n_frames = max(2, int(round(args.dur * fps)))
    hold = int(round(args.hold * fps))          # son değerde bekleme kareleri
    num_f = font(ANTON, args.size)
    lab_f = font(OSWALD, max(40, args.size // 4))

    span = args.end - args.start
    cy = args.cy if args.cy else H // 2

    for i in range(n_frames + hold):
        t = min(1.0, i / max(1, n_frames - 1))
        val = args.start + span * ease_out_cubic(t)
        if i >= n_frames:
            val = args.end
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        if args.label:
            draw_centered(d, cy - args.size // 2 - 30, args.label.upper(), lab_f, LABEL_C)
        txt = f"{args.prefix}{fmt_tr(val, args.decimals)}{args.suffix}"
        # hedefe inince sarı vurgu, yolda beyaz — landing "payoff" hissi
        col = YELLOW if (i >= n_frames - 1) else WHITE
        draw_centered(d, cy + 20, txt, num_f, col)
        img.save(f"{outdir}/frame_{i:04d}.png")

    total = n_frames + hold
    print(f"[countup] {total} kare üretildi → {outdir}/frame_%04d.png "
          f"({args.start:g}→{args.end:g}{args.suffix}, {fps}fps, ease-out)")

    # Alfa'lı .mov (ffmpeg varsa) — doğrudan overlay-video olarak da kullanılabilir.
    if shutil.which("ffmpeg"):
        mov = f"{outdir}.mov"
        cmd = ["ffmpeg", "-y", "-framerate", str(fps), "-i", f"{outdir}/frame_%04d.png",
               "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", mov]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            print(f"[countup] alfa mov → {mov}")
        else:
            print(f"[countup] mov atlandı: {r.stderr.strip().splitlines()[-1] if r.stderr else '?'}")
    return outdir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--dur", type=float, default=2.2, help="animasyon süresi (sn)")
    ap.add_argument("--hold", type=float, default=0.6, help="son değerde bekleme (sn)")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--suffix", default="")
    ap.add_argument("--prefix", default="")
    ap.add_argument("--decimals", type=int, default=0)
    ap.add_argument("--label", default="")
    ap.add_argument("--size", type=int, default=220)
    ap.add_argument("--cy", type=int, default=0, help="sayının dikey merkezi (0=ekran ortası)")
    ap.add_argument("--out", required=True, help="çıktı klasörü (frame_%04d.png)")
    render(ap.parse_args())


if __name__ == "__main__":
    main()
