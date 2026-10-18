#!/usr/bin/env python3
"""Canlı blog yazıları — Jinja2 şablonu + veri JSON'ları → src/content/blog/<slug>.md

Neden: zam sezonu yazılarındaki rakamlar elle yazılıp bayatlıyordu. "2027 zamları" rehberi
"2027 yeniden değerleme oranı tahmini" aramasında p6 iken 3 Kasım'da (Ekim Yİ-ÜFE) oran
açıklandığında hâlâ "tahmin %27,8" diyecekti; emlak vergisi satırı da kanun değişikliğinden
habersiz kalmıştı. Şablon yazıların rakamları ve durum cümleleri (tahmin → kesinleşti → tebliğ)
veri dosyalarından gelir; veriyi güncelleyen her hat bu betiği çağırır (kira-artis-update.sh).

Şablon: content-templates/blog/<slug>.md.j2   (Jinja2; bağlam aşağıda build_context())
Çıktı:  src/content/blog/<slug>.md             (frontmatter başında "# OTOMATİK" yorumu)
Durum:  data/live-posts-state.json             (son üretilen içeriğin özeti → elle düzenleme tespiti)

Kurallar:
  - Üretilen dosya DOĞRUDAN düzenlenmez; değişiklik şablona yapılır, sonra bu betik çalışır.
  - Dosya, son üretimden sonra elle değiştirildiyse ÜZERİNE YAZILMAZ: "UYARI ... elle düzenlenmiş"
    basılır (health.py gösterir). Değişikliği şablona taşı, sonra `--adopt <slug>` ile devral.
  - Gövde değişince updatedDate bugüne (İstanbul) çekilir → sitemap lastmod + "güncellendi" sinyali.
  - Bağlamdaki eksik alan/şablon hatası o yazıyı ATLAR (bozuk içerik yazılmaz), diğerlerine devam eder.

Kullanım:
  python3 scripts/live-posts.py               # değişenleri yaz → "GÜNCELLENDİ <slug>"
  python3 scripts/live-posts.py --check       # yazmadan rapor (fark / elle düzenleme)
  python3 scripts/live-posts.py --adopt SLUG  # mevcut dosyayı ezip şablondan üret (ilk devralma)
  python3 scripts/live-posts.py --print SLUG  # üretilecek içeriği ekrana bas
Çıkış kodu daima 0 (veri hatlarını bozmaz).
"""
import datetime as dt
import glob
import hashlib
import json
import math
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL_DIR = os.path.join(REPO, "content-templates", "blog")
OUT_DIR = os.path.join(REPO, "src", "content", "blog")
STATE = os.path.join(REPO, "data", "live-posts-state.json")
MARKER = "# OTOMATİK ÜRETİLİR"

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos",
         "Eylül", "Ekim", "Kasım", "Aralık"]


# ----------------------------- biçimlendirme -----------------------------

def num(x, d=0):
    """Türkçe sayı: 7350.5 → '7.351' (d=0), 27.81 → '27,81' (d=2)."""
    s = f"{float(x):,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def pct(x, d=1):
    return "%" + num(x, d)


def tl(x):
    return num(math.floor(float(x) + 1e-9)) + " TL"


def ay_adi(key):
    """'2026-10' → 'Ekim 2026'."""
    return f"{AYLAR[int(key[5:7]) - 1]} {key[:4]}"


def tarih(iso):
    """'2026-11-03' → '3 Kasım 2026'."""
    d = dt.date.fromisoformat(str(iso)[:10])
    return f"{d.day} {AYLAR[d.month - 1]} {d.year}"


def gun_ay(iso):
    """'2026-11-03' → '3 Kasım' (Türkçe ek eklenecek yerlerde: "3 Kasım'da", "3 Kasım'ı")."""
    d = dt.date.fromisoformat(str(iso)[:10])
    return f"{d.day} {AYLAR[d.month - 1]}"


def istanbul_today():
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=3)).date()


# ----------------------------- bağlam -----------------------------

def _load(name):
    with open(os.path.join(REPO, "data", name), encoding="utf-8") as f:
        return json.load(f)


def _release_of(covers):
    """TÜİK takviminden 'Ekim 2026' verisinin açıklanma günü (yoksa None)."""
    for p in sorted(glob.glob(os.path.join(REPO, "data", "tuik-enflasyon-*.json"))):
        try:
            for r in json.load(open(p, encoding="utf-8"))["releases"]:
                if r.get("covers") == covers:
                    return r["date"]
        except Exception:
            continue
    return None


def ctx_yd():
    """data/yeniden-degerleme.json → yeniden değerleme oranı bağlamı (sayfa mantığıyla aynı)."""
    yd = _load("yeniden-degerleme.json")
    hedef = int(yd["hedefYil"])
    teblig = yd.get("tebligOrani")
    uygulanan = yd.get("uygulananOrani")
    oran = float(teblig if teblig is not None else yd["onikiAyOrt"])
    durum = "teblig" if teblig is not None else ("hesap" if yd.get("ekimVerisiGeldi") else "tahmin")
    son_ay = yd["sonAy"]
    kalan = max(0, 10 - int(son_ay[5:7])) if durum == "tahmin" else 0
    veri_son = yd.get("veriSonAy") or son_ay
    aylar = sorted((m for m in yd["months"] if m["ay"] <= veri_son), key=lambda m: m["ay"])[-5:]
    gecmis = sorted(yd.get("gecmis") or [], key=lambda g: g["uygulamaYili"])
    onceki = next((g for g in gecmis if g["uygulamaYili"] == hedef - 1), None)
    harc_oran = float(uygulanan) if uygulanan is not None else oran

    def zam(tutar, kalem="vergi"):
        """2026 tutarının hedef yıl karşılığı (kuruş atılır). kalem='harc' → CB kararı varsa o oran."""
        r = harc_oran if kalem == "harc" else oran
        return math.floor(float(tutar) * (1 + r / 100) + 1e-9)

    def senaryo(tutar, r):
        return math.floor(float(tutar) * (1 + r / 100) + 1e-9)

    return {
        "hedef": hedef, "onceki_yil": hedef - 1, "oran": oran, "durum": durum,
        "teblig": teblig, "uygulanan": uygulanan, "harc_oran": harc_oran,
        "son_ay": son_ay, "son_ay_adi": ay_adi(son_ay), "kalan_ay": kalan,
        "veri_son_ay_adi": ay_adi(veri_son),
        "aylar": [{"adi": ay_adi(m["ay"]), "aylik": m["aylik"], "yillik": m["yillik"]} for m in aylar],
        "gecmis": gecmis, "onceki": onceki,
        "bant_alt": math.floor(oran), "bant_ust": math.ceil(oran + 1),
        "kesinlesme_gunu": _release_of(f"Ekim {hedef - 1}") or f"{hedef - 1}-11-03",
        "sonraki_aciklama": yd.get("sonrakiAciklama"),
        "guncellendi": yd.get("updated"),
        "zam": zam, "senaryo": senaryo,
    }


def build_context():
    ctx = {"bugun": istanbul_today().isoformat()}
    for key, fn in (("yd", ctx_yd),):
        try:
            ctx[key] = fn()
        except Exception as e:  # tek kaynak bozuksa onu kullanan şablonlar StrictUndefined ile atlanır
            print(f"[live-posts] UYARI: bağlam '{key}' kurulamadı: {e}")
    return ctx


# ----------------------------- üretim -----------------------------

def _env():
    try:
        import jinja2
    except ImportError:
        print("[live-posts] UYARI: jinja2 yok (python3 -m pip install jinja2) — hiçbir yazı üretilmedi")
        return None
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TPL_DIR),
        undefined=jinja2.StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )
    env.filters.update(num=num, pct=pct, tl=tl, ay_adi=ay_adi, tarih=tarih, gun_ay=gun_ay)
    return env


UPD_RE = re.compile(r"^updatedDate:.*$", re.M)


def normalize(text):
    """Karşılaştırma için: updatedDate satırı ve satır sonu boşlukları hariç."""
    text = UPD_RE.sub("updatedDate: X", text)
    return "\n".join(line.rstrip() for line in text.strip().splitlines()) + "\n"


def digest(text):
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()[:16]


def current_updated(text):
    m = re.search(r"^updatedDate:\s*['\"]?([0-9-]{10})", text, re.M)
    if m:
        return m.group(1)
    m = re.search(r"^pubDate:\s*['\"]?([0-9-]{10})", text, re.M)
    return m.group(1) if m else istanbul_today().isoformat()


def render(env, name, ctx, updated):
    out = env.get_template(name).render(**ctx, updated=updated)
    if MARKER not in out.split("---", 2)[1]:
        raise ValueError(f"şablon frontmatter'ında '{MARKER}' yorumu yok")
    return out


def load_state():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return {}


def save_state(state):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def main(argv):
    check = "--check" in argv
    adopt = argv[argv.index("--adopt") + 1] if "--adopt" in argv else None
    show = argv[argv.index("--print") + 1] if "--print" in argv else None
    env = _env()
    if env is None:
        return 0
    ctx = build_context()
    state = load_state()
    changed_state = False
    templates = sorted(os.path.basename(p) for p in glob.glob(os.path.join(TPL_DIR, "*.md.j2")))
    for name in templates:
        slug = name[:-len(".md.j2")]
        if show and slug != show:
            continue
        out_path = os.path.join(OUT_DIR, f"{slug}.md")
        cur = open(out_path, encoding="utf-8").read() if os.path.exists(out_path) else None
        try:
            prev_upd = current_updated(cur) if cur else istanbul_today().isoformat()
            new = render(env, name, ctx, prev_upd)
            if cur is not None and normalize(new) != normalize(cur):
                new = render(env, name, ctx, istanbul_today().isoformat())
        except Exception as e:
            print(f"[live-posts] UYARI: {slug} üretilemedi ({type(e).__name__}: {e}) — dosyaya dokunulmadı")
            continue
        if show:
            sys.stdout.write(new)
            return 0
        rec = state.get(slug)
        if cur is not None and slug != adopt:
            if rec is None:
                print(f"[live-posts] UYARI: {slug} henüz devralınmadı (elle yazılmış dosya) — "
                      f"`python3 scripts/live-posts.py --adopt {slug}` ile devral")
                continue
            if digest(cur) != rec.get("hash"):
                print(f"[live-posts] UYARI: {slug} elle düzenlenmiş (son üretimden farklı) — ÜZERİNE YAZILMADI. "
                      f"Değişikliği content-templates/blog/{name} şablonuna taşı, sonra --adopt {slug}")
                continue
        if cur is not None and normalize(new) == normalize(cur):
            if check:
                print(f"[live-posts] {slug}: güncel")
            continue
        if check:
            print(f"[live-posts] {slug}: GÜNCELLENECEK (veri değişti)")
            continue
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(new)
        state[slug] = {"hash": digest(new), "uretim": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                       "sablon": f"content-templates/blog/{name}"}
        changed_state = True
        print(f"[live-posts] GÜNCELLENDİ {slug}")
    if changed_state and not check:
        save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
