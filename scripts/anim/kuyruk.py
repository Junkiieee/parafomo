#!/usr/bin/env python3
"""ParaFOMO onaylı yayın kuyruğu + stil deneyi (Kaan kararı 2026-10-31).

Akış: gece `uret` takvimden (agent/plan/icerik-takvimi.json) 2 konu seçer, her birine deneydeki
sıradaki stili verir, senaryo + animasyon üretir ve kuyruğa "bekliyor" yazar. Sabah raporunda Kaan
görür; `onayla` ile onaylananlar sırayla yayın saatlerinde (`yayinla`, cron) çıkar. Hiçbir şey
onaysız yayınlanmaz. `rapor` stillerin karnesini çıkarır (deney aşama 1: eşit dağılım).

  kuyruk.py uret [--adet 2] [--dry]
  kuyruk.py liste
  kuyruk.py onayla <slug|no> ... [--tarih YYYY-MM-DD]   (tarih: o günden önce yayınlanmaz)
  kuyruk.py reddet <slug|no> ...
  kuyruk.py ekle <slug> --title "…" [--style defter] [--format ekonomi_defteri] [--tarih …]
                                      (elle yapılmış bölüm: short-<slug>.json + "file" mp4 hazır olmalı)
  kuyruk.py yayinla                   (cron: onaylı sıradakini yayınlar)
  kuyruk.py begen <no> [--not "…"]   kuyruk.py begenme <no> [--not "…"]   (Kaan'ın yayın sonrası oyu)
  kuyruk.py yayinla --no <no>         (olay videosu: onaydan hemen sonra)
  kuyruk.py rapor [--json]
"""
import argparse, datetime as dt, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable
DATA = "/root/parafomo-data/onay"
KUYRUK = os.path.join(DATA, "kuyruk.json")
TAKVIM = os.path.join(ROOT, "agent", "plan", "icerik-takvimi.json")
SCEN_DIR = os.path.join(ROOT, "public", "social", "scenarios")
# Deney (Kaan 2026-10-31 "diğer tekniklerle de deneyelim"): asıl eksen TEKNİK, renk/doku ikincil.
#   iso    = kodla izometrik infografik (scripts/anim) — içinde 5 kaplama döner (STILLER)
#   klasik = eski viral motor: stok/arşiv görsel + Manim veri kartı (shorts-build-v4); kanalın 1000+ izlenen
#            videolarının çoğu bu motordan → taban çizgisi
#   defter = Ekonomi Defteri (elle, haftalık; `ekle` ile girer)
# Kaan 2026-10-31 (2. karar): "eski sistemde stillerle video üretimi yapılmasın, yenileri deneyelim" → klasik ÇIKTI.
#   Gece hattı yalnız yeni motor: izometrik, 8 kaplamanın hepsi döner. Kaan her yayında beğendi/beğenmedi der
#   (`begen` / `begenme`) → karne izlenme verisinin yanında Kaan'ın oyunu da gösterir.
TEKNIKLER = ["iso"]
STILLER = ["iso", "paper", "riso", "blueprint", "cutpaper", "ink", "pixel", "sketch"]
# Kaan 2026-10-31 katalog oyu: "izometrik kesik kağıt ile ekonomi defterini beğendim" → her gece 1. video FAVORİ
# kaplamayla, 2. video kalan kaplamalardan sırayla (keşif; Kaan'ın oyuyla elenir/eklenir).
FAVORI = ["cutpaper"]
SES = "tr-TR-Chirp3-HD-Orus"
FORMATLAR = ["shock_number", "myth", "single_concept"]


def now():
    return dt.datetime.now(dt.timezone.utc)


def bugun_tr():
    return (now() + dt.timedelta(hours=3)).date().isoformat()   # TSİ = UTC+3 (yaz saati yok)


def load():
    os.makedirs(DATA, exist_ok=True)
    if os.path.exists(KUYRUK):
        return json.load(open(KUYRUK, encoding="utf-8"))
    return {"items": [], "used_topics": []}


def save(q):
    tmp = KUYRUK + ".tmp"
    json.dump(q, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, KUYRUK)


def find(q, keys):
    out = []
    for k in keys:
        for i, it in enumerate(q["items"]):
            if it["slug"] == k or str(it.get("no")) == str(k):
                out.append(it)
    return out


# ---------------------------------------------------------------- üretim
def week_for(day):
    weeks = json.load(open(TAKVIM, encoding="utf-8"))["weeks"]
    cur = None
    for w in weeks:
        if w["start"] <= day.isoformat():
            cur = w
    return cur or weeks[0]


def pick_topic(q, day):
    w = week_for(day)
    for t in w["topics"]:
        if t not in q["used_topics"]:
            return t, w
    # konular bittiyse tema + farklı açı (LLM); tekrar etmesin diye kullanılanları da söyle
    son = [it["topic"] for it in q["items"][-12:]]
    return f"{w['theme']} — daha önce işlenmeyen yeni bir açı (işlenenler: {'; '.join(son)})", w


def teknik_of(it):
    return it.get("teknik") or ("defter" if it.get("style") == "defter" else "klasik" if it.get("style") == "klasik" else "iso")


def pick_style(q, taken, k=0):
    if k == 0 and FAVORI:
        return FAVORI[(len([1 for it in q["items"] if it.get("style") in FAVORI])) % len(FAVORI)]
    sayac = {s: 0 for s in STILLER if s not in FAVORI}
    for it in q["items"]:
        if it.get("style") in sayac and it["status"] != "reddedildi":
            sayac[it["style"]] += 1
    aday = sorted(sayac, key=lambda s: (s in taken, sayac[s], STILLER.index(s)))
    return aday[0]


def run(cmd, env=None, **kw):
    e = dict(os.environ); e.update(env or {})
    return subprocess.run(cmd, cwd=ROOT, env=e, text=True, capture_output=True, **kw)


OTO = "/root/parafomo-data/onay/oto.json"   # {"bitis": "YYYY-MM-DD"} — o güne kadar (dahil) onay beklenmez


def oto_aktif():
    """Kaan 2026-11-01: 'bir hafta boyunca otomatik paylaşımlar yapılsın ardından konuşalım' → 8 Kasım'a kadar
    üretilen her video kendiliğinden onaylı (yayın saatleri aynı). Bitişten sonra otomatik olarak onay moduna döner."""
    try:
        return bugun_tr() <= json.load(open(OTO, encoding="utf-8"))["bitis"]
    except Exception:
        return False


def uret(a):
    q = load()
    day = now().date()
    taken = {it["style"] for it in q["items"] if it.get("created", "")[:10] == day.isoformat()}
    n_done = 0
    for k in range(a.adet):
        topic, w = pick_topic(q, day)
        teknik = TEKNIKLER[(day.toordinal() + k) % len(TEKNIKLER)]   # her gece biri iso biri klasik, sıra günlük döner
        style = pick_style(q, taken, k) if teknik == "iso" else "klasik"
        fmt = FORMATLAR[(day.toordinal() * a.adet + k) % len(FORMATLAR)]
        print(f"[üret] {k+1}/{a.adet} konu: {topic[:80]} | format {fmt} | teknik {teknik} | stil {style}")
        if a.dry:   # kaydetmeden: sıradaki konu/stil nasıl dağılırdı
            taken.add(style); q["used_topics"].append(topic); continue
        r = run([PY, os.path.join(ROOT, "scripts", "viral-script.py"), "--format", fmt, "--topic", topic], timeout=900)
        scen = (r.stdout.strip().splitlines() or [""])[-1]
        if r.returncode != 0 or not os.path.exists(scen):
            print("[üret] senaryo üretilemedi:", (r.stderr or r.stdout)[-300:]); continue
        slug = json.load(open(scen, encoding="utf-8"))["slug"]
        if teknik == "klasik":
            run([PY, os.path.join(ROOT, "scripts", "manimify.py"), scen, "--hybrid"], timeout=1800)
            r = run(["nice", "-n", "19", PY, os.path.join(ROOT, "scripts", "shorts-build-v4.py"), slug, "--scenario", scen,
                     "--engine", "google", "--voice", SES], timeout=3600)
        else:
            r = run([PY, os.path.join(ROOT, "scripts", "anim", "anim_short.py"), "--scenario", scen],
                    env={"ANIM_SKIN": style}, timeout=3600)
        mp4 = os.path.join(ROOT, "public", "social", f"short-{slug}.mp4")
        if r.returncode != 0 or not os.path.exists(mp4):
            print("[üret] render başarısız:", (r.stderr or "")[-400:]); continue
        meta = json.load(open(os.path.join(ROOT, "public", "social", f"short-{slug}.json"), encoding="utf-8"))
        no = max([it.get("no", 0) for it in q["items"]] + [0]) + 1
        q["items"].append({"no": no, "slug": slug, "title": meta.get("title", slug), "topic": topic, "week": w["start"],
                           "format": fmt, "teknik": teknik, "style": style, "mp4": mp4, "scenario": scen,
                           "created": now().isoformat(timespec="seconds"), "status": "bekliyor"})
        if oto_aktif():
            q["items"][-1].update({"status": "onaylandi", "approved": now().isoformat(timespec="seconds"), "oto": True})
        if topic in w["topics"]:
            q["used_topics"].append(topic)
        taken.add(style); n_done += 1
        save(q)
        print(f"[üret] ✅ #{no} {slug} ({style})")
    return 0 if n_done or a.dry else 2


# ---------------------------------------------------------------- onay
def liste(a):
    q = load()
    for it in q["items"]:
        if a.hepsi or it["status"] in ("bekliyor", "onaylandi") or (it["status"] == "yayinlandi" and not it.get("kaan")):
            tar = f" [{it['yayin_tarihi']}]" if it.get("yayin_tarihi") else ""
            tar += {"+": " 👍", "-": " 👎"}.get(it.get("kaan"), "")
            print(f"#{it['no']:<3} {it['status']:<11} {teknik_of(it):<7} {it['style']:<9} {it['format']:<14} {it['slug']}{tar}  —  {it['title'][:70]}")
    return 0


def onayla(a):
    q = load()
    for it in find(q, a.ids):
        if it["status"] in ("bekliyor", "reddedildi"):
            it["status"] = "onaylandi"; it["approved"] = now().isoformat(timespec="seconds")
            if a.tarih:
                it["yayin_tarihi"] = a.tarih
            print("onaylandı:", it["no"], it["slug"], a.tarih or "")
        elif it["status"] == "onaylandi" and a.tarih:   # onaylı bölümün yayın gününü kaydır
            it["yayin_tarihi"] = a.tarih
            print("tarih değişti:", it["no"], it["slug"], a.tarih)
    save(q); return 0


def ekle(a):
    """Elle yapılmış bölümü (Ekonomi Defteri) kuyruğa koyar; stil deneyine sayılmaz (STILLER dışı)."""
    q = load()
    if find(q, [a.slug]):
        print("zaten kuyrukta:", a.slug); return 1
    mp = os.path.join(ROOT, "public", "social", f"short-{a.slug}.json")
    mp4 = json.load(open(mp, encoding="utf-8")).get("file", "") if os.path.exists(mp) else ""
    if not (mp4 and os.path.exists(mp4)):
        print("short-<slug>.json ya da içindeki mp4 yok:", mp); return 2
    no = max([it["no"] for it in q["items"]] or [0]) + 1
    it = {"no": no, "slug": a.slug, "title": a.title, "topic": a.title, "week": "", "format": a.format,
          "style": a.style, "mp4": mp4, "scenario": "", "created": now().isoformat(timespec="seconds"),
          "status": "bekliyor"}
    if a.tarih:
        it["yayin_tarihi"] = a.tarih
    q["items"].append(it); save(q)
    print("eklendi:", no, a.slug)
    if a.onayla or oto_aktif():
        a.ids = [a.slug]; return onayla(a)
    return 0


def oyla(a, deger):
    q = load()
    for it in find(q, a.ids):
        it["kaan"] = deger
        if a.not_:
            it["kaan_not"] = a.not_
        print(("👍" if deger == "+" else "👎"), it["no"], it["slug"], it.get("style"))
    save(q); return 0


def reddet(a):
    q = load()
    for it in find(q, a.ids):
        if it["status"] in ("bekliyor", "onaylandi"):
            it["status"] = "reddedildi"; print("reddedildi:", it["no"], it["slug"])
    save(q); return 0


def yayinla(a):
    q = load()
    gun = bugun_tr()
    sira = [it for it in q["items"] if it["status"] == "onaylandi" and it.get("yayin_tarihi", "") <= gun]
    if a.no:   # belirli bir videoyu hemen yayınla (olay videosu: Kaan onaylayınca bekletmeden)
        sira = [it for it in q["items"] if str(it.get("no")) == str(a.no) and it["status"] == "onaylandi"]
    if not a.dry and not a.no:   # zamanlanmış uzun bölüm yayına girdiyse: liste + yorum (Kaan onaylı yüklenmişti)
        r = run([PY, "scripts/longform/lf_upload.py", "tamamla"], env={"ONAYLI_YAYIN": "1"}, timeout=600)
        if r.stdout.strip():
            print(r.stdout[-400:])
    if not sira:
        print("[yayın] bugün çıkacak onaylı video yok"); return 0
    # tarihi bugün olan (seri bölümü) önce; sonra onay sırası
    it = sorted(sira, key=lambda x: (x.get("yayin_tarihi", "") != gun, x.get("approved", "")))[0]
    slug = it["slug"]
    env = {"ONAYLI_YAYIN": "1"}   # PUBLISH_PAUSED bayrağı yalnız onaylı yayına izin verir
    if a.dry:
        print("[yayın] (dry) sıradaki:", slug); return 0
    r = run([PY, "scripts/youtube-upload.py", slug, "--privacy", "public"], env=env, timeout=1800)
    print(r.stdout[-800:], r.stderr[-400:])
    meta_p = os.path.join(ROOT, "public", "social", f"short-{slug}.json")
    meta = json.load(open(meta_p, encoding="utf-8"))
    if not meta.get("video_id"):
        it["status"] = "hata"; it["error"] = "youtube yüklemesi başarısız"; save(q); return 2
    run([PY, "scripts/youtube-extras.py", slug, "--format", it["format"]], env=env, timeout=600)
    r = run([PY, "scripts/instagram-reel.py", slug], env=env, timeout=1800); print(r.stdout[-400:])
    r = run([PY, "scripts/facebook-reel.py", slug], env=env, timeout=1800); print(r.stdout[-300:])
    meta = json.load(open(meta_p, encoding="utf-8"))
    it.update({"status": "yayinlandi", "published": now().isoformat(timespec="seconds"),
               "youtube_id": meta["video_id"],
               "ig_permalink": meta.get("ig_reel_permalink", ""), "ig_media_id": meta.get("ig_reel_id", "")})
    save(q)
    print(f"[yayın] ✅ {slug} → https://youtu.be/{it['youtube_id']}  {it['ig_permalink']}")
    return 0


# ---------------------------------------------------------------- ölçüm
def yt_stats(vids):
    sys.path.insert(0, os.path.join(ROOT, "scripts", "learn"))
    import lib
    from googleapiclient.discovery import build
    creds = lib.youtube_credentials(["https://www.googleapis.com/auth/youtube.readonly",
                                     "https://www.googleapis.com/auth/yt-analytics.readonly"])
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    ya = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    out = {}
    for i in range(0, len(vids), 50):
        b = vids[i:i + 50]
        for v in yt.videos().list(part="statistics", id=",".join(b)).execute().get("items", []):
            s = v["statistics"]
            out[v["id"]] = {"views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0))}
        try:
            rep = ya.reports().query(ids="channel==MINE", startDate="2026-10-01", endDate=now().date().isoformat(),
                                     dimensions="video", metrics="averageViewPercentage,engagedViews,subscribersGained",
                                     filters="video==" + ",".join(b)).execute()
        except Exception:   # engagedViews desteklenmezse onsuz
            rep = ya.reports().query(ids="channel==MINE", startDate="2026-10-01", endDate=now().date().isoformat(),
                                     dimensions="video", metrics="averageViewPercentage,subscribersGained",
                                     filters="video==" + ",".join(b)).execute()
        h = [c["name"] for c in rep.get("columnHeaders", [])]
        for row in rep.get("rows", []):
            d = dict(zip(h, row)); out.setdefault(d["video"], {}).update({k: d[k] for k in h if k != "video"})
    return out


def ig_stats(ids):
    env = dict(l.strip().split("=", 1) for l in open(os.path.expanduser("~/.config/parafomo/instagram.env"))
               if "=" in l and not l.startswith("#"))
    import urllib.request
    out = {}
    for mid in ids:
        try:
            r = json.load(urllib.request.urlopen(
                f"https://graph.facebook.com/v21.0/{mid}/insights?metric=reach,views,saved,shares&access_token={env['IG_PAGE_TOKEN']}"))
            out[mid] = {m["name"]: m["values"][0]["value"] for m in r["data"]}
        except Exception:
            pass
    return out


def median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


def rapor(a):
    q = load()
    pub = [it for it in q["items"] if it["status"] == "yayinlandi" and it.get("youtube_id")]
    if not pub:
        print("henüz yayınlanmış deney videosu yok"); return 0
    ys = yt_stats([it["youtube_id"] for it in pub])
    igs = ig_stats([it["ig_media_id"] for it in pub if it.get("ig_media_id")])
    rows = []
    for it in pub:
        y = ys.get(it["youtube_id"], {}); g = igs.get(it.get("ig_media_id"), {})
        age = (now() - dt.datetime.fromisoformat(it["published"])).total_seconds() / 86400
        rows.append({"no": it["no"], "slug": it["slug"], "teknik": teknik_of(it), "style": it["style"], "format": it["format"], "age_d": round(age, 1),
                     "views": y.get("views", 0), "avp": y.get("averageViewPercentage"), "engaged": y.get("engagedViews"),
                     "subs": y.get("subscribersGained", 0), "ig_reach": g.get("reach"), "ig_saved": g.get("saved"),
                     "kaan": it.get("kaan", "")})
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1)); return 0
    print("VİDEO BAZINDA (yaş gün · YT izlenme · ort. izleme % · abone · IG erişim)")
    for r in sorted(rows, key=lambda r: -r["no"]):
        print(f"  #{r['no']:<3} {r['teknik']:<7} {r['style']:<9} {r['age_d']:>4}g  {r['views']:>6}  {r['avp'] or 0:>5.1f}%  +{r['subs']}  IG {r['ig_reach'] or '-'}  {({'+': '👍', '-': '👎'}).get(r['kaan'], '·')}  {r['slug'][:45]}")
    def karne(baslik, key, vals):
        print(f"\n{baslik} (yalnız ≥7 günlük videolar; ortanca)")
        for s in vals:
            rr = [r for r in rows if r[key] == s and r["age_d"] >= 7]
            if not rr:
                n_all = sum(1 for r in rows if r[key] == s)
                print(f"  {s:<9} n=0 (yayında {n_all}, 7 günü dolan yok)"); continue
            v = median([r["views"] for r in rr]); p = median([r["avp"] or 0 for r in rr])
            sub = sum(r["subs"] for r in rr); tv = sum(r["views"] for r in rr)
            oy = [r for r in rows if r[key] == s and r["kaan"]]
            ky = f"  Kaan {sum(r['kaan'] == '+' for r in oy)}👍/{sum(r['kaan'] == '-' for r in oy)}👎" if oy else ""
            print(f"  {s:<9} n={len(rr)}  izlenme ortanca {v:>7.0f}  izleme %{p:>5.1f}  abone/1000 {1000*sub/max(tv,1):.1f}{ky}")
    karne("TEKNİK KARNESİ", "teknik", TEKNIKLER + ["defter", "klasik"])
    rows = [r for r in rows if r["teknik"] == "iso"]
    karne("İZOMETRİK İÇİNDE KAPLAMA", "style", STILLER)
    return 0


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("uret"); p.add_argument("--adet", type=int, default=2); p.add_argument("--dry", action="store_true"); p.set_defaults(f=uret)
    p = sp.add_parser("liste"); p.add_argument("--hepsi", action="store_true"); p.set_defaults(f=liste)
    p = sp.add_parser("onayla"); p.add_argument("ids", nargs="+"); p.add_argument("--tarih", default=""); p.set_defaults(f=onayla)
    p = sp.add_parser("ekle"); p.add_argument("slug"); p.add_argument("--title", required=True)
    p.add_argument("--style", default="defter"); p.add_argument("--format", default="ekonomi_defteri")
    p.add_argument("--tarih", default=""); p.add_argument("--onayla", action="store_true"); p.set_defaults(f=ekle)
    p = sp.add_parser("reddet"); p.add_argument("ids", nargs="+"); p.set_defaults(f=reddet)
    for ad, deger in (("begen", "+"), ("begenme", "-")):   # Kaan'ın yayın sonrası oyu
        p = sp.add_parser(ad); p.add_argument("ids", nargs="+"); p.add_argument("--not", dest="not_", default="")
        p.set_defaults(f=lambda a, d=deger: oyla(a, d))
    p = sp.add_parser("yayinla"); p.add_argument("--dry", action="store_true"); p.add_argument("--no", default="")
    p.set_defaults(f=yayinla)
    p = sp.add_parser("rapor"); p.add_argument("--json", action="store_true"); p.set_defaults(f=rapor)
    a = ap.parse_args()
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
