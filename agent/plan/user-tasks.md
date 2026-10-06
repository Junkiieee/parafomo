1. **Kalıcı Claude token'ı (5 dk, en önemlisi)** — Eylül'de OAuth oturumu 8 gece düştü, tüm LLM işleri
   sessizce durdu. Sunucuda bir kez: `claude setup-token` → tarayıcıda onayla → verilen token'ı
   `/root/.config/parafomo/claude.env` dosyasına tek satır `CLAUDE_CODE_OAUTH_TOKEN=<token>` olarak yaz
   (`chmod 600`). Tüm cron'lar bunu otomatik kullanır. _(eklendi 2026-10-06)_
2. **(opsiyonel) Instagram insights izni** — `instagram_manage_insights` olmadan Reels erişimi
   ölçülemiyor, IG'ye bu yüzden yatırım yapılmıyor. Meta uygulamasında izni ekleyip sayfa token'ını
   yenilersen ajan IG'yi de veriyle yönetir. _(eklendi 2026-10-06)_
