#!/usr/bin/env bash
#
# ParaFOMO — aylık TÜİK verisi: kira artış oranı + TÜFE serisi (emekli zammı) (TÜİK ~3'ü açıklar; TEDB duyurusu) → data/kira-artis-2026.json.
# Oran değiştiyse commit + build kapılı push (Cloudflare deploy → /kira-artis-orani-hesaplama tazelenir).
# Cron: her ayın 3-10'u 08:20 / 12:20 UTC + açıklama günü 10 dakikada bir scripts/release-watch.py üzerinden
# (açıklama 10:00 TSİ = 07:00 UTC). Veri değişince: canlı blog yazıları (scripts/live-posts.py) → commit →
# build kapılı deploy → sitemap canlıya çıkınca IndexNow + GSC sitemap (Google/Bing yeniden tarasın).
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
# Aynı gün Yİ-ÜFE + yeniden değerleme oranı tahmini (/yeniden-degerleme-orani, /mtv-hesaplama)
python3 "$REPO/scripts/yeniden-degerleme-update.py"
# Aylık kartların OG görselleri (stat değiştiyse yazılır)
python3 "$REPO/scripts/og-images.py" --only kira-artis-orani-hesaplama,enflasyon-takvimi,emekli-zammi-hesaplama,memur-zammi-hesaplama,yeniden-degerleme-orani,mtv-hesaplama || true
# Rakamları bu verilerden gelen blog yazıları (content-templates/blog/*.md.j2) — elle düzenlenmişse ezmez, uyarır
python3 "$REPO/scripts/live-posts.py" || true
# TÜİK günü sonuç Short'u (enflasyon + kira tavanı; Kasım'da yeniden değerleme, Ocak/Temmuz'da emekli zammı)
setsid nohup python3 "$REPO/scripts/event-short.py" >> "$REPO/logs/event-short.log" 2>&1 < /dev/null &
# Yalnız şablondan üretilen yazılar commit'lenir (başka hattın yarım yazısı karışmasın)
LIVE=""
for t in "$REPO"/content-templates/blog/*.md.j2; do
  [ -e "$t" ] || continue
  b=$(basename "$t" .md.j2); LIVE="$LIVE src/content/blog/$b.md"
done
PATHS="data/kira-artis-2026.json data/tufe-aylik.json data/yeniden-degerleme.json public/og data/live-posts-state.json$LIVE"
# shellcheck disable=SC2086
if [ -z "$(git status --porcelain $PATHS)" ]; then
  exit 0
fi
# shellcheck disable=SC2086
git_add_commit "veri: kira artış / TÜFE / Yİ-ÜFE-yeniden değerleme güncellendi (otomatik $(date -u '+%F %H:%M UTC'))" $PATHS \
  || { echo "commit başarısız"; exit 0; }
# app.parafomo.com (portföy reel getiri + /birikim) TÜFE'yi kendi kopyasından okur — yeni ay gelince oraya da dağıt
bash "$REPO/scripts/deploy-app.sh" || echo "UYARI: app veri dağıtımı başarısız"
if bash "$REPO/scripts/deploy-push.sh"; then
  # Cloudflare 1-3 dk'da yayınlar; yeni sitemap (bugünkü lastmod) canlıya çıkınca arama motorlarına haber ver
  if python3 "$REPO/scripts/wait-live.py" "https://parafomo.com/sitemap-0.xml" --contains "<lastmod>$(date -u '+%F')" --timeout 600; then
    python3 "$REPO/scripts/indexnow.py" || true
    /root/.venvs/parafomo/bin/python "$REPO/scripts/gsc-sitemap.py" --force || true
  else
    echo "UYARI: yeni sitemap 10 dk içinde canlıya çıkmadı — IndexNow/GSC bildirimi learn-daily'ye kaldı"
  fi
fi
