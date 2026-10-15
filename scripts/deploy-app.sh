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
cp "$REPO/data/tufe-aylik.json" "$REPO/data/benchmarks.json" "$DEST/"   # reel getiri + kıyas serileri
# BIST kodu → parafomo.com halka arz şirket sayfası (portföy "İlgili veri" köprüsü)
python3 -c "import json,sys; d=json.load(open('$REPO/data/halka-arz-sirketler.json')); json.dump({i['bist_code']: i['slug'] for i in d['items'].values() if i.get('bist_code') and i.get('slug')}, open('$DEST/halka-arz-map.json','w'))"
chmod -R a+rX "$DEST"
echo "[app] yayınlandı -> $DEST"
