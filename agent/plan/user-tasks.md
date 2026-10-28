# Kaan'dan beklenenler (güncelleme 2026-10-28 — 2 kısa iş + 1 tarihli; yeni hesap/API ihtiyacı yok)

1. **ŞİMDİ (30 saniye) — Instagram Reel açıklamasının ilk satırını düzelt**
   YouTube başlığı 2026-10-28'de API'den düzeltildi (ju3eIYBRa7M → "Merkez Bankası faiz kararı cebine nasıl dokunuyor").
   Instagram API açıklama düzenlemeyi desteklemiyor (#3 Unknown method) → elle: https://www.instagram.com/reel/DeyWcNigded/
   → ⋯ → Düzenle → ilk satır "Merkez Bankası faizi sabit tuttu, cebine ne oldu" yerine
   "Merkez Bankası faiz kararı cebine nasıl dokunuyor" → Bitti. (TCMB faizi %37→%36 indirdi; "sabit tuttu" yanlış.)

1b. **ŞİMDİ (10 saniye) — gün içi fiyat tazeleme cron'unu kur**
   `scripts/prices-refresh.sh` + `deploy/crontab.txt` satırı hazır (altın/DXY/tahvil Pzt-Cmt 5 kez tazelenir; hafta sonu
   Cuma fiyatı kalmaz). Otomatik izin denetimi crontab yazmayı engelledi → Claude Code'a şunu yaz:
   `! crontab /root/parafomo/deploy/crontab.txt`

2. **3 Kasım (Salı) öğleden sonra — Google'a "yeniden tara" de (5 dakika)**
   TÜİK Ekim verisi 10:00'da açıklanınca sitedeki 2027 yeniden değerleme sayfaları otomatik "Belli Oldu: %X" olur,
   ama Google bu sayfaları ~10 günde bir tarıyor. Search Console → üstteki "URL denetimi" kutusu → aşağıdaki her
   adresi yapıştır → "Dizine eklenmesini iste": parafomo.com/yeniden-degerleme-orani/ ·
   parafomo.com/blog/2027-zamlari-yeniden-degerleme-orani-rehberi/ · parafomo.com/mtv-hesaplama/ ·
   parafomo.com/emlak-vergisi-hesaplama/ · parafomo.com/kira-artis-orani-hesaplama/ ·
   parafomo.com/blog/ekim-2026-enflasyon-beklentisi-3-kasim/ (2 Kasım'da yayınlanacak önizleme). (Aynısı 5 Ocak'ta emekli/memur
   zammı sayfaları için de değerli olacak.) Neden: yılın en büyük arama dalgası o gün; Google eski "tahmin"i
   gösterirse tık kaçar.

_EVDS anahtarı 2026-10-15'te doğrulandı (`~/.config/parafomo/evds.env`)._
_Görev Masası (2026-10-15, Kaan kararı): Claude Docs panosu emekli → **dashboard.parafomo.com** kanonik; kararlar
`agent/board.py` ile yerel dosyadan okunur (bağlayıcı gerekmez). Eski "pano okunamıyor" görevi bununla kapandı._

_Not (2026-10-11, Kaan): X (Twitter) otomatik paylaşım YAPILMAYACAK — şimdilik gündemde değil,
tekrar açılırsa Kaan söyler. Ajan bu konuda görev/öneri üretmesin._
_info@parafomo.com: ✅ ÇALIŞIYOR (2026-10-11 test edildi) — Cloudflare Email Routing aktif, mail Kaan'ın
kişisel adresine yönleniyor. Görev kapandı._

_2026-10-13 (Kaan): app.parafomo.com Google OAuth origin'i ZATEN ekli; site Bing Webmaster'da ZATEN var (GSC'den içe
aktarma — sitede doğrulama dosyası/etiketi olmaz, yokluğu kanıt değildir). İkisini tekrar görev yapma._
