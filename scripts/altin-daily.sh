#!/usr/bin/env bash
#
# ParaFOMO — Günlük altın fiyatları Instagram postu (bu sunucuda cron ile).
# Akış: rastgele 0-59 dk bekle -> senkronla -> kart üret -> commit+push
#       -> görsel GitHub raw'da canlı olunca -> IG'ye postla.
# Cron: 0 6 * * *  (06:00 UTC = 09:00 TR; +rastgele dk ile 09:00-10:00 TR arası)
#
set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"

REPO="/root/parafomo"
VENV_PY="/root/.venvs/parafomo/bin/python"
[ -x "$VENV_PY" ] || VENV_PY="python3"
cd "$REPO" || { echo "HATA: repo yok"; exit 1; }

echo "[$(date -u '+%F %T UTC')] Altın IG postu başladı"

# 0) Rastgele 0-59 dk bekle (her gün farklı dakika → 09:00-10:00 TR arası)
if [ "${1:-}" != "--now" ]; then
  WAIT=$(( RANDOM % 3540 ))
  echo "[*] Rastgele bekleme: $((WAIT/60)) dk $((WAIT%60)) sn"
  sleep "$WAIT"
fi

# 1) Senkronla
git pull --rebase --autostash origin main >/dev/null 2>&1 || echo "UYARI: pull başarısız (devam)"

# 2) Günlük kartı üret
echo "[*] Kart üretiliyor"
"$VENV_PY" "$REPO/scripts/altin-card.py" 2>&1 | sed 's/^/    [kart] /' || { echo "HATA: kart üretilemedi"; exit 1; }

STAMP=$(TZ=Europe/Istanbul date '+%Y%m%d')
IMG="public/social/altin-${STAMP}.jpg"
[ -f "$IMG" ] || { echo "HATA: $IMG yok"; exit 1; }

# 3) Eski kartları buda (son 14 gün kalsın — repo şişmesin)
find public/social -name 'altin-*.jpg' -type f -mtime +14 -delete 2>/dev/null || true
rm -f public/social/altin-today.jpg 2>/dev/null || true  # önizleme artığı

# 4) Commit + push (görseli GitHub'a taşır → raw URL canlı olur)
git add public/social/altin-*.jpg
if ! git diff --cached --quiet; then
  git commit -m "altın: günlük IG kartı ${STAMP}" >/dev/null 2>&1
  if git push origin main 2>&1 | sed 's/^/    [push] /'; then
    echo "[+] Push başarılı"
  else
    echo "HATA: push başarısız"; exit 1
  fi
else
  echo "[i] Kart zaten commit'li"
fi

# 5) Görsel GitHub raw'da canlı olana kadar bekle (max ~3 dk)
RAW="https://raw.githubusercontent.com/Junkiieee/parafomo/main/${IMG}"
echo "[*] Görselin canlı olması bekleniyor: $RAW"
ok=0
for i in $(seq 1 18); do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$RAW")
  if [ "$code" = "200" ]; then ok=1; echo "[+] Görsel canlı (deneme $i)"; break; fi
  sleep 10
done
[ "$ok" = "1" ] || { echo "HATA: görsel raw'da canlı olmadı"; exit 1; }

# 6) Instagram'a postla
echo "[*] Instagram'a postlanıyor"
python3 "$REPO/scripts/post-altin-instagram.py" 2>&1 | sed 's/^/    [ig] /'

echo "[$(date -u '+%F %T UTC')] Altın IG postu tamamlandı"
