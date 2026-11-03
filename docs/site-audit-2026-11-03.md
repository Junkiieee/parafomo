# Site denetimi — 2026-11-03

Tek seferlik geniş denetim. Kapsam: mobil/tablet düzen, hız, SEO meta, teknik SEO ve erişilebilirlik.
Araçlar: Playwright ile 310 sayfanın 375 / 768 / 1024 px taraması, Lighthouse 12 (mobil, 16 şablon),
axe-core 4.10 (310 sayfa) ve `scripts/seo-audit.py`.

## Sonuç

| Ölçüt | Önce | Sonra |
|---|---|---|
| Mobilde yana taşan sayfa | 64 | 0 |
| Lighthouse performans (8 şablon) | 89–95 | 96–100 |
| İlk ziyaret aktarımı (anasayfa) | 301 KB | 161 KB |
| seo-audit UYARI | 83 | 23 (kalanlar bilerek, aşağıda) |
| Sitemap'te lastmod'suz URL | 114 | 31 (veri beslemesi olmayan sabit sayfalar) |
| axe ihlali olan sayfa (mobil) | 241 / 310 | bkz. PR açıklaması |

## Bilerek dokunulmayanlar

- **Açık bahislerin sayfaları** (B261015-1, B261022-1, B261029-1) ve otomatik üretilen
  `2027-zamlari-yeniden-degerleme-orani-rehberi`: title/description değişmedi, ölçüm bozulmasın.
  Kalan 23 seo-audit uyarısının 22'si bunlar.
  - Not: `abd-ekim-2026-nfp-istihdam-verisi-fed-dolar-altin` başlığı hâlâ "Fed 28 Ekim'de Ne Yapar?" diye
    soruyor, oysa karar açıklandı. `pce-gdp-eylul-2026-…` başlığı da "— Fed 28 Ekim" diye yarım bitiyor.
    Bahis değerlendirmesinden sonra düzeltilmeli.
- **`ilk-issizlik-basvurulari-nedir-initial-jobless-claims`** başlığı 76 karakter. Kısaltınca "Initial Jobless
  Claims" anahtar kelimesi düşüyor.
- **news-sitemap kapsamı.** Son 48 saatte *güncellenen* olay yazıları da girmeye devam ediyor. Google News
  kuralı yalnız yeni yayımlananları istiyor, ama bu davranış B261022-1 motorunun parçası. Yalnız tarih
  hesabı düzeltildi (gelecek tarih yazılmıyor).

## Sonraya kalanlar (öneri)

1. **OG kartı:** 45 sayfa (75 halka arz şirket sayfası hariç) genel `og-default.png`'yi kullanıyor. Bunlar
   anasayfa, `/blog/`, kategoriler, `/altin-fiyatlari/` ve 11 alt sayfası, faiz/kdv/net-maaş, TCMB/Fed
   takvimi ve ekonomik takvim. WhatsApp paylaşım önizlemesi için `scripts/og-images.py` CARDS'a eklenmeli;
   rakamlar kaynağından doğrulanarak.
2. **AVIF kapaklar:** WebP'ye göre ~%27 küçük. Ama sharp ile kapak başına ~4 sn kodlama sürüyor, ilk build
   ~5 dk uzar. Build kapısının süre sınırına bakılmadan eklenmemeli.
3. **`/altin-fiyatlari/14-ayar-altin/` ve `/18-ayar-altin/`:** rakamlar maskelenince gövdenin %84'ü aynı.
   Ayara özgü metin eklenmeli.
4. **Dataset şeması (26 sayfa):** `spatialCoverage`/`temporalCoverage` eklenebilir. 9 sayfada `license`
   yok; lisans kararı Kaan'ın.
5. **Hesaplayıcı giriş kenarlığı:** #e0e8e4, beyazla 1,25:1 (WCAG 1.4.11 için 3:1 gerekir). 48 sayfada
   sayfa içi kural var; ortak bir `--input-border` değişkenine taşınmalı.
6. **Anasayfa ≤900px odak sırası:** `.hero-visual { order: -1 }` görsel sırayı değiştiriyor; Tab sırası
   DOM'u izliyor.
