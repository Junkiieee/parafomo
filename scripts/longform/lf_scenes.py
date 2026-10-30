"""16:9 hareketli bilgi-grafik sahneleri (PIL). Stok video YOK: her kare veriden çizilir.

Her sahne türü `spec` (senaryodaki "show" nesnesi) + zaman t + süre dur alır, 1920x1080 RGB kare döner.
Giriş animasyonu bittikten sonra içerik sabitlenir (önbellek) ve yalnız hafif bir yakınlaşma uygulanır.

Türler: title, chapter, bigstat, compare, table, bars, steps, bullets, timeline, quote, cta
"""
import functools
import math
import re

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from lf_common import (ANTON, BG, BG2, BRAND, DEEP, FPS, GOLD, H, LIGHT, LINE, MUTED, OSWALD,
                       PANEL, RED, SANS_B, W, WHITE, tr_num)

M = 140  # yatay kenar boşluğu


# ───────────────────────── yardımcılar ─────────────────────────

@functools.lru_cache(maxsize=256)
def font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight:
        try:
            f.set_variation_by_name(weight)
        except Exception:
            pass
    return f


def osw(size, weight="Bold"):
    return font(OSWALD, size, weight)


def anton(size):
    return font(ANTON, size)


def tr_upper(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def prog(t, start, length):
    return ease((t - start) / length) if length > 0 else (1.0 if t >= start else 0.0)


def mix(c1, c2, a):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * a) for i in range(3))


def tw(draw, text, f):
    b = draw.textbbox((0, 0), text, font=f)
    return b[2] - b[0]


def fit(draw, text, maker, max_w, start, minimum=20):
    s = start
    while s > minimum and tw(draw, text, maker(s)) > max_w:
        s -= 4
    return maker(s)


def wrap(draw, text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        cand = (cur + " " + w_).strip()
        if tw(draw, cand, f) <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def text_at(draw, xy, text, f, fill, a=1.0, anchor="la"):
    if a <= 0:
        return
    draw.text(xy, text, font=f, fill=mix(BG, fill, a), anchor=anchor)


NUM_RE = re.compile(r"^(?P<pre>[^\d]*)(?P<num>\d[\d.]*(?:,\d+)?)(?P<suf>.*)$")


def countup(value, p):
    """'%27,81' / '7.349 TL' / '≈17.139 TL' → p∈[0,1] oranında sayan metin (biçim korunur)."""
    m = NUM_RE.match(value.strip())
    if not m or p >= 1:
        return value
    raw = m.group("num")
    dec = len(raw.split(",")[1]) if "," in raw else 0
    try:
        x = float(raw.replace(".", "").replace(",", "."))
    except ValueError:
        return value
    return f"{m.group('pre')}{tr_num(x * p, dec)}{m.group('suf')}"


@functools.lru_cache(maxsize=1)
def background():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for y in range(H):  # dikey hafif gradyan
        d.line([(0, y), (W, y)], fill=mix(BG2, BG, y / H))
    grid = Image.new("RGB", (W, H), (0, 0, 0))
    g = ImageDraw.Draw(grid)
    for x in range(0, W, 120):
        g.line([(x, 0), (x, H)], fill=(10, 12, 13))
    for y in range(0, H, 120):
        g.line([(0, y), (W, y)], fill=(10, 12, 13))
    img = Image.blend(img, Image.composite(grid, img, grid.convert("L").point(lambda v: 60 if v else 0)), 0.5)
    # kenar karartma (vignette)
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-W * 0.25, -H * 0.35, W * 1.25, H * 1.35], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(220))
    dark = Image.new("RGB", (W, H), (6, 8, 9))
    return Image.composite(img, dark, vig)


def badge(draw, x, y, text, a, color=RED, size=44):
    if a <= 0 or not text:
        return 0
    f = osw(size, "Bold")
    t = tr_upper(text)
    w_ = tw(draw, t, f) + 44
    h_ = int(size * 1.55)
    draw.rectangle([x, y, x + w_, y + h_], fill=mix(BG, color, a))
    draw.text((x + 22, y + h_ // 2), t, font=f, fill=mix(color, WHITE, a), anchor="lm")
    return h_


# ───────────────────────── sahneler ─────────────────────────
# Her sahne: draw(img, d, spec, t, dur) → None; anim_end(spec, dur) → içerik sabitlendiği an (s)

def s_title(img, d, sp, t, dur):
    y = 300
    bh = badge(d, M, y, sp.get("badge", ""), prog(t, 0, 0.3))
    if bh:
        y += bh + 40
    f = anton(150)
    lines = wrap(d, tr_upper(sp.get("headline", "")), f, W - 2 * M)
    if len(lines) > 3:
        f = anton(110)
        lines = wrap(d, tr_upper(sp.get("headline", "")), f, W - 2 * M)
    p = prog(t, 0.1, 0.55)
    for i, ln in enumerate(lines):
        text_at(d, (M, y + int((1 - p) * 40)), ln, f, WHITE if i else GOLD, p)
        y += int(f.size * 1.12)
    if sp.get("sub"):
        f2 = osw(52, "Regular")
        for ln in wrap(d, sp["sub"], f2, W - 2 * M)[:2]:
            text_at(d, (M, y + 30), ln, f2, MUTED, prog(t, 0.45, 0.5))
            y += 70


def s_chapter(img, d, sp, t, dur):
    p = prog(t, 0, 0.6)
    x0 = M + int((1 - p) * -60)
    num = f"{int(sp.get('n', 1)):02d}"
    text_at(d, (x0, H // 2), num, anton(300), BRAND, p, anchor="lm")
    bx = x0 + tw(d, num, anton(300)) + 60
    d.rectangle([bx, H // 2 - 150, bx + 10, H // 2 + 150], fill=mix(BG, BRAND, p))
    tx = bx + 60
    text_at(d, (tx, H // 2 - 150), "BÖLÜM " + num, osw(46, "Medium"), MUTED, prog(t, 0.15, 0.5), anchor="lm")
    lines = wrap(d, tr_upper(sp.get("title", "")), osw(96, "Bold"), W - tx - M)[:2]
    y = H // 2 - 30 if len(lines) == 1 else H // 2 - 70
    for ln in lines:
        text_at(d, (tx, y), ln, osw(96, "Bold"), WHITE, prog(t, 0.2, 0.5), anchor="lm")
        y += 115


def s_bigstat(img, d, sp, t, dur):
    cy = H // 2 + 10
    if sp.get("badge"):
        badge(d, M, 150, sp["badge"], prog(t, 0, 0.3))
    if sp.get("label"):
        f = fit(d, tr_upper(sp["label"]), lambda s: osw(s, "SemiBold"), W - 2 * M, 64)
        text_at(d, (W // 2, cy - 230), tr_upper(sp["label"]), f, MUTED, prog(t, 0, 0.4), anchor="mm")
    val = countup(sp.get("value", ""), prog(t, 0.15, 1.0))
    f = fit(d, sp.get("value", ""), anton, W - 2 * M, 320)
    text_at(d, (W // 2, cy), val, f, GOLD, prog(t, 0.1, 0.3), anchor="mm")
    if sp.get("note"):
        f2 = osw(50, "Regular")
        y = cy + 210
        for ln in wrap(d, sp["note"], f2, W - 2 * M - 200)[:2]:
            text_at(d, (W // 2, y), ln, f2, WHITE, prog(t, 0.7, 0.5), anchor="mm")
            y += 66


def s_compare(img, d, sp, t, dur):
    if sp.get("label"):
        f = fit(d, tr_upper(sp["label"]), lambda s: osw(s, "SemiBold"), W - 2 * M, 72)
        text_at(d, (W // 2, 230), tr_upper(sp["label"]), f, WHITE, prog(t, 0, 0.4), anchor="mm")
    cy = H // 2 + 40
    lx, rx = W // 4 + 30, 3 * W // 4 - 30
    side_w = 2 * min(lx - M + 40, (W // 2 - 110) - lx)   # ok bölgesine taşmasın
    fv = fit(d, max(sp.get("before", ""), sp.get("after", ""), key=lambda v: tw(d, v, anton(190))),
             anton, side_w, 190)
    pa = prog(t, 0.1, 0.4)
    text_at(d, (lx, cy - 170), sp.get("before_label", ""), osw(54, "Medium"), MUTED, pa, anchor="mm")
    text_at(d, (lx, cy), sp.get("before", ""), fv, MUTED, pa, anchor="mm")
    # ok
    pa2 = prog(t, 0.45, 0.35)
    if pa2 > 0:
        ax = W // 2
        d.line([(ax - 70, cy), (ax - 70 + int(120 * pa2), cy)], fill=BRAND, width=12)
        if pa2 > 0.9:
            d.polygon([(ax + 60, cy), (ax + 20, cy - 34), (ax + 20, cy + 34)], fill=BRAND)
    pb = prog(t, 0.6, 0.3)
    text_at(d, (rx, cy - 170), sp.get("after_label", ""), osw(54, "Medium"), GOLD, pb, anchor="mm")
    text_at(d, (rx, cy), countup(sp.get("after", ""), prog(t, 0.6, 0.9)), fv, GOLD, pb, anchor="mm")
    if sp.get("note"):
        f2 = osw(48, "Regular")
        y = cy + 200
        for ln in wrap(d, sp["note"], f2, W - 2 * M)[:2]:
            text_at(d, (W // 2, y), ln, f2, WHITE, prog(t, 1.1, 0.5), anchor="mm")
            y += 62


def s_table(img, d, sp, t, dur):
    rows = sp.get("rows", [])[:7]
    cols = sp.get("cols", [])
    n = max(len(cols), max((len(r) for r in rows), default=0))
    if not n:
        return
    y = 150
    if sp.get("title"):
        f = fit(d, tr_upper(sp["title"]), lambda s: osw(s, "Bold"), W - 2 * M, 64)
        text_at(d, (M, y), tr_upper(sp["title"]), f, WHITE, prog(t, 0, 0.4))
        y += 110
    rh = min(104, int((H - y - 130) / (len(rows) + 1)))
    fs = int(rh * 0.46)
    first_w = int((W - 2 * M) * (0.46 if n >= 3 else 0.6))
    other_w = ((W - 2 * M) - first_w) // max(1, n - 1)
    xs = [M] + [M + first_w + other_w * (i + 1) for i in range(n - 1)]
    hl = sp.get("highlight_col", n - 1)
    ph = prog(t, 0.1, 0.4)
    for i, c in enumerate(cols[:n]):
        f = osw(int(fs * 0.85), "Medium")
        text_at(d, (xs[i] if i == 0 else xs[i] - 24, y + rh // 2), tr_upper(c), f,
                GOLD if i == hl and i else MUTED, ph, anchor="lm" if i == 0 else "rm")
    y += rh
    d.line([(M, y), (W - M, y)], fill=mix(BG, LINE, ph), width=2)
    for r_i, row in enumerate(rows):
        p = prog(t, 0.3 + r_i * 0.14, 0.4)
        if p <= 0:
            break
        if r_i % 2 == 0:
            d.rectangle([M - 20, y + 4, W - M + 20, y + rh - 4], fill=mix(BG, PANEL, p))
        for i, cell in enumerate(row[:n]):
            if i == 0:
                f = fit(d, str(cell), lambda s: osw(s, "Regular"), first_w - 30, fs)
                text_at(d, (xs[0], y + rh // 2), str(cell), f, WHITE, p, anchor="lm")
            else:
                f = osw(fs, "Bold" if i == hl else "Regular")
                text_at(d, (xs[i] - 24, y + rh // 2), str(cell), f, GOLD if i == hl else WHITE, p,
                        anchor="rm")
        y += rh
    if sp.get("note"):
        text_at(d, (M, H - 120), sp["note"], osw(36, "Regular"), MUTED, prog(t, 0.8, 0.5))


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def s_bars(img, d, sp, t, dur):
    items = sp.get("items", [])[:9]
    if not items:
        return
    y0 = 150
    if sp.get("title"):
        f = fit(d, tr_upper(sp["title"]), lambda s: osw(s, "Bold"), W - 2 * M, 64)
        text_at(d, (M, y0), tr_upper(sp["title"]), f, WHITE, prog(t, 0, 0.4))
    vmax = max(_num(it.get("value")) for it in items) or 1
    hl = str(sp.get("highlight", ""))
    long_labels = max(len(str(it.get("label", ""))) for it in items) > 9
    if long_labels:  # yatay çubuklar
        top, bottom = 290, H - 130
        bh = min(96, (bottom - top) // len(items))
        lw = 520
        for i, it in enumerate(items):
            p = prog(t, 0.2 + i * 0.1, 0.6)
            y = top + i * bh
            col = GOLD if str(it.get("label")) == hl else BRAND
            text_at(d, (M + lw - 30, y + bh // 2), str(it.get("label", "")),
                    fit(d, str(it.get("label", "")), lambda s: osw(s, "Regular"), lw - 40, int(bh * 0.42)),
                    WHITE, min(1, p * 2), anchor="rm")
            full = (W - 2 * M - lw - 260) * _num(it.get("value")) / vmax
            d.rectangle([M + lw, y + bh * 0.18, M + lw + max(4, full * p), y + bh * 0.82], fill=mix(BG, col, min(1, p * 2)))
            text_at(d, (M + lw + full * p + 24, y + bh // 2), str(it.get("text", it.get("value"))),
                    osw(int(bh * 0.44), "Bold"), col, p, anchor="lm")
        return
    base = H - 210
    top = 330
    n = len(items)
    slot = (W - 2 * M) / n
    bw = slot * 0.56
    d.line([(M, base), (W - M, base)], fill=LINE, width=3)
    for i, it in enumerate(items):
        p = prog(t, 0.2 + i * 0.09, 0.7)
        cx = M + slot * (i + 0.5)
        hgt = (base - top) * _num(it.get("value")) / vmax * p
        col = GOLD if str(it.get("label")) == hl else BRAND
        d.rectangle([cx - bw / 2, base - hgt, cx + bw / 2, base], fill=mix(BG, col, min(1, p * 2)))
        text_at(d, (cx, base + 46), str(it.get("label", "")), osw(44, "Medium"),
                WHITE if col == GOLD else MUTED, min(1, p * 2), anchor="mm")
        if p > 0.6:
            text_at(d, (cx, base - hgt - 40), str(it.get("text", it.get("value"))), osw(46, "Bold"),
                    col, (p - 0.6) / 0.4, anchor="mm")


def _reveal_times(n, dur):
    span = max(1.0, dur * 0.7)
    return [0.25 + i * span / max(1, n) for i in range(n)]


def s_steps(img, d, sp, t, dur, bullets=False):
    lines = sp.get("lines" if not bullets else "items", [])[:6]
    y = 170
    if sp.get("title"):
        f = fit(d, tr_upper(sp["title"]), lambda s: osw(s, "Bold"), W - 2 * M, 64)
        text_at(d, (M, y), tr_upper(sp["title"]), f, WHITE, prog(t, 0, 0.4))
        y += 140
    gap = min(150, (H - y - 140) // max(1, len(lines)))
    times = _reveal_times(len(lines), dur)
    for i, ln in enumerate(lines):
        p = prog(t, times[i], 0.45)
        if p <= 0:
            break
        result = (not bullets) and str(ln).strip().startswith("=")
        cy = y + gap // 2
        if bullets:
            d.rectangle([M, cy - 14, M + 28, cy + 14], fill=mix(BG, BRAND, p))
        else:
            d.ellipse([M, cy - 30, M + 60, cy + 30], fill=mix(BG, GOLD if result else BRAND, p))
            text_at(d, (M + 30, cy), str(i + 1), osw(36, "Bold"), BG, 1 if p > 0.5 else 0, anchor="mm")
        f = fit(d, str(ln), lambda s: osw(s, "Bold" if result else "Regular"), W - 2 * M - 120,
                76 if result else 58)
        text_at(d, (M + 100 + int((1 - p) * 30), cy), str(ln), f, GOLD if result else WHITE, p, anchor="lm")
        y += gap


def s_bullets(img, d, sp, t, dur):
    s_steps(img, d, sp, t, dur, bullets=True)


def s_timeline(img, d, sp, t, dur):
    items = sp.get("items", [])[:5]
    if not items:
        return
    if sp.get("title"):
        f = fit(d, tr_upper(sp["title"]), lambda s: osw(s, "Bold"), W - 2 * M, 64)
        text_at(d, (M, 170), tr_upper(sp["title"]), f, WHITE, prog(t, 0, 0.4))
    ly = H // 2 + 20
    pl = prog(t, 0.1, 0.8)
    d.line([(M, ly), (M + (W - 2 * M) * pl, ly)], fill=LINE, width=6)
    slot = (W - 2 * M) / len(items)
    times = _reveal_times(len(items), dur)
    for i, it in enumerate(items):
        p = prog(t, times[i], 0.45)
        if p <= 0:
            break
        cx = M + slot * (i + 0.5)
        hot = bool(it.get("hot"))
        col = GOLD if hot else BRAND
        r = 22 if hot else 16
        d.ellipse([cx - r, ly - r, cx + r, ly + r], fill=mix(BG, col, p))
        text_at(d, (cx, ly - 80), it.get("date", ""), fit(d, it.get("date", ""), lambda s: osw(s, "Bold"),
                slot - 30, 52), col, p, anchor="mm")
        f = osw(36, "Regular")
        yy = ly + 70
        for ln in wrap(d, it.get("text", ""), f, slot - 40)[:3]:
            text_at(d, (cx, yy), ln, f, WHITE, p, anchor="mm")
            yy += 48


def s_quote(img, d, sp, t, dur):
    p = prog(t, 0, 0.5)
    text_at(d, (M, 250), "“", anton(260), BRAND, p, anchor="lm")
    f = osw(64, "Medium")
    lines = wrap(d, sp.get("text", ""), f, W - 2 * M - 120)
    if len(lines) > 5:
        f = osw(52, "Medium")
        lines = wrap(d, sp.get("text", ""), f, W - 2 * M - 120)
    y = 380
    for ln in lines[:7]:
        text_at(d, (M + 60, y), ln, f, WHITE, prog(t, 0.15, 0.5))
        y += int(f.size * 1.3)
    if sp.get("source"):
        text_at(d, (M + 60, y + 40), "— " + sp["source"], osw(42, "Regular"), MUTED, prog(t, 0.5, 0.5))


def s_cta(img, d, sp, t, dur):
    p = prog(t, 0, 0.5)
    f = anton(120)
    y = 260
    for ln in wrap(d, tr_upper(sp.get("headline", "")), f, W - 2 * M)[:2]:
        text_at(d, (W // 2, y), ln, f, WHITE, p, anchor="mm")
        y += 135
    url = sp.get("url", "parafomo.com")
    fu = osw(70, "Bold")
    uw = tw(d, url, fu) + 100
    pu = prog(t, 0.3, 0.5)
    yy = y + 70
    d.rounded_rectangle([W // 2 - uw // 2, yy, W // 2 + uw // 2, yy + 120], radius=60, fill=mix(BG, BRAND, pu))
    text_at(d, (W // 2, yy + 60), url, fu, BG if pu > 0.5 else BRAND, 1, anchor="mm")
    if sp.get("sub"):
        text_at(d, (W // 2, yy + 200), sp["sub"], osw(46, "Regular"), MUTED, prog(t, 0.5, 0.5), anchor="mm")
    # abone düğmesi (nabız)
    pb = prog(t, 0.8, 0.4)
    if pb > 0:
        s = 1 + 0.04 * math.sin(t * 4)
        bw_, bh_ = int(420 * s), int(110 * s)
        bx, by = W // 2 - bw_ // 2, yy + 300
        d.rounded_rectangle([bx, by, bx + bw_, by + bh_], radius=18, fill=mix(BG, RED, pb))
        f = font(SANS_B, int(54 * s))
        lbl = "ABONE OL"
        tx = W // 2 + 28
        d.polygon([(tx - tw(d, lbl, f) // 2 - 62, by + bh_ // 2 - 22), (tx - tw(d, lbl, f) // 2 - 62, by + bh_ // 2 + 22),
                   (tx - tw(d, lbl, f) // 2 - 24, by + bh_ // 2)], fill=mix(RED, WHITE, pb))
        text_at(d, (tx, by + bh_ // 2), lbl, f, WHITE, pb, anchor="mm")


SCENES = {"title": s_title, "chapter": s_chapter, "bigstat": s_bigstat, "compare": s_compare,
          "table": s_table, "bars": s_bars, "steps": s_steps, "bullets": s_bullets,
          "timeline": s_timeline, "quote": s_quote, "cta": s_cta}
def anim_end(sp, dur):
    k = sp.get("kind")
    if k in ("steps", "bullets", "timeline"):
        n = len(sp.get("lines") or sp.get("items") or [])
        return _reveal_times(max(1, n), dur)[-1] + 0.5
    if k == "table":
        return 0.3 + len(sp.get("rows", [])) * 0.14 + 0.9
    if k == "cta":
        return dur + 1  # abone düğmesi sürekli nabız atıyor
    if k in ("bigstat", "compare"):
        return 1.7
    if k == "bars":
        return 0.2 + len(sp.get("items", [])) * 0.09 + 0.8
    return 1.0


def draw_content(sp, t, dur):
    img = background().copy()
    d = ImageDraw.Draw(img)
    SCENES.get(sp.get("kind"), s_title)(img, d, sp, t, dur)
    return img


# ───────────────────────── HUD: bölüm etiketi + ilerleme çubuğu ─────────────────────────

def draw_hud(img, chapter_label, t_global, total, chapters):
    """chapters: [(start_s, end_s)] — alt çubukta bölüm aralıkları; dolu kısım = izlenen."""
    d = ImageDraw.Draw(img)
    if chapter_label:
        d.rectangle([60, 52, 72, 88], fill=BRAND)
        d.text((88, 70), tr_upper(chapter_label), font=osw(30, "Medium"), fill=MUTED, anchor="lm")
    d.text((W - 60, 70), "parafomo.com", font=osw(30, "Medium"), fill=MUTED, anchor="rm")
    y = H - 14
    for (a, b) in chapters:
        x0 = 60 + (W - 120) * a / total + 3
        x1 = 60 + (W - 120) * b / total - 3
        d.rectangle([x0, y - 5, x1, y + 1], fill=LINE)
        if t_global > a:
            xf = min(x1, 60 + (W - 120) * t_global / total)
            if xf > x0:
                d.rectangle([x0, y - 5, xf, y + 1], fill=BRAND)
    return img


def zoom(img, s):
    if s <= 1.0005:
        return img
    zw, zh = int(W * s), int(H * s)
    big = img.resize((zw, zh), Image.BILINEAR)
    x, y = (zw - W) // 2, (zh - H) // 2
    return big.crop((x, y, x + W, y + H))


# ───────────────────────── kapak (1280x720) ─────────────────────────

def thumbnail(spec, out_path):
    """spec: {"top": "2027 ZAMLARI", "big": "%27,8", "bottom": "NELER ARTIYOR?"} — kapakta en fazla
    3-4 kelime; başlığı tekrar etmez (başlık+kapak birlikte denetlenir, lf_package)."""
    TW, TH = 1280, 720
    img = background().resize((TW, TH), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    # sol kırmızı blok + üst yazı
    top = tr_upper(spec.get("top", ""))
    if top:
        f = fit(d, top, lambda s: osw(s, "Bold"), TW - 120, 78)
        w_ = tw(d, top, f) + 60
        d.rectangle([40, 50, 40 + w_, 50 + int(f.size * 1.5)], fill=RED)
        d.text((70, 50 + int(f.size * 0.75)), top, font=f, fill=WHITE, anchor="lm")
    big = spec.get("big", "")
    fb = fit(d, big, anton, TW - 100, 330)
    # okunurluk için koyu gölge
    sh = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((TW // 2 + 8, TH // 2 + 38), big, font=fb, fill=(0, 0, 0, 200), anchor="mm")
    img.paste(sh.filter(ImageFilter.GaussianBlur(10)), (0, 0), sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(img)
    d.text((TW // 2, TH // 2 + 30), big, font=fb, fill=GOLD, anchor="mm")
    bot = tr_upper(spec.get("bottom", ""))
    if bot:
        f = fit(d, bot, lambda s: osw(s, "Bold"), TW - 120, 84)
        d.rectangle([0, TH - 130, TW, TH], fill=(0, 0, 0))
        d.text((TW // 2, TH - 65), bot, font=f, fill=WHITE, anchor="mm")
    d.rectangle([0, 0, TW, 10], fill=BRAND)
    img.save(out_path, "JPEG", quality=92)
    return out_path
