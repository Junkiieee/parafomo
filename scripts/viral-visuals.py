#!/usr/bin/env python3
"""
ParaFOMO — Viral Shorts görsel motoru (senaryo↔görsel eşleşmesi, ücretsiz).

Senaryonun her "beat"i için yapılandırılmış bir görsel isteğini ({type, query})
DOĞRU ÜCRETSİZ kaynaktan çözer ve mevcut shorts-build make_clip hattına uygun
1296x2304 bir B-roll mp4 döndürür:

  - person / place / logo / gold / object  → Wikimedia Commons (kamu malı / CC),
       gerçek fotoğraf. "Trump" senaryosunda ekranda gerçekten Trump çıkar.
  - concept / scene / broll                → Pexels dikey stok video (mevcut yol).
  - chart                                  → (faz 2) veri-grafik; şimdilik fallback.

Tasarım: Wikimedia'dan gelen STILL, 1296x2304 sabit kareye getirilip kısa bir
mp4'e yazılır; hareket (Ken Burns) yine shorts-build make_clip içinde uygulanır
— böylece still'ler ve videolar tek bir hareket yolundan geçer.

CLI test:
  python3 scripts/viral-visuals.py test "Donald Trump" --type person
  → /tmp/vv_test.mp4 üretir + lisans/atıf yazar.
"""
import os
import re
import sys
import json
import argparse
import subprocess
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = "/root/.cache/parafomo/viral-visuals"
UA = "ParaFOMO/1.0 (https://parafomo.com; mailto:contact@parafomo.com)"

W, H = 1296, 2304   # make_clip'in beklediği B-roll boyutu (sonra 1080x1920'ye crop'lanır)
FPS = 30

# Wikimedia'dan görsel ÇEKİLECEK görsel tipleri (gerçek varlıklar)
ENTITY_TYPES = {"person", "place", "logo", "gold", "object", "building", "thing", "map"}
# Pexels stok videoya gidecek tipler (soyut/sahne)
STOCK_TYPES = {"concept", "scene", "broll", "abstract", "mood"}

# Atıf gerektirmeyen lisanslar (kamu malı / CC0) — bunları öncele
NOATTR_LIC = ("public domain", "cc0", "no restrictions", "pd-")


# ---------------------------------------------------------------- Wikimedia

def _http_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=25))


def _lic_rank(lic):
    l = (lic or "").lower()
    if any(k in l for k in NOATTR_LIC):
        return 0           # en iyi: atıf gerekmez
    if "cc by" in l or "cc-by" in l or "attribution" in l:
        return 1           # atıf gerekir ama serbest
    return 2


def wikimedia_search(query, limit=12):
    """Commons'ta bitmap arar; (genişlik, yükseklik, url, başlık, lisans, sanatçı) listesi."""
    api = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"filetype:bitmap {query}", "gsrnamespace": "6",
        "gsrlimit": str(limit), "prop": "imageinfo",
        "iiprop": "url|size|extmetadata", "iiurlwidth": "1280",
    }
    try:
        data = _http_json(api + "?" + urllib.parse.urlencode(params))
    except Exception as e:
        print(f"[i] Wikimedia '{query}' arama hatası: {str(e)[:70]}")
        return []
    out = []
    pages = (data.get("query") or {}).get("pages") or {}
    for p in pages.values():
        ii = (p.get("imageinfo") or [{}])[0]
        w, h = ii.get("width") or 0, ii.get("height") or 0
        url = ii.get("thumburl") or ii.get("url")
        if not url or w < 500:
            continue
        meta = ii.get("extmetadata") or {}
        lic = (meta.get("LicenseShortName") or {}).get("value", "")
        artist = re.sub(r"<[^>]+>", "", (meta.get("Artist") or {}).get("value", "")).strip()
        out.append({"w": w, "h": h, "url": url, "title": p.get("title", ""),
                    "lic": lic, "artist": artist[:80]})
    return out


def _entity_score(c, want_portrait):
    """Adayı sırala: lisans serbestliği + makul en-boy + çözünürlük."""
    ar = (c["h"] / c["w"]) if c["w"] else 0
    # aşırı panoramik/çok dar görselleri ele (dikey video için kötü)
    if ar < 0.5 or ar > 3.0:
        shape = 3
    elif want_portrait:
        shape = abs(ar - 1.4)        # hafif dikey tercih
    else:
        shape = abs(ar - 1.0)
    return (_lic_rank(c["lic"]), round(shape, 2), -c["w"])


def wikimedia_image(query, out_img, want_portrait=True):
    """En uygun Commons görselini indirir. Döner: dict(atıf) veya None."""
    cands = wikimedia_search(query)
    # belirgin alakasızları ele (ör. 'gene', 'map of' gibi gürültü başlıklar)
    cands = [c for c in cands if not re.search(r"\b(gene|chromosome|dna|molecule)\b",
                                               c["title"], re.I)]
    if not cands:
        return None
    cands.sort(key=lambda c: _entity_score(c, want_portrait))
    best = cands[0]
    try:
        req = urllib.request.Request(best["url"], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r, open(out_img, "wb") as o:
            o.write(r.read())
    except Exception as e:
        print(f"[i] Wikimedia indirme hatası: {str(e)[:70]}")
        return None
    if os.path.getsize(out_img) < 8000:
        return None
    need_attr = _lic_rank(best["lic"]) != 0
    return {"source": "Wikimedia Commons", "title": best["title"],
            "license": best["lic"], "artist": best["artist"],
            "need_attribution": need_attr,
            "credit": (f'{best["title"].replace("File:", "")} — '
                       f'{best["artist"] or "Wikimedia Commons"} ({best["lic"]})')}


# ---------------------------------------------------------------- Pexels (stok)

def pexels_video(query, out_mp4):
    """Dikey stok video indirir (cache'li). Döner: dict veya None."""
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return None
    try:
        url = ("https://api.pexels.com/videos/search?orientation=portrait&size=medium"
               "&per_page=8&query=" + urllib.parse.quote(query))
        req = urllib.request.Request(url, headers={"Authorization": key, "User-Agent": UA})
        data = json.load(urllib.request.urlopen(req, timeout=20))
        vids = data.get("videos", [])
        if not vids:
            return None
        best = None
        for v in vids:
            for f in v["video_files"]:
                h, w = f.get("height") or 0, f.get("width") or 0
                if h >= w and 1080 <= h <= 2200:
                    score = abs(h - 1920)
                    if best is None or score < best[0]:
                        best = (score, f["link"])
        if not best:
            f = max(vids[0]["video_files"], key=lambda f: f.get("height", 0))
            best = (0, f["link"])
        dreq = urllib.request.Request(best[1], headers={"User-Agent": UA})
        with urllib.request.urlopen(dreq, timeout=60) as r, open(out_mp4, "wb") as o:
            o.write(r.read())
        return {"source": "Pexels", "license": "Pexels License", "need_attribution": False,
                "credit": f"Pexels — {query}"}
    except Exception as e:
        print(f"[i] Pexels '{query}' alınamadı: {str(e)[:70]}")
        return None


# ---------------------------------------------------------------- veri grafiği

BRAND_HEX = "#2BB194"
LIGHT_HEX = "#63D491"
BG_TOP = "#0F1719"
BG_BOT = "#0A1012"
WHITE_HEX = "#FFFFFF"
MUTE_HEX = "#9FB1AD"


def _grp_tr(n):
    return format(int(round(n)), ",").replace(",", ".")


def render_chart(payload, out_img):
    """Veri payload'ını dikey 1296x2304 grafiğe çevirir (line=backtest, bars=karşılaştırma).
    İçerik üst-orta güvenli bölgede; alt kısım altyazıya bırakılır."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    # kalın sans yükle (video ile tutarlı)
    try:
        font_manager.fontManager.addfont(SANS_B)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=SANS_B).get_name()
    except Exception:
        pass

    dpi = 200
    fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi)
    fig.patch.set_facecolor(BG_TOP)
    # dikey arka plan gradyanı
    axbg = fig.add_axes([0, 0, 1, 1]); axbg.axis("off")
    import numpy as np
    grad = np.linspace(0, 1, 256).reshape(-1, 1)
    axbg.imshow(grad, extent=[0, 1, 0, 1], aspect="auto",
                cmap=_two_color_cmap(BG_TOP, BG_BOT), zorder=0)

    kind = payload.get("kind", "line")
    if kind == "bars":
        _render_bars(fig, payload)
    else:
        _render_line(fig, payload)

    fig.savefig(out_img, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
    return out_img


def _two_color_cmap(c0, c1):
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("bg", [c1, c0])


def _render_line(fig, p):
    """Geri-dönük getiri: büyüyen çizgi + başlangıç/bitiş + büyük yüzde."""
    pts = p["points"]; xs = list(range(len(pts)))
    label = p.get("label", ""); unit = p.get("unit", "")
    pct = p.get("pct", 0)
    up = pct >= 0
    accent = LIGHT_HEX if up else "#FF6B6B"

    # üst başlık + büyük yüzde (güvenli bölge: üst)
    fig.text(0.5, 0.86, label.upper(), color=MUTE_HEX, fontsize=22,
             ha="center", va="center", fontweight="bold")
    fig.text(0.5, 0.80, f"{'+' if up else ''}{pct}%", color=accent, fontsize=78,
             ha="center", va="center", fontweight="bold")
    if "amount" in p and "end_value" in p:
        fig.text(0.5, 0.735,
                 f"{_grp_tr(p['amount'])} ₺  →  {_grp_tr(p['end_value'])} ₺",
                 color=WHITE_HEX, fontsize=30, ha="center", va="center", fontweight="bold")

    # grafik ekseni (orta bölge)
    ax = fig.add_axes([0.12, 0.30, 0.76, 0.36]); ax.set_facecolor("none")
    ax.plot(xs, pts, color=accent, linewidth=5, solid_capstyle="round", zorder=3)
    ax.fill_between(xs, pts, min(pts), color=accent, alpha=0.12, zorder=2)
    # başlangıç & bitiş noktaları
    ax.scatter([xs[0], xs[-1]], [pts[0], pts[-1]], s=90, color=accent, zorder=4,
               edgecolors=BG_TOP, linewidths=2)
    ax.annotate(f"{_grp_tr(pts[0])}", (xs[0], pts[0]), color=MUTE_HEX, fontsize=18,
                xytext=(6, -28), textcoords="offset points", fontweight="bold")
    ax.annotate(f"{_grp_tr(pts[-1])}", (xs[-1], pts[-1]), color=WHITE_HEX, fontsize=20,
                xytext=(-10, 14), textcoords="offset points", ha="right", fontweight="bold")
    rng = max(pts) - min(pts) or 1
    ax.set_ylim(min(pts) - rng * 0.15, max(pts) + rng * 0.22)
    ax.set_xlim(-0.4, len(pts) - 0.6)
    # x ay etiketleri kaldırıldı — altyazı bölgesiyle çakışmasın (dönem anlatımda geçer)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)


def _render_bars(fig, p):
    """Karşılaştırma: enstrümanlar arası yüzde getiri (yatay bar yarışı)."""
    items = p["items"]
    title = p.get("title", "BU YIL KİM KAZANDIRDI?")
    fig.text(0.5, 0.84, title.upper(), color=WHITE_HEX, fontsize=30,
             ha="center", va="center", fontweight="bold")
    ax = fig.add_axes([0.14, 0.34, 0.72, 0.40]); ax.set_facecolor("none")
    names = [i["name"] for i in items][::-1]
    pcts = [i["pct"] for i in items][::-1]
    ypos = range(len(names))
    colors = [LIGHT_HEX if v >= 0 else "#FF6B6B" for v in pcts]
    ax.barh(list(ypos), pcts, color=colors, height=0.6, zorder=3)
    maxv = max(abs(v) for v in pcts) or 1
    for y, v, n in zip(ypos, pcts, names):
        ax.text(v + maxv * 0.03 if v >= 0 else v - maxv * 0.03, y,
                f"%{v}", color=WHITE_HEX, fontsize=26, va="center",
                ha="left" if v >= 0 else "right", fontweight="bold")
        ax.text(0, y + 0.42, n, color=MUTE_HEX, fontsize=18, va="bottom",
                ha="left", fontweight="bold")
    ax.set_xlim(min(0, min(pcts)) - maxv * 0.1, maxv * 1.25)
    ax.set_yticks([]); ax.set_xticks([])
    for s in ax.spines.values():
        s.set_visible(False)


# ---------------------------------------------------------------- still → mp4

def still_to_broll(img, dur, out_mp4):
    """STILL'i 1296x2304 sabit kareye getirip kısa mp4 yazar (hareketi make_clip verir)."""
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"setsar=1,fps={FPS},eq=saturation=1.06")
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-t", f"{dur:.3f}", "-i", img,
                    "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-t", f"{dur:.3f}", out_mp4], check=True, capture_output=True)
    return out_mp4


# ---------------------------------------------------------------- resolve

def _slug(s):
    return re.sub(r"\W+", "_", s.strip().lower())[:60]


def resolve(spec, dur, out_mp4, cache_dir=CACHE):
    """spec={"type","query"} → make_clip'e uygun B-roll mp4. (path, attribution|None)."""
    os.makedirs(cache_dir, exist_ok=True)
    typ = (spec.get("type") or "concept").lower()
    query = spec.get("query", "").strip()

    # 0) Veri grafiği → matplotlib (gerçek veriden, her seferinde benzersiz)
    if typ == "chart" and spec.get("chart"):
        img = os.path.join(cache_dir, f"chart_{_slug(query or spec['chart'].get('label','c'))}.png")
        try:
            render_chart(spec["chart"], img)
            still_to_broll(img, dur, out_mp4)
            return out_mp4, {"source": "ParaFOMO (Yahoo Finance verisi)",
                             "need_attribution": False, "credit": "Veri: Yahoo Finance"}
        except Exception as e:
            print(f"[i] grafik üretilemedi: {str(e)[:80]} → stok'a düşülüyor")

    if not query:
        return None, None

    # 1) Gerçek varlık → Wikimedia still
    if typ in ENTITY_TYPES:
        img = os.path.join(cache_dir, f"wm_{_slug(query)}.jpg")
        attr = None
        if os.path.exists(img) and os.path.getsize(img) > 8000:
            attr = {"source": "Wikimedia Commons", "need_attribution": False, "credit": query}
        else:
            attr = wikimedia_image(query, img, want_portrait=(typ in {"person", "logo"}))
        if attr:
            still_to_broll(img, dur, out_mp4)
            return out_mp4, attr
        # Wikimedia bulamazsa stok videoya düş
        print(f"[i] Wikimedia '{query}' yok → Pexels'e düşülüyor")

    # 2) Soyut/sahne (veya entity fallback) → Pexels video
    cache_vid = os.path.join(cache_dir, f"px_{_slug(query)}.mp4")
    if os.path.exists(cache_vid) and os.path.getsize(cache_vid) > 10000:
        subprocess.run(["cp", cache_vid, out_mp4], check=True)
        return out_mp4, {"source": "Pexels", "need_attribution": False, "credit": query}
    attr = pexels_video(query, cache_vid)
    if attr and os.path.exists(cache_vid):
        subprocess.run(["cp", cache_vid, out_mp4], check=True)
        return out_mp4, attr
    return None, None


# ---------------------------------------------------------------- CLI test

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["test"])
    ap.add_argument("query")
    ap.add_argument("--type", default="person")
    ap.add_argument("--dur", type=float, default=4.0)
    ap.add_argument("--out", default="/tmp/vv_test.mp4")
    args = ap.parse_args()
    # .env (PEXELS) yükle
    envf = os.path.join(ROOT, ".env")
    if os.path.exists(envf):
        for ln in open(envf):
            m = re.match(r'\s*([A-Z_]+)=(.*)', ln)
            if m:
                os.environ.setdefault(m.group(1), m.group(2).strip())
    path, attr = resolve({"type": args.type, "query": args.query}, args.dur, args.out)
    if path:
        print(f"[+] OK → {path}")
        print(f"    atıf: {json.dumps(attr, ensure_ascii=False)}")
    else:
        print("[-] görsel çözülemedi")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
