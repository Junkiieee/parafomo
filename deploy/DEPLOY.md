# Portföy Takip — Dağıtım

Backend bu sunucuda (Hetzner 91.107.202.64) systemd + Caddy ile çalışır. Statik
site (Astro) Cloudflare'e deploy edilir. Fiyat kaynakları ücretsiz (Yahoo `.IS` +
Truncgil). Plan: `agent/state/feature-backlog.md`.

## Backend servisi (kurulu)

- Kod: `/root/parafomo/backend` (main)
- Venv: `/root/.venvs/parafomo-api` (`pip install -r backend/requirements.txt`)
- Ortam: `backend/.env` (gitignore'lu, chmod 600). Şablon: `backend/.env.example`
- Veritabanı: `/root/parafomo-data/portfolio.db` (SQLite, repo dışı)
- Servis: `deploy/parafomo-api.service` → `/etc/systemd/system/parafomo-api.service`
- Dinleme: `127.0.0.1:8000` (yalnız localhost; internete Caddy açar)

Komutlar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now parafomo-api.service
sudo systemctl status parafomo-api.service
sudo systemctl restart parafomo-api.service      # kod güncellenince
journalctl -u parafomo-api.service -f            # log
curl -s http://127.0.0.1:8000/health
```

## Public erişim: api.parafomo.com

1. **DNS** (Cloudflare): `api.parafomo.com` A → `91.107.202.64`, **DNS-only (gri bulut)**
   — Caddy Let's Encrypt HTTP-01 doğrulamasını doğrudan yapsın.
2. **Caddy**: `deploy/Caddy-api.conf` bloğunu `/etc/caddy/Caddyfile`'a ekle →
   `sudo systemctl reload caddy`. İlk istekte sertifika otomatik alınır.
3. Doğrula: `curl -s https://api.parafomo.com/health`

## Statik site (Cloudflare)

Panel/araç sayfaları API'yi `https://api.parafomo.com` olarak çağırır (sabit varsayılan;
`localStorage.pf_api_base` ile yerelde override edilir). Deploy:

```bash
cd /root/parafomo && bash scripts/deploy-push.sh
```

Canlıya giden tek yol **git push**'tur: `deploy-push.sh` önce kilitli `npm run build` alır, geçerse
push'lar; Cloudflare push'tan siteyi kendisi derleyip yayınlar (1-3 dk). Sunucudan elle
`npx wrangler deploy` YAPMA: commit'lenmemiş çalışma dizinini yayınlar, sonraki push'un derlemesi de
onu sessizce ezer. (Cron'ların push'ları da aynı build kapısından geçer: `scripts/lib/gitsync.sh`.)

## Servisleri güncelleme (deploy/*.service, deploy/Caddy-*.conf)

Repo'daki bu dosyalar ŞABLONDUR; değişiklik sunucuya kendiliğinden geçmez.

```bash
sudo cp /root/parafomo/deploy/parafomo-api.service /root/parafomo/deploy/parafomo-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl restart parafomo-api parafomo-dashboard
systemctl is-active parafomo-api parafomo-dashboard        # ikisi de "active"
curl -s http://127.0.0.1:8000/health                       # {"status":"ok"}
journalctl -u parafomo-api -u parafomo-dashboard -n 30 --no-pager   # "Permission denied"/"Read-only" yok
```

Sonra panelde bir nota bir harf yazıp "kaydedildi" görmeli, Üretim sekmesinde takvim dolu olmalı.
Bozulursa: ilgili `.service` dosyasındaki `# --- Sertleştirme` bloğunu silip yukarıdaki iki
`systemctl` satırını tekrarla. Caddy bloğu değişince: `/etc/caddy/Caddyfile`'daki bloğu yenisiyle
değiştir (`<BCRYPT_HASH>` yerine mevcut hash kalsın) → `caddy validate --config /etc/caddy/Caddyfile`
→ `sudo systemctl reload caddy`. `dashboard/server.py` değişince: `sudo systemctl restart parafomo-dashboard`
(app.js/index.html değişikliği git sync ile anında geçer, yeniden başlatma gerekmez).
`deploy/crontab.txt` değişince: önce `crontab -l | diff - /root/parafomo/deploy/crontab.txt` — fark yalnız
yeni değişiklikse `crontab /root/parafomo/deploy/crontab.txt` (canlı crontab'da şablonda olmayan bir satır
varsa önce onu şablona taşı; kurulum tüm crontab'ı değiştirir).

`app.parafomo.com` bloğu repoda yoktu: `deploy/Caddy-app.conf` başvuru şablonudur — mevcut bloğa
`Cache-Control: no-cache` (HTML/JS/CSS/JSON/sw.js) ve güvenlik başlık satırlarını ekle; yoksa yayından sonra
kullanıcılar eski uygulama sürümünü görebilir. Doğrula: `curl -sI https://app.parafomo.com/portfoy/app.js | grep -i cache-control`.

Cron saatleri **UTC**'dir (`deploy/crontab.txt`); sunucu saat dilimi UTC olmalı:
`timedatectl | grep "Time zone"` → `Etc/UTC` (değilse tüm işler ve paneldeki takvim 3 saat kayar).

## Yedek ve geri yükleme

`scripts/backup.sh` her gün 04:30 UTC'de (`maintenance.sh` içinden) `/root/parafomo-backups/`
altına `portfolio-YYYYMMDD.db` (portföy DB'si, tutarlı kopya) + `config-YYYYMMDD.tgz` (`.env`'ler,
`~/.config/parafomo`, Caddyfile) yazar; 14 gün saklar; `backup.env` varsa R2'ye de yükler.
Son yedeğin tarihi: `ls -lt /root/parafomo-backups | head -3` (bugünün/dünün tarihi görünmeli).

Portföy DB'sini geri yükleme (ör. `portfolio-20261102.db`):

```bash
B=/root/parafomo-backups/portfolio-20261102.db
/root/.venvs/parafomo/bin/python -c "import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute('pragma integrity_check').fetchone()[0])" "$B"   # "ok" yazmalı
sudo systemctl stop parafomo-api
cd /root/parafomo-data && for f in portfolio.db portfolio.db-journal portfolio.db-wal portfolio.db-shm; do [ -e "$f" ] && mv "$f" "$f.eski-$(date +%F)"; done
cp "$B" /root/parafomo-data/portfolio.db && chmod 600 /root/parafomo-data/portfolio.db
sudo systemctl start parafomo-api && curl -s http://127.0.0.1:8000/health
```

Sunucu tamamen gittiyse: Cloudflare → R2 → yedek bucket'ı → `parafomo/portfolio-…db` ve
`parafomo/config-…tgz` dosyalarını indir (`.enc` uzantılıysa şifrelidir: `scripts/backup.sh` başındaki
`openssl enc -d …` komutuyla aç); yeni sunucuda `tar -xzf config-….tgz -C /` ayarları,
yukarıdaki adımlar DB'yi geri koyar. Yedek ile son durum arasındaki (en çok ~1 gün) kayıtlar kaybolur.

## Kullanıcıdan beklenenler (opsiyonel özellikler için)

- **Google ile giriş**: Google Cloud Console → OAuth 2.0 **Web** İstemci Kimliği; yetkili JS
  kaynağı `https://parafomo.com`. Client ID'yi hem `backend/.env`'e (`PORTFOLIO_GOOGLE_CLIENT_ID`)
  hem site build ortamına (`PUBLIC_GOOGLE_CLIENT_ID`) koy. Boşken Google butonu gizli, e-posta girişi çalışır.
- **Şifre sıfırlama e-postası**: `backend/.env`'e SMTP bilgileri (`PORTFOLIO_SMTP_*`). Boşken akış
  çalışır ama link e-posta yerine servis loguna yazılır.
