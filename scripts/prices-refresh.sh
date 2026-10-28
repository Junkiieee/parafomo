#!/usr/bin/env bash
#
# ParaFOMO — "canlı" fiyat sayfalarını gün içinde tazeler (cron).
# Neden (denetim 2026-10-22): altın/DXY/tahvil verisi yalnız hafta içi 06:00 UTC'de
# (daily-content.sh) yenileniyordu; Cuma fiyatı Pazartesi'ye kadar duruyordu.
# Burada piyasa saatlerinde ve Cumartesi tazelenir; değişiklik yoksa hiçbir şey
# yapmaz, varsa commit + push (Cloudflare otomatik deploy).
#
# Kullanım: prices-refresh.sh [--dry-run]   (--dry-run: veriyi çeker, commit/push yapmaz)
# Cron: 30 8,10,12,14,16 * * 1-6

set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"

REPO="/root/parafomo"
. "$REPO/scripts/lib/gitsync.sh"
cd "$REPO" || { echo "HATA: repo yok"; exit 1; }
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1

echo "[$(date -u '+%F %T UTC')] Fiyat tazeleme başladı"
[ $DRY -eq 1 ] || git_sync >/dev/null 2>&1 || echo "UYARI: pull başarısız (devam)"

python3 "$REPO/scripts/altin-fiyat.py" 2>&1 | sed 's/^/  [altin] /'
python3 "$REPO/scripts/dxy.py" 2>&1 | sed 's/^/  [dxy] /'
python3 "$REPO/scripts/us-tahvil.py" 2>&1 | sed 's/^/  [tahvil] /'

FILES=(data/altin-fiyat.json data/dxy.json data/us-tahvil.json)
if git diff --quiet -- "${FILES[@]}"; then
  echo "  değişiklik yok"
  exit 0
fi
if [ $DRY -eq 1 ]; then
  git diff --stat -- "${FILES[@]}"
  echo "  --dry-run: commit/push yapılmadı"
  exit 0
fi
git_add_commit "fiyat: gün içi tazeleme ($(date -u '+%F %H:%M') UTC)" "${FILES[@]}" || { echo "HATA: commit"; exit 1; }
git_push_retry main && echo "  push tamam (deploy tetiklendi)"
