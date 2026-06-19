#!/usr/bin/env bash
#
# ParaFOMO — günlük içerik motoru (bu sunucuda cron ile çalışır).
# Akış: repo'yu senkronla -> claude headless ile yeni yazı üret+commit -> push.
# Push olunca Cloudflare Pages otomatik deploy eder.
#
# Cron örneği (her gün 08:07 UTC):
#   7 8 * * * /root/parafomo/scripts/daily-content.sh >> /root/parafomo/logs/cron.log 2>&1

set -uo pipefail

# --- Cron'un sınırlı PATH'ini düzelt (node, npm, claude, git) ---
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"

REPO="/root/parafomo"
LOG_DIR="$REPO/logs"
PROMPT_FILE="$REPO/scripts/daily-prompt.md"
mkdir -p "$LOG_DIR"

STAMP="$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=================================================="
echo "[$STAMP] ParaFOMO günlük içerik motoru başladı"

cd "$REPO" || { echo "HATA: repo dizinine girilemedi"; exit 1; }

# 1) Uzak depo ile senkronla (çakışmayı önle)
echo "[*] git pull --rebase"
git pull --rebase --autostash origin main || echo "UYARI: pull başarısız, devam ediliyor"

# 2) Headless claude ile içerik üret (agent: yazıyı yazar, keywords/daily-log günceller, build eder, commit'ler)
echo "[*] claude headless çalışıyor (içerik üretimi)..."
PROMPT="$(cat "$PROMPT_FILE")"
claude -p "$PROMPT" \
  --model claude-sonnet-4-6 \
  --permission-mode acceptEdits \
  --allowedTools Bash Read Write Edit Glob Grep \
  2>&1 | sed 's/^/    [claude] /'

# 3) Güvenlik ağı: agent commit'lemediyse kalan değişiklikleri topla
if [ -n "$(git status --porcelain)" ]; then
  echo "[*] Commit edilmemiş değişiklikler bulundu, toplanıyor"
  git add -A
  git commit -m "içerik: otomatik günlük güncelleme ($(date -u '+%Y-%m-%d'))" || true
fi

# 4) Push (Cloudflare deploy'unu tetikler) — SSH deploy key ile şifresiz
if git log origin/main..HEAD --oneline 2>/dev/null | grep -q .; then
  echo "[*] Yerel commit'ler push ediliyor"
  if git push origin main 2>&1 | sed 's/^/    [push] /'; then
    echo "[+] Push başarılı — Cloudflare deploy tetiklendi"
  else
    echo "[!] HATA: push başarısız (SSH deploy key eklendi mi?)"
    exit 2
  fi
else
  echo "[i] Push edilecek yeni commit yok"
fi

echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Tamamlandı"
