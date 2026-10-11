#!/usr/bin/env bash
# app.parafomo.com — statik portföy uygulamasını yayınlar.
# Kaynak: repo app/ + public'ten güncel bist-symbols.json ve favicon.
# Hedef: /srv/parafomo-app (Caddy file_server; caddy kullanıcısı /root'u okuyamaz).
set -euo pipefail
REPO="/root/parafomo"
DEST="/srv/parafomo-app"
mkdir -p "$DEST"
rsync -a --delete "$REPO/app/" "$DEST/"
cp "$REPO/public/bist-symbols.json" "$REPO/public/favicon.svg" "$DEST/"
chmod -R a+rX "$DEST"
echo "[app] yayınlandı -> $DEST"
