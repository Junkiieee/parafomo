#!/usr/bin/env bash
#
# ParaFOMO — günlük yazıyı Telegram kanalına (@parafomo) gönderir.
# daily-content.sh tarafından, içerik push edildikten SONRA çağrılır.
# Çift gönderimi önlemek için son gönderilen slug'ı hatırlar.
#
# Tek başına test: scripts/post-telegram.sh
# Zorla yeniden gönder:  scripts/post-telegram.sh --force

set -uo pipefail

REPO="/root/parafomo"
ENV_FILE="$REPO/.env"
LOG_FILE="$REPO/docs/daily-log.md"
STATE_FILE="$REPO/logs/telegram-last.txt"   # logs/ gitignore'lu
SITE="https://parafomo.com"

FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1

# --- .env'den Telegram kimlik bilgilerini yükle ---
if [ ! -f "$ENV_FILE" ]; then echo "[tg] HATA: .env yok"; exit 1; fi
TELEGRAM_BOT_TOKEN="$(grep -E '^TELEGRAM_BOT_TOKEN=' "$ENV_FILE" | head -1 | cut -d= -f2-)"
TELEGRAM_CHAT_ID="$(grep -E '^TELEGRAM_CHAT_ID=' "$ENV_FILE" | head -1 | cut -d= -f2-)"
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
  echo "[tg] HATA: .env içinde TELEGRAM_BOT_TOKEN/CHAT_ID bulunamadı"; exit 1
fi

# --- En yeni yayınlanan yazıyı daily-log.md'den çek ---
# Satır biçimi:  **Yayınlanan yazı:** [Başlık](/blog/slug)
LINE="$(grep -m1 'Yayınlanan yazı' "$LOG_FILE" 2>/dev/null)"
TITLE="$(printf '%s' "$LINE" | sed -n 's/.*\[\(.*\)\](.*/\1/p')"
SLUG="$(printf '%s' "$LINE" | sed -n 's#.*(/blog/\([^)]*\)).*#\1#p')"
if [ -z "$SLUG" ] || [ -z "$TITLE" ]; then
  echo "[tg] HATA: daily-log.md'den yazı ayrıştırılamadı"; exit 1
fi

# --- Çift gönderim kontrolü ---
mkdir -p "$REPO/logs"
LAST="$(cat "$STATE_FILE" 2>/dev/null || true)"
if [ "$FORCE" -eq 0 ] && [ "$LAST" = "$SLUG" ]; then
  echo "[tg] '$SLUG' zaten gönderilmiş, atlanıyor"; exit 0
fi

# --- Açıklamayı yazının frontmatter'ından al ---
POST_FILE="$REPO/src/content/blog/$SLUG.md"
DESC="$(sed -n 's/^description:[[:space:]]*"\(.*\)"[[:space:]]*$/\1/p' "$POST_FILE" 2>/dev/null | head -1)"

URL="$SITE/blog/$SLUG"

# --- HTML escape (Telegram parse_mode=HTML için) ---
esc() { printf '%s' "$1" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g'; }

MSG="📊 <b>$(esc "$TITLE")</b>"
[ -n "$DESC" ] && MSG="$MSG

$(esc "$DESC")"
MSG="$MSG

🔗 <a href=\"$URL\">Yazının tamamını oku</a>

#finans #yatırım #parafomo"

# --- Gönder ---
RESP="$(curl -s --max-time 20 -X POST \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d chat_id="$TELEGRAM_CHAT_ID" \
  -d parse_mode="HTML" \
  -d disable_web_page_preview=false \
  --data-urlencode text="$MSG")"

if printf '%s' "$RESP" | grep -q '"ok":true'; then
  echo "[tg] Gönderildi: $TITLE"
  printf '%s' "$SLUG" > "$STATE_FILE"
else
  echo "[tg] HATA: gönderim başarısız → $RESP"
  exit 2
fi
