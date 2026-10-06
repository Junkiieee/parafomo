# 🚀 PLANLANMIŞ BÜYÜK ÖZELLİK — Ücretsiz Portföy Takip Sistemi

> ✅✅ **TAMAMEN BİTTİ ve CANLI (2026-09-02, RC oturumunda tek seferde — plandaki çok-gecelik iş bir oturumda).**
> Backend main'de + systemd `parafomo-api` + Caddy **https://api.parafomo.com** (TLS). Sayfalar canlı:
> /portfoy-takip (halka açık SEO + üyeliksiz hesaplayıcı), /portfoy/panel (üye paneli), /portfoy/sifre-sifirla.
> E-posta+şifre auth + Google girişi (kod) + şifre sıfırlama (kod) + canlı değerleme (Yahoo+Truncgil).
> Aşağıdaki tüm adımlar (ilk gece + sonraki geceler) YAPILDI. Detay: `deploy/DEPLOY.md`, `tasks-for-user.md`.
> **Sadece 2 opsiyonel dış girdi bekliyor (şart değil):** Google Client ID (`PUBLIC_/PORTFOLIO_GOOGLE_CLIENT_ID`)
> + SMTP (`PORTFOLIO_SMTP_*`). Venv: `/root/.venvs/parafomo-api`.

## Amaç
İnsanların **ücretsiz** kullanacağı bir portföy takip sistemi → kullanıcı sürekli
siteye geri gelir → kalıcı trafik + sadık kitle + büyüme kaldıracı.

## Kapsam (kullanıcı ne yapacak)
- Kendi **hesabını oluşturur** (üyelik).
- Portföyüne **BIST hisseleri + altın + gümüş** ekler — **manuel** giriş (adet/gram + alış fiyatı/tarihi).
- Portföyün **güncel değerini + kâr/zararını** canlı fiyatlarla takip eder.

## Kullanıcının onayladığı kararlar (2026-08-30)
1. **Fiyat verisi:** mevcut ücretsiz kaynaklar kullanılacak — BIST hisse → Yahoo Finance
   (`<TICKER>.IS`), altın/gümüş → Truncgil (zaten repoda). **Paralı API ALINMAYACAK.**
   Gerçek bir eksik (ör. gecikmesiz fiyat, kapsanmayan ticker) çıkarsa → `tasks-for-user.md`'ye
   yaz, kullanıcı satın alsın. Kendi başına ücretli servise geçme.
2. **Depolama:** **bu sunucuda** (Hetzner 91.107.202.64). Cloudflare D1 değil.
3. **Giriş:** hem **e-posta + şifre** hem **Google ile giriş** (ikisi de).
4. **SEO ZORUNLU — "her şeyiyle düzgün":** aşağıdaki SEO bölümü şart.

## Önerilen mimari (kullanıcıyla mutabık — ajan iyileştirebilir)
- **İki katman:**
  - *Halka açık SEO sayfaları* (tanıtım + üyeliksiz "portföy değeri hesaplama" aracı):
    Astro statik → Cloudflare Pages (mevcut hat). Tam indekslenebilir.
  - *Uygulama* (üyelik + özel portföy paneli): **bu sunucuda backend** — FastAPI (Python,
    mevcut venv/araç setiyle uyumlu) + veritabanı, systemd servis + Caddy reverse-proxy,
    subdomain `api.parafomo.com` (Cloudflare DNS → sunucu, TLS Caddy'de).
- **Veritabanı:** başta **SQLite** (kur-çalıştır kolay, binlerce kullanıcıya yeter). Büyürse Postgres.
- **Auth:** e-posta+şifre (argon2/bcrypt hash) + Google OAuth. Oturum = JWT. Şifre sıfırlama akışı.
- **Panel:** giriş sonrası client-side (Astro island / küçük SPA), API'yi JWT ile çağırır.
- **Güvenlik:** sunucu hardening desenine uy (localhost'a bind + Caddy önünde), sırlar `.env`'de,
  parola hash'li, rate-limit, CORS yalnız parafomo.com. Canlı `main`/siteyi bozma; ayrı dalda dene, build geçmeden deploy etme.

## SEO — ZORUNLU (kullanıcı özellikle vurguladı: "her şeyiyle düzgün")
- **Trafik mıknatısı = halka açık sayfalar:**
  - Tanıtım sayfası: hedef sorgular "ücretsiz portföy takip", "bist portföy takip programı",
    "altın gümüş portföy takibi", "hisse takip uygulaması" vb. (GSC/`seo-opportunities.md`'den doğrula).
  - **Üyeliksiz "portföy değeri hesaplama" aracı** (hesap açmadan holding girip anlık değer görür) —
    hem güçlü SEO aracı hem üyeliğe huni. Statik + client-side hesap.
- **Tam teknik SEO:** benzersiz title/description, `Article`+`FAQPage`+`BreadcrumbList` şeması,
  OG görseli (social-card), mevcut `/altin-*`, `/bist-*`, `/halka-arz` sayfalarından iç link,
  sitemap'e ekleme, hızlı statik yük. `daily-content.sh`'daki SEO doğrulama grep'ini bu sayfalara da uygula.
- **Panel/login sayfaları:** `noindex` + robots disallow + canonical halka açık sayfaya. SEO'ya girmesin.

## İlk gece (Perşembe) önerilen ilk adım
Hepsini bir gecede bitirme. Perşembe: mimariyi kur (backend iskeleti + DB şeması + auth’un e-posta
kısmı + tek uçtan uca akış: kayıt → 1 hisse ekle → değer gör) + halka açık tanıtım sayfası taslağı.
Sonraki geceler: Google OAuth, altın/gümüş, kâr/zarar, SEO cilası, üyeliksiz hesaplama aracı.
