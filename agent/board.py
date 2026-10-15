#!/usr/bin/env python3
"""
ParaFOMO Ajanı v2 — GÖREV MASASI (dashboard.parafomo.com'un veri katmanı).

Görevlerin metni ajanın kendi dosyalarından OKUNUR (tek kaynak, ikinci kopya yok):
  agent/plan/week.md        → ajanın kuyruğu (- [ ] T4 (etiket) — **başlık** · ayrıntı)
  agent/plan/user-tasks.md  → Kaan'dan beklenenler (1. **başlık** + girintili ayrıntı)
Kaan'ın kararları/notları ve ajanın durum satırları ayrı tutulur:
  /root/parafomo-data/board.json  (repo DIŞI — GitHub reposu herkese açık, notlar özel)

Ajan komutları (headless'ta `python3 agent/board.py ...`):
  brief                          → Kaan'ın kararları + yeni istekleri + işaretleri (brief'e girer)
  status <ID> "<metin>"          → kuyruktaki görevin "Ajan durumu" satırı (ör. "Canlı — <link>")
  user <no|slug> verified "<not>"→ Kaan "Yaptım" dedi, sunucuda doğrulandı (sonra user-tasks.md'den sil)
  user <no|slug> reopen "<neden>"→ doğrulanamadı; Kaan'a ne eksik olduğunu yaz
  inbox <N> taken|done|declined "<not>" → Kaan'ın panelden verdiği görev isteğini işle
  counts                         → e-posta özeti için sayılar (JSON)
"""
import contextlib
import datetime as dt
import fcntl
import json
import os
import re
import sys
import unicodedata

ROOT = "/root/parafomo"
PLAN = os.path.join(ROOT, "agent", "plan")
WEEK = os.path.join(PLAN, "week.md")
USER_TASKS = os.path.join(PLAN, "user-tasks.md")
STORE = os.environ.get("PARAFOMO_BOARD", "/root/parafomo-data/board.json")

DECISIONS = {"pending": "Onay bekliyor", "approved": "Onaylandı (öne al)", "rejected": "Reddedildi"}
USER_STATES = {"todo": "Yapılacak", "done": "Yaptım", "later": "Sonraya", "verified": "Doğrulandı"}
INBOX_STATES = {"new": "Yeni", "taken": "Kuyruğa alındı", "done": "Bitti", "declined": "Yapılmayacak"}

TASK_RE = re.compile(r"^- \[([ xX-])\] (.*)$")
ID_RE = re.compile(r"^([A-Z][A-Za-z]*-?[A-Za-z0-9]*\d[A-Za-z0-9]*|[A-Z]+-[a-z]+)\b\s*(?:\(([^)]*)\))?\s*(?:—\s*)?(.*)$", re.S)
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
USER_RE = re.compile(r"^(\d+)\.\s+(.*)$")


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def slug(s):
    s = s.replace("ı", "i").replace("İ", "i")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _read(path):
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        return ""


# ---------- depo (kilitli, atomik) ----------

def _empty():
    return {"agent": {}, "user": {}, "inbox": [], "log": []}


def load():
    try:
        d = json.load(open(STORE, encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    base = _empty()
    base.update({k: v for k, v in d.items() if k in base})
    return base


@contextlib.contextmanager
def edit():
    """with edit() as d: ... → kilit altında oku-değiştir-yaz (panel ve ajan aynı anda yazabilir)."""
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    with open(STORE + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        d = load()
        yield d
        d["log"] = d["log"][-300:]
        tmp = STORE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tmp, STORE)


def _log(d, who, what):
    d["log"].append({"ts": now(), "who": who, "what": what})


# ---------- markdown kaynaklarını ayrıştır ----------

def parse_week(text=None):
    text = _read(WEEK) if text is None else text
    m = re.search(r"plan-date:\s*(\d{4}-\d{2}-\d{2})", text)
    plan_date = m.group(1) if m else ""
    title = (text.splitlines() or [""])[0].lstrip("# ").strip()
    tasks, log_done, section, cur = [], [], "", None
    status_md = []
    for line in text.splitlines():
        if line.startswith("## "):
            section, cur = line[3:].strip(), None
            continue
        if section == "Durum" and line.strip():
            status_md.append(line)
        tm = TASK_RE.match(line)
        if tm:
            cur = None
            mark, rest = tm.group(1), tm.group(2)
            im = ID_RE.match(rest)
            state = {"x": "done", "X": "done", "-": "dropped"}.get(mark, "open")
            if not im:
                if state == "done":
                    log_done.append(rest)
                continue
            tid, tag, body = im.group(1), (im.group(2) or ""), im.group(3)
            b = BOLD_RE.search(body)
            ttl = (b.group(1) if b else (tag or re.split(r" · | — ", body)[0])).strip().rstrip(":").strip()
            result = ""
            if state == "done":
                r = re.match(r"→\s*(.*?)(?: — \*\*| · haftalık koşu)", body)
                result = r.group(1).strip() if r else ""
            elif state == "dropped":
                result = body.split(" — ", 1)[-1] if not b else ""
            cur = {"id": tid, "tag": tag, "title": ttl or tid, "state": state, "section": section,
                   "body": body, "result": result, "key": f"{tid}:{slug(ttl)[:40]}"}
            tasks.append(cur)
        elif cur is not None and line.startswith("  ") and line.strip():
            cur["body"] += "\n" + line.strip()
        elif not line.strip():
            cur = None
    return {"plan_date": plan_date, "title": title, "tasks": tasks, "log_done": log_done,
            "status_md": "\n".join(status_md)}


def parse_user_tasks(text=None):
    text = _read(USER_TASKS) if text is None else text
    items, notes, cur = [], [], None
    for line in text.splitlines():
        um = USER_RE.match(line)
        if um:
            b = BOLD_RE.search(um.group(2))
            ttl = (b.group(1) if b else um.group(2)).strip()
            rest = BOLD_RE.sub("", um.group(2), count=1).strip() if b else ""
            cur = {"no": int(um.group(1)), "title": ttl, "slug": slug(ttl)[:60], "body": rest}
            items.append(cur)
        elif cur is not None and line.startswith("   ") and line.strip():
            cur["body"] += ("\n" if cur["body"] else "") + line[3:].rstrip()
        elif line.strip() and not line.startswith("#"):
            cur = None
            notes.append(line)
        elif not line.strip() and notes and notes[-1] != "":
            notes.append("")
    return items, "\n".join(notes).strip()


# ---------- birleşik görünüm (panel API + brief) ----------

def view():
    d = load()
    wk = parse_week()
    for t in wk["tasks"]:
        e = d["agent"].get(t["key"], {})
        t["decision"] = e.get("decision", "pending")
        t["note"] = e.get("note", "")
        t["agent_status"] = e.get("agent_status", "")
        t["agent_status_ts"] = e.get("agent_status_ts", "")
        t["updated"] = e.get("updated", "")
    items, notes = parse_user_tasks()
    live = set()
    for it in items:
        e = d["user"].get(it["slug"], {})
        it["status"] = e.get("status", "todo")
        it["note"] = e.get("note", "")
        it["agent_note"] = e.get("agent_note", "")
        it["updated"] = e.get("updated", "")
        live.add(it["slug"])
    # user-tasks.md'den düşmüş ama panelde izi olan işler → "son kapananlar"
    closed = sorted(({"slug": k, **v} for k, v in d["user"].items()
                     if k not in live and v.get("status") in ("done", "verified")),
                    key=lambda r: r.get("updated", ""), reverse=True)[:8]
    return {"week": wk, "user_tasks": items, "user_notes": notes, "user_closed": closed,
            "inbox": sorted(d["inbox"], key=lambda r: r.get("created", ""), reverse=True),
            "log": d["log"][-40:][::-1]}


def counts(v=None):
    v = v or view()
    open_tasks = [t for t in v["week"]["tasks"] if t["state"] == "open"]
    return {
        "agent_open": len(open_tasks),
        "agent_pending": sum(1 for t in open_tasks if t["decision"] == "pending"),
        "user_todo": sum(1 for u in v["user_tasks"] if u["status"] in ("todo",)),
        "user_done_unverified": sum(1 for u in v["user_tasks"] if u["status"] == "done"),
        "inbox_new": sum(1 for i in v["inbox"] if i.get("status") == "new"),
    }


# ---------- panelden yazma (server.py çağırır) ----------

def set_decision(key, decision=None, note=None, who="kaan"):
    if decision is not None and decision not in DECISIONS:
        raise ValueError("geçersiz karar")
    task = next((t for t in parse_week()["tasks"] if t["key"] == key), None)
    if not task:
        raise KeyError("görev bulunamadı (plan değişmiş olabilir — sayfayı yenile)")
    with edit() as d:
        e = d["agent"].setdefault(key, {})
        e["title"], e["id"] = task["title"], task["id"]
        if decision is not None and decision != e.get("decision"):
            e["decision"] = decision
            _log(d, who, f"{task['id']} → {DECISIONS[decision]}")
        if note is not None and note != e.get("note", ""):
            e["note"] = note.strip()
            _log(d, who, f"{task['id']} notu güncellendi")
        e["updated"] = now()
        return e


def set_user(slug_, status=None, note=None, who="kaan"):
    if status is not None and status not in USER_STATES:
        raise ValueError("geçersiz durum")
    items, _ = parse_user_tasks()
    it = next((i for i in items if i["slug"] == slug_), None)
    with edit() as d:
        e = d["user"].setdefault(slug_, {})
        if it:
            e["title"] = it["title"]
        elif not e:
            raise KeyError("görev bulunamadı")
        if status is not None and status != e.get("status"):
            e["status"] = status
            if who == "kaan":
                e["agent_note"] = ""      # yeni işaret → ajanın eski 'eksik' notu geçersiz
            _log(d, who, f"“{e.get('title', slug_)[:50]}” → {USER_STATES[status]}")
        if note is not None and note != e.get("note", ""):
            e["note"] = note.strip()
        e["updated"] = now()
        return e


def add_inbox(text, who="kaan"):
    text = text.strip()
    if not text:
        raise ValueError("boş istek")
    with edit() as d:
        n = 1 + max([int(i["id"][1:]) for i in d["inbox"] if i.get("id", "N0")[1:].isdigit()] or [0])
        item = {"id": f"N{n}", "text": text[:2000], "created": now(), "status": "new", "agent_note": ""}
        d["inbox"].append(item)
        _log(d, who, f"Yeni istek {item['id']}: {text[:60]}")
        return item


def delete_inbox(iid, who="kaan"):
    with edit() as d:
        before = len(d["inbox"])
        d["inbox"] = [i for i in d["inbox"] if not (i["id"] == iid and i.get("status") == "new")]
        if len(d["inbox"]) == before:
            raise KeyError("yalnız henüz alınmamış istek geri çekilebilir")
        _log(d, who, f"{iid} geri çekildi")


# ---------- ajan CLI ----------

def _find_task(tid):
    ts = [t for t in parse_week()["tasks"] if t["id"] == tid]
    if not ts:
        sys.exit(f"week.md'de {tid} yok")
    return ts[-1]


def cmd_status(tid, text):
    t = _find_task(tid)
    with edit() as d:
        e = d["agent"].setdefault(t["key"], {"decision": "pending"})
        e.update(title=t["title"], id=tid, agent_status=text.strip(), agent_status_ts=now())
        _log(d, "ajan", f"{tid}: {text[:80]}")
    print(f"ok — {tid} durumu yazıldı")


def cmd_user(ref, action, note):
    items, _ = parse_user_tasks()
    it = next((i for i in items if str(i["no"]) == ref or i["slug"] == ref), None)
    if not it:
        sys.exit(f"user-tasks.md'de '{ref}' yok (numara ya da slug ver)")
    with edit() as d:
        e = d["user"].setdefault(it["slug"], {})
        e["title"] = it["title"]
        if action == "verified":
            e["status"], e["agent_note"] = "verified", note
            _log(d, "ajan", f"“{it['title'][:50]}” doğrulandı")
        elif action == "reopen":
            e["status"], e["agent_note"] = "todo", note
            _log(d, "ajan", f"“{it['title'][:50]}” doğrulanamadı: {note[:60]}")
        else:
            sys.exit("eylem: verified | reopen")
        e["updated"] = now()
    print(f"ok — '{it['title']}' → {action}"
          + (" · şimdi user-tasks.md'den bu maddeyi sil" if action == "verified" else ""))


def cmd_inbox(iid, action, note):
    if action not in ("taken", "done", "declined"):
        sys.exit("eylem: taken | done | declined")
    with edit() as d:
        it = next((i for i in d["inbox"] if i["id"] == iid), None)
        if not it:
            sys.exit(f"{iid} yok")
        it["status"], it["agent_note"], it["updated"] = action, note, now()
        _log(d, "ajan", f"{iid} → {INBOX_STATES[action]}: {note[:60]}")
    print(f"ok — {iid} → {action}")


def render_brief():
    v = view()
    out = ["Kanonik görev masası: **dashboard.parafomo.com** (Claude Docs panosu emekli). Kaan'ın kararları "
           "aşağıda; burada adı geçmeyen açık görev = karar verilmemiş → normal sırayla yap."]
    dec = [t for t in v["week"]["tasks"] if t["state"] == "open" and (t["decision"] != "pending" or t["note"])]
    if dec:
        out += ["", "**Kaan'ın kararları (week.md kuyruğu):**"]
        for t in dec:
            act = {"approved": "ONAYLANDI → kuyrukta öne al", "rejected": "REDDEDİLDİ → yapma; week.md'de [-] yap",
                   "pending": "karar yok"}[t["decision"]]
            out.append(f"- {t['id']} “{t['title']}” — {act}" + (f" · Kaan'ın notu (talimat): {t['note']}" if t["note"] else ""))
    else:
        out += ["", "_Kuyrukta Kaan'ın onay/red/notu yok._"]
    new = [i for i in v["inbox"] if i.get("status") in ("new", "taken")]
    if new:
        out += ["", "**Kaan'ın panelden verdiği görev istekleri** (yeni → değerlendir, week.md kuyruğuna uygun yere "
                "ekle, `python3 agent/board.py inbox <N> taken \"T14 olarak eklendi\"`; biterse `done`; "
                "kırmızı çizgiye takılıyorsa `declined \"neden\"`):"]
        for i in new:
            out.append(f"- {i['id']} [{INBOX_STATES[i['status']]}] ({i['created'][:10]}) {i['text']}"
                       + (f" — ajan notu: {i['agent_note']}" if i.get("agent_note") else ""))
    marked = [u for u in v["user_tasks"] if u["status"] != "todo" or u["note"]]
    if marked:
        out += ["", "**Kaan'ın işaretlediği kullanıcı görevleri (user-tasks.md):**"]
        for u in marked:
            hint = {"done": "YAPTIM dedi → sunucuda doğrula; doğruysa `python3 agent/board.py user "
                            f"{u['no']} verified \"kanıt\"` + user-tasks.md'den sil; değilse `... reopen \"eksik ne\"`",
                    "later": "SONRAYA bıraktı → bu hafta hatırlatma",
                    "verified": "doğrulandı (user-tasks.md'den silinmeli)",
                    "todo": "yapılacak"}[u["status"]]
            out.append(f"- #{u['no']} “{u['title']}” — {hint}" + (f" · Kaan'ın notu: {u['note']}" if u["note"] else ""))
    out += ["", "Koşu sonunda üzerinde çalıştığın görev için: `python3 agent/board.py status <ID> \"<kısa durum>\"` "
            "(ör. \"Canlı — https://parafomo.com/x/\", \"Engel: EVDS anahtarı bekleniyor\")."]
    return "\n".join(out)


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return
    cmd = a[0]
    if cmd == "brief":
        print(render_brief())
    elif cmd == "counts":
        print(json.dumps(counts(), ensure_ascii=False))
    elif cmd == "json":
        print(json.dumps(view(), ensure_ascii=False, indent=1))
    elif cmd == "status" and len(a) >= 3:
        cmd_status(a[1], " ".join(a[2:]))
    elif cmd == "user" and len(a) >= 3:
        cmd_user(a[1], a[2], " ".join(a[3:]))
    elif cmd == "inbox" and len(a) >= 3:
        cmd_inbox(a[1], a[2], " ".join(a[3:]))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
