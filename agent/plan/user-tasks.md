# Kaan'dan beklenenler (güncelleme 2026-10-28 RC — 3 kısa iş + 1 tarihli + 1 karar; 10-30 madde 6 kapandı)

5. **Sunucu zamanlayıcısını kur (1 dakika) — Cloudflare izni ✅ 2026-11-10 eklendi (parafomo-claude token, 30 günlük geçmiş çekildi)** Kalan tek adım: Claude oturumunda `! crontab /root/parafomo/deploy/crontab.txt`
   dash.cloudflare.com → sağ üst profil → **My Profile → API Tokens** → parafomo'nun kullandığı token'ın yanındaki
   **Edit** → Permissions'a iki satır olduğundan emin ol: **Zone · Zone · Read** ve **Zone · Analytics · Read** (Zone Resources: parafomo.com) → Continue → Update Token.
   Token değişmez, sadece izni genişler. Sonra Claude oturumunda şu tek satırı çalıştır (günlük bot arşivi zamanlaması;
   sınıflandırıcı crontab yazmama izin vermiyor): `! crontab /root/parafomo/deploy/crontab.txt` — ve bana "ekledim" yaz. Sonra: hangi bot (Google, ChatGPT, Claude, Perplexity) hangi
   sayfaları ne sıklıkla okuyor haftalık rapor (Cloudflare'in IP ile doğruladığı bot etiketleri — verifiedBotCategory; yöntem DuvInc/cloudflare-ai-crawl-history (MIT) ile aynı, ama Python cron + yerel arşiv; CF 30 gün tutar, biz kalıcı saklarız) + ChatGPT/Perplexity'nin kullanıcı sorusu üzerine açtığı sayfalar → konu seçimi.

_2026-11-10: Madde 4 (GSC yeniden tara: yeniden-degerleme-orani, 2027 rehberi, kira-artis) Kaan "yaptım" → KAPANDI. CEO raporu 11-11/11-12'de URL denetimiyle son taramanın 10 Kasım sonrasına geçtiğini doğrulasın; geçmediyse tekrar sor._

_2026-11-09: R15 EVET (Kaan) → /sitene-ekle/ + /embed/altin + /embed/kira-artis yayında (2659a7a). Cinecode denemesi: Kaan "şimdilik yapma"._

_2026-10-30 RC: R14 EVET → uzun video hattı kuruldu (scripts/longform/); ilk video yayında https://youtu.be/L-q8AL-NmxQ; 3 Kasım "belli oldu" videosu otomatik üretilip yayınlanacak (Kaan onayı)._
_2026-10-30 RC: IG Reel DeyWcNigded açıklaması düzeltildi (API ile doğrulandı)._
_2026-10-30 RC: crontab kuruldu (prices-refresh canlı, dry-run OK) · Meta yeniden yetki tamam: süresiz Page token'da pages_manage_posts + pages_manage_engagement + read_insights + instagram_manage_insights; ilk FB link paylaşımı 1226177233908930_122124848547372466; IG reach/saved/shares okunuyor. (Use case'e "Manage everything on your Page" eklendi; Explorer pages_read_user_content hatası verdi → doğrudan OAuth dialog linkiyle alındı.)_
_2026-10-30 RC: "TMSF 400 bin Reel'ini sil" görevi kapandı — Reel Instagram'a hiç yayınlanmamış (26 Eylül IG işleme hatası, logs/viral.log); silinecek bir şey yok._

_EVDS anahtarı 2026-10-15'te doğrulandı (`~/.config/parafomo/evds.env`)._
_Görev Masası (2026-10-15, Kaan kararı): Claude Docs panosu emekli → **dashboard.parafomo.com** kanonik; kararlar
`agent/board.py` ile yerel dosyadan okunur (bağlayıcı gerekmez). Eski "pano okunamıyor" görevi bununla kapandı._

_Not (2026-10-11, Kaan): X (Twitter) otomatik paylaşım YAPILMAYACAK — şimdilik gündemde değil,
tekrar açılırsa Kaan söyler. Ajan bu konuda görev/öneri üretmesin._
_info@parafomo.com: ✅ ÇALIŞIYOR (2026-10-11 test edildi) — Cloudflare Email Routing aktif, mail Kaan'ın
kişisel adresine yönleniyor. Görev kapandı._

_2026-10-13 (Kaan): app.parafomo.com Google OAuth origin'i ZATEN ekli; site Bing Webmaster'da ZATEN var (GSC'den içe
aktarma — sitede doğrulama dosyası/etiketi olmaz, yokluğu kanıt değildir). İkisini tekrar görev yapma._
