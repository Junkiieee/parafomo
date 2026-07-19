#!/usr/bin/env bash
#
# ParaFOMO — günlük VİRAL Shorts otomasyonu (blog→video hattından AYRI).
# Akış: senkronla → günün formatını seç (haftalık rotasyon) → viral senaryo üret
#       (Claude, blog'dan bağımsız) → video üret (senaryo görselleriyle: Wikimedia
#       kişi/yer + Pexels sahne) → YouTube'a PUBLIC yükle → Telegram önizleme →
#       senaryo dosyasını commit+push.
#
# Haftalık format rotasyonu (date +%u: 1=Pzt ... 7=Paz):
#   Pzt karşılaştırma · Sal mit · Çar geri-dönük getiri · Per sayı şoku
#   Cum güncel/tepki · Cmt tek kavram · Paz mit (evergreen güçlü)
#
# ZAMAN DİLİMİ DENEYİ: cron'da 6 satır (her aday saat için bir tane), her biri --at <i>
# taşır; yalnız bugünün slotuna (gün_no % 6) denk gelen satır yayınlar. Yayın saati
# logs/viral-times.csv'ye yazılır → en iyi saati izlenme ile kıyaslamak için.
#   0  5 * * * /root/parafomo/scripts/viral-daily.sh --at 0 >> /root/parafomo/logs/viral.log 2>&1
#   0  8 * * * /root/parafomo/scripts/viral-daily.sh --at 1 >> /root/parafomo/logs/viral.log 2>&1
#   0 10 * * * /root/parafomo/scripts/viral-daily.sh --at 2 >> /root/parafomo/logs/viral.log 2>&1
#   0 13 * * * /root/parafomo/scripts/viral-daily.sh --at 3 >> /root/parafomo/logs/viral.log 2>&1
#   30 15 * * * /root/parafomo/scripts/viral-daily.sh --at 4 >> /root/parafomo/logs/viral.log 2>&1
#   30 18 * * * /root/parafomo/scripts/viral-daily.sh --at 5 >> /root/parafomo/logs/viral.log 2>&1

set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"

REPO="/root/parafomo"
VPY="/root/.venvs/parafomo/bin/python"
cd "$REPO" || { echo "HATA: repo yok"; exit 1; }

echo "=================================================="
echo "[$(date -u '+%F %T UTC')] Viral Shorts otomasyonu başladı"

# .env (PEXELS, TELEGRAM)
set -a; . "$REPO/.env"; set +a

# 1) Senkronla
{ git fetch origin main && git rebase --autostash origin/main; } || echo "UYARI: pull başarısız (devam)"

# Argümanlar: --at N (zaman-dilimi slot indeksi), --format X, --topic "..."
SLOT_AT=""; FORMAT_OVERRIDE=""; TOPIC=""
while [ $# -gt 0 ]; do
  case "$1" in
    --at)     SLOT_AT="$2"; shift 2 ;;
    --format) FORMAT_OVERRIDE="$2"; shift 2 ;;
    --topic)  TOPIC="$2"; shift 2 ;;
    *)        echo "UYARI: bilinmeyen arg '$1'"; shift ;;
  esac
done

# 2a) ZAMAN DİLİMİ DENEYİ — 6 aday saat (UTC). Her gün SADECE biri yayınlar; hangisi
#     olduğu yıl-günü ile döner (slot = gün_no % 6). Cron'da 6 satır var, her biri kendi
#     --at indeksini taşır; yalnız bugünün slotuna denk gelen satır devam eder, diğerleri çıkar.
#     Amaç: zamanla her slotun izlenme performansını kıyaslayıp en iyi saati bulmak.
SLOTS_UTC=("05:00" "08:00" "10:00" "13:00" "15:30" "18:30")  # TR(UTC+3): 08 11 13 16 18:30 21:30
NUM_SLOTS=${#SLOTS_UTC[@]}
DOY=$(( 10#$(date -u +%j) ))
TODAY_SLOT=$(( DOY % NUM_SLOTS ))

# Öğrenme katmanı: en iyi saat KANITLANMIŞSA (policy=exploit) hedef slotu ona çek —
# ama 3 günde 1 gün KEŞFE ayır ki diğer slotlar taze veri almaya devam etsin (aksi halde
# kazanan slota kilitlenince diğerleri bir daha hiç yayınlamaz = keşif ölür). Keşif günü
# TÜM slotları sırayla gezer ((DOY/3)%N → 1,2,3,4,5,0,...), yalnız bugünün slotunu değil.
LEARNED_SLOT="$("$VPY" "$REPO/scripts/learn/winner.py" viral.slot 2>/dev/null || true)"
if [ -n "$LEARNED_SLOT" ] && [ "$LEARNED_SLOT" -ge 0 ] 2>/dev/null && [ "$LEARNED_SLOT" -lt "$NUM_SLOTS" ] 2>/dev/null; then
  if [ $(( DOY % 3 )) -eq 0 ]; then
    TARGET_SLOT=$(( (DOY / 3) % NUM_SLOTS ))
    echo "[🧠] Keşif günü: slot $TARGET_SLOT = ${SLOTS_UTC[$TARGET_SLOT]} UTC (diğer saatler taze veri alsın)"
  else
    TARGET_SLOT="$LEARNED_SLOT"
    echo "[🧠] Öğrenilen yayın saati devrede: slot $TARGET_SLOT = ${SLOTS_UTC[$TARGET_SLOT]} UTC"
  fi
else
  TARGET_SLOT="$TODAY_SLOT"   # karar yok → tam rotasyon (mevcut keşif davranışı)
fi

SLOT_LABEL="manual"
if [ -n "$SLOT_AT" ]; then
  if [ "$SLOT_AT" != "$TARGET_SLOT" ]; then
    echo "[i] Slot $SLOT_AT bugünün hedefi değil (hedef: $TARGET_SLOT = ${SLOTS_UTC[$TARGET_SLOT]} UTC) — atlanıyor."
    exit 0
  fi
  SLOT_LABEL="${SLOTS_UTC[$TARGET_SLOT]}"
  echo "[*] Zaman dilimi: slot $TARGET_SLOT = $SLOT_LABEL UTC (TR $(printf '%02d' $(( (10#${SLOT_LABEL%%:*} + 3) % 24 ))):${SLOT_LABEL##*:}))"
fi

# 2b) Günün formatı (haftanın günü; slottan bağımsız). Override: --format
declare -A DOW_FMT=(
  [1]=comparison [2]=myth [3]=backtest_return [4]=shock_number
  [5]=news_reaction [6]=single_concept [7]=myth
)
FORMAT="${FORMAT_OVERRIDE:-${DOW_FMT[$(date -u +%u)]}}"
# Öğrenme katmanı: metrik yeterliyse KANITLANMIŞ formatı kullan; yoksa winner.py BOŞ
# döner ve gün-bazlı rotasyon (keşif) sürer. Manuel --format her ikisini de ezer.
if [ -z "$FORMAT_OVERRIDE" ]; then
  LEARNED_FMT="$("$VPY" "$REPO/scripts/learn/winner.py" viral.format 2>/dev/null || true)"
  if [ -n "$LEARNED_FMT" ]; then FORMAT="$LEARNED_FMT"; echo "[🧠] Öğrenilen format devrede: $FORMAT"; fi
fi
echo "[*] Format: $FORMAT ${TOPIC:+| Konu: $TOPIC}"

# 2c) Veri-formatı rotasyonu — aksi halde backtest hep 'gold' + 10.000 TL üretir,
#     bu da birebir aynı videoyu doğurur. Enstrüman/tutar/aralığı yıl-günüyle döndür.
EXTRA_ARGS=()
if [ "$FORMAT" = "backtest_return" ]; then
  INSTR_POOL=(gold usd bist); AMT_POOL=(5000 10000 25000 50000 100000); RNG_POOL=(1y 2y 3y 5y)
  EXTRA_ARGS+=(--instrument "${INSTR_POOL[$(( DOY % 3 ))]}" \
               --amount "${AMT_POOL[$(( DOY % 5 ))]}" \
               --range "${RNG_POOL[$(( (DOY / 3) % 4 ))]}")
  echo "[*] Backtest rotasyonu: ${EXTRA_ARGS[*]}"
fi

# 3) Ses rotasyonu (blog hattının done-state'inden bağımsız; yıl-günü ile döner)
VOICE="$("$VPY" - <<PY
import datetime, importlib.util
spec = importlib.util.spec_from_file_location("shorts_state", "$REPO/scripts/shorts-state.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
V = mod.VOICES
print(V[datetime.datetime.utcnow().timetuple().tm_yday % len(V)])
PY
)"
echo "[*] Ses: $VOICE"

# 4) Senaryo üret (stdout son satırı = json yolu)
SCEN="$("$VPY" "$REPO/scripts/viral-script.py" --format "$FORMAT" ${TOPIC:+--topic "$TOPIC"} ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"} | tail -1)"
if [ -z "$SCEN" ] || [ ! -f "$SCEN" ]; then
  echo "HATA: senaryo üretilemedi (format=$FORMAT)"; exit 2
fi
SLUG="$("$VPY" -c "import json,sys; print(json.load(open('$SCEN'))['slug'])")"
echo "[+] Senaryo: $SCEN (slug=$SLUG)"

# 5) Video üret (senaryo görselleriyle)
echo "[*] Video üretiliyor..."
if ! "$VPY" "$REPO/scripts/shorts-build.py" "$SLUG" --scenario "$SCEN" --engine google --voice "$VOICE"; then
  echo "HATA: video üretilemedi ($SLUG)"; exit 2
fi

# 6) YouTube'a PUBLIC yükle (OAuth hazır değilse atlar, hattı düşürmez)
echo "[*] YouTube'a yükleniyor (public)..."
YT_URL=""
if "$VPY" "$REPO/scripts/youtube-upload.py" "$SLUG" --privacy public; then
  YT_URL="$("$VPY" -c "import json;print(json.load(open('public/social/short-$SLUG.json')).get('youtube_url',''))")"
else
  echo "UYARI: YouTube yükleme atlandı/başarısız (devam)"
fi

# 6b) Abone-büyütme ekstraları: oynatma listesi + abone CTA yorumu (force-ssl scope
#     yoksa zarifçe atlar; youtube-reauth.py ile aktive edilir). Pipeline'ı düşürmez.
if [ -n "$YT_URL" ]; then
  "$VPY" "$REPO/scripts/youtube-extras.py" "$SLUG" --format "$FORMAT" 2>&1 | sed 's/^/    [extras] /' || true
fi

# 6c) Instagram Reels — aynı videoyu Reel olarak yayınla (IG pivot: feed yerine Reels).
#     Kendi videosunu media dalına barındırıp IG'ye verir; hata olsa hattı düşürmez.
echo "[*] Instagram Reel yayınlanıyor..."
IG_REEL=""
if "$VPY" "$REPO/scripts/instagram-reel.py" "$SLUG" 2>&1 | sed 's/^/    [reel] /'; then
  IG_REEL="$("$VPY" -c "import json;print(json.load(open('public/social/short-$SLUG.json')).get('ig_reel_permalink',''))" 2>/dev/null || true)"
else
  echo "UYARI: IG Reel atlandı/başarısız (devam)"
fi

# 7) Telegram önizleme
echo "[*] Telegram'a gönderiliyor..."
VID="$REPO/public/social/short-$SLUG.mp4"
CAP="🎬 Viral Shorts [$FORMAT] · ⏰ $SLOT_LABEL UTC%0A%0A${YT_URL:+▶️ $YT_URL%0A}${IG_REEL:+📸 $IG_REEL%0A}🔊 ${VOICE##*-}%0A%0A#parafomo"
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendVideo" \
  -F "chat_id=${TELEGRAM_CHAT_ID}" -F "video=@${VID}" -F "supports_streaming=true" \
  --form-string "caption=$(printf '%b' "$CAP")" >/dev/null || echo "UYARI: Telegram gönderilemedi"

# 8) Senaryo dosyasını commit + push (kayıt için) — yalnız bu çalıştırmanın slug'ı
if [ -f "public/social/scenarios/$SLUG.json" ]; then
  git add "public/social/scenarios/$SLUG.json"
  git commit -m "viral-shorts: $SLUG senaryosu ($FORMAT, otomatik)" || true
  git push origin main 2>&1 | sed 's/^/    [push] /' || echo "UYARI: push başarısız"
fi

# 9) Yayın saatini logla (en iyi saati bulmak için sonradan izlenme ile kıyaslanır)
CSV="$REPO/logs/viral-times.csv"
[ -f "$CSV" ] || echo "yayin_utc,slot_utc,slot_idx,format,slug,youtube_url" > "$CSV"
echo "$(date -u '+%F %T'),$SLOT_LABEL,${SLOT_AT:-manual},$FORMAT,$SLUG,$YT_URL" >> "$CSV"

echo "[$(date -u '+%F %T UTC')] Tamamlandı: $SLUG @ $SLOT_LABEL UTC ${YT_URL:+→ $YT_URL}"
