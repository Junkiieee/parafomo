# Hafta planı — 2026-10-29 → 2026-11-04
_Haftalık koşu: 2026-10-29 · model claude-opus-5-5_
<!-- plan-date: 2026-10-29 -->

## Durum
- Gerçek erişim (Direct hariç) son 7g **76** (geçen haftaki koşuda 59) · son tam hafta 202643: **81** — 9 haftanın en iyisi
  (202642: 64, 4 hafta önce 202639: 36). 28g 228 (196). Hedefin %1,1'i.
- GSC 202643: **40 tık / 4.196 gösterim** (202642: 43 / 2.130). Gösterim 2 katına çıktı ama tık yerinde saydı. Artış
  derin sıralardan geldi, tık getirmiyor: /tasit-kredisi 419 gösterim p85, altın alt sayfaları +500 p83-91, kredi kartı faiz p81.
  Tıklar iki yerden geliyor. Biri **sosyal ödeme sayfaları** (doğum yardımı 4 tık p8,4 · evde bakım 4 p15,6 · engelli 2 p22,
  açılış 10-19). Diğeri eski kazananlar (euro-mı-dolar-mı 5, altın-getiri 3). Bundan yeni bahis çıktı: **B261029-1**.
- Halka arz bahsi **lost** (7g 194 gösterim / 4 tık, iki haftadır düz). Sayfalar otomatik akmaya devam ediyor.
  Fed 28 Ekim sonuç kutusu 19:25 UTC'de kendiliğinden geldi, sonuç Short'u yayında. **T21 bitti.**
- YouTube **60 abone (+7/7g, en iyi hafta)** · +7.016 izlenme/7g (önceki +1.886) · 1000 izlenme başına abone 0,69'dan 0,8'e.
  En çok izlenen üç videonun ikisi aranan konuların blog→Short'u: Fed önizleme 1.159, geçici vergi 1.019 (altın takı 936).
  Viral formatlar 11-192 izlenme. IG 21 / FB 0 (Meta izni bekleniyor) · bülten 1 · AdSense kapalı (Kaan kararı).
- **Otopsi:** geçen haftanın 4 tarihsiz görevi 10-23'te bitti. 10-26→10-28 koşuları 3-10 dk sürdü, kuyruk boştu.
  Bu yüzden bu hafta **9 tarihsiz görev** var. §9c'nin ilk 15 satırı yine OTORITE ya da eşleme gürültüsü
  (borsa istanbul/bist 100/"evet" → yanlış sayfa). Bu yüzden web görevleri bu koşuda Trends'le yeni ölçülen sorgulardan seçildi:
  KYK burs 122 (son 4 hafta 459) · bedelli askerlik 111 · doğum izni 97 · emekli maaşı 2027 98 (zirve 852) · dul maaşı 31 +
  yetim aylığı 19 · askerlik borçlanması 30.

## Bahisler
- **B261029-1 — Sosyal haklar kümesi (devlet ödemesi/SGK hak tutarı sayfaları)** · 7g ≥25 tık + ≥700 gös (baz 9 / 240) · değerlendirme 2026-11-26
- **B261022-1 — Olay takvimi motoru** · olay yazıları 28g ≥60 tık + ≥900 gös (şimdi 31 / 463) · değerlendirme 2026-11-19
- **B261015-1 — Fırsat motoru: 2027 zam sezonu + hacimli araçlar** · 7g ≥400 gös + ≥10 tık (şimdi 167 / 1) · değerlendirme 2026-11-12
- Kapandı: B261006-1 (halka arz şirket sayfaları) → **lost** (7g 194 gös / 4 tık, hedef 500/15; iki hafta düz).

## Görev kuyruğu (günlük koşu en üstteki [ ]'yi alır)
Kural: TARİHLİ görevin günü geldiyse ÖNCE o; yoksa en üstteki tarihsiz [ ]. Gecede 1-2 görev bitir; 5 dk'da biten koşu = hata.
Resmî rakamı birincil kaynaktan (mevzuat.gov.tr, RG, SGK, ASHB, GSB, MSB) doğrula. İki kaynak çelişirse o rakamı YAZMA,
"resmî duyuruyu kontrol edin" de.
**Yeni sayfa kontrol listesi:** `src/data/tools.ts` kaydı (k: anahtar kelimeler) + Footer TOOL_LINKS + `scripts/og-images.py`
CARDS + `image="/og/<slug>.png"` + FAQPage + ilgili 2 sayfadan metin içi link → `npm run build` →
`bash scripts/deploy-push.sh` → `python3 scripts/wait-live.py https://parafomo.com/<slug>/` → keyword-map'e `[x]`. Rakam
`data/*.json`'a kaynak URL + tarih ile girer. Memur katsayısına bağlı tutarlar `data/emekli-memur.json`'dan okunur, sayfaya
sabit yazılmaz. Ocak 2027 tahmini `src/data/zam2027.ts`'ten gelir (evde-bakim-maasi kalıbı).

- [x] T21 (B261022-1) — **Fed 28 Ekim sonrası kontrol** → policy-decisions 19:25 UTC: sabit, bant %3,75–4,00, oy 10–2
  (kaynak federalreserve.gov monetary20261028a). Canlıda başlık "Fed 28 Ekim Kararı Açıklandı (sabit): Faiz Bandı %3,75–4,00".
  /fed-faiz-takvimi "Sıradaki Karar 9 Aralık". Sonuç Short'u https://youtube.com/shorts/Ow7VUplxNY0 · haftalık koşu 2026-10-29.
- [ ] T23 (B261029-1 — TARİHLİ, 1 Kasım) — **Emekli promosyonu tablosunu yenile** · Akbank, Garanti BBVA ve Yapı Kredi
  kampanyaları 31 Ekim'de bitiyor; health.py 1 Kasım'da uyarır. Her bankanın kendi kampanya sayfasından yeni tutarı ve
  bitiş tarihini al → `data/emekli-promosyon.json`. Kampanya yenilenmediyse satırı "kampanya sona erdi" yap, tutar uydurma.
  Build → deploy. · Kabul: https://parafomo.com/emekli-promosyonu/ güncel tarihleri gösteriyor ve health.py temiz.
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
- [ ] T22 (B261022-1 | R1 — TARİHLİ, 4 Kasım, T13'ten hemen sonra) — **TÜİK 3 Kasım olay günü doğrulaması** · (1)
  `logs/event-shorts.json`'da `tuik:2026-10` `done` mı, iki video da (enflasyon+kira / yeniden değerleme) açılıyor mu?
  `failed` ise kök nedeni `logs/event-short.log`'dan bul. Olay ≤36 saatlikse `python3 scripts/event-short.py` ile yeniden üret.
  (2) /blog/ekim-2026-enflasyon-beklentisi-3-kasim'da sonuç kutusu "Açıklandı" + başlık doğru mu? SSS'yi geçmiş zamana
  çevir, `updatedDate` ekle. (3) /kira-artis-orani-hesaplama, /emekli-zammi-hesaplama ve /memur-zammi-hesaplama Ekim TÜFE'sini
  gösteriyor mu? (4) app.parafomo.com TÜFE kopyası güncel mi (health.py)? · Kabul: dört madde canlıda doğru, ya da
  sorunun nedeni raporda.
- [x] T24 (B261029-1) — **/kyk-burs-miktari yeni veri sayfası (KYK burs/kredi tutarı + geri ödeme)** → canlı https://parafomo.com/kyk-burs-miktari/ (GSB 05.01.2026: 4.000/8.000/12.000 TL; tarihçe 2024-26; 351 s.K. md.16 geri ödeme+erteleme hesaplayıcısı; health Ocak tazeliği) · 2026-10-30 · hedef: kyk burs
  (hacim 122, son 4 hafta 459 — zirve ŞU AN, Ekim). 2026-2027 öğretim yılı burs/öğrenim kredisi tutarlarını (önlisans/lisans,
  yüksek lisans, doktora) YALNIZ GSB/KYK resmî duyurusundan al (gsb.gov.tr, kygm.gsb.gov.tr). Ödeme günü, başvuru/sonuç
  takvimi ve "burs mu kredi mi" farkını ekle. Hesaplayıcı: aylık tutar × ay → toplam borç; geri ödeme taksiti (mezuniyetten
  2 yıl sonra, taksit sayısı = kredi alınan ay sayısı; TÜFE/ÜFE güncellemesinin güncel kuralını 5102 s.K.'dan doğrula). 2026-2027
  tutarı henüz açıklanmadıysa sayfayı 2025-2026 resmî tutarla, "yeni dönem tutarı açıklanınca güncellenir" notuyla aç.
  health.py'ye tazelik satırı ekle. · Kabul: sayfa canlı, tutarın kaynağı ve tarihi sayfada; FAQPage var.
- [x] T25 (B261029-1) — **/bedelli-askerlik-ucreti yeni veri sayfası** → canlı https://parafomo.com/bedelli-askerlik-ucreti/
  (7179 md.9 mevzuat.gov.tr metni: 300.000 gösterge × ödeme günü katsayısı — 7577 s.K. ile 240.000'den; 300.000 × 1,575512 =
  472.653,60 TL MSB ile birebir; ek bedel 3.500 gösterge/ay hesaplayıcısı; dövizle askerlik md.39 = aynı TL'nin avro karşılığı,
  sabit 5.000 € YOK; Ocak 2027 ≈ 516.829 TL zam2027'den; OG kartı, tools.ts, Footer, memur-zammı + evde-bakım linkleri) · commit
  f54b955 · haftalık koşu 2026-10-29 · hedef: bedelli askerlik ücreti (hacim 111, zirve
  Mart 427; tutar Ocak ve Temmuz'da memur katsayısıyla değişir). Formülü 7179 s. Askeralma Kanunu md.10'dan al
  (mevzuat.gov.tr; gösterge × memur aylık katsayısı). `data/emekli-memur.json` katsayısıyla hesapla. Temmuz 2026 tutarını
  MSB/ASAL duyurusuyla çapraz kontrol et. Ocak 2027 tahmini zam2027 memur projeksiyonundan, "tahmin" etiketiyle. Ek bölümler:
  dövizle askerlik (tutar kanundan), taksit/ödeme yeri. Yaş/şart bilgisi yalnız kanundan. /evde-bakim-maasi ve
  /memur-zammi-hesaplama'dan link. · Kabul: sayfa canlı, hesaplanan tutar resmî duyuruyla kuruşu kuruşuna aynı.
- [x] T26 (R3 — YouTube) — **YouTube arama başlık turu (20 video)** → 20/20 güncellendi (scripts/youtube-retitle.py --dry/--apply), baz agent/memory/yt-retitle-2026-11.json (YT araması 28g %18,8); yanlış TMSF limitli asQhzroHVUM (400 bin, gerçek 1,2 mn) gizliye alındı · 2026-10-30 — · izlenmenin %19-21'i YouTube aramasından. Bu hafta
  aranan konuların blog→Short'u öne çıktı (Fed önizleme 1.159, geçici vergi 1.019). Yeni betik
  `scripts/youtube-retitle.py --dry` yaz (`agent/state/yt_retitle.py` kalıbı). Betik son 60 günün en çok izlenen 20
  videosunu alır, `data/learning/yt-search-terms.json` + brief §1b arama kalıplarına bakarak yeni başlık önerir: konu + yıl/ay
  ilk 40 karakterde, abartısız, videonun söylediğiyle birebir. Öneri listesini report.md'ye koy, sonra uygula: `videos.update`
  part=snippet; categoryId, tags ve description geri gönderilir. Uygulamadan önce `yt_search_share` bazını
  `agent/memory/yt-retitle-2026-11.json`'a kaydet. · Kabul: 20 video güncel + baz dosyası commit'li; haftalık koşu 11-12'de kıyaslar.
- [ ] T27 (B261015-1 | R2) — **"Emekli maaşım ne kadar olacak?" tutar tablosu** · hedef: emekli maaşı 2027 (hacim 98,
  zirve Ocak 852) + "X TL emekli maaşı ne kadar olacak" uzun kuyruğu. Yeni sayfa AÇMA: /emekli-zammi-hesaplama'ya
  `#tutar-tablosu` bölümü ekle. En düşük aylık + 15/18/20/25/30/35/40/50 bin TL maaşlar için Ocak 2027 tahmini (SSK ve
  Bağ-Kur ayrı). Rakamlar `src/data/zam2027.ts`'ten üretilir, elle sayı yok. Aynı bileşenle /memur-zammi-hesaplama'ya
  memur maaşı 2027 (41) tablosu ekle. FAQPage'e 2 soru. · Kabul: iki sayfada tablo canlı; TÜFE güncellenince tablo kendiliğinden değişiyor.
- [ ] T28 (B261029-1) — **/askerlik-borclanmasi-hesaplama yeni araç** · hedef: askerlik borçlanması (hacim 30, zirve
  Aralık 75). Formül 5510 md.41: gün × prime esas günlük kazanç (alt sınır = günlük brüt asgari ücret, üst sınır 9 katı) ×
  %32 (4/a; 4/b ve 4/c oranlarını kanundan doğrula). Doğum borçlanmasını aynı sayfada ayrı bölüm yap (çocuk başı 720 gün,
  en fazla 3 çocuk; şartlar kanundan). Asgari ücret `data/asgari-ucret.json`'dan. Bilgi notu: Ocak'ta asgari ücret artınca
  borçlanma tutarı da artar (tavsiye dili yok). /emeklilik-hesaplama ve /blog/sgk-hizmet-dokumu-nasil-alinir-nasil-okunur'dan
  link. · Kabul: canlı; 3 örnek hesap SGK'nın kendi örneği ya da formülle tutarlı.
- [ ] T29 (R4 — YouTube) — **Konu oynatma listeleri + abone vaadi** · 1000 izlenme başına abone 0,8. Format listeleri
  var, ama aranabilir konu listeleri yok. `scripts/youtube-extras.py`'ye başlık/etiket anahtar kelimesine göre konu listeleri ekle:
  "Zam Sezonu 2027: Emekli, Memur, Asgari Ücret" · "Faiz Kararları: TCMB ve Fed" · "Altın: Fiyat, Ayar, Getiri" ·
  "Vergi ve Harçlar 2027". Video hem format hem konu listesine girer. Son 60 günü tek seferlik geri doldur (`--backfill`,
  kota: insert başına 50 birim, günlük 10.000; gerekirse iki güne böl). Konu listesine giren yeni videoların sabit yorumu:
  "Rakam açıklanınca ilk burada — abone ol" + ilgili araç linki (funnel_comment). · Kabul: 4 liste kanalda görünür ve
  dolu; yeni videolar otomatik ekleniyor (log).
- [ ] T30 (B261029-1) — **/dul-yetim-maasi-hesaplama yeni araç** · hedef: dul maaşı (hacim 31, zirve Ocak 129) + yetim
  aylığı (19, zirve Ocak 73). Hak sahibi oranları 5510 md.34'ten: eş %50, çocuk yoksa ve eş çalışmıyorsa %75, çocuk %25,
  ana-baba %25, toplam ≤%100 ve indirim kuralı. Bağlanma şartları md.32-33'ten. Girdi: ölenin aylığı + hak sahipleri →
  kişi başı tutar. Ocak 2027 zam tahmini emekli zammı modülünden. En düşük aylık tamamlamasının nasıl bölüşüldüğünü SGK'dan
  doğrula; doğrulayamazsan yazma. · Kabul: canlı; kanundaki 2 örnek senaryo doğru hesaplanıyor.
- [ ] T31 (B261029-1) — **/dogum-izni-hesaplama yeni araç** · hedef: doğum izni (hacim 97, zirve Nisan 393). İzin süresini
  GÜNCEL metinden al: İş Kanunu md.74 + 657 DMK md.104. 2025-2026 süre değişikliği var mı, mevzuat.gov.tr güncel metninden
  kontrol et, haber sitesinden alma. Tahmini doğum tarihi → izin başlangıcı/bitişi; çoğul gebelik ve erken doğum kuralları;
  babalık izni (işçi/memur); süt izni. Analık ödeneği 5510 md.18: günlük kazancın 2/3'ü × gün. /dogum-yardimi ile karşılıklı
  link. · Kabul: canlı; tarih hesabı 3 senaryoda kanunla tutarlı.
- [ ] T32 (R10 — Instagram) — **BIST kartlarını akıştan Story'ye al** · IG'de günde 6-7 gönderi var; BIST/altın kartlarına
  etkileşim 0, Reels ortalaması 1. 465 gönderiye 21 takipçi. BIST açılış+kapanış kartı betiğine `--story` modu ekle
  (`scripts/post-*-instagram.py`; bist kapanış story'si zaten var: commit 0dd12b8 kalıbı). Altın kartını haftada 3 güne indir.
  Cron değişikliğini `deploy/crontab.txt`'e yaz. Kaan'ın user-tasks #1'deki `crontab deploy/crontab.txt` komutu bunu da kurar;
  ayrı görev açma. Her betiği `--dry` ile dene. · Kabul: crontab.txt diff + dry çıktısı raporda; script commit'li.

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
- [ ] V4 (video kalitesi | R13) — **Olay günü ve aynı küme kapısı: viral slotu atla** · 28 Ekim'de Fed sonuç Short'u
  ile aynı gün çıkan viral "fed faizi TL'yi…" videosu 11 izlenme aldı, gram altın videosu 16. Aynı gün aynı küme
  birbirini yiyor (V2 dersi). Ayrıca kanalda şablon video hacmi YPP'deki "özgün olmayan içerik" riskini büyütüyor.
  Yapılacak: `viral-daily.sh`/`viral-script.py`'de bugün `logs/event-shorts.json`'da `done` olay varsa ya da gündem Short'u
  çıktıysa viral slotunu atla (log'a "olay günü — atlandı" yaz). Önce izole dene: son 14 günü simüle et, kaç slotun
  atlanacağını rapora yaz. · Kabul: `--dry` simülasyonu + kapı commit'li; ertesi olay günü (3 Kasım) log'da "atlandı" görünür.
- [ ] P3 (portföy) — **Fiyat kaynağı dayanıklılığı** (backlog-portfolio.md) · Yahoo 429 ya da boş yanıt verirse yedek
  kaynağa geç (altın için mevcut `data/altin-fiyat.json`). Son iyi fiyatı cache'te tut, süresini akıllıca uzat. Toplu fiyatı
  tek tek değil batch çek. Veritabanı şeması DEĞİŞMEZ. Değişiklikten sonra `systemctl restart parafomo-api` +
  `curl -s https://api.parafomo.com/health`. · Kabul: 429 simülasyonunda özet uç noktası fiyat döndürüyor; backlog'da [x].
- [ ] M1 (web/mobil | R20) — **Mobil yatay taşmalar + WebApplication şeması** · ziyaretçinin %65'i mobil. 360 px'te
  geniş tablolar taşıyor (ör. fed-faiz-karari-28-ekim-2026-beklentiler 495 px). Yazı tablolarını PostLayout düzeyinde
  `overflow-x:auto` sarmalayıcıya al. Bülten formu 320 px'te 7 px taşıyor, düzelt. WebApplication şemasını yalnız
  tools.ts'deki gerçek araçlara bas. · Kabul: 360 px'te yatay kaydırma yok (tarayıcı testi ya da CSS kanıtı); şema yalnız araçlarda.
- [ ] S1 (sistem) — **Fırsat motoru eşleme gürültüsü** · §9c'de sitede karşılığı OLAN sorgular hâlâ YENI_* çıkıyor:
  brüt asgari ücret → /asgari-ucret-hesaplama · kıdem tazminatı tavanı → /kidem-tazminati-hesaplama · mevduat faiz oranları →
  /mevduat-faizi-hesaplama · enflasyon oranı → /enflasyon-hesaplama · emekli maaş hesaplama → /en-dusuk-emekli-maasi ·
  brütten nete maaş hesaplama → /net-maas-hesaplama · faiz kararı ne zaman → /tcmb-faiz-takvimi. Bunları `SYNONYMS`'e ekle.
  "borsa istanbul", "bist 100", "borsa gündem" ve "evet" sorguları en-iyi-yatırım/halka-arz yazısına yanlış bağlanıyor; bunları
  hariç tut. Bu koşuda ölçülen yeni sorguları `HEAD_TERMS`'e ekle (kyk burs, bedelli askerlik ücreti, doğum izni, dul maaşı,
  askerlik borçlanması, emekli maaşı 2027). · Kabul: §9c ilk 15 satırında yanlış eşleme yok.

## Kullanıcı girdisi gelince (o gün en üste al)
- Meta izni gelirse (`logs/fb-status.json` ok:true) → roadmap R9 ilk hafta ölçümü.
- Kaan R14/R15 kararını verirse → roadmap'te ilgili maddeyi aç/kapat.

## Notlar (günlük koşu için)
- **Blog kuyruğu tarihli** (content-queue.md): 30 Ekim Ekim enflasyonu önizlemesi · 4 Kasım ABD NFP önizlemesi (NFP 6 Kasım
  Cuma 15:30 TSİ, iki takvim aynı) · 9 Kasım ABD CPI önizlemesi (CPI 10 Kasım; tek kaynak, BLS'den doğrula). Bir gün
  aksarsa günlük koşu o günün tarihli satırını EN ÜSTE taşısın. Slug'lar bahis desenine uymalı: `abd-ekim-2026-nfp-…` YOK
  (Ekim NFP adı zaten kullanıldı) → `abd-kasim-2026-nfp-istihdam-verisi-…` ve `abd-kasim-2026-cpi-verisi-…`.
- **Neden bu sıra:** baş sorgular otorite kilidinde (yeni araçlar da p60-99). Kazanılan yerler üç tane: sosyal ödeme sayfaları
  (p8-22, tık var), 2027 varyantları (p6-11) ve olay günü yazıları. Video tarafında aranan konuların blog→Short'u.
- **YAPMA:** baş sorgu için başlık/H1/FAQ dürtmesi · "X mi Y mi" yazısı · yeni getiri sayfası · yeni halka arz emeği
  (B261006-1 lost; sayfalar otomatik) · JOLTS/PCE/ISM/GDP yazısı · elle sonuç kutusu.
- **RC 2026-10-18/19/28 altyapısı — TEKRARLAMA:** açıklama günü motoru, olay sonucu Short'u, paylaş çubuğu, News sitemap,
  Facebook yayıncıları, render kilidi, roadmap.md.
- Kuyruk biterse: `agent/plan/roadmap.md` en üstteki uygun madde (R5 Discover, R6 ince yazılar, R11 alarm, R12 llms.txt).
- Headless: döngü/değişken/awk/heredoc yok; çok adımlı iş `agent/state/*.py` ile.

## Biten / iptal (bu hafta)
- Geçen hafta biten (10-22 → 10-28): T4b TCMB kararı (−100 bp, regex düzeltmesi) · T17 /emekli-promosyonu · T18
  /emeklilik-hesaplama · T19 fırsat motoru alt sayfa eşlemesi · T20 /kredi-karti-faiz-hesaplama · V3 günlük konu kümesi
  kapısı · P2 app veri tazeliği · ek: /gss-primi-hesaplama, /otv-hesaplama, halka arz başlıkları ≤70 · RC 10-28: olay sonucu
  Short motoru, paylaş çubuğu + News sitemap, FB yayıncıları, roadmap. Bu koşuda: T21 Fed kontrolü · T25 /bedelli-askerlik-ucreti.
- T24 notu (10-29): KYK 2026-2027 tutarı resmî olarak bulunamadı (haberler çelişkili: "4.000/8.000/12.000 TL Ocak 2026'dan beri",
  "2027 tutarı yıl sonuna doğru"). Günlük koşu yalnız gsb.gov.tr / kygm duyurusuyla yazsın.
