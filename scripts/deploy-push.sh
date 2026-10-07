#!/usr/bin/env bash
#
# ParaFOMO — BUILD KAPILI PUSH (ajanın ve elle çalışmanın tek güvenli deploy komutu).
# Push'lanmamış commit varsa: npm run build GEÇERSE kilitli push (→ Cloudflare otomatik deploy).
# Build kırıksa push YAPMAZ ve hatanın son satırlarını basar.
#
# Kullanım: bash scripts/deploy-push.sh
set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"
REPO="/root/parafomo"
cd "$REPO" || exit 1
. "$REPO/scripts/lib/gitsync.sh"

if ! [ -n "$(git log origin/main..HEAD --oneline 2>/dev/null)" ]; then
  echo "[deploy] push edilecek yerel commit yok"; exit 0
fi
if [ -n "$(git status --porcelain -- src astro.config.mjs package.json 2>/dev/null)" ]; then
  echo "[deploy] UYARI: src/ altında commit'lenmemiş değişiklik var — build onları da içerir; önce commit'le"
fi
echo "[deploy] build..."
if ! npm run build > "$REPO/logs/deploy-build.log" 2>&1; then
  echo "[deploy] BUILD KIRIK — push YAPILMADI. Son satırlar:"
  tail -20 "$REPO/logs/deploy-build.log"
  exit 1
fi
if git_push_retry main; then
  echo "[deploy] push tamam — Cloudflare 1-3 dk içinde yayınlar ($(git log -1 --format='%h %s'))"
else
  echo "[deploy] push başarısız"; exit 1
fi
