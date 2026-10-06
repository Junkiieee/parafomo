#!/usr/bin/env python3
"""
ParaFOMO Büyüme Ajanı — BÜYÜME MOTORU (token'sız fırsat üretici / "eller").

Darboğaz on-page üretim değil; OTORİTE + DAĞITIM + gösterim havuzu. Bu script,
zaten üretilmiş artefaktları (docs/seo-opportunities.md, kpi-history.jsonl,
sayfa/blog envanteri) okuyup beynin gece kararları için 4 fırsat bloğu üretir.
Canlı GSC/GA çağırmaz (o veriler dashboard/seo-opportunities tarafından üretilir);
canlı-web (SERP okuma) beynin WebFetch'i tarafından yapılır — burada sadece
NEYE bakılacağı seçilir. Hiç LLM çağırmaz, hiç token yakmaz.

Bloklar:
  A) Araç/veri sayfası adayları  — havuzu BÜYÜTEN toolable-niyet sorguları
  B) SERP-boşluk hedefleri       — sayfa-2 sorguları (beyin canlı SERP analizi yapsın)
  C) Dağıtım hedefleri           — güçlü sayfalar → backlink/atıf kuyruğu taslağı
  D) Öncü göstergeler            — kpi-history kısa-vade deltaları (deneyi hızlı kapat)

Kullanım: python3 agent/growth-engine.py   (stdout → digest'e gömülür)
"""
import os, re, json, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPP_MD = os.path.join(ROOT, "docs", "seo-opportunities.md")
HIST = os.path.join(ROOT, "agent", "memory", "kpi-history.jsonl")
PAGES_DIR = os.path.join(ROOT, "src", "pages")
BLOG_DIR = os.path.join(ROOT, "src", "content", "blog")
DATA_DIR = os.path.join(ROOT, "data")

# Toolable niyet: veri/hesaplama/karşılaştırma sayfası olabilecek sorgular.
# (blog yazısı değil — kendi başına trafik çeken, rakibin zayıf olduğu HEDEF SAYFA)
TOOL_HINTS = {
    "hesapla": "hesaplayıcı", "hesaplama": "hesaplayıcı", "ne kadar": "hesaplayıcı",
    "kaç tl": "hesaplayıcı", "kaç lira": "hesaplayıcı", "kaç para": "hesaplayıcı",
    "çevir": "çevirici", "çevirici": "çevirici", "kuru": "canlı-veri", "kur": "canlı-veri",
    "fiyat": "canlı-veri", "fiyatı": "canlı-veri", "ne kadar oldu": "canlı-veri",
    "canlı": "canlı-veri", "bugün": "canlı-veri", "kaç": "hesaplayıcı",
    "takvim": "veri-tablosu", "listesi": "veri-tablosu", "tablosu": "veri-tablosu",
    "karşılaştır": "karşılaştırma", "vs": "karşılaştırma", "mı yoksa": "karşılaştırma",
    "getiri": "hesaplayıcı", "faiz oranı": "canlı-veri", "oranları": "veri-tablosu",
}

# Yaygın TR durak kelimeler (page/query eşleştirme için gürültü temizliği)
STOP = set("nedir ne demek nasıl için ile ve veya bir bu şu o mi mı mu mü en".split())


def parse_opportunities():
    """seo-opportunities.md → [{query, impressions, position, clicks}] (sıralı)."""
    rows = []
    if not os.path.exists(OPP_MD):
        return rows
    pat = re.compile(
        r"`([^`]+)`\s*—\s*gösterim\s*(\d+),\s*sıra\s*([\d.]+),\s*tıklama\s*(\d+)")
    for line in open(OPP_MD, encoding="utf-8"):
        m = pat.search(line)
        if m:
            rows.append({
                "query": m.group(1).strip(),
                "impr": int(m.group(2)),
                "pos": float(m.group(3)),
                "clicks": int(m.group(4)),
            })
    return rows


def existing_page_slugs():
    """Var olan hedef sayfalar (blog HARİÇ .astro sayfaları) + blog slug'ları."""
    astro = set()
    for p in glob.glob(os.path.join(PAGES_DIR, "**", "*.astro"), recursive=True):
        astro.add(os.path.splitext(os.path.basename(p))[0].lower())
    blog = set()
    for p in glob.glob(os.path.join(BLOG_DIR, "*.md*")):
        blog.add(os.path.splitext(os.path.basename(p))[0].lower())
    return astro, blog


def keywords(text):
    words = re.findall(r"[a-zçğıöşü0-9]+", text.lower())
    return {w for w in words if w not in STOP and len(w) > 2}


def toolable(query):
    ql = query.lower()
    for hint, kind in TOOL_HINTS.items():
        if hint in ql:
            return kind
    return None


def has_covering_page(query, astro, blog):
    """Sorguyu belirgin şekilde karşılayan bir sayfa/blog var mı? (kaba eşleşme)"""
    qk = keywords(query)
    if not qk:
        return False
    for slug in list(astro) + list(blog):
        sk = keywords(slug.replace("-", " "))
        if qk and len(qk & sk) >= max(2, len(qk) - 1):
            return True
    return False


def data_sources():
    return [os.path.basename(p) for p in sorted(glob.glob(os.path.join(DATA_DIR, "*.json")))]


def load_history(n=8):
    rows = []
    if os.path.exists(HIST):
        for line in open(HIST, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows[-n:]


def block_a(opps, astro, blog):
    """Araç/veri sayfası adayları — havuzu büyüten, sayfası olmayan toolable sorgular."""
    out = ["## BÜYÜME-A) Araç/veri sayfası adayları (havuzu BÜYÜT — tam özerk)"]
    out.append("_Toolable-niyet + henüz hedef sayfası yok. Bankalarla head-term'de "
               "dövüşmek yerine kendi verinle ÖZGÜN araç/veri sayfası kur (Astro island)._")
    cands = []
    for o in opps:
        kind = toolable(o["query"])
        if kind and not has_covering_page(o["query"], astro, blog):
            cands.append((o, kind))
    if not cands:
        out.append("- _Bu dönem net toolable-niyet fırsatı yok; blog derinleştirmeye/"
                    "yeni veri kaynağına yönel (aşağıdaki data/ listesine bak)._")
    else:
        for o, kind in cands[:8]:
            out.append(f"- `{o['query']}` → **{kind}** sayfası "
                       f"(gösterim {o['impr']}, sıra {o['pos']}, tık {o['clicks']})")
    out.append(f"- _Eldeki veri kaynakları:_ {', '.join(data_sources()) or '(yok)'}")
    return "\n".join(out)


def block_b(opps, astro, blog):
    """SERP-boşluk hedefleri — sayfa-2 sorguları, bizim sayfamız VAR → canlı SERP analizi."""
    out = ["## BÜYÜME-B) SERP-boşluk hedefleri (sayfa-2 → sayfa-1 — canlı analiz gerek)"]
    out.append("_Sayfası VAR ama 8-20. sırada (sayfa 2). Beyin: her biri için **WebFetch ile "
               "1. sayfa rakiplerini oku**, neden geride olduğunu çıkar (derinlik/şema/tazelik/"
               "başlık/H2), somut on-page diff uygula. En çok gösterimliden başla._")
    targets = [o for o in opps if 8 <= o["pos"] <= 20 and o["impr"] >= 4
               and has_covering_page(o["query"], astro, blog)]
    targets.sort(key=lambda o: (-o["impr"], o["pos"]))
    if not targets:
        # sayfası olmayan ama page-2 olanlar da fırsat (önce sayfa güçlendir/oluştur)
        alt = [o for o in opps if 8 <= o["pos"] <= 20 and o["impr"] >= 4]
        alt.sort(key=lambda o: (-o["impr"], o["pos"]))
        if alt:
            out.append("_(Eşleşen sayfa bulunamadı — bunlar için önce hedef sayfayı netleştir:)_")
            for o in alt[:5]:
                out.append(f"- `{o['query']}` — gösterim {o['impr']}, sıra {o['pos']}")
        else:
            out.append("- _Sayfa-2 bandında (8-20) fırsat yok._")
    else:
        for o in targets[:6]:
            out.append(f"- `{o['query']}` — gösterim {o['impr']}, sıra {o['pos']} "
                       f"→ 1. sayfa rakiplerini oku, boşluğu kapat")
    return "\n".join(out)


def block_c(opps):
    """Dağıtım hedefleri — dış otoriteyi açan tek yol. Beyin ready-to-paste taslak üretir."""
    out = ["## BÜYÜME-C) Dağıtım / backlink kuyruğu (dış otorite — DRAFT özerk, POST kullanıcı)"]
    out.append("_İç-link var olan otoriteyi dağıtır; YENİ otorite dış atıf/backlink ister — "
               "headless POST edilemez. Beyin: en güçlü konuya **ready-to-paste** doğal katkı "
               "taslakları üretsin (SPAM DEĞİL — gerçek soruya değerli cevap + tek bağlamsal link), "
               "`agent/state/distribution-queue.md`'ye yazsın, kullanıcı görevlerine kuyruklasın._")
    # En güçlü konu kümesi = en çok gösterim toplayan sorgu kökü
    roots = {}
    for o in opps:
        root = " ".join(list(keywords(o["query"]))[:2]) or o["query"]
        roots.setdefault(root, 0)
        roots[root] += o["impr"]
    top = sorted(roots.items(), key=lambda x: -x[1])[:3]
    venues = ("Ekşi Sözlük ilgili başlık · Reddit r/borsa veya r/Turkey · "
              "Quora TR sorusu · finans forumu (Finansbook/DonanımHaber ekonomi) · "
              "ilgili blog yorumu")
    if top:
        out.append(f"- **Öncelikli konular (gösterim ağırlıklı):** "
                   + ", ".join(f"`{r}` ({v})" for r, v in top))
    out.append(f"- **Aday mecralar:** {venues}")
    out.append("- **Linklenebilir varlık fikri:** özgün veri çalışması (ör. halka-arz getiri "
               "analizi, enflasyon-maaş erime hesabı) → gazeteci/blog atıfı çeker.")
    return "\n".join(out)


def block_d():
    """Öncü göstergeler — deneyi haftalarca 'open' bırakmamak için kısa-vade delta."""
    out = ["## BÜYÜME-D) Öncü göstergeler (deneyi HIZLI kapat — 3-7 gün delta)"]
    hist = load_history(8)
    if len(hist) < 2:
        out.append("- _Yeterli geçmiş yok (>=2 gün gerek)._")
        return "\n".join(out)
    first, last = hist[0], hist[-1]

    def delta(key, label, up_good=True):
        a, b = first.get(key), last.get(key)
        if a is None or b is None:
            return f"- {label}: veri yok"
        d = round(b - a, 2)
        arrow = "→ düz"
        if d > 0:
            arrow = "📈 artış" if up_good else "📉 (istenmeyen artış)"
        elif d < 0:
            arrow = "📉 düşüş" if up_good else "📈 (iyi düşüş)"
        return f"- {label}: {a} → {b} ({'+' if d>=0 else ''}{d}) {arrow}"

    span = f"{first.get('date','?')} → {last.get('date','?')} ({len(hist)} gün)"
    out.append(f"_Pencere: {span}. Bunlar tıklamadan ÖNCE kımıldar — deneyin yönünü erken gösterir._")
    out.append(delta("gsc_impr_week", "GSC gösterim/hafta (havuz büyüyor mu)", True))
    out.append(delta("gsc_best_pos", "GSC en iyi pozisyon (küçük=iyi)", False))
    out.append(delta("gsc_opportunities", "Fırsat sorgusu sayısı", True))
    out.append(delta("organic_week", "Organik erişim/hafta", True))
    out.append(delta("direct_share", "Direct payı (küçük=iyi)", False))
    out.append(delta("yt_subs", "YouTube abone", True))
    out.append("- **Kural:** gösterim/pozisyon 5-7 günde kımıldadıysa deneyi `won/lost` "
               "kapat; tıklamayı haftalarca bekleme.")
    return "\n".join(out)


def main():
    opps = parse_opportunities()
    astro, blog = existing_page_slugs()
    print("# 🚀 BÜYÜME MOTORU — fırsat blokları (growth-engine.py, token'sız)")
    print("_Darboğaz: otorite + dağıtım + gösterim havuzu. Aşağıdaki 4 blok gece kararların için._\n")
    print(block_a(opps, astro, blog)); print()
    print(block_b(opps, astro, blog)); print()
    print(block_c(opps)); print()
    print(block_d())


if __name__ == "__main__":
    main()
