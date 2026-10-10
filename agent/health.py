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
    ("Blog→Short (YouTube)", "shorts.log", r"bu çalıştırmada [1-9]\d* Shorts yayınlandı", 30, "11:00 UTC"),
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
        if y and y.get("sonAy") != prev:
            out.append(f"Yİ-ÜFE/YD serisi bayat (son {y.get('sonAy')} ≠ {prev}) → scripts/yeniden-degerleme-update.py")
    for name, label in (("fomc-2026.json", "Fed"), ("tcmb-2026.json", "TCMB")):
        d = load(name)
        if not d:
            continue
        for m in d["meetings"]:
            # karar günü + 1 gün sonra hâlâ result yoksa
            if (today - dt.date.fromisoformat(m["decisionDate"])).days >= 1 and not m.get("result"):
                out.append(f"{label} {m['decisionDate']} kararı yazılmadı → scripts/policy-decisions.sh")
    return out


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
    return p


if __name__ == "__main__":
    h = collect()
    if "--json" in sys.argv:
        print(json.dumps(h, ensure_ascii=False, indent=1))
    else:
        print(render(h))
        pr = problems(h)
        print("\n**Sorunlar:** " + ("; ".join(pr) if pr else "yok"))
