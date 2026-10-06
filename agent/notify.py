#!/usr/bin/env python3
"""
ParaFOMO Ajanı v2 — E-POSTA (rapor + uyarı). Telegram'a rapor GİTMEZ.

  report [--dry] [--force]   → günün raporu: KPI satırı + ajanın yazdığı bölüm + üretim
                               sağlığı + bugünün yayın takvimi + kullanıcı görevleri.
                               Ajan bu gece çalışamadıysa konu satırı bunu söyler ve ajan
                               bölümü yerine NEDENİ yazılır (eski sistem dünkü raporu yeni
                               tarihle tekrar gönderiyordu — artık rapor dosyası koşudan
                               ESKİYSE kullanılmaz).
  alert --key K --subject S --body B [--force]
                             → acil uyarı; aynı anahtar için günde en fazla bir kez.

.env: EMAIL_USER, EMAIL_APP_PASSWORD, EMAIL_TO (Gmail App Password; port 587 STARTTLS —
bu sunucuda 465 kapalı).
"""
import argparse
import datetime as dt
import json
import os
import smtplib
import ssl
import sys
from email.mime.text import MIMEText

ROOT = "/root/parafomo"
AG = os.path.join(ROOT, "agent")
STATE = os.path.join(AG, "state")
sys.path.insert(0, AG)


def env():
    e = {}
    try:
        for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                e[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return e


def send(subject, body, dry=False):
    if dry:
        print(f"Konu: {subject}\n\n{body}")
        return True
    e = env()
    user, pw = e.get("EMAIL_USER"), e.get("EMAIL_APP_PASSWORD")
    to = e.get("EMAIL_TO") or user
    if not user or not pw:
        print("[mail] EMAIL_USER/EMAIL_APP_PASSWORD yok — gönderilemedi")
        return False
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"], msg["From"], msg["To"] = subject, user, to
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
            s.ehlo()
            s.starttls(context=ssl.create_default_context())
            s.login(user, pw)
            s.sendmail(user, [t.strip() for t in to.split(",")], msg.as_string())
        print("[mail] gönderildi ->", to)
        return True
    except Exception as ex:
        print("[mail] HATA:", ex)
        return False


def marker(key):
    return os.path.join(STATE, f".mail-{key}-{dt.datetime.now(dt.timezone.utc):%Y-%m-%d}")


def once(key, force):
    os.makedirs(STATE, exist_ok=True)
    return force or not os.path.exists(marker(key))


def mark(key):
    open(marker(key), "w").close()
    # 10 günden eski işaretleri buda
    cutoff = dt.datetime.now().timestamp() - 10 * 86400
    for f in os.listdir(STATE):
        if f.startswith(".mail-") and os.path.getmtime(os.path.join(STATE, f)) < cutoff:
            try:
                os.remove(os.path.join(STATE, f))
            except OSError:
                pass


def read(path, default=""):
    try:
        return open(path, encoding="utf-8").read().strip()
    except OSError:
        return default


def kpi_line():
    try:
        k = json.load(open(os.path.join(STATE, "kpi.json"), encoding="utf-8"))
    except Exception:
        return "_(KPI alınamadı)_"
    return (f"📊 Gerçek ziyaretçi (7g): {k.get('real_7d')} (hedef 7000 → %{(k.get('real_7d') or 0) / 70:.1f}) · "
            f"Google: {k.get('gsc_clicks_7d')} tık / {k.get('gsc_impr_7d')} gösterim (7g) · "
            f"AI asistan (28g): {k.get('ai_assistant_28d')} · "
            f"YouTube: {k.get('yt_subs')} abone, {k.get('yt_views') or 0:,} izlenme, {k.get('yt_videos')} video")


def cmd_report(a):
    import health
    import pubplan
    st = {}
    try:
        st = json.load(open(os.path.join(STATE, "run-status.json"), encoding="utf-8"))
    except Exception:
        pass
    mode = st.get("mode", "daily")
    key = f"report-{mode}"
    if not once(key, a.force) and not a.dry:
        print(f"[mail] bugünün {mode} raporu zaten gönderildi (--force ile zorla)")
        return
    outcome = st.get("outcome", "?")
    rep_path = os.path.join(STATE, "report.md")
    rep = ""
    if os.path.exists(rep_path) and st.get("started"):
        started = dt.datetime.fromisoformat(st["started"]).timestamp()
        if os.path.getmtime(rep_path) >= started:   # yalnız BU koşuda yazılmış rapor
            rep = read(rep_path)
    h = health.collect()
    probs = health.problems(h)
    today = dt.datetime.now(dt.timezone.utc).date()
    label = "Haftalık Plan" if mode == "weekly" else "Gece Raporu"
    if outcome == "success":
        subject = f"🤖 ParaFOMO {label} — {today}"
    elif outcome == "budget":
        subject = f"🤖 ParaFOMO {label} — {today} (bütçe tavanında kesildi)"
    else:
        subject = f"⚠️ ParaFOMO — ajan bu gece çalışamadı ({outcome}) — {today}"
    if probs:
        subject += f" · {len(probs)} sorun"
    parts = [kpi_line(), ""]
    if rep:
        parts += [rep, ""]
    else:
        why = st.get("message") or "bilinmiyor"
        parts += [f"## Ajan bu gece rapor yazmadı",
                  f"- Sonuç: **{outcome}** — {why[:400]}",
                  "- Üretim hatları (videolar, kartlar, veri) ajandan bağımsız çalışmaya devam eder.", ""]
        if outcome == "auth":
            parts += ["**Yapman gereken:** sunucuda `claude setup-token` → token'ı "
                      "`/root/.config/parafomo/claude.env` içine `CLAUDE_CODE_OAUTH_TOKEN=...` olarak yaz "
                      "(ya da hızlıca `claude` → /login).", ""]
    parts += ["## Üretim sağlığı", health.render(h), ""]
    parts += ["## Bugün ne zaman ne çıkıyor", pubplan.render(today), ""]
    tasks = read(os.path.join(AG, "plan", "user-tasks.md"))
    if tasks:
        parts += ["## Senden istenenler", tasks, ""]
    if st.get("denied"):
        parts += ["## İzin listesi dışında kalan komutlar (ajan denedi, sistem reddetti)",
                  "_Gerekliyse agent/allowed-tools.txt'e eklenebilir:_"]
        parts += [f"- `{c}`" for c in st["denied"][:8]] + [""]
    parts += [f"— ajan: {st.get('mode', '?')} · {st.get('model', '?')} · maliyet ${st.get('cost', '?')} "
              f"(API-eşdeğeri) · {st.get('minutes', '?')} dk · {st.get('turns', '?')} tur"]
    if send(subject, "\n".join(parts), a.dry) and not a.dry:
        mark(key)


def cmd_alert(a):
    if not once(f"alert-{a.key}", a.force):
        print(f"[mail] '{a.key}' uyarısı bugün zaten gönderildi")
        return
    if send(a.subject, a.body, a.dry) and not a.dry:
        mark(f"alert-{a.key}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report"); r.add_argument("--dry", action="store_true"); r.add_argument("--force", action="store_true")
    r.set_defaults(fn=cmd_report)
    al = sub.add_parser("alert"); al.add_argument("--key", required=True); al.add_argument("--subject", required=True)
    al.add_argument("--body", required=True); al.add_argument("--dry", action="store_true"); al.add_argument("--force", action="store_true")
    al.set_defaults(fn=cmd_alert)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
