#!/usr/bin/env bash
#
# ParaFOMO — günlük EK "tamamen Manim" Shorts (normal viral hattından AYRI, izole).
# Akış: senkronla → format seç → viral senaryo üret (Claude) → manimify (tam-Manim'e çevir)
#       → shorts-build → YouTube(public)+IG+Telegram → senaryoyu commit+push.
# Amaç: normal üretim (stok+Manim) YANINDA, tek tutarlı özgün Manim dilinde ek video.
# İzole: burada hata olsa normal viral-daily'ye dokunmaz.
set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"
REPO="/root/parafomo"; VPY="/root/.venvs/parafomo/bin/python"
cd "$REPO" || { echo "HATA: repo yok"; exit 1; }
. "$REPO/scripts/lib/gitsync.sh"
set -a; . "$REPO/.env"; set +a

{ git fetch origin main && git rebase --autostash origin/main; } || echo "UYARI: pull başarısız (devam)"
echo "=================================================="
echo "[$(date -u '+%F %T UTC')] Manim-daily (tam-Manim ek video) başladı"

DOY=$(( 10#$(date -u +%j) ))
# Ana videodan FARKLI konu için format rotasyonunu kaydır (backtest'i öne al — veri grafiği parlar).
FMT_POOL=(backtest_return comparison shock_number single_concept myth)
FORMAT="${1:-${FMT_POOL[$(( DOY % ${#FMT_POOL[@]} ))]}}"
echo "[*] Format: $FORMAT"

# backtest ise veri rotasyonu (grafik çeşitlensin)
EXTRA_ARGS=()
if [ "$FORMAT" = "backtest_return" ]; then
  INSTR=(gold usd bist); AMT=(5000 10000 25000 50000 100000); RNG=(1y 2y 3y 5y)
  EXTRA_ARGS+=(--instrument "${INSTR[$(( DOY % 3 ))]}" --amount "${AMT[$(( DOY % 5 ))]}" --range "${RNG[$(( (DOY/3) % 4 ))]}")
fi

# Ses rotasyonu (tutarlı sesler havuzundan)
VOICE="$("$VPY" - <<PY
import datetime, importlib.util
s=importlib.util.spec_from_file_location("st","$REPO/scripts/shorts-state.py")
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
print(m.VOICES[datetime.datetime.utcnow().timetuple().tm_yday % len(m.VOICES)])
PY
)"

# 1) Senaryo üret (Claude)
SCEN="$("$VPY" "$REPO/scripts/viral-script.py" --format "$FORMAT" ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"} | tail -1)"
[ -n "$SCEN" ] && [ -f "$SCEN" ] || { echo "HATA: senaryo üretilemedi"; exit 2; }

# 2) Tam-Manim'e çevir
SCEN_M="$("$VPY" "$REPO/scripts/manimify.py" "$SCEN" | tail -1)"
[ -n "$SCEN_M" ] && [ -f "$SCEN_M" ] || { echo "HATA: manimify başarısız"; exit 2; }
SLUG="$("$VPY" -c "import json;print(json.load(open('$SCEN_M'))['slug'])")"
echo "[+] Tam-Manim senaryo: $SLUG"

# 3) Build (Manim sahneleri + TTS + altyazı)
if ! "$VPY" "$REPO/scripts/shorts-build-v4.py" "$SLUG" --scenario "$SCEN_M" --engine google --voice "$VOICE"; then
  echo "HATA: video üretilemedi ($SLUG)"; exit 2
fi

# 4) Yayın
YT_URL=""
if "$VPY" "$REPO/scripts/youtube-upload.py" "$SLUG" --privacy public; then
  YT_URL="$("$VPY" -c "import json;print(json.load(open('public/social/short-$SLUG.json')).get('youtube_url',''))" 2>/dev/null || true)"
else echo "UYARI: YouTube atlandı"; fi
[ -n "$YT_URL" ] && "$VPY" "$REPO/scripts/youtube-extras.py" "$SLUG" --format "$FORMAT" 2>/dev/null || true

IG_REEL=""
if "$VPY" "$REPO/scripts/instagram-reel.py" "$SLUG" 2>&1 | sed 's/^/    [reel] /'; then
  IG_REEL="$("$VPY" -c "import json;print(json.load(open('public/social/short-$SLUG.json')).get('ig_reel_permalink',''))" 2>/dev/null || true)"
else echo "UYARI: IG Reel atlandı"; fi

VID="$REPO/public/social/short-$SLUG.mp4"
CAP="🎬 Tam-Manim Shorts [$FORMAT]%0A%0A${YT_URL:+▶️ $YT_URL%0A}${IG_REEL:+📸 $IG_REEL%0A}🔊 ${VOICE##*-}%0A%0A#parafomo"
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendVideo" \
  -F "chat_id=${TELEGRAM_CHAT_ID}" -F "video=@${VID}" -F "supports_streaming=true" \
  --form-string "caption=$(printf '%b' "$CAP")" >/dev/null || echo "UYARI: Telegram gönderilemedi"

# 5) Senaryoyu kaydet
if [ -f "public/social/scenarios/$SLUG.json" ]; then
  git add "public/social/scenarios/$SLUG.json"
  git commit -m "manim-shorts: $SLUG (tam-Manim, otomatik)" || true
  git_push_retry main
fi
echo "[$(date -u '+%F %T UTC')] Manim-daily tamam: $SLUG ${YT_URL:+→ $YT_URL}"
