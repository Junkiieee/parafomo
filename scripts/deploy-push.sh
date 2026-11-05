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
# flock: aynı anda iki build dist/'i bozmasın · nice: sunucudaki diğer işler önce gelsin
# Log kilit ALINDIKTAN sonra açılır (bekleyen iş, çalışan build'in logunu kesmesin); kilit zaman aşımı (75)
# "build kırık" değildir → sahte alarm maili yok, push sonraki çalışmaya kalır.
flock -E 75 -w 600 /tmp/parafomo-build.lock sh -c 'nice -n 10 npm run build > "$1" 2>&1' _ "$REPO/logs/deploy-build.log"
rc=$?
if [ "$rc" -eq 75 ]; then
  echo "[deploy] build kilidi 10 dk'da boşalmadı (başka build sürüyor) — push YAPILMADI, sonraki çalışma dener"; exit 1
fi
if [ "$rc" -ne 0 ]; then
  echo "[deploy] BUILD KIRIK — push YAPILMADI. Son satırlar:"
  tail -20 "$REPO/logs/deploy-build.log"
  # Kaan'a uyarı (günde bir kez). 2026-11-02: build kırıkken sessiz kalınınca canlı site sabahki sürümde kaldı,
  # SEO denetimi yarım dist'i tarayıp 87 sahte "kırık link" maili attı.
  python3 "$REPO/agent/notify.py" alert --key build-kirik --subject "parafomo: site build KIRIK — push yapılmadı" \
    --body "$(printf 'deploy-push.sh: npm run build geçmedi, push YAPILMADI; canlı site eski sürümde.\n\n%s\n\nDüzelt: hatayı gider, sonra bash scripts/deploy-push.sh' "$(tail -25 "$REPO/logs/deploy-build.log")")" >/dev/null 2>&1 || true
  exit 1
fi
# SEO bekçisi: yeni build'de kırık link / yanlış kanonik vb. KRİTİK varsa göster (push'u engellemez)
# (build kilidi altında: başka bir işin build'i dist/'i boşaltırken taranırsa sahte "kırık link" çıkıyordu)
flock -w 600 /tmp/parafomo-build.lock python3 "$REPO/scripts/seo-audit.py" 2>/dev/null | sed -n '1,12p' | sed 's/^/[deploy] /' || true
# build az önce geçti → gitsync.sh build kapısı ikinci kez build almasın
if SKIP_BUILD_GATE=1 git_push_retry main; then
  echo "[deploy] push tamam — Cloudflare 1-3 dk içinde yayınlar ($(git log -1 --format='%h %s'))"
else
  echo "[deploy] push başarısız"; exit 1
fi
