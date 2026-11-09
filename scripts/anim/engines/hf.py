"""Yarışma motoru `hf` — HeyGen HyperFrames (Apache-2.0) ile senaryo → sessiz 1080x1920 mp4.

Kaan 2026-11-06: "hepsini 1 ay deneyelim, en çok izlenen kazansın". anim_build.py sesi, kelime zamanlamasını,
müziği ve metayı kendisi üretir; bu modül yalnız görüntüyü çizer:

    render(spec, lines, dur, wd, W, H, lock) -> sessiz mp4 yolu

spec["data"] = {"eyebrow", "scenes": [{"type", "head", "data", "line"}]} (tipler: anim_from_scenario.TYPES).
Kurulum (repo dışı, sabit sürüm):
    mkdir -p /root/.cache/parafomo/hf-node && cd /root/.cache/parafomo/hf-node && \
    echo '{"private":true}' > package.json && npm i --ignore-scripts hyperframes@0.9.19 gsap@3.15.0
Render ağsız: GSAP yerel dosyadan satır içine gömülür, fontlar yerel.
"""
import html as H_
import json
import os
import re
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TPL = os.path.join(HERE, "hf")
HF_NODE = os.environ.get("HF_NODE", "/root/.cache/parafomo/hf-node")
HF_BIN = os.path.join(HF_NODE, "node_modules", ".bin", "hyperframes")
GSAP = os.path.join(HF_NODE, "node_modules", "gsap", "dist", "gsap.min.js")
BROWSER = "/root/.cache/ms-playwright/chromium_headless_shell-1148/chrome-linux/headless_shell"
FONTS = {"Anton-Regular.ttf": os.path.join(ROOT, "assets", "fonts", "Anton-Regular.ttf"),
         "Oswald.ttf": os.path.join(ROOT, "assets", "fonts", "Oswald.ttf"),
         "IBMPlexMono-Medium.ttf": os.path.join(HERE, "fonts", "IBMPlexMono-Medium.ttf")}
INSTALL = ("mkdir -p /root/.cache/parafomo/hf-node && cd /root/.cache/parafomo/hf-node && "
           "echo '{\"private\":true}' > package.json && npm i --ignore-scripts hyperframes@0.9.19 gsap@3.15.0")

E = H_.escape


# ---------------------------------------------------------------- sayı biçimi (scenes.js fmtVal ile aynı kural)
def dec_of(v):
    if abs(v - round(v)) < 1e-9:
        return 0
    return 1 if abs(v * 10 - round(v * 10)) < 1e-9 else 2


def fmt_num(v, d=None):
    d = dec_of(v) if d is None else d
    s = f"{abs(v):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if v < 0 else "") + s


def val_parts(v, unit="", suffix=""):
    """→ (önek, sayı, sonek, ondalık, sayılacak değer)."""
    money = unit in ("₺", "$", "€")
    if money and abs(v) >= 100:
        v, d = round(v), 0
    else:
        d = dec_of(v)
    sx = f" {suffix}" if suffix else ""
    n = fmt_num(v, d)
    if money:
        return unit, n, sx, d, v
    if unit == "%":
        return "%", n, "", d, v
    if unit == "x":
        return "", n, "x", d, v
    return "", n, sx + (f" {unit}" if unit else ""), d, v


def fmt_val(v, unit="", suffix=""):
    p, n, s, _, _ = val_parts(v, unit, suffix)
    return p + n + s


# ---------------------------------------------------------------- kelime zamanları
def _norm(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def word_times(line):
    caps = line["cap"].split()
    ts = line.get("words") or []
    if len(ts) != len(caps):   # hizalama yoksa orantılı dağıt
        n = max(1, len(caps))
        ts = [line["t0"] + (line["t1"] - line["t0"]) * i / n for i in range(len(caps))]
    ends = [ts[i + 1] if i + 1 < len(ts) else line["t1"] for i in range(len(ts))]
    return list(zip(caps, ts, ends))


def find_t(line, needles, frac=0.35):
    """needles'tan birini içeren ilk kelimenin başlangıcı; yoksa satırın frac noktası."""
    ws = word_times(line)
    for nd in needles:
        nd = _norm(str(nd)).strip()
        if not nd:
            continue
        for w, t, _ in ws:
            if nd in _norm(w):
                return t
    return line["t0"] + (line["t1"] - line["t0"]) * frac


def num_needles(v, suffix=""):
    out = [fmt_num(v), fmt_num(round(v)) if abs(v) >= 100 else ""]
    if abs(v) >= 1000 and abs(v) % 1000 == 0:
        out.append(fmt_num(v / 1000))
    return [x for x in out if x]


def spread_t(line, k, n):
    """k. maddenin tahmini anı: satırda t0+0,3 → t0+%65·süre arasında eşit yayılım."""
    a, b = line["t0"] + 0.3, line["t0"] + 0.65 * (line["t1"] - line["t0"])
    return a if n <= 1 else a + (max(a, b) - a) * k / (n - 1)


def seq_t(line, needles, k, n):
    """Eşleşen kelime anı, ama en geç tahmin anı (eşleşme yoksa tahmin)."""
    est = spread_t(line, k, n)
    hit = find_t(line, needles, frac=-1)
    return est if hit < line["t0"] else min(hit, est)


# ---------------------------------------------------------------- ikonlar (düz SVG, viewBox 200)
ICON = {
    "coins": '<ellipse cx="100" cy="150" rx="70" ry="24" fill="#C9962E"/><rect x="30" y="118" width="140" height="32" fill="#E8B23A"/>'
             '<ellipse cx="100" cy="118" rx="70" ry="24" fill="#FFC94D"/><ellipse cx="100" cy="88" rx="70" ry="24" fill="#C9962E"/>'
             '<rect x="30" y="58" width="140" height="30" fill="#E8B23A"/><ellipse cx="100" cy="58" rx="70" ry="24" fill="#FFD978"/>'
             '<text x="100" y="70" text-anchor="middle" font-family="Anton" font-size="34" fill="#8A6414">₺</text>',
    "gold": '<polygon points="40,150 70,70 130,70 160,150" fill="#E8B23A"/><polygon points="70,70 130,70 120,90 80,90" fill="#FFD978"/>'
            '<polygon points="40,150 160,150 150,165 50,165" fill="#C9962E"/>',
    "cash": '<rect x="25" y="55" width="150" height="90" rx="10" fill="#2BB194"/><rect x="38" y="68" width="124" height="64" rx="6" fill="none" stroke="#12302A" stroke-width="5"/>'
            '<circle cx="100" cy="100" r="22" fill="#12302A"/><text x="100" y="112" text-anchor="middle" font-family="Anton" font-size="32" fill="#63D491">₺</text>',
    "house": '<polygon points="100,30 175,95 25,95" fill="#E3120B"/><rect x="45" y="95" width="110" height="80" fill="#F4EFE2"/>'
             '<rect x="85" y="125" width="32" height="50" fill="#2BB194"/><rect x="55" y="110" width="22" height="22" fill="#63B4E6"/>',
    "car": '<path d="M30 120 L50 80 Q55 70 70 70 L130 70 Q145 70 150 80 L170 120 Z" fill="#E3120B"/><rect x="22" y="115" width="156" height="35" rx="10" fill="#E3120B"/>'
           '<rect x="62" y="80" width="76" height="32" rx="5" fill="#63B4E6"/><circle cx="60" cy="152" r="18" fill="#1a1a1a"/><circle cx="140" cy="152" r="18" fill="#1a1a1a"/>',
    "bank": '<polygon points="100,25 180,70 20,70" fill="#F4EFE2"/><rect x="30" y="160" width="140" height="18" fill="#F4EFE2"/>'
            '<rect x="42" y="80" width="18" height="74" fill="#C9D3CF"/><rect x="77" y="80" width="18" height="74" fill="#C9D3CF"/>'
            '<rect x="112" y="80" width="18" height="74" fill="#C9D3CF"/><rect x="142" y="80" width="18" height="74" fill="#C9D3CF"/>',
    "calendar": '<rect x="30" y="40" width="140" height="135" rx="14" fill="#F4EFE2"/><rect x="30" y="40" width="140" height="38" rx="14" fill="#E3120B"/>'
                '<rect x="30" y="62" width="140" height="16" fill="#E3120B"/><rect x="60" y="25" width="12" height="30" rx="6" fill="#3a464c"/>'
                '<rect x="128" y="25" width="12" height="30" rx="6" fill="#3a464c"/><rect x="110" y="125" width="34" height="30" rx="5" fill="#2BB194"/>',
    "chart": '<rect x="35" y="120" width="28" height="50" fill="#2BB194"/><rect x="78" y="95" width="28" height="75" fill="#2BB194"/>'
             '<rect x="121" y="65" width="28" height="105" fill="#63D491"/><polyline points="30,105 80,75 115,85 170,35" fill="none" stroke="#FFC94D" stroke-width="10"/>'
             '<polygon points="172,30 150,34 168,52" fill="#FFC94D"/>',
    "percent": '<circle cx="62" cy="62" r="28" fill="none" stroke="#FFC94D" stroke-width="16"/><circle cx="138" cy="138" r="28" fill="none" stroke="#FFC94D" stroke-width="16"/>'
               '<line x1="150" y1="40" x2="50" y2="160" stroke="#FFC94D" stroke-width="18" stroke-linecap="round"/>',
    "card": '<rect x="22" y="50" width="156" height="100" rx="14" fill="#3E6FD8"/><rect x="22" y="72" width="156" height="22" fill="#1a1a1a"/>'
            '<rect x="40" y="110" width="40" height="26" rx="5" fill="#FFC94D"/><rect x="100" y="118" width="60" height="10" rx="5" fill="#C9D9FF"/>',
    "piggy": '<ellipse cx="100" cy="110" rx="70" ry="52" fill="#E05A8A"/><circle cx="160" cy="105" r="18" fill="#F07BA3"/>'
             '<rect x="60" y="150" width="18" height="28" fill="#E05A8A"/><rect x="120" y="150" width="18" height="28" fill="#E05A8A"/>'
             '<rect x="85" y="62" width="34" height="8" rx="4" fill="#3A1424"/><circle cx="140" cy="95" r="6" fill="#3A1424"/>',
}


def icon(name, cls, id_):
    body = ICON.get(name) or ICON["coins"]
    return (f'<svg id="{id_}" class="{cls}" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">'
            f'<circle cx="100" cy="100" r="98" fill="#1B2429" stroke="#2A363C" stroke-width="3"/>'
            f'<g transform="translate(20 20) scale(.8)">{body}</g></svg>')


def anton_fit(text, width, size, ratio=0.5):
    """Anton yaklaşık karakter genişliği ≈ 0,5 em → genişliğe sığan en büyük boyut."""
    n = max(1, len(text))
    return int(min(size, width / (ratio * n)))


# ---------------------------------------------------------------- sahne kurucular
class Scene:
    def __init__(self, i, sc, line, s, e, first):
        self.i, self.sc, self.d, self.line, self.s, self.e, self.first = i, sc, sc.get("data") or {}, line, s, e, first
        self.js = []

    def id(self, x):
        return f"s{self.i}{x}"

    def at(self, t):   # sahne içinde güvenli zaman
        return max(self.s + 0.05, min(t, self.e - 0.35))

    def enter(self, sel, t, frm, to=None, dur=0.45, ease="expo.out"):
        """Sahne 0'da (kanca) öğeler ilk karede hazır: giriş animasyonu yok."""
        if self.first:
            return
        to = to or {}
        to_s = ", ".join(f"{k}: {json.dumps(v)}" for k, v in to.items())
        self.js.append(f"tl.fromTo('{sel}', {{{frm}}}, {{{to_s + ', ' if to_s else ''}duration: {dur}, ease: '{ease}'}}, {self.at(t):.3f});")

    def counter(self, el, val, d, t, dur=0.9):
        if self.first:
            return
        t1 = self.at(t)
        t0 = max(self.s + 0.05, t1 - dur)
        self.js.append(f"(() => {{ const o = {{ v: 0 }}; const el = '{el}'; tl.fromTo(o, {{ v: 0 }}, {{ v: {val}, duration: {t1 - t0 + 0.01:.3f}, "
                       f"ease: 'power2.out', onUpdate: () => {{ document.getElementById(el).textContent = fmtN(o.v, {d}); }} }}, {t0:.3f}); }})();")

    # --- tipler
    def big_number(self):
        d = self.d
        p, n, sx, dec, cv = val_parts(float(d.get("value", 0)), d.get("unit", ""), d.get("suffix", ""))
        full = p + n + sx
        fs = anton_fit(full, 960, 320)
        t = find_t(self.line, num_needles(float(d.get("value", 0))))
        self.enter(f"#{self.id('ic')}", t - 0.6, "opacity: 0, scale: 0.6", {"opacity": 1, "scale": 1}, 0.4, "back.out(1.7)")
        self.enter(f"#{self.id('bv')}", t - 0.9, "opacity: 0, scale: 0.8", {"opacity": 1, "scale": 1}, 0.4)
        self.counter(self.id("n"), cv, dec, t)
        self.enter(f"#{self.id('lb')}", t + 0.1, "opacity: 0, y: 30", {"opacity": 1, "y": 0}, 0.4, "power3.out")
        lb = d.get("label", "")
        return (icon(d.get("icon"), "bn-icon", self.id("ic")) +
                f'<div id="{self.id("bv")}" class="bn-val" style="font-size:{fs}px"><span>{E(p)}</span>'
                f'<span id="{self.id("n")}">{E(n)}</span><span>{E(sx)}</span></div>'
                f'<div id="{self.id("lb")}" class="bn-label">{E(lb)}</div>')

    def _cols(self, items, unit, suffix, hl, gap, width, vsize, maxh=430, spread=False):
        vals = [abs(float(x.get("value", 0))) for x in items]
        mx = max(vals + [1e-9])
        out = []
        for k, x in enumerate(items):
            v = float(x.get("value", 0))
            p, n, sx, dec, cv = val_parts(v, unit, suffix)
            h = max(24, int(maxh * abs(v) / mx))
            on = (k == hl)
            color = "var(--gold)" if on else ("var(--green)" if hl is None and k == len(items) - 1 else "#E37B4F" if k == 0 else "#5B6B70")
            vcol = "var(--gold)" if on else "var(--ink)"
            fs = min(vsize, anton_fit(p + n + sx, width + gap - 10, vsize))
            if spread:   # bars: maddeler satıra yayılır, eşleşme geç kalırsa tahmin tavandır
                t = seq_t(self.line, num_needles(v), k, len(items))
            else:
                t = find_t(self.line, num_needles(v), frac=0.2 + 0.6 * k / max(1, len(items) - 1) if len(items) > 1 else 0.4)
            self.enter(f"#{self.id('b%d' % k)}", t - 0.35, "scaleY: 0", {"scaleY": 1}, 0.6)
            self.enter(f"#{self.id('v%d' % k)}", t - 0.05, "opacity: 0, y: 24", {"opacity": 1, "y": 0}, 0.3, "power3.out")
            self.enter(f"#{self.id('l%d' % k)}", t - 0.35, "opacity: 0", {"opacity": 1}, 0.3, "power1.out")
            self.counter(self.id("n%d" % k), cv, dec, t + 0.25, 0.6)
            out.append(f'<div class="col" style="width:{width}px">'
                       f'<div id="{self.id("v%d" % k)}" class="col-v" style="font-size:{fs}px;color:{vcol}">{E(p)}'
                       f'<span id="{self.id("n%d" % k)}">{E(n)}</span>{E(sx)}</div>'
                       f'<div id="{self.id("b%d" % k)}" class="col-bar" style="width:{width - 20}px;height:{h}px;background:{color}"></div>'
                       f'<div id="{self.id("l%d" % k)}" class="col-l">{E(str(x.get("label", "")))}</div></div>')
        return f'<div class="cols" style="gap:{gap}px">{"".join(out)}</div>'

    def compare(self):
        d = self.d
        a, b = d.get("a") or {}, d.get("b") or {}
        html = self._cols([a, b], d.get("unit", ""), d.get("suffix", ""), 1, 120, 300, 110, spread=True)
        if d.get("note"):
            tb = seq_t(self.line, num_needles(float(b.get("value", 0))), 1, 2)
            self.enter(f"#{self.id('nt')}", tb + 0.5, "opacity: 0, scale: 1.6", {"opacity": 1, "scale": 1}, 0.28, "power4.in")
            html += f'<div id="{self.id("nt")}" class="note"><span>{E(d["note"])}</span></div>'
        return html

    def bars(self):
        d = self.d
        items = (d.get("items") or [])[:6]
        n = max(1, len(items))
        gap = 40 if n > 3 else 90
        width = min(260, int((940 - gap * (n - 1)) / n))
        hl = d.get("hl")
        return self._cols(items, d.get("unit", ""), d.get("suffix", ""), hl if isinstance(hl, int) else None, gap, width,
                          100 if n <= 3 else 64, maxh=480, spread=True)

    def layers(self):
        d = self.d
        unit = d.get("unit", "")
        tot = d.get("total") or {}
        parts = (d.get("parts") or [])[:4]
        s = sum(abs(float(p.get("value", 0))) for p in parts) or 1
        cols = ["#4F7BD8", "#2BB194", "#E37B4F", "#B57BE0"]
        p_, n_, sx_, dec_, cv_ = val_parts(float(tot.get("value", 0)), unit)
        tt = find_t(self.line, num_needles(float(tot.get("value", 0))), frac=0.7)
        self.enter(f"#{self.id('tot')} .t-l", self.s + 0.1, "opacity: 0, y: -30", {"opacity": 1, "y": 0}, 0.4, "power3.out")
        # toplam, söylendiği anda damga gibi gelir (önceden "₺0" görünmesin)
        self.enter(f"#{self.id('tot')} .t-v", tt - 0.25, "opacity: 0, scale: 1.5", {"opacity": 1, "scale": 1}, 0.3, "power4.in")
        segs, rows = [], []
        for k, pt in enumerate(parts):
            v = float(pt.get("value", 0))
            on = bool(pt.get("hl"))
            c = "var(--gold)" if on else cols[k % len(cols)]
            t = find_t(self.line, num_needles(v), frac=0.25 + 0.5 * k / max(1, len(parts) - 1) if len(parts) > 1 else 0.4)
            t = min(t, self.s + 0.7 + 1.1 * k)   # çubuk uzun süre boş kalmasın: parçalar sahne başında dolar
            self.enter(f"#{self.id('g%d' % k)}", t - 0.3, "scaleX: 0", {"scaleX": 1}, 0.55)
            self.enter(f"#{self.id('r%d' % k)}", t - 0.3, "opacity: 0, x: -60", {"opacity": 1, "x": 0}, 0.4)
            segs.append(f'<div id="{self.id("g%d" % k)}" class="ly-seg" style="width:{100 * abs(v) / s:.2f}%;background:{c}"></div>')
            rows.append(f'<div id="{self.id("r%d" % k)}" class="ly-row{" on" if on else ""}"><div class="r-l"><i style="background:{c}"></i>'
                        f'{E(str(pt.get("label", "")))}</div><div class="r-v">{E(fmt_val(v, unit))}</div></div>')
        return (f'<div id="{self.id("tot")}" class="ly-total"><div class="t-l">{E(str(tot.get("label", "")))}</div>'
                f'<div class="t-v">{E(p_)}<span id="{self.id("tn")}">{E(n_)}</span>{E(sx_)}</div></div>'
                f'<div class="ly-bar">{"".join(segs)}</div><div class="ly-rows">{"".join(rows)}</div>')

    def steps(self):
        items = [str(x) for x in (self.d.get("items") or [])][:4]
        n = max(1, len(items))
        fs = 66 if max((len(x) for x in items), default=0) <= 20 else 56
        out, prev = [], self.s
        for k, it in enumerate(items):
            stem = [w[:5] for w in re.findall(r"\w+", it) if len(w) >= 4][:1]
            t = seq_t(self.line, stem, k, n)
            t = max(t, prev + 0.4)
            prev = t
            self.enter(f"#{self.id('p%d' % k)}", t - 0.3, "opacity: 0, x: -90", {"opacity": 1, "x": 0}, 0.45)
            last = " last" if k == n - 1 and n >= 3 else ""
            out.append(f'<div id="{self.id("p%d" % k)}" class="step{last}"><div class="num">{k + 1}</div>'
                       f'<div class="st" style="font-size:{fs}px">{E(it)}</div></div>')
        return f'<div class="steps">{"".join(out)}</div>'

    def icon_text(self):
        d = self.d
        txt = str(d.get("text", ""))
        plain = txt.replace("*", "")
        fs = 132 if len(plain) <= 18 else 112 if len(plain) <= 30 else 94 if len(plain) <= 44 else 80
        parts = re.split(r"\*([^*]+)\*", txt)
        out, ems = [], []
        for k, p in enumerate(parts):
            if k % 2:
                ems.append(p)
                out.append(f'<span id="{self.id("em%d" % len(ems))}" class="em">{E(p)}</span>')
            else:
                out.append(E(p))
        self.enter(f"#{self.id('ic')}", self.s + 0.05, "opacity: 0, scale: 0.6, rotation: -10", {"opacity": 1, "scale": 1, "rotation": 0}, 0.5, "back.out(1.6)")
        self.enter(f"#{self.id('tx')}", self.s + 0.15, "opacity: 0, y: 40", {"opacity": 1, "y": 0}, 0.4, "power3.out")
        for k, em in enumerate(ems, 1):
            w = [x for x in re.findall(r"[\w,%.]+", em) if len(x) >= 2][:1]
            t = find_t(self.line, [w[0][:6]] if w else [], frac=0.4)
            if self.first:   # kanca karesi: vurgu ilk karede dolu
                self.js.append(f"tl.set('#{self.id('em%d' % k)}', {{ backgroundSize: '100% 80%', color: '#0F1316' }}, 0);")
            else:   # vurgu gelene kadar sarı yazı, şerit gelince koyu yazı (koyu zeminde hiç kaybolmaz)
                self.js.append(f"tl.fromTo('#{self.id('em%d' % k)}', {{ backgroundSize: '0% 80%', color: '#FFC94D' }}, "
                               f"{{ backgroundSize: '100% 80%', color: '#0F1316', duration: 0.35, ease: 'power2.out' }}, {self.at(t - 0.1):.3f});")
        return (icon(d.get("icon"), "it-icon", self.id("ic")) +
                f'<div id="{self.id("tx")}" class="it-text" style="font-size:{fs}px"><div>{"".join(out)}</div></div>')

    def cta(self):
        d = self.d
        l1, l2, sub = str(d.get("l1", "")), str(d.get("l2", "")), str(d.get("sub", ""))
        f1 = anton_fit(l1, 900, 150, 0.52)
        f2 = anton_fit(l2, 860, 150, 0.52)
        ta = find_t(self.line, ["abone"], frac=0.7)
        self.enter(f"#{self.id('q1')}", self.s + 0.05, "opacity: 0, y: 40, filter: 'blur(6px)'", {"opacity": 1, "y": 0, "filter": "blur(0px)"}, 0.3)
        self.enter(f"#{self.id('q2')}", self.s + 0.3, "opacity: 0, scale: 0.8", {"opacity": 1, "scale": 1}, 0.35, "back.out(1.6)")
        self.enter(f"#{self.id('sub')}", self.s + 0.8, "opacity: 0", {"opacity": 1}, 0.3, "power1.out")
        self.enter(f"#{self.id('ab')}", ta - 0.2, "scale: 0, opacity: 0", {"scale": 1, "opacity": 1}, 0.5, "elastic.out(1, 0.5)")
        self.enter(f"#{self.id('br')}", ta + 0.6, "opacity: 0, y: 20", {"opacity": 1, "y": 0}, 0.35, "power3.out")
        return (f'<div class="cta-q"><div id="{self.id("q1")}" style="font-size:{f1}px">{E(l1)}</div>'
                f'<div id="{self.id("q2")}" class="l2" style="font-size:{f2}px"><span class="hl">{E(l2)}</span></div></div>'
                f'<div id="{self.id("sub")}" class="cta-sub">{E(sub)}</div>'
                f'<div id="{self.id("ab")}" class="abone"><div class="play"></div>ABONE OL</div>'
                f'<div id="{self.id("br")}" class="brand">parafomo.com</div>')

    def build(self):
        typ = self.sc.get("type")
        fn = getattr(self, typ, None) if typ in ("big_number", "layers", "bars", "compare", "steps", "icon_text", "cta") else None
        if fn is None:
            raise ValueError(f"hf: bilinmeyen sahne tipi {typ!r}")
        body = fn()
        head = str(self.sc.get("head", ""))
        hs = 96 if len(head) <= 18 else 84
        if not self.first:
            self.js.insert(0, f"tl.fromTo('#{self.id('hd')}', {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.3, ease: 'power3.out' }}, {self.s + 0.02:.3f});")
        # sürekli küçük hareket: görsel yavaşça büyür (statik kare olmasın)
        self.js.append(f"tl.fromTo('#{self.id('vz')}', {{ scale: 1 }}, {{ scale: 1.035, duration: {self.e - self.s:.3f}, ease: 'none' }}, {self.s:.3f});")
        if self.e is not None and not self.last:
            self.js.append(f"tl.to('#{self.id('hd')}, #{self.id('vz')}', {{ opacity: 0, filter: 'blur(8px)', duration: 0.18, ease: 'power2.in' }}, {self.e - 0.2:.3f});")
        return (f'<div id="sc{self.i}" class="clip scene" data-start="{self.s:.3f}" data-duration="{self.e - self.s:.3f}" data-track-index="1">'
                f'<div id="{self.id("hd")}" class="head" style="font-size:{hs}px"><div>{E(head)}</div></div>'
                f'<div id="{self.id("vz")}" class="viz">{body}</div></div>')


# ---------------------------------------------------------------- altyazı
def captions(lines, dur):
    groups = []
    for l in lines:
        ws = word_times(l)
        cur = []
        for k, w in enumerate(ws):
            cur.append(w)
            if len(cur) >= 4 or (w[0][-1] in ".,;:?!" and len(cur) >= 2) or k == len(ws) - 1:
                groups.append(cur)
                cur = []
    hs, js = [], []
    for gi, g in enumerate(groups):
        g0 = max(0.0, g[0][1] - 0.08)
        nxt = groups[gi + 1][0][1] - 0.08 if gi + 1 < len(groups) else dur
        g1 = min(g[-1][2] + 0.25, nxt)
        if g1 - g0 < 0.12:
            g1 = g0 + 0.12
        spans = " ".join(f'<span class="w" id="c{gi}w{k}">{E(w[0])}</span>' for k, w in enumerate(g))
        hs.append(f'<div id="cap{gi}" class="clip capg" data-start="{g0:.3f}" data-duration="{g1 - g0:.3f}" data-track-index="9">'
                  f'<div class="capin" id="ci{gi}">{spans}</div></div>')
        js.append(f"tl.fromTo('#ci{gi}', {{ opacity: 0, y: 18 }}, {{ opacity: 1, y: 0, duration: 0.14, ease: 'power3.out' }}, {g0:.3f});")
        for k, w in enumerate(g):
            js.append(f"tl.set('#c{gi}w{k}', {{ className: 'w on' }}, {w[1]:.3f});")
            e = g[k + 1][1] if k + 1 < len(g) else g1
            js.append(f"tl.set('#c{gi}w{k}', {{ className: 'w' }}, {max(w[1] + 0.05, e - 0.01):.3f});")
    return hs, js


# ---------------------------------------------------------------- kompozisyon
def compose(spec, lines, dur):
    data = spec.get("data") or {}
    scenes = data.get("scenes") or []
    if not scenes:
        raise ValueError("hf: spec.data.scenes boş")
    by_id = {l["id"]: l for l in lines}
    starts = []
    for i, sc in enumerate(scenes):
        ln = by_id.get(sc.get("line")) or lines[min(i, len(lines) - 1)]
        starts.append(0.0 if i == 0 else max(starts[-1] + 0.6, ln["t0"] - 0.15))
    objs, html_sc, js = [], [], []
    for i, sc in enumerate(scenes):
        ln = by_id.get(sc.get("line")) or lines[min(i, len(lines) - 1)]
        e = starts[i + 1] if i + 1 < len(scenes) else dur
        s = Scene(i, sc, ln, starts[i], e, i == 0)
        s.last = i == len(scenes) - 1
        html_sc.append(s.build())
        js += s.js
        objs.append(s)
    if scenes[0].get("type") in ("big_number", "compare", "layers", "icon_text"):   # kanca: 0,5 sn'de vurgu darbesi
        js.append("tl.fromTo('#s0vz', { x: 0 }, { x: 12, duration: 0.05, yoyo: true, repeat: 5, ease: 'none' }, 0.55);")
    segs = "".join(f'<div class="seg"><i id="pg{i}"></i></div>' for i in range(len(scenes)))
    for o in objs:
        js.append(f"tl.fromTo('#pg{o.i}', {{ scaleX: 0 }}, {{ scaleX: 1, duration: {max(0.1, o.e - o.s):.3f}, ease: 'none' }}, {o.s:.3f});")
    js.append(f"tl.fromTo('#grid', {{ y: 0 }}, {{ y: -240, duration: {dur:.3f}, ease: 'none' }}, 0);")
    cap_h, cap_j = captions(lines, dur)
    js += cap_j
    css = open(os.path.join(TPL, "style.css"), encoding="utf-8").read()
    fonts = ("@font-face { font-family: 'Anton'; src: url('assets/fonts/Anton-Regular.ttf'); }\n"
             "@font-face { font-family: 'OswaldV'; src: url('assets/fonts/Oswald.ttf'); font-weight: 200 700; }\n"
             "@font-face { font-family: 'PlexMono'; src: url('assets/fonts/IBMPlexMono-Medium.ttf'); }\n")
    gsap = open(GSAP, encoding="utf-8").read()
    eb = str(data.get("eyebrow", ""))
    script = ("const tl = gsap.timeline({ paused: true });\n"
              "const fmtN = (v, d) => { const s = Math.abs(v).toFixed(d).split('.'); s[0] = s[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, '.'); "
              "return (v < 0 ? '-' : '') + s.join(','); };\n" + "\n".join(js) +
              "\nwindow.__timelines = window.__timelines || {};\nwindow.__timelines['main'] = tl;\ntl.seek(0);\n")
    return f"""<!doctype html>
<html lang="tr" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script>{gsap}</script>
<style>{fonts}{css}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur:.3f}" data-width="1080" data-height="1920">
  <div id="bg" class="clip" data-start="0" data-duration="{dur:.3f}" data-track-index="0" data-layout-ignore><div id="grid"></div></div>
  <div id="eyebrow" class="clip" data-start="0" data-duration="{dur:.3f}" data-track-index="2">{E(eb)}</div>
  {chr(10).join(html_sc)}
  <div id="foot" class="clip" data-start="0" data-duration="{dur:.3f}" data-track-index="3">{segs}<span class="mark">PARAFOMO</span></div>
  {chr(10).join(cap_h)}
</div>
<script>{script}</script>
</body>
</html>
"""


def _env():
    env = dict(os.environ, HYPERFRAMES_NO_TELEMETRY="1", DO_NOT_TRACK="1", HYPERFRAMES_NO_UPDATE_CHECK="1",
               HYPERFRAMES_BROWSER_PATH=BROWSER, PUPPETEER_EXECUTABLE_PATH=BROWSER)
    return env


def project(spec, lines, dur, wd):
    proj = os.path.join(wd, "hf")
    if os.path.isdir(proj):
        shutil.rmtree(proj)
    os.makedirs(os.path.join(proj, "assets", "fonts"))
    for name, src in FONTS.items():
        shutil.copy(src, os.path.join(proj, "assets", "fonts", name))
    json.dump({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
               "media": {"autoProxy": False}}, open(os.path.join(proj, "hyperframes.json"), "w"), indent=2)
    json.dump({"id": spec["slug"][:60], "name": spec["slug"][:60]}, open(os.path.join(proj, "meta.json"), "w"))
    open(os.path.join(proj, "index.html"), "w", encoding="utf-8").write(compose(spec, lines, dur))
    return proj


def check(proj):
    r = subprocess.run(["nice", "-n", "19", HF_BIN, "check", proj, "--json", "--samples", "7", "--no-browser-gpu"],
                       capture_output=True, text=True, env=_env(), timeout=600)
    try:
        rep = json.loads(r.stdout[r.stdout.index("{"):])
    except Exception:
        raise RuntimeError(f"hf check çıktısı okunamadı: {(r.stderr or r.stdout)[-400:]}")
    errs = []
    def walk(x):
        if isinstance(x, dict):
            if x.get("severity") == "error":
                errs.append(f"{x.get('code')}: {x.get('message', '')[:140]} [{x.get('selector', '')}]")
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(rep)
    json.dump(rep, open(os.path.join(proj, "check.json"), "w"), ensure_ascii=False, indent=1)
    if not rep.get("ok") or errs:
        raise RuntimeError("hf check hatası:\n  " + "\n  ".join(errs[:12] or ["ok=false (ayrıntı: check.json)"]))
    return rep


def render(spec, lines, dur, wd, W, H, lock):
    if W != 1080 or H != 1920:
        raise NotImplementedError("hf motoru yalnız 9:16 Short (1080x1920)")
    if not (os.path.exists(HF_BIN) and os.path.exists(GSAP)):
        raise RuntimeError("HyperFrames kurulu değil. Kur: " + INSTALL)
    proj = project(spec, lines, dur, wd)
    check(proj)
    out = os.path.join(wd, "video-hf.mp4")
    cmd = ["nice", "-n", "19", "ionice", "-c3", HF_BIN, "render", proj, "-o", out, "--fps", "30", "--workers", "1",
           "--crf", "20", "--no-browser-gpu", "--quiet"]
    if lock:
        cmd = ["flock", lock] + cmd
    r = subprocess.run(cmd, env=_env(), capture_output=True, text=True, timeout=3600)
    if r.returncode != 0 or not os.path.exists(out):
        raise RuntimeError(f"hf render başarısız: {(r.stderr or r.stdout)[-600:]}")
    return out
