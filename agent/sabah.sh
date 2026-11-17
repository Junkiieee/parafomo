#!/usr/bin/env bash
#
# Parafomo SABAH RUTİNİ — oturumdan bağımsız (Kaan 2026-11-17: "kapanmamasını nasıl sağlarız").
# Önceden Claude Code oturumundaki 7 günlük cron'a bağlıydı; oturum kapanınca ya da süre dolunca dururdu.
# Artık sistem cron'u çalıştırır:  37 4 * * * /root/parafomo/agent/sabah.sh >> /root/parafomo/logs/sabah.log 2>&1
#
# İstem: agent/prompts/sabah.md · İzinler: agent/allowed-tools.txt (acceptEdits, listede olmayan komut reddedilir)
# Hata olursa Kaan'a tek uyarı (agent/notify.py, anahtar sabah-hata, günde en çok bir).
#   agent/sabah.sh [--dry]
set -uo pipefail
export HOME=/root
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
REPO=/root/parafomo
cd "$REPO" || exit 0
[ -f /root/.config/parafomo/claude.env ] && { set -a; . /root/.config/parafomo/claude.env; set +a; }

MODEL="${SABAH_MODEL:-opus}"; EFFORT="${SABAH_EFFORT:-medium}"; BUDGET="${SABAH_BUDGET:-12}"
LOGDIR="$REPO/agent/logs"; mkdir -p "$LOGDIR"
STAMP="$(date -u +%Y%m%d-%H%M)"
OUT="$LOGDIR/sabah-$STAMP.json"; ERR="$LOGDIR/sabah-$STAMP.err"
mapfile -t ALLOWED < <(grep -vE '^\s*(#|$)' agent/allowed-tools.txt)
COMMON=(--model "$MODEL" --effort "$EFFORT" --output-format json
        --permission-mode acceptEdits --allowedTools "${ALLOWED[@]}" --disable-slash-commands)
echo "=================================================="
echo "[$(date -u '+%F %T UTC')] Sabah rutini — model=$MODEL effort=$EFFORT tavan=\$$BUDGET (${#ALLOWED[@]} izinli araç)"
if [ "${1:-}" = "--dry" ]; then
  echo "[dry] claude -p ${COMMON[*]:0:6} … --max-budget-usd $BUDGET < agent/prompts/sabah.md"; exit 0
fi

# Ağır iş kilidi (ajan, günlük içerik, render): en çok 40 dk bekle, sonra atla
exec 8>"$REPO/.git/parafomo-heavy.lock"
if ! flock -w 2400 8; then
  echo "[sabah] başka ağır iş 40 dk'dır sürüyor — bugün atlandı"
  /root/.venvs/parafomo/bin/python agent/notify.py alert --key sabah-hata --subject "parafomo: sabah rutini atlandı (kilit)" \
    --body "Başka bir ağır iş 40 dakikadır sürüyordu; sabah rutini bugün çalışmadı." >/dev/null 2>&1 || true
  exit 0
fi

claude -p "${COMMON[@]}" --max-budget-usd "$BUDGET" < agent/prompts/sabah.md > "$OUT" 2> "$ERR"
RC=$?
OZET="$(/root/.venvs/parafomo/bin/python -c "import json,sys
try:
    d=json.load(open('$OUT')); print(('HATA ' if d.get('is_error') else '')+str(d.get('result',''))[-1500:]); print('maliyet: \$%.2f, tur: %s' % (d.get('total_cost_usd') or 0, d.get('num_turns')))
except Exception as e: print('çıktı okunamadı:', e)")"
echo "$OZET"
if [ $RC -ne 0 ] || echo "$OZET" | head -1 | grep -q '^HATA\|okunamadı'; then
  /root/.venvs/parafomo/bin/python agent/notify.py alert --key sabah-hata --subject "parafomo: sabah rutini hata verdi" \
    --body "$(printf 'agent/sabah.sh çıkış=%s\n\n%s\n\nhata günlüğü: %s\n%s' "$RC" "$OZET" "$ERR" "$(tail -15 "$ERR")")" >/dev/null 2>&1 || true
fi
echo "[$(date -u '+%F %T UTC')] Sabah rutini bitti (çıkış $RC)"
