"""Görüntü motoru `hikaye` — "Para hikâyeleri" (2026-11-17, Kaan'ın beğendiği Miselyum tarzı + senaryo kitabı).

Düz vektör karakterler (hikaye_kit.py) + koyu atmosferik zemin + kelime kelime renkli altyazı, HyperFrames ile
sessiz 1080x1920 mp4. Ses, kelime zamanlaması, müzik ve meta anim_build.py'den gelir (diğer motorlarla aynı sözleşme):

    render(spec, lines, dur, wd, W, H, lock) -> sessiz mp4 yolu

Senaryo kitabındaki görsel kurallar burada uygulanır:
  - Kare 0 boş/karartma değil: ilk sahne t=0'da hazır, karakter zaten olayın içinde.
  - Kanca kartı (≤6 kelime) yalnız ilk ~2,2 sn; sonra yalnız altyazı.
  - Altyazı 1–3 kelimelik gruplar, alt menü bölgesinin üstünde; *yıldızlı* kelimeler ve rakamlar vurgulu.
  - Rakamlar ekranda en az 1,5 sn kalır; her sahne bir anlatı vuruşu (satır).

spec["data"] = {
  "tema": "gece" | "alacakaranlik" | "dram",
  "kanca": ["ERİYEN", "*YÜZLÜK*"],
  "scenes": [{
     "line": "s0",
     "baslik": ["Bu yüzlük", "*eriyor*"],          # isteğe bağlı üst başlık (en çok 2 satır)
     "etiket": "2016",                             # isteğe bağlı hap etiket
     "oyuncular": [{"id": "a", "k": "yuzluk", "ifade": "endiseli", "x": 540, "y": 1000, "olcek": 1.0,
                    "giris": "yok|zipla|sol|sag|alt", "olaylar": [{"kelime": "eriyor", "ifade": "korkmus",
                    "eylem": "kucul|titre|zipla|erit|git|bak", "deger": 0.7, "x": 300, "y": 900}]}],
     "dekor": [{"d": "simit", "adet": 12, "kalan": 5, "kelime": "bugün", "x": 540, "y": 1180, "olcek": 0.45}],
     "sayi": {"deger": 600, "birim": "simit", "onek": "", "not": "2016", "kelime": "600", "y": 520},
     "vs": {"sol": {"k": "altin", "etiket": "Altın", "deger": "+%5"}, "sag": {"k": "yuzluk", "etiket": "Dolar", "deger": "+%17"}},
     "cubuk": {"a": {"etiket": "2016", "deger": 600}, "b": {"etiket": "Bugün", "deger": 248}, "birim": "simit", "not": "2,4 kat az"},
     "gosterge": {"bas": 0, "son": 7, "birim": "atm", "not": "×3 araba lastiği", "kelime": "..."},
     "soru": true                                  # kapanış: yorum balonu + soru vurgusu
  }]
}
"""
import html as H_
import json
import os
import re
import shutil
import subprocess

from . import hikaye_kit as kit
from .hf import GSAP, HF_BIN, INSTALL, _env, _norm, check, find_t, fmt_num, word_times

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FONT_DIR = os.path.join(ROOT, "public", "fonts")
FONTS = {"inter-latin.woff2": os.path.join(FONT_DIR, "inter-latin.woff2"),
         "inter-latin-ext.woff2": os.path.join(FONT_DIR, "inter-latin-ext.woff2"),
         "Anton-Regular.ttf": os.path.join(ROOT, "assets", "fonts", "Anton-Regular.ttf")}
E = H_.escape
W, H = 1080, 1920
VURGU = "#ffb547"

TEMA = {
    "gece": ("radial-gradient(120% 70% at 50% 42%, #1f4134 0%, #10261f 45%, #08110e 100%)", "#cfe9dc", "#2f6b55"),
    "alacakaranlik": ("linear-gradient(180deg, #14213d 0%, #23305a 45%, #5b3d63 72%, #9c4f2c 100%)", "#ffe6c7", "#3b2f4a"),
    "dram": ("radial-gradient(110% 60% at 50% 38%, #18262c 0%, #0b1216 55%, #050709 100%)", "#bcd3dc", "#22343b"),
}


def _yuzde(b):
    """Birim yüzde mi? Türkçede yüzde işareti sayının ÖNÜNE yazılır (%21,2)."""
    return (b or "").strip() == "%"


def _vurgula(metin):
    """*kelime* → vurgu rengi; geri kalan kaçışlı."""
    parts = re.split(r"(\*[^*]+\*)", metin or "")
    return "".join(f'<b class="vz">{E(p[1:-1])}</b>' if p.startswith("*") and p.endswith("*") else E(p) for p in parts)


def _t(line, kelime, frac=0.35):
    return find_t(line, [kelime], frac) if kelime else line["t0"] + (line["t1"] - line["t0"]) * frac


# ---------------------------------------------------------------- altyazı (1–3 kelime, vurgulu)
CAP_GEN = 21.0   # 78 px kalın altyazı, 980 px: "Tabloda bugünkü aylığına" (20,7) sığar, "Memur emeklisinde %10,75." (23,1) taşar


def _gen(s):
    """Altyazı satırının yaklaşık genişliği (ortalama harf = 1)."""
    w = 0.0
    for ch in s:
        if ch == " ":
            w += 0.35
        elif ch in "iıIlj.,;:'!|":
            w += 0.45
        elif ch in "fjtr":
            w += 0.7
        elif ch in "MWmw%@₺":
            w += 1.45
        elif ch.isupper() or ch.isdigit():
            w += 1.15
        else:
            w += 1.0
    return w


def captions(lines, dur, vurgu_kelimeler=()):
    """Vurgu: rakam içeren kelimeler + spec.data.vurgu listesindeki kelimeler (altyazı metni yıldızsız kalır ki
    whisper hizalaması bozulmasın)."""
    vk = {_norm(re.sub(r"[^\w%₺']", "", w)) for w in vurgu_kelimeler}
    hs, js, groups = [], [], []
    for l in lines:
        ham = l["cap"].split()
        vurgu = [bool(re.search(r"\d", w)) or _norm(re.sub(r"[^\w%₺']", "", w)) in vk for w in ham]
        ws = word_times(l)
        cur = []
        for k, w in enumerate(ws):
            # Genişlik: grup tek satıra sığmazsa ikinci satır kaynak yazısının üstüne biniyordu (2026-11-17, "Memur
            # emeklisinde %10,75."). Bu kelime satırı taşıracaksa önce mevcut grubu kapat.
            if cur and _gen(" ".join(x[0][0] for x in cur) + " " + w[0]) > CAP_GEN:
                groups.append(cur)
                cur = []
            cur.append((w, vurgu[k] if k < len(vurgu) else False))
            if len(cur) >= 3 or (w[0][-1] in ".,;:?!…" and len(cur) >= 1) or k == len(ws) - 1:
                groups.append(cur)
                cur = []
    for gi, g in enumerate(groups):
        g0 = max(0.0, g[0][0][1] - 0.06)
        nxt = groups[gi + 1][0][0][1] - 0.06 if gi + 1 < len(groups) else dur
        g1 = max(g0 + 0.15, min(g[-1][0][2] + 0.2, nxt))
        spans = " ".join(f'<span class="w{" vz" if v else ""}" id="c{gi}w{k}">{E(w[0])}</span>' for k, (w, v) in enumerate(g))
        hs.append(f'<div id="cap{gi}" class="clip capg" data-start="{g0:.3f}" data-duration="{g1 - g0:.3f}" data-track-index="9">'
                  f'<div class="capin" id="ci{gi}">{spans}</div></div>')
        js.append(f"tl.fromTo('#ci{gi}', {{ scale: 0.86, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.12, ease: 'back.out(2)' }}, {g0:.3f});")
        for k, (w, _) in enumerate(g):
            js.append(f"tl.set('#c{gi}w{k}', {{ className: '{'w vz on' if g[k][1] else 'w on'}' }}, {w[1]:.3f});")
    return hs, js


# ---------------------------------------------------------------- sahne
class Sahne:
    def __init__(self, i, sc, line, s, e, kanca=False):
        self.i, self.sc, self.line, self.s, self.e = i, sc, line, s, e
        self.kanca = kanca
        self.js, self.parca = [], []

    def at(self, t):
        return max(self.s, min(self.e - 0.05, t))

    def oyuncu(self, o, n):
        kid = f"s{self.i}{o.get('id', 'o' + str(n))}"
        x, y, olc = float(o.get("x", 540)), float(o.get("y", 1000)), float(o.get("olcek", 1.0))
        svg_k = kit.karakter(o["k"], o.get("ifade", "normal"), kid)
        size = 600 * olc
        self.parca.append(f'<div class="oyuncu" id="{kid}w" style="left:{x - size / 2:.0f}px;top:{y - size / 2:.0f}px;'
                          f'width:{size:.0f}px;height:{size:.0f}px"><svg viewBox="0 0 600 600" width="100%" height="100%">'
                          f'{svg_k}</svg></div>')
        g = o.get("giris", "yok")
        s = self.s
        if g == "zipla":
            self.js.append(f"tl.fromTo('#{kid}w', {{ y: 60, scale: 0.6 }}, {{ y: 0, scale: 1, duration: 0.35, ease: 'back.out(2.2)' }}, {s:.3f});")
        elif g in ("sol", "sag"):
            dx = -900 if g == "sol" else 900
            self.js.append(f"tl.fromTo('#{kid}w', {{ x: {dx} }}, {{ x: 0, duration: 0.45, ease: 'power3.out' }}, {s:.3f});")
        elif g == "alt":
            self.js.append(f"tl.fromTo('#{kid}w', {{ y: 700 }}, {{ y: 0, duration: 0.45, ease: 'power3.out' }}, {s:.3f});")
        # canlılık: hafif nefes + göz kırpma (enflasyon dahil her karakterde göz grubu var)
        d = max(0.4, self.e - self.s)
        self.js.append(f"tl.fromTo('#{kid}', {{ scaleY: 1 }}, {{ scaleY: 1.025, duration: 0.9, repeat: {int(d / 0.9)}, yoyo: true, "
                       f"ease: 'sine.inOut', transformOrigin: '50% 100%' }}, {s:.3f});")
        for kk in range(int(d // 2.6)):
            tb = s + 1.1 + kk * 2.6
            self.js.append(f"tl.to('#{kid}-gozler', {{ scaleY: 0.1, duration: 0.07, yoyo: true, repeat: 1, transformOrigin: '50% 50%' }}, {tb:.3f});")
        for ev in o.get("olaylar", []):
            t = self.at(_t(self.line, ev.get("kelime"), ev.get("frac", 0.5)))
            if ev.get("ifade"):   # ifade değişimi: yeni yüz SVG'si üst üste, eskisini gizle
                yeni = f"{kid}x{len(self.parca)}"
                self.parca.append(f'<div class="oyuncu ifade" id="{yeni}w" style="left:{x - size / 2:.0f}px;top:{y - size / 2:.0f}px;'
                                  f'width:{size:.0f}px;height:{size:.0f}px;opacity:0"><svg viewBox="0 0 600 600" width="100%" '
                                  f'height="100%">{kit.karakter(o["k"], ev["ifade"], yeni)}</svg></div>')
                self.js.append(f"tl.set('#{kid}w', {{ opacity: 0 }}, {t:.3f}); tl.set('#{yeni}w', {{ opacity: 1 }}, {t:.3f});")
                kid_eski, kid = kid, yeni
            hedef = f"#{kid}w"
            e = ev.get("eylem")
            if e == "kucul":
                self.js.append(f"tl.to('.oyuncu[id^=\"s{self.i}{o.get('id', 'o' + str(n))}\"]', {{ scale: {float(ev.get('deger', 0.6))}, "
                               f"duration: 0.5, ease: 'power2.inOut', transformOrigin: '50% 90%' }}, {t:.3f});")
            elif e == "erit":
                self.js.append(f"tl.to('.oyuncu[id^=\"s{self.i}{o.get('id', 'o' + str(n))}\"]', {{ scaleY: {float(ev.get('deger', 0.55))}, "
                               f"scaleX: 1.12, duration: 0.8, ease: 'power1.in', transformOrigin: '50% 95%' }}, {t:.3f});")
            elif e == "titre":
                self.js.append(f"tl.fromTo('{hedef}', {{ x: 0 }}, {{ x: 14, duration: 0.05, yoyo: true, repeat: 7, ease: 'none' }}, {t:.3f});")
            elif e == "zipla":
                self.js.append(f"tl.to('{hedef}', {{ y: -90, duration: 0.18, yoyo: true, repeat: 1, ease: 'power2.out' }}, {t:.3f});")
            elif e == "git":
                self.js.append(f"tl.to('.oyuncu[id^=\"s{self.i}{o.get('id', 'o' + str(n))}\"]', {{ x: {float(ev.get('x', x)) - x:.0f}, "
                               f"y: {float(ev.get('y', y)) - y:.0f}, duration: 0.6, ease: 'power2.inOut' }}, {t:.3f});")

    def dekor(self, d, n):
        adet, kalan = int(d.get("adet", 1)), d.get("kalan")
        olc = float(d.get("olcek", 0.5))
        size = 200 * olc
        sut = min(adet, int(d.get("sutun", 6)))
        satir = (adet + sut - 1) // sut
        x0 = float(d.get("x", 540)) - sut * size * 1.08 / 2
        y0 = float(d.get("y", 1150)) - satir * size * 1.08 / 2
        for k in range(adet):
            did = f"s{self.i}d{n}_{k}"
            px, py = x0 + (k % sut) * size * 1.08, y0 + (k // sut) * size * 1.08
            self.parca.append(f'<div class="dekor" id="{did}" style="left:{px:.0f}px;top:{py:.0f}px;width:{size:.0f}px;height:{size:.0f}px">'
                              f'<svg viewBox="0 0 200 200" width="100%" height="100%">{kit.dekor(d["d"], did + "g")}</svg></div>')
            self.js.append(f"tl.fromTo('#{did}', {{ scale: 0 }}, {{ scale: 1, duration: 0.25, ease: 'back.out(2)' }}, {self.s + 0.05 + k * 0.035:.3f});")
        if kalan is not None:
            t = self.at(_t(self.line, d.get("kelime"), 0.55))
            for k in range(int(kalan), adet):
                self.js.append(f"tl.to('#s{self.i}d{n}_{k}', {{ opacity: 0.12, scale: 0.8, duration: 0.2 }}, {t + (k - int(kalan)) * 0.04:.3f});")

    def sayi(self, sy):
        y = int(sy.get("y", 470))
        v = float(sy["deger"])
        d = 0 if abs(v - round(v)) < 1e-9 else (1 if abs(v * 10 - round(v * 10)) < 1e-9 else 2)   # 7,75 → 7,75 (7,8 değil)
        t = self.at(_t(self.line, sy.get("kelime"), 0.2))
        self.js.append(f"tl.fromTo('#s{self.i}sy', {{ opacity: 0, scale: 0.7 }}, {{ opacity: 1, scale: 1, duration: 0.25, "
                       f"ease: 'back.out(2)' }}, {t:.3f});")
        on, bir = sy.get("onek", ""), sy.get("birim", "")
        if _yuzde(bir) and not on:   # Türkçe yazım: %21,2 (21,2% değil)
            on, bir = "%", ""
        self.parca.append(f'<div class="sayi" id="s{self.i}sy" style="top:{y}px"><span class="on">{E(on)}</span>'
                          f'<span id="s{self.i}n">{fmt_num(float(sy.get("bas", 0)) if sy.get("say", True) else v, d)}</span>'
                          f'<span class="bir">{E(bir)}</span>'
                          f'{"<div class=not>" + E(sy["not"]) + "</div>" if sy.get("not") else ""}</div>')
        if sy.get("say", True):
            self.js.append(f"(() => {{ const o = {{ v: {float(sy.get('bas', 0))} }}; tl.to(o, {{ v: {v}, duration: 0.9, ease: 'power2.out', onUpdate: () => {{ "
                           f"document.getElementById('s{self.i}n').textContent = fmtN(o.v, {d}); }} }}, {t:.3f}); }})();")

    def vs(self, v):
        for taraf, x in (("sol", 300), ("sag", 780)):
            o = v[taraf]
            self.oyuncu({"id": taraf, "k": o["k"], "ifade": o.get("ifade", "normal"), "x": x, "y": 820, "olcek": 0.6,
                         "giris": "sol" if taraf == "sol" else "sag"}, taraf)
            self.parca.append(f'<div class="vs-et" style="left:{x - 200}px">{E(o.get("etiket", ""))}'
                              f'<b class="vz">{E(o.get("deger", ""))}</b></div>')
        self.parca.append('<div class="vs-rozet" id="s%dvs">VS</div>' % self.i)
        self.js.append(f"tl.fromTo('#s{self.i}vs', {{ scale: 0, rotation: -20 }}, {{ scale: 1, rotation: 0, duration: 0.35, "
                       f"ease: 'back.out(3)' }}, {self.s + 0.3:.3f});")

    def cubuk(self, c):
        mx = max(float(c["a"]["deger"]), float(c["b"]["deger"]), 1)
        for k, (taraf, x) in enumerate((("a", 330), ("b", 750))):
            o = c[taraf]
            h = 500 * float(o["deger"]) / mx
            bid = f"s{self.i}c{taraf}"
            self.parca.append(f'<div class="cubuk" style="left:{x - 150}px"><div class="cd">'
                              + (f'<small>%</small>{fmt_num(float(o["deger"]))}' if _yuzde(c.get("birim")) else
                                 f'{fmt_num(float(o["deger"]))} <small>{E(c.get("birim", ""))}</small>') + f'</div><div class="cb" id="{bid}" style="height:{h:.0f}px'
                              f';background:{"#4fa3e0" if k == 0 else VURGU}"></div><div class="ce">{E(o["etiket"])}</div></div>')
            self.js.append(f"tl.fromTo('#{bid}', {{ scaleY: 0 }}, {{ scaleY: 1, duration: 0.6, ease: 'power2.out', "
                           f"transformOrigin: '50% 100%' }}, {self.s + 0.2 + k * 0.35:.3f});")
        if c.get("not"):
            self.parca.append(f'<div class="cnot">{_vurgula(c["not"])}</div>')

    def tablo(self, tb):
        """Zam tablosu kartı (2026-11-17 biçim araştırması: '2027 Ocak zamlı emekli maaşları' tablosu IG'de 2 milyon).
        {"baslik": "…", "sutunlar": ["…", …], "satirlar": [["…", …], …] (en çok 8), "vurgu": satır no, "kelime": "…", "not": "…"}"""
        sut = tb.get("sutunlar") or []
        sat = (tb.get("satirlar") or [])[:8]
        t0 = self.s + 0.25
        h = [f'<div class="tablo" id="s{self.i}tb">']
        if tb.get("baslik"):
            h.append(f'<div class="tb">{E(tb["baslik"])}</div>')
        h.append("<table>")
        if sut:
            h.append("<tr>" + "".join(f"<th>{E(x)}</th>" for x in sut) + "</tr>")
        hemen = bool(tb.get("hemen"))   # tablo önceki sahnede zaten görüldü: satırlar hazır, vurgu sabit
        v = tb.get("vurgu")
        for r, row in enumerate(sat):
            sinif = ' class="vurgu"' if (hemen and v == r) else ""
            h.append(f'<tr id="s{self.i}t{r}"{sinif}>' + "".join(f"<td>{E(str(x))}</td>" for x in row) + "</tr>")
            if not hemen:
                self.js.append(f"tl.fromTo('#s{self.i}t{r}', {{ opacity: 0, x: -40 }}, {{ opacity: 1, x: 0, duration: 0.25, "
                               f"ease: 'power2.out' }}, {t0 + r * 0.14:.3f});")
        h.append("</table>")
        if tb.get("not"):
            h.append(f'<div class="tnot">{_vurgula(tb["not"])}</div>')
        h.append("</div>")
        self.parca.append("".join(h))
        if not hemen and isinstance(v, int) and 0 <= v < len(sat):
            tv = max(t0 + len(sat) * 0.14 + 0.2, self.at(_t(self.line, tb.get("kelime"), 0.6)))
            self.js.append(f"tl.to('#s{self.i}t{v} td', {{ backgroundColor: '#f4c26b', color: '#3a2606', duration: 0.2 }}, {tv:.3f});")
            self.js.append(f"tl.fromTo('#s{self.i}t{v}', {{ scale: 1 }}, {{ scale: 1.04, duration: 0.18, yoyo: true, repeat: 1, "
                           f"transformOrigin: '50% 50%' }}, {tv:.3f});")

    def gosterge(self, g):
        bas, son = float(g.get("bas", 0)), float(g["son"])
        t = self.at(_t(self.line, g.get("kelime"), 0.25))
        gd = (f'<div class="gd">%<span id="s{self.i}gv">{fmt_num(bas)}</span></div>' if _yuzde(g.get("birim")) else
              f'<div class="gd"><span id="s{self.i}gv">{fmt_num(bas)}</span> {E(g.get("birim", ""))}</div>')
        self.parca.append(f'<div class="gosterge"><svg viewBox="0 0 400 260" width="520" height="338">'
                          f'<path d="M40 220 A160 160 0 0 1 360 220" stroke="#ffffff22" stroke-width="34" fill="none" stroke-linecap="round"/>'
                          f'<path d="M40 220 A160 160 0 0 1 360 220" stroke="url(#gr{self.i})" stroke-width="34" fill="none" '
                          f'stroke-linecap="round" pathLength="100" stroke-dasharray="100" id="s{self.i}ga" stroke-dashoffset="100"/>'
                          f'<g id="s{self.i}ib" style="transform-origin:200px 220px"><line x1="200" y1="220" x2="200" y2="86" stroke="#fff" '
                          f'stroke-width="10" stroke-linecap="round"/></g><circle cx="200" cy="220" r="18" fill="#fff"/>'
                          f'<defs><linearGradient id="gr{self.i}"><stop offset="0" stop-color="#5fd39b"/><stop offset=".6" '
                          f'stop-color="#ffb547"/><stop offset="1" stop-color="#ff6b5b"/></linearGradient></defs></svg>'
                          f'{gd}'
                          f'{"<div class=not>" + _vurgula(g["not"]) + "</div>" if g.get("not") else ""}</div>')
        oran = 100 * (son - bas) / max(1e-9, float(g.get("tavan", son)) - bas)
        self.js.append(f"tl.fromTo('#s{self.i}ib', {{ rotation: -90 }}, {{ rotation: {-90 + 180 * oran / 100:.1f}, duration: 1.1, "
                       f"ease: 'power2.out' }}, {t:.3f});")
        self.js.append(f"tl.to('#s{self.i}ga', {{ attr: {{ 'stroke-dashoffset': {100 - oran:.1f} }}, duration: 1.1, ease: 'power2.out' }}, {t:.3f});")
        self.js.append(f"(() => {{ const o = {{ v: {bas} }}; tl.to(o, {{ v: {son}, duration: 1.1, ease: 'power2.out', onUpdate: () => {{ "
                       f"document.getElementById('s{self.i}gv').textContent = fmtN(o.v, 0); }} }}, {t:.3f}); }})();")

    def build(self):
        sc = self.sc
        if sc.get("baslik"):
            satirlar = sc["baslik"] if isinstance(sc["baslik"], list) else [sc["baslik"]]
            self.parca.append(f'<div class="baslik" id="s{self.i}b">' + "<br>".join(_vurgula(x) for x in satirlar[:2]) + "</div>")
            if self.i > 0:
                self.js.append(f"tl.fromTo('#s{self.i}b', {{ y: -30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: 'power3.out' }}, {self.s:.3f});")
        if sc.get("etiket"):
            t_et = 2.35 if (self.i == 0 and self.kanca) else self.s + 0.05
            self.parca.append(f'<div class="hap" id="s{self.i}h">{E(sc["etiket"])}</div>')
            self.js.append(f"tl.fromTo('#s{self.i}h', {{ scale: 0 }}, {{ scale: 1, duration: 0.25, ease: 'back.out(2.5)' }}, {t_et:.3f});")
        for n, d in enumerate(sc.get("dekor", [])):
            self.dekor(d, n)
        for n, o in enumerate(sc.get("oyuncular", [])):
            self.oyuncu(o, n)
        if sc.get("sayi"):
            self.sayi(sc["sayi"])
        if sc.get("vs"):
            self.vs(sc["vs"])
        if sc.get("cubuk"):
            self.cubuk(sc["cubuk"])
        if sc.get("gosterge"):
            self.gosterge(sc["gosterge"])
        if sc.get("tablo"):
            self.tablo(sc["tablo"])
        if sc.get("kaynak"):
            self.parca.append(f'<div class="kaynak">{E(sc["kaynak"])}</div>')
        if sc.get("zemin"):
            self.parca.append(f'<div class="zemin" style="top:{int(sc["zemin"])}px"></div>')
        if sc.get("soru"):
            self.parca.append(f'<div class="balon" id="s{self.i}q"><svg viewBox="0 0 120 100" width="150" height="125"><path d="M10 10 h100 '
                              f'a10 10 0 0 1 10 10 v46 a10 10 0 0 1 -10 10 h-58 l-24 20 v-20 h-18 a10 10 0 0 1 -10 -10 v-46 '
                              f'a10 10 0 0 1 10 -10z" fill="#5fd39b"/><circle cx="38" cy="43" r="7" fill="#0b1512"/><circle cx="60" '
                              f'cy="43" r="7" fill="#0b1512"/><circle cx="82" cy="43" r="7" fill="#0b1512"/></svg></div>')
            self.js.append(f"tl.fromTo('#s{self.i}q', {{ scale: 0 }}, {{ scale: 1, duration: 0.3, ease: 'back.out(2.5)' }}, {self.s + 0.4:.3f});")
        return (f'<div id="sc{self.i}" class="clip sahne" data-start="{self.s:.3f}" data-duration="{self.e - self.s:.3f}" '
                f'data-track-index="5">{"".join(self.parca)}</div>')


# ---------------------------------------------------------------- kompozisyon
CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 1080px; height: 1920px; overflow: hidden; background: #08110e; }
body { font-family: 'InterP', system-ui, sans-serif; color: #fff; }
#root { position: relative; width: 1080px; height: 1920px; overflow: hidden; }
#bg { position: absolute; inset: 0; }
.toz { position: absolute; border-radius: 50%; }
.zemin { position: absolute; left: 0; right: 0; height: 6px; background: rgba(120, 200, 160, .35); }
.sahne { position: absolute; inset: 0; }
.oyuncu, .dekor { position: absolute; }
.baslik { position: absolute; top: 230px; left: 60px; right: 60px; text-align: center; font-weight: 700; font-size: 96px;
  line-height: 1.04; letter-spacing: -2px; text-shadow: 0 6px 30px rgba(0,0,0,.45); }
.vz { color: #ffb547; }
.hap { position: absolute; top: 150px; left: 0; right: 0; margin: 0 auto; width: fit-content; white-space: nowrap; text-align: center;
  background: #f4c26b; color: #3a2606; font-weight: 700; font-size: 38px; padding: 8px 28px; border-radius: 999px; }
#kanca { position: absolute; top: 230px; left: 40px; right: 40px; text-align: center; font-family: 'AntonP', sans-serif;
  font-size: 150px; line-height: 1.0; letter-spacing: 1px; text-transform: uppercase; text-shadow: 0 8px 40px rgba(0,0,0,.5); }
.capg { position: absolute; left: 50px; right: 50px; top: 1330px; text-align: center; }
.capin { display: inline-block; font-weight: 700; font-size: 78px; line-height: 1.12; letter-spacing: -1px;
  text-shadow: 0 4px 0 rgba(0,0,0,.55), 0 0 30px rgba(0,0,0,.6); }
.capin .w { color: rgba(255,255,255,.42); }
.capin .w.on { color: #fff; }
.capin .w.vz.on { color: #ffb547; }
.sayi { position: absolute; left: 0; right: 0; text-align: center; font-family: 'AntonP', sans-serif; font-size: 190px; line-height: 1;
  color: #fff; text-shadow: 0 10px 40px rgba(0,0,0,.5); }
.sayi .on, .sayi .bir { font-size: 90px; color: #ffb547; margin: 0 12px; }
.sayi .not, .gosterge .not, .cnot { font-family: 'InterP', sans-serif; font-weight: 700; font-size: 44px; color: #fff; margin-top: 14px;
  letter-spacing: 0; }
.gosterge { position: absolute; top: 560px; left: 0; right: 0; text-align: center; }
.gosterge .gd { font-family: 'AntonP', sans-serif; font-size: 120px; margin-top: -40px; }
.vs-et { position: absolute; top: 1050px; width: 400px; text-align: center; font-weight: 700; font-size: 46px; }
.vs-et b { display: block; font-family: 'AntonP', sans-serif; font-size: 96px; margin-top: 6px; }
.vs-rozet { position: absolute; top: 750px; left: 470px; width: 140px; height: 140px; line-height: 140px; text-align: center;
  font-family: 'AntonP', sans-serif; font-size: 80px; color: #ff6b5b; text-shadow: 0 6px 24px rgba(0,0,0,.5); }
.tablo { position: absolute; top: 300px; left: 50px; right: 50px; }
.tablo .tb { font-weight: 700; font-size: 46px; color: #f4c26b; text-align: center; margin-bottom: 14px; }
.tablo table { width: 100%; border-collapse: separate; border-spacing: 0 10px; font-variant-numeric: tabular-nums; }
.tablo th { font-size: 30px; color: #cfe3da; text-align: right; padding: 0 18px; font-weight: 700; }
.tablo td { font-size: 48px; font-weight: 700; padding: 14px 18px; background: rgba(255,255,255,.09); text-align: right; white-space: nowrap; }
.tablo th:first-child, .tablo td:first-child { text-align: left; }
.tablo tr td:first-child { border-radius: 14px 0 0 14px; }
.tablo tr td:last-child { border-radius: 0 14px 14px 0; }
.tablo tr.vurgu td { background: #f4c26b; color: #3a2606; }
.tablo .tnot { font-size: 30px; color: #b8c7c0; text-align: center; margin-top: 12px; line-height: 1.3; }
.cubuk { position: absolute; top: 470px; width: 300px; height: 680px; display: flex; flex-direction: column; justify-content: flex-end;
  align-items: center; }
.cubuk .cb { width: 180px; border-radius: 18px 18px 6px 6px; }
.cubuk .cd { font-family: 'AntonP', sans-serif; font-size: 70px; margin-bottom: 12px; }
.cubuk .cd small { font-family: 'InterP', sans-serif; font-weight: 700; font-size: 32px; }
.cubuk .ce { font-weight: 700; font-size: 40px; margin-top: 14px; color: #f4c26b; }
.cnot { position: absolute; top: 1172px; left: 0; right: 0; text-align: center; }
.balon { position: absolute; top: 1060px; left: 465px; }
.kaynak { position: absolute; left: 60px; right: 60px; top: 1490px; text-align: center; font-weight: 600; font-size: 30px;
  color: rgba(255,255,255,.88); text-shadow: 0 2px 8px rgba(0,0,0,.6); }
#marka { position: absolute; right: 44px; bottom: 300px; font-family: 'AntonP', sans-serif; font-size: 34px; letter-spacing: 3px;
  color: rgba(255,255,255,.8); text-shadow: 0 2px 8px rgba(0,0,0,.6); }
"""


def compose(spec, lines, dur):
    data = spec.get("data") or {}
    scenes = data.get("scenes") or []
    if not scenes:
        raise ValueError("hikaye: spec.data.scenes boş")
    bg, toz, zemin = TEMA.get(data.get("tema", "gece"), TEMA["gece"])
    by_id = {l["id"]: l for l in lines}
    starts = []
    for i, sc in enumerate(scenes):
        ln = by_id.get(sc.get("line")) or lines[min(i, len(lines) - 1)]
        starts.append(0.0 if i == 0 else max(starts[-1] + 0.8, ln["t0"] - 0.12))
    html_sc, js = [], []
    for i, sc in enumerate(scenes):
        ln = by_id.get(sc.get("line")) or lines[min(i, len(lines) - 1)]
        e = starts[i + 1] if i + 1 < len(scenes) else dur
        s = Sahne(i, sc, ln, starts[i], e, kanca=bool(data.get("kanca")))
        html_sc.append(s.build())
        js += s.js
        if i > 0:   # sahne geçişi: kısa beyaz parlama yerine yumuşak kayma (vuruş değişimi görünür olsun)
            js.append(f"tl.fromTo('#sc{i}', {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.22, ease: 'power2.out' }}, {starts[i]:.3f});")
    # kanca kartı: t=0'da hazır, ~2,2 sn sonra kalkar
    kanca = data.get("kanca") or []
    kanca_html = ""
    if kanca:
        kanca_html = (f'<div id="kanca" class="clip" data-start="0" data-duration="{min(2.4, dur):.3f}" data-track-index="7">'
                      + "<br>".join(_vurgula(x) for x in kanca[:2]) + "</div>")
        js.append("tl.fromTo('#kanca', { scale: 1.08 }, { scale: 1, duration: 0.5, ease: 'power2.out' }, 0);")
        js.append("tl.to('#kanca', { opacity: 0, y: -40, duration: 0.25, ease: 'power2.in' }, 2.1);")
    # toz parçacıkları (sabit tohum → her render aynı)
    import random
    rnd = random.Random(7)
    tozlar = []
    for k in range(34):
        x, y, r = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(2, 5)
        tozlar.append(f'<i class="toz" id="tz{k}" style="left:{x:.0f}px;top:{y:.0f}px;width:{r:.1f}px;height:{r:.1f}px;'
                      f'background:{toz};opacity:{rnd.uniform(.15, .45):.2f}"></i>')
        js.append(f"tl.to('#tz{k}', {{ y: {rnd.uniform(-90, -30):.0f}, x: {rnd.uniform(-20, 20):.0f}, duration: {dur:.3f}, ease: 'none' }}, 0);")
    cap_h, cap_j = captions(lines, dur, data.get("vurgu", []))
    js += cap_j
    fonts = ("@font-face { font-family: 'InterP'; src: url('assets/fonts/inter-latin.woff2') format('woff2'); font-weight: 400 700; "
             "unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+20AC, U+20BA, U+2122; }\n"
             "@font-face { font-family: 'InterP'; src: url('assets/fonts/inter-latin-ext.woff2') format('woff2'); font-weight: 400 700; "
             "unicode-range: U+0100-02BA, U+02BD-02C5, U+1E00-1EFF, U+20A0-20C0; }\n"
             "@font-face { font-family: 'AntonP'; src: url('assets/fonts/Anton-Regular.ttf'); }\n")
    gsap = open(GSAP, encoding="utf-8").read()
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
<style>{fonts}{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur:.3f}" data-width="1080" data-height="1920">
  <div id="bg" class="clip" data-start="0" data-duration="{dur:.3f}" data-track-index="0" data-layout-ignore style="background:{bg}">{"".join(tozlar)}
</div>
  {chr(10).join(html_sc)}
  {kanca_html}
  <div id="marka" class="clip" data-start="0" data-duration="{dur:.3f}" data-track-index="3">PARAFOMO</div>
  {chr(10).join(cap_h)}
</div>
<script>{script}</script>
</body>
</html>
"""


def project(spec, lines, dur, wd):
    proj = os.path.join(wd, "hikaye")
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


def render(spec, lines, dur, wd, W_, H_, lock):
    if W_ != 1080 or H_ != 1920:
        raise NotImplementedError("hikaye motoru yalnız 9:16 Short (1080x1920)")
    if not (os.path.exists(HF_BIN) and os.path.exists(GSAP)):
        raise RuntimeError("HyperFrames kurulu değil. Kur: " + INSTALL)
    proj = project(spec, lines, dur, wd)
    check(proj)
    out = os.path.join(wd, "video-hikaye.mp4")
    cmd = ["nice", "-n", "19", "ionice", "-c3", HF_BIN, "render", proj, "-o", out, "--fps", "30", "--workers", "1",
           "--crf", "20", "--no-browser-gpu", "--quiet"]
    if lock:
        cmd = ["flock", lock] + cmd
    r = subprocess.run(cmd, env=_env(), capture_output=True, text=True, timeout=3600)
    if r.returncode != 0 or not os.path.exists(out):
        raise RuntimeError(f"hikaye render başarısız: {(r.stderr or r.stdout)[-600:]}")
    return out
