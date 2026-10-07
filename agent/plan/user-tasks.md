1. **Videolar için müzik (10 dk)** — YouTube Studio → Ses Kütüphanesi → filtre "Atıf gerekmez" → enerjik/
   kurumsal/elektronik 8-10 parça indir → sunucuda `/root/parafomo-media/music/` klasörüne koy (ya da bana
   ulaştır). Klasörde dosya olduğu an tüm videolar otomatik gerçek müzik kullanır; şu an geçici "pad" var. _(2026-10-06)_
2. **Kalıcı Claude token'ı (5 dk)** — sunucuda `claude setup-token` → token'ı
   `/root/.config/parafomo/claude.env` dosyasına `CLAUDE_CODE_OAUTH_TOKEN=<token>` olarak yaz (`chmod 600`).
   OAuth kesintisinin kalıcı çözümü + yeni token Max 5x bilgisini de taşır. _(2026-10-06)_
3. **X (Twitter) otomatik paylaşım** — developer.x.com → projenin faturalandırmasını (pay-per-use, ~$6-8/ay)
   aç. Anahtarlar zaten `.env`'de; açılınca ajan her gün veri kartı + yeni yazıyı X'e de basar (trafik dağıtımı). _(2026-10-06)_
4. **info@parafomo.com gerçekten sana ulaşıyor mu?** — sitede iletişim adresi bu. Kendine bir test maili at;
   gelmiyorsa Cloudflare → Email Routing'de info@ → Gmail yönlendirmesi ekle. _(2026-10-06)_
5. **Uzak yedek (opsiyonel, 10 dk)** — Cloudflare R2 bucket + API token → `/root/.config/parafomo/backup.env`:
   `R2_ACCOUNT_ID=`, `R2_ACCESS_KEY_ID=`, `R2_SECRET_ACCESS_KEY=`, `R2_BUCKET=`. _(2026-10-06)_
