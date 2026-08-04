#!/usr/bin/env python3
"""
ParaFOMO Büyüme Ajanı — DENEY/KARAR DEFTERI (öğren, unutma, sonuca göre ilerle).

Ajanın ~1 günlük hafızasını KALICI hale getirir: her önemli hamle bir "deney"
olarak hipotez+beklenen metrik+baseline ile kaydedilir; olgunlaşınca gerçek
sonuca göre kapatılır ve kalıcı bir öğrenime dönüşür. Hepsi agent/memory/'de
(versiyonlanır → git geçmişi = kalıcı hafıza). digest-extras.py bunları geri besler.

Komutlar:
  add   --channel web|youtube|instagram|infra --action "..." --hypothesis "..." \
        --metric "izlenecek metrik" [--baseline "değer"]
  close --id <id> --status won|lost|inconclusive --outcome "..." --learning "..."
  learn --channel <k> --text "kalıcı içgörü"
  list-open
"""
import os, sys, json, argparse, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEM = os.path.join(ROOT, "agent", "memory")
EXP = os.path.join(MEM, "experiments.jsonl")
LEARN = os.path.join(MEM, "learnings.md")


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def _load():
    rows = []
    if os.path.exists(EXP):
        for line in open(EXP, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows


def _save(rows):
    os.makedirs(MEM, exist_ok=True)
    with open(EXP, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def cmd_add(a):
    os.makedirs(MEM, exist_ok=True)
    rows = _load()
    date = _now()
    seq = sum(1 for r in rows if r.get("id", "").startswith(date)) + 1
    rec = {"id": f"{date}-{seq}", "date": date, "channel": a.channel, "action": a.action,
           "hypothesis": a.hypothesis, "metric": a.metric, "baseline": a.baseline or "",
           "status": "open", "checked": "", "outcome": "", "learning": ""}
    with open(EXP, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("deney eklendi:", rec["id"])


def cmd_close(a):
    rows = _load()
    hit = False
    for r in rows:
        if r.get("id") == a.id:
            r.update(status=a.status, outcome=a.outcome, learning=a.learning, checked=_now())
            hit = True
    if not hit:
        print("bulunamadı:", a.id); sys.exit(1)
    _save(rows)
    print("deney kapandı:", a.id, "->", a.status)
    if a.learning:
        _append_learn(r["channel"], a.learning)


def _append_learn(channel, text):
    os.makedirs(MEM, exist_ok=True)
    with open(LEARN, "a", encoding="utf-8") as f:
        f.write(f"- [{_now()}][{channel}] {text}\n")


def cmd_learn(a):
    _append_learn(a.channel, a.text)
    print("öğrenim eklendi")


def cmd_list_open(a):
    n = 0
    for r in _load():
        if r.get("status") == "open":
            n += 1
            print(f"{r['id']} [{r['channel']}] {r['action']} | metrik: {r['metric']} | baseline: {r['baseline']}")
    if n == 0:
        print("(açık deney yok)")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("--channel", required=True); a.add_argument("--action", required=True)
    a.add_argument("--hypothesis", required=True); a.add_argument("--metric", required=True); a.add_argument("--baseline", default="")
    a.set_defaults(fn=cmd_add)
    c = sub.add_parser("close"); c.add_argument("--id", required=True); c.add_argument("--status", required=True, choices=["won", "lost", "inconclusive"])
    c.add_argument("--outcome", required=True); c.add_argument("--learning", default=""); c.set_defaults(fn=cmd_close)
    l = sub.add_parser("learn"); l.add_argument("--channel", required=True); l.add_argument("--text", required=True); l.set_defaults(fn=cmd_learn)
    lo = sub.add_parser("list-open"); lo.set_defaults(fn=cmd_list_open)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
