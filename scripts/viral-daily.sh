#!/usr/bin/env bash
#
# ParaFOMO — günlük VİRAL Shorts otomasyonu (blog→video hattından AYRI).
# Akış: senkronla → günün formatını seç (haftalık rotasyon) → viral senaryo üret
#       (Claude, blog'dan bağımsız) → video üret (senaryo görselleriyle: Wikimedia
#       kişi/yer + Pexels sahne) → YouTube'a PUBLIC yükle → Telegram önizleme →
#       senaryo dosyasını commit+push.
#
# GECE/GÜNDÜZ AYRIMI (token'ı geceye topla):
#   --prepare : SADECE senaryo üret (Claude) + manifest'e yaz + commit, çık. Gece çalışır.
#   --publish : Claude ÇAĞIRMAZ; gece hazırlanan senaryoyu render+upload eder (sıfır token).
#               Hazır senaryo yoksa YEDEK olarak kendi üretir (hat asla durmaz).
#   (mod yoksa: eski hepsi-bir-arada davranış — geriye dönük uyumlu / manuel test.)
#
# Haftalık format rotasyonu (date +%u: 1=Pzt ... 7=Paz):
#   Pzt karşılaştırma · Sal mit · Çar geri-dönük getiri · Per sayı şoku
#   Cum güncel/tepki · Cmt tek kavram · Paz mit (evergreen güçlü)
#
# ZAMAN DİLİMİ DENEYİ: publish cron'unda 6 satır (her aday saat için bir tane), her biri
# --at <i> taşır; yalnız bugünün slotuna (gün_no % 6) denk gelen satır yayınlar.
#   30 0 * * * /root/parafomo/scripts/viral-daily.sh --prepare >> /root/parafomo/logs/viral.log 2>&1
#   0  5 * * * /root/parafomo/scripts/viral-daily.sh --publish --at 0 >> /root/parafomo/logs/viral.log 2>&1
#   ... (--at 1..5 diğer saatlerde) ...

set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"

REPO="/root/parafomo"
VPY="/root/.venvs/parafomo/bin/python"
cd "$REPO" || { echo "HATA: repo yok"; exit 1; }
. "$REPO/scripts/lib/gitsync.sh"

# .env (PEXELS, TELEGRAM)
set -a; . "$REPO/.env"; set +a

# 1) Senkronla
{ git fetch origin main && git rebase --autostash origin/main; } || echo "UYARI: pull başarısız (devam)"

# Argümanlar: --prepare | --publish | --at N | --format X | --topic "..."
MODE="full"; SLOT_AT=""; FORMAT_OVERRIDE=""; TOPIC=""
while [ $# -gt 0 ]; do
  case "$1" in
    --prepare) MODE="prepare"; shift ;;
    --publish) MODE="publish"; shift ;;
    --at)      SLOT_AT="$2"; shift 2 ;;
    --format)  FORMAT_OVERRIDE="$2"; shift 2 ;;
    --topic)   TOPIC="$2"; shift 2 ;;
    *)         echo "UYARI: bilinmeyen arg '$1'"; shift ;;
  esac
done

echo "=================================================="
echo "[$(date -u '+%F %T UTC')] Viral Shorts ($MODE) başladı"

MANIFEST="$REPO/logs/pending-viral.json"
TODAY="$(date -u +%Y%m%d)"

# 2a) ZAMAN DİLİMİ DENEYİ — sadece publish/full modunda geçerli (prepare slot'a bakmaz).
SLOTS_UTC=("05:00" "08:00" "10:00" "13:00" "15:30" "18:30")  # TR(UTC+3): 08 11 13 16 18:30 21:30
NUM_SLOTS=${#SLOTS_UTC[@]}
DOY=$(( 10#$(date -u +%j) ))
TODAY_SLOT=$(( DOY % NUM_SLOTS ))
SLOT_LABEL="manual"

if [ "$MODE" != "prepare" ]; then
  LEARNED_SLOT="$("$VPY" "$REPO/scripts/learn/winner.py" viral.slot 2>/dev/null || true)"
  if [ -n "$LEARNED_SLOT" ] && [ "$LEARNED_SLOT" -ge 0 ] 2>/dev/null && [ "$LEARNED_SLOT" -lt "$NUM_SLOTS" ] 2>/dev/null; then
    if [ $(( DOY % 3 )) -eq 0 ]; then
      TARGET_SLOT=$(( (DOY / 3) % NUM_SLOTS ))
      echo "[🧠] Keşif günü: slot $TARGET_SLOT = ${SLOTS_UTC[$TARGET_SLOT]} UTC"
    else
      TARGET_SLOT="$LEARNED_SLOT"
      echo "[🧠] Öğrenilen yayın saati devrede: slot $TARGET_SLOT = ${SLOTS_UTC[$TARGET_SLOT]} UTC"
    fi
  else
    TARGET_SLOT="$TODAY_SLOT"
  fi
  if [ -n "$SLOT_AT" ]; then
    if [ "$SLOT_AT" != "$TARGET_SLOT" ]; then
      echo "[i] Slot $SLOT_AT bugünün hedefi değil (hedef: $TARGET_SLOT = ${SLOTS_UTC[$TARGET_SLOT]} UTC) — atlanıyor."
      exit 0
    fi
    SLOT_LABEL="${SLOTS_UTC[$TARGET_SLOT]}"
    echo "[*] Zaman dilimi: slot $TARGET_SLOT = $SLOT_LABEL UTC"
  fi
fi

# ============================================================================
# PUBLISH: gece hazırlanan senaryoyu yükle (Claude ÇAĞIRMA). Yoksa yedek üret.
# ============================================================================
SCEN=""; SLUG=""; FORMAT=""; VOICE=""
if [ "$MODE" = "publish" ] && [ -f "$MANIFEST" ]; then
  read -r M_DATE M_SLUG M_SCEN M_FORMAT M_VOICE < <("$VPY" -c "
import json
try:
    m=json.load(open('$MANIFEST'))
    print(m.get('date',''), m.get('slug',''), m.get('scen',''), m.get('format',''), m.get('voice',''))
except Exception:
    print('')
")
  if [ "$M_DATE" = "$TODAY" ] && [ -n "${M_SCEN:-}" ] && [ -f "$M_SCEN" ]; then
    SCEN="$M_SCEN"; SLUG="$M_SLUG"; FORMAT="$M_FORMAT"; VOICE="$M_VOICE"
    echo "[publish] Hazır senaryo kullanılıyor: $SLUG ($FORMAT/$VOICE) — TOKEN HARCANMADI ✅"
  else
    echo "[publish] UYARI: bugüne hazır senaryo yok → yedek üretim (Claude)."
  fi
fi

# ============================================================================
# ÜRET (Claude) — prepare modunda daima; publish'te sadece hazır senaryo yoksa (yedek).
# ============================================================================
if [ -z "$SCEN" ]; then
  # Format
  declare -A DOW_FMT=([1]=comparison [2]=myth [3]=backtest_return [4]=shock_number [5]=news_reaction [6]=single_concept [7]=myth)
  FORMAT="${FORMAT_OVERRIDE:-${DOW_FMT[$(date -u +%u)]}}"
  if [ -z "$FORMAT_OVERRIDE" ]; then
    LEARNED_FMT="$("$VPY" "$REPO/scripts/learn/winner.py" viral.format 2>/dev/null || true)"
    [ -n "$LEARNED_FMT" ] && { FORMAT="$LEARNED_FMT"; echo "[🧠] Öğrenilen format: $FORMAT"; }
  fi
  echo "[*] Format: $FORMAT ${TOPIC:+| Konu: $TOPIC}"

  # Veri-formatı rotasyonu (backtest çeşitlensin)
  EXTRA_ARGS=()
  if [ "$FORMAT" = "backtest_return" ]; then
    INSTR_POOL=(gold usd bist); AMT_POOL=(5000 10000 25000 50000 100000); RNG_POOL=(1y 2y 3y 5y)
    EXTRA_ARGS+=(--instrument "${INSTR_POOL[$(( DOY % 3 ))]}" --amount "${AMT_POOL[$(( DOY % 5 ))]}" --range "${RNG_POOL[$(( (DOY / 3) % 4 ))]}")
    echo "[*] Backtest rotasyonu: ${EXTRA_ARGS[*]}"
  fi

  # Ses rotasyonu
  VOICE="$("$VPY" - <<PY
import datetime, importlib.util
spec = importlib.util.spec_from_file_location("shorts_state", "$REPO/scripts/shorts-state.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
V = mod.VOICES
print(V[datetime.datetime.utcnow().timetuple().tm_yday % len(V)])
PY
)"
  echo "[*] Ses: $VOICE"

  # Senaryo üret (stdout son satırı = json yolu)
  SCEN="$("$VPY" "$REPO/scripts/viral-script.py" --format "$FORMAT" ${TOPIC:+--topic "$TOPIC"} ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"} | tail -1)"
  if [ -z "$SCEN" ] || [ ! -f "$SCEN" ]; then
    echo "HATA: senaryo üretilemedi (format=$FORMAT)"; exit 2
  fi
  SLUG="$("$VPY" -c "import json,sys; print(json.load(open('$SCEN'))['slug'])")"
  echo "[+] Senaryo: $SCEN (slug=$SLUG)"

  # Senaryo dosyasını commit+push (kayıt)
  if [ -f "public/social/scenarios/$SLUG.json" ]; then
    git add "public/social/scenarios/$SLUG.json"
    git commit -m "viral-shorts: $SLUG senaryosu ($FORMAT, otomatik)" || true
    git_push_retry main
  fi
fi

# ============================================================================
# PREPARE: manifest'e yaz ve ÇIK (render/upload yok — o gündüz yapılacak).
# ============================================================================
if [ "$MODE" = "prepare" ]; then
  "$VPY" -c "
import json
json.dump({'date':'$TODAY','slug':'$SLUG','scen':'$SCEN','format':'$FORMAT','voice':'$VOICE'}, open('$MANIFEST','w'))
print('[prepare] manifest yazıldı: $SLUG ($FORMAT/$VOICE)')
"
  echo "[$(date -u '+%F %T UTC')] PREPARE tamam: $SLUG — gündüz publish edilecek."
  exit 0
fi

# ============================================================================
# RENDER + YAYIN (publish/full) — sıfır token.
# ============================================================================
echo "[*] Video üretiliyor..."
if ! "$VPY" "$REPO/scripts/shorts-build-v4.py" "$SLUG" --scenario "$SCEN" --engine google --voice "$VOICE"; then
  echo "HATA: video üretilemedi ($SLUG)"; exit 2
fi

echo "[*] YouTube'a yükleniyor (public)..."
YT_URL=""
if "$VPY" "$REPO/scripts/youtube-upload.py" "$SLUG" --privacy public; then
  YT_URL="$("$VPY" -c "import json;print(json.load(open('public/social/short-$SLUG.json')).get('youtube_url',''))")"
else
  echo "UYARI: YouTube yükleme atlandı/başarısız (devam)"
fi

if [ -n "$YT_URL" ]; then
  "$VPY" "$REPO/scripts/youtube-extras.py" "$SLUG" --format "$FORMAT" 2>&1 | sed 's/^/    [extras] /' || true
fi

echo "[*] Instagram Reel yayınlanıyor..."
IG_REEL=""
if "$VPY" "$REPO/scripts/instagram-reel.py" "$SLUG" 2>&1 | sed 's/^/    [reel] /'; then
  IG_REEL="$("$VPY" -c "import json;print(json.load(open('public/social/short-$SLUG.json')).get('ig_reel_permalink',''))" 2>/dev/null || true)"
else
  echo "UYARI: IG Reel atlandı/başarısız (devam)"
fi

echo "[*] Telegram'a gönderiliyor..."
VID="$REPO/public/social/short-$SLUG.mp4"
CAP="🎬 Viral Shorts [$FORMAT] · ⏰ $SLOT_LABEL UTC%0A%0A${YT_URL:+▶️ $YT_URL%0A}${IG_REEL:+📸 $IG_REEL%0A}🔊 ${VOICE##*-}%0A%0A#parafomo"
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendVideo" \
  -F "chat_id=${TELEGRAM_CHAT_ID}" -F "video=@${VID}" -F "supports_streaming=true" \
  --form-string "caption=$(printf '%b' "$CAP")" >/dev/null || echo "UYARI: Telegram gönderilemedi"

# Yayın saatini logla
CSV="$REPO/logs/viral-times.csv"
[ -f "$CSV" ] || echo "yayin_utc,slot_utc,slot_idx,format,slug,youtube_url" > "$CSV"
echo "$(date -u '+%F %T'),$SLOT_LABEL,${SLOT_AT:-manual},$FORMAT,$SLUG,$YT_URL" >> "$CSV"

echo "[$(date -u '+%F %T UTC')] Tamamlandı: $SLUG @ $SLOT_LABEL UTC ${YT_URL:+→ $YT_URL}"
