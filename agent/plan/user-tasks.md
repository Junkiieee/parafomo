1. **AdSense hesabı (para kazanmanın kapısı)** — https://adsense.google.com → parafomo.com ile hesap aç
   (kimlik/ödeme bilgileri senin). Bana yalnız **yayıncı kimliğini** (`ca-pub-XXXXXXXXXXXXXXXX`) ver; site
   doğrulama kodunu ve ads.txt'i ajan koyar, sonra sen "İncelemeye gönder"e basarsın. _(2026-10-06)_
2. **Kalıcı Claude token'ı (5 dk)** — sunucuda `claude setup-token` → token'ı
   `/root/.config/parafomo/claude.env` dosyasına `CLAUDE_CODE_OAUTH_TOKEN=<token>` olarak yaz (`chmod 600`).
   Eylül'deki 8 gecelik kesintinin kalıcı çözümü. _(2026-10-06)_
3. **X (Twitter) otomatik paylaşım** — developer.x.com → projenin faturalandırmasını (pay-per-use, ~$6-8/ay)
   aç. Anahtarlar zaten `.env`'de; açılınca ajan her gün veri kartı + yeni yazıyı X'e de basar. _(2026-10-06)_
4. **info@parafomo.com gerçekten sana ulaşıyor mu?** — sitede iletişim adresi bu. Kendine bir test maili at;
   gelmiyorsa Cloudflare → Email Routing'de info@ → Gmail yönlendirmesi ekle (AdSense ve güven için şart). _(2026-10-06)_
5. **Uzak yedek (opsiyonel, 10 dk)** — Cloudflare R2'de bir bucket + API token (S3 uyumlu, ücretsiz katman) →
   `/root/.config/parafomo/backup.env`: `R2_ACCOUNT_ID=`, `R2_ACCESS_KEY_ID=`, `R2_SECRET_ACCESS_KEY=`,
   `R2_BUCKET=`. Portföy kullanıcı verisinin sunucu dışı kopyası. _(2026-10-06)_
