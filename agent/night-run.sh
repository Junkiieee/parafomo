#!/usr/bin/env bash
#
# ParaFOMO Büyüme Ajanı — GECE KOŞUSU (orchestrator).
#
# Akış: main'i güncelle → token'sız digest üret → beyni (claude -p, tam özerk)
#       çalıştır → rapor + kullanıcı görevlerini Telegram'a gönder.
#
# ZARİF ÇÖKÜŞ: beyin limite/hataya çarparsa bu script 0 döner; mevcut
# deterministik cron'lar tabanı yayınlamaya devam eder → sistem asla tamamen durmaz.
#
# Elle test:   bash agent/night-run.sh --dry     (beyni çağırmaz, sadece digest+prompt hazırlar)
# Gerçek koşu: bash agent/night-run.sh
#
set -uo pipefail
export HOME=/root
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
# root'ta headless araç kullanımı için: bu sunucu ParaFOMO'ya adanmış sandbox ortam.
export IS_SANDBOX=1

REPO=/root/parafomo
cd "$REPO" || { echo "HATA: repo yok"; exit 0; }

DRY=0
[ "${1:-}" = "--dry" ] && DRY=1

STAMP="$(date -u +%Y%m%d-%H%M)"
LOGDIR="$REPO/agent/logs"; mkdir -p "$LOGDIR"
MODEL="${AGENT_MODEL:-claude-sonnet-4-6}"

echo "[night $STAMP] başlıyor (model=$MODEL, dry=$DRY)"

# 1) main'i güncelle (yanlış-dal/çakışma önle)
{ git fetch origin main && git rebase --autostash origin/main; } 2>/dev/null \
  || echo "[uyarı] pull başarısız (devam)"

# 2) Token'sız digest
bash agent/build-digest.sh || echo "[uyarı] digest üretilemedi (devam)"

# 3) Beyin promptu
PROMPT="$(cat agent/growth-agent.md)

=== BUGÜNKÜ DURUM DİGEST'İ ($(date -u +%Y-%m-%d)) ===
$(cat agent/state/digest.md 2>/dev/null)"

if [ "$DRY" = 1 ]; then
  echo "[night] --dry: beyin çağrılmadı. Prompt uzunluğu: $(printf '%s' "$PROMPT" | wc -c) karakter."
  echo "[night] digest: agent/state/digest.md — kontrol et."
  exit 0
fi

# 4) Beyni çalıştır — TAM ÖZERK headless (cron'da izin sorusuna takılmamalı)
#    AGENT_MAX_TURNS ayarlıysa turn tavanı uygulanır (ilk gözetimli koşu / bütçe kontrolü).
TURN_ARGS=()
[ -n "${AGENT_MAX_TURNS:-}" ] && TURN_ARGS=(--max-turns "$AGENT_MAX_TURNS")
echo "[night] beyin başlıyor ${AGENT_MAX_TURNS:+(max-turns=$AGENT_MAX_TURNS)} ..."
claude -p "$PROMPT" \
  --model "$MODEL" \
  --dangerously-skip-permissions \
  "${TURN_ARGS[@]}" \
  < /dev/null \
  > "$LOGDIR/night-$STAMP.log" 2>&1 \
  || echo "[uyarı] beyin oturumu hata/limit ile bitti (zarif çöküş — taban cron'lar sürüyor)"

echo "[night] beyin bitti. Oturum logu: $LOGDIR/night-$STAMP.log"

# 5) Rapor + görev listesini TEK e-posta olarak gönder (Telegram YOK)
bash agent/notify.sh || echo "[uyarı] e-posta bildirimi başarısız"

echo "[night $STAMP] tamamlandı."
