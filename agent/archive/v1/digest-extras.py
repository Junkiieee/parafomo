#!/usr/bin/env python3
"""
ParaFOMO Büyüme Ajanı — digest'e HAM VERİ ekleri (token'sız, LLM yok).

build-digest.sh bunu çağırır; çıktısı digest.md'ye eklenir. Amaç: ajana
yüzeysel özet değil, üzerinde MUHAKEME edebileceği ham veri vermek:
  - GSC ham sorgular (pozisyon/tıklama/gösterim)
  - Öğrenme motoru detayı (format/ses/saat/konu sıralaması + skor)
  - YouTube video performansı (retention + izlenme, başlık/slug ile)
  - Blog envanteri (başlık · tarih · kategori · etiketler)

Her bölüm izole try/except: biri patlarsa digest bozulmaz.
"""
import os, re, json, glob
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = os.path.join(ROOT, "data", "learning")
MEM = os.path.join(ROOT, "agent", "memory")


def out(s=""):
    print(s)


def sec_gsc_queries():
    try:
        d = json.load(open(os.path.join(L, "web-queries.json"), encoding="utf-8"))
        rows = d.get("top", [])[:35]
        if not rows:
            return
        out("## HAM: GSC arama sorguları (Google seni gösteriyor — sıralamayı çekmek fırsat)")
        out("| Sorgu | Gösterim | Tıklama | Ort. Pozisyon |")
        out("|---|---|---|---|")
        for r in rows:
            out(f"| {r.get('query','')} | {r.get('impressions',0)} | {r.get('clicks',0)} | {r.get('position',0):.1f} |")
        out()
        out("_Yorum ipucu: yüksek gösterim + 0 tıklama + pozisyon 10-30 = en yüksek kaldıraç (hedefli sayfa/başlık/iç-link ile ilk sayfaya çek)._")
        out()
    except Exception as e:
        out(f"_(GSC sorguları alınamadı: {e})_\n")


def _rank_block(node, label):
    if not isinstance(node, dict):
        return
    pol = node.get("policy", "?")
    nxt = node.get("next_pick")
    out(f"**{label}** — politika: `{pol}`{' · seçim: `%s`' % nxt if nxt else ''}")
    for a in (node.get("ranking") or [])[:5]:
        out(f"  - {a.get('arm','')}: skor={a.get('score',0):.1f} (n={a.get('n',0)})")
    out()


def sec_learning():
    try:
        d = json.load(open(os.path.join(L, "winners.json"), encoding="utf-8"))
        out("## HAM: Öğrenme motoru detayı (neyin tuttuğu — kanıt + skor)")
        out(f"_Pencere: {d.get('window_days')} gün · min örnek: {d.get('min_samples')} · sinyaller: {d.get('signals')}_\n")
        sh = d.get("shorts", {}); vi = d.get("viral", {})
        _rank_block(sh.get("voice"), "Shorts · Ses")
        _rank_block(sh.get("engine"), "Shorts · Motor")
        _rank_block(vi.get("format"), "Viral · Format")
        _rank_block(vi.get("slot"), "Viral · Yayın saati")
        tp = d.get("topics")
        if tp:
            out(f"**Konular:** {json.dumps(tp, ensure_ascii=False)[:400]}")
        nt = d.get("notes")
        if nt:
            out(f"**Notlar:** {json.dumps(nt, ensure_ascii=False)[:300]}")
        out()
    except Exception as e:
        out(f"_(Öğrenme detayı alınamadı: {e})_\n")


def sec_youtube():
    try:
        # id -> slug (ledger)
        slug = {}
        led = os.path.join(L, "content-ledger.jsonl")
        if os.path.exists(led):
            for line in open(led, encoding="utf-8"):
                try:
                    o = json.loads(line)
                    slug[o.get("id")] = o.get("slug") or ""
                except Exception:
                    pass
        # id -> son metrik (metrics.jsonl, son kayıt kazanır)
        latest = OrderedDict()
        mf = os.path.join(L, "metrics.jsonl")
        if not os.path.exists(mf):
            return
        for line in open(mf, encoding="utf-8"):
            try:
                o = json.loads(line)
                if o.get("channel") == "youtube":
                    latest[o["id"]] = o.get("metrics", {})
            except Exception:
                pass
        if not latest:
            return
        items = [(vid, m, slug.get(vid, "")) for vid, m in latest.items()]
        items.sort(key=lambda x: x[1].get("views", 0), reverse=True)
        out("## HAM: YouTube video performansı (retention = asıl kalite sinyali)")
        out("| Video (slug) | İzlenme | Retention % | Ort.sn | Beğeni | Yorum |")
        out("|---|---|---|---|---|---|")
        for vid, m, sl in items[:25]:
            name = sl or vid.replace("youtube:", "")
            out(f"| {name[:44]} | {m.get('views',0)} | {m.get('avg_view_pct',0):.0f} | {m.get('avg_view_sec',0)} | {m.get('likes',0)} | {m.get('comments',0)} |")
        out()
        out("_Yorum ipucu: yüksek retention + düşük izlenme = kanca/başlık/kapak sorunu (dağıtım). Düşük retention = içerik/tempo sorunu._")
        out()
    except Exception as e:
        out(f"_(YouTube performansı alınamadı: {e})_\n")


def sec_blog():
    try:
        files = sorted(glob.glob(os.path.join(ROOT, "src", "content", "blog", "*.md*")))
        if not files:
            return
        out(f"## HAM: Blog envanteri ({len(files)} yazı — iç-link/konu kümesi/boşluk analizi için)")
        out("| Yazı | Tarih | Kategori | Etiketler |")
        out("|---|---|---|---|")
        for f in files:
            try:
                txt = open(f, encoding="utf-8").read()[:1200]
                title = (re.search(r'^title:\s*"?(.*?)"?\s*$', txt, re.M) or [None, ""])[1]
                date = (re.search(r'^pubDate:\s*(.*?)\s*$', txt, re.M) or [None, ""])[1]
                cat = (re.search(r'^category:\s*"?(.*?)"?\s*$', txt, re.M) or [None, ""])[1]
                tags = (re.search(r'^tags:\s*\[(.*?)\]', txt, re.M) or [None, ""])[1]
                slug = os.path.basename(f).rsplit(".", 1)[0]
                out(f"| {title[:52] or slug} | {date} | {cat} | {tags[:60]} |")
            except Exception:
                pass
        out()
    except Exception as e:
        out(f"_(Blog envanteri alınamadı: {e})_\n")


def sec_learnings():
    try:
        p = os.path.join(MEM, "learnings.md")
        if not os.path.exists(p):
            return
        lines = [l.rstrip() for l in open(p, encoding="utf-8") if l.strip() and l.strip().startswith("-")]
        if not lines:
            return
        out("## HAFIZA: Kalıcı öğrenimler (kararlarını BUNA göre ver — kanıtlıyı ikiye katla, kaybedeni tekrarlama)")
        for l in lines[-70:]:
            out(l)
        out()
    except Exception as e:
        out(f"_(öğrenimler alınamadı: {e})_\n")


def sec_experiments():
    try:
        p = os.path.join(MEM, "experiments.jsonl")
        if not os.path.exists(p):
            return
        rows = []
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
        if not rows:
            return
        openr = [r for r in rows if r.get("status") == "open"]
        closed = [r for r in rows if r.get("status") != "open"]
        out("## HAFIZA: AÇIK deneyler (Adım 0'da SONUÇLARINI ÖLÇ ve kapat: won/lost/inconclusive)")
        if openr:
            for r in openr:
                out(f"- `{r['id']}` [{r.get('channel','')}] {r.get('action','')} → izlenen metrik: **{r.get('metric','')}** (baseline: {r.get('baseline','')}, açılış: {r.get('date','')})")
        else:
            out("(açık deney yok)")
        out()
        if closed:
            out("## HAFIZA: Kapanmış deneyler (son 25 — ne tuttu / ne tutmadı, PATERN ara)")
            out("| id | kanal | eylem | sonuç | öğrenim |")
            out("|---|---|---|---|---|")
            for r in closed[-25:]:
                out(f"| {r.get('id','')} | {r.get('channel','')} | {r.get('action','')[:32]} | {r.get('status','')}: {r.get('outcome','')[:38]} | {r.get('learning','')[:40]} |")
            out()
    except Exception as e:
        out(f"_(deneyler alınamadı: {e})_\n")


def sec_kpi_trend():
    try:
        p = os.path.join(MEM, "kpi-history.jsonl")
        if not os.path.exists(p):
            return
        rows = []
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
        if not rows:
            return
        rows = rows[-14:]
        out("## KPI TAKİP: kuzey yıldızı metrikleri zaman içinde (HAREKETİ izle, hamlelerinle ilişkilendir)")
        out("| Tarih | Organik/hf | Direct% | GSC tık | GSC gös | CTR% | En iyi poz | YT izlenme | YT abone |")
        out("|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            out(f"| {r.get('date','')} | {r.get('organic_week',0)} | {r.get('direct_share',0)} | {r.get('gsc_clicks_week',0)} | {r.get('gsc_impr_week',0)} | {r.get('gsc_ctr',0)} | {r.get('gsc_best_pos',0)} | {r.get('yt_views',0)} | {r.get('yt_subs',0)} |")
        out()
        if len(rows) >= 2:
            a, b = rows[0], rows[-1]
            out(f"_Değişim ({a.get('date')} → {b.get('date')}): organik {a.get('organic_week',0)}→{b.get('organic_week',0)} · "
                f"GSC gösterim {a.get('gsc_impr_week',0)}→{b.get('gsc_impr_week',0)} · "
                f"GSC tıklama {a.get('gsc_clicks_week',0)}→{b.get('gsc_clicks_week',0)} · "
                f"YT izlenme {a.get('yt_views',0)}→{b.get('yt_views',0)}. Hangi hamle hangi kımıldamayı yaptı, Adım 0'da bağla._")
        out()
    except Exception as e:
        out(f"_(KPI takip alınamadı: {e})_\n")


if __name__ == "__main__":
    # KPI trend + hafıza önce (karar öncesi görülsün), sonra ham veri.
    sec_kpi_trend()
    sec_learnings()
    sec_experiments()
    sec_gsc_queries()
    sec_learning()
    sec_youtube()
    sec_blog()
