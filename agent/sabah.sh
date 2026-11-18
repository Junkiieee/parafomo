#!/usr/bin/env bash
#
# Parafomo SABAH RUTİNİ — oturumdan bağımsız (Kaan 2026-11-17: "kapanmamasını nasıl sağlarız").
# Önceden Claude Code oturumundaki 7 günlük cron'a bağlıydı; oturum kapanınca ya da süre dolunca dururdu.
# Artık sistem cron'u çalıştırır:  37 4 * * * /root/parafomo/agent/sabah.sh >> /root/parafomo/logs/sabah.log 2>&1
# (Eski gece ajanı agent/run.sh 2026-11-18'de emekli oldu; günlük tek Claude koşusu budur.)
#
# İstem: agent/prompts/sabah.md + sonuna SAĞLIK bölümü (agent/health.py --sabah → agent/state/saglik.md)
# İzinler: agent/allowed-tools.txt (acceptEdits, listede olmayan komut reddedilir)
#          agent/denied-tools.txt  (izin listesinden ÖNCE gelir: push/reset/rebase, sır dosyası okuma…)
# Çalışma dizinleri: repo + /root/parafomo-data (plan.json, senaryo kararları, trend dosyaları)
# Hata olursa Kaan'a tek uyarı (agent/notify.py, anahtar sabah-hata, günde en çok bir).
# Operasyonel sağlık sorunu varsa (geciken hat, site/API düştü, kuyruk boşalıyor…) ayrı tek uyarı: anahtar saglik.
#   agent/sabah.sh [--dry]
set -uo pipefail
export HOME=/root
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
REPO=/root/parafomo
VPY=/root/.venvs/parafomo/bin/python
cd "$REPO" || exit 0
. "$REPO/scripts/lib/gitsync.sh"
[ -f /root/.config/parafomo/claude.env ] && { set -a; . /root/.config/parafomo/claude.env; set +a; }

MODEL="${SABAH_MODEL:-opus}"; EFFORT="${SABAH_EFFORT:-medium}"; BUDGET="${SABAH_BUDGET:-12}"
# Duvar saati tavanı (sn): ağır-iş kilidini tutarken sonsuza dek takılmasın (daily-content.sh 06:00'da bu kilidi bekler)
TIMEOUT="${SABAH_TIMEOUT:-5400}"
LOGDIR="$REPO/agent/logs"; STATE="$REPO/agent/state"; mkdir -p "$LOGDIR" "$STATE"
STAMP="$(date -u +%Y%m%d-%H%M)"
OUT="$LOGDIR/sabah-$STAMP.json"; ERR="$LOGDIR/sabah-$STAMP.err"
PROMPT="$STATE/sabah-prompt.md"; SAGLIK="$STATE/saglik.md"
mapfile -t ALLOWED < <(grep -vE '^\s*(#|$)' agent/allowed-tools.txt)
DENIED=()
[ -f agent/denied-tools.txt ] && mapfile -t DENIED < <(grep -vE '^\s*(#|$)' agent/denied-tools.txt)
COMMON=(--model "$MODEL" --effort "$EFFORT" --output-format json
        --permission-mode acceptEdits --allowedTools "${ALLOWED[@]}")
[ ${#DENIED[@]} -gt 0 ] && COMMON+=(--disallowedTools "${DENIED[@]}")
COMMON+=(--add-dir /root/parafomo-data --disable-slash-commands)
echo "=================================================="
echo "[$(date -u '+%F %T UTC')] Sabah rutini — model=$MODEL effort=$EFFORT tavan=\$$BUDGET süre≤$((TIMEOUT / 60))dk (${#ALLOWED[@]} izinli, ${#DENIED[@]} yasak kural)"
if [ "${1:-}" = "--dry" ]; then
  echo "[dry] git: main + git_sync · sağlık: $VPY agent/health.py --sabah $SAGLIK"
  echo "[dry] timeout --kill-after=60 $TIMEOUT claude -p ${COMMON[*]:0:6} … --add-dir /root/parafomo-data … --max-budget-usd $BUDGET < $PROMPT (sabah.md + saglik.md)"
  exit 0
fi

# Ağır iş kilidi (ajan, günlük içerik, render): en çok 40 dk bekle, sonra atla
exec 8>"$REPO/.git/parafomo-heavy.lock"
if ! flock -w 2400 8; then
  echo "[sabah] başka ağır iş 40 dk'dır sürüyor — bugün atlandı"
  "$VPY" agent/notify.py alert --key sabah-hata --subject "parafomo: sabah rutini atlandı (kilit)" \
    --body "Başka bir ağır iş 40 dakikadır sürüyordu; sabah rutini bugün çalışmadı." >/dev/null 2>&1 || true
  exit 0
fi

# Dal bekçisi (eski run.sh'tan; 2026-07-19 olayı: cron'lar yanlış dala commit'ledi, içerik canlıya gitmedi).
# deploy-push.sh `main`i push'lar → başka daldaki commit "yayında" sanılır ama yayına çıkmaz.
cur="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
if [ "$cur" != "main" ]; then
  echo "[!] çalışma dizini '$cur' dalında → main'e dönülüyor"
  if ! git_locked git checkout -q main; then
    echo "[sabah] main'e dönülemedi — bugün atlandı"
    "$VPY" agent/notify.py alert --key sabah-hata --subject "parafomo: sabah rutini atlandı (dal '$cur')" \
      --body "$(printf "/root/parafomo '%s' dalında ve 'git checkout main' başarısız oldu (muhtemelen commit'lenmemiş çakışan değişiklik).\nSabah rutini bugün ÇALIŞMADI. Düzelt: cd /root/parafomo && git status" "$cur")" >/dev/null 2>&1 || true
    exit 0
  fi
fi
git_sync || echo "[uyarı] git sync başarısız (devam)"

# Sağlık (token'sız): hatlar, disk, git, site/API, yayın kuyruğu, bayat veri → istemin sonuna.
# Operasyonel sorun varsa Kaan'a tek uyarı (bayat veri/SEO uyarı DEĞİL: onları bu koşu kapatır).
ALARM="$(timeout 300 "$VPY" agent/health.py --sabah "$SAGLIK" 2>"$STATE/saglik.err")"; HRC=$?
if [ $HRC -ne 0 ]; then
  ALARM="agent/health.py çalışmadı (çıkış $HRC): $(tail -3 "$STATE/saglik.err" | tr '\n' ' ')"
  printf '_agent/health.py çalışmadı (çıkış %s) — sağlık tablosu yok; logs/ altındaki logları elle kontrol et._\n' "$HRC" > "$SAGLIK"
fi
if [ -n "$ALARM" ]; then
  echo "[sağlık] $(printf '%s' "$ALARM" | tr '\n' ';')"
  "$VPY" agent/notify.py alert --key saglik --subject "parafomo: üretim sağlığı — $(printf '%s\n' "$ALARM" | wc -l) sorun" \
    --body "$(printf '%s\n\nAyrıntı: /root/parafomo/agent/state/saglik.md (sabah rutini de bunu okuyup düzeltmeye çalışır).' "$ALARM")" >/dev/null 2>&1 || true
else
  echo "[sağlık] operasyonel sorun yok"
fi
{
  cat agent/prompts/sabah.md
  printf '\n\n=== SAĞLIK — %s (agent/health.py; dosya: agent/state/saglik.md) ===\n' "$(date -u '+%F %H:%M UTC')"
  cat "$SAGLIK" 2>/dev/null
} > "$PROMPT"

timeout --kill-after=60 "$TIMEOUT" claude -p "${COMMON[@]}" --max-budget-usd "$BUDGET" < "$PROMPT" > "$OUT" 2> "$ERR"
RC=$?
OZET="$("$VPY" -c "import json,sys
try:
    d=json.load(open('$OUT')); print(('HATA ' if d.get('is_error') else '')+str(d.get('result',''))[-1500:]); print('maliyet: \$%.2f, tur: %s' % (d.get('total_cost_usd') or 0, d.get('num_turns')))
    den=d.get('permission_denials') or []
    if den:
        print('izin reddi: %d — ilk 3: %s' % (len(den), ' | '.join(str((x.get('tool_input') or {}).get('command') or x.get('tool_name'))[:120].replace(chr(10),' ') for x in den[:3])))
except Exception as e: print('çıktı okunamadı:', e)")"
echo "$OZET"
[ $RC -eq 124 ] && OZET="$(printf 'ZAMAN AŞIMI: %s dk dolunca durduruldu.\n%s' "$((TIMEOUT / 60))" "$OZET")"
if [ $RC -ne 0 ] || echo "$OZET" | head -1 | grep -q '^HATA\|okunamadı'; then
  "$VPY" agent/notify.py alert --key sabah-hata --subject "parafomo: sabah rutini hata verdi" \
    --body "$(printf 'agent/sabah.sh çıkış=%s\n\n%s\n\nhata günlüğü: %s\n%s' "$RC" "$OZET" "$ERR" "$(tail -15 "$ERR")")" >/dev/null 2>&1 || true
fi
echo "[$(date -u '+%F %T UTC')] Sabah rutini bitti (çıkış $RC)"
