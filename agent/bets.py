#!/usr/bin/env python3
"""
ParaFOMO Ajanı v2 — BAHİS DEFTERİ (deney defterinin yerine).

Neden değişti: eski deney defterinde 59 deneyin 50'si "sonuçsuz" kapandı. Günde
~7 ziyaretçi ve video başına ~110 izlenmeyle tekil ince ayarlar 5-7 günde ölçülemez.
Bahis = BÜYÜK, 2-4 haftalık, toplu metrikle değerlendirilen strateji hamlesi.
Aynı anda en fazla 3 aktif bahis. Küçük işler bahis değildir (plan görevidir).

Komutlar:
  add   --title "..." --lever web|youtube|instagram|infra --hypothesis "..."
        --metric "..." --baseline "..." --target "..." --review YYYY-MM-DD [--pages REGEX]
  set-pages --id B... --pages REGEX   → brief bu desene uyan sayfaların GSC tık/gösterimini
                                         ve (haftalık) Google indeks durumunu otomatik hesaplar
  note  --id B... --text "haftalık kanıt notu"
  close --id B... --status won|lost|killed --result "sayılarla sonuç" --learning "tek cümle ders"
  list  [--all] [--md]
"""
import argparse
import datetime as dt
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = os.path.join(ROOT, "agent", "memory", "bets.jsonl")
MAX_ACTIVE = 3


def today():
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def load():
    rows = []
    if os.path.exists(FILE):
        for line in open(FILE, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows


def save(rows):
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    tmp = FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, FILE)


def find(rows, bid):
    for r in rows:
        if r["id"] == bid:
            return r
    sys.exit(f"bahis bulunamadı: {bid}")


def cmd_add(a):
    rows = load()
    active = [r for r in rows if r["status"] == "active"]
    if len(active) >= MAX_ACTIVE:
        sys.exit(f"HATA: zaten {len(active)} aktif bahis var (tavan {MAX_ACTIVE}). Önce birini kapat.")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%y%m%d")
    n = sum(1 for r in rows if r["id"].startswith(f"B{stamp}")) + 1
    rec = {"id": f"B{stamp}-{n}", "opened": today(), "title": a.title, "lever": a.lever,
           "hypothesis": a.hypothesis, "metric": a.metric, "baseline": a.baseline,
           "target": a.target, "review": a.review, "status": "active", "pages": a.pages or "",
           "notes": [], "result": "", "learning": "", "closed": ""}
    rows.append(rec)
    save(rows)
    print("bahis açıldı:", rec["id"])


def cmd_note(a):
    rows = load()
    r = find(rows, a.id)
    r.setdefault("notes", []).append(f"{today()}: {a.text}")
    save(rows)
    print("not eklendi:", a.id)


def cmd_set_pages(a):
    import re
    re.compile(a.pages)  # geçersiz desen erken patlasın
    rows = load()
    find(rows, a.id)["pages"] = a.pages
    save(rows)
    print(f"sayfa deseni: {a.id} → {a.pages}")


def cmd_close(a):
    rows = load()
    r = find(rows, a.id)
    r.update(status=a.status, result=a.result, learning=a.learning, closed=today())
    save(rows)
    print(f"bahis kapandı: {a.id} → {a.status}")


def render(rows, show_all=False):
    act = [r for r in rows if r["status"] == "active"]
    out = []
    for r in act:
        due = " ⏰ DEĞERLENDİRME ZAMANI" if r.get("review") and r["review"] <= today() else ""
        out.append(f"- **{r['id']} — {r['title']}** [{r['lever']}] · açılış {r['opened']} · "
                   f"değerlendirme {r.get('review', '?')}{due}")
        out.append(f"  - Hipotez: {r['hypothesis']}")
        out.append(f"  - Metrik: {r['metric']} · baz: {r['baseline']} · hedef: {r['target']}"
                   + (f" · sayfa deseni: `{r['pages']}`" if r.get("pages") else ""))
        for n in r.get("notes", [])[-3:]:
            out.append(f"  - Not: {n}")
    if not act:
        out.append("- (aktif bahis yok)")
    closed = [r for r in rows if r["status"] != "active"]
    if show_all:
        closed_view = closed
    else:
        cutoff = (dt.date.today() - dt.timedelta(days=35)).isoformat()
        closed_view = [r for r in closed if (r.get("closed") or "") >= cutoff]
    if closed_view:
        out.append("")
        out.append("Kapanan bahisler" + ("" if show_all else " (son 5 hafta)") + ":")
        for r in closed_view:
            out.append(f"- {r['id']} {r['title']} → **{r['status']}**: {r.get('result', '')}"
                       + (f" · Ders: {r['learning']}" if r.get("learning") else ""))
    return "\n".join(out)


def cmd_list(a):
    print(render(load(), a.all))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("add")
    for k in ("title", "lever", "hypothesis", "metric", "baseline", "target", "review"):
        s.add_argument(f"--{k}", required=True)
    s.add_argument("--pages", default="")
    s.set_defaults(fn=cmd_add)
    s = sub.add_parser("set-pages"); s.add_argument("--id", required=True); s.add_argument("--pages", required=True)
    s.set_defaults(fn=cmd_set_pages)
    s = sub.add_parser("note"); s.add_argument("--id", required=True); s.add_argument("--text", required=True)
    s.set_defaults(fn=cmd_note)
    s = sub.add_parser("close"); s.add_argument("--id", required=True)
    s.add_argument("--status", required=True, choices=["won", "lost", "killed"])
    s.add_argument("--result", required=True); s.add_argument("--learning", default="")
    s.set_defaults(fn=cmd_close)
    s = sub.add_parser("list"); s.add_argument("--all", action="store_true"); s.add_argument("--md", action="store_true")
    s.set_defaults(fn=cmd_list)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
