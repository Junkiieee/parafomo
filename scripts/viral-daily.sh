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
# Cron örneği (her gün 12:30 UTC — blog shorts'undan ayrı bir saat):
#   30 12 * * * /root/parafomo/scripts/viral-daily.sh >> /root/parafomo/logs/viral.log 2>&1

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
git pull --rebase --autostash origin main || echo "UYARI: pull başarısız (devam)"

# 2) Günün formatı (override: $1 ile elle format verilebilir)
declare -A DOW_FMT=(
  [1]=comparison [2]=myth [3]=backtest_return [4]=shock_number
  [5]=news_reaction [6]=single_concept [7]=myth
)
FORMAT="${1:-${DOW_FMT[$(date -u +%u)]}}"
TOPIC="${2:-}"
echo "[*] Format: $FORMAT ${TOPIC:+| Konu: $TOPIC}"

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
SCEN="$("$VPY" "$REPO/scripts/viral-script.py" --format "$FORMAT" ${TOPIC:+--topic "$TOPIC"} | tail -1)"
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

# 7) Telegram önizleme
echo "[*] Telegram'a gönderiliyor..."
VID="$REPO/public/social/short-$SLUG.mp4"
CAP="🎬 Viral Shorts [$FORMAT]%0A%0A${YT_URL:+▶️ $YT_URL%0A}🔊 ${VOICE##*-}%0A%0A#parafomo"
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendVideo" \
  -F "chat_id=${TELEGRAM_CHAT_ID}" -F "video=@${VID}" -F "supports_streaming=true" \
  --form-string "caption=$(printf '%b' "$CAP")" >/dev/null || echo "UYARI: Telegram gönderilemedi"

# 8) Senaryo dosyasını commit + push (kayıt için) — yalnız bu çalıştırmanın slug'ı
if [ -f "public/social/scenarios/$SLUG.json" ]; then
  git add "public/social/scenarios/$SLUG.json"
  git commit -m "viral-shorts: $SLUG senaryosu ($FORMAT, otomatik)" || true
  git push origin main 2>&1 | sed 's/^/    [push] /' || echo "UYARI: push başarısız"
fi

echo "[$(date -u '+%F %T UTC')] Tamamlandı: $SLUG ${YT_URL:+→ $YT_URL}"
