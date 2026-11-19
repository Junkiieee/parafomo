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
. "$REPO/scripts/lib/gitsync.sh"
cd "$REPO" || { echo "HATA: repo yok"; exit 1; }

echo "[$(date -u '+%F %T UTC')] Halka arz güncelleme başladı"

# Uzakla senkronla (çakışmayı önle)
git_sync >/dev/null 2>&1 || echo "UYARI: pull başarısız (devam)"

# Veriyi çek (ağ hatasında mevcut JSON'u korur, çökmez)
python3 "$REPO/scripts/fetch-halka-arz.py" 2>&1 | sed 's/^/  /'

# Getiri analizini güncelle (Yahoo güncel fiyatları; ağ hatasında mevcut depoyu korur)
python3 "$REPO/scripts/ipo-returns.py" 2>&1 | sed 's/^/  /'

# Değişiklik var mı? (hem build verisi hem public kopya)
FILES=(data/halka-arz.json data/halka-arz-sirketler.json public/halka-arz.json data/halka-arz-getiri.json public/halka-arz-getiri.json)
DURUM="$(git status --porcelain -- "${FILES[@]}")"
if [ -z "$DURUM" ]; then
  echo "[i] Değişiklik yok — deploy gerekmiyor."
  exit 0
fi
# Yalnız "updated" zaman damgası değiştiyse geri al, deploy yok. Neden (denetim 2026-11-18, zamanlama-5): 7 günde
# 28 commit'in 17'si yalnız bu satırdı (gece/hafta sonu BIST kapalıyken) → her biri build + deploy, 79 /halka-arz/
# sayfasında sahte dateModified/lastmod (src/data/page-lastmod.mjs: "lastmod yalnız veri gerçekten değişince").
# Desen satıra sabit: küçültülmüş tek satır JSON'da gerçek değişiklik yutulmaz. Yeni (izlenmeyen) dosya varsa atlanmaz.
TS_ONLY='^ *"updated": *"[^"]*",? *$'
if ! printf '%s\n' "$DURUM" | grep -q '^??' && git diff --quiet -I"$TS_ONLY" -- "${FILES[@]}"; then
  git_locked git checkout -q -- "${FILES[@]}"
  echo "[i] Değişiklik yok (yalnız zaman damgası) — deploy gerekmiyor."
  exit 0
fi

echo "[*] Değişiklik bulundu, commit + push"
git_add_commit "halka-arz: takvim verisi güncellendi (otomatik $(date -u '+%F %H:%M UTC'))" \
  "${FILES[@]}" \
  || { echo "commit başarısız"; exit 0; }
if git_push_retry main; then
  echo "[+] Push başarılı — Cloudflare deploy tetiklendi"
else
  echo "[!] Push başarısız"
  exit 2
fi
