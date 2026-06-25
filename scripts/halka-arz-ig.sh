#!/usr/bin/env bash
#
# ParaFOMO — Halka arz TARİH postu (talep tarihleri belli olunca, cron).
# data/halka-arz.json'da tarihi belli, tarih-postlanmamış arzları bulur;
# kart üretir (--type tarih) -> commit+push -> raw canlı olunca -> IG'ye postlar.
# Gündüz guard (09-21 TR). dedup: logs/halka-arz-posted.txt
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

FORCE="${1:-}"
HOUR=$(TZ=Europe/Istanbul date +%H)
if [ "$FORCE" != "--now" ] && { [ "$HOUR" -lt 9 ] || [ "$HOUR" -ge 21 ]; }; then
  echo "[i] Gündüz dışı (saat $HOUR TR) — atlanıyor."; exit 0
fi

echo "[$(date -u '+%F %T UTC')] Halka arz TARİH kontrolü başladı"
git pull --rebase --autostash origin main >/dev/null 2>&1 || echo "UYARI: pull başarısız"

SLUGS=$(python3 "$REPO/scripts/post-halka-arz-instagram.py" --list)
[ -z "$SLUGS" ] && { echo "[i] Yeni tarihli arz yok."; exit 0; }
echo "[*] Tarihi belli yeni arz(lar): $SLUGS"

# Spam koruması: tek seferde en fazla 3
SEL=""; n=0
for s in $SLUGS; do n=$((n+1)); [ "$n" -gt 3 ] && break; SEL="$SEL $s"; done

for s in $SEL; do
  echo "[*] Kart: $s"
  "$VENV_PY" "$REPO/scripts/halka-arz-card.py" --slug "$s" --type tarih 2>&1 | sed 's/^/    [kart] /' || echo "UYARI: $s kartı üretilemedi"
done

git add public/social/halka-arz-*-tarih.jpg 2>/dev/null
if ! git diff --cached --quiet; then
  git commit -m "halka arz: tarih kartı ($SEL )" >/dev/null 2>&1
  git push origin main 2>&1 | sed 's/^/    [push] /' || { echo "HATA: push"; exit 1; }
fi

for s in $SEL; do
  KEY=$(echo "$s" | sed 's/[^A-Za-z0-9-]//g')
  RAW="https://raw.githubusercontent.com/Junkiieee/parafomo/main/public/social/halka-arz-${KEY}-tarih.jpg"
  ok=0
  for i in $(seq 1 18); do
    [ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$RAW")" = "200" ] && { ok=1; break; }
    sleep 10
  done
  [ "$ok" != "1" ] && { echo "UYARI: $s görseli canlı değil, atlanıyor"; continue; }
  echo "[*] IG post: $s"
  OUT=$(python3 "$REPO/scripts/post-halka-arz-instagram.py" --slug "$s" 2>&1); echo "$OUT" | sed 's/^/    [ig] /'
  if echo "$OUT" | grep -q "YAYINLANDI"; then
    echo "[*] Story planlandı (~2-3 dk sonra)"
    bash "$REPO/scripts/share-story.sh" "public/social/halka-arz-${KEY}-tarih.jpg" "HALKA ARZ" "Detaylar profilde" 2>&1 | sed 's/^/    [story] /' || true
  fi
done

echo "[$(date -u '+%F %T UTC')] Halka arz TARİH kontrolü tamamlandı"
