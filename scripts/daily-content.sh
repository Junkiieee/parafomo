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
{ git fetch origin main && git rebase --autostash origin/main; } || echo "UYARI: pull başarısız, devam ediliyor"

# 1b) Ekonomik takvimi güncelle (tek dış sorgu; içerik seçimi bunu okuyabilir)
echo "[*] Ekonomik takvim çekiliyor"
python3 "$REPO/scripts/fetch-economic-calendar.py" 2>&1 | sed 's/^/    [takvim] /' || echo "UYARI: takvim güncellenemedi (devam)"

# 1b2) BIST halka arz takvimini güncelle (data/halka-arz.json -> /halka-arz sayfası)
echo "[*] Halka arz takvimi çekiliyor"
python3 "$REPO/scripts/fetch-halka-arz.py" 2>&1 | sed 's/^/    [halka-arz] /' || echo "UYARI: halka arz takvimi güncellenemedi (devam)"

# 1c) GSC fırsat sorgularını güncelle (içerik seçimi KAYNAK (b) — takvimden sonra,
#     backlog'dan önce). venv'de google kütüphaneleri var (sistem Python'da yok).
echo "[*] GSC fırsat sorguları çekiliyor"
GSC_PY="/root/.venvs/parafomo/bin/python"
[ -x "$GSC_PY" ] || GSC_PY="python3"
"$GSC_PY" "$REPO/scripts/seo-opportunities.py" 2>&1 | sed 's/^/    [seo] /' || echo "UYARI: GSC fırsatları güncellenemedi (motor backlog'a düşer)"

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

# 5) Telegram kanalına (@parafomo) yeni yazıyı gönder (dedup'lı — aynı yazıyı 2 kez atmaz)
echo "[*] Telegram'a gönderiliyor"
"$REPO/scripts/post-telegram.sh" || echo "UYARI: Telegram gönderimi başarısız (devam)"

echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Tamamlandı"
