# ParaFOMO Portföy API

Ücretsiz portföy takip sisteminin backend'i (FastAPI + SQLite). Kullanıcılar
üye olur, BIST hissesi / altın / gümüş pozisyonlarını **manuel** girer, canlı
fiyatlarla portföy değeri ve kâr/zararını görür.

Plan: `agent/state/feature-backlog.md`. Fiyatlar ücretsiz kaynaklardan
(BIST → Yahoo Finance `.IS`, altın/gümüş → Truncgil v3). Paralı API yok.

## Kurulum

```bash
python3 -m venv /root/.venvs/parafomo-api
/root/.venvs/parafomo-api/bin/pip install -r requirements.txt
cp .env.example .env      # PORTFOLIO_JWT_SECRET'ı güçlü bir değerle değiştir
```

## Çalıştırma (geliştirme)

```bash
cd backend
/root/.venvs/parafomo-api/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Dokümantasyon: http://127.0.0.1:8000/docs

## Uç noktalar (ilk gece)

| Metot | Yol | Açıklama |
|-------|-----|----------|
| POST | `/auth/register` | E-posta + şifre ile kayıt → JWT |
| POST | `/auth/login` | Giriş → JWT |
| GET | `/auth/me` | Oturum sahibi kullanıcı |
| POST | `/portfolio/holdings` | Pozisyon ekle |
| GET | `/portfolio/holdings` | Pozisyonları listele |
| DELETE | `/portfolio/holdings/{id}` | Pozisyon sil |
| GET | `/portfolio/summary` | Canlı değerleme + toplam kâr/zarar |
| GET | `/health` | Sağlık kontrolü |

Auth gerektiren uç noktalar `Authorization: Bearer <token>` bekler.

## Güvenlik notları

- Token'da parola parmak izi (`pwv`) var: şifre sıfırlanınca / hesap Google'a ilk kez
  bağlanınca o kullanıcının eski oturumları düşer.
- Giriş, kayıt, şifre sıfırlama, Google girişi, bülten ve `/public/*` IP başına hız
  sınırlıdır (`app/ratelimit.py`, süreç içi). Üyeliksiz uçların gönderdiği e-postalar
  ayrıca saatlik toplam bütçeye tabidir (`PORTFOLIO_PUBLIC_MAIL_PER_HOUR`).
- Gövde üst sınırı 64 KB (`/inbox/ingest` 6 MB); sayılarda NaN/Infinity reddedilir.

## Testler

Ağsız, geçici DB ile çalışır (gerçek `.env`, SMTP ve fiyat kaynaklarına dokunmaz):

```bash
pip install pytest   # requirements.txt'e ek
python -m pytest backend/tests        # repo kökünden
```

## Sonraki geceler (backlog)

- Google ile giriş (OAuth)
- Şifre sıfırlama akışı
- Halka açık "portföy değeri hesaplama" aracı (üyeliksiz, SEO)
- Panel (Astro island / SPA)
- Dağıtım: systemd servisi + Caddy reverse-proxy + `api.parafomo.com` (DNS)
