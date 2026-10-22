# Hafta planı — 2026-10-22 → 2026-10-28
_Haftalık koşu: 2026-10-22 · model claude-opus-5-5_
<!-- plan-date: 2026-10-22 -->

## Durum
- Gerçek erişim (Direct hariç) son 7g **59** (28g 196) · son tam hafta 202642: **64** — 9 haftanın en iyisi (202641: 32,
  4 hafta önce 202638: 48). GSC 202642: 43 tık / 2.130 gös (202641: 17 / 973) — gösterim 2x. Kaynak: olay yazıları
  (TCMB 22 Ekim, ABD CPI/NFP) + halka arz sayfaları (7g 8 tık / 197 gös, 2x) + 2027 zamları yazısı (116 gös/7g).
  Hâlâ hedefin ~%0,9'u.
- Geçen hafta 20+ yeni araç sayfası açıldı, hepsi 1-6 günde indekslendi; baş sorgularda p60-99 (otorite kilidi
  yeni sayfalarda da aynı), 2027 varyantlarında p6-11. Sezon (Kasım-Ocak) başlamadan tık beklenmez; ilk test 3 Kasım.
- **Ders:** olay önizleme yazıları 28g 31 tık — blog tıklarının yarısı. Yeni bahis B261022-1. Getiri bahsi **lost**.
- **§9c'nin ilk 15 satırı tükendi:** 12'si OTORITE, kalan 3'ü eşleme hatası (22 ayar bilezik/çeyrek altın sayfası var,
  borsa istanbul/bist 100 gürültü). Bu yüzden görevler bu koşuda Trends ile YENİ ölçülen sorgulardan:
  emekli promosyon **178,6**, fed faiz kararı 80,9, enflasyon beklentisi 45,6, geçici vergi 46,1, ek gösterge 43,7,
  sgk hizmet dökümü 30,1, emeklilik yaşı 25,5, emeklilik hesaplama 23,7. T19 motoru düzeltir.
- YouTube 53 abone (+0/7g), +1.886 izlenme/7g, W42 video medyanı 72. Bülten 1, Telegram 2, AdSense kapalı (Kaan kararı).

## Bahisler
- **B261022-1 — Olay takvimi motoru** · olay önizleme/sonuç yazıları 28g ≥60 tık + ≥900 gös (baz 31 / 506) · değerlendirme 2026-11-19
- **B261015-1 — Fırsat motoru: 2027 zam sezonu + hacimli araçlar** · 7g ≥400 gös + ≥10 tık (şimdi 226 / 1) · değerlendirme 2026-11-12
- **B261006-1 — Halka arz şirket sayfaları** · /halka-arz/* 7g ≥500 gös + ≥15 tık (şimdi 197 / 8) · değerlendirme 2026-11-03
- Kapandı: B261006-2 (getiri kümesi) → **lost** (28g 33 tık, baz 42, hedef 85).

## Görev kuyruğu (günlük koşu en üstteki [ ]'yi alır)
Kural: TARİHLİ görevin günü geldiyse önce o. Veri sayfasında rakamı resmi kaynaktan doğrula; iki kaynak çelişirse YAZMA.
Yeni sayfa = `src/data/tools.ts` kaydı (k: anahtar kelimeler) + Footer TOOL_LINKS + `scripts/og-images.py` CARDS +
`image="/og/<slug>.png"` + FAQPage + ilgili 2 sayfadan metin içi link → `npm run build` → `bash scripts/deploy-push.sh`
→ `python3 scripts/wait-live.py https://parafomo.com/<slug>/` → keyword-map'e `[x]`.

- [ ] T4b (B261022-1 — TARİHLİ, 23 Ekim sabahı) — **TCMB kararı sonrası kontrol** · /blog/tcmb-ekim-2026-faiz-karari-ppk-beklentiler/
  üstünde otomatik sonuç kutusu "açıklandı" + sonucBaslik görünüyor mu, /tcmb-faiz-takvimi kararı gösteriyor mu (yoksa
  `logs/policy-decisions.log`); SSS'yi geçmiş zamana çevir ("Ekim 2026'da TCMB faiz indirecek mi?" → gerçekleşen karar),
  "Son durum" bölümünü "Karar öncesi beklenti" olarak yeniden adlandır, `updatedDate`. ELLE kutu ekleme. Sıradaki PPK
  tarihini data/tcmb-2026.json'dan yazıya ekle. · Kabul: canlıda kutu + geçmiş zaman SSS.
- [ ] T17 (B261015-1) — **/emekli-promosyonu yeni veri sayfası** · hedef: emekli promosyon (hacim 178,6, son 4h 156 —
  sitede karşılığı yok, §9c'deki en büyük boş niyet). İçerik: (a) banka banka tablo — banka · promosyon tutarı (maaş
  aralığına göre kademeler) · ek kampanya şartı (otomatik ödeme/kart harcaması) · taahhüt süresi · kaynak linki · kontrol
  tarihi. YALNIZ bankanın KENDİ resmi kampanya sayfasında yazan rakam (WebFetch/WebSearch ≤12; haber sitesi rakamı
  YAZILMAZ). Kamu (Ziraat, Halkbank, VakıfBank) + büyük özel (İş, Garanti BBVA, Akbank, Yapı Kredi, QNB, DenizBank, ING,
  TEB, Enpara) — en az 6 banka doğrulanmazsa doğrulananlarla yayınla, eksiği yazma. Rakamı `data/emekli-promosyon.json`'a
  (banka, kademeler, şartlar, url, kontrol) yaz; sayfa oradan okur. (b) "Maaşına göre promosyon" mini hesaplayıcı:
  maaş gir → bankaların o kademedeki tutarı sıralı. (c) Promosyon nasıl alınır / banka değiştirme (taşıma) adımları,
  iade şartı (taahhüt bozulursa kısmi iade) — bankanın sözleşme metninden; genel kuralı doğrulayamazsan "bankaya göre
  değişir" de. (d) Ocak 2027 notu: zam sonrası bankalar kademeleri günceller → sayfa tarihli. health.py'a tazelik satırı
  (kontrol > 30 gün → UYARI). Başlık: "Emekli Promosyonu 2026: Banka Banka Güncel Tutarlar (<ay>)". /en-dusuk-emekli-maasi
  ve /emekli-zammi-hesaplama'dan metin içi link. Tavsiye dili yok ("en iyi banka" deme; "en yüksek tutar" tablo sırası).
  · Kabul: canlıda 200; her satırda kaynak linki + kontrol tarihi; hesaplayıcı çalışır; FAQPage; health.py satırı.
- [ ] T18 (B261015-1) — **/emeklilik-hesaplama yeni araç (ne zaman emekli olurum)** · hedef: emeklilik yaşı (25,5) +
  emeklilik hesaplama (23,7) + ne zaman emekli olurum (14,3) + sgk hizmet dökümü (30,1 — nasıl alınır bölümü).
  Girdi: doğum tarihi, cinsiyet, ilk sigorta girişi, statü (4/a SSK, 4/b Bağ-Kur, 4/c memur), prim günü. Çıktı: yaş +
  prim günü + sigortalılık süresi şartı ve tahmini emeklilik tarihi. Kurallar: 08.09.1999 öncesi (EYT — 7438 s.K. ile yaş
  şartı kalktı; kademeli prim günü tablosu 506 geçici 81), 08.09.1999–30.04.2008 (5510 geçici md. kadın 58/erkek 60,
  7000 gün; 25 yıl + 4500 gün seçeneği), 01.05.2008 sonrası (prim günü 7200'e kademeli, yaş 2036'dan itibaren 65'e
  kademeli — 5510 md.28 tablosu). TÜM tabloları mevzuat.gov.tr 5510 güncel metninden (pypdf) al; doğrulayamadığın
  statüyü (ör. 4/b farkları) hesaplayıcıdan çıkar, "e-Devlet'ten kontrol edin" de. 3 örnek profili SGK/resmî broşür
  örneğiyle karşılaştır, sonucu rapora yaz. Bölüm: "SGK hizmet dökümü nasıl alınır" (e-Devlet adımları, belge okuma).
  · Kabul: build geçer; canlıda 3 örnek profil doğru tarih verir; FAQPage; /en-dusuk-emekli-maasi + /bagkur-primi-hesaplama link.
- [ ] T19 (sistem — konu seçimi doğruluğu) — **opportunity_finder: alt sayfalar + yeni ölçülen sorgular** ·
  `scripts/learn/opportunity_finder.py` sayfa listesi yalnız `src/pages/*.astro` + blog; dinamik route alt sayfalarını
  (`/altin-fiyatlari/<tür>`, `/halka-arz/<slug>` HARİÇ tut — şirket adları gürültü) `dist/**/index.html` ya da sitemap'ten
  ekle. Sonuç: "22 ayar bilezik" → /altin-fiyatlari/22-ayar-bilezik, "çeyrek altın" → /altin-fiyatlari/ceyrek-altin,
  "cumhuriyet altını" zaten doğru. Eşanlam haritası (küçük dict): "memur maaşı" → /memur-zammi-hesaplama, "trafik cezası
  sorgulama" → /trafik-cezalari-hesaplama, "çocuk parası" → /dogum-yardimi, "sgk prim borcu" → /vergi-borcu-sorgulama.
  HEAD_TERMS'e bu koşuda ölçülenleri ekle: emekli promosyon, fed faiz kararı, enflasyon beklentisi, geçici vergi, ek
  gösterge, sgk hizmet dökümü, emeklilik yaşı, emeklilik hesaplama, katılım hesabı, kredi kartı faiz hesaplama, çocuk
  parası. Önbellekten oku (yeniden çekme). · Kabul: yeniden çalıştırınca 22 ayar bilezik / çeyrek altın YENI_YAZI değil;
  emekli promosyon listede (T17 canlıysa BEKLE); commit.
- [ ] T21 (B261022-1 — TARİHLİ, 29 Ekim sabahı) — **Fed 28 Ekim sonrası kontrol** · 26 Ekim'de daily-content'in yazdığı
  Fed önizleme yazısında (`fed-faiz-karari-28-ekim-2026-…`) `sonuc: "fed:2026-10-28"` var mı (yoksa 27 Ekim'de ekle);
  29 Ekim: kutu "açıklandı" + /fed-faiz-takvimi kararı gösteriyor mu (yoksa `logs/policy-decisions.log`); SSS geçmiş
  zamana, `updatedDate`. Rakamı elle tahmin ETME. · Kabul: canlıda kutu + /fed-faiz-takvimi güncel.
- [ ] T13 (zam sezonu — TARİHLİ, 3 Kasım sonrası · Kaan ONAYLADI) — **YD kesinleşme kontrolü:** 3 Kasım'da release-watch.py
  (10 dk'da bir, 07:00-10:50 UTC) Ekim Yİ-ÜFE gelir gelmez /yeniden-degerleme-orani, /mtv-hesaplama vb. ve CANLI
  yazı /blog/2027-zamlari-yeniden-degerleme-orani-rehberi'yi otomatik "Belli Oldu: %X" yapar (RC 10-18; oran EVDS
  endeksinden TÜİK yöntemiyle — 3 Kasım sabahı TÜİK bülteninin "12 aylık ortalamalara göre" Yİ-ÜFE rakamıyla
  karşılaştır; fark varsa data/yeniden-degerleme.json onikiAyOrt'u bültendeki değere düzelt + `python3 scripts/live-posts.py`
  + deploy). 4 Kasım sabahı günlük koşunun İLK işi: tüm YD'ye bağlı sayfalar (emlak, damga, tapu, veraset, muayene,
  pasaport, trafik, gelir vergisi istisnası, değer artış) "tahmin" yerine kesin oranı gösteriyor mu — `grep -l` ile tara.
  Kasım sonu: VUK tebliğini WebSearch ile doğrula → `tebligOrani` alanına yaz (gecmis'e ELLE satır EKLEME; tur Haziran
  2027'de kapanınca otomatik arşivlenir). Aralık: MTV/harç/damga için CB kararı çıkarsa → `uygulananOrani` (MTV,
  pasaport-harç sayfaları ve canlı yazı bu oranı kullanır). Her yazımdan sonra `python3 scripts/live-posts.py` → commit →
  `bash scripts/deploy-push.sh`. · Kabul: sayfalar canlıda doğru durumu gösterir.
- [ ] T20 (keyword-map) — **/kredi-karti-faiz-hesaplama yeni araç** · hedef: kredi kartı faiz hesaplama (11,6) + kredi
  kartı faiz oranı (7,7). TCMB'nin GÜNCEL azami akdi/gecikme faiz oranları (TCMB duyurusu, tarihli; EVDS'te varsa veriden),
  borç × ay → faiz + KKDF %15 + BSMV %15, asgari ödeme yapılırsa borç kaç ayda biter tablosu. /blog/kredi-karti-asgari-
  odeme-tutari-2026 ve /blog/kredi-yapilandirma-2026-… yazılarından link. · Kabul: T17 ile aynı (veri dosyası + kaynak).
- [ ] T14 (zam sezonu — TARİHLİ, TÜİK 2027 takvimi yayımlanınca; genelde Ocak'ın ilk günleri) — **TÜİK 2027
  takvimi:** `data/tuik-enflasyon-2027.json` oluştur (2026 dosyasıyla aynı şema; en az "Aralık 2026" → Ocak 2027
  açıklama günü). release-watch.py, emekli/memur sayfaları ve sonuç kutusu takvim dosyalarını glob'la okur; dosya yoksa
  ayın 3-6'sına bakılır (çalışır ama tarih metni eksik kalır). · Kabul: `python3 scripts/release-watch.py --dry --today <gün>` doğru günü söyler.
- [ ] T15 (zam sezonu — 5 Ocak 2027, açıklama günü) — **Ocak 2027 emekli zammı resmî rakam kontrolü:** /emekli-zammi-hesaplama
  ve /memur-zammi-hesaplama birikimli enflasyonu aylık % değişimleri bileşikleyerek hesaplıyor (Temmuz 2026 resmî %17,75 =
  bileşik %17,75). 5 Ocak'ta Aralık TÜFE açıklanınca resmî SSK/Bağ-Kur oranını ÇSGB/SGK açıklamasından doğrula; farklıysa
  `data/tufe-aylik.json`'a `"resmiZam": {"2027-01": {"ssk": <oran>}}` ekle (src/data/zam2027.ts bunu esas alır) →
  build → deploy. · Kabul: canlı sayfadaki oran resmî açıklamayla aynı.
- [ ] T16 (zam sezonu — TARİHLİ, 24 Aralık–10 Ocak) — **Ocak 2027 resmî tarife turu** (RC 10-18 listesi). Aralık sonu
  Resmî Gazete'de çıkan her tebliği WebSearch/RG ile doğrula, sayfayı 2027 resmî rakamına çevir ("tahmin" → "resmî"),
  OG kartını (`scripts/og-images.py` sabit kartlar) yenile, build → deploy. Sıra = arama hacmi:
  1. Asgari ücret: `scripts/asgari-ucret-watch.py` otomatik yazar → doğrula; 1 Ocak'ta yıl devri otomatik. Bağlı sabitler:
     `net-maas-hesaplama` (MIN_BRUT + 2027 tarife), `issizlik-maasi-hesaplama` (MIN_BRUT).
  2. GVK 2027 tarifesi (dilimler, kira istisnası) → `vergi-dilimi-hesaplama`, `gelir-vergisi-hesaplama`, `net-maas-hesaplama`.
  3. MTV 2027 tarifesi + Harçlar Tebliği (CB oranı ≠ YD olabilir → `data/yeniden-degerleme.json` `uygulananOrani`) →
     `mtv-hesaplama` ORNEK tutarları, `pasaport-ehliyet-harci`, `noter-ucretleri` harçları, `tapu-harci-hesaplama` asgari harç.
  4. DVK Tebliği Seri 72 → `damga-vergisi-hesaplama` (BAZ_YIL=2027, tutarlar). VİVK Tebliği Seri 58 → `data/veraset-2026.json`
     2027 değerleri. Noterlik Ücret Tarifesi 2027 → `noter-ucretleri`. TKGM 2027 fiyat listesi → `data/tapu-harci-2026.json`
     `gosterge2027`. TÜVTÜRK 2027 tarifesi (1 Ocak) → `arac-muayene-ucreti`.
  5. Kıdem tavanı (HMB katsayı genelgesi) → `data/kidem-tavan.json`; memur katsayıları → `data/emekli-memur.json`
     (/evde-bakim-maasi ve /engelli-maasi kendiliğinden döner; ASHB Ocak duyurusundaki resmî tutarları `data/sosyal-aylik-2026.json`
     resmi bloğuna yaz; 2027 bütçe K cetveli kanunlaşınca butce.2027.durum="kanun"); doğum yardımı CB kararıyla artarsa
     `data/dogum-yardimi-2026.json`; en düşük emekli aylığı + bayram ikramiyesi; trafik cezaları 2027; emekli promosyonu
     tablosunu Ocak kademeleriyle yenile (T17).
  6. 5 Ocak sonrası: `src/data/zam2027.ts` PERIOD'u 2027-01..06 (Temmuz 2027 zammı) turuna çevir; emekli/memur sayfa metinleri.
  · Kabul: listedeki her sayfa canlıda 2027 resmî rakamını gösterir; health.py temiz.

## Bakım / ürün
- [ ] V3 (video kalitesi/özgünlük) — **Günlük konu kümesi kapısı** · V2 bulgusu (10-15): aynı gün aynı konudan iki video
  → biri akışı alıyor, diğeri 0-13 izlenme; son günlerde altın 3 hatta aynı gün (10-21: altin-cetveli viral + altin-faizsiz
  Manim; 10-20: altin-dusse viral + altin-hesabi daily). `scripts/viral-script.py` konu seçimine kapı: bugün (UTC) diğer
  hatların yüklediği/planladığı videoların başlık+slug'ından ana varlık kümesini çıkar (altın/dolar/euro/borsa/kripto/
  faiz/kredi/vergi/emekli — küçük anahtar sözlük) ve viral senaryo aynı kümeye düşüyorsa farklı kümeden konu seç (yoksa
  üret, log'a yaz — üretimi durdurma). Kaynak: youtube-upload kayıtları/`public/social/` bugünkü dosyalar. İzole test:
  `--dry` ile bugünün durumunda seçilen kümeyi yazdır. · Kabul: commit + rapora dry-run çıktısı; 7 gün sonra haftalık
  koşu aynı gün aynı kümeden 2+ video sayısını sayar (baz: 10-15→10-21).
- [x] P2 (portföy) — → kira-artis-update.sh TÜFE değişince `deploy-app.sh` çağırıyor + health.py "app TÜFE kopyası eski" bekçisi; app yeniden dağıtıldı (TÜFE 2026-09 güncel — sorun gecikme mekanizmasıydı: app ayın 2'sinde, TÜFE ayın 3'ünde → ~1 ay) · haftalık koşu 10-22 — **app.parafomo.com veri tazeliği** · Kabul: commit; backlog-portfolio.md notu.

## Kullanıcı girdisi gelince (o gün en üste al)
- R2 bilgileri → `/root/.config/parafomo/backup.env` (backup.sh otomatik kullanır).

## Notlar (günlük koşu için)
- **Blog kuyruğu tarihlidir** (content-queue.md): 26 Ekim Fed önizleme, 2 Kasım Ekim enflasyonu önizleme. Bir gün
  aksarsa günlük koşu (03:00 UTC, daily-content'ten önce) o günün tarihli konusunu kuyruğun EN ÜSTÜNE taşısın.
  Olay yazısı slug'ı bahis desenine uymalı: `fed-faiz-karari-28-ekim-2026-…`, `ekim-2026-enflasyon-beklentisi-…`.
- **Sonraki olaylar (B261022-1, haftalık koşu 10-29 kuyruğa koyar):** ABD NFP (Ekim verisi, BLS takviminden doğrula —
  genelde Kasım'ın ilk Cuma'sı) ve ABD CPI (Ekim verisi, BLS) önizlemeleri — Trends ≈0 ama GSC'de tık getiriyor.
  JOLTS/PCE/ISM/GDP önizlemesi YAZMA.
- **Neden bu sıra:** baş sorgularda otorite kilidi (yeni sayfalarda da p60-99); kazanılabilir yer gelecek yıl (2027),
  sitede karşılığı olmayan hacimli niyet (emekli promosyon 178,6) ve olay günü yazıları.
- **YAPMA:** baş sorgular için başlık-H1-FAQ dürtmesi · "X mi Y mi" yazısı · yeni getiri sayfası (B261006-2 lost) ·
  JOLTS/PCE/ISM yazısı · elle sonuç kutusu (sonuc: frontmatter otomatik).
- **RC 2026-10-18/19 altyapısı — TEKRARLAMA/GERİ ALMA:** açıklama günü motoru (live-posts, `sonuc:` kutusu, release-watch,
  sitemap lastmod) · asgari ücret veriden + Aralık bekçisi · ana sayfa "2027 Zam Sezonu" · blog "Bu konuda hesapla"
  kutusu (`src/data/tools.ts`) · K10-K21 araç sayfaları.
- Olay sonrası güncelleme bekleyen yazılar: abd-ekim-2026-cpi (açıklandı — sonuç kutusu var mı kontrol et).
- Headless: döngü/değişken/awk/heredoc yok; çok adımlı iş `agent/state/*.py` ile.

## Biten / iptal (bu hafta)
- Geçen hafta biten (10-15 → 10-21): T1 /konut-kredisi-hesaplama · T2 kıdem 2027 tavan · T3 /emlak-vergisi-hesaplama ·
  T4 TCMB yazısı güncellendi (yanlış faiz düzeltildi) · T5 /ihtiyac-kredisi-hesaplama + EVDS faizleri · T6 OTORITE eylemi ·
  K1 memur zammı · K2 en düşük emekli maaşı · K3 bayram ikramiyesi · K5 enflasyon hesaplama · K8 gelir vergisi ·
  K9a ihbar · K9b yıllık izin · K10-K13, K16, K19-K21 (RC) · kurumlar vergisi · bağ-kur primi · değer artış kazancı ·
  altın alt sayfa title'ları · PCE sonuç kutuları · V1 altyazı çakışması (6 gün temiz) · V2 0-izlenme teşhisi ·
  P1 panel→içerik köprüsü. Bitmeyen: T4b (tarihli 23 Ekim), T13-T16 (tarihli).
