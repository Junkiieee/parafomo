#!/usr/bin/env bash
#
# ParaFOMO — Yeni halka arz Instagram duyurusu (olay-tetiklemeli, cron).
# data/halka-arz.json'da tarihi+fiyatı belli, postlanmamış arzları bulur;
# kart üretir -> commit+push -> GitHub raw canlı olunca -> IG'ye postlar.
# Gündüz guard: sadece 09-21 TR arası postlar (gece düşeni sabah yakalar).
# dedup: logs/halka-arz-posted.txt
#
# Cron: 45 6,9,12,15 * * *  (gün içi 4 kontrol; veri 6 saatte bir tazeleniyor)
#
set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"

REPO="/root/parafomo"
VENV_PY="/root/.venvs/parafomo/bin/python"
[ -x "$VENV_PY" ] || VENV_PY="python3"
cd "$REPO" || { echo "HATA: repo yok"; exit 1; }

FORCE="${1:-}"  # --now: gündüz guard'ı atla (test için)

# Gündüz guard (09-21 TR)
HOUR=$(TZ=Europe/Istanbul date +%H)
if [ "$FORCE" != "--now" ] && { [ "$HOUR" -lt 9 ] || [ "$HOUR" -ge 21 ]; }; then
  echo "[i] Gündüz dışı (saat $HOUR TR) — atlanıyor."
  exit 0
fi

echo "[$(date -u '+%F %T UTC')] Halka arz IG kontrolü başladı"

git pull --rebase --autostash origin main >/dev/null 2>&1 || echo "UYARI: pull başarısız (devam)"

# Yeni postlanabilir kodlar
CODES=$(python3 "$REPO/scripts/post-halka-arz-instagram.py" --list)
if [ -z "$CODES" ]; then
  echo "[i] Yeni halka arz yok."
  exit 0
fi
echo "[*] Yeni arz(lar): $CODES"

# Spam koruması: tek seferde en fazla 3
COUNT=0
SELECTED=""
for c in $CODES; do
  COUNT=$((COUNT+1)); [ "$COUNT" -gt 3 ] && break
  SELECTED="$SELECTED $c"
done

# Kartları üret
for c in $SELECTED; do
  echo "[*] Kart: $c"
  "$VENV_PY" "$REPO/scripts/halka-arz-card.py" --code "$c" 2>&1 | sed 's/^/    [kart] /' || echo "UYARI: $c kartı üretilemedi"
done

# Commit + push (raw URL'ler canlı olsun)
git add public/social/halka-arz-*.jpg 2>/dev/null
if ! git diff --cached --quiet; then
  git commit -m "halka arz: IG kartı ($SELECTED )" >/dev/null 2>&1
  git push origin main 2>&1 | sed 's/^/    [push] /' || { echo "HATA: push"; exit 1; }
fi

# Her kod için raw canlı olunca postla
for c in $SELECTED; do
  RAW="https://raw.githubusercontent.com/Junkiieee/parafomo/main/public/social/halka-arz-${c}.jpg"
  ok=0
  for i in $(seq 1 18); do
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$RAW")
    [ "$code" = "200" ] && { ok=1; break; }
    sleep 10
  done
  if [ "$ok" != "1" ]; then echo "UYARI: $c görseli canlı değil, atlanıyor"; continue; fi
  echo "[*] IG post: $c"
  python3 "$REPO/scripts/post-halka-arz-instagram.py" --code "$c" 2>&1 | sed 's/^/    [ig] /'
done

# Not: dedup durumu logs/halka-arz-posted.txt (gitignore'lu, disk'te kalıcı).

echo "[$(date -u '+%F %T UTC')] Halka arz IG kontrolü tamamlandı"
