#!/usr/bin/env bash
#
# ParaFOMO — günlük YEDEK: portföy veritabanı (gerçek kullanıcı verisi) + sunucu ayarları.
#
# Hedef: /root/parafomo-backups (repo DIŞI, chmod 700 — repo herkese açık, kullanıcı verisi
# ve sırlar ASLA git'e girmez). 14 gün saklanır.
# Uzak kopya (opsiyonel): /root/.config/parafomo/backup.env içinde R2/S3 bilgileri varsa
# (R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET) aynı dosyalar oraya da
# yüklenir. Yoksa yalnız yerel yedek alınır (sunucu diski çökerse korumaz).
#
# maintenance.sh her gün çağırır; elle: bash scripts/backup.sh
set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
DEST="/root/parafomo-backups"
DB="/root/parafomo-data/portfolio.db"
STAMP="$(date -u +%Y%m%d)"
umask 077
mkdir -p "$DEST"
chmod 700 "$DEST"

# 1) SQLite: çalışan servisi durdurmadan tutarlı kopya (online backup API)
if [ -f "$DB" ]; then
  /root/.venvs/parafomo/bin/python - "$DB" "$DEST/portfolio-$STAMP.db" <<'PY'
import sqlite3, sys
src = sqlite3.connect(sys.argv[1]); dst = sqlite3.connect(sys.argv[2])
with dst:
    src.backup(dst)
n = dst.execute("select count(*) from users").fetchone()[0]
dst.close(); src.close()
print(f"[backup] portföy DB yedeklendi ({n} kullanıcı) -> {sys.argv[2]}")
PY
else
  echo "[backup] UYARI: $DB yok"
fi

# 2) Sunucu ayarları + sırlar (yalnız yerel, kısıtlı izinle)
tar -czf "$DEST/config-$STAMP.tgz" -C / \
  root/parafomo/.env root/parafomo/backend/.env root/.config/parafomo etc/caddy/Caddyfile \
  2>/dev/null && echo "[backup] ayarlar yedeklendi -> $DEST/config-$STAMP.tgz"

# 3) Eskileri buda (14 gün)
find "$DEST" -maxdepth 1 -type f \( -name 'portfolio-*.db' -o -name 'config-*.tgz' \) -mtime +14 -delete

# 4) Uzak kopya (yapılandırılmışsa)
if [ -f /root/.config/parafomo/backup.env ]; then
  set -a; . /root/.config/parafomo/backup.env; set +a
  if [ -n "${R2_ACCOUNT_ID:-}" ] && [ -n "${R2_BUCKET:-}" ]; then
    /root/.venvs/parafomo/bin/python - "$DEST/portfolio-$STAMP.db" "$DEST/config-$STAMP.tgz" <<'PY' \
      || echo "[backup] UYARI: uzak yükleme başarısız"
import os, sys
import boto3
s3 = boto3.client("s3", endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
                  aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                  aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"], region_name="auto")
for p in sys.argv[1:]:
    if os.path.exists(p):
        s3.upload_file(p, os.environ["R2_BUCKET"], "parafomo/" + os.path.basename(p))
        print("[backup] uzak kopya:", os.path.basename(p))
PY
  fi
fi
