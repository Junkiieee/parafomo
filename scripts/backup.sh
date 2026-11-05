#!/usr/bin/env bash
#
# ParaFOMO — günlük YEDEK: portföy veritabanı (gerçek kullanıcı verisi) + sunucu ayarları.
#
# Hedef: /root/parafomo-backups (repo DIŞI, chmod 700 — repo herkese açık, kullanıcı verisi
# ve sırlar ASLA git'e girmez). 14 gün saklanır.
# Uzak kopya (opsiyonel): /root/.config/parafomo/backup.env içinde R2/S3 bilgileri varsa
# (R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET) aynı dosyalar oraya da
# yüklenir. Yoksa yalnız yerel yedek alınır (sunucu diski çökerse korumaz).
# BACKUP_PASSPHRASE da tanımlıysa R2'ye yalnız ŞİFRELİ (.enc) kopya gider — DB kişisel veri (KVKK),
# config-*.tgz tüm sırlar. Parolayı ayrıca parola yöneticisinde sakla (sunucu giderse lazım). Açmak:
#   openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -in X.enc -out X   (parolayı sorar)
# Bir adım başarısızsa Kaan'a uyarı maili gider (günde bir; agent/notify.py).
#
# maintenance.sh her gün çağırır; elle: bash scripts/backup.sh
set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
DEST="/root/parafomo-backups"
DB="/root/parafomo-data/portfolio.db"
BOARD="/root/parafomo-data/board.json"
STAMP="$(date -u +%Y%m%d)"
FAIL=""
umask 077
mkdir -p "$DEST"
chmod 700 "$DEST"

# 1) SQLite: çalışan servisi durdurmadan tutarlı kopya (online backup API)
if [ -f "$DB" ]; then
  /root/.venvs/parafomo/bin/python - "$DB" "$DEST/portfolio-$STAMP.db" <<'PY' || FAIL="$FAIL portföy-DB"
import sqlite3, sys
src = sqlite3.connect(sys.argv[1]); dst = sqlite3.connect(sys.argv[2])
with dst:
    src.backup(dst)
ok = dst.execute("pragma integrity_check").fetchone()[0]
n = dst.execute("select count(*) from users").fetchone()[0]
dst.close(); src.close()
if ok != "ok":
    sys.exit(f"[backup] HATA: yedek bütünlük kontrolünden geçmedi: {ok}")
print(f"[backup] portföy DB yedeklendi ({n} kullanıcı) -> {sys.argv[2]}")
PY
else
  echo "[backup] UYARI: $DB yok"; FAIL="$FAIL portföy-DB-yok"
fi

# 1b) Panel kararları/notları (board.json: repo DIŞI, git'te kopyası YOK) + canlı crontab (şablondan sapmış olabilir)
if [ -f "$BOARD" ]; then
  cp "$BOARD" "$DEST/board-$STAMP.json" && echo "[backup] panel kararları (board.json) yedeklendi" || FAIL="$FAIL board.json"
fi
crontab -l > "$DEST/crontab-$STAMP.txt" 2>/dev/null || rm -f "$DEST/crontab-$STAMP.txt"

# 2) Sunucu ayarları + sırlar (kısıtlı izinle; backup.env varsa R2'ye de gider — BACKUP_PASSPHRASE yoksa ŞİFRESİZ)
# --ignore-failed-read: biri eksikse diğerleri yine arşivlenir ve bu "başarılı" sayılır (eskiden sessizce mesajsız kalıyordu)
tar -czf "$DEST/config-$STAMP.tgz" -C / --ignore-failed-read \
  root/parafomo/.env root/parafomo/backend/.env root/.config/parafomo etc/caddy/Caddyfile \
  2>/dev/null && echo "[backup] ayarlar yedeklendi -> $DEST/config-$STAMP.tgz" || FAIL="$FAIL ayarlar"

# 3) Eskileri buda (14 gün)
find "$DEST" -maxdepth 1 -type f \( -name 'portfolio-*.db' -o -name 'config-*.tgz' -o -name 'board-*.json' -o -name 'crontab-*.txt' \) -mtime +14 -delete

# 4) Uzak kopya (yapılandırılmışsa)
if [ -f /root/.config/parafomo/backup.env ]; then
  set -a; . /root/.config/parafomo/backup.env; set +a
  if [ -n "${R2_ACCOUNT_ID:-}" ] && [ -n "${R2_BUCKET:-}" ]; then
    UP=()
    for p in "$DEST/portfolio-$STAMP.db" "$DEST/board-$STAMP.json" "$DEST/config-$STAMP.tgz"; do
      [ -f "$p" ] || continue
      if [ -n "${BACKUP_PASSPHRASE:-}" ]; then
        openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt -pass env:BACKUP_PASSPHRASE -in "$p" -out "$p.enc" \
          && UP+=("$p.enc") || FAIL="$FAIL şifreleme"
      else
        UP+=("$p")
      fi
    done
    [ -n "${BACKUP_PASSPHRASE:-}" ] || echo "[backup] UYARI: BACKUP_PASSPHRASE yok — R2'ye ŞİFRESİZ gidiyor (kişisel veri + sırlar)"
    /root/.venvs/parafomo/bin/python - "${UP[@]}" <<'PY' \
      || { echo "[backup] UYARI: uzak yükleme başarısız"; FAIL="$FAIL uzak-kopya"; }
import os, sys
import boto3
from botocore.config import Config
# R2 joker sertifikası bucket'lı alt alan adını kapsamıyor → virtual-host stili TLS'te düşer, path şart
s3 = boto3.client("s3", endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
                  aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                  aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"], region_name="auto",
                  config=Config(s3={"addressing_style": "path"}))
for p in sys.argv[1:]:
    if os.path.exists(p):
        s3.upload_file(p, os.environ["R2_BUCKET"], "parafomo/" + os.path.basename(p))
        print("[backup] uzak kopya:", os.path.basename(p))
PY
    rm -f "$DEST"/*.enc
  fi
fi

# 5) Sessiz başarısızlık olmasın: maintenance.log'u kimse okumuyor → mail (notify.py aynı anahtarla günde bir)
if [ -n "$FAIL" ]; then
  echo "[backup] HATA: başarısız adım(lar):$FAIL"
  python3 /root/parafomo/agent/notify.py alert --key backup-failed --subject "parafomo: YEDEK başarısız ($FAIL )" \
    --body "scripts/backup.sh şu adımlarda başarısız oldu:$FAIL. Ayrıntı: /root/parafomo/logs/maintenance.log (son 'Bakım başladı' bölümü)." >/dev/null 2>&1 || true
  exit 1
fi
