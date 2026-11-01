# Video yönü — 2026-10-30 (Kaan kararı: "parafomonun kullanım stilini değiştiriyoruz")

**Karar:** ParaFOMO'nun görsel dili artık kodla çizilmiş animasyon (`scripts/anim/`). Eski stok-video / Manim kartı /
statik görsel kart üretimi emekli. Shorts, Reels ve uzun videolar bu dille yapılır. Ajan: video işlerini bu dosyaya
göre seç; eski motora (shorts-build-v4) yalnız yeni motor çökerse yedek olarak düşülür.

## İki görsel dil
1. **Veri animasyonu (izometrik + kaplamalar)** — günlük Shorts/Reels. `scripts/anim/scenes.js` sahneleri (büyük rakam,
   patlatılmış katman, sütun, karşılaştırma, adımlar, ikonlu cümle, kapanış), `skins.js` 8 kaplama, dönüş `skins.json`.
   Sahne planı gece hazırlıkta LLM'le (`anim_from_scenario.py`), sayı kapısı: ekrandaki rakam o an konuşulan cümlede geçer.
2. **"Ekonomi Defteri" (el çizimi, insanlı; 2026-10-31 Kaan: Dalio'ya benzer ad/görüntü telif riski → ayrıştı)** — haftalık seri.
   `scripts/anim/kits/defter.js`: düz krem kâğıt, koyu mürekkep, YÜZLÜ büyük kafalı karakterler (ana karakter Mert: sarı
   kapüşonlu, gözlüklü), Türkiye mekânları (simitçi), fosforlu kalem vurgusu, Caveat el yazısı, ParaFOMO yeşili başlık kartı.
   "Ekonomi Makinesi" adı ve lacivert süslü çerçeve KULLANILMAZ. İlk bölüm: `pieces/defter-enflasyon` (Short, 37 sn).
   Eski `kits/dalio.js` + `pieces/dalio-enflasyon` emekli (yayınlanmadı).
   **Yayın: haftada 2 Short — Salı + Cuma 13:00** (Kaan 2026-10-31 "iki shorta çıkaralım"). Bölüm elle yazılır (`pieces/defter-*.js/json`,
   `"short": true, "format": "ekonomi_defteri"`), sonra `kuyruk.py ekle <slug> --title … --tarih <Cuma> --onayla`
   (tarihli onay: o günden önce çıkmaz; YT "Ekonomi Defteri" listesi + meta `comment` ile bölüm yorumu).
   #1 Enflasyon (simit) → Sal 3 Kas (TÜFE günü) · #2 Taksit → Cum 6 Kas · #3 Önce zam sonra indirim (11.11 arifesi) → Sal 10 Kas
   (Kaan onayı bekliyor) · #4 Cum 13 Kas: "Faiz nedir" (Pazar uzun bölümün habercisi). Sonraki adaylar: vergi dilimi (Aralık
   maaşı), kredi kartı asgari ödeme, bileşik enflasyon. Rakamlar "örnek" etiketli, güncel veri iddiası yok.
   **Uzun bölüm (16:9) — her Pazar 12:00 TSİ** (Kaan 2026-10-31 "seoya uygun ekonomi defteri tarzında haftada 1 gün").
   Aynı motor: spec'e `"aspect": "16:9"` + satırlara `"chapter"` → `public/social/longform/<slug>.mp4` + meta (bölümler,
   SRT, kapak = parçanın `drawThumb()`'ı). Kit 16:9'da titleCard/pageTitle yatay düzene geçer. Yükleme Kaan izleyip
   onaylayınca: `ONAYLI_YAYIN=1 lf_upload.py upload <slug> --at <Pazar 09:00Z>` (gizli + zamanlanmış) → yayında
   `lf_upload.py publish <slug>` ("Ekonomi Defteri" listesi + bölüm yorumu). SEO: başlık ≤60 krk aranan soru
   ("Enflasyon Nedir…"), `lf_package.py` kapak/başlık denetimi, açıklamada anahtar kelimeler + araç linki + rehber linki,
   Türkçe SRT. Uzun #1 Enflasyon nedir (5:45, 11 bölüm) → Paz 8 Kas · #2 Faiz nedir → Paz 15 Kas · sonra kredi/borç,
   dolar kuru, maaşın anatomisi, emekli zammı hesabı (Ocak'tan önce), kira artışı, altın.

   **Konu seçimi VERİYLE ve ONAYSIZ (Kaan 2026-11-01: "bana sunma, sen seç ve paylaş"):** `scripts/anim/defter_konu.py plan
   --hafta <Pzt> --yaz` → havuz `agent/plan/defter-konular.json`, seçimler `agent/plan/defter-plan.json`. Sinyal: Trends 12 ay
   hacmi + son 4 hafta ivmesi (fırsat motoru önbelleği; fiyat niyeti ×0,4, dev baş terim ×0,4) × YouTube öneri sayısı × tema
   (bu hafta ×1,6, 5 hafta içinde gelecek ×1,3). Önce Pazar uzun, Cuma Short = aynı konunun habercisi, Salı = kalan en iyi.
   Verilen söz (bölüm sonunda "sonraki sayfa") veriden önce gelir → `elle: true` + `neden`. Ekonomi Defteri bölümleri artık
   Kaan onayı beklemeden `kuyruk.py ekle … --tarih … --onayla` ile kuyruğa girer; video bilgi için Kaan'a gönderilir (itiraz
   ederse çekilir). Gece aday Short'ları için onay kuralı DEĞİŞMEDİ. Havuz boşaldıkça yeni konu eklenir; Pazar karnesinde
   bölüm izlenmeleri + Kaan oyu sinyale eklenecek.

## Yayın düzeni (2026-10-31 Kaan onayı)
- **Takvim:** `agent/plan/icerik-takvimi.json` — 2 Kas → 10 Oca, 10 hafta zam sezonu (yeniden değerleme, 11.11, vergi dilimi,
  asgari ücret, emekli zammı, faiz kararları, 2026 karnesi). Gece üretimi konuları buradan alır.
- **Onaylı kuyruk:** `scripts/anim/kuyruk.py` (+ `scripts/kuyruk.sh` cron). Gece 00:40 UTC 2 aday → sabah raporunda Kaan onaylar
  → 10:00 ve 16:00 UTC (13:00/19:00 TSİ) yayın. Onaysız hiçbir şey çıkmaz; `PUBLISH_PAUSED` yerinde, yalnız `ONAYLI_YAYIN=1` geçer.
  Kuyruk/geri bildirim: `/root/parafomo-data/onay/kuyruk.json`. Adayların rakamları sabah raporundan ÖNCE doğrulanır
  (ilk adayda "cezalar her Kasım %25 artıyor" hatası yakalandı → düzeltildi).
- **KARAR 2026-10-31 (son): eski motor (klasik stok+kart, Manim) gece hattından ÇIKTI** — Kaan: "eski sistemde stillerle
  video üretimi yapılmasın, yenileri deneyelim; her paylaşımda beğendim/beğenmedim diyeceğim". Gece: 2 izometrik, 8
  kaplamanın hepsi döner (iso, paper, riso, blueprint, cutpaper, ink, pixel, sketch). Kaan'ın oyu `kuyruk.py begen|begenme
  <no>` → `rapor` karnesinde izlenmenin yanında. Sabah raporu dünkü yayınlar için oyu sorar. Olay videosu (event-short)
  PUBLISH_PAUSED altında üretilir → kuyruğa "bekliyor" → Kaan onaylayınca `kuyruk.sh yayinla --no <n>` hemen çıkar.
  Blog (daily-content) + bülten 2026-10-31 yeniden AÇIK; ajan ~7 Kasım'da açılacak; viral/shorts/news/manim/spk-ig KAPALI.
- **Teknik deneyi (2026-10-31 güncelleme, Kaan "diğer tekniklerle de deneyelim"):** 5 kaplama aynı izometrik çizimin
  renkleri olduğu için asıl eksen TEKNİK yapıldı: her gece 1 `iso` (kodla izometrik infografik, kaplama içeride döner) +
  1 `klasik` (eski viral motor: stok/arşiv görsel + Manim veri kartı, shorts-build-v4; kanalın 1000+ videolarının çoğu bu
  motordan → taban çizgisi) + haftalık `defter`. Karne iki katmanlı: teknik karnesi + izometrik içinde kaplama karnesi.
  Hazır olunca 4. teknik adayı: kinetik tipografi (Anton/Oswald) ya da Economist kolaj; otomatik defter (V4).
- **Stil deneyi (izometrik içinde):** 5 kaplama (iso, paper, riso, blueprint, cutpaper) eşit dağılım, ~3 hafta; ölçüt 7. gün ortanca izlenme,
  ort. izleme %, abone/1000, IG erişim (`kuyruk.py rapor`). Aşama 2 = alt yarı elenir, %70 kazanan / %30 keşif.
  Aşama 3 = sırayla kanca tipi, süre, müzik (tek değişken). Haftalık karne Pazar raporunda; kalıcı karar Kaan'ın.
- **Kanal temizliği (31 Eki):** YouTube'da toplam izlenmesi 1000 altı 320 video gizleniyor (liste: `/root/parafomo-data/yt-private-plan-20261031.json`,
  geri alma `tools/yt_hide_under.py undo`). IG: Kaan çoğunu gizledi; kalan 190 Reel silinecek (yedek `/root/parafomo-data/ig-backup-20261031*`),
  `instagram_manage_contents` izni için Kaan'ın token'ı bekleniyor.

## Kanallar
- **YouTube Shorts:** günde 2 güçlü video (3-4 değil). Öncelik: olay günleri (`event-short.py`) > blog konusu > viral format.
- **YouTube uzun:** her Pazar 1 "Ekonomi Defteri" uzun bölümü (16:9, 6-10 dk; 8 dk üstü orta reklam açar).
  Konu sırası: enflasyon → faiz nasıl çalışır → kredi/borç döngüsü → dolar kuru neden yükselir → maaşın anatomisi
  (vergi/SGK) → emekli zammı nasıl hesaplanır (Ocak dalgasından önce) → kira artış oranı → altın neden değerli.
- **Instagram:** eski görsel gönderiler DURDU (altin-daily / bist-daily ×2 / halka-arz-ig cron'ları 2026-10-30 KAPALI).
  Kaan eski gönderileri uygulamadan arşivliyor. Günde en çok 2 Reel (yeni stil).
- **Facebook:** Reels aynı videolar (değişiklik yok).
- **Kanal temizliği:** 2026-10-30'da son 90 günde 0 izlenmeli 23 video gizlendi (liste ve geri alma:
  `/root/parafomo-data/yt-private-plan-20261030.json`). 2026-11-30'da yeniden bak; izlenme alanlar açık kalır.

## Teknik sıra (V = video işi)
- [x] V1 (2026-10-31) — kaplama seçimi yerine stil deneyi (kuyruk.py, 5 stil eşit dağılım → veriyle eleme).
- [ ] V2 (Kaan kararı) — ses zinciri A/B (EQ + de-esser + kompresör) → evet ise anim_build anlatımına ekle.
- [x] V3 (2026-10-30) — Instagram Reels günlük üst sınır 2 (instagram-reel.py; fazlası yalnız YouTube/FB).
- [ ] V4 — defter kitini (karakterli) otomatik hatta bağla, sonra deneye 6. stil olarak girer: LLM sahne planı → karakterli sahne şablonları (alışveriş, para yağmuru,
  kuyruk, fiyat etiketi, grafik, banka, ev, maaş bordrosu). Kabul: bir senaryodan insansız elle müdahalesiz Short.
- [x] V5 (2026-10-31) — uzun video 16:9 anim motorunda (aspect 16:9 + chapter + SRT + kapak); ilk bölüm Enflasyon nedir.
- [ ] V6 — ölçüm: meta `engine: anim` etiketi; 14 gün sonra yeni/eski kıyas (izlenme, ort. izlenme %, abone/1000 izlenme).
  Hedef: abone/1000 izlenme ≥ 2 (şu an ~0,8).
- [ ] V7 — HyperFrames blok testi (data-chart, milestone-reveal; sunucu boştayken, yük korumasıyla).
- [ ] V8 — SFX katmanı (Kenney CC0 + kodla üretilen efekt), sahne kesmeleri müzik vuruşuna (librosa).

## Sunucu nezaketi (Kaan: aynı sunucuda başka işler de var)
Render hep `nice 19` + Chromium alt süreçleri 30 karede bir renice + 1 dk yük > 2,5 ise 20 dk'ya kadar bekler.
Ağır işler (uzun video render) gece saatlerine konur.
