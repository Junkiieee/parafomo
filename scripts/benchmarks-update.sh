#!/usr/bin/env bash
# Kıyas serilerini (USD, gram altın/gümüş, XU100) aylık tazeler, commit'ler ve app'e dağıtır.
# Cron: 10 5 2 * * (ayın 2'si 08:10 TR)
set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
REPO="/root/parafomo"
cd "$REPO" || exit 1
. "$REPO/scripts/lib/gitsync.sh"

git_sync >/dev/null 2>&1 || echo "UYARI: pull başarısız (devam)"

python3 scripts/build-benchmarks.py || { echo "HATA: benchmark üretimi başarısız"; exit 1; }

if [ -n "$(git status --porcelain data/benchmarks.json)" ]; then
  git_add_commit "veri: kıyas serileri güncellendi (otomatik $(date -u '+%F %H:%M UTC'))" data/benchmarks.json
  git_push_retry main || echo "UYARI: push başarısız"
fi

bash scripts/deploy-app.sh
