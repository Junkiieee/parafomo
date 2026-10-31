#!/usr/bin/env python3
"""ParaFOMO onaylı yayın kuyruğu + stil deneyi (Kaan kararı 2026-10-31).

Akış: gece `uret` takvimden (agent/plan/icerik-takvimi.json) 2 konu seçer, her birine deneydeki
sıradaki stili verir, senaryo + animasyon üretir ve kuyruğa "bekliyor" yazar. Sabah raporunda Kaan
görür; `onayla` ile onaylananlar sırayla yayın saatlerinde (`yayinla`, cron) çıkar. Hiçbir şey
onaysız yayınlanmaz. `rapor` stillerin karnesini çıkarır (deney aşama 1: eşit dağılım).

  kuyruk.py uret [--adet 2] [--dry]
  kuyruk.py liste
  kuyruk.py onayla <slug|no> ...      kuyruk.py reddet <slug|no> ...
  kuyruk.py yayinla                   (cron: onaylı sıradakini yayınlar)
  kuyruk.py rapor [--json]
"""
import argparse, datetime as dt, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable
DATA = "/root/parafomo-data/onay"
KUYRUK = os.path.join(DATA, "kuyruk.json")
TAKVIM = os.path.join(ROOT, "agent", "plan", "icerik-takvimi.json")
SCEN_DIR = os.path.join(ROOT, "public", "social", "scenarios")
# Deney aşama 1: otomatik hatta yarışan stiller (karakterli "Ekonomi Defteri" haftalık seride, V4 gelince eklenir)
STILLER = ["iso", "paper", "riso", "blueprint", "cutpaper"]
FORMATLAR = ["shock_number", "myth", "single_concept"]


def now():
    return dt.datetime.now(dt.timezone.utc)


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


def pick_style(q, taken):
    sayac = {s: 0 for s in STILLER}
    for it in q["items"]:
        if it.get("style") in sayac and it["status"] != "reddedildi":
            sayac[it["style"]] += 1
    aday = sorted(STILLER, key=lambda s: (s in taken, sayac[s], STILLER.index(s)))
    return aday[0]


def run(cmd, env=None, **kw):
    e = dict(os.environ); e.update(env or {})
    return subprocess.run(cmd, cwd=ROOT, env=e, text=True, capture_output=True, **kw)


def uret(a):
    q = load()
    day = now().date()
    taken = {it["style"] for it in q["items"] if it.get("created", "")[:10] == day.isoformat()}
    n_done = 0
    for k in range(a.adet):
        topic, w = pick_topic(q, day)
        style = pick_style(q, taken)
        fmt = FORMATLAR[(day.toordinal() * a.adet + k) % len(FORMATLAR)]
        print(f"[üret] {k+1}/{a.adet} konu: {topic[:80]} | format {fmt} | stil {style}")
        if a.dry:
            taken.add(style); continue
        r = run([PY, os.path.join(ROOT, "scripts", "viral-script.py"), "--format", fmt, "--topic", topic], timeout=900)
        scen = (r.stdout.strip().splitlines() or [""])[-1]
        if r.returncode != 0 or not os.path.exists(scen):
            print("[üret] senaryo üretilemedi:", (r.stderr or r.stdout)[-300:]); continue
        slug = json.load(open(scen, encoding="utf-8"))["slug"]
        r = run([PY, os.path.join(ROOT, "scripts", "anim", "anim_short.py"), "--scenario", scen],
                env={"ANIM_SKIN": style}, timeout=3600)
        mp4 = os.path.join(ROOT, "public", "social", f"short-{slug}.mp4")
        if r.returncode != 0 or not os.path.exists(mp4):
            print("[üret] render başarısız:", (r.stderr or "")[-400:]); continue
        meta = json.load(open(os.path.join(ROOT, "public", "social", f"short-{slug}.json"), encoding="utf-8"))
        no = max([it.get("no", 0) for it in q["items"]] + [0]) + 1
        q["items"].append({"no": no, "slug": slug, "title": meta.get("title", slug), "topic": topic, "week": w["start"],
                           "format": fmt, "style": style, "mp4": mp4, "scenario": scen,
                           "created": now().isoformat(timespec="seconds"), "status": "bekliyor"})
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
        if a.hepsi or it["status"] in ("bekliyor", "onaylandi"):
            print(f"#{it['no']:<3} {it['status']:<11} {it['style']:<9} {it['format']:<14} {it['slug']}  —  {it['title'][:70]}")
    return 0


def onayla(a):
    q = load()
    for it in find(q, a.ids):
        if it["status"] in ("bekliyor", "reddedildi"):
            it["status"] = "onaylandi"; it["approved"] = now().isoformat(timespec="seconds")
            print("onaylandı:", it["no"], it["slug"])
    save(q); return 0


def reddet(a):
    q = load()
    for it in find(q, a.ids):
        if it["status"] in ("bekliyor", "onaylandi"):
            it["status"] = "reddedildi"; print("reddedildi:", it["no"], it["slug"])
    save(q); return 0


def yayinla(a):
    q = load()
    sira = [it for it in q["items"] if it["status"] == "onaylandi"]
    if not sira:
        print("[yayın] onaylı video yok"); return 0
    it = sorted(sira, key=lambda x: x.get("approved", ""))[0]
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
        rows.append({"no": it["no"], "slug": it["slug"], "style": it["style"], "format": it["format"], "age_d": round(age, 1),
                     "views": y.get("views", 0), "avp": y.get("averageViewPercentage"), "engaged": y.get("engagedViews"),
                     "subs": y.get("subscribersGained", 0), "ig_reach": g.get("reach"), "ig_saved": g.get("saved")})
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1)); return 0
    print("VİDEO BAZINDA (yaş gün · YT izlenme · ort. izleme % · abone · IG erişim)")
    for r in sorted(rows, key=lambda r: -r["no"]):
        print(f"  #{r['no']:<3} {r['style']:<9} {r['age_d']:>4}g  {r['views']:>6}  {r['avp'] or 0:>5.1f}%  +{r['subs']}  IG {r['ig_reach'] or '-'}  {r['slug'][:45]}")
    print("\nSTİL KARNESİ (yalnız ≥7 günlük videolar; ortanca)")
    for s in STILLER:
        rr = [r for r in rows if r["style"] == s and r["age_d"] >= 7]
        if not rr:
            n_all = sum(1 for r in rows if r["style"] == s)
            print(f"  {s:<9} n=0 (yayında {n_all}, 7 günü dolan yok)"); continue
        v = median([r["views"] for r in rr]); p = median([r["avp"] or 0 for r in rr])
        sub = sum(r["subs"] for r in rr); tv = sum(r["views"] for r in rr)
        print(f"  {s:<9} n={len(rr)}  izlenme ortanca {v:>7.0f}  izleme %{p:>5.1f}  abone/1000 {1000*sub/max(tv,1):.1f}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("uret"); p.add_argument("--adet", type=int, default=2); p.add_argument("--dry", action="store_true"); p.set_defaults(f=uret)
    p = sp.add_parser("liste"); p.add_argument("--hepsi", action="store_true"); p.set_defaults(f=liste)
    p = sp.add_parser("onayla"); p.add_argument("ids", nargs="+"); p.set_defaults(f=onayla)
    p = sp.add_parser("reddet"); p.add_argument("ids", nargs="+"); p.set_defaults(f=reddet)
    p = sp.add_parser("yayinla"); p.add_argument("--dry", action="store_true"); p.set_defaults(f=yayinla)
    p = sp.add_parser("rapor"); p.add_argument("--json", action="store_true"); p.set_defaults(f=rapor)
    a = ap.parse_args()
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
