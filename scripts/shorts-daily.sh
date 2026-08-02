#!/usr/bin/env bash
#
# ParaFOMO — günlük YouTube Shorts otomasyonu (cron).
# Akış: senkronla → sıradaki (en eski) yazıyı seç → senaryo (yoksa Claude üretir+kaydeder)
#       → video üret (B-roll+senkron+o günkü ses) → YouTube'a PUBLIC yükle
#       → Telegram'a önizleme → durumu güncelle → senaryo değişikliğini commit+push.
#
# GECE/GÜNDÜZ AYRIMI (token'ı geceye topla):
#   --prepare : SADECE senaryoyu üret (Claude) + commit, çık. state'i İLERLETMEZ →
#               publish aynı slug'ı bulur. Gece (içerik motorundan sonra) çalışır.
#   --publish : Claude ÇAĞIRMAZ (senaryo zaten var); render+upload+state. Sıfır token.
#   (mod yoksa: eski hepsi-bir-arada davranış.)
#
# Cron örneği:
#   30 1 * * * /root/parafomo/scripts/shorts-daily.sh --prepare >> .../shorts.log 2>&1
#   30 9 * * * /root/parafomo/scripts/shorts-daily.sh --publish >> .../shorts.log 2>&1

set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"

REPO="/root/parafomo"
VPY="/root/.venvs/parafomo/bin/python"
cd "$REPO" || { echo "HATA: repo yok"; exit 1; }

# Mod: --prepare | --publish | (yok=full)
MODE="full"
case "${1:-}" in
  --prepare) MODE="prepare" ;;
  --publish) MODE="publish" ;;
esac

echo "=================================================="
echo "[$(date -u '+%F %T UTC')] Shorts otomasyonu ($MODE) başladı"

# .env (PEXELS, TELEGRAM)
set -a; . "$REPO/.env"; set +a

# 1) Senkronla
{ git fetch origin main && git rebase --autostash origin/main; } || echo "UYARI: pull başarısız (devam)"

# Tek bir yazıyı işler. MODE'a göre: prepare=sadece senaryo; publish=render+yayın; full=hepsi.
# Dönüş: 0 başarı, 1 atla (boş/zaten işlenmiş), 2 hata.
process_one() {
  local slug="$1" voice="$2" engine="${3:-google}"
  [ -z "$slug" ] && return 1
  echo "--------------------------------------------------"
  echo "[*] Yazı: $slug | Motor: $engine | Ses: $voice | Mod: $MODE"

  # PREPARE: sadece senaryoyu üret (Claude) + commit; render/upload YOK, state İLERLEMEZ.
  if [ "$MODE" = "prepare" ]; then
    "$VPY" "$REPO/scripts/shorts-script.py" "$slug" || { echo "UYARI: senaryo üretilemedi ($slug)"; return 2; }
    if [ -n "$(git status --porcelain src/content/blog/)" ]; then
      git add src/content/blog/
      git commit -m "shorts: $slug senaryosu hazırlandı (gece, otomatik)" || true
      git push origin main 2>&1 | sed 's/^/    [push] /' || echo "UYARI: push başarısız"
    fi
    echo "[prepare] $slug senaryosu hazır — gündüz publish edilecek."
    return 0
  fi

  # PUBLISH: senaryo zaten var → Claude ATLA. FULL: yoksa üret (yedek).
  if [ "$MODE" != "publish" ]; then
    "$VPY" "$REPO/scripts/shorts-script.py" "$slug" || echo "UYARI: senaryo üretilemedi (auto-FAQ kullanılacak)"
  fi

  # Video üret — motora göre doğru ses bayrağı (google: --voice, edge: --edge-voice)
  echo "[*] Video üretiliyor..."
  local voice_flag="--voice"
  [ "$engine" = "edge" ] && voice_flag="--edge-voice"
  if ! "$VPY" "$REPO/scripts/shorts-build.py" "$slug" --engine "$engine" "$voice_flag" "$voice"; then
    echo "HATA: video üretilemedi ($slug) — atlanıyor"; return 2
  fi

  # YouTube'a PUBLIC yükle
  echo "[*] YouTube'a yükleniyor (public)..."
  if ! "$VPY" "$REPO/scripts/youtube-upload.py" "$slug" --privacy public; then
    echo "HATA: yükleme başarısız ($slug) — atlanıyor"; return 2
  fi
  local yt_url
  yt_url="$("$VPY" -c "import json;print(json.load(open('public/social/short-$slug.json')).get('youtube_url',''))")"

  # Telegram önizleme
  echo "[*] Telegram'a gönderiliyor..."
  local vid="$REPO/public/social/short-$slug.mp4"
  local cap="🎬 Yeni Shorts yayında!%0A%0A🔊 Ses: ${voice##*-} (${engine})%0A▶️ ${yt_url}%0A%0A#parafomo"
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendVideo" \
    -F "chat_id=${TELEGRAM_CHAT_ID}" -F "video=@${vid}" -F "supports_streaming=true" \
    --form-string "caption=$(printf '%b' "$cap")" >/dev/null || echo "UYARI: Telegram gönderilemedi"

  # Durumu güncelle (done + ses rotasyonu ilerlet)
  "$VPY" "$REPO/scripts/shorts-state.py" commit "$slug"

  # Senaryo değişikliğini (frontmatter shorts:) commit + push
  if [ -n "$(git status --porcelain src/content/blog/)" ]; then
    git add src/content/blog/
    git commit -m "shorts: $slug senaryosu kaydedildi (otomatik)" || true
    git push origin main 2>&1 | sed 's/^/    [push] /' || echo "UYARI: push başarısız"
  fi
  echo "[+] Tamamlandı: $slug → $yt_url"
  return 0
}

# 2) Günde 2 Shorts: önce EN YENİ (o günkü blog yazısıyla senkron), sonra EN ESKİ
#    işlenmemiş yazı (backlog'u eritir). Aynı slug iki kez işlenmez.
PROCESSED=0
DONE_SLUGS=""
for WHERE in newest oldest; do
  NEXT="$("$VPY" "$REPO/scripts/shorts-state.py" next "$WHERE")"
  SLUG="$(echo "$NEXT" | cut -f1)"
  VOICE="$(echo "$NEXT" | cut -f2)"
  ENGINE="$(echo "$NEXT" | cut -f3)"
  if [ -z "$SLUG" ]; then
    echo "[i] '$WHERE' için işlenecek yazı yok."
    continue
  fi
  case " $DONE_SLUGS " in
    *" $SLUG "*) echo "[i] $SLUG zaten bu çalıştırmada işlendi — atlanıyor."; continue ;;
  esac
  if process_one "$SLUG" "$VOICE" "$ENGINE"; then
    PROCESSED=$((PROCESSED + 1))
    DONE_SLUGS="$DONE_SLUGS $SLUG"
  fi
done

if [ "$PROCESSED" -eq 0 ]; then
  echo "[i] Kuyruk boş — işlenecek yeni yazı yok."
fi
VERB="yayınlandı"; [ "$MODE" = "prepare" ] && VERB="hazırlandı"
echo "[$(date -u '+%F %T UTC')] Tamamlandı — bu çalıştırmada $PROCESSED Shorts $VERB"
