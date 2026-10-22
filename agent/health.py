#!/usr/bin/env python3
"""
ParaFOMO Ajanı v2 — ÜRETİM SAĞLIĞI (token'sız).

Her üretim hattının SON BAŞARILI çalışmasını loglardan bulur, beklenen sıklıkla
kıyaslar → OK / GECİKTİ / HATA. Ayrıca: Claude kota/oturum durumu, disk, git
(dal, ileride/geride, yarım rebase), canlı site + portföy API'si.

Eski sistemin en pahalı hatası buydu: 8 gece OAuth düşük kaldı, hatlar sessizce
durdu, kimse fark etmedi. Bu betik brief'in ve e-postanın ilk bölümünü besler.

Kullanım:
  python3 agent/health.py            # markdown tablo
  python3 agent/health.py --json     # makine-okur özet
"""
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request

ROOT = "/root/parafomo"
LOGS = os.path.join(ROOT, "logs")
STATE = os.path.join(ROOT, "agent", "state")
TS_RE = re.compile(r"\[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}):\d{2} UTC\]")
ERR_RE = re.compile(r"HATA|Traceback|hit your|Failed to authenticate|ÜRETİLEMEDİ|başarısız", re.I)

# ad, log, başarı deseni, beklenen azami yaş (saat; None = olaya bağlı), not
PIPELINES = [
    ("Viral Short (YouTube+IG)", "viral.log", r"\] Tamamlandı: \S+ @", 30, "günlük 1 slot"),
    # "Kuyruk boş" = Shorts'a çevrilecek yeni yazı yok (hafta sonu blog yok) → hata değil (2026-10-18 yanlış alarm)
    ("Blog→Short (YouTube)", "shorts.log", r"bu çalıştırmada [1-9]\d* Shorts yayınlandı|Kuyruk boş — işlenecek yeni yazı yok", 30, "11:00 UTC"),
    ("Manim Short (YouTube+IG)", "manim-daily.log", r"Manim-daily tamam:", 30, "16:00 UTC"),
    ("Gündem Short", "news.log", r"gündem videosu üretildi", None, "yalnız yüksek-etkili olay günü"),
    ("Blog yazısı", "cron.log", r"\] Tamamlandı$", 80, "Pzt-Cum"),
    ("IG altın kartı", "altin-ig.log", r"YAYINLANDI", 30, "her gün"),
    ("IG BIST kartları", "bist.log", r"YAYINLANDI", 80, "Pzt-Cum"),
    ("Halka arz verisi", "halka-arz.log", r"Değişiklik yok|Push başarılı", 14, "6 saatte bir"),
    ("Öğrenme döngüsü", "learn.log", r"Öğrenme döngüsü tamamlandı", 30, "günlük"),
]


def _now():
    return dt.datetime.now(dt.timezone.utc)


def _parse_ts(m):
    return dt.datetime.strptime(f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc)


def scan_log(path, ok_pat, tail_bytes=400_000):
    """Son başarı zamanı + başarıdan SONRAKİ son hata satırı."""
    if not os.path.exists(path):
        return None, None, None
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - tail_bytes))
        text = f.read().decode("utf-8", "ignore")
    ok_re = re.compile(ok_pat)
    cur = last_ok = last_err = last_run = None
    for line in text.splitlines():
        m = TS_RE.search(line)
        if m:
            cur = _parse_ts(m)
            last_run = cur
        if ok_re.search(line):
            last_ok = cur
            last_err = None
        elif ERR_RE.search(line) and "UYARI" not in line[:8]:
            last_err = (cur, line.strip()[:160])
    return last_ok, last_err, last_run


def age_h(t):
    return (_now() - t).total_seconds() / 3600 if t else None


def fmt_age(h):
    if h is None:
        return "hiç"
    return f"{h:.0f} sa önce" if h < 48 else f"{h / 24:.1f} gün önce"


def pipelines():
    rows = []
    for name, log, pat, max_h, note in PIPELINES:
        last_ok, last_err, last_run = scan_log(os.path.join(LOGS, log), pat)
        h = age_h(last_ok)
        if max_h is None:
            status = "OK" if not last_err else "HATA"
        elif last_ok is None or h > max_h:
            status = "GECİKTİ"
        else:
            status = "OK"
        if last_err and status == "OK" and max_h is not None:
            status = "UYARI"
        rows.append({"name": name, "status": status, "last_ok": last_ok.isoformat() if last_ok else None,
                     "age": fmt_age(h), "note": note,
                     "error": last_err[1] if last_err else ""})
    return rows


def agent_status():
    try:
        d = json.load(open(os.path.join(STATE, "run-status.json"), encoding="utf-8"))
    except Exception:
        return {"name": "Ajan (gece koşusu)", "status": "BİLİNMİYOR", "age": "hiç", "note": "", "error": ""}
    end = d.get("ended") or d.get("started")
    h = age_h(dt.datetime.fromisoformat(end)) if end else None
    ok = d.get("outcome") == "success"
    status = "OK" if ok and h is not None and h < 30 else ("GECİKTİ" if ok else "HATA")
    return {"name": f"Ajan ({d.get('mode', '?')})", "status": status, "age": fmt_age(h),
            "note": f"{d.get('model', '?')} · ${d.get('cost', '?')}",
            "error": "" if ok else f"{d.get('outcome')}: {(d.get('message') or '')[:140]}"}


def llm_status():
    try:
        d = json.load(open(os.path.join(LOGS, "llm-status.json"), encoding="utf-8"))
    except Exception:
        d = {"state": "ok"}
    st = d.get("state", "ok")
    until = d.get("until")
    if st in ("session_limit", "weekly_limit") and until:
        try:
            if dt.datetime.fromisoformat(until) <= _now():
                st = "ok"
        except Exception:
            pass
    return {"state": st, "until": until, "message": d.get("message", "")}


def git_status():
    def g(*a):
        r = subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True, timeout=30)
        return r.stdout.strip()
    branch = g("rev-parse", "--abbrev-ref", "HEAD")
    rebasing = os.path.isdir(os.path.join(ROOT, ".git", "rebase-merge")) or \
        os.path.isdir(os.path.join(ROOT, ".git", "rebase-apply"))
    ab = g("rev-list", "--left-right", "--count", "origin/main...HEAD").split()
    behind, ahead = (int(ab[0]), int(ab[1])) if len(ab) == 2 else (0, 0)
    dirty = [l for l in g("status", "--porcelain").splitlines() if l.strip()]
    stashes = [l for l in g("stash", "list").splitlines() if "agent-wip" in l]
    return {"branch": branch, "rebasing": rebasing, "ahead": ahead, "behind": behind,
            "dirty": len(dirty), "dirty_sample": dirty[:6], "agent_stashes": stashes[:3]}


def http_ok(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "parafomo-health"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except Exception as e:
        return str(e)[:60]


def stale_data():
    """Elle/aylık beslenen veri sayfaları bayatladı mı? (2026-10-10: kira sayfası 2 ay eski kalmıştı.)"""
    out = []
    today = dt.date.today()
    AY = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    def load(name):
        try:
            return json.load(open(os.path.join(ROOT, "data", name), encoding="utf-8"))
        except Exception:
            return None
    if today.day > 8:  # TÜİK ~3'ü açıklar; 8'inden sonra hâlâ eskiyse sorun
        k = load("kira-artis-2026.json")
        want = f"{AY[today.month - 1]} {today.year}"
        if k and k.get("guncelAy") != want:
            out.append(f"kira oranı bayat ({k.get('guncelAy')} ≠ {want}) → scripts/kira-artis-update.sh")
        t = load("tufe-aylik.json")
        prev = (today.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
        if t and t["months"][0]["ay"] != prev:
            out.append(f"TÜFE serisi bayat (son {t['months'][0]['ay']} ≠ {prev}) → scripts/tufe-update.py")
        y = load("yeniden-degerleme.json")
        son = (y or {}).get("veriSonAy") or (y or {}).get("sonAy")
        if y and son != prev:
            out.append(f"Yİ-ÜFE/YD serisi bayat (son {son} ≠ {prev}) → scripts/yeniden-degerleme-update.py")
    # Yeniden değerleme sezon bekçisi (Kasım-Aralık): Ekim verisi + tebliğ takibi (week.md T13)
    y = load("yeniden-degerleme.json")
    if y:
        yil = today.year
        if today >= dt.date(yil, 11, 4) and y.get("sonAy", "") < f"{yil}-10":
            out.append(f"YD KRİTİK: Ekim {yil} Yİ-ÜFE hâlâ yok (son {y.get('sonAy')}) — oran kesinleşemedi → scripts/yeniden-degerleme-update.py")
        teblig_ok = (y.get("hedefYil") == yil + 1 and y.get("tebligOrani")) or \
            any(g.get("uygulamaYili") == yil + 1 for g in y.get("gecmis", []))
        if today >= dt.date(yil, 12, 5) and not teblig_ok:
            out.append(f"YD KRİTİK: {yil + 1} tebliğ oranı doğrulanıp yazılmadı → WebSearch ile Resmî Gazete tebliğini bul, data/yeniden-degerleme.json tebligOrani alanına yaz, sonra python3 scripts/live-posts.py")
    # Kıdem tazminatı tavanı Ocak/Temmuz'da değişir; HMB katsayı genelgesi ilk haftada çıkar
    kt = load("kidem-tavan.json")
    if kt and today.day > 10 and today.month in (1, 7):
        want = f"{today.year}-{today.month:02d}-01"
        if kt["donemler"][-1]["baslangic"] != want:
            out.append(f"kıdem tavanı bayat (son dönem {kt['donemler'][-1]['baslangic']} ≠ {want}) → WebSearch ile HMB/TÜRMOB tavanını doğrula, data/kidem-tavan.json'a yeni dönem ekle")
    # Memur katsayıları / en düşük aylıklar Ocak-Temmuz değişir (HMB genelgesi ilk hafta); bayram ikramiyesi yılbaşı
    em = load("emekli-memur.json")
    if em and today.month in (1, 7) and today.day > 15 and em.get("donem") != f"{today.year}-{today.month:02d}":
        out.append(f"memur katsayıları / en düşük emekli aylığı bayat (dönem {em.get('donem')}) → WebSearch ile HMB genelgesi + "
                   "SGK tutarlarını ≥2 kaynakla doğrula, data/emekli-memur.json'u güncelle (/memur-zammi-hesaplama, /en-dusuk-emekli-maasi)")
    # Sosyal aylıklar (/engelli-maasi): memur katsayısı yeni döneme geçtiyse ASHB resmî tutarları da girilmeli
    sa = load("sosyal-aylik-2026.json")
    if em and sa and em.get("donem") and sa.get("resmi", {}).get("donem") and em["donem"] > sa["resmi"]["donem"]:
        out.append(f"sosyal aylıklar bayat: memur katsayısı {em['donem']} ama ASHB resmî tutarlar {sa['resmi']['donem']} → "
                   "ASHB duyurusundan 65 yaş/engelli aylıklarını doğrula, data/sosyal-aylik-2026.json resmi bloğunu güncelle")
    # Emekli promosyonu (/emekli-promosyonu): bankaların kampanyaları ay sonunda biter; resmi sayfadan yeniden kontrol
    ep = load("emekli-promosyon.json")
    if ep:
        biten = [b["banka"] for b in ep["bankalar"] if b.get("bitis") and b["bitis"] < today.isoformat()]
        eski = (today - dt.date.fromisoformat(ep["kontrol"])).days
        if biten or eski > 30:
            out.append(f"emekli promosyonu kontrol bekliyor (son kontrol {ep['kontrol']}, {eski} gün; süresi dolan: "
                       f"{', '.join(biten) or 'yok'}) → bankaların resmi sayfalarını WebFetch ile oku, data/emekli-promosyon.json "
                       "tutar/bitis/kontrol alanlarını güncelle (haber sitesi rakamı YAZMA)")
    # app.parafomo.com kendi veri kopyasını okur (deploy-app.sh); repo TÜFE'si ilerideyse app reel getirisi eskide kalır
    try:
        app_t = json.load(open("/srv/parafomo-app/tufe-aylik.json", encoding="utf-8"))
        rt = load("tufe-aylik.json")
        if rt and app_t["months"][0]["ay"] != rt["months"][0]["ay"]:
            out.append(f"app TÜFE kopyası eski ({app_t['months'][0]['ay']} ≠ {rt['months'][0]['ay']}) → bash scripts/deploy-app.sh")
    except Exception:
        pass
    # TCMB haftalık faizleri (EVDS): son hafta (Cuma) 13 günden eskiyse anahtar/API bozulmuş olabilir
    fz = load("faiz-oranlari.json")
    if fz and (today - dt.date.fromisoformat(fz["hafta"])).days > 13:
        out.append(f"TCMB faiz verisi bayat (son hafta {fz['hafta']}) → bash scripts/evds-update.sh (EVDS anahtarı: ~/.config/parafomo/evds.env)")
    # Günlük/sık güncellenen veri dosyaları: 'updated' alanı eşikten eskiyse alarm
    for name, max_days, fix in (
        ("altin-getiri.json", 4, "scripts/gold-returns.py"), ("dolar-getiri.json", 4, "scripts/dollar-returns.py"),
        ("gumus-getiri.json", 4, "scripts/silver-returns.py"), ("euro-getiri.json", 4, "scripts/euro-returns.py"),
        ("bitcoin-getiri.json", 4, "scripts/bitcoin-returns.py"), ("bist-getiri.json", 4, "scripts/bist-returns.py"),
        ("altin-fiyat.json", 3, "scripts/altin-fiyat.py"), ("halka-arz.json", 2, "scripts/fetch-halka-arz.py"),
        ("economic-calendar.json", 9, "scripts/fetch-economic-calendar.py"),
    ):
        d = load(name)
        upd = (d or {}).get("updated", "")[:10]
        try:
            age = (today - dt.date.fromisoformat(upd)).days
        except Exception:
            continue
        if age > max_days:
            out.append(f"{name} bayat ({age} gün; eşik {max_days}) → {fix}")
    # Talep madencisi + OG kartları üretim kontrolü
    try:
        g = json.load(open(os.path.join(ROOT, "data", "learning", "demand-gaps.json"), encoding="utf-8"))
        age = (today - dt.date.fromisoformat(g["generated_utc"][:10])).days
        if age > 9:
            out.append(f"demand-gaps.json bayat ({age} gün) → scripts/learn/demand_miner.py (learn-daily Çrş+Paz)")
    except Exception:
        out.append("demand-gaps.json yok → scripts/learn/demand_miner.py")
    og = os.path.join(ROOT, "public", "og")
    pngs = [os.path.join(og, f) for f in os.listdir(og)] if os.path.isdir(og) else []
    if len(pngs) < 10:
        out.append(f"OG kartları eksik ({len(pngs)} png) → scripts/og-images.py")
    elif pngs and all((dt.date.today() - dt.date.fromtimestamp(os.path.getmtime(p))).days > 45 for p in pngs):
        out.append("OG kartları 45+ gündür hiç yenilenmemiş → scripts/og-images.py üretimi kontrol et")
    # Canlı blog yazıları (content-templates/blog → scripts/live-posts.py): elle düzenleme veri güncellemesini durdurur
    try:
        import subprocess
        r = subprocess.run(["python3", os.path.join(ROOT, "scripts", "live-posts.py"), "--check"],
                           capture_output=True, text=True, timeout=60)
        for line in r.stdout.splitlines():
            if "UYARI" in line:
                out.append("canlı yazı: " + line.replace("[live-posts] UYARI: ", "")[:220])
            elif "GÜNCELLENECEK" in line:
                out.append("canlı yazı veriden geride: " + line.replace("[live-posts] ", "") + " → python3 scripts/live-posts.py")
    except Exception as e:
        out.append(f"live-posts --check çalışmadı: {e}")
    # Yıl sonu: son toplantı geçtiyse gelecek yılın takvimi eklenmiş olmalı (takvim sayfası "sıradaki karar"ı gösteremez)
    for name, label, extra in (("tcmb-2026.json", "TCMB", None), ("fomc-2026.json", "Fed", "meetings2027")):
        dd = load(name)
        if not dd:
            continue
        dates = [m["decisionDate"] for m in dd.get("meetings", [])] + [m["decisionDate"] for m in dd.get(extra, [])] if extra else \
            [m["decisionDate"] for m in dd.get("meetings", [])]
        nxt = os.path.exists(os.path.join(ROOT, "data", name.replace("2026", str(today.year + 1))))
        if dates and max(dates) < today.isoformat() and not nxt:
            out.append(f"{label} {today.year + 1} toplantı takvimi yok (son toplantı {max(dates)} geçti) → resmî takvimi "
                       f"WebSearch ile doğrula, data/{name.replace('2026', str(today.year + 1))} ekle ve sayfayı ona bağla")
    for name, label in (("fomc-2026.json", "Fed"), ("tcmb-2026.json", "TCMB")):
        d = load(name)
        if not d:
            continue
        for m in d["meetings"]:
            # karar günü + 1 gün sonra hâlâ result yoksa
            if (today - dt.date.fromisoformat(m["decisionDate"])).days >= 1 and not m.get("result"):
                out.append(f"{label} {m['decisionDate']} kararı yazılmadı → scripts/policy-decisions.sh")
    return out


def seo_status():
    """scripts/seo-audit.py özeti (panel + sorun listesi)."""
    try:
        d = json.load(open(os.path.join(ROOT, "data", "learning", "seo-audit.json"), encoding="utf-8"))
    except Exception:
        return None
    age = (_now() - dt.datetime.fromisoformat(d["generated"])).total_seconds() / 3600
    return {"counts": d["counts"], "index": d["index"], "pages": d["pages"], "age_h": round(age, 1),
            "by_code": d.get("by_code", {}), "codes": d.get("codes", {}),
            "issues": [i for i in d["issues"] if i["sev"] != "BİLGİ"][:200]}


def collect():
    du = shutil.disk_usage("/")
    return {
        "ts": _now().isoformat(timespec="seconds"),
        "pipelines": pipelines(),
        "agent": agent_status(),
        "llm": llm_status(),
        "git": git_status(),
        "disk_pct": round(du.used / du.total * 100),
        "disk_free_gb": round(du.free / 1e9, 1),
        "site": http_ok("https://parafomo.com/"),
        "api": http_ok("https://api.parafomo.com/health"),
        "stale": stale_data(),
        "seo": seo_status(),
    }


ICON = {"OK": "✅", "UYARI": "🟡", "GECİKTİ": "🔴", "HATA": "🔴", "BİLİNMİYOR": "⚪"}


def render(h):
    out = ["| Hat | Durum | Son başarı | Not |", "|---|---|---|---|"]
    for r in h["pipelines"] + [h["agent"]]:
        err = f" — `{r['error'][:110]}`" if r.get("error") and r["status"] != "OK" else ""
        out.append(f"| {r['name']} | {ICON.get(r['status'], '')} {r['status']} | {r['age']} | {r['note']}{err} |")
    llm = h["llm"]
    llm_txt = "✅ ok" if llm["state"] == "ok" else f"🔴 {llm['state']}" + (f" (→ {llm['until']})" if llm.get("until") else "")
    g = h["git"]
    git_txt = f"{g['branch']}" + (" · ⚠️ YARIM REBASE" if g["rebasing"] else "") + \
        (f" · {g['ahead']} push bekliyor" if g["ahead"] else "") + (f" · {g['behind']} geride" if g["behind"] else "") + \
        (f" · {g['dirty']} kirli dosya" if g["dirty"] else " · temiz")
    if g["agent_stashes"]:
        git_txt += f" · yarım ajan işi stash'te: {g['agent_stashes'][0]}"
    disk = f"%{h['disk_pct']} dolu ({h['disk_free_gb']} GB boş)" + (" ⚠️" if h["disk_pct"] >= 88 else "")
    out += ["", f"- **Claude (LLM) durumu:** {llm_txt}",
            f"- **Git:** {git_txt}",
            f"- **Disk:** {disk}",
            f"- **Canlı site:** {h['site']} · **Portföy API:** {h['api']}",
            "- **Veri tazeliği:** " + ("✅ güncel" if not h.get("stale") else "🔴 " + "; ".join(h["stale"]))]
    return "\n".join(out)


def problems(h):
    """E-posta konusu/özet için kısa sorun listesi."""
    p = [f"{r['name']}: {r['status']}" for r in h["pipelines"] + [h["agent"]] if r["status"] in ("GECİKTİ", "HATA")]
    if h["llm"]["state"] != "ok":
        p.append(f"Claude: {h['llm']['state']}")
    if h["git"]["rebasing"]:
        p.append("git: yarım rebase")
    if h["disk_pct"] >= 88:
        p.append(f"disk %{h['disk_pct']}")
    if h["site"] != 200:
        p.append(f"site: {h['site']}")
    if h["api"] != 200:
        p.append(f"api: {h['api']}")
    p += [f"veri: {x}" for x in h.get("stale", [])]
    seo = h.get("seo")
    if seo and seo["counts"].get("KRİTİK"):
        p.append(f"SEO: {seo['counts']['KRİTİK']} kritik sorun")
    if seo and seo["age_h"] > 72:
        p.append("SEO denetimi 3 gündür çalışmadı (learn-daily.sh)")
    return p


if __name__ == "__main__":
    h = collect()
    if "--json" in sys.argv:
        print(json.dumps(h, ensure_ascii=False, indent=1))
    else:
        print(render(h))
        pr = problems(h)
        print("\n**Sorunlar:** " + ("; ".join(pr) if pr else "yok"))
