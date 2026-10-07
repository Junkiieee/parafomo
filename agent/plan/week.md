# Hafta planı — 2026-10-07 → 2026-10-14
_Kurulum oturumu (v2 başlangıç planı) · 2026-10-06 · ilk haftalık Opus koşusu Perşembe 2026-10-08'de bu planı revize eder._
<!-- plan-date: 2026-10-06 -->

## Durum
- Kaan hedefi netleştirdi (2026-10-06): **ParaFOMO'yu marka yap ve siteden para kazan — ama ÖNCE TRAFİK.**
  AdSense trafik oturana kadar YOK (Kaan kararı). Claude Max 5x'e geçildi (günlük koşu da Opus). Tüm onaylar verildi;
  gereken hesap/API'yi o getirecek (`agent/plan/user-tasks.md`). Marka kitabı: `agent/plan/brand.md`.
- Sistem 30 Eylül'den beri duraklatılmıştı; v2 ile yeniden başlıyor. Ajansız haftada bile gerçek erişim
  51/hafta (202640, rekor) — veri sayfası motoru gecikmeli çalışmaya devam ediyor.
- GSC 28g: 105 tık / 6.433 gös. En çok tıklanan: /altin-getiri (32), /enflasyon-takvimi (10), /dolar-getiri (10).
  AI asistan 28g'de 20 kullanıcı (~%12). Telegram kanalı 2 üye (dağıtım etkisi ~0).
- **Bozuk:** her yazının ve ana sayfanın altındaki bülten formu `action="#"` — kimse abone olamıyor (N1).

## Bahisler
- **B261006-1 — Halka arz şirket sayfaları** · GSC /halka-arz/* ≥500 gös + ≥15 tık/hafta · 2026-11-03
- **B261006-2 — Getiri kümesini genişlet** · küme 28g tık ~43 → ≥85 · 2026-11-03
- **B261006-4 — YouTube video kalite reformu** · yeni videolarda 7g medyan ≥200 izlenme + ≥8 abone/hafta · 2026-10-28
- ~~B261006-3 AdSense~~ — kapatıldı (Kaan: önce trafik)

## Görev kuyruğu (günlük koşu en üstteki [ ]'yi alır)
- [x] T1 (B261006-1) — **Halka arz şirket sayfaları: `/halka-arz/<slug>` dinamik rota + ilk yayın.** → 40 sayfa canlı (40/40 200, sitemap 40, /halka-arz'dan 40 iç-link; örn. https://parafomo.com/halka-arz/albayrak-hazir-beton-san-ve-tic-a-s/). fetch-halka-arz.py künyeyi (şekil, fon kullanımı, finansallar, halka açıklık, iskonto, büyüklük, dağıtım sonuçları, kişi başı lot) yapısal çıkarıyor → hiçbir sayfa ince değil, hepsi index; kalıcı arşiv `data/halka-arz-sirketler.json` (takvimden düşen sayfa 404 olmaz). Title şablonu T2'den önden yapıldı · 2026-10-07
  `src/pages/halka-arz/[slug].astro` (getStaticPaths ← `data/halka-arz.json` items; `halka-arz-getiri.json`
  ile `bist_code`/şirket adı üzerinden birleştir). Her sayfa: H1 "<Şirket> Halka Arz" + durum, talep
  tarihleri, fiyat, lot, dağıtım yöntemi, aracı kurum tablosu; borsada işlem görüyorsa halka arz fiyatına
  göre getiri (+ 2026 halka arz ortalamasıyla kıyas); "nasıl katılınır" kısa rehber; SSS (FAQPage şeması:
  ne zaman / kaç lot / fiyatı ne / kaç kazandırdı — yalnız veride olan alanlarla); BreadcrumbList;
  /halka-arz ve /halka-arz-getiri'ye bağlantı; kaynak (halkarz.com) + güncelleme tarihi. /halka-arz
  listesindeki her şirket adı kendi sayfasına linklensin. İnce içerik riskine dikkat: veride neredeyse hiç
  alan olmayan arzlar için de sayfa mantıklı mı karar ver (gerekirse `noindex`). Sayfalar
  `halka-arz-update.sh` 6 saatte bir veri tazeledikçe deploy'la kendiliğinden güncellenir.
  · Kabul: build geçer; canlıda ≥30 şirket sayfası 200 döner; sitemap'te görünür; /halka-arz'dan linkli.
- [ ] M1 (SEO/marka) — **Güven (E-E-A-T) sayfaları + Organization şeması** (finans/YMYL sıralaması için; reklamla ilgisi yok). `/hakkimizda`'yı yeniden yaz
  (misyon = brand.md konumlandırması; içerik nasıl üretiliyor: veriler kaynaklarından otomatik çekilir,
  metinler yapay zekâ destekli hazırlanır — DÜRÜST yaz, olmayan insan/uzman denetimini iddia etme);
  yeni `/editoryal-politika` (kaynak, doğruluk, düzeltme, "yatırım tavsiyesi değildir", ortaklık/reklam
  ilkesi) ve `/metodoloji` (getiri/takvim/hesaplayıcı formülleri ve veri kaynakları: Yahoo Finance,
  TCMB, TÜİK, halkarz.com...) ve `/iletisim` (SITE.email + sosyal hesaplar). Footer'a linkler. Tüm sayfalara
  `Organization` JSON-LD (logo + `sameAs`: X, Instagram, YouTube @parafomo, Telegram). Yazı şemasında
  publisher = Organization. · Kabul: 4 sayfa canlı 200; footer'da; şema `grep` ile doğrulanır.
- [ ] N1 (dağıtım) — **Bülten v1 — kendi altyapımızla (bozuk formu onar).** Backend'e (`backend/`, portföy
  protokolü: geçici DB ile test → restart → /health) `POST /newsletter/subscribe` (e-posta + KVKK onayı,
  IP rate-limit, çift onay: Brevo SMTP ile — portföy şifre sıfırlama maili zaten bu altyapıyı kullanıyor —
  onay linki), `GET /newsletter/confirm`, `GET /newsletter/unsubscribe` (token), ayrı `newsletter_subscribers`
  tablosu (mevcut tabloları DEĞİŞTİRME). `src/components/Newsletter.astro` formu bu uca bağlansın (başarı/
  hata mesajı, `action="#"` kalmasın). Haftalık gönderim betiği ayrı görev (N2). · Kabul: canlıda abone ol →
  onay maili gelir → onaylayınca DB'de `confirmed`; çık linki çalışır; build geçer.
- [ ] T2 (B261006-1) — **Halka arz sayfalarını SEO ile güçlendir:** her sayfaya title/description şablonu
  ("<Şirket> (<KOD>) halka arz: tarih, fiyat, lot ve getiri"); /halka-arz sayfasına "Ekim 2026 halka arz
  takvimi" bölümü + iç linkler; ALBTN blog yazısından şirket sayfasına bağlantı. · Kabul: meta + şema
  `grep` ile doğrulanır, canlıda kontrol.
- [ ] T3 (B261006-2) — **/gumus-getiri sayfası:** `scripts/silver-returns.py` (gold-returns.py kalıbı;
  Yahoo SI=F × USDTRY=X; gram gümüş TL = ons/31.1035 × kur; YTD + 1/3/5/10 yıl TL/USD getirisi; ağ hatasında
  mevcut veriyi koru) → `data/gumus-getiri.json` + `public/` kopyası → `src/pages/gumus-getiri.astro`
  (altin-getiri.astro kalıbı) → /altin-dolar-borsa hub tablosuna gümüş satırı → `daily-content.sh` veri
  adımlarına ekle. · Kabul: build geçer, canlıda sayfa + hub'da gümüş.
- [ ] T4 (B261006-2) — **/euro-getiri sayfası** (EURTRY=X; T3 ile aynı kalıp; "euro mu dolar mı" karar
  bölümü + /dolar-getiri ve hub'a bağlantı). · Kabul: build geçer, canlıda sayfa + hub'da euro.
- [ ] T5 (AI asistan görünürlüğü) — `public/llms.txt` (site özeti + en değerli veri/araç sayfaları +
  kaynak/güncelleme notu); getiri ve takvim sayfalarında görünür "Son güncelleme: <tarih> · Kaynak: ..."
  satırı ve Dataset şeması (yoksa). · Kabul: canlıda /llms.txt 200; 3 sayfada şema doğrulanır.

## Bakım / ürün / marka
- [ ] P1 (portföy) — `agent/plan/backlog-portfolio.md`'deki en üstteki açık madde (şu an: İzleme listesi /
  watchlist — sahip olmadan takip). Backend değişirse protokoldeki restart + /health. · Kabul: build geçer,
  canlı panelde akış çalışır.
- [ ] V1 (video) — **Format kararı için kanıt tablosu:** viral videolar (2026-08-01 →) format × izlenme
  (yayından ≥7 gün sonra) × beğeni/yorum; `data/learning/metrics.jsonl` + `content-ledger.jsonl`'dan
  python ile çıkar, sonucu bu dosyanın "Notlar" bölümüne yaz. 09-30'daki rotasyon değişikliği (shock/news
  azaltıldı) izlenme verisiyle tutarlı mı? Karar haftalık koşunun — sen yalnız tabloyu ve 3 satırlık yorumu yaz.
- [ ] V2 (marka) — **YouTube kanal kimliğini markayla hizala:** kanal adı "ParaFOMO", açıklama brand.md
  konumlandırması + parafomo.com (UTM'li) + Telegram/Instagram, kanal anahtar kelimeleri. YouTube API
  (`channels.update` brandingSettings, mevcut OAuth `youtube.force-ssl` ise) ile dene; yetki yetmezse
  Kaan'a 3 adımlık görev yaz. · Kabul: kanal sayfasında yeni açıklama görünür.

## Kullanıcı girdisi gelince (o gün en üste al)
- X API ödemesi açılınca → günlük veri kartı + yeni yazı paylaşım betiği (`scripts/post-x.py`), cron önerisi.
- R2/S3 yedek bilgileri → `/root/.config/parafomo/backup.env` (backup.sh otomatik kullanır; boto3 gerekirse venv'e kur).

## Notlar
- YouTube düzeltmeleri (2026-10-06, B261006-4): yayındaki videolarda alakasız yabancı stok (Filipin pesosu etiketi,
  zloti, Hollanda bayrağı), simsiyah kare, "2.021" yıl rozeti, statik/İ'siz Manim kartları vardı. Düzeltildi:
  kültüre özgü stok → rakamlı marka kartı (`content_concept` safe bayrağı); görsel yoksa kart; blog videoları
  artık senaryonun seçtiği gerçek görselleri (TCMB binası, Fitch logosu) kullanıyor (`shorts_visuals` hiç
  okunmuyordu); kart v2 (rakam ana öğe, Türkçe büyük harf, üst üçte bir, karartmasız); "yüzde on beş"=%15;
  senaryo görsel kuralı: Türk kurumu gerçek adıyla, yabancı banknot/etiket/bayrak yasak.
  Müzik: `/root/parafomo-media/music/` klasörüne parça konunca otomatik kullanılır (Kaan getirecek).
- Kurulum oturumunda yapıldı (2026-10-06): marka sesi tüm videolarda **Orus** (Edge A/B kapandı);
  viral videolarda jenerik stok sahneler otomatik **Manim marka kartına** dönüşüyor (`manimify.py --hybrid`;
  gerçek foto/grafik korunuyor); blog→Short videoları artık IG Reel de oluyor; portföy DB günlük yedek
  (`scripts/backup.sh` → /root/parafomo-backups); footer'a YouTube + Telegram linkleri.
- v1 deneyi 2026-09-30-1 (viral format rebalansı, `scripts/viral-daily.sh` DOW_FMT) hâlâ yürürlükte; ilk
  haftalık koşu V1 tablosuyla karar verecek.
- Video müziği: render "gerçek müzik yok → geçici pad" diyor — telifsiz müzik kütüphanesi bir video kalitesi
  görevi olabilir (haftalık koşu değerlendirsin).

## Biten / iptal (bu hafta)
