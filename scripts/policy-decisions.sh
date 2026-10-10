#!/usr/bin/env bash
#
# ParaFOMO — Fed/TCMB faiz kararı (birincil kaynak) → data/fomc-2026.json, data/tcmb-2026.json.
# Bekleyen karar yoksa ağa çıkmaz; karar yazıldıysa commit + build kapılı push (takvim sayfaları tazelenir).
# Cron: TCMB 14:00 TSİ (11:00 UTC), Fed 21:00/22:00 TSİ (18:00/19:00 UTC) → 11:25, 13:25, 19:25, 21:25 UTC.
set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"
REPO="/root/parafomo"
. "$REPO/scripts/lib/gitsync.sh"
cd "$REPO" || exit 1
out=$(python3 "$REPO/scripts/policy-decisions.py" 2>&1); echo "[$(date -u '+%F %T UTC')] $out"
case "$out" in *GÜNCELLENDİ*) ;; *) exit 0 ;; esac
git_sync >/dev/null 2>&1 || echo "UYARI: pull başarısız (devam)"
git_add_commit "veri: faiz kararı eklendi (otomatik $(date -u '+%F %H:%M UTC'))" data/fomc-2026.json data/tcmb-2026.json \
  || { echo "commit başarısız"; exit 0; }
bash "$REPO/scripts/deploy-push.sh"
