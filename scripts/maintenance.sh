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
#    public/social (üst düzey) + anim/ + longform/ (2026-11-18: alt klasörler hiç silinmiyordu, her build dist'e
#    kopyalıyordu). Kuyrukta bekleyen/onaylı video ve yayımlanmamış (zamanlanmış özel) uzun video KORUNUR.
# 1b) Render önbelleği iş klasörleri (/root/.cache/parafomo/anim, longform; ~1 GB) — 14 gündür dokunulmamış olanlar
#    (tts/ ve bekleyen slug'lar hariç). Ayrıntı: scripts/lib/medya_temizle.py
python3 "$REPO/scripts/lib/medya_temizle.py" --gun 14 2>&1 || echo "[!] medya_temizle.py hata verdi (devam)"

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

# 4) Ajan koşu logları — 45 günden eski; sabah rutininin geçici script/kare sayfaları (agent/tmp) — 7 günden eski
find agent/logs -type f -mtime +45 -delete 2>/dev/null
find agent/tmp -type f -mtime +7 -delete 2>/dev/null

# 4b) Yedek: portföy DB (gerçek kullanıcı verisi) + ayarlar → /root/parafomo-backups (repo dışı)
bash "$REPO/scripts/backup.sh" 2>&1 | sed 's/^/    /'

# 5) Git hijyeni — yalnız ajan/ağır iş ÇALIŞMIYORSA; ağır-iş kilidi hijyen boyunca TUTULUR
#    (haftalık gc birkaç dakika sürebilir; sabah rutini 04:37'de kilidi bekler, yarışmaz).
#    instagram-reel.py her Reel mp4'ünü `hash-object -w` ile ana depoya yazıp media dalına force-push'luyor;
#    refs/remotes/origin/media reflog'u (90 gün) bu blob'ları tutuyordu (~0.65 GB, denetim 2026-11-18 repo-2).
#    Günlük: o reflog'u 3 günde budar. Pazar: gc --prune=3.days.ago (büyük dosyada delta araması yok: 3 GB RAM).
exec 7>"$REPO/.git/parafomo-heavy.lock"
if flock -n 7; then
  git_locked bash -c '
    if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ]; then
      { git rebase --abort || git rebase --quit; } >/dev/null 2>&1 && echo "[!] yarım kalmış rebase temizlendi"
    fi
    git reflog expire --expire=3.days.ago --expire-unreachable=3.days.ago refs/remotes/origin/media >/dev/null 2>&1
    if [ "$(date -u +%u)" = 7 ]; then
      once=$(du -sm .git | cut -f1)
      if nice -n 19 git -c core.bigFileThreshold=2m -c pack.threads=1 gc --prune=3.days.ago -q; then
        echo "[*] haftalık git gc: .git ${once} MB → $(du -sm .git | cut -f1) MB"
      else
        echo "[!] haftalık git gc başarısız"
      fi
    else
      git gc --auto -q
    fi
  '
  flock -u 7
else
  echo "[i] ajan çalışıyor — git hijyeni atlandı"
fi
exec 7>&-

# 6) Disk uyarısı (2026-11-18: %89 / 4.0 GB boşa inene kadar kimse uyarılmadı). Boş < 4 GB ya da ≥ %90 →
#    Kaan'a günde bir uyarı + en büyük dizinler (silinebilir adaylar). Eşik agent/health.py ile aynı.
avail_kb=$(df --output=avail -k / | tail -1 | tr -dc 0-9)
pct=$(df --output=pcent / | tail -1 | tr -dc 0-9)
if [ "${avail_kb:-0}" -lt 4000000 ] || [ "${pct:-0}" -ge 90 ]; then
  echo "[!] disk %$pct dolu, $((avail_kb / 1024 / 1024)) GB boş — uyarı"
  python3 "$REPO/agent/notify.py" alert --key disk --subject "parafomo: disk %$pct dolu ($((avail_kb / 1024)) MB boş)" \
    --body "$(printf 'Boş alan azaldı: %s MB (%%%s dolu). 1 GB altında build/render/SQLite yazımı patlar.\n\nEn büyük dizinler:\n%s\n\nSilinebilir adaylar: kullanılmayan Whisper modelleri (~/.cache/huggingface), eski Claude CLI sürümleri (~/.local/share/claude/versions), parafomo dışı klasörler (Kaan kararı).\nBakım her gün eski render + önbellek siler (scripts/maintenance.sh).' \
      "$((avail_kb / 1024))" "$pct" \
      "$(du -xsh /root/.cache/* /root/.local/share/claude /root/parafomo/.git /root/parafomo/dist /root/parafomo/public/social /root/parafomo-backups /root/parafomo-data /root/binance /srv/* 2>/dev/null | sort -rh | head -15)")" \
    >/dev/null 2>&1 || true
fi

echo "[$(date -u '+%F %T UTC')] Bakım tamam — disk: $(df -h / | awk 'NR==2{print $5" dolu, "$4" boş"}')"
