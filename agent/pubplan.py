#!/usr/bin/env python3
"""
ParaFOMO Ajanı v2 — BUGÜNÜN YAYIN TAKVİMİ (token'sız, crontab'dan türetilir).

Eskiden "bugün ne ne zaman çıkacak" tablosunu LLM yazıyordu (token + hata payı).
Artık gerçek crontab satırları + viral slot/format mantığı (viral-daily.sh ile aynı)
okunup deterministik üretilir → e-postadaki takvim her zaman gerçeğe eşit.

Kullanım: python3 agent/pubplan.py [--date YYYY-MM-DD] [--all]
  --all : arka plan işlerini (hazırlık, veri, öğrenme) de göster
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys

ROOT = "/root/parafomo"
VPY = "/root/.venvs/parafomo/bin/python"
SLOTS_UTC = ["05:00", "08:00", "10:00", "13:00", "15:30", "18:30"]  # viral-daily.sh ile aynı


def crontab_lines():
    try:
        if os.environ.get("PARAFOMO_CRONTAB"):   # test/önizleme: dosyadan oku
            out = open(os.environ["PARAFOMO_CRONTAB"], encoding="utf-8").read()
        else:
            out = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return []
    return [l.strip() for l in out.splitlines() if l.strip() and not l.strip().startswith("#")]


def _field_match(field, value, lo, hi):
    for part in field.split(","):
        step = 1
        if "/" in part:
            part, s = part.split("/", 1)
            step = int(s)
        if part == "*":
            a, b = lo, hi
        elif "-" in part:
            a, b = map(int, part.split("-", 1))
        else:
            a = b = int(part)
        if a <= value <= b and (value - a) % step == 0:
            return True
    return False


def times_today(spec, day):
    """5 alanlı cron → bugünün (saat, dakika) listesi (ay/gün alanları desteklenir)."""
    mi, ho, dom, mon, dow = spec
    cron_dow = (day.isoweekday() % 7)  # cron: 0=Pazar
    if not _field_match(dom, day.day, 1, 31) or not _field_match(mon, day.month, 1, 12):
        return []
    if not (_field_match(dow, cron_dow, 0, 7) or (cron_dow == 0 and _field_match(dow, 7, 0, 7))):
        return []
    return [(h, m) for h in range(24) if _field_match(ho, h, 0, 23)
            for m in range(60) if _field_match(mi, m, 0, 59)]


def viral_plan(day):
    """viral-daily.sh'taki slot + format mantığının birebir kopyası."""
    doy = day.timetuple().tm_yday
    learned = None
    try:
        r = subprocess.run([VPY, f"{ROOT}/scripts/learn/winner.py", "viral.slot"],
                           capture_output=True, text=True, timeout=30)
        v = r.stdout.strip()
        learned = int(v) if v.isdigit() and int(v) < len(SLOTS_UTC) else None
    except Exception:
        pass
    if learned is not None:
        target = (doy // 3) % len(SLOTS_UTC) if doy % 3 == 0 else learned
        why = "keşif günü" if doy % 3 == 0 else "öğrenilen saat"
    else:
        target, why = doy % len(SLOTS_UTC), "rotasyon"
    fmt = None
    try:
        src = open(f"{ROOT}/scripts/viral-daily.sh", encoding="utf-8").read()
        m = re.search(r"declare -A DOW_FMT=\(([^)]*)\)", src)
        table = dict(re.findall(r"\[(\d)\]=(\w+)", m.group(1))) if m else {}
        fmt = table.get(str(day.isoweekday()))
        r = subprocess.run([VPY, f"{ROOT}/scripts/learn/winner.py", "viral.format"],
                           capture_output=True, text=True, timeout=30)
        if r.stdout.strip():
            fmt = r.stdout.strip() + " (öğrenilen)"
    except Exception:
        pass
    return target, why, fmt


def high_events(day):
    try:
        d = json.load(open(f"{ROOT}/data/economic-calendar.json", encoding="utf-8"))
        return [e.get("title", "") for e in d.get("events", [])
                if e.get("date") == day.isoformat() and e.get("impact") == "High"]
    except Exception:
        return []


def build(day, show_all=False):
    target, why, fmt = viral_plan(day)
    events = high_events(day)
    rows = []
    for line in crontab_lines():
        parts = line.split(None, 5)
        if len(parts) < 6:
            continue
        spec, cmd = parts[:5], parts[5]
        for (h, m) in times_today(spec, day):
            label, bg = None, False
            if "viral-daily.sh" in cmd and "--prepare" in cmd:
                label, bg = "Viral senaryo hazırlığı (LLM)", True
            elif "viral-daily.sh" in cmd:
                at = re.search(r"--at (\d)", cmd)
                if at and int(at.group(1)) != target:
                    continue
                label = f"YouTube Short + IG Reel — viral ({fmt or '?'}; slot {target}, {why})"
            elif "shorts-daily.sh" in cmd and "--prepare" in cmd:
                label, bg = "Blog→Short senaryo hazırlığı (LLM)", True
            elif "shorts-daily.sh" in cmd:
                label = "YouTube Short — günün blog yazısından"
            elif "manim-daily.sh" in cmd:
                label = "YouTube Short + IG Reel — tam-Manim animasyon"
            elif "news-daily.sh" in cmd:
                if not events and not show_all:
                    continue
                label = ("Gündem Short — " + "; ".join(events[:2])) if events else "Gündem Short (olay yok → atlar)"
            elif "daily-content.sh" in cmd:
                label = "Blog yazısı (+ Telegram kanalı)"
            elif "altin-daily.sh" in cmd:
                label = "IG altın kartı + story (0-59 dk rastgele gecikme)"
            elif "bist-daily.sh" in cmd:
                label = "IG BIST " + ("kapanış" if "kapanis" in cmd else "açılış") + " kartı + story"
            elif "halka-arz-ig.sh" in cmd:
                label = "IG halka arz tarih kartı (yeni tarih varsa)"
            elif "spk-onay-ig.sh" in cmd:
                label = "IG SPK onay kartı (yeni bülten varsa)"
            elif "halka-arz-update.sh" in cmd:
                label, bg = "Halka arz verisi güncelleme", True
            elif "learn-daily.sh" in cmd:
                label, bg = "Öğrenme döngüsü (metrik topla)", True
            elif "weekly-report.py" in cmd:
                label, bg = "Haftalık trafik raporu", True
            elif "agent/run.sh" in cmd:
                label, bg = "Büyüme ajanı (gece koşusu)", True
            elif "maintenance.sh" in cmd:
                label, bg = "Bakım (disk/log temizliği)", True
            else:
                label, bg = os.path.basename(cmd.split()[0]), True
            if bg and not show_all:
                continue
            rows.append((h, m, label))
    rows.sort()
    return rows


def render(day=None, show_all=False):
    day = day or dt.datetime.now(dt.timezone.utc).date()
    rows = build(day, show_all)
    if not rows:
        return "_(aktif yayın cron'u yok — otomasyon duraklatılmış olabilir)_"
    # Aynı işin gün içindeki tekrarlarını tek satırda topla (ilk saat sırası korunur)
    grouped = {}
    for h, m, label in rows:
        grouped.setdefault(label, []).append((h, m))
    out = ["| UTC | TR | Ne çıkıyor |", "|---|---|---|"]
    for label, times in sorted(grouped.items(), key=lambda kv: kv[1][0]):
        utc = ", ".join(f"{h:02d}:{m:02d}" for h, m in times)
        tr = ", ".join(f"{(h + 3) % 24:02d}:{m:02d}" for h, m in times)
        out.append(f"| {utc} | {tr} | {label} |")
    return "\n".join(out)


if __name__ == "__main__":
    d = None
    if "--date" in sys.argv:
        d = dt.date.fromisoformat(sys.argv[sys.argv.index("--date") + 1])
    print(render(d, "--all" in sys.argv))
