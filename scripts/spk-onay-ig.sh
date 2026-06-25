#!/usr/bin/env bash
#
# ParaFOMO — SPK bülteni yeni halka arz ONAY postu (cron).
# Yeni SPK bülteni çıkınca "İlk Halka Arzlar"ı çekip (logolu) toplu/tek
# onay kartını üretir -> commit+push -> raw canlı olunca -> IG'ye postlar.
# dedup: logs/spk-bulten-posted.txt (bülten no). Gündüz guard (09-21 TR).
#
# Cron: 30 7,11,15 * * *  (gün içi 3 kontrol; SPK bülteni ~haftalık)
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

echo "[$(date -u '+%F %T UTC')] SPK onay kontrolü başladı"
git pull --rebase --autostash origin main >/dev/null 2>&1 || echo "UYARI: pull başarısız"

# Yeni bülten varsa kartı üret ('NEW <no> <img>' / 'NONE')
OUT=$("$VENV_PY" "$REPO/scripts/spk-onay.py" --build)
echo "[*] $OUT"
case "$OUT" in
  NEW*) IMG=$(echo "$OUT" | awk '{print $3}') ;;
  *) echo "[i] Yeni bülten yok."; exit 0 ;;
esac

git add "public/social/$IMG" 2>/dev/null
if ! git diff --cached --quiet; then
  git commit -m "halka arz: SPK onay kartı ($OUT)" >/dev/null 2>&1
  git push origin main 2>&1 | sed 's/^/    [push] /' || { echo "HATA: push"; exit 1; }
fi

RAW="https://raw.githubusercontent.com/Junkiieee/parafomo/main/public/social/$IMG"
ok=0
for i in $(seq 1 18); do
  [ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$RAW")" = "200" ] && { ok=1; break; }
  sleep 10
done
[ "$ok" != "1" ] && { echo "HATA: görsel canlı değil"; exit 1; }

echo "[*] IG post"
OUT=$("$VENV_PY" "$REPO/scripts/spk-onay.py" --post 2>&1); echo "$OUT" | sed 's/^/    [ig] /'

# Feed postu yayınlandıysa ~2-3 dk sonra story paylaş
if echo "$OUT" | grep -q "YAYINLANDI"; then
  echo "[*] Story planlandı (~2-3 dk sonra)"
  bash "$REPO/scripts/share-story.sh" "public/social/$IMG" "SPK ONAYI" "Detaylar profilde" 2>&1 | sed 's/^/    [story] /' || true
fi

echo "[$(date -u '+%F %T UTC')] SPK onay kontrolü tamamlandı"
