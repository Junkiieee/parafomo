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
   **Yayın: her Cuma 1 bölüm** (Kaan 2026-10-31 "süper olmuş devam böyle"). Bölüm elle yazılır (`pieces/defter-*.js/json`,
   `"short": true, "format": "ekonomi_defteri"`), sonra `kuyruk.py ekle <slug> --title … --tarih <Cuma> --onayla`
   (tarihli onay: o günden önce çıkmaz; YT "Ekonomi Defteri" listesi + meta `comment` ile bölüm yorumu).
   #1 Enflasyon (simit) → 6 Kas · #2 Taksit mi peşin mi (11.11 haftası) → 13 Kas · sonraki adaylar: bileşik enflasyon,
   vergi dilimi (Aralık maaşı), faiz nedir (TCMB/Fed haftası). Rakamlar "örnek" etiketli, güncel veri iddiası yok.

## Yayın düzeni (2026-10-31 Kaan onayı)
- **Takvim:** `agent/plan/icerik-takvimi.json` — 2 Kas → 10 Oca, 10 hafta zam sezonu (yeniden değerleme, 11.11, vergi dilimi,
  asgari ücret, emekli zammı, faiz kararları, 2026 karnesi). Gece üretimi konuları buradan alır.
- **Onaylı kuyruk:** `scripts/anim/kuyruk.py` (+ `scripts/kuyruk.sh` cron). Gece 00:40 UTC 2 aday → sabah raporunda Kaan onaylar
  → 10:00 ve 16:00 UTC (13:00/19:00 TSİ) yayın. Onaysız hiçbir şey çıkmaz; `PUBLISH_PAUSED` yerinde, yalnız `ONAYLI_YAYIN=1` geçer.
  Kuyruk/geri bildirim: `/root/parafomo-data/onay/kuyruk.json`. Adayların rakamları sabah raporundan ÖNCE doğrulanır
  (ilk adayda "cezalar her Kasım %25 artıyor" hatası yakalandı → düzeltildi).
- **Stil deneyi:** aşama 1 = 5 stil (iso, paper, riso, blueprint, cutpaper) eşit dağılım, ~3 hafta; ölçüt 7. gün ortanca izlenme,
  ort. izleme %, abone/1000, IG erişim (`kuyruk.py rapor`). Aşama 2 = alt yarı elenir, %70 kazanan / %30 keşif.
  Aşama 3 = sırayla kanca tipi, süre, müzik (tek değişken). Haftalık karne Pazar raporunda; kalıcı karar Kaan'ın.
- **Kanal temizliği (31 Eki):** YouTube'da toplam izlenmesi 1000 altı 320 video gizleniyor (liste: `/root/parafomo-data/yt-private-plan-20261031.json`,
  geri alma `tools/yt_hide_under.py undo`). IG: Kaan çoğunu gizledi; kalan 190 Reel silinecek (yedek `/root/parafomo-data/ig-backup-20261031*`),
  `instagram_manage_contents` izni için Kaan'ın token'ı bekleniyor.

## Kanallar
- **YouTube Shorts:** günde 2 güçlü video (3-4 değil). Öncelik: olay günleri (`event-short.py`) > blog konusu > viral format.
- **YouTube uzun:** haftada 1 "Ekonomi Defteri" bölümü, 8-10 dk (orta reklam), aynı bölümden 2-3 Short kesit.
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
- [ ] V5 — uzun video 16:9: lf_ hattının görsel katmanı anim + defter kitine taşınır; "Ekonomi Defteri #1: Enflasyon" 8-10 dk.
- [ ] V6 — ölçüm: meta `engine: anim` etiketi; 14 gün sonra yeni/eski kıyas (izlenme, ort. izlenme %, abone/1000 izlenme).
  Hedef: abone/1000 izlenme ≥ 2 (şu an ~0,8).
- [ ] V7 — HyperFrames blok testi (data-chart, milestone-reveal; sunucu boştayken, yük korumasıyla).
- [ ] V8 — SFX katmanı (Kenney CC0 + kodla üretilen efekt), sahne kesmeleri müzik vuruşuna (librosa).

## Sunucu nezaketi (Kaan: aynı sunucuda başka işler de var)
Render hep `nice 19` + Chromium alt süreçleri 30 karede bir renice + 1 dk yük > 2,5 ise 20 dk'ya kadar bekler.
Ağır işler (uzun video render) gece saatlerine konur.
