# Hafta planı — 2026-10-07 → 2026-10-14
_Kurulum oturumu (v2 başlangıç planı) · 2026-10-06 · ilk haftalık Opus koşusu Perşembe 2026-10-08'de bu planı revize eder._
<!-- plan-date: 2026-10-06 -->

## Durum
- Sistem 2026-09-30'dan beri duraklatılmıştı; v2 ile yeniden başlıyor. Ajansız geçen haftada bile
  gerçek erişim 51/hafta ile rekor (202640) — veri sayfası motoru gecikmeli etkiyle çalışmaya devam ediyor.
- GSC 28g: 105 tık / 6.433 gösterim. En çok tıklanan: /altin-getiri (32), /enflasyon-takvimi (10),
  /dolar-getiri (10). AI asistan 28g'de 20 kullanıcı (~%12).
- Talep sinyali: "albayrak hazır beton hisse" 179 gös (poz 12, tek blog yazısı); "halka arz
  takvimi/takvim/tarihleri" ~97 gös ama /halka-arz poz ~67-70 → şirket bazlı halka arz sayfaları boşluğu.

## Bahisler
- **B261006-1 — Halka arz şirket sayfaları** · GSC /halka-arz/* ≥500 gös + ≥15 tık/hafta · değerlendirme 2026-11-03
- **B261006-2 — Getiri kümesini genişlet** · küme 28g tık ~42 → ≥85 · değerlendirme 2026-11-03

## Görev kuyruğu (günlük koşu en üstteki [ ]'yi alır)
- [ ] T1 (B261006-1) — **Halka arz şirket sayfaları: `/halka-arz/<slug>` dinamik rota + ilk yayın.**
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
- [ ] T2 (B261006-1) — **Halka arz sayfalarını SEO ile güçlendir:** her sayfaya title/description şablonu
  ("<Şirket> (<KOD>) halka arz: tarih, fiyat, lot ve getiri"), varsa Organization/Event şeması doğrulaması,
  /halka-arz sayfasının kendisine "Ekim 2026 halka arz takvimi" bölümü + iç linkler; ALBTN blog yazısından
  şirket sayfasına bağlantı. · Kabul: `grep` ile şema + meta doğrulanır, canlıda kontrol.
- [ ] T3 (B261006-2) — **/gumus-getiri sayfası:** `scripts/silver-returns.py` (gold-returns.py kalıbı;
  Yahoo SI=F × USDTRY=X; gram gümüş TL = ons/31.1035 × kur; YTD + 1/3/5/10 yıl TL/USD getirisi; ağ hatasında
  mevcut veriyi koru) → `data/gumus-getiri.json` + `public/` kopyası → `src/pages/gumus-getiri.astro`
  (altin-getiri.astro kalıbı) → /altin-dolar-borsa hub tablosuna gümüş satırı → `daily-content.sh` veri
  adımlarına ekle. · Kabul: build geçer, canlıda sayfa + hub'da gümüş.
- [ ] T4 (B261006-2) — **/euro-getiri sayfası** (EURTRY=X; T3 ile aynı kalıp; "euro mu dolar mı" karar
  bölümü + /dolar-getiri ve hub'a bağlantı). · Kabul: build geçer, canlıda sayfa + hub'da euro.
- [ ] T5 (AI asistan görünürlüğü) — `public/llms.txt` (site özeti + en değerli veri/araç sayfalarının
  listesi + kaynak/güncelleme notu); getiri ve takvim sayfalarında görünür "Son güncelleme: <tarih> ·
  Kaynak: ..." satırı ve Dataset şeması (yoksa). · Kabul: canlıda /llms.txt 200; 3 sayfada şema doğrulanır.

## Bakım / ürün
- [ ] P1 (portföy) — `agent/plan/backlog-portfolio.md`'deki en üstteki açık madde (şu an: İzleme listesi /
  watchlist — sahip olmadan takip). Backend değişirse protokoldeki restart + /health. · Kabul: build geçer,
  canlı panelde akış çalışır.
- [ ] V1 (video) — **Format kararı için kanıt tablosu:** viral videolar (2026-08-01 →) format × izlenme
  (yayından ≥7 gün sonra) × beğeni/yorum; `data/learning/metrics.jsonl` + `content-ledger.jsonl`'dan
  python ile çıkar, sonucu bu dosyanın "Notlar" bölümüne yaz. 09-30'daki rotasyon değişikliği (shock/news
  azaltıldı) izlenme verisiyle tutarlı mı? Karar haftalık koşunun — sen yalnız tabloyu ve 3 satırlık yorumu yaz.

## Notlar
- v1 deneyi 2026-09-30-1 (viral format rebalansı, `scripts/viral-daily.sh` DOW_FMT) hâlâ yürürlükte; ilk
  haftalık koşu V1 tablosuyla karar verecek.

## Biten / iptal (bu hafta)
