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
cd /root/parafomo && npm run build && npx wrangler deploy
```

(Gecelik `daily-content.sh` cron'u da build+deploy yapar; yeni sayfalar o gece de yayına girer.)

## Kullanıcıdan beklenenler (opsiyonel özellikler için)

- **Google ile giriş**: Google Cloud Console → OAuth 2.0 **Web** İstemci Kimliği; yetkili JS
  kaynağı `https://parafomo.com`. Client ID'yi hem `backend/.env`'e (`PORTFOLIO_GOOGLE_CLIENT_ID`)
  hem site build ortamına (`PUBLIC_GOOGLE_CLIENT_ID`) koy. Boşken Google butonu gizli, e-posta girişi çalışır.
- **Şifre sıfırlama e-postası**: `backend/.env`'e SMTP bilgileri (`PORTFOLIO_SMTP_*`). Boşken akış
  çalışır ama link e-posta yerine servis loguna yazılır.
