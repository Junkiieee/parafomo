"""Yarışma motoru `news` — piyasa bülteni paketi (Lemo-Opuscar news-package stilinden, MIT © 2026 LemoLab).

anim_build.py sözleşmesi: render(spec, lines, dur, wd, W, H, lock) → sessiz mp4 yolu.
Sahne verisi spec["data"] (anim_from_scenario tipleri); çizim scripts/anim/engines/news/news.js.
Kaynak satırı yalnız spec'teki `source` (metin) ya da senaryoda "örnek" geçiyorsa "ÖRNEK HESAP" etiketi —
motor kendi bilgisinden kaynak/rakam eklemez.
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ANIM = os.path.dirname(HERE)
FONTS = os.path.join(HERE, "fonts")
FPS = 30


def _page(spec, lines, dur, W, H, path):
    blob = " ".join([spec.get("title", ""), spec.get("description", "")] + [l.get("cap", "") for l in lines])
    src = spec.get("source") if isinstance(spec.get("source"), str) else ""
    meta = {"title": spec.get("title", "").replace(" #Shorts", "").strip(),
            "ornek": "örnek" in blob.lower(), "source": src.strip()[:70]}
    tl = {"dur": dur, "fps": FPS, "lines": [{k: v for k, v in l.items() if k != "mp3"} for l in lines],
          "data": spec.get("data") or {}}
    fz = lambda n: "file://" + os.path.join(FONTS, n)  # noqa: E731
    js = open(os.path.join(HERE, "news", "news.js"), encoding="utf-8").read()
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: Bar; src: url('{fz("BarlowCondensed-ExtraBold.ttf")}'); font-weight: 800; }}
@font-face {{ font-family: Bar; src: url('{fz("BarlowCondensed-SemiBold.ttf")}'); font-weight: 600; }}
@font-face {{ font-family: Mono; src: url('{fz("IBMPlexMono-Medium.ttf")}'); font-weight: 500; }}
@font-face {{ font-family: Mono; src: url('{fz("IBMPlexMono-SemiBold.ttf")}'); font-weight: 600; }}
html,body {{ margin:0; background:#000; overflow:hidden; }} canvas {{ display:block; }}
</style></head><body><canvas id="c"></canvas>
<script>"use strict";
const W = {W}, H = {H}, FPS = {FPS};
const TL = {json.dumps(tl, ensure_ascii=False)};
const META = {json.dumps(meta, ensure_ascii=False)};
{js}
</script></body></html>"""
    open(path, "w", encoding="utf-8").write(html)


def render(spec, lines, dur, wd, W, H, lock):
    if W > H:
        raise SystemExit("news motoru yalnız dikey (9:16) Short içindir")
    d = os.path.join(wd, "news")
    os.makedirs(d, exist_ok=True)
    html, vid = os.path.join(d, "page.html"), os.path.join(d, "video.mp4")
    _page(spec, lines, dur, W, H, html)
    frames = int(round(dur * FPS))
    cmd = ["nice", "-n", "19", "ionice", "-c3", "node", os.path.join(ANIM, "render.mjs"), html, str(frames), str(FPS),
           vid, str(W), str(H)]
    if lock:
        cmd = ["flock", lock] + cmd
    subprocess.run(cmd, check=True)
    return vid


def stills(spec, lines, dur, wd, W, H, times, out_prefix):
    """Deneme: belirli saniyelerden PNG kareler (render.mjs olmadan, playwright ile)."""
    d = os.path.join(wd, "news")
    os.makedirs(d, exist_ok=True)
    html = os.path.join(d, "page.html")
    _page(spec, lines, dur, W, H, html)
    js = f"""
const {{ chromium }} = require('/root/.cache/parafomo/anim-node/node_modules/playwright-core');
(async () => {{
  const b = await chromium.launch({{ args: ['--disable-gpu'] }});
  const p = await b.newPage({{ viewport: {{ width: {W}, height: {H} }} }});
  p.on('pageerror', e => console.error('sayfa hatası:', e.message));
  await p.goto('file://{html}');
  await p.waitForFunction(() => window.ANIM_READY === true, null, {{ timeout: 30000 }});
  for (const t of {json.dumps(times)}) {{
    await p.evaluate(t => window.render(t), t);
    await p.locator('canvas').screenshot({{ path: '{out_prefix}' + t + '.png' }});
  }}
  await b.close();
}})();"""
    subprocess.run(["nice", "-n", "19", "node", "-e", js], check=True)
