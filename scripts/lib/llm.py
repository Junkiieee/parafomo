#!/usr/bin/env python3
"""
ParaFOMO — TEK LLM KAPISI (script'lerin bütün `claude -p` çağrıları buradan geçer).

Neden var (Eylül 2026 otopsisi):
  1) Her script claude'u doğrudan çağırıyordu → her çağrı Claude Code'un tüm bağlamını
     (araç tanımları, kullanıcı ayarları: opus+xhigh, proje hafızası; ~25K token)
     yüklüyordu. Pro planında kota bunun yüzünden erken tükeniyordu.
  2) auth/limit HATA METNİ içerik sanılıp yayınlandı (~20 IG caption'ı "Failed to
     authenticate..." olarak çıktı).
  3) Kota dolunca her iş ayrı ayrı 4×90 sn deneyip boşa bekliyordu; 8 gece boyunca
     OAuth süresi dolmuşken kimse uyarılmadı.

Bu modül:
  - YALIN çağrı: araçsız, ayarsız, MCP'siz, boş dizinden (~7K token bağlam).
  - Hata sınıfı: ok | auth | session_limit | weekly_limit | transient | other.
  - Durum dosyası logs/llm-status.json: sert limit varsa 'until' zamanına kadar hiç
    çağrı YAPILMAZ (anında ok=False döner).
  - auth / sert limitte günde bir kez uyarı e-postası (agent/notify.py alert).
  - Hata ASLA içerik olarak dönmez: ok=False ise text="" .
  - Script çağrıları birbirini bekler (logs/llm.lock) → aynı anda token yenileme yarışı yok.

Python:
    sys.path.insert(0, "/root/parafomo/scripts/lib"); from llm import call
    ok, text, kind = call(prompt, model="sonnet", effort="low", timeout=300)
CLI:
    python3 scripts/lib/llm.py --model haiku --effort low < prompt.txt
    stdout = yanıt · exit: 0 ok · 3 auth · 4 limit · 5 diğer
    python3 scripts/lib/llm.py --status      # durum dosyasını yazdır
"""
import datetime as dt
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import time

ROOT = "/root/parafomo"
LOGS = os.path.join(ROOT, "logs")
STATUS = os.path.join(LOGS, "llm-status.json")
LOCK = os.path.join(LOGS, "llm.lock")
USAGE = os.path.join(LOGS, "llm-usage.jsonl")
EMPTY_CWD = "/root/.cache/parafomo-llm"          # proje hafızası/CLAUDE.md yüklenmesin
TOKEN_ENV = "/root/.config/parafomo/claude.env"  # opsiyonel: CLAUDE_CODE_OAUTH_TOKEN=...
NOTIFY = os.path.join(ROOT, "agent", "notify.py")

AUTH_PAT = ("failed to authenticate", "oauth", "access token", "401", "invalid api key",
            "please run /login", "not logged in", "authentication_error", "re-authenticate")
TRANSIENT_PAT = ("overloaded", "rate limit", "rate_limit", "529", "502", "503", "timed out",
                 "try again", "temporarily", "econnreset", "network")


def _now():
    return dt.datetime.now(dt.timezone.utc)


def claude_env():
    """cron'un kısıtlı ortamı için PATH/HOME + (varsa) uzun ömürlü OAuth token."""
    env = dict(os.environ)
    env["HOME"] = "/root"
    env["PATH"] = "/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    try:
        for line in open(TOKEN_ENV, encoding="utf-8"):
            line = line.strip()
            if line.startswith("CLAUDE_CODE_OAUTH_TOKEN=") and len(line) > 30:
                env["CLAUDE_CODE_OAUTH_TOKEN"] = line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return env


# ------------------------------------------------------------------ durum dosyası
def read_status():
    try:
        return json.load(open(STATUS, encoding="utf-8"))
    except Exception:
        return {"state": "ok"}


def write_status(state, message="", until=None):
    os.makedirs(LOGS, exist_ok=True)
    d = {"state": state, "updated": _now().isoformat(timespec="seconds"),
         "until": until.isoformat(timespec="seconds") if until else None,
         "message": (message or "")[:300]}
    tmp = STATUS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    os.replace(tmp, STATUS)
    return d


def blocked_until():
    """Sert limit hâlâ sürüyorsa bitiş zamanını döndür, yoksa None."""
    s = read_status()
    if s.get("state") in ("session_limit", "weekly_limit") and s.get("until"):
        try:
            until = dt.datetime.fromisoformat(s["until"])
            if until > _now():
                return until
        except Exception:
            pass
    return None


# ------------------------------------------------------------------ sınıflandırma
_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def parse_reset(text):
    """'resets 2:40am (UTC)' · 'resets 10pm (UTC)' · 'resets Sep 30, 10pm (UTC)' → datetime."""
    m = re.search(r"resets\s+(?:([A-Za-z]{3})[a-z]*\s+(\d{1,2}),\s*)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)",
                  text or "", re.I)
    if not m:
        return None
    mon, day, hh, mm, ap = m.groups()
    h = int(hh) % 12 + (12 if ap.lower() == "pm" else 0)
    now = _now()
    if mon and day and mon.lower()[:3] in _MONTHS:
        cand = now.replace(month=_MONTHS[mon.lower()[:3]], day=int(day), hour=h,
                           minute=int(mm or 0), second=0, microsecond=0)
        if cand < now - dt.timedelta(days=1):
            cand = cand.replace(year=now.year + 1)
        return cand
    cand = now.replace(hour=h, minute=int(mm or 0), second=0, microsecond=0)
    if cand <= now:
        cand += dt.timedelta(days=1)
    return cand


def classify(text, status_code=None):
    low = (text or "").lower()
    if "weekly limit" in low or "monthly limit" in low or ("usage limit" in low and "week" in low):
        return "weekly_limit"
    if "session limit" in low or "hit your limit" in low or "5-hour" in low:
        return "session_limit"
    if "hit your" in low and "limit" in low:
        return "weekly_limit" if parse_reset(text) and (parse_reset(text) - _now()).days >= 1 else "session_limit"
    if status_code == 401 or any(p in low for p in AUTH_PAT):
        return "auth"
    if status_code in (429, 500, 502, 503, 529) or any(p in low for p in TRANSIENT_PAT):
        return "transient"
    return "other"


# ------------------------------------------------------------------ uyarı
def alert(kind, message, until=None):
    """Kullanıcıya günde en fazla bir kez (tür başına) uyarı e-postası."""
    if kind == "auth":
        subj = "⚠️ ParaFOMO: Claude oturumu düştü — LLM işleri durdu"
        body = ("Sunucudaki Claude CLI kimlik doğrulaması başarısız. Video senaryoları, blog ve "
                "ajan bu düzelene kadar ÇALIŞMAZ (deterministik kartlar sürer).\n\n"
                "Kalıcı çözüm (bir kez):  sunucuda `claude setup-token` çalıştır, verdiği token'ı\n"
                f"{TOKEN_ENV} dosyasına `CLAUDE_CODE_OAUTH_TOKEN=<token>` olarak yaz.\n"
                "Hızlı çözüm:  sunucuda `claude` aç → /login.\n\n"
                f"Hata: {message[:300]}")
    else:
        when = until.strftime("%d %b %H:%M UTC") if until else "?"
        subj = f"⏸️ ParaFOMO: Claude kotası doldu ({'haftalık' if kind == 'weekly_limit' else '5 saatlik'}) — {when}'e kadar"
        body = (f"Claude Pro kotası doldu ({kind}). {when}'e kadar LLM gerektiren işler (senaryo, blog, "
                "ajan) atlanacak; deterministik işler (kartlar, veri güncelleme, hazır videoların "
                "yayını) sürer.\n\nSık oluyorsa: interaktif kullanımı azalt ya da Max plana geç.\n\n"
                f"Mesaj: {message[:300]}")
    key = f"llm-{kind}"
    try:
        subprocess.run([sys.executable, NOTIFY, "alert", "--key", key, "--subject", subj,
                        "--body", body], timeout=60, capture_output=True)
    except Exception:
        pass


# ------------------------------------------------------------------ çağrı
class _Lock:
    def __init__(self, path, wait):
        self.path, self.wait, self.f = path, wait, None

    def __enter__(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.f = open(self.path, "w")
        deadline = time.time() + self.wait
        while True:
            try:
                fcntl.flock(self.f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except BlockingIOError:
                if time.time() > deadline:
                    raise TimeoutError("llm kilidi alınamadı")
                time.sleep(3)

    def __exit__(self, *a):
        try:
            fcntl.flock(self.f, fcntl.LOCK_UN)
            self.f.close()
        except Exception:
            pass


def _log_usage(tag, model, d, kind):
    try:
        u = d.get("usage") or {}
        rec = {"ts": _now().isoformat(timespec="seconds"), "tag": tag, "model": model, "kind": kind,
               "cost": d.get("total_cost_usd"), "in": u.get("input_tokens"),
               "cache_create": u.get("cache_creation_input_tokens"),
               "cache_read": u.get("cache_read_input_tokens"), "out": u.get("output_tokens")}
        with open(USAGE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _one(prompt, model, effort, timeout, think=True, files=None):
    os.makedirs(EMPTY_CWD, exist_ok=True)
    env = claude_env()
    if not think:  # tek cümlelik işlerde "düşünme" ~15x token yakıyor (ölçüm 2026-10-06: 681 → 45)
        env["MAX_THINKING_TOKENS"] = "0"
    # files: görsel/metin dosyaları boş çalışma dizinine kopyalanır, model yalnız Read aracıyla okur
    tools = ""
    if files:
        for f in files:
            shutil.copy(f, os.path.join(EMPTY_CWD, os.path.basename(f)))
        tools = "Read"
    cmd = ["claude", "-p", "--model", model, "--output-format", "json",
           "--tools", tools, "--strict-mcp-config", "--disable-slash-commands",
           "--no-session-persistence", "--setting-sources", ""]
    if files:
        cmd += ["--allowedTools", "Read"]
    if effort:
        cmd += ["--effort", effort]
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                           timeout=timeout, cwd=EMPTY_CWD, env=env)
    except subprocess.TimeoutExpired:
        return None, "transient", "zaman aşımı"
    except FileNotFoundError:
        return None, "other", "claude CLI bulunamadı"
    raw = (r.stdout or "").strip()
    try:
        d = json.loads(raw.splitlines()[-1] if raw else "{}")
    except Exception:
        d = {}
    if d.get("type") == "result" and not d.get("is_error") and (d.get("result") or "").strip():
        return d, "ok", d["result"].strip()
    msg = (d.get("result") or raw or r.stderr or "").strip()
    kind = classify(msg + " " + (r.stderr or ""), d.get("api_error_status"))
    return d, kind, msg


def call(prompt, model="sonnet", effort="low", timeout=300, tries=2, tag="", lock_wait=900, think=True,
         files=None):
    """→ (ok: bool, text: str, kind: str). ok=False iken text DAİMA boş.
    think=False: genişletilmiş düşünmeyi kapatır (kısa caption/tek cümle işleri için)."""
    until = blocked_until()
    if until:
        return False, "", read_status().get("state", "session_limit")
    try:
        with _Lock(LOCK, lock_wait):
            kind, msg = "other", ""
            for attempt in range(1, tries + 1):
                d, kind, msg = _one(prompt, model, effort, timeout, think, files)
                _log_usage(tag, model, d or {}, kind)
                if kind == "ok":
                    if read_status().get("state") != "ok":
                        write_status("ok")
                    return True, msg, "ok"
                if kind in ("session_limit", "weekly_limit"):
                    until = parse_reset(msg) or (_now() + dt.timedelta(hours=1))
                    prev = read_status()
                    write_status(kind, msg, until)
                    if prev.get("state") != kind:
                        alert(kind, msg, until)
                    return False, "", kind
                if kind == "auth":
                    write_status("auth", msg)
                    alert("auth", msg)
                    return False, "", kind
                if attempt < tries:
                    time.sleep(30 if kind == "transient" else 5)
            print(f"[llm] başarısız ({kind}): {msg[:160]}", file=sys.stderr)
            return False, "", kind
    except TimeoutError:
        print("[llm] kilit zaman aşımı — başka bir LLM çağrısı çok uzun sürdü", file=sys.stderr)
        return False, "", "transient"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--effort", default="low")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--tag", default="cli")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--no-think", action="store_true")
    a = ap.parse_args()
    if a.status:
        s = read_status()
        print(json.dumps(s, ensure_ascii=False))
        return 0
    prompt = sys.stdin.read()
    ok, text, kind = call(prompt, a.model, a.effort, a.timeout, tag=a.tag, think=not a.no_think)
    if ok:
        print(text)
        return 0
    return {"auth": 3, "session_limit": 4, "weekly_limit": 4}.get(kind, 5)


if __name__ == "__main__":
    sys.exit(main())
