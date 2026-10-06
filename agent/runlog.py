#!/usr/bin/env python3
"""
ParaFOMO Ajanı v2 — koşu kaydı + mod seçimi (run.sh'ın yardımcısı).

  pick-mode                       → "weekly" | "daily" (stdout)
  start --mode M --model X        → agent/state/run-status.json (koşu başladı)
  finish --json <claude çıktısı> [--resumed-from <json>]
                                  → sonucu sınıflandır, run-status.json + memory/runs.jsonl
                                    stdout: "<outcome>\t<session_id>\t<reset_epoch|0>"
  skip --reason "..."             → koşu hiç başlamadı (kota/auth) kaydı

Haftalık koşu kuralı: Perşembe (Claude haftalık kotası Çarşamba 22:00 UTC'de
sıfırlanıyor → pahalı Opus koşusu taze kotaya denk gelsin) ve son 4 günde başarılı
haftalık yoksa; ya da hangi gün olursa olsun son 8 günde başarılı haftalık yoksa.
"""
import argparse
import datetime as dt
import json
import os
import sys

ROOT = "/root/parafomo"
STATE = os.path.join(ROOT, "agent", "state")
RUNS = os.path.join(ROOT, "agent", "memory", "runs.jsonl")
STATUS = os.path.join(STATE, "run-status.json")
sys.path.insert(0, os.path.join(ROOT, "scripts", "lib"))
WEEKLY_DOW = int(os.environ.get("AGENT_WEEKLY_DOW", "4"))  # 1=Pzt … 4=Perşembe


def now():
    return dt.datetime.now(dt.timezone.utc)


def load_runs():
    if not os.path.exists(RUNS):
        return []
    out = []
    for line in open(RUNS, encoding="utf-8"):
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def last_weekly_ok():
    for r in reversed(load_runs()):
        if r.get("mode") == "weekly" and r.get("outcome") == "success":
            return dt.datetime.fromisoformat(r["started"])
    return None


def plan_date():
    """agent/plan/week.md içindeki <!-- plan-date: YYYY-MM-DD --> (kurulum/elle yazılmış plan)."""
    import re
    try:
        m = re.search(r"plan-date:\s*(\d{4}-\d{2}-\d{2})",
                      open(os.path.join(ROOT, "agent", "plan", "week.md"), encoding="utf-8").read())
        return dt.datetime.fromisoformat(m.group(1)).replace(tzinfo=dt.timezone.utc) if m else None
    except Exception:
        return None


def pick_mode():
    """Perşembe (haftalık kota sıfırlamasından sonra) haftalık; Perşembe kaçtıysa 8. günde telafi.
    Hiç haftalık koşu yoksa: taze (≤7 gün) bir plan varsa Perşembe'yi bekle, yoksa hemen haftalık."""
    lw = last_weekly_ok()
    if now().isoweekday() == WEEKLY_DOW and (lw is None or (now() - lw).days >= 4):
        return "weekly"
    if lw is not None:
        return "weekly" if (now() - lw).days >= 8 else "daily"
    pd = plan_date()
    return "weekly" if pd is None or (now() - pd).days >= 8 else "daily"


def write_status(d):
    os.makedirs(STATE, exist_ok=True)
    tmp = STATUS + ".tmp"
    json.dump(d, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, STATUS)


def read_status():
    try:
        return json.load(open(STATUS, encoding="utf-8"))
    except Exception:
        return {}


def append_run(d):
    os.makedirs(os.path.dirname(RUNS), exist_ok=True)
    keep = {k: d.get(k) for k in ("started", "ended", "mode", "model", "effort", "outcome", "cost",
                                   "turns", "minutes", "resumed", "message", "denied")}
    with open(RUNS, "a", encoding="utf-8") as f:
        f.write(json.dumps(keep, ensure_ascii=False) + "\n")


def parse_result(path):
    try:
        raw = open(path, encoding="utf-8").read().strip()
        return json.loads(raw.splitlines()[-1]) if raw else {}, raw
    except Exception:
        try:
            return {}, open(path, encoding="utf-8", errors="ignore").read()[-600:]
        except Exception:
            return {}, ""


def classify(d, raw):
    """→ (outcome, message). outcome: success | budget | session_limit | weekly_limit | auth | error"""
    import llm
    if d.get("type") == "result" and not d.get("is_error"):
        sub = d.get("subtype", "")
        if sub == "success":
            return "success", (d.get("result") or "")[:300]
        if "budget" in sub:
            return "budget", f"bütçe tavanına ulaşıldı ({sub})"
        return "error", sub
    msg = (d.get("result") or raw or "").strip()[:400]
    sub = d.get("subtype", "")
    if "budget" in sub:
        return "budget", f"bütçe tavanına ulaşıldı ({sub})"
    kind = llm.classify(msg, d.get("api_error_status"))
    if kind in ("session_limit", "weekly_limit"):
        llm.write_status(kind, msg, llm.parse_reset(msg))
        return kind, msg
    if kind == "auth":
        llm.write_status("auth", msg)
        return "auth", msg
    return "error", msg or "boş çıktı"


def cmd_start(a):
    d = {"started": now().isoformat(timespec="seconds"), "mode": a.mode, "model": a.model,
         "effort": a.effort, "outcome": "running", "pid": os.getpid()}
    write_status(d)


def cmd_finish(a):
    import llm
    st = read_status()
    d, raw = parse_result(a.json)
    outcome, msg = classify(d, raw)
    cost = d.get("total_cost_usd")
    if a.prev_cost:
        cost = round((cost or 0) + float(a.prev_cost), 4)
    started = dt.datetime.fromisoformat(st.get("started")) if st.get("started") else now()
    denied = [((x.get("tool_input") or {}).get("command") or x.get("tool_name") or "?")[:120]
              for x in (d.get("permission_denials") or [])]
    if denied:
        st["denied"] = (st.get("denied") or []) + denied
    st.update(ended=now().isoformat(timespec="seconds"), outcome=outcome, message=msg,
              cost=round(cost, 3) if isinstance(cost, (int, float)) else cost,
              turns=d.get("num_turns"), session_id=d.get("session_id"),
              minutes=round((now() - started).total_seconds() / 60), resumed=bool(a.prev_cost))
    write_status(st)
    reset = 0
    if outcome in ("session_limit", "weekly_limit"):
        r = llm.parse_reset(msg)
        reset = int(r.timestamp()) if r else 0
    if not a.no_log:
        append_run(st)
    # Boş alan yerine "-": bash `read` sekmeleri birleştirip alanları kaydırmasın.
    print(f"{outcome}\t{d.get('session_id') or '-'}\t{reset}\t{cost if cost is not None else 0}")


def cmd_skip(a):
    st = {"started": now().isoformat(timespec="seconds"), "ended": now().isoformat(timespec="seconds"),
          "mode": a.mode, "model": a.model, "outcome": a.outcome, "message": a.reason, "cost": 0}
    write_status(st)
    append_run(st)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pick-mode").set_defaults(fn=lambda a: print(pick_mode()))
    s = sub.add_parser("start"); s.add_argument("--mode"); s.add_argument("--model"); s.add_argument("--effort", default="")
    s.set_defaults(fn=cmd_start)
    s = sub.add_parser("finish"); s.add_argument("--json", required=True)
    s.add_argument("--prev-cost", default=""); s.add_argument("--no-log", action="store_true")
    s.set_defaults(fn=cmd_finish)
    s = sub.add_parser("skip"); s.add_argument("--mode"); s.add_argument("--model")
    s.add_argument("--outcome", default="skipped"); s.add_argument("--reason", required=True)
    s.set_defaults(fn=cmd_skip)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
