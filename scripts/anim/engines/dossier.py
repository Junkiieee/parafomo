"""Yarışma motoru `dossier` — Lemo-Opuscar halftone-dossier stili (MIT, LemoLab) parametrik hali.

anim_build.py çağırır: render(spec, lines, dur, wd, W, H, lock) → sessiz 1080x1920 mp4 yolu.
Sahne şablonları engines/dossier/dossier.js; fontlar engines/fonts (OFL). Kare çizimi scripts/anim/render.mjs ile,
sonra doku iyi sıkışmadığı için bit hızı sınırlı yeniden kodlama (~2,4 Mbps → 40 sn ≈ 12 MB).
"""
import hashlib
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ANIM = os.path.dirname(HERE)
FONTS = os.path.join(HERE, "fonts")
FPS = 30


def _meta(spec):
    slug = spec.get("slug", "x")
    txt = " ".join(str(spec.get(k, "")) for k in ("source", "calc", "description"))
    no = int(hashlib.md5(slug.encode()).hexdigest(), 16) % 900 + 100
    yil = re.search(r"20\d\d", spec.get("title", "") + " " + txt)
    return {"slug": slug, "ornek": bool(re.search(r"örnek", txt, re.I)), "fileNo": f"{yil.group(0) if yil else '2026'}/{no:03d}",
            "no": no, "yil": yil.group(0) if yil else "2026"}


def page(spec, lines, dur, path):
    tl = {"dur": dur, "fps": FPS, "lines": [{k: v for k, v in l.items() if k != "mp3"} for l in lines], "data": spec["data"]}
    m = _meta(spec)
    js = open(os.path.join(HERE, "dossier", "dossier.js"), encoding="utf-8").read()
    ff = lambda n: "file://" + os.path.join(FONTS, n)  # noqa: E731
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: Slab; src: url('{ff("AlfaSlabOne-Regular.ttf")}'); font-display: block; }}
@font-face {{ font-family: Mono; src: url('{ff("IBMPlexMono-SemiBold.ttf")}'); font-weight: 600; font-display: block; }}
@font-face {{ font-family: Sans; src: url('{ff("Archivo-VF.ttf")}'); font-weight: 100 900; font-display: block; }}
html,body {{ margin:0; background:#000; overflow:hidden; }} canvas {{ display:block; }}
</style></head><body><canvas id="c"></canvas>
<span style="font-family:Slab;position:absolute;opacity:0">₺ş</span><span style="font-family:Sans;font-weight:900;position:absolute;opacity:0">₺ş</span><span style="font-family:Mono;font-weight:600;position:absolute;opacity:0">ş</span>
<script>"use strict";
const TL = {json.dumps(tl, ensure_ascii=False)};
const META = {json.dumps(m, ensure_ascii=False)};
META.nextNo = (k) => META.yil + '/' + String(META.no + k).padStart(3, '0');
{js}
</script></body></html>"""
    open(path, "w", encoding="utf-8").write(html)
    return path


def render(spec, lines, dur, wd, W, H, lock):
    html = page(spec, lines, dur, os.path.join(wd, "dossier.html"))
    raw, vid = os.path.join(wd, "dossier-raw.mp4"), os.path.join(wd, "dossier.mp4")
    frames = int(round(dur * FPS))
    cmd = ["nice", "-n", "19", "ionice", "-c3", "node", os.path.join(ANIM, "render.mjs"), html, str(frames), str(FPS), raw,
           str(W), str(H)]
    if lock:
        cmd = ["flock", lock] + cmd
    subprocess.run(cmd, check=True)
    subprocess.run(["nice", "-n", "19", "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", raw, "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "24", "-maxrate", "2400k", "-bufsize", "4800k", "-pix_fmt", "yuv420p",
                    "-threads", "1", "-an", vid], check=True)
    os.remove(raw)
    return vid
