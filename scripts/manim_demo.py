"""
ParaFOMO — Manim deneme sahnesi (video kalitesi değerlendirmesi).
Dikey 1080x1920 Shorts formatı. LaTeX YOK (Pango/Text) — texlive gerektirmez.

Render:
  manim -r 1080,1920 --fps 60 --format mp4 -o parafomo-manim-demo \
        scripts/manim_demo.py ParaFomoDemo
"""
from manim import *

# ParaFOMO marka paleti
BG      = "#081613"   # koyu teal-siyah zemin
TEAL    = "#2bb194"
TEAL_L  = "#63d491"
DEEP    = "#1e6b7f"
YELLOW  = "#FFE14D"   # vurgu (sayı highlight)
RED     = "#E2475A"
INK     = "#E0E8E4"
FONT    = "Liberation Sans"

config.background_color = BG
config.frame_height = 16.0
config.frame_width = 9.0


def tl(x):
    """Türk lirası biçimi: 47850 -> '47.850 ₺'"""
    return f"{int(round(x)):,}".replace(",", ".") + " ₺"


class ParaFomoDemo(Scene):
    def construct(self):
        # ---- Marka şeridi (üst) ----
        brand = Text("ParaFOMO", font=FONT, weight=BOLD, color=TEAL_L).scale(0.75)
        brand.to_edge(UP, buff=0.6)
        dot = Dot(color=YELLOW, radius=0.07).next_to(brand, RIGHT, buff=0.12).shift(DOWN*0.02)
        self.play(FadeIn(brand, shift=DOWN*0.3), run_time=0.6)
        self.play(FadeIn(dot, scale=0.4), run_time=0.3)

        # ---- Kanca başlık (kinetik) ----
        l1 = Text("10.000 ₺", font=FONT, weight=BOLD, color=INK).scale(1.5)
        l2 = Text("5 yıl önce altın alsaydın?", font=FONT, color=INK).scale(0.72)
        head = VGroup(l1, l2).arrange(DOWN, buff=0.35)
        head.next_to(brand, DOWN, buff=0.9)
        self.play(Write(l1), run_time=0.7)
        self.play(FadeIn(l2, shift=UP*0.2), run_time=0.5)
        # sayıya sarı vurgu darbesi (pattern-interrupt)
        self.play(l1.animate.set_color(YELLOW).scale(1.08), run_time=0.25)
        self.play(l1.animate.scale(1/1.08), run_time=0.2)

        # ---- Grafik: büyüyen değer eğrisi ----
        years = [2021, 2022, 2023, 2024, 2025, 2026]
        vals  = [10000, 14200, 21800, 30500, 39900, 47850]
        ax = Axes(
            x_range=[2021, 2026, 1],
            y_range=[0, 50000, 10000],
            x_length=6.6, y_length=6.2,
            axis_config={"color": "#3a5750", "stroke_width": 2,
                         "include_ticks": True, "include_numbers": False},
            tips=False,
        )
        ax.move_to(ORIGIN).shift(DOWN*0.6)

        pts = [ax.coords_to_point(x, y) for x, y in zip(years, vals)]
        curve = VMobject(color=TEAL_L, stroke_width=7).set_points_as_corners(pts)
        # zemine dolgu (area)
        base_l = ax.coords_to_point(2021, 0)
        base_r = ax.coords_to_point(2026, 0)
        area = VMobject(fill_color=TEAL, fill_opacity=0.22, stroke_width=0)
        area.set_points_as_corners(pts + [base_r, base_l])

        # yıl etiketleri
        xlabels = VGroup(*[
            Text(str(y), font=FONT, color="#7fb0a4").scale(0.4)
            .next_to(ax.coords_to_point(y, 0), DOWN, buff=0.15)
            for y in years
        ])

        self.play(Create(ax), FadeIn(xlabels), run_time=0.9)
        self.play(Create(curve), FadeIn(area), run_time=1.8, rate_func=rate_functions.ease_out_cubic)

        # uç noktada parlayan nokta
        tip = Dot(pts[-1], color=YELLOW, radius=0.11)
        glow = tip.copy().set_opacity(0.35).scale(2.2)
        self.play(FadeIn(tip), FadeIn(glow), run_time=0.4)

        # ---- Count-up sayaç (payoff) ----
        tracker = ValueTracker(10000)
        counter = Text(tl(10000), font=FONT, weight=BOLD, color=YELLOW).scale(1.4)
        counter.next_to(ax, DOWN, buff=0.7)

        def upd(m):
            m.become(Text(tl(tracker.get_value()), font=FONT, weight=BOLD, color=YELLOW).scale(1.4)
                     .next_to(ax, DOWN, buff=0.7))
        counter.add_updater(upd)
        self.add(counter)
        self.play(tracker.animate.set_value(47850), run_time=1.8,
                  rate_func=rate_functions.ease_out_cubic)
        counter.remove_updater(upd)

        # kazanç rozeti
        gain = Text("+%378", font=FONT, weight=BOLD, color=TEAL_L).scale(0.85)
        gain.next_to(counter, DOWN, buff=0.35)
        self.play(FadeIn(gain, scale=0.6), run_time=0.5)
        self.play(gain.animate.scale(1.12), rate_func=there_and_back, run_time=0.4)

        # ---- Kapanış CTA ----
        cta = Text("Detaylı analiz → parafomo.com", font=FONT, color="#9fc7bc").scale(0.5)
        cta.to_edge(DOWN, buff=0.7)
        self.play(FadeIn(cta, shift=UP*0.2), run_time=0.5)
        self.wait(0.8)
