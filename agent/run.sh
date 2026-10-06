#!/usr/bin/env bash
#
# ParaFOMO Ajanı v2 — ORKESTRATÖR (gecelik tek giriş noktası).
#
#   agent/run.sh [auto|daily|weekly] [--dry]
#   cron: 0 3 * * * /root/parafomo/agent/run.sh auto >> /root/parafomo/logs/agent.log 2>&1
#
# Akış: kilit → mod seç → git sync → brief (token'sız) → kota kapısı → claude -p
#       (oturum limiti ≤4 sa ise bekle + --resume) → artık temizliği + build kapısı + push
#       → koşu kaydı → e-posta.
#
# İZİN MODELİ (v1'den farkı): izin atlama YOK. Ajan acceptEdits modunda ve yalnız
# agent/allowed-tools.txt'deki araç/komutlarla çalışır; listede olmayan komut otomatik
# reddedilir (headless'ta soru sorulmaz). Yetki genişletmek = o dosyaya satır eklemek.
#
# Modlar (v1'den farkı: her gece Opus yerine haftada bir Opus):
#   weekly — Stratejist: skor kartı, bahis kararları, haftalık plan, dersleri yeniden yaz.
#            Varsayılan opus/high, tavan $20. Perşembe (haftalık kota sıfırlamasından sonra).
#   daily  — Operatör: sağlık → plandaki sıradaki görevi uçtan uca bitir → kısa rapor.
#            Varsayılan opus/medium, tavan $8 (Max 5x, 2026-10-06).
# Knob'lar (env): AGENT_{DAILY,WEEKLY}_{MODEL,EFFORT,BUDGET}, AGENT_WEEKLY_DOW (4=Perş.)
#
set -uo pipefail
export HOME=/root
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

REPO=/root/parafomo
VPY=/root/.venvs/parafomo/bin/python
cd "$REPO" || exit 0
. "$REPO/scripts/lib/gitsync.sh"

MODE="auto"; DRY=0
for a in "$@"; do
  case "$a" in
    --dry) DRY=1 ;;
    auto|daily|weekly) MODE="$a" ;;
  esac
done

STATE="$REPO/agent/state"; LOGDIR="$REPO/agent/logs"
mkdir -p "$STATE" "$LOGDIR"
# Opsiyonel uzun ömürlü token (claude setup-token) — OAuth süresi dolma sorununun kalıcı çözümü
[ -f /root/.config/parafomo/claude.env ] && { set -a; . /root/.config/parafomo/claude.env; set +a; }

# Tek kopya + ağır-iş kilidi (daily-content.sh bunu bekler; bakım git hijyenini atlar)
exec 8>"$REPO/.git/parafomo-heavy.lock"
if ! flock -n 8; then
  echo "[agent] başka bir ajan/ağır iş sürüyor — çıkılıyor"; exit 0
fi

[ "$MODE" = "auto" ] && MODE="$("$VPY" agent/runlog.py pick-mode)"
if [ "$MODE" = "weekly" ]; then
  MODEL="${AGENT_WEEKLY_MODEL:-opus}"; EFFORT="${AGENT_WEEKLY_EFFORT:-high}"; BUDGET="${AGENT_WEEKLY_BUDGET:-20}"
else
  MODEL="${AGENT_DAILY_MODEL:-opus}"; EFFORT="${AGENT_DAILY_EFFORT:-medium}"; BUDGET="${AGENT_DAILY_BUDGET:-8}"
fi
STAMP="$(date -u +%Y%m%d-%H%M)"
echo "=================================================="
echo "[$(date -u '+%F %T UTC')] Ajan başladı — mod=$MODE model=$MODEL effort=$EFFORT tavan=\$$BUDGET dry=$DRY"

# 1) Repo: main'de ve güncel
cur="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
if [ "$cur" != "main" ]; then
  echo "[!] dal '$cur' → main'e dönülüyor"; git_locked git checkout -q main || true
fi
git_sync || echo "[uyarı] git sync başarısız (devam)"

# 2) Brief (token'sız) + prompt
"$VPY" agent/brief.py --mode "$MODE" > "$STATE/brief.md" 2> "$LOGDIR/brief-$STAMP.err" \
  || echo "[uyarı] brief kısmi üretildi"
PROMPT="$STATE/prompt.md"
{
  cat agent/prompts/core.md; echo
  cat "agent/prompts/$MODE.md"; echo
  echo "=== BRIEF — $(date -u '+%F %H:%M UTC') ==="
  cat "$STATE/brief.md"
} > "$PROMPT"
echo "[agent] prompt: $(wc -c < "$PROMPT") bayt (~$(( $(wc -c < "$PROMPT") / 4 )) token)"

# İzinli araçlar (yorum/boş satır hariç)
mapfile -t ALLOWED < <(grep -vE '^\s*(#|$)' agent/allowed-tools.txt)

if [ "$DRY" = 1 ]; then
  echo "[agent] --dry: beyin çağrılmadı. Prompt: $PROMPT · izinli araç kuralı: ${#ALLOWED[@]}"; exit 0
fi

# 3) Kota kapısı: sert limit sürüyorsa ve ≤3 saatte bitecekse bekle, değilse atla
until_ts="$("$VPY" -c "import sys; sys.path.insert(0,'scripts/lib'); import llm; u=llm.blocked_until(); print(int(u.timestamp()) if u else 0)")"
if [ "${until_ts:-0}" -gt 0 ]; then
  wait_s=$(( until_ts - $(date +%s) + 180 ))
  if [ "$wait_s" -le 10800 ]; then
    echo "[agent] Claude kotası dolu — $(( wait_s / 60 )) dk bekleniyor"; sleep "$wait_s"
  else
    echo "[agent] Claude kotası $(( wait_s / 3600 )) saat daha dolu — bu gece atlandı"
    "$VPY" agent/runlog.py skip --mode "$MODE" --model "$MODEL" --outcome "quota_skip" \
      --reason "Claude kotası dolu ($(date -u -d @"$until_ts" '+%d %b %H:%M UTC')'e kadar)"
    "$VPY" agent/notify.py report
    exit 0
  fi
fi

# 4) Beyin. Ajanın değiştirdiği dosyaları ayırt etmek için önce kirli listeyi al.
BEFORE="$STATE/dirty-before.txt"
git status --porcelain | sed 's/^...//' | sort > "$BEFORE"
"$VPY" agent/runlog.py start --mode "$MODE" --model "$MODEL" --effort "$EFFORT"
OUT="$LOGDIR/run-$STAMP.json"
COMMON=(--model "$MODEL" --effort "$EFFORT" --output-format json
        --permission-mode acceptEdits --allowedTools "${ALLOWED[@]}"
        --strict-mcp-config --disable-slash-commands)
echo "[agent] beyin çalışıyor..."
claude -p "${COMMON[@]}" --max-budget-usd "$BUDGET" < "$PROMPT" > "$OUT" 2> "$LOGDIR/run-$STAMP.err"
RES="$("$VPY" agent/runlog.py finish --json "$OUT" --no-log)"
IFS=$'\t' read -r OUTCOME SID RESET COST <<< "$RES"
echo "[agent] sonuç: $OUTCOME (maliyet \$$COST)"

# 4b) 5 saatlik oturum limitine takıldıysa: ≤4 saatte sıfırlanacaksa bekle ve KALDIĞI YERDEN devam et
if [ "$OUTCOME" = "session_limit" ] && [ "$SID" != "-" ] && [ "${RESET:-0}" -gt 0 ]; then
  wait_s=$(( RESET - $(date +%s) + 240 ))
  if [ "$wait_s" -gt 0 ] && [ "$wait_s" -le 14400 ]; then
    echo "[agent] oturum limiti — $(( wait_s / 60 )) dk sonra devam edilecek (session $SID)"
    sleep "$wait_s"
    "$VPY" -c "import sys; sys.path.insert(0,'scripts/lib'); import llm; llm.write_status('ok')"
    OUT2="$LOGDIR/run-$STAMP-resume.json"
    REMAIN="$("$VPY" -c "print(max(0.5, round(float('$BUDGET') - float('${COST:-0}' or 0), 2)))")"
    echo "Claude kotası sıfırlandı. Kaldığın yerden devam et: yarım görevi bitir (build → commit), sonra agent/state/report.md'yi yaz." \
      | claude -p --resume "$SID" "${COMMON[@]}" --max-budget-usd "$REMAIN" > "$OUT2" 2>> "$LOGDIR/run-$STAMP.err"
    RES="$("$VPY" agent/runlog.py finish --json "$OUT2" --prev-cost "${COST:-0}" --no-log)"
    IFS=$'\t' read -r OUTCOME SID RESET COST <<< "$RES"
    echo "[agent] devam sonucu: $OUTCOME (toplam maliyet \$$COST)"
  fi
fi

# 5) Artık temizliği: ajanın commit'lemeden bıraktığı dosyalar → stash (sonraki koşu inceler).
#    Yalnız bu koşuda kirlenen yollar; diğer cron'ların dosyalarına dokunulmaz.
git status --porcelain | sed 's/^...//' | sort > "$STATE/dirty-after.txt"
mapfile -t LEFT < <(comm -13 "$BEFORE" "$STATE/dirty-after.txt" \
  | grep -vE '^(public/social/|logs/|data/learning/|agent/state/|agent/logs/|dist/)' || true)
if [ "${#LEFT[@]}" -gt 0 ]; then
  echo "[agent] commit'lenmemiş ajan işi stash'leniyor: ${LEFT[*]}"
  git_locked git stash push -u -q -m "agent-wip-$STAMP" -- "${LEFT[@]}" \
    || echo "[uyarı] stash başarısız — dosyalar çalışma dizininde kaldı"
fi

# 6) Build kapısı + push: push'lanmamış commit varsa site build'i GEÇMEDEN gönderme
if git log origin/main..HEAD --oneline 2>/dev/null | grep -q .; then
  if npm run build > "$LOGDIR/build-$STAMP.log" 2>&1; then
    git_push_retry main && echo "[agent] push tamam (Cloudflare deploy tetiklendi)"
  else
    echo "[!] BUILD KIRIK — push YAPILMADI (log: $LOGDIR/build-$STAMP.log)"
    "$VPY" agent/notify.py alert --key build-broken \
      --subject "⚠️ ParaFOMO: ajan commit'leri build'i kırıyor — push durduruldu" \
      --body "Ajanın commit'leri yerelde duruyor, canlıya gitmedi. Log: $LOGDIR/build-$STAMP.log
Son satırlar:
$(tail -25 "$LOGDIR/build-$STAMP.log")"
    OUTCOME="build_broken"
  fi
fi

# 7) Koşu kaydı + e-posta
"$VPY" - "$OUTCOME" <<'PY'
import sys
sys.path.insert(0, "/root/parafomo/agent")
import runlog
st = runlog.read_status()
if sys.argv[1] == "build_broken":
    st["outcome"] = "build_broken"; st["message"] = "commit'ler build'i kırdı, push yapılmadı"
runlog.write_status(st)
runlog.append_run(st)
PY
"$VPY" agent/notify.py report
echo "[$(date -u '+%F %T UTC')] Ajan bitti — $OUTCOME"
