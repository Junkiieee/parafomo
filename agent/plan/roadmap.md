# Yol haritası — kalıcı fikir havuzu (RC 2026-10-28, Kaan: "sistemi geliştirecek her şeyi düşün, canlıya al")

**Ne işe yarar:** `week.md` kuyruğunda bugün yapılabilir görev kalmadığında günlük koşu buradan en üstteki uygun
`[ ]` maddeyi alır, week.md'ye `T<n>` olarak ekler ve uçtan uca yapar — **boş koşu yok** (10-26→10-28 koşuları 3-10 dk
sürdü, kuyruk boştu). Haftalık koşu her hafta bu listeyi gözden geçirir: biteni `[x]`, anlamsızlaşanı `[-]` yapar,
sıralar, yeni fikir ekler (açık madde ≤ 25). Biçim: `- [ ] R<n> (kanal) — **başlık** · neden · ne · Kabul: …`.
`(Kaan kararı)` etiketli madde Kaan onaylamadan yapılmaz — onay/ret `user-tasks.md` ya da panelden gelir.

## ⚠️ YENİ VİDEO YÖNÜ (Kaan kararı 2026-10-30) — video işleri önce `agent/plan/video-yon.md`
Görsel dil kodla-animasyona geçti (izometrik veri animasyonu + el çizimi "Ekonomi Makinesi" serisi). R10/R13 bu dosyadaki
V3/V-hacim kararıyla güncellendi; R14 (uzun video) → V5 olarak devam. Eski IG görsel kart cron'ları kapalı.

## Teşhis güncellemesi (haftalık koşu 2026-10-29)
- W43 gerçek erişim 81 (9 haftanın en iyisi). GSC gösterimi 2x (4.196) ama tık 40'ta kaldı: artış p80+ sıralardan.
  Tıklar sosyal ödeme sayfalarından geliyor (doğum yardımı/evde bakım/engelli p8-22) → yeni küme B261029-1 (week T24-T31).
- YouTube +7 abone/7g (60), 1000 izlenme başına abone 0,8. En iyi iki video aranan konunun blog→Short'u (Fed önizleme
  1.159, geçici vergi 1.019) → R3 başlık turu öne alındı.
- Bu haftaya alınanlar: R1 → T22 (TÜİK 4 Kasım) · R2 → T27 · R3 → T26 · R4 → T29 · R10 → T32 · R13 → V4 · R20 → M1.

## Teşhis (2026-10-28 verisi — kararları buna dayandır)
- Gerçek ziyaretçi 7g **78** (hedef 7000, %1,1). Google tıklarının **~%95'i** Google'ın gizlediği nadir uzun-kuyruk
  sorgulardan (28g 131 tıkın yalnız 6'sı görünür sorgudan); gösterimlerin %69'u 50. sıranın altında. Büyüme = sayfa ×
  uzun-kuyruk yüzeyi + olay günleri; baş sorgular otorite kilidinde.
- Discover **0**, Google News ~0 gösterim. Geri dönen ziyaretçi 28g 15 / 419 (sadakat ~0).
- YouTube 28g 8.650 izlenme → **6 abone (%0,07)**. Kaynak: Shorts akışı %78, **YouTube araması %21**. İzleyicinin
  **%68'i 35-54 yaş** (zam sezonunun kitlesi); %11'i Almanya'dan. En iyi günler olay günleri (TCMB 22 Ekim 1.346 izl/gün).
- Instagram 465 gönderi → 21 takipçi. Facebook sayfası 0 takipçi, hiç kullanılmıyor — ama GA4'te facebook.com'dan 28g
  46 ziyaretçi zaten geliyor.
- Kasım-Ocak = yılın en büyük finans arama dalgası (3 Kasım YD/TÜFE, Aralık asgari ücret, 5 Ocak emekli/memur zammı).

## Yapıldı (RC 2026-10-28) — tekrar yapma, yalnız izle
- [x] R0a (YouTube/olay) — **Olay sonucu Short motoru** → `scripts/event-short.py`: TÜİK/TCMB/Fed/asgari ücret resmî
  rakamı gelince "açıklandı" videosu (zorunlu rakam başlıkta yoksa video çıkmaz); durum `logs/event-shorts.json`,
  sağlık §3 "Dağıtım" satırı. İlk canlı: Fed 28 Ekim (policy-decisions 19:25 UTC), TÜİK 3 Kasım.
- [x] R0b (web) — **Paylaş çubuğu + Discover/News hazırlığı** → WhatsApp/Telegram/FB/X/kopyala (UTM `utm_campaign=share`,
  GA4 `share` olayı; 147 araç/veri sayfası + her yazıda 2 çubuk), Article şemasında 1600×900 kapak fotoğrafı, olay
  yazılarında NewsArticle, `/news-sitemap.xml` (robots.txt + GSC'ye gönderildi 10-28) · commit 41f42d3.
- [x] R0c (Facebook) — **Facebook Reels + link paylaşımı** → `scripts/facebook-reel.py`, `scripts/facebook-post.py`
  (izin gelene kadar sessiz atlar; `logs/fb-status.json`). Kaan'ın Meta izni bekleniyor (user-tasks).
- [x] R0d (ajan) — **Kendi kendini besleyen kuyruk + kanal metrikleri** → bu dosya, brief §1b (YouTube arama payı,
  abone/1000 izlenme, IG/FB takipçi, Discover/News, gizli sorgu payı, geri dönen, paylaş trafiği), §4 kuyruk derinliği.
- [x] R0e (video) — **Render kilidi** → üç video hattı aynı geçici klasörü kullanıyordu; artık sırayla render.

## Açık — öncelik sırası (kaldıraç × başarı olasılığı)
- [ ] R1 (olay günü — her olayda) — **Olay günü doğrulama rutini** · olay sonrası İLK günlük koşuda: `logs/event-shorts.json`
  ilgili anahtar `done` mı + YouTube linki açılıyor mu; `failed` ise `logs/event-short.log`'dan kök nedeni bul, düzelt,
  olay hâlâ tazeyse (≤36 sa) `python3 scripts/event-short.py` ile yeniden üret. Takvim: Fed 28 Ekim → 29 Ekim koşusu ·
  TÜİK 3 Kasım → 4 Kasım · TÜİK 3 Aralık · Fed 9 Aralık · TCMB 10 Aralık · asgari ücret (Aralık sonu) · TÜİK 5 Ocak.
  Kabul: her olayın videosu yayında ya da nedeni raporda.
- [x] R2 (zam sezonu · → week T27, 10-29) → iki sayfada #tutar-tablosu canlı · 2026-10-30 — — **"Maaşım ne kadar olacak?" tutar tabloları** · Ocak'ta "X TL emekli maaşı ne kadar olacak"
  türü uzun-kuyruk patlar; tıkların ~%95'i zaten uzun-kuyruktan. /emekli-zammi-hesaplama'ya (yeni sayfa DEĞİL) tutar
  tablosu bölümü: en düşük aylık + 15/20/25/30/40 bin TL… için Ocak 2027 tahmini (5 Ocak'ta kesin) — rakamlar
  `src/data/zam2027.ts`/veriden; aynısı /asgari-ucret-hesaplama için net/brüt/işveren maliyeti tablosu (Aralık'ta
  açıklanınca otomatik). Şişirme yok, tek sayfa + çapa linkler. Kabul: canlı, veriden üretilir, FAQPage güncel.
- [x] R3 (YouTube · → week T26, 10-29) → 20 video yeniden başlıklandı, baz yt-retitle-2026-11.json; kıyas haftalık 11-12 · 2026-10-30 — — **Arama odaklı başlık turu** · izlenmenin %21'i YouTube aramasından. Son 60 günün en çok izlenen 20
  videosunun başlık/açıklamasını aranan kalıba çek (konu + yıl/ay ilk 40 karakterde; yanıltıcı değil). Token
  `youtube.force-ssl` içeriyor → `videos.update part=snippet` (categoryId + tags + description geri gönder). Önce
  `scripts/youtube-retitle.py --dry` yaz, öneri listesini rapora koy, sonra uygula. Kabul: 20 video güncel + baz
  (yt_search_share) kaydı; 14 gün sonra haftalık koşu kıyaslar.
- [ ] R4 (YouTube · → week T29, 10-29; olay listesi + sabit yorum 345fc9b'de yapıldı) — **Abone dönüşümü %0,07 → %0,3** · 28g 8.650 izlenme → 6 abone. Seri playlist'leri ("Zam Sezonu 2027",
  "Faiz Kararları", "Altın") `youtube-extras.py` ile otomatik; son karede tek net vaat ("Rakam açıklanınca ilk burada —
  abone ol"); olay Short'larına sabit yorumla sıradaki olay tarihi. Kabul: playlist'ler + CTA metni canlı; brief §1b
  `yt_subs_per_1k` 4 haftalık trend.
- [ ] R5 (web/Discover) — **Olay yazılarını Discover'a uygun kur** · Discover 0. Olay önizleme/sonuç yazılarında kapak =
  kurumun gerçek fotoğrafı (1600×900, Wikimedia), başlık "kimin cebine ne" (tık tuzağı değil), ilk paragrafta rakam,
  yayın günü sabah. Kabul: §1b `discover_impr_28d` > 0 ya da 3 hafta sonra ders.
- [ ] R6 (SEO) — **İndekslenmeyen ince yazıları birleştir** · seo-audit: 24 sayfa 14+ gündür "Tarandı - dizine
  eklenmemiş" (çoğu genel "nedir"). Haftada 3-4'ünü konusu aynı güçlü sayfaya 301'le (worker REDIRECTS) ya da özgün
  veri/tablo ekle. Kabul: liste 24 → < 10; 301'ler canlıda.
- [ ] R7 (SEO/CTR) — **İlk sayfadaki sorgular için başlık/description** · p1-10'da gösterim alıp 0 tık: "gümüş mü altın mı
  daha çok kazandırdı" p7,8 · "fed toplantı tarihleri 2026" p9,2 · "euro 1 yılda ne kadar kazandırır" p7,4 · "fed faiz
  kararı takvimi 2026" p7,6. (Baş-sorgu dürtmesi DEĞİL — onlar p60+.) Sorgunun kelimesini title/description'a koy.
  Kabul: 10 sayfa; 14 gün sonra bu sorguların CTR'ı.
- [ ] R8 (WhatsApp) — **Paylaşım döngüsünü büyüt** · R0b ölçümü (§1b "paylaş butonundan gelen") 2 hafta veri toplasın;
  tık geliyorsa hesaplayıcı sonuçlarını paylaşım metnine ekle ("Ocak zammım %X çıktı — sen de hesapla: link").
  Kabul: veriyle karar (≥10 ziyaret/hafta → genişlet; 0 → bırak).
- [ ] R9 (Facebook) — **İzin gelince ilk hafta** · `logs/fb-status.json` ok:true olunca 7 gün: GA4 facebook kaynağı + sayfa
  takipçisi (§1b). Reels erişim veriyorsa blog link paylaşımı + olay Short'ları FB'de sürer; vermiyorsa ders yaz.
- [ ] R10 (Instagram · → week T32, 10-29) — **Akışı Reels'e çevir** · ölçüm (RC 10-28, son 8 gün): günde 6-7 gönderi = 3-4 Reel (ort. 1
  beğeni+yorum) + 2 BIST kartı + 1 altın kartı (ikisi de 0 etkileşim); halka arz/SPK kartları koşullu, son günlerde çıkmadı.
  465 gönderi → 21 takipçi. Öneri: BIST açılış+kapanış kartı → Story'ye (akışa değil), altın kartı haftada 3; Reels
  açıklamasında ilk satır = arama kalıbı (IG araması). Cron'u sen yazamazsın → `deploy/crontab.txt` + Kaan'a tek satırlık
  görev; script tarafı (feed yerine story) senin. (insights izni gelirse önce ölç.)
- [ ] R11 (sadakat) — **"Rakam açıklanınca haber ver" alarmı** · geri dönen ziyaretçi ~0. Bülten formunu zam sezonu
  sayfalarında "Emekli zammı/asgari ücret açıklanınca e-posta" olarak sun; olay motoru (event-short) tetiklendiğinde
  abonelere kısa mail (newsletter altyapısı + Brevo var). Kabul: form + otomatik mail + abone sayısı §12'de.
- [ ] R12 (AI asistan) — **AI cevap motorları** · ChatGPT 28g 17 ziyaretçi (gerçek trafiğin ~%8'i, Bing indeksinden).
  `/llms.txt`'i `src/data/tools.ts`'ten otomatik üret (araç + tek cümle cevap + güncelleme tarihi); araç sayfalarında
  "Kısa cevap" kutusu (rakam + tarih + kaynak) eksik olanlara. Kabul: llms.txt build'de üretiliyor.
- [ ] R13 (video · olay günü kapısı → week V4, 10-29) — **Video hacmi: günde 3-4 → 2-3 güçlü** · aynı gün aynı küme yamyamlığı + "özgün olmayan içerik" riski;
  son 45 günün en zayıfı daily-short/manim (medyan 67). Manim hattını haftada 3'e indirmeyi `deploy/crontab.txt` ile öner
  (Kaan görevi). Olay günü sonuç Short'u varsa o gün viral slotu atlansın (viral-daily.sh kapısı).
- [ ] R14 (Kaan kararı) — **Zam sezonu uzun video (5-8 dk)** · YouTube aramasında uzun video + açıklamada tıklanabilir site
  linki (Shorts'ta link yok). Kaan "önce Shorts" demişti; 35-54 yaş kitlesi + Ocak dalgası için 1 deneme öner.
- [ ] R15 (Kaan kararı) — **Gömülebilir hesaplayıcı / altın fiyatı widget'ı** · siteler ekledikçe kaynak linki = doğal
  backlink (baş sorgulardaki otorite kilidinin tek kalıcı çözümü). Kaan 10-15'te "dış link planı şimdilik yok" dedi.
- [ ] R16 (Kaan kararı) — **Açık veri sayfası** · CSV/JSON (TÜFE/kira oranı/altın-dolar getirisi/halka arz getirileri
  tarihçesi) — gazeteci/blogcu atıfı. R15 ile aynı karar.
- [ ] R18 (Kaan kararı) — **TikTok'a aynı dikey videolar** · her gün zaten 2-4 dikey video üretiyoruz; TikTok Türkiye'de
  YouTube Shorts'tan büyük kısa video kitlesi. Content Posting API: Kaan TikTok hesabı + geliştirici uygulaması açar,
  denetim (audit) onayına kadar videolar yalnız "özel" yüklenir. Onay gelirse ajan `scripts/tiktok-upload.py` yazar
  (facebook-reel.py kalıbı: izin yoksa sessiz atla). Ban riski: aynı videoyu birebir 3 platforma basmak serbest, spam değil.
- [ ] R20 (web/mobil · → week M1, 10-29) — **Mobil taşmaları düzelt** · tarayıcı testi (RC 10-28, 360 px): geniş tablolu bazı yazılar
  yatay taşıyor (ör. fed-faiz-karari-28-ekim-2026-beklentiler 495 px genişliğinde render oluyor); bülten formu 320 px'te
  7 px taşıyor. Ziyaretçinin %65'i mobil (GSC) ve Google mobil kullanılabilirliğe bakıyor. Tabloları `overflow-x:auto`
  sarmalayıcıya al (yazı şablonu/PostLayout düzeyinde, tek tek değil). Ayrıca WebApplication şeması URL'inde "hesaplama"
  geçen HER sayfaya basılıyor (araç merkezi /hesaplama-araclari/ ve ileride slug'ında 'hesaplama' geçen blog yazıları
  dahil) → yalnız gerçek hesaplayıcılara (tools.ts) daralt. Kabul: 360 px'te yatay kaydırma yok; şema yalnız araçlarda.
- [ ] R19 (bakım — TARİHLİ, 2027-01-21'den önce) — **Meta Graph API v21 → güncel sürüm** · v21.0 desteği 21 Ocak 2027'de
  bitiyor (sonra Meta çağrıları en eski açık sürüme yönlendirir — davranış değişebilir). `grep -rn "v21.0" scripts/` →
  instagram-*.py, post-*-instagram.py, facebook-*.py, metrics_instagram.py tek seferde güncel sürüme; birer --dry ile dene.
  Kabul: tüm Meta betikleri yeni sürümde, IG yayını + FB dry-run sorunsuz. (Facebook ayrıca: Meta bazı sayfalarda ayda 2
  organik link gönderisi sınırı test ediyor — FB link gönderileri reddedilirse linki yoruma taşı.)
- [ ] R21 (web — sosyal haklar kümesi 2. dalga) — **B261029-1 tutarsa kümeyi genişlet** · 11-12'de ilk 3 yeni sayfa
  (KYK, bedelli, borçlanma) gösterim alıyorsa sıradakiler: er maaşı (15,5 → /bedelli-askerlik-ucreti bölümü), 65 yaş aylığı
  (12,8 → /engelli-maasi bölümü zaten var; tools.ts `k`), yaşlılık/malullük aylığı, kreş/çocuk desteği, "emekli ikramiyesi"
  (memur) — her biri önce `agent/state/measure_topics.py` ile ölç (hacim ≥ 5). Kabul: ölçüm tablosu + en az 2 yeni sayfa.
- [ ] R22 (web/veri) — **Temettü takvimi veri sayfası** · "temettü hisseleri" 10,2 + "temettü veren hisseler" 7,3 (ölçüldü
  10-28 fırsat motoru). KAP'tan resmî temettü dağıtım tarihleri + hisse başı brüt/net tutar; tablo otomatik güncellenir
  (halka-arz-update kalıbı). Veri kaynağı KAP'tan güvenilir çekilemiyorsa AÇMA. Zirve Nisan-Mayıs (genel kurul sezonu) →
  Mart'ta hazır olmalı. Kabul: data/temettu-2027.json + /temettu-takvimi canlı.
- [ ] R17 (Kaan, 2 dk) — **Yandex Webmaster** · Türkiye'de ~%5 arama payı; IndexNow zaten Yandex'e de gidiyor, site
  doğrulaması Kaan'ın hesabıyla. Düşük öncelik.
