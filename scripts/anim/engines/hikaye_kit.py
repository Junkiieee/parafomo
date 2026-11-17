"""'Para hikâyeleri' karakter ve dekor kiti (2026-11-17).

Kaan'ın beğendiği tarz (Miselyum kısa videoları): düz renkli vektör, basit geometrik karakter + büyük göz,
koyu atmosferik zemin. Burada paranın kişileştirilmiş karakterleri SVG olarak çizilir; parçalara id verilir ki
GSAP göz kırpma, bakış, ağız ve gövde hareketlerini canlandırabilsin. Gerçek banknot tasarımı KOPYALANMAZ
(yalnız renk + "100" işareti), başka kanalların karakterleri de kopyalanmaz.

    karakter(ad, ifade="normal", kid="k0") -> "<g id=kid>…</g>"   (600x600 koordinat sistemi, merkez 300,300)
    dekor(ad, kid) -> küçük nesneler (simit, ekmek, çay, sepet, para destesi)
Adlar: yuzluk, altin, zarf, ev, enflasyon, kumbara · ifadeler: normal, mutlu, endiseli, saskin, uzgun, korkmus
"""

KOYU = "#10202a"

# ---------------------------------------------------------------- yüz
KAS = {   # (sol kaş, sağ kaş) — göz merkezlerine göre göreli çizgiler
    "normal": ("M-38 -78 q38 -16 76 0", "M-38 -78 q38 -16 76 0"),
    "mutlu": ("M-38 -86 q38 -26 76 0", "M-38 -86 q38 -26 76 0"),
    "endiseli": ("M-40 -70 q40 -34 80 -8", "M-40 -78 q40 -26 80 8"),
    "saskin": ("M-38 -98 q38 -26 76 0", "M-38 -98 q38 -26 76 0"),
    "uzgun": ("M-40 -82 q40 6 80 18", "M-40 -64 q40 -12 80 -18"),
    "korkmus": ("M-40 -84 q40 -30 80 -6", "M-40 -90 q40 -24 80 6"),
}
AGIZ = {
    "normal": ('<path d="M-30 0 q30 22 60 0" fill="none" stroke="{k}" stroke-width="10" stroke-linecap="round"/>'),
    "mutlu": ('<path d="M-44 -6 q44 70 88 0 z" fill="{k}"/><path d="M-22 22 q22 14 44 0" fill="#e86a6a"/>'),
    "endiseli": ('<path d="M-32 10 q16 -14 32 0 q16 14 32 0" fill="none" stroke="{k}" stroke-width="10" stroke-linecap="round"/>'),
    "saskin": ('<ellipse cx="0" cy="8" rx="22" ry="28" fill="{k}"/>'),
    "uzgun": ('<path d="M-32 16 q32 -26 64 0" fill="none" stroke="{k}" stroke-width="10" stroke-linecap="round"/>'),
    "korkmus": ('<path d="M-36 14 l12 -12 l12 12 l12 -12 l12 12 l12 -12" fill="none" stroke="{k}" stroke-width="9" '
                'stroke-linecap="round" stroke-linejoin="round"/>'),
}


def yuz(kid, cx, cy, ifade="normal", aralik=130, goz=52, renk=KOYU, agiz_y=118):
    """İki büyük göz + kaş + ağız. Parça id'leri: {kid}-gozler, {kid}-gl/gr (göz akı), {kid}-bl/br (bebek), {kid}-agiz."""
    ifade = ifade if ifade in KAS else "normal"
    kl, kr = KAS[ifade]
    bebek = 0.42 if ifade != "korkmus" else 0.26
    out = [f'<g id="{kid}-gozler">']
    for t, x in (("l", cx - aralik / 2), ("r", cx + aralik / 2)):
        out.append(f'<g id="{kid}-g{t}" class="goz" transform="translate({x:.1f} {cy:.1f})">'
                   f'<ellipse rx="{goz}" ry="{goz * 1.12:.1f}" fill="#fff"/>'
                   f'<g id="{kid}-b{t}"><circle cx="6" cy="8" r="{goz * bebek:.1f}" fill="{renk}"/>'
                   f'<circle cx="{6 + goz * 0.2:.1f}" cy="{8 - goz * 0.2:.1f}" r="{goz * 0.14:.1f}" fill="#fff"/></g></g>')
    out.append("</g>")
    out.append(f'<path id="{kid}-kl" d="{kl}" transform="translate({cx - aralik / 2:.1f} {cy:.1f})" fill="none" '
               f'stroke="{renk}" stroke-width="11" stroke-linecap="round"/>')
    out.append(f'<path id="{kid}-kr" d="{kr}" transform="translate({cx + aralik / 2 - 0:.1f} {cy:.1f}) scale(-1 1)" '
               f'fill="none" stroke="{renk}" stroke-width="11" stroke-linecap="round"/>')
    out.append(f'<g id="{kid}-agiz" transform="translate({cx:.1f} {cy + agiz_y:.1f})">{AGIZ[ifade].format(k=renk)}</g>')
    if ifade == "uzgun":
        out.append(f'<path id="{kid}-yas" d="M{cx + aralik / 2 + 30:.1f} {cy + 40:.1f} q10 22 0 34 q-10 -12 0 -34z" fill="#8fd3ff"/>')
    return "".join(out)


# ---------------------------------------------------------------- karakterler
def _yuzluk(kid, ifade):
    mavi, koyu, acik = "#3b82c4", "#2a5f91", "#cfe6fb"
    return (f'<g id="{kid}-ayak" stroke="{koyu}" stroke-width="14" stroke-linecap="round" fill="none">'
            f'<path d="M215 440 l-26 96"/><path d="M265 445 l6 92"/><path d="M335 445 l-6 92"/><path d="M385 440 l26 96"/></g>'
            f'<g id="{kid}-kol" stroke="{koyu}" stroke-width="13" stroke-linecap="round" fill="none">'
            f'<path id="{kid}-kolL" d="M62 300 q-48 18 -58 70"/><path id="{kid}-kolR" d="M538 300 q48 18 58 70"/></g>'
            f'<g id="{kid}-govde"><rect x="60" y="150" width="480" height="300" rx="44" fill="{mavi}"/>'
            f'<rect x="60" y="150" width="480" height="150" rx="44" fill="#fff" opacity=".10"/>'
            f'<rect x="98" y="186" width="404" height="228" rx="28" fill="none" stroke="{acik}" stroke-width="7" '
            f'stroke-dasharray="1 17" stroke-linecap="round"/>'
            f'<text x="118" y="250" font-family="Baslik, Anton, sans-serif" font-size="58" fill="{acik}">100</text>'
            f'<circle cx="468" cy="378" r="22" fill="none" stroke="{acik}" stroke-width="6"/></g>'
            + yuz(kid, 300, 300, ifade, aralik=128, goz=48))


def _dolar(kid, ifade):
    yesil, koyu, acik = "#3f9d63", "#2b7047", "#d3f2dd"
    return (f'<g id="{kid}-ayak" stroke="{koyu}" stroke-width="14" stroke-linecap="round" fill="none">'
            f'<path d="M215 440 l-26 96"/><path d="M265 445 l6 92"/><path d="M335 445 l-6 92"/><path d="M385 440 l26 96"/></g>'
            f'<g id="{kid}-kol" stroke="{koyu}" stroke-width="13" stroke-linecap="round" fill="none">'
            f'<path d="M62 300 q-48 18 -58 70"/><path d="M538 300 q48 18 58 70"/></g>'
            f'<g id="{kid}-govde"><rect x="60" y="150" width="480" height="300" rx="44" fill="{yesil}"/>'
            f'<rect x="60" y="150" width="480" height="150" rx="44" fill="#fff" opacity=".10"/>'
            f'<rect x="98" y="186" width="404" height="228" rx="28" fill="none" stroke="{acik}" stroke-width="7" '
            f'stroke-dasharray="1 17" stroke-linecap="round"/>'
            f'<text x="118" y="250" font-family="Baslik, Anton, sans-serif" font-size="58" fill="{acik}">$</text>'
            f'<text x="452" y="398" font-family="Baslik, Anton, sans-serif" font-size="46" fill="{acik}">$</text></g>'
            + yuz(kid, 300, 300, ifade, aralik=128, goz=48))


def _yuzde(kid, ifade):
    mor, koyu = "#7b5cd6", "#5a3fb0"
    return (f'<g id="{kid}-ayak" stroke="{koyu}" stroke-width="14" stroke-linecap="round" fill="none">'
            f'<path d="M240 470 l-18 74"/><path d="M360 470 l18 74"/></g>'
            f'<g id="{kid}-govde"><rect x="110" y="110" width="380" height="380" rx="90" fill="{mor}"/>'
            f'<rect x="110" y="110" width="380" height="190" rx="90" fill="#fff" opacity=".10"/>'
            f'<text x="300" y="250" text-anchor="middle" font-family="Baslik, Anton, sans-serif" font-size="120" fill="#e7defc">%</text></g>'
            + yuz(kid, 300, 330, ifade, aralik=120, goz=40, agiz_y=86))


def _altin(kid, ifade):
    return (f'<g id="{kid}-govde"><circle cx="300" cy="300" r="205" fill="#d99a1e"/>'
            f'<circle cx="300" cy="292" r="200" fill="#f6c443"/>'
            f'<circle cx="300" cy="292" r="168" fill="none" stroke="#ffe08a" stroke-width="10" stroke-dasharray="3 16" stroke-linecap="round"/>'
            f'<path d="M180 170 q60 -60 150 -50" stroke="#fff6cc" stroke-width="18" fill="none" stroke-linecap="round" opacity=".7"/></g>'
            + yuz(kid, 300, 285, ifade, aralik=124, goz=46, renk="#5a3a06"))


def _zarf(kid, ifade):
    return (f'<g id="{kid}-ayak" stroke="#b9a37a" stroke-width="13" stroke-linecap="round" fill="none">'
            f'<path d="M230 460 l-14 84"/><path d="M370 460 l14 84"/></g>'
            f'<g id="{kid}-govde"><rect x="70" y="170" width="460" height="295" rx="26" fill="#f3e6c8"/>'
            f'<path id="{kid}-kapak" d="M70 196 L300 330 L530 196 L530 196 Q530 170 504 170 L96 170 Q70 170 70 196 Z" fill="#e7d3a6"/>'
            f'<g transform="translate(408 228) rotate(8)"><rect x="-74" y="-30" width="148" height="56" rx="10" fill="none" '
            f'stroke="#c0503a" stroke-width="6"/><text x="0" y="14" text-anchor="middle" font-family="Baslik, Anton, sans-serif" '
            f'font-size="36" fill="#c0503a">MAAŞ</text></g></g>'
            + yuz(kid, 300, 352, ifade, aralik=120, goz=40, agiz_y=80))


def _ev(kid, ifade):
    return (f'<g id="{kid}-govde"><rect x="372" y="118" width="46" height="96" rx="6" fill="#8a4b39"/>'
            f'<path d="M92 290 L300 112 L508 290 Z" fill="#c8553d"/><path d="M92 290 L300 112 L330 138 L132 290 Z" fill="#fff" opacity=".10"/>'
            f'<rect x="130" y="282" width="340" height="250" rx="14" fill="#f2e2c4"/>'
            f'<rect x="262" y="430" width="76" height="102" rx="10" fill="#8a4b39"/><circle cx="324" cy="482" r="6" fill="#f2c26b"/>'
            f'<rect x="268" y="190" width="64" height="40" rx="8" fill="#f4c26b" opacity=".9"/></g>'
            + yuz(kid, 300, 352, ifade, aralik=150, goz=38, agiz_y=62))


def _enflasyon(kid, ifade):
    ifade = ifade if ifade in ("normal", "mutlu", "saskin") else "normal"
    dis = "".join(f'<path d="M{x} 338 l14 26 l14 -26z" fill="#fff"/>' for x in range(214, 372, 28))
    return (f'<g id="{kid}-govde"><path d="M300 92 C430 92 520 190 512 318 C506 430 420 512 300 512 C180 512 92 432 88 318 '
            f'C84 190 170 92 300 92 Z" fill="#5b2d8e"/>'
            f'<path d="M190 140 q-40 -60 -20 -96 q24 34 54 70z M410 140 q40 -60 20 -96 q-24 34 -54 70z" fill="#5b2d8e"/>'
            f'<path d="M300 92 C430 92 520 190 512 318 C470 230 400 170 300 160 C200 170 130 230 88 318 C84 190 170 92 300 92 Z" '
            f'fill="#fff" opacity=".07"/></g>'
            f'<g id="{kid}-gozler"><g id="{kid}-gl" transform="translate(236 252)"><ellipse rx="40" ry="34" fill="#ffd34d"/>'
            f'<g id="{kid}-bl"><ellipse cx="4" cy="2" rx="9" ry="22" fill="#1a0b2e"/></g></g>'
            f'<g id="{kid}-gr" transform="translate(364 252)"><ellipse rx="40" ry="34" fill="#ffd34d"/>'
            f'<g id="{kid}-br"><ellipse cx="4" cy="2" rx="9" ry="22" fill="#1a0b2e"/></g></g></g>'
            f'<path d="M188 214 l70 22 M412 214 l-70 22" stroke="#1a0b2e" stroke-width="13" stroke-linecap="round"/>'
            f'<g id="{kid}-agiz"><path d="M196 330 Q300 470 404 330 Z" fill="#1a0b2e"/>{dis}'
            f'<path d="M262 410 q38 20 76 0 q-38 34 -76 0z" fill="#d94f6b"/></g>')


def _kumbara(kid, ifade):
    pembe, koyu = "#f29bb5", "#d9718f"
    return (f'<g id="{kid}-ayak" fill="{koyu}"><rect x="170" y="430" width="44" height="74" rx="14"/>'
            f'<rect x="380" y="430" width="44" height="74" rx="14"/></g>'
            f'<g id="{kid}-govde"><ellipse cx="300" cy="330" rx="230" ry="170" fill="{pembe}"/>'
            f'<path d="M150 200 l10 -70 l60 50z" fill="{koyu}"/><rect x="250" y="168" width="100" height="16" rx="8" fill="{koyu}"/>'
            f'<ellipse cx="300" cy="300" rx="200" ry="70" fill="#fff" opacity=".08"/>'
            f'<ellipse cx="510" cy="340" rx="40" ry="48" fill="{koyu}"/><circle cx="500" cy="328" r="7" fill="#8a3550"/>'
            f'<circle cx="502" cy="354" r="7" fill="#8a3550"/>'
            f'<path d="M72 320 q-36 -10 -30 -40" stroke="{koyu}" stroke-width="10" fill="none" stroke-linecap="round"/></g>'
            + yuz(kid, 330, 300, ifade, aralik=120, goz=36, agiz_y=74))


# ---------------------------------------------------------------- insanlar (2026-11-17)
# Araştırma (YouTube TR finans Shorts, Eyl–Kas 2026): küçük kanallarda patlayan 2D para hikâyelerinin hepsi
# gündelik ikilemdeki İNSANLARI anlatıyor (aynı maaşı alan iki iş arkadaşı, kiracı–ev sahibi, emekli).
# Para karakterleri bu hikâyelerde sahne nesnesi ya da kötü karakter (enflasyon) olur. Aynı büyük göz yüzü.
def _insan(kid, ifade, ten, sac_arka, sac_on, govde, ekstra=""):
    """Ortak insan gövdesi: büyük kafa (300,215), kısa gövde, çubuk kol/bacak. 600x600."""
    koyu = "#22313a"
    return (f'<g id="{kid}-ayak" stroke="{koyu}" stroke-width="16" stroke-linecap="round" fill="none">'
            f'<path d="M262 530 l-8 52"/><path d="M338 530 l8 52"/></g>'
            f'<g id="{kid}-kol" stroke="{ten}" stroke-width="22" stroke-linecap="round" fill="none">'
            f'<path id="{kid}-kolL" d="M196 420 q-44 34 -46 92"/><path id="{kid}-kolR" d="M404 420 q44 34 46 92"/></g>'
            f'<g id="{kid}-govde">{govde}</g>'
            f'{sac_arka}'
            f'<circle cx="300" cy="215" r="148" fill="{ten}"/>'
            f'<ellipse cx="300" cy="150" rx="104" ry="40" fill="#fff" opacity=".10"/>'
            f'{sac_on}{ekstra}'
            + yuz(kid, 300, 220, ifade, aralik=104, goz=36, agiz_y=86))


def _kadin(kid, ifade):   # genç çalışan kadın
    sac = "#3b2a24"
    arka = f'<path d="M144 230 Q140 70 300 62 Q460 70 456 230 L460 372 Q412 392 382 352 L218 352 Q188 392 140 372 Z" fill="{sac}"/>'
    on = f'<path d="M156 196 Q170 80 300 74 Q420 80 446 178 Q380 120 304 132 Q228 120 156 196 Z" fill="{sac}"/>'
    govde = ('<path d="M190 560 Q186 404 236 372 L364 372 Q414 404 410 560 Z" fill="#2bb3a3"/>'
             '<path d="M270 372 L300 420 L330 372 Z" fill="#f5f0e6"/>')
    return _insan(kid, ifade, "#f2c9a5", arka, on, govde)


def _erkek(kid, ifade):   # genç çalışan erkek
    sac = "#2b1e17"
    on = f'<path d="M154 214 Q146 70 300 64 Q456 70 448 210 Q430 140 372 132 Q330 150 286 126 Q220 138 172 150 Q158 176 154 214 Z" fill="{sac}"/>'
    govde = ('<path d="M190 560 Q186 404 236 372 L364 372 Q414 404 410 560 Z" fill="#f08a3c"/>'
             '<path d="M262 372 L300 410 L338 372" fill="none" stroke="#c9692a" stroke-width="10" stroke-linejoin="round"/>')
    return _insan(kid, ifade, "#e8b48a", "", on, govde)


def _emekli(kid, ifade):   # emekli amca: kır saç, bıyık, gözlük
    on = ('<path d="M152 240 Q140 150 196 118 Q186 176 196 222 Z M448 240 Q460 150 404 118 Q414 176 404 222 Z" fill="#d7dadd"/>')
    gozluk = ('<g fill="none" stroke="#3a3f45" stroke-width="8"><circle cx="248" cy="220" r="48"/><circle cx="352" cy="220" r="48"/>'
              '<path d="M296 214 q4 -8 8 0"/></g>'
              '<path d="M248 288 Q300 270 352 288 Q330 312 300 300 Q270 312 248 288 Z" fill="#d7dadd"/>')
    govde = ('<path d="M190 560 Q186 404 236 372 L364 372 Q414 404 410 560 Z" fill="#8a6a4a"/>'
             '<path d="M300 380 L300 560" stroke="#6f5338" stroke-width="8"/><circle cx="300" cy="430" r="7" fill="#e9d8b8"/>'
             '<circle cx="300" cy="490" r="7" fill="#e9d8b8"/>')
    return _insan(kid, ifade, "#f0c8a0", "", on, govde, ekstra=gozluk)


def _evsahibi(kid, ifade):   # ev sahibi / patron: takım elbise, kravat
    sac = "#4a3b33"
    on = f'<path d="M156 200 Q150 76 300 68 Q452 76 446 196 Q404 112 300 112 Q214 112 172 150 Q160 170 156 200 Z" fill="{sac}"/>'
    govde = ('<path d="M190 560 Q186 404 236 372 L364 372 Q414 404 410 560 Z" fill="#2f3e57"/>'
             '<path d="M262 372 L300 470 L338 372 Z" fill="#f5f0e6"/>'
             '<path d="M300 384 L286 404 L300 470 L314 404 Z" fill="#c0392b"/>'
             '<path d="M236 372 L300 470 M364 372 L300 470" fill="none" stroke="#23304a" stroke-width="8"/>'
             '<circle cx="300" cy="500" r="7" fill="#8fa0bd"/>')
    return _insan(kid, ifade, "#efc39b", "", on, govde)


KARAKTER = {"yuzluk": _yuzluk, "dolar": _dolar, "yuzde": _yuzde, "altin": _altin, "zarf": _zarf, "ev": _ev, "enflasyon": _enflasyon, "kumbara": _kumbara,
            "kadin": _kadin, "erkek": _erkek, "emekli": _emekli, "evsahibi": _evsahibi}


def karakter(ad, ifade="normal", kid="k0"):
    if ad not in KARAKTER:
        raise ValueError(f"bilinmeyen karakter: {ad} ({', '.join(KARAKTER)})")
    return f'<g id="{kid}" class="karakter">{KARAKTER[ad](kid, ifade)}</g>'


# ---------------------------------------------------------------- dekor (küçük nesneler, 200x200)
def dekor(ad, kid="d0"):
    if ad == "simit":
        susam = "".join(f'<ellipse cx="{100 + 62 * c:.0f}" cy="{100 + 62 * s:.0f}" rx="4" ry="2.4" fill="#fff4d6"/>'
                        for c, s in ((1, 0), (.7, .7), (0, 1), (-.7, .7), (-1, 0), (-.7, -.7), (0, -1), (.7, -.7)))
        return (f'<g id="{kid}"><circle cx="100" cy="100" r="80" fill="#b5652a"/><circle cx="100" cy="100" r="32" fill="#0b1512"/>'
                f'<circle cx="100" cy="100" r="80" fill="none" stroke="#d08a4b" stroke-width="8" opacity=".6"/>{susam}</g>')
    if ad == "ekmek":
        return (f'<g id="{kid}"><path d="M20 130 Q20 60 100 56 Q180 60 180 130 Z" fill="#d79b52"/>'
                f'<rect x="20" y="124" width="160" height="22" rx="8" fill="#c0843f"/>'
                f'<path d="M64 84 l16 22 M98 76 l16 24 M132 84 l14 22" stroke="#f3c98d" stroke-width="7" stroke-linecap="round"/></g>')
    if ad == "cay":
        return (f'<g id="{kid}"><path d="M70 40 Q60 80 74 104 Q60 130 72 168 L128 168 Q140 130 126 104 Q140 80 130 40 Z" '
                f'fill="#ffffff" opacity=".25"/><path d="M74 70 Q66 90 78 106 Q66 128 76 160 L124 160 Q134 128 122 106 '
                f'Q134 90 126 70 Z" fill="#c2421f"/><ellipse cx="100" cy="180" rx="54" ry="10" fill="#e9e1d3"/></g>')
    if ad == "sepet":
        return (f'<g id="{kid}"><path d="M20 50 L50 50 L72 130 L166 130 L182 74 L60 74" fill="none" stroke="#e9eef0" '
                f'stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/><circle cx="84" cy="160" r="14" fill="#e9eef0"/>'
                f'<circle cx="152" cy="160" r="14" fill="#e9eef0"/></g>')
    if ad == "deste":
        return (f'<g id="{kid}">' + "".join(f'<rect x="{30 + 6 * i}" y="{120 - 18 * i}" width="140" height="60" rx="8" '
                                             f'fill="{"#3b82c4" if i % 2 == 0 else "#356fa8"}"/>' for i in range(4)) + '</g>')
    raise ValueError(f"bilinmeyen dekor: {ad}")
