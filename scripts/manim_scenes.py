"""
ParaFOMO — Manim sahne kütüphanesi (Shorts arka planı / veri animasyonu).

shorts-build-v4.py `visual.type=="manim"` segmentinde subprocess ile çağırır;
1080x1920 / 30fps mp4 üretir, make_clip onu B-roll gibi işler. LaTeX YOK (Pango).
Kendi kendine render eder, sonucu --out'a kopyalar. Başarısızsa exit!=0 → Pexels fallback.

TEMALAR (--theme): slate (varsayılan, açık-koyu lacivert) · dark (koyu teal) · light (editoryal krem)
SAHNELER (--scene): backtest · compare · bigstat
GÜVENLİ BÖLGE: üstte eyebrow (~230px), altta altyazı (~1400px) → içerik dikey merkeze toplanır.

Örnekler:
  python scripts/manim_scenes.py --scene backtest --theme slate --dur 6 --start 10000 --end 47850 --title "..." --out x.mp4
  python scripts/manim_scenes.py --scene compare --theme light --dur 7 --items "Altın:378,Borsa:210,Dolar:145,Mevduat:64" --title "5 yılda kim kazandırdı?" --out x.mp4
  python scripts/manim_scenes.py --scene bigstat --theme slate --dur 5 --end 80 --label "her 100 kişiden" --sub "birikimini altında tutuyor" --out x.mp4
"""
import os, sys, glob, shutil, tempfile, argparse

ap = argparse.ArgumentParser()
ap.add_argument("--scene", default="backtest",
                choices=["backtest", "compare", "bigstat", "pie", "concept"])
ap.add_argument("--theme", default="slate", choices=["slate", "dark", "light"])
ap.add_argument("--dur", type=float, default=6.0)
ap.add_argument("--start", type=float, default=10000)
ap.add_argument("--end", type=float, default=47850)
ap.add_argument("--items", default="")   # compare: "Etiket:deger,Etiket:deger,..."
ap.add_argument("--title", default="")
ap.add_argument("--sub", default="")
ap.add_argument("--label", default="")     # bigstat üst etiket
ap.add_argument("--keyword", default="")   # concept: büyük anahtar kelime
ap.add_argument("--stat", default="")      # concept: vurgu istatistiği (ör. "400 ₺ → 2.000 ₺")
ap.add_argument("--glyph", default="₺")    # concept: arka plan sembolü
ap.add_argument("--suffix", default=" ₺")
ap.add_argument("--out", required=True)
A = ap.parse_args()

from manim import *

# ---- Tema paletleri ----
THEMES = {
    "slate": dict(bg="#14273a", ink="#EAF2F0", mute="#8fb3c9", axis="#3b566b",
                  teal="#37c9a3", tealL="#5fe3c0", accent="#FFE14D", red="#ff6b7a"),
    "dark":  dict(bg="#0c1f1b", ink="#E7F0EC", mute="#7fb0a4", axis="#33514a",
                  teal="#2bb194", tealL="#63d491", accent="#FFE14D", red="#ff6b7a"),
    "light": dict(bg="#f4f1ea", ink="#14323C", mute="#5b6f74", axis="#c7bfb0",
                  teal="#16a085", tealL="#0f7f68", accent="#E2475A", red="#E2475A"),
}
T = THEMES[A.theme]
FONT = "Liberation Sans"

config.pixel_width = 1080
config.pixel_height = 1920
config.frame_rate = 30
config.frame_height = 16.0
config.frame_width = 9.0
config.background_color = T["bg"]
config.disable_caching = True
config.verbosity = "ERROR"


def tl(x, suffix=""):
    return f"{int(round(x)):,}".replace(",", ".") + suffix


def bg_depth():
    """Hafif dikey gradyan derinlik (düz zemin hissini kırar)."""
    top = Rectangle(width=9.2, height=16.2, stroke_width=0,
                    fill_color=[T["bg"], T["teal"]], fill_opacity=1)
    top.set_opacity(0.0)  # gradyan yerine hafif vignette kullanacağız
    vig = Rectangle(width=9.2, height=16.2, stroke_width=0, fill_color="#000000",
                    fill_opacity=0.0)
    return VGroup()


def fit(mobj, maxw=8.0):
    if mobj.width > maxw:
        mobj.scale(maxw / mobj.width)
    return mobj


class BacktestScene(Scene):
    def construct(self):
        start, end = A.start, A.end
        pct = (end / start - 1) * 100 if start else 0
        intro = 0.9 + 0.5 + 1.4 + 0.5 + 1.4 + 0.4
        hold = max(0.7, A.dur + 0.8 - intro)

        if A.title:
            t = fit(Text(A.title, font=FONT, weight=BOLD, color=T["ink"]).scale(0.62), 8.2)
            t.move_to([0, 5.3, 0])
            self.play(FadeIn(t, shift=DOWN * 0.25), run_time=0.9)
        vals = [start, start*1.28, start*1.9, start*2.6, start*3.3, end]
        n = len(vals)
        ax = Axes(x_range=[0, n-1, 1], y_range=[0, end*1.08, end/4],
                  x_length=6.4, y_length=5.2,
                  axis_config={"color": T["axis"], "stroke_width": 2, "include_ticks": False},
                  tips=False).move_to([0, 1.0, 0])
        pts = [ax.coords_to_point(i, v) for i, v in enumerate(vals)]
        curve = VMobject(color=T["tealL"], stroke_width=8).set_points_as_corners(pts)
        area = VMobject(fill_color=T["teal"], fill_opacity=0.22, stroke_width=0)
        area.set_points_as_corners(pts + [ax.coords_to_point(n-1, 0), ax.coords_to_point(0, 0)])
        self.play(Create(ax), run_time=0.5)
        self.play(Create(curve), FadeIn(area), run_time=1.4, rate_func=rate_functions.ease_out_cubic)
        tip = Dot(pts[-1], color=T["accent"], radius=0.13)
        self.play(FadeIn(tip, scale=0.5), FadeIn(tip.copy().set_opacity(0.3).scale(2.2)), run_time=0.5)

        tr = ValueTracker(start)
        counter = Text(tl(start, A.suffix), font=FONT, weight=BOLD, color=T["accent"]).scale(1.35)
        counter.move_to([0, -2.5, 0])
        counter.add_updater(lambda m: m.become(
            Text(tl(tr.get_value(), A.suffix), font=FONT, weight=BOLD, color=T["accent"])
            .scale(1.35).move_to([0, -2.5, 0])))
        self.add(counter)
        self.play(tr.animate.set_value(end), run_time=1.4, rate_func=rate_functions.ease_out_cubic)
        counter.clear_updaters()
        badge = Text(f"+%{pct:.0f}", font=FONT, weight=BOLD, color=T["teal"]).scale(0.72).move_to([0, -3.35, 0])
        self.play(FadeIn(badge, scale=0.6), run_time=0.4)
        self.wait(hold)


class CompareScene(Scene):
    """Animasyonlu karşılaştırma barları (Altın vs Dolar vs Borsa...) — kazanan vurgulu."""
    def construct(self):
        items = []
        for tok in A.items.split(","):
            if ":" in tok:
                name, val = tok.split(":", 1)
                try:
                    items.append((name.strip(), float(val)))
                except ValueError:
                    pass
        if not items:
            items = [("Altın", 378), ("Borsa", 210), ("Dolar", 145), ("Mevduat", 64)]
        vmax = max(v for _, v in items)
        winner = max(range(len(items)), key=lambda i: items[i][1])

        title = fit(Text(A.title or "5 yılda kim kazandırdı?", font=FONT, weight=BOLD,
                         color=T["ink"]).scale(0.6), 8.2).move_to([0, 5.6, 0])
        self.play(FadeIn(title, shift=DOWN*0.2), run_time=0.7)

        rows = VGroup()
        top, gap, barmaxw = 3.6, 1.9, 6.2
        anims, counters = [], []
        for i, (name, val) in enumerate(items):
            y = top - i * gap
            lab = Text(name, font=FONT, weight=BOLD, color=T["ink"]).scale(0.5)
            lab.move_to([-3.9, y + 0.55, 0]).align_to([-3.9, 0, 0], LEFT)
            w = max(0.35, barmaxw * val / vmax)
            col = T["accent"] if i == winner else T["teal"]
            track = RoundedRectangle(width=barmaxw, height=0.62, corner_radius=0.31,
                                     stroke_width=0, fill_color=T["axis"], fill_opacity=0.35)
            track.move_to([-3.9 + barmaxw/2, y, 0])
            bar = RoundedRectangle(width=w, height=0.62, corner_radius=0.31, stroke_width=0,
                                   fill_color=col, fill_opacity=1)
            bar.move_to([-3.9 + w/2, y, 0])
            bar.stretch(0.001, 0, about_edge=LEFT)
            valtxt = Text(f"+%{int(val)}", font=FONT, weight=BOLD, color=col).scale(0.5)
            valtxt.move_to([-3.9 + w + 0.9, y, 0])
            rows.add(lab, track, bar, valtxt)
            anims.append(AnimationGroup(FadeIn(lab, shift=RIGHT*0.2),
                                        bar.animate.stretch(1000, 0, about_edge=LEFT)))
            counters.append(valtxt)
        self.add(*[m for m in rows if isinstance(m, (RoundedRectangle,))])
        self.play(FadeIn(VGroup(*[rows[j] for j in range(1, len(rows), 4)])), run_time=0.3)  # tracks
        self.play(LaggedStart(*anims, lag_ratio=0.25), run_time=2.2,
                  rate_func=rate_functions.ease_out_cubic)
        self.play(*[FadeIn(c, shift=LEFT*0.1) for c in counters], run_time=0.5)
        # kazanan vurgusu
        wb = rows[winner*4 + 2]
        self.play(Flash(wb, color=T["accent"], line_length=0.3, num_lines=12), run_time=0.6)
        self.wait(max(0.7, A.dur + 0.6 - 4.5))


class BigstatScene(Scene):
    """Sayı-şoku: dev bir yüzde/rakam sayarak dolar; üst etiket + alt açıklama."""
    def construct(self):
        end = A.end
        is_pct = A.suffix.strip() in ("%", "") and end <= 100 and A.scene == "bigstat"
        if A.label:
            lab = fit(Text(A.label, font=FONT, color=T["mute"]).scale(0.6), 7.5).move_to([0, 3.6, 0])
            self.play(FadeIn(lab, shift=DOWN*0.2), run_time=0.6)
        tr = ValueTracker(0)
        def fmt(v):
            return ("%" + tl(v)) if is_pct else tl(v, A.suffix)
        num = Text(fmt(0), font=FONT, weight=BOLD, color=T["accent"]).scale(2.6).move_to([0, 0.3, 0])
        num.add_updater(lambda m: m.become(
            Text(fmt(tr.get_value()), font=FONT, weight=BOLD, color=T["accent"])
            .scale(2.6).move_to([0, 0.3, 0])))
        self.add(num)
        self.play(tr.animate.set_value(end), run_time=1.8, rate_func=rate_functions.ease_out_cubic)
        num.clear_updaters()
        self.play(num.animate.scale(1.06), rate_func=there_and_back, run_time=0.4)
        if A.sub:
            sub = fit(Text(A.sub, font=FONT, weight=BOLD, color=T["ink"]).scale(0.6), 8.0).move_to([0, -3.0, 0])
            self.play(FadeIn(sub, shift=UP*0.2), run_time=0.6)
        self.wait(max(0.8, A.dur + 0.6 - 3.4))


class PieScene(Scene):
    """Donut/pasta grafik: paylar süpürülerek çizilir, kazanan dilim vurgulu, altta lejant."""
    def construct(self):
        items = []
        for tok in A.items.split(","):
            if ":" in tok:
                name, val = tok.split(":", 1)
                try:
                    items.append((name.strip(), float(val)))
                except ValueError:
                    pass
        if not items:
            items = [("Altın", 40), ("Borsa", 25), ("Dolar", 20), ("Mevduat", 15)]
        total = sum(v for _, v in items) or 1
        pal = [T["teal"], T["tealL"], T["accent"], T["red"], T["mute"]]
        biggest = max(range(len(items)), key=lambda i: items[i][1])

        if A.title:
            ttl = fit(Text(A.title, font=FONT, weight=BOLD, color=T["ink"]).scale(0.6), 8.2)
            ttl.move_to([0, 5.6, 0]); self.play(FadeIn(ttl, shift=DOWN*0.2), run_time=0.7)

        center = [0, 1.4, 0]
        R, r = 2.6, 1.45
        start = 90 * DEGREES
        sectors, sweeps, labels = [], [], []
        for i, (name, val) in enumerate(items):
            ang = -val / total * TAU
            col = pal[i % len(pal)]
            sec = AnnularSector(inner_radius=r, outer_radius=R, angle=ang, start_angle=start,
                                color=col, fill_opacity=1, stroke_width=2, stroke_color=T["bg"])
            sec.move_arc_center_to(center)
            if i == biggest:
                sec.set_stroke(T["ink"], 3)
            sectors.append(sec)
            sweeps.append(GrowFromPoint(sec, center))
            # yüzde etiketi dilim ortasında
            mid = start + ang / 2
            lp = [center[0] + (R+0.05)*0.78*np.cos(mid), center[1] + (R+0.05)*0.78*np.sin(mid), 0]
            pctxt = Text(f"%{val/total*100:.0f}", font=FONT, weight=BOLD,
                         color=T["bg"] if A.theme == "light" else "#0a1417").scale(0.42).move_to(lp)
            labels.append(pctxt)
            start += ang
        self.play(LaggedStart(*sweeps, lag_ratio=0.2), run_time=1.8)
        self.play(*[FadeIn(l) for l in labels], run_time=0.4)

        # lejant (donut altında)
        leg = VGroup()
        for i, (name, val) in enumerate(items):
            dot = Dot(radius=0.16, color=pal[i % len(pal)])
            txt = Text(f"{name}  %{val/total*100:.0f}", font=FONT, weight=BOLD, color=T["ink"]).scale(0.42)
            row = VGroup(dot, txt).arrange(RIGHT, buff=0.25)
            leg.add(row)
        leg.arrange_in_grid(rows=2, cols=2, buff=(0.9, 0.4)).move_to([0, -3.1, 0])
        self.play(FadeIn(leg, shift=UP*0.2), run_time=0.6)
        self.wait(max(0.7, A.dur + 0.6 - 4.5))


class ConceptScene(Scene):
    """Markalı anlatı kartı (STOK YERİNE): büyük anahtar kelime + vurgu istatistiği +
    hafif hareketli sembol arka planı. Tüm video tek tutarlı özgün dilde kalır."""
    def construct(self):
        # arka plan: soluk sürüklenen finans sembolleri (özgün doku, stok değil)
        rng = np.random.default_rng(abs(hash(A.keyword or A.title)) % (2**32))
        glyphs = VGroup()
        for _ in range(12):
            g = Text(A.glyph, font=FONT, weight=BOLD, color=T["teal"]).scale(rng.uniform(0.5, 1.4))
            g.move_to([rng.uniform(-4, 4), rng.uniform(-7.5, 7.5), 0]).set_opacity(rng.uniform(0.05, 0.14))
            glyphs.add(g)
        self.add(glyphs)
        drift = ValueTracker(0)
        glyphs.add_updater(lambda m, d=drift: m.shift(UP * 0.008))

        kw = A.keyword or A.title or "PARA"
        big = fit(Text(kw.upper(), font=FONT, weight=BOLD, color=T["ink"]).scale(1.5), 8.2)
        big.move_to([0, 2.2, 0])
        bar = Line([-2.2, 1.15, 0], [2.2, 1.15, 0], color=T["accent"], stroke_width=8)
        self.play(FadeIn(big, shift=UP*0.3, scale=0.9), run_time=0.7)
        self.play(Create(bar), run_time=0.4)

        if A.stat:
            chip = fit(Text(A.stat, font=FONT, weight=BOLD, color=T["accent"]).scale(0.95), 8.0)
            chip.move_to([0, -0.4, 0])
            self.play(FadeIn(chip, scale=0.7), run_time=0.5)
            self.play(chip.animate.scale(1.06), rate_func=there_and_back, run_time=0.35)
        if A.sub:
            sub = fit(Text(A.sub, font=FONT, color=T["mute"]).scale(0.6), 8.0).move_to([0, -3.0, 0])
            self.play(FadeIn(sub, shift=UP*0.2), run_time=0.5)
        used = 2.0 + (0.85 if A.stat else 0) + (0.5 if A.sub else 0)
        self.play(drift.animate.set_value(1), run_time=max(0.8, A.dur + 0.7 - used), rate_func=linear)


SCENES = {"backtest": BacktestScene, "compare": CompareScene, "bigstat": BigstatScene,
          "pie": PieScene, "concept": ConceptScene}


def main():
    tmp = tempfile.mkdtemp(prefix="manim_")
    config.media_dir = tmp
    config.output_file = "scene"
    try:
        SCENES[A.scene]().render()
    except Exception as e:
        print(f"[manim] render hata: {str(e)[:200]}", file=sys.stderr)
        shutil.rmtree(tmp, ignore_errors=True)
        return 1
    vids = sorted(glob.glob(os.path.join(tmp, "videos", "**", "*.mp4"), recursive=True),
                  key=os.path.getmtime)
    if not vids:
        print("[manim] çıktı mp4 yok", file=sys.stderr)
        shutil.rmtree(tmp, ignore_errors=True); return 1
    os.makedirs(os.path.dirname(os.path.abspath(A.out)), exist_ok=True)
    shutil.copy(vids[-1], A.out)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"[manim] {A.out} ({os.path.getsize(A.out)//1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
