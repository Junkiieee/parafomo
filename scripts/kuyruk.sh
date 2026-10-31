#!/usr/bin/env bash
# Onaylı yayın kuyruğu cron sarmalayıcısı (scripts/anim/kuyruk.py). Kaan kararı 2026-10-31:
#   gece  : kuyruk.sh uret --adet 2   → 2 aday video (takvim konusu + deney stili), "bekliyor"
#   gündüz: kuyruk.sh yayinla         → Kaan'ın onayladığı sıradaki video YouTube + IG + FB
set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"
REPO="/root/parafomo"
cd "$REPO" || exit 1
set -a; . "$REPO/.env"; set +a
exec 9>/tmp/parafomo-kuyruk.lock
flock -w 3600 9 || { echo "kilit alınamadı"; exit 1; }
echo "[$(date -u '+%F %T UTC')] kuyruk $*"
/root/.venvs/parafomo/bin/python "$REPO/scripts/anim/kuyruk.py" "$@"
