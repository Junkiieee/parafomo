# Site denetimi — 2026-11-03

Tek seferlik geniş denetim. Kapsam: site (mobil/tablet düzen, hız, SEO meta, teknik SEO, erişilebilirlik),
backend, panel/deploy/cron, portföy uygulaması (`app/`), script ve ajan hatları, 2027 yıl geçişi.
Araçlar: Playwright ile 310 sayfanın 375 / 768 / 1024 px taraması, Lighthouse 12 (mobil, 16 şablon),
axe-core 4.10 (310 sayfa), `scripts/seo-audit.py`, backend için pytest (102 test) ve sahte tarihli
build'ler (`FAKE_NOW=2027-… node --require fakedate.cjs`; yalnız denetim sırasında kullanıldı, repoda yok).

## Sonuç

| Ölçüt | Önce | Sonra |
|---|---|---|
| Mobilde yana taşan sayfa | 64 | 0 |
| Lighthouse performans (8 şablon) | 89–95 | 96–100 |
| İlk ziyaret aktarımı (anasayfa) | 301 KB | 161 KB |
| seo-audit UYARI | 83 | 22 (kalanlar bilerek, aşağıda) |
| Sitemap'te lastmod'suz URL | 114 | 26 (veri beslemesi olmayan sabit sayfalar) |
| axe ihlali olan sayfa (mobil, gradyanlar düzleştirilmiş kontrastla) | 241 / 310 (829 düğüm) | 0 / 312 |
| Kendi OG kartı olmayan araç/veri sayfası | 45 | 15 |

## Aynı gün yapılan ek işler

- **OG kartları:** 30 araç/veri sayfası kendi kartını alıyor (`scripts/og-images.py`, rakamlar veriden).
- **AVIF kapaklar:** build başına 30 sn bütçeyle, en yeni kapaktan başlayarak üretiliyor (WebP'den ~%25 küçük).
- **14/18/22 ayar altın sayfaları:** ayara özgü bölüm eklendi.
- **Giriş kenarlığı:** ortak `--input-border` (#739586, beyazla 3,3:1), 52 dosya.
- **Anasayfa ≤900 px odak sırası** görsel sırayla aynı.
- **llms.txt** build'de `tools.ts`'ten üretiliyor (77 link). **404** sayfası adresteki kelimelere en yakın
  yazı/aracı öneriyor.
- **Türkçe ekler:** `src/data/ek.ts` sayının okunuşuna göre ek veriyor ("Ayın 17'si", "%23'ü", "49,98'e",
  "2027'de"). Yıl ekleri (`yilDa`/`yilYa`) de bunu kullanıyor.
- **Backend** (102 test): e-posta bombalama ve kaba kuvvete hız sınırı, NaN/sonsuz değerle bozulan portföy,
  yer tutucu JWT anahtarı, Google girişinde `iss` kontrolü, şifre sıfırlama ve hesap silme sertleştirmesi.
- **Panel / deploy / ops:** panelde kayıtlı XSS ve donma, CSP; cron işleri `flock` ile tekil; systemd ve Caddy
  sertleştirme şablonları; gelen posta işleyicisinde zaman aşımı ve yedek adres; şifreli ve izlenen yedek.
- **Portföy uygulaması:** Türkçe sayı girişi ("1.234,5") yanlış tutar kaydediyordu; fiyatsız pozisyonda sahte
  −%100; service worker eski sürümü gösteriyordu (pf-v4).
- **Script'ler:** 11 hata (tekrar alarm maili, Fed 2027 toplantıları, halka arz tarihleri, atomik yazım…);
  altın fiyatında Yahoo yedeğinde ons yanlış kurla ölçekleniyordu.

## 2027 yıl geçişi

Sahte tarihli build'lerle denendi (Ocak, Mart 2027). Düzeltilenler:

- Zam sayfaları (asgari ücret, memur, emekli, kıdem tavanı, en düşük emekli maaşı, evde bakım/bedelli/engelli
  OG kartları): Ocak katsayısı girilince **çift zam** göstermiyor; boş dönemde build çökmüyor; Aralık verisi
  gelince "kesinleşti" diliyle konuşuyor.
- TÜİK, TCMB ve Fed takvimleri **bütün yıl dosyalarını** okuyor (sayfalar, sitemap, `policy-decisions.py`,
  ajan özeti `agent/brief.py`). TCMB 2027 kararları `tcmb-2027.json` eklenince otomatik doluyor.
- Halka arz getirileri yeni yıla **en az 5 arz** işlem görünce geçiyor; şirket sayfaları getirisini koruyor.
- Faiz, bono, kredi, ihtiyaç kredisi, enflasyon hesaplama ve ekonomik takvim başlıkları 1 Ocak'ta
  kendiliğinden yeni yıla geçiyor (`BU_YIL`).
- `health.py` 1 Ocak'ta yanlış "tcmb-2028.json ekle" uyarısı vermiyor.

**Elle güncellenmesi gerekenler (Ocak 2027, veri gelince):** yıllık tutar kullanan sayfaların başlık ve
tabloları bilerek otomatik ilerlemiyor; veri güncellenince yıl da güncellenmeli. Net maaş, gelir vergisi ve
vergi dilimi (2027 tarifesi), `bagkur-prim-2026.json`, `gss-prim-2026.json`, `sosyal-aylik-2026.json`,
`dogum-yardimi-2026.json`, `tapu-harci-2026.json`, `veraset-2026.json`, yıllık izin ve ihbar tablolarındaki
"33.030 ₺ = 2026 brüt asgari ücret", mevduat stopaj oranları, KDV oranları SSS'si. TCMB 2027 toplantıları
için `data/tcmb-2027.json` (biçim 2026 dosyasıyla aynı; `previous` = 2026'nın son faizi).

## Sunucuda elle yapılacaklar

Repo'daki `deploy/` dosyaları şablondur; sunucuya kendiliğinden geçmez (adımlar `deploy/DEPLOY.md`'de).

1. `backend/.env` → `PORTFOLIO_JWT_SECRET` en az 32 karakter rastgele olmalı. Yer tutucuysa servis her
   başlangıçta rastgele anahtar üretir (herkes çıkış yapar) ve `journalctl -u parafomo-api` CRITICAL yazar.
2. Crontab'ı şablondan yeniden kur (`flock` satırları): önce `crontab -l | diff - deploy/crontab.txt`.
3. systemd birimlerini kopyala, `daemon-reload` + yeniden başlat; Caddy api/dashboard bloklarını yenile,
   `app.parafomo.com` bloğuna `deploy/Caddy-app.conf`'taki `Cache-Control: no-cache` satırlarını ekle.
4. Şifreli yedek için `BACKUP_PASSPHRASE` tanımla. `.env` dosyalarına `chmod 600`.
5. `timedatectl` → `Etc/UTC` (cron saatleri UTC).
6. Cloudflare Worker değişkenleri (isteğe bağlı): `INBOX_FALLBACK` (API çökerse postanın yönleneceği adres),
   `INBOX_ALLOWED_FROM`.

## Karar bekleyenler (Kaan)

- **Halka arz getirisi doğruluğu:** getiri, bedelsiz sermaye artırımını hesaba katmıyor; bölünme yapan
  şirketlerde getiri olduğundan düşük çıkıyor (bugünkü ortalama −%30,1 büyük olasılıkla fazla kötümser).
  Yahoo'nun bölünme verisiyle (`events=split`) sunucuda doğrulanmalı.
- **Google ile ilk giriş şifreyi siliyor:** e-postayla açılmış bir hesaba ilk kez Google ile girilince şifre
  temizleniyor (ele geçirme önlemi). Ürün kararı: böyle mi kalsın, yoksa bağlamadan önce onay mı istensin?
- **Alarm e-postaları** doğrulanmamış adreslere de gidebiliyor; e-posta doğrulaması eklenmeli mi?

## Bilerek dokunulmayanlar

- **Açık bahislerin sayfaları** (B261015-1, B261022-1, B261029-1) ve otomatik üretilen
  `2027-zamlari-yeniden-degerleme-orani-rehberi`: title/description değişmedi, ölçüm bozulmasın.
  Kalan 22 seo-audit uyarısının 21'i bunlar. (Yıl geçişi ve ek düzeltmeleri bu sayfaların bugünkü
  çıktısını değiştirmiyor; yalnız yanlış ekler düzeldi.)
  - Not: `abd-ekim-2026-nfp-istihdam-verisi-fed-dolar-altin` başlığı hâlâ "Fed 28 Ekim'de Ne Yapar?" diye
    soruyor, oysa karar açıklandı. `pce-gdp-eylul-2026-…` başlığı da "— Fed 28 Ekim" diye yarım bitiyor.
    Bahis değerlendirmesinden sonra düzeltilmeli.
- **`ilk-issizlik-basvurulari-nedir-initial-jobless-claims`** başlığı 76 karakter. Kısaltınca "Initial Jobless
  Claims" anahtar kelimesi düşüyor.
- **news-sitemap kapsamı.** Son 48 saatte *güncellenen* olay yazıları da girmeye devam ediyor. Google News
  kuralı yalnız yeni yayımlananları istiyor, ama bu davranış B261022-1 motorunun parçası. Yalnız tarih
  hesabı düzeltildi (gelecek tarih yazılmıyor).

## Sonraya kalanlar (öneri)

1. **OG kartı:** kalan 15 sayfa (anasayfa, `/blog/`, kategoriler gibi) genel kartı kullanıyor.
2. **Dataset şeması (26 sayfa):** `spatialCoverage`/`temporalCoverage` eklenebilir. 9 sayfada `license`
   yok; lisans kararı Kaan'ın.
3. **Veri dosyalarına güncellenme günü:** `emekli-memur.json`, `kyk-burs.json`, `emekli-promosyon.json`,
   `kredi-karti-faiz.json` gibi dosyalarda `updated` alanı yok; bu yüzden beslediği sayfalar (bayram
   ikramiyesi, KYK, emekli promosyonu…) sitemap'te lastmod alamıyor.
