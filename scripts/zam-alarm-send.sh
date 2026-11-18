#!/usr/bin/env bash
# Zam alarmı — "zam-alarmi:" etiketli onaylı abonelere açıklama günü tek e-posta (backend/app/zam_alarm_send.py).
# Cron'da DEĞİL: scripts/asgari-ucret-watch.py (asgari ücret açıklanınca) ve scripts/release-watch.py
# (Ocak'ta Aralık TÜFE'si gelince) çağırır. Olay başına tek gönderim (/root/parafomo-data/zam-alarm-state.json).
# GO-LIVE KAPISI: /root/parafomo-data/dash/kontrol.json → "zam_alarm_gonder": true değilse gerçek aboneye GİTMEZ.
# Kullanım: bash scripts/zam-alarm-send.sh --olay asgari-2027 [--dry-run | --to adres | --max N]
set -uo pipefail
cd "$(dirname "$0")/../backend" || exit 1
exec /root/.venvs/parafomo-api/bin/python -m app.zam_alarm_send "$@"
