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

# --- Günde tek gönderim kilidi (çift e-posta önlemi) ---
# Hem beyin ajanı hem night-run wrapper notify.sh çağırabilir; kim önce başarıyla
# gönderirse marker konur, aynı UTC günü içindeki ikinci çağrı atlanır.
# Elle yeniden göndermek için: bash agent/notify.sh --force
MARKER="$REPO/agent/state/.mail-sent-$(date -u +%Y-%m-%d)"
if [ "${1:-}" != "--force" ] && [ -f "$MARKER" ]; then
  echo "[mail] bugün ($(date -u +%Y-%m-%d)) rapor zaten gönderildi — atlanıyor (çift önlemi). Zorlamak için: --force"
  exit 0
fi

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
    # Port 465 (SSL) bulut sunucularda genelde engelli → 587 (STARTTLS).
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
        s.ehlo()
        s.starttls(context=ctx)
        s.login(user, pw)
        s.sendmail(user, [t.strip() for t in to.split(",")], msg.as_string())
    print("[mail] gönderildi ->", to)
except Exception as e:
    print("[mail] HATA:", e)
    sys.exit(1)
PY

# Yalnızca gönderim BAŞARILIYSA marker koy (hata olursa sonraki çağrı yeniden dener).
if [ $? -eq 0 ]; then
  : > "$MARKER"
  # eski marker'ları buda (son 7 gün kalsın)
  find "$REPO/agent/state" -maxdepth 1 -name '.mail-sent-*' -type f -mtime +7 -delete 2>/dev/null || true
fi
