# Kaan'dan beklenenler (güncelleme 2026-10-28 RC — 3 kısa iş + 1 tarihli + 1 karar)

1. **ŞİMDİ (10 saniye) — gün içi fiyat tazeleme cron'unu kur**
   `scripts/prices-refresh.sh` + `deploy/crontab.txt` satırı hazır (altın/DXY/tahvil Pzt-Cmt 5 kez tazelenir; hafta sonu
   Cuma fiyatı kalmaz). Otomatik izin denetimi crontab yazmayı engelledi → Claude Code'a şunu yaz:
   `! crontab /root/parafomo/deploy/crontab.txt`

2. **ŞİMDİ (3 dakika) — Meta izni: Facebook paylaşımı + Instagram ölçümü tek seferde**
   Neden: YouTube izleyicimizin %68'i 35-54 yaş — Facebook'un ana kitlesi; sayfamız 0 takipçi ve hiç paylaşım yapmıyor
   (yine de facebook.com'dan ayda ~46 ziyaretçi geliyor). Reels + blog link paylaşımı kodu HAZIR; tek eksik
   `pages_manage_posts` izni. Aynı adımda Instagram erişim ölçümü (`instagram_manage_insights`) de açılır.
   Adımlar: (1) Claude Code'a `! python3 /root/parafomo/scripts/instagram-reauth.py scopes` yaz → izin listesini gösterir.
   (2) https://developers.facebook.com/tools/explorer/ → sağ üstte uygulamayı seç → listedeki izinleri işaretle →
   "Generate Access Token" → Facebook/Instagram onayı. (3) Çıkan kısa ömürlü token'ı kopyala →
   `! python3 /root/parafomo/scripts/instagram-reauth.py exchange "<TOKEN>"` → "güncellendi" yazınca bitti; ertesi
   videodan itibaren Facebook'ta da yayın başlar.

3. **ŞİMDİ (30 saniye) — Instagram Reel açıklamasının ilk satırını düzelt** (yaptıysan "Yaptım" de)
   YouTube başlığı 2026-10-28'de API'den düzeltildi (ju3eIYBRa7M → "Merkez Bankası faiz kararı cebine nasıl dokunuyor").
   Instagram API açıklama düzenlemeyi desteklemiyor (#3 Unknown method) → elle: https://www.instagram.com/reel/DeyWcNigded/
   → ⋯ → Düzenle → ilk satır "Merkez Bankası faizi sabit tuttu, cebine ne oldu" yerine
   "Merkez Bankası faiz kararı cebine nasıl dokunuyor" → Bitti. (TCMB faizi %37→%36 indirdi; "sabit tuttu" yanlış.)

4. **3 Kasım (Salı) öğleden sonra — Google'a "yeniden tara" de (5 dakika)**
   TÜİK Ekim verisi 10:00'da açıklanınca sitedeki 2027 yeniden değerleme sayfaları otomatik "Belli Oldu: %X" olur,
   ama Google bu sayfaları ~10 günde bir tarıyor. Search Console → üstteki "URL denetimi" kutusu → aşağıdaki her
   adresi yapıştır → "Dizine eklenmesini iste": parafomo.com/yeniden-degerleme-orani/ ·
   parafomo.com/blog/2027-zamlari-yeniden-degerleme-orani-rehberi/ · parafomo.com/mtv-hesaplama/ ·
   parafomo.com/emlak-vergisi-hesaplama/ · parafomo.com/kira-artis-orani-hesaplama/ ·
   parafomo.com/blog/ekim-2026-enflasyon-beklentisi-3-kasim/ (2 Kasım'da yayınlanacak önizleme). (Aynısı 5 Ocak'ta emekli/memur
   zammı sayfaları için de değerli olacak.) Neden: yılın en büyük arama dalgası o gün; Google eski "tahmin"i
   gösterirse tık kaçar.

5. **Karar (1 dakika) — iki büyüme önerisi: evet/hayır yeter** (yol haritası R14 + R15)
   (a) **Zam sezonu için 1 uzun YouTube videosu (5-8 dk)** — "Emekli zammı Ocak 2027: tam hesap" gibi. Neden: izlenmemizin
   %21'i YouTube aramasından geliyor ve uzun videonun açıklamasındaki site linki tıklanabilir (Shorts'ta değil). Sen
   "önce Shorts" demiştin; bu tek bir deneme. (b) **Gömülebilir hesaplayıcı / altın fiyatı widget'ı** — başka siteler
   eklerse kaynak linki = doğal backlink; Google'daki baş sorgulardaki (p60-99) otorite kilidinin kalıcı çözümü. 15 Ekim'de
   "dış link planı şimdilik yok" demiştin. Panelde ya da bana "a evet / b hayır" gibi yazman yeterli.

_EVDS anahtarı 2026-10-15'te doğrulandı (`~/.config/parafomo/evds.env`)._
_Görev Masası (2026-10-15, Kaan kararı): Claude Docs panosu emekli → **dashboard.parafomo.com** kanonik; kararlar
`agent/board.py` ile yerel dosyadan okunur (bağlayıcı gerekmez). Eski "pano okunamıyor" görevi bununla kapandı._

_Not (2026-10-11, Kaan): X (Twitter) otomatik paylaşım YAPILMAYACAK — şimdilik gündemde değil,
tekrar açılırsa Kaan söyler. Ajan bu konuda görev/öneri üretmesin._
_info@parafomo.com: ✅ ÇALIŞIYOR (2026-10-11 test edildi) — Cloudflare Email Routing aktif, mail Kaan'ın
kişisel adresine yönleniyor. Görev kapandı._

_2026-10-13 (Kaan): app.parafomo.com Google OAuth origin'i ZATEN ekli; site Bing Webmaster'da ZATEN var (GSC'den içe
aktarma — sitede doğrulama dosyası/etiketi olmaz, yokluğu kanıt değildir). İkisini tekrar görev yapma._
