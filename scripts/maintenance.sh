#!/usr/bin/env bash
#
# ParaFOMO — günlük BAKIM (token'sız): disk, log, önbellek, git hijyeni.
#
# Neden (2026-10 otopsisi): disk %83'e dayanmıştı — 2 GB yayınlanmış video render'ı
# public/social'da duruyor, her `npm run build` bunları dist/'e bir kez daha kopyalıyordu
# (+2 GB, yavaş build); görsel/B-roll önbelleği 2.8 GB'a şişmişti.
#
# Silinenler YENİDEN ÜRETİLEBİLİR: videolar YouTube/IG'de yayında ve senaryoları git'te;
# önbellek gerektiğinde yeniden indirilir.
#
# Cron: 30 4 * * * /root/parafomo/scripts/maintenance.sh >> /root/parafomo/logs/maintenance.log 2>&1

set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="/root"
REPO="/root/parafomo"
cd "$REPO" || exit 0
. "$REPO/scripts/lib/gitsync.sh"

echo "=================================================="
echo "[$(date -u '+%F %T UTC')] Bakım başladı — disk: $(df -h / | awk 'NR==2{print $5" dolu, "$4" boş"}')"

# 1) Yayınlanmış video render'ları — 14 günden eski MP4 (kaynak YouTube/IG + git'teki senaryo)
n=$(find public/social -maxdepth 1 -name '*.mp4' -mtime +14 -print -delete 2>/dev/null | wc -l)
echo "[*] eski video render'ı silindi: $n"

# 2) Medya önbellekleri — 30 gündür hiç okunmamış dosyalar
n=$(find /root/.cache/parafomo/broll /root/.cache/parafomo/viral-visuals -type f -atime +30 -print -delete 2>/dev/null | wc -l)
echo "[*] kullanılmayan önbellek dosyası silindi: $n"

# 3) Büyük logları kırp (8 MB üstü → son 2 MB kalır)
for f in logs/*.log logs/*.jsonl; do
  [ -f "$f" ] || continue
  if [ "$(stat -c %s "$f")" -gt 8000000 ]; then
    tail -c 2000000 "$f" > "$f.tmp" && mv "$f.tmp" "$f" && echo "[*] log kırpıldı: $f"
  fi
done

# 4) Ajan koşu logları — 45 günden eski
find agent/logs -type f -mtime +45 -delete 2>/dev/null

# 4b) Yedek: portföy DB (gerçek kullanıcı verisi) + ayarlar → /root/parafomo-backups (repo dışı)
bash "$REPO/scripts/backup.sh" 2>&1 | sed 's/^/    /'

# 5) Git hijyeni — yalnız ajan/ağır iş ÇALIŞMIYORSA (ağır-iş kilidi boştaysa)
if flock -n "$REPO/.git/parafomo-heavy.lock" true; then
  git_locked bash -c '
    if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ]; then
      { git rebase --abort || git rebase --quit; } >/dev/null 2>&1 && echo "[!] yarım kalmış rebase temizlendi"
    fi
    git gc --auto -q
  '
else
  echo "[i] ajan çalışıyor — git hijyeni atlandı"
fi

echo "[$(date -u '+%F %T UTC')] Bakım tamam — disk: $(df -h / | awk 'NR==2{print $5" dolu, "$4" boş"}')"
