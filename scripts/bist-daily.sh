#!/usr/bin/env bash
#
# ParaFOMO — BIST açılış/kapanış Instagram postu (bu sunucuda cron ile).
# Akış: hafta içi guard -> kart üret -> commit+push -> raw canlı -> IG post.
#
# Cron:
#   15 7  * * 1-5  /root/parafomo/scripts/bist-daily.sh acilis  >> ...
#   20 15 * * 1-5  /root/parafomo/scripts/bist-daily.sh kapanis >> ...
#   (07:15 UTC=10:15 TR açılış · 15:20 UTC=18:20 TR kapanış · Pzt-Cum)
#
set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"

REPO="/root/parafomo"
VENV_PY="/root/.venvs/parafomo/bin/python"
[ -x "$VENV_PY" ] || VENV_PY="python3"
cd "$REPO" || { echo "HATA: repo yok"; exit 1; }

PTYPE="${1:-acilis}"   # acilis | kapanis
FORCE="${2:-}"

# Hafta içi guard (BIST hafta sonu kapalı)
DOW=$(TZ=Europe/Istanbul date +%u)   # 1=Pzt .. 7=Paz
if [ "$FORCE" != "--now" ] && [ "$DOW" -ge 6 ]; then
  echo "[i] Hafta sonu — BIST kapalı, atlanıyor."; exit 0
fi

echo "[$(date -u '+%F %T UTC')] BIST $PTYPE postu başladı"
{ git fetch origin main && git rebase --autostash origin/main; } >/dev/null 2>&1 || echo "UYARI: pull başarısız"

echo "[*] Kart üretiliyor"
"$VENV_PY" "$REPO/scripts/bist-card.py" --type "$PTYPE" 2>&1 | sed 's/^/    [kart] /' || { echo "HATA: kart"; exit 1; }

STAMP=$(TZ=Europe/Istanbul date '+%Y%m%d')
IMG="public/social/bist-${PTYPE}-${STAMP}.jpg"
[ -f "$IMG" ] || { echo "HATA: $IMG yok"; exit 1; }

# eski bist kartlarını buda (>10 gün)
find public/social -name 'bist-*.jpg' -type f -mtime +10 -delete 2>/dev/null || true
rm -f public/social/bist-preview.jpg 2>/dev/null || true

git add public/social/bist-*.jpg 2>/dev/null
if ! git diff --cached --quiet; then
  git commit -m "bist: $PTYPE kartı $STAMP" >/dev/null 2>&1
  git push origin main 2>&1 | sed 's/^/    [push] /' || { echo "HATA: push"; exit 1; }
fi

RAW="https://raw.githubusercontent.com/Junkiieee/parafomo/main/${IMG}"
ok=0
for i in $(seq 1 18); do
  [ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$RAW")" = "200" ] && { ok=1; break; }
  sleep 10
done
[ "$ok" != "1" ] && { echo "HATA: görsel canlı değil"; exit 1; }

echo "[*] Instagram'a postlanıyor"
OUT=$(python3 "$REPO/scripts/post-bist-instagram.py" --type "$PTYPE" 2>&1); echo "$OUT" | sed 's/^/    [ig] /'

# Feed postu yayınlandıysa ~2-3 dk sonra story paylaş
if echo "$OUT" | grep -q "YAYINLANDI"; then
  [ "$PTYPE" = "kapanis" ] && SLBL="BIST KAPANIŞ" || SLBL="BIST AÇILIŞ"
  echo "[*] Story planlandı (~2-3 dk sonra)"
  bash "$REPO/scripts/share-story.sh" "$IMG" "$SLBL" "BIST 100 ve piyasa profilde" 2>&1 | sed 's/^/    [story] /' || true
fi

echo "[$(date -u '+%F %T UTC')] BIST $PTYPE postu tamamlandı"
