#!/usr/bin/env bash
#
# ParaFOMO Büyüme Ajanı — gece raporunu TEK bir e-posta olarak gönderir.
# TELEGRAM'A HİÇBİR RAPOR GİTMEZ. Kaynak: agent/state/report.md
# (rapor zaten şunları içerir: dün otopsisi + bugün yapılanlar + bugünkü
#  paylaşım takvimi + kullanıcı görevleri).
#
# Gerekli .env anahtarları (Gmail App Password):
#   EMAIL_USER=<gonderen@gmail.com>
#   EMAIL_APP_PASSWORD=<16 haneli app password>
#   EMAIL_TO=<alici@gmail.com>   (opsiyonel; yoksa EMAIL_USER'a gider)
#
set -uo pipefail
export HOME=/root
REPO=/root/parafomo
cd "$REPO" || exit 0

set -a; . "$REPO/.env" 2>/dev/null; set +a

USER_ADDR="${EMAIL_USER:-}"
PASS="${EMAIL_APP_PASSWORD:-}"
TO="${EMAIL_TO:-${EMAIL_USER:-}}"

if [ -z "$USER_ADDR" ] || [ -z "$PASS" ]; then
  echo "[mail] UYARI: EMAIL_USER/EMAIL_APP_PASSWORD .env'de yok — e-posta gönderilemedi."
  echo "[mail] Gmail App Password oluşturup .env'e ekleyin (EMAIL_USER=, EMAIL_APP_PASSWORD=, EMAIL_TO=)."
  exit 0
fi

BODY_FILE="$REPO/agent/state/report.md"
[ -f "$BODY_FILE" ] || { echo "[mail] rapor dosyası yok (beyin oturumu yarım kalmış olabilir)"; exit 0; }

SUBJECT="🤖 ParaFOMO Gece Raporu — $(date -u +%Y-%m-%d)"

python3 - "$USER_ADDR" "$PASS" "$TO" "$SUBJECT" "$BODY_FILE" <<'PY'
import sys, smtplib, ssl
from email.mime.text import MIMEText
user, pw, to, subject, body_file = sys.argv[1:6]
body = open(body_file, encoding="utf-8").read()
msg = MIMEText(body, "plain", "utf-8")
msg["Subject"] = subject
msg["From"] = user
msg["To"] = to
ctx = ssl.create_default_context()
try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
        s.login(user, pw)
        s.sendmail(user, [t.strip() for t in to.split(",")], msg.as_string())
    print("[mail] gönderildi ->", to)
except Exception as e:
    print("[mail] HATA:", e)
    sys.exit(1)
PY
