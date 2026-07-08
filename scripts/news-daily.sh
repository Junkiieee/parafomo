#!/usr/bin/env bash
#
# ParaFOMO — GÜNDEM yakalayıcı otomasyon (ekonomik takvim → viral news_reaction).
# Akış: takvimi tazele → günü gelen High-impact olay var mı (calendar-trigger.py) →
#       varsa ve o gün işlenmemişse → viral-daily.sh --format news_reaction --topic ...
#       → başarıyla üretilirse günü 'mark' et (aynı gün tekrar tetiklenmez).
#
# Kanıt: gündem-tepki videoları eğitici "nedir" videolarının 5-10 katı açılış yapıyor.
# Bu betik viral hattan AYRI çalışır ama aynı viral-daily.sh motorunu kullanır.
#
# Cron örneği (her sabah 07:45 UTC — içerik/veri tazelendikten sonra, viral slotlarından önce):
#   45 7 * * * /root/parafomo/scripts/news-daily.sh >> /root/parafomo/logs/news.log 2>&1
#
# Not: veri günün ilerleyen saatinde açıklansa bile "bugün gündemde ne var" reaksiyonu
# sabah yayınlanır (arama/merak o gün zirvede). Pencereyi öne almak için WINDOW ayarla.

set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"

REPO="/root/parafomo"
VPY="/root/.venvs/parafomo/bin/python"
cd "$REPO" || { echo "HATA: repo yok"; exit 1; }

WINDOW="${WINDOW:-0}"   # 0 = yalnız bugün; artırırsan olayı 1-2 gün önden yakalar

echo "=================================================="
echo "[$(date -u '+%F %T UTC')] Gündem yakalayıcı başladı (window=$WINDOW)"

set -a; . "$REPO/.env"; set +a
{ git fetch origin main && git rebase --autostash origin/main; } || echo "UYARI: pull başarısız (devam)"

# 1) Takvimi tazele (best-effort; başarısız olursa mevcut json ile devam)
"$VPY" "$REPO/scripts/fetch-economic-calendar.py" 2>&1 | sed 's/^/    [cal] /' || echo "UYARI: takvim tazelenemedi (mevcut veri kullanılacak)"

# 2) Günü gelen, işlenmemiş High-impact olayı seç → "<tarih>\t<konu>"
LINE="$("$VPY" "$REPO/scripts/calendar-trigger.py" next --window "$WINDOW")"
if [ -z "$LINE" ]; then
  echo "[i] Bugün için tetiklenecek yüksek-etkili gündem yok — çıkılıyor."
  exit 0
fi
DATE="${LINE%%$'\t'*}"
TOPIC="${LINE#*$'\t'}"
echo "[*] Gündem yakalandı ($DATE): $TOPIC"

# 3) Viral news_reaction videosunu üret (viral-daily.sh tüm hattı yürütür: senaryo →
#    video → YouTube public → Telegram → commit). Slot deneyi devre dışı (--at yok = manual).
if "$REPO/scripts/viral-daily.sh" --format news_reaction --topic "$TOPIC"; then
  # 4) Yalnız başarıda işaretle → aynı gün tekrar tetiklenmez
  "$VPY" "$REPO/scripts/calendar-trigger.py" mark "$DATE"
  echo "[$(date -u '+%F %T UTC')] Tamamlandı: gündem videosu üretildi ($DATE)"
else
  echo "HATA: gündem videosu üretilemedi ($DATE) — işaretlenmedi, yarın tekrar denenecek"
  exit 2
fi
