#!/usr/bin/env bash
# Haftalık bülten — onaylı abonelere gönderir (backend/app/newsletter_send.py).
# Cron: pazartesi 05:30 UTC (08:30 TSİ). ISO hafta kilidi aynı haftada ikinci gönderimi engeller.
# Kullanım: bash scripts/newsletter-send.sh [--dry-run | --to adres | --force]
set -uo pipefail
cd /root/parafomo/backend || exit 1
exec /root/.venvs/parafomo-api/bin/python -m app.newsletter_send "$@"
