#!/usr/bin/env bash
#
# ParaFOMO — aylık TÜİK verisi: kira artış oranı + TÜFE serisi (emekli zammı) (TÜİK ~3'ü açıklar; TEDB duyurusu) → data/kira-artis-2026.json.
# Oran değiştiyse commit + build kapılı push (Cloudflare deploy → /kira-artis-orani-hesaplama tazelenir).
# Cron: her ayın 3-8'i, 08:20 / 12:20 UTC (açıklama 10:00 TSİ = 07:00 UTC).
set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"
REPO="/root/parafomo"
. "$REPO/scripts/lib/gitsync.sh"
cd "$REPO" || exit 1
echo "[$(date -u '+%F %T UTC')] kira artış güncelleme"
git_sync >/dev/null 2>&1 || echo "UYARI: pull başarısız (devam)"
python3 "$REPO/scripts/kira-artis-update.py"
# Aynı gün TÜFE aylık serisi (emekli zammı sayfası) — TCMB tablosu
python3 "$REPO/scripts/tufe-update.py"
if [ -z "$(git status --porcelain data/kira-artis-2026.json data/tufe-aylik.json)" ]; then
  exit 0
fi
git_add_commit "veri: kira artış oranı / TÜFE güncellendi (otomatik $(date -u '+%F'))" data/kira-artis-2026.json data/tufe-aylik.json \
  || { echo "commit başarısız"; exit 0; }
bash "$REPO/scripts/deploy-push.sh"
