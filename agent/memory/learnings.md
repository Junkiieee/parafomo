# ParaFOMO — Kalıcı dersler (düzenlenmiş)

_v1'in 59 deneyi + 2,5 aylık KPI'ından damıtıldı; son yeniden yazım: haftalık koşu 2026-10-29.
≤40 madde, tekrar yok, kanıtıyla. Ham geçmiş: agent/archive/v1/memory/._

## Kanıtlı çalışan
- **Yeni arama niyeti açan veri/araç sayfaları tek kanıtlı web kaldıracı.** 08-11→09-02 takvim + getiri sayfaları
  sonrası GSC tık ~4 → ~40/hafta, gerçek erişim ~3 → ~45-80/hafta (W43: 81). Tekil sayfa etkisi ölçülemez; toplu motor olarak izle. Sorgunun SAYISAL cevabı başlıkta ve ilk ekranda + tarih.
- **Sosyal ödeme / SGK hak sayfaları finans araçlarından çok daha iyi sıralanıyor (10-29):** 10-19'da açılan /dogum-yardimi
  p8,4 (4 tık/7g), /evde-bakim-maasi p15,6 (4), /engelli-maasi p22 (2) — araç/veri sayfalarının 20 tıkının yarısı; aynı
  hafta açılan finans araçları (taşıt kredisi p85, kredi kartı faiz p81, tapu p69) tık almadı. Tutar resmî formülden
  (gösterge × katsayı, 5510 oranları) hesaplanır, rakip zayıf. Bahis B261029-1.
- **Olay önizleme/sonuç yazıları en verimli blog türü:** 28g 31 tık / 463 gös (abd-issizlik 10, abd-ekim-cpi 7,
  tcmb-ekim 5, nfp 3). Olaydan 1-3 gün önce yayınla; `sonuc:` frontmatter'ı ile kutu otomatik gelir (Fed 28 Ekim
  kutusu 19:25 UTC'de kendiliğinden geldi). Bahis B261022-1.
- **Trends ≈0 ≠ tık yok:** ABD CPI/NFP önizlemeleri Trends'te ölçülemez ama GSC'de tık alıyor. İzinli olay ailesi: TCMB,
  Fed, TÜİK TÜFE, ABD CPI, ABD NFP. JOLTS/PCE/ISM/GDP hayır (pce-gdp yazıları 28g 2 tık).
- **"Gelecek yıl" ve uzun-kuyrukta yeni sayfalar ilk haftada p4-11:** 2027 bayram ikramiyesi p6-9, 2027 bakıcı maaşı p10,
  2027 yeniden değerleme tahmini p10-11, 2027 trafik cezaları p10, 10 yıllık pasaport 2027 p6, /blog/2027-zamlari p7.
- **Yeni sayfalar 1-6 günde indeksleniyor** (sitemap gönderimi learn-daily + IndexNow + tools.ts iç linkleri); indeks darboğaz değil.
- **Google tıklarının ~%95'i gizli uzun-kuyruk sorgulardan** (28g 137 tıkta %95,3). GSC sorgu tablosu tıkları açıklamaz →
  sayfa bazında ölç (`agent/state/gsc_wow.py`: sayfa türü + hafta/hafta).
- **Talep olaya bağlı ve dalgalı:** /altin-getiri W38 21 tık → W39-41 3-5 tık, sıra sabit p6-8. Tık düşüşünü sıralama
  kaybı sanma — önce gösterim+sıraya bak.
- **AI asistanlar gerçek trafiğin ~%7-8'i** (28g 17-21) — net tablo + kaynak + tarih alıntılanıyor.
- **Emekli/memur zammı tek kanonik sayfa** (/emekli-zammi-hesaplama, /memur-zammi-hesaplama) — yeni blog yazısı AÇMA.
  Talep Ocak/Temmuz'a yığılı: emekli maaşı 2027 zirve 852, asgari ücret 2027 zirve 3.155 (Aralık), emekli zammı vekil 998.
- **Halka arz şirket sayfaları küçük ama kalıcı uzun-kuyruk verir** (B261006-1 lost, 10-29): 7g ~4-8 tık / ~195 gös,
  p4-8, iki haftadır düz; hacim yeni arza bağlı, ölçeklenmiyor. Otomatik kalsın, ek emek koyma.

## Kanıtlı çalışmayan (tekrar deneme)
- **Baş sorgular otorite kilidinde, başlık sorunu değil:** eski ve yeni araçlar p60-99 (kira artış p95, kıdem p95, konut
  kredisi p95, taşıt kredisi p85, emlak vergisi p75-81, altın alt sayfaları p83-97) — başlık/H1 sorguyu zaten içeriyor.
  On-page dürtme yapma; 2027/uzun kuyruk/sosyal hak açısıyla gir. OTORITE çıkan kelimeye yeni sayfa açma.
- **Gösterim artışı ≠ trafik:** W43 GSC gösterimi 2x (2.130 → 4.196) ama tık 43 → 40; artış p80+ sıralardan. Başarıyı tıkla ölç.
- **Getiri sayfası türü tek başına talep yaratmıyor (B261006-2 lost):** gümüş/euro/bitcoin getiri 28g toplam 3 tık. Yeni getiri sayfası açma.
- **Hacmi ölçülmemiş konuya yazı:** "dolar mı altın mı", "X mi Y mi", bono hesaplama, geçici vergi hesaplama 0,7, gss primi
  2026 0,5, aile destek programı 1,5, kömür yardımı 0,8. Kural: hacim ≥ 5 (istisna: izinli olay ailesi).
- **Mevcut sayfayı on-page dürtmek** (iç-link, sinonim, FAQ, tazelik, exact-match yeni yazı) 5-7 günde pozisyon oynatmadı — 6+ teyit.
- **Canlı değer/fiyat sorguları** (altın fiyat alt sayfaları p83-97, dolar endeksi p76) yüzey açmadı.
- **Video üretim-kalitesi reformu izlenmeyi kaldırmadı (B261006-4 lost)** ve **video mikro-düzenlemeleri** (fade, açılış,
  micro-cut, kanca, SFX — 11 deneme) ölçülebilir fark yaratmadı. Video izlenmesine bahis hedefi koyma.
- **Vekil metrikle format seçmek** (09-30 "65% AVD kapısı" → backtest ×2): sonuç metriğinde en zayıf çıktı.
- **Elle paylaşım gerektiren dağıtım** (26+ Reddit/Ekşi taslağı paylaşılmadı) · **IG caption/hashtag denemeleri**
  (insights izni yok) · **Shorts→site hunisi** ~0.
- **Trafiksiz ürün cilası:** portföy 5 üye — UX iyileştirmesi kayıt getirmez; ürün işi bakım düzeyinde.
- **Kuyrukta yalnız tarihli görev bırakmak:** 10-22 planının 4 tarihsiz görevi 10-23'te bitti → 10-26→10-28 koşuları 3-10 dk
  boş geçti. Haftalık planda ≥8 tarihsiz görev + roadmap.md yedeği.

## YouTube
- **Aranan konunun blog→Short'u bu hafta en iyisi (10-29, n=2):** Fed önizleme 1.159, geçici vergi 1.019 izlenme; aynı
  hafta viral formatlar 11-192. İzlenmenin %19-21'i YouTube aramasından; kitle %68 35-54 yaş. Abone 53 → 60 (+7/7g, en iyi
  hafta), 1000 izlenme başına abone 0,69 → 0,8. Başlık = aranan kalıp (R3) testi sürüyor.
- **Aynı gün aynı küme yamyamlığı:** biri akışı alıyor, diğeri 0-16 izlenme (V2 10-15: dolar 5000 ×2 → 13 vs 554; 10-28 Fed
  sonuç Short'u günü viral Fed videosu 11). Olay günü viral slotu atlanmalı (V4).
- 343 video → 60 abone. YPP uzak; günde ~3 şablon video "özgün olmayan içerik" riskini taşır → hacim artırma.
- Kazanan temalar: altın + kayıp korkusu (altın takı ayarı 936), gizli kesinti rakamı. Shock rakamı her zaman kaynaklı olmalı.

## Kısıtlar ve çevre
- **Hukuki rakamı birincil kaynaktan doğrula** (mevzuat.gov.tr güncel metni, RG, GİB, TCMB, TÜİK, SGK, ASHB; PDF'i pypdf
  ile oku). Haber siteleri eski bilgiyi tekrarlıyor: trafik cezası indirimi 1 AY (KK 17/6), gecikme zammı %3,7
  (13.11.2025), emlak vergisi değeri 2027'de YD'nin TAMAMI kadar artar (7566 s.K.).
- **2026 artış oranları:** harç/MTV/damga CB kararıyla %18,95; muayene, tapu döner sermaye, veraset istisnası tam YD
  %25,49; noter tarifesi YD'ye bağlı değil. Evde bakım = 10.000 gösterge × memur katsayısı; engelli/65 yaş = K cetveli
  göstergesi × katsayı + %5.
- **Veri sessizce bayatlar:** elle girilen her veri otomatik güncelleyici ya da health.py tazelik satırı ister (kampanya
  bitişleri dahil: emekli promosyonu 31 Ekim). app.parafomo.com veri kopyaları deploy-app.sh ile gider.
- **Fırsat motoru eşlemesi yanıltabilir:** sitede karşılığı olan sorgular YENI_* çıkıyor (brüt asgari ücret, kıdem tavanı,
  mevduat faiz oranları), "borsa istanbul/bist 100/evet" yanlış sayfaya bağlanıyor → `SYNONYMS` + hariç listesi (S1).
  §9c ilk 15 satırı iki haftadır OTORITE/gürültü: yeni konu = Trends'le yeni ölçüm (`agent/state/measure_topics.py`).
- **Canlı blog yazıları** (`# OTOMATİK ÜRETİLİR`) şablondan düzenlenir (`content-templates/blog/*.j2` + live-posts.py).
- **Kanonik URL:** iç linkler '/' ile; worker/index.js 301'leri ve REDIRECTS haritası kalır.
- **Olay yazılarında tarih hatası riski** (Fed "4-5 Kasım" → 27-28 Ekim; TCMB faizi ~%22-25 diyordu, gerçek %37). Tarih/oranı
  resmi kaynaktan (TCMB/Fed/BLS/TÜİK takvimi, data/*.json) al. Slug'da ay adı = YAYIN ayı (abd-ekim-2026-nfp = Eylül verisi).
- **Hız:** darboğaz fontlardı (kendi sunucu + optional; 10-13). Yeni harici font/3. taraf script ekleme.
- **Headless izin listesi:** `for`/`until`, `x=$(...)`, `awk`, heredoc, `cd X && …`, repo dışı yol, `;` ile zincirlenmiş
  `python3 -c` + `sed` reddedilir. Çok adımlı işi `agent/state/*.py` ya da tek `python3 -c` ile yap; dosya düzenlemesi Edit ile.
- **Astro derleyici tuzağı:** frontmatter'da iç içe template literal'den SONRA gelen ASCII apostrof build'i bozar →
  Türkçe ekleri ’ (U+2019) ile yaz. Teşhis: `node agent/state/astro_check.mjs <dosya>`.
- **Ölçüm araçları:** Trends `agent/state/measure_topics.py` (QS listesi; 429 → tekrar) · GSC küme
  `agent/state/gsc_pattern.py '<regex>'` · hafta/hafta sayfa türü `agent/state/gsc_wow.py`. GSC ~2-3 gün gecikmeli.
- **Claude kotası:** Max 5x; haftalık kota Çarşamba 22:00 UTC sıfırlanır. daily-content ajanla aynı anda çalışmaz —
  haftalık koşu 06:00 UTC'den önce bitmeli.
- Dış veri kaynakları sessizce bozulur (Truncgil, Investing 403, Yahoo 429) → her fetch degrade edebilmeli. EVDS anahtarı VAR.
- **Dağıtım kanalları zayıf:** Telegram 2, bülten 1 onaylı abone, YouTube 60, IG 21 takipçi / 469 gönderi, Facebook
  sayfası 0 (GA4'te facebook.com'dan 28g 46 ziyaretçi; FB yayını Meta izni bekliyor). Geri dönen 28g 14 / 418.
- **Video render tek seferde bir tane** (RC 10-28): tüm hatlar /tmp/shorts_frames kullanır; shorts-build-v4.py kilitli.
