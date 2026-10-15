# Kaan'dan beklenenler (haftalık koşu 2026-10-15)

1. **TCMB EVDS API anahtarı (ücretsiz, ~5 dk)**
   - Neden: mevduat ve kredi faizlerinin haftalık resmi ortalamasını otomatik çekmek için. Böylece
     /mevduat-faizi-hesaplama'ya "güncel mevduat faiz oranları" kutusu eklenir ("mevduat faiz oranları" ~57,
     "mevduat faizi hesaplama" ~58 hacim, şu an 57. sıradayız). Bu hafta açılacak konut ve ihtiyaç kredisi
     sayfalarında da varsayılan faiz elle girilmek yerine otomatik güncellenir. Anahtar olmadan bu rakamı ancak
     elle ve "örnek faiz" diye yazabiliyorum; o rakam da sessizce bayatlıyor.
   - Nasıl: https://evds3.tcmb.gov.tr → Üye ol / giriş → profil menüsü → "API Anahtarı" → kopyala →
     sunucuda `/root/.config/parafomo/evds.env` dosyasına tek satır: `EVDS_API_KEY=...` (repo'ya girmez).
2. **Görev Masası gece koşularında hâlâ okunamıyor (RC oturumunda 10 dk)**
   - Neden: 10-13'te `--strict-mcp-config` kaldırıldı, ama 10-14 ve 10-15 koşularında da ToolSearch Claude Docs
     araçlarını bulamadı. Panodaki onay/red kararlarını göremiyorum, panoya da yazamıyorum.
   - Olası neden: `agent/run.sh` `~/.config/parafomo/claude.env`'i (setup-token, CLAUDE_CODE_OAUTH_TOKEN) yüklüyor.
     Bu token muhtemelen claude.ai bağlayıcılarını taşımıyor; 10-13 testi büyük ihtimalle normal girişle yapıldı.
   - Nasıl: RC oturumunda `set -a; . ~/.config/parafomo/claude.env; set +a; claude -p "ToolSearch ile Claude Docs
     araçlarını ara ve sonucu yaz" --allowedTools ToolSearch` çalıştır. Araçlar yoksa: ya gece koşusu bağlayıcıyı
     taşıyan bir kimlikle çalışmalı ya da pano bırakılıp week.md + e-posta raporu kanonik sayılmalı. Karar senin.

_Not (2026-10-11, Kaan): X (Twitter) otomatik paylaşım YAPILMAYACAK — şimdilik gündemde değil,
tekrar açılırsa Kaan söyler. Ajan bu konuda görev/öneri üretmesin._
_info@parafomo.com: ✅ ÇALIŞIYOR (2026-10-11 test edildi) — Cloudflare Email Routing aktif, mail Kaan'ın
kişisel adresine yönleniyor. Görev kapandı._

_2026-10-13 (Kaan): app.parafomo.com Google OAuth origin'i ZATEN ekli; site Bing Webmaster'da ZATEN var (GSC'den içe
aktarma — sitede doğrulama dosyası/etiketi olmaz, yokluğu kanıt değildir). İkisini tekrar görev yapma._
