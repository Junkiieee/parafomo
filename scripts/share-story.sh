#!/usr/bin/env bash
#
# ParaFOMO — Bir feed kartından Instagram STORY üretip paylaşır.
# Feed postundan ~2-3 dk SONRA çağrılır (içeride bekler).
# Kullanım: share-story.sh <kart_yolu> "<ETİKET>" "<CTA>"
#
set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"
REPO="/root/parafomo"
VENV_PY="/root/.venvs/parafomo/bin/python"
[ -x "$VENV_PY" ] || VENV_PY="python3"
cd "$REPO" || exit 0

CARD="${1:-}"; LABEL="${2:-GÜNCEL}"; CTA="${3:-Detaylar profilde}"
[ -n "$CARD" ] && [ -f "$CARD" ] || { echo "[story] kart yok: $CARD"; exit 0; }

# feed postundan 2-3 dk sonra paylaş
sleep "${STORY_DELAY:-140}"

base=$(basename "$CARD" .jpg)
STORY="public/social/story-${base}.jpg"
"$VENV_PY" "$REPO/scripts/story-card.py" "$CARD" "$STORY" --label "$LABEL" --cta "$CTA" \
  || { echo "[story] üretilemedi"; exit 0; }

# eski story görsellerini buda (>7 gün)
find public/social -name 'story-*.jpg' -type f -mtime +7 -delete 2>/dev/null || true

git add public/social/ 2>/dev/null
if ! git diff --cached --quiet; then
  git commit -m "story: $base" >/dev/null 2>&1
  git push origin main >/dev/null 2>&1 || { echo "[story] push başarısız"; exit 0; }
fi

RAW="https://raw.githubusercontent.com/Junkiieee/parafomo/main/$STORY"
for i in $(seq 1 18); do
  [ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$RAW")" = "200" ] && break
  sleep 10
done
python3 "$REPO/scripts/post-story-instagram.py" "$RAW"
