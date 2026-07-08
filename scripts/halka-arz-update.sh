#!/usr/bin/env bash
#
# ParaFOMO — BIST halka arz takvimini gün içinde güncel tutar (cron).
# fetch-halka-arz.py ile halkarz.com'dan veriyi çeker; data/halka-arz.json
# DEĞİŞTİYSE commit + push eder (Cloudflare otomatik deploy → /halka-arz tazelenir).
# Değişiklik yoksa hiçbir şey yapmaz (gürültüsüz, idempotent).
#
# Cron örneği (her 6 saatte bir):
#   15 */6 * * * /root/parafomo/scripts/halka-arz-update.sh >> /root/parafomo/logs/halka-arz.log 2>&1

set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"

REPO="/root/parafomo"
cd "$REPO" || { echo "HATA: repo yok"; exit 1; }

echo "[$(date -u '+%F %T UTC')] Halka arz güncelleme başladı"

# Uzakla senkronla (çakışmayı önle)
{ git fetch origin main && git rebase --autostash origin/main; } >/dev/null 2>&1 || echo "UYARI: pull başarısız (devam)"

# Veriyi çek (ağ hatasında mevcut JSON'u korur, çökmez)
python3 "$REPO/scripts/fetch-halka-arz.py" 2>&1 | sed 's/^/  /'

# Değişiklik var mı? (hem build verisi hem public kopya)
if [ -z "$(git status --porcelain data/halka-arz.json public/halka-arz.json)" ]; then
  echo "[i] Değişiklik yok — deploy gerekmiyor."
  exit 0
fi

echo "[*] Değişiklik bulundu, commit + push"
git add data/halka-arz.json public/halka-arz.json
git commit -m "halka-arz: takvim verisi güncellendi (otomatik $(date -u '+%F %H:%M UTC'))" || { echo "commit başarısız"; exit 0; }
if git push origin main 2>&1 | sed 's/^/  [push] /'; then
  echo "[+] Push başarılı — Cloudflare deploy tetiklendi"
else
  echo "[!] Push başarısız"
  exit 2
fi
