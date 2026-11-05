"""
ParaFOMO Panel — dashboard.parafomo.com (yalnız Kaan; Caddy basic_auth arkasında, 127.0.0.1:8792).

Veri: ajanın kendi dosyaları (agent/plan, agent/memory, agent/state) + agent/board.py (kararlar).
Yazma yalnız board.py üzerinden; panel başka hiçbir dosyaya dokunmaz.
Çalıştır: /root/.venvs/parafomo-api/bin/uvicorn server:app --app-dir dashboard --host 127.0.0.1 --port 8792
"""
import datetime as dt
import json
import os
import sys
import threading
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

ROOT = "/root/parafomo"
AG = os.path.join(ROOT, "agent")
HERE = os.path.dirname(os.path.abspath(__file__))
# health.git_status() her 2 dk `git status` çalıştırır; varsayılan git index.lock'u alıp index'i yazar →
# aynı anda cron'un git add/commit'i "index.lock exists" ile düşebilir. Panel yalnız okur: kilit alma.
os.environ.setdefault("GIT_OPTIONAL_LOCKS", "0")
sys.path.insert(0, AG)
import bets      # noqa: E402
import board     # noqa: E402
import health    # noqa: E402
import pubplan   # noqa: E402

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

# Ajan/e-posta kaynaklı metin innerHTML ile çizilir → XSS'e karşı ikinci kat: satır içi script/olay
# özniteliği/javascript: URL'si çalışmaz; başka sitede çerçevelenemez (Caddy'nin X-Frame-Options'ına ek).
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
       "font-src https://fonts.gstatic.com; img-src 'self'; connect-src 'self'; object-src 'none'; "
       "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["Content-Security-Policy"] = CSP
    resp.headers["X-Content-Type-Options"] = "nosniff"
    if request.url.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"   # özel notlar tarayıcı/ara önbellekte kalmasın
    return resp

# health.collect() canlı siteyi/API'yi yoklar, pubplan winner.py çalıştırır → kısa önbellek
_cache, _lock = {}, threading.Lock()


def cached(key, ttl, fn):
    with _lock:
        hit = _cache.get(key)
        if hit and time.time() - hit[0] < ttl:
            return hit[1]
    val = fn()
    with _lock:
        _cache[key] = (time.time(), val)
    return val


def jsonl(path, last=None):
    rows = []
    try:
        for line in open(path, encoding="utf-8"):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    pass
    except OSError:
        pass
    return rows[-last:] if last else rows


def read(path):
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        return ""


def schedule():
    # Panel TSİ gününü gösterir (app.js saatlere +3 ekler). UTC tarihi 00:00-03:00 TSİ arasında DÜNÜN
    # gün-kısıtlı işlerini (Pzt bülteni, Pzt-Cum blog…) "bugün" diye listeliyordu. Cron saatleri UTC kalır.
    day = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=3)).date()
    pub = {(h, m, l) for h, m, l in pubplan.build(day, False)}
    rows, seen = [], {}
    for h, m, label in pubplan.build(day, True):
        seen.setdefault(label, []).append((h, m))
    for label, times in seen.items():
        rows.append({"label": label, "bg": (times[0][0], times[0][1], label) not in pub,
                     "utc": [f"{h:02d}:{m:02d}" for h, m in times]})
    rows.sort(key=lambda r: r["utc"][0])
    return rows


def run_info():
    st = {}
    try:
        st = json.load(open(os.path.join(AG, "state", "run-status.json"), encoding="utf-8"))
    except (OSError, ValueError):
        pass
    rep_path = os.path.join(AG, "state", "report.md")
    rep, rep_ts = read(rep_path), None
    if rep:
        rep_ts = dt.datetime.fromtimestamp(os.path.getmtime(rep_path), dt.timezone.utc).isoformat(timespec="seconds")
    runs = jsonl(os.path.join(AG, "memory", "runs.jsonl"), 30)
    for r in runs:
        r.pop("session_id", None)
    return {"status": st, "report": rep, "report_ts": rep_ts, "runs": runs[::-1]}


# CSRF: basic_auth kimliği tarayıcıda başka sitelerden gelen isteklere de otomatik eklenir → her /api/ ucu
# özel başlık ister (çapraz sitede ancak CORS ön-uçuşuyla eklenebilir; panel CORS izni vermez).
# GET'ler de: <img src=".../api/health"> her seferinde git + alt süreç + canlı yoklama tetikliyordu.
def guard(req: Request):
    if req.headers.get("x-dash") != "1":
        raise HTTPException(403, "eksik başlık")


@app.get("/api/state")
def state(req: Request):
    guard(req)
    v = board.view()
    return {
        "now": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "board": v,
        "counts": board.counts(v),
        "decisions": board.DECISIONS,
        "user_states": board.USER_STATES,
        "inbox_states": board.INBOX_STATES,
        "kpi": jsonl(os.path.join(AG, "memory", "kpi-daily.jsonl")),
        "bets": [b for b in bets.load() if b.get("status") == "active"],
        "bets_closed": [b for b in bets.load() if b.get("status") != "active"][-4:][::-1],
        "agent": run_info(),
        "health": cached("health", 120, health.collect),
        "schedule": cached("schedule", 600, schedule),
        "roadmap": read(os.path.join(AG, "plan", "roadmap.md")),
    }


@app.get("/api/health")
def health_fresh(req: Request):
    guard(req)
    with _lock:
        _cache.pop("health", None)
    h = cached("health", 120, health.collect)
    return {"health": h, "problems": health.problems(h)}


# ---------- yazma uçları (guard yukarıda: özel başlık şartı) ----------
# Not/istek metni ajanın prompt'una girer → makul üst sınır (board.json ve token şişmesin).

class AgentIn(BaseModel):
    decision: str | None = None
    note: str | None = Field(None, max_length=10000)


class UserIn(BaseModel):
    status: str | None = None
    note: str | None = Field(None, max_length=10000)


class InboxIn(BaseModel):
    text: str = Field(max_length=10000)


def _wrap(fn):
    try:
        return fn()
    except KeyError as e:
        raise HTTPException(404, str(e).strip("'\""))
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/agent/{key:path}")
def post_agent(key: str, body: AgentIn, req: Request):
    guard(req)
    return _wrap(lambda: board.set_decision(key, body.decision, body.note))


@app.post("/api/user/{slug}")
def post_user(slug: str, body: UserIn, req: Request):
    guard(req)
    if body.status == "verified":
        raise HTTPException(400, "doğrulamayı ajan yapar")
    return _wrap(lambda: board.set_user(slug, body.status, body.note))


@app.post("/api/inbox")
def post_inbox(body: InboxIn, req: Request):
    guard(req)
    return _wrap(lambda: board.add_inbox(body.text))


@app.delete("/api/inbox/{iid}")
def del_inbox(iid: str, req: Request):
    guard(req)
    _wrap(lambda: board.delete_inbox(iid))
    return {"ok": True}


# ---------- statik ----------

STATIC = {"app.js": "application/javascript", "app.css": "text/css", "icon.svg": "image/svg+xml",
          "manifest.webmanifest": "application/manifest+json"}


@app.get("/")
def index():
    return FileResponse(os.path.join(HERE, "index.html"), headers={"Cache-Control": "no-cache"})


@app.get("/{name}")
def static(name: str):
    if name not in STATIC:
        return JSONResponse({"detail": "yok"}, status_code=404)
    return FileResponse(os.path.join(HERE, name), media_type=STATIC[name], headers={"Cache-Control": "no-cache"})
