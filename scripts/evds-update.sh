#!/usr/bin/env bash
#
# ParaFOMO — TCMB haftalık ağırlıklı ortalama mevduat/kredi faizleri (EVDS) → data/faiz-oranlari.json.
# Yeni hafta geldiyse OG kartları + commit + build kapılı push (/mevduat-faizi-hesaplama, /konut-kredisi-hesaplama,
# /ihtiyac-kredisi-hesaplama, /kredi-hesaplama varsayılan faizleri tazelenir).
# Cron: Perşembe+Cuma 12:40 UTC (TCMB önceki Cuma'nın verisini hafta içinde yayımlar; 2. gün yedek).
set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"
REPO="/root/parafomo"
. "$REPO/scripts/lib/gitsync.sh"
cd "$REPO" || exit 1
echo "[$(date -u '+%F %T UTC')] EVDS faiz güncelleme"
git_sync >/dev/null 2>&1 || echo "UYARI: pull başarısız (devam)"
python3 "$REPO/scripts/evds-rates.py"
python3 "$REPO/scripts/kredi-karti-faiz.py" || true
python3 "$REPO/scripts/og-images.py" --only mevduat-faizi-hesaplama,konut-kredisi-hesaplama,ihtiyac-kredisi-hesaplama,kredi-hesaplama,kredi-karti-faiz-hesaplama || true
if [ -z "$(git status --porcelain data/faiz-oranlari.json data/kredi-karti-faiz.json public/og)" ]; then
  exit 0
fi
git_add_commit "veri: TCMB haftalık mevduat/kredi faizleri (otomatik $(date -u '+%F'))" data/faiz-oranlari.json data/kredi-karti-faiz.json public/og \
  || { echo "commit başarısız"; exit 0; }
bash "$REPO/scripts/deploy-push.sh"
