#!/usr/bin/env bash
#
# ParaFOMO Büyüme Ajanı — gece raporu + kullanıcı görevlerini Telegram'a gönderir.
# Kaynak: agent/state/report.md + agent/state/tasks-for-user.md
#
set -uo pipefail
export HOME=/root
REPO=/root/parafomo
cd "$REPO" || exit 0

ENV_FILE="$REPO/.env"
[ -f "$ENV_FILE" ] || { echo "[tg] .env yok"; exit 0; }
BOT="$(grep -E '^TELEGRAM_BOT_TOKEN=' "$ENV_FILE" | head -1 | cut -d= -f2-)"
CHAT="$(grep -E '^TELEGRAM_CHAT_ID=' "$ENV_FILE" | head -1 | cut -d= -f2-)"
[ -n "$BOT" ] && [ -n "$CHAT" ] || { echo "[tg] kimlik yok"; exit 0; }

REPORT="$(cat agent/state/report.md 2>/dev/null || echo '(rapor üretilmedi — beyin oturumu yarım kalmış olabilir)')"
TASKS="$(cat agent/state/tasks-for-user.md 2>/dev/null || echo '(görev dosyası yok)')"

MSG="🤖 *ParaFOMO Büyüme Ajanı — Gece Raporu* ($(date -u +%Y-%m-%d))

${REPORT}

━━━━━━━━━━
📋 *Senin görevlerin (bugün):*
${TASKS}"

# Telegram mesaj sınırı ~4096 karakter → güvenli kes.
MSG="$(printf '%s' "$MSG" | cut -c1-3900)"

curl -sS -X POST "https://api.telegram.org/bot${BOT}/sendMessage" \
  --data-urlencode "chat_id=${CHAT}" \
  --data-urlencode "text=${MSG}" \
  --data-urlencode "parse_mode=Markdown" \
  -o /dev/null -w '[tg] HTTP %{http_code}\n' \
  || echo "[tg] gönderim başarısız"
