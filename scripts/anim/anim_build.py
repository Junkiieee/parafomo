#!/usr/bin/env python3
"""Kodla çizilmiş animasyonlu Short (9:16) üretir — stil kitleri: scripts/anim/vendor (MIT, cth9191/animate).

    python3 scripts/anim/anim_build.py scripts/anim/pieces/net-maas-anatomi.json [--still 3.5,12,30] [--no-lock]

Akış: her satır Orus ile seslendirilir (önbellekli) → satır süreleri zaman çizelgesi olur (sahneler satırların
başlangıcına göre oynar, ses saattir) → sayfa (çekirdek + stil kiti + sahne + çizelge) → Chromium'da kare kare
render (nice 19, ionice idle, Shorts kilidi) → anlatım + müzik (konuşmada kısılır) + loudnorm -14 LUFS → mux.
--still: yalnız o saniyelerin karelerini PNG çıkarır (tasarım kontrolü, ses/render yok).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "longform"))
from lf_common import ROOT, MUSIC_DIR, tts, duration, run  # noqa: E402

W, H, FPS = 1080, 1920, 30
RATE = 1.15                     # Shorts temposu (uzun-form 1.08)
LEAD, GAP, TAIL = 0.35, 0.28, 1.6
MUSIC_VOL = 0.12
OUT_DIR = os.path.join(ROOT, "public", "social", "anim")
WORK = "/root/.cache/parafomo/anim"
LOCK = "/tmp/shorts_frames.lock"
VENDOR = os.path.join(HERE, "vendor", "animate")
FONTS = os.path.join(ROOT, "assets", "fonts")


def timeline(spec):
    t, lines = LEAD, []
    for ln in spec["lines"]:
        mp3 = tts(ln["say"], rate=RATE)
        d = duration(mp3)
        lines.append({"id": ln["id"], "t0": round(t, 3), "t1": round(t + d, 3), "cap": ln["cap"], "mp3": mp3})
        t += d + ln.get("after", GAP)
    return lines, round(t - GAP + TAIL, 3)


def page(spec, lines, dur, path):
    tl = {"dur": dur, "fps": FPS, "lines": [{k: v for k, v in l.items() if k != "mp3"} for l in lines],
          "data": spec["data"]}
    js = lambda p: open(p, encoding="utf-8").read()  # noqa: E731
    head = f"""
const W = {W}, H = {H}, FPS = {FPS}, CX = 470, ISO_DARK = true;
const TL = {json.dumps(tl, ensure_ascii=False)};
"""
    style = spec.get("style", "isometric")
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: Anton; src: url('file://{FONTS}/Anton-Regular.ttf'); }}
@font-face {{ font-family: Oswald; src: url('file://{FONTS}/Oswald.ttf'); font-weight: 200 700; }}
html,body {{ margin:0; background:#000; }}
</style></head><body><canvas id="c" width="{W}" height="{H}"></canvas>
<span style="font-family:Anton;position:absolute;opacity:0">₺0</span><span style="font-family:Oswald;position:absolute;opacity:0">a</span>
<script>"use strict";
{head}
{js(os.path.join(VENDOR, 'core.js'))}
{js(os.path.join(VENDOR, style + '.js'))}
{js(os.path.join(HERE, 'brand.js'))}
{js(os.path.join(HERE, 'pieces', spec['scene']))}
const CANVAS = document.getElementById('c');
ctx = CANVAS.getContext('2d');
window.renderFrame = (f, png) => {{
  F = f; B = Math.floor(f / 2); TT = f / FPS; E0 = 0; DEFER = [];
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  drawPiece();
  screen(); for (const d of DEFER) d(); DEFER = null;
  return CANVAS.toDataURL(png ? 'image/png' : 'image/jpeg', 0.93).split(',')[1];
}};
Promise.all([document.fonts.load('60px Anton'), document.fonts.load('600 60px Oswald')]).then(() => {{ window.ANIM_READY = true; }});
</script></body></html>"""
    open(path, "w", encoding="utf-8").write(html)


def stills(html, times, out_prefix):
    node = f"""
const {{ chromium }} = require('/root/.cache/parafomo/anim-node/node_modules/playwright-core');
(async () => {{
  const b = await chromium.launch(); const p = await b.newPage({{ viewport: {{ width: {W}, height: {H} }} }});
  p.on('pageerror', e => {{ console.error('HATA', e.message); process.exitCode = 1; }});
  await p.goto('file://{html}'); await p.waitForFunction(() => window.ANIM_READY === true);
  for (const t of {json.dumps(times)}) {{
    const b64 = await p.evaluate(f => window.renderFrame(f, true), Math.round(t * {FPS}));
    require('fs').writeFileSync('{out_prefix}' + t + '.png', Buffer.from(b64, 'base64'));
    console.log('{out_prefix}' + t + '.png');
  }}
  await b.close();
}})();"""
    subprocess.run(["node", "-e", node], check=True)


def music_track(slug):
    tracks = sorted(f for f in os.listdir(MUSIC_DIR) if f.endswith(".mp3"))
    return os.path.join(MUSIC_DIR, tracks[int(hashlib.sha1(slug.encode()).hexdigest(), 16) % len(tracks)])


def audio(lines, dur, slug, out):
    inputs, chains = [], []
    for i, l in enumerate(lines):
        inputs += ["-i", l["mp3"]]
        ms = int(l["t0"] * 1000)
        chains.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{i}]")
    n = len(lines)
    mix = "".join(f"[v{i}]" for i in range(n))
    track = music_track(slug)
    g = (";".join(chains) + f";{mix}amix=inputs={n}:normalize=0,apad,atrim=0:{dur},asplit=2[n1][n2];"
         f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{dur},volume={MUSIC_VOL},"
         f"afade=t=out:st={dur - 1.5}:d=1.5[m];"
         f"[m][n1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[md];"
         f"[n2][md]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs, "-stream_loop", "-1", "-i", track,
         "-filter_complex", g, "-map", "[a]", "-c:a", "pcm_s16le", out])
    return os.path.basename(track)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--still", default="")
    ap.add_argument("--no-lock", action="store_true")
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding="utf-8"))
    slug = spec["slug"]
    wd = os.path.join(WORK, slug)
    os.makedirs(wd, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    lines, dur = timeline(spec)
    html = os.path.join(wd, "page.html")
    page(spec, lines, dur, html)
    print(f"[anim] {len(lines)} satır, {dur:.1f} sn")
    if a.still:
        stills(html, [float(x) for x in a.still.split(",")], os.path.join(wd, "still-"))
        return 0
    t0 = time.time()
    frames = int(round(dur * FPS))
    vid = os.path.join(wd, "video.mp4")
    cmd = ["nice", "-n", "19", "ionice", "-c3", "node", os.path.join(HERE, "render.mjs"), html, str(frames), str(FPS), vid]
    if not a.no_lock:
        cmd = ["flock", LOCK] + cmd
    subprocess.run(cmd, check=True)
    wav = os.path.join(wd, "mix.wav")
    track = audio(lines, dur, slug, wav)
    out = os.path.join(OUT_DIR, f"{slug}.mp4")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", vid, "-i", wav, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out])
    meta = {"slug": slug, "title": spec["title"], "file": out, "duration": dur, "music": track,
            "link": spec.get("link"), "lines": [{k: v for k, v in l.items() if k != "mp3"} for l in lines]}
    json.dump(meta, open(os.path.join(OUT_DIR, f"{slug}.meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[anim] ✅ {out} ({dur:.1f} sn, render {time.time() - t0:.0f} sn, müzik: {track})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
