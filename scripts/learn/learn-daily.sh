#!/usr/bin/env bash
#
# ParaFOMO — öğrenme döngüsü orkestratörü (cron ile günlük çalışır).
# Akış: ledger'ı türet → tüm kanallardan metrik topla → karar üret → Telegram özeti.
# Her adım kendi içinde hataya dayanıklıdır; bir kanal düşse boru hattı durmaz.
#
# Cron örneği (her gün 07:15 UTC — viral/shorts yayınları oturduktan sonra):
#   15 7 * * * /root/parafomo/scripts/learn/learn-daily.sh >> /root/parafomo/logs/learn.log 2>&1

set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"

REPO="/root/parafomo"
VPY="/root/.venvs/parafomo/bin/python"
LEARN="$REPO/scripts/learn"
cd "$REPO" || { echo "HATA: repo yok"; exit 1; }

echo "=================================================="
echo "[$(date -u '+%F %T UTC')] Öğrenme döngüsü başladı"

echo "[1/4] Ledger türetiliyor"
"$VPY" "$LEARN/build_ledger.py" || echo "UYARI: ledger başarısız (devam)"

echo "[2/4] Metrikler toplanıyor"
"$VPY" "$LEARN/metrics_web.py"       || echo "UYARI: web metrik başarısız"
"$VPY" "$LEARN/metrics_instagram.py" || echo "UYARI: ig metrik başarısız"
"$VPY" "$LEARN/metrics_youtube.py"   || echo "UYARI: yt metrik başarısız"
"$VPY" "$LEARN/seo_targets.py"       || echo "UYARI: seo hedefleri başarısız"

echo "[3/4] Karar üretiliyor"
TG=""; [ "${1:-}" = "--telegram" ] && TG="--telegram"
"$VPY" "$LEARN/decide.py" $TG || echo "UYARI: karar üretimi başarısız"

echo "[4/4] Rapor + SEO hedefleri commit ediliyor"
if [ -n "$(git ls-files -u 2>/dev/null)" ]; then
  echo "UYARI: çözülmemiş merge var → commit atlanıyor (dosyalar yine de güncel)"
elif [ -n "$(git status --porcelain docs/learning-report.md src/data/seo-targets.json 2>/dev/null)" ]; then
  git add docs/learning-report.md src/data/seo-targets.json
  git commit -m "öğrenme: günlük rapor + SEO iç-link hedefleri ($(date -u '+%F'))" || true
  git push origin main 2>&1 | sed 's/^/    [push] /' || echo "UYARI: push başarısız"
fi

echo "[$(date -u '+%F %T UTC')] Öğrenme döngüsü tamamlandı"
