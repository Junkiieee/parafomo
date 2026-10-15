# Kaan'dan beklenenler (haftalık koşu 2026-10-15)

1. **TCMB EVDS API anahtarı (ücretsiz, ~5 dk)**
   - Neden: mevduat ve kredi faizlerinin haftalık resmi ortalamasını otomatik çekmek için. Böylece
     /mevduat-faizi-hesaplama'ya "güncel mevduat faiz oranları" kutusu eklenir ("mevduat faiz oranları" ~57,
     "mevduat faizi hesaplama" ~58 hacim, şu an 57. sıradayız). Bu hafta açılacak konut ve ihtiyaç kredisi
     sayfalarında da varsayılan faiz elle girilmek yerine otomatik güncellenir. Anahtar olmadan bu rakamı ancak
     elle ve "örnek faiz" diye yazabiliyorum; o rakam da sessizce bayatlıyor.
   - Nasıl: https://evds3.tcmb.gov.tr → Üye ol / giriş → profil menüsü → "API Anahtarı" → kopyala →
     sunucuda `/root/.config/parafomo/evds.env` dosyasına tek satır: `EVDS_API_KEY=...` (repo'ya girmez).
_Görev Masası (2026-10-15, Kaan kararı): Claude Docs panosu emekli → **dashboard.parafomo.com** kanonik; kararlar
`agent/board.py` ile yerel dosyadan okunur (bağlayıcı gerekmez). Eski "pano okunamıyor" görevi bununla kapandı._

_Not (2026-10-11, Kaan): X (Twitter) otomatik paylaşım YAPILMAYACAK — şimdilik gündemde değil,
tekrar açılırsa Kaan söyler. Ajan bu konuda görev/öneri üretmesin._
_info@parafomo.com: ✅ ÇALIŞIYOR (2026-10-11 test edildi) — Cloudflare Email Routing aktif, mail Kaan'ın
kişisel adresine yönleniyor. Görev kapandı._

_2026-10-13 (Kaan): app.parafomo.com Google OAuth origin'i ZATEN ekli; site Bing Webmaster'da ZATEN var (GSC'den içe
aktarma — sitede doğrulama dosyası/etiketi olmaz, yokluğu kanıt değildir). İkisini tekrar görev yapma._
