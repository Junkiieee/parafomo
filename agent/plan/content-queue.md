# Blog konu kuyruğu

`scripts/daily-content.sh` (Pzt-Cum 06:00 UTC) "Kuyruk" bölümündeki EN ÜSTTEKİ `- [ ]` satırı yazar ve
`- [x] ... → /blog/<slug> (tarih)` yapar. Kuyruğu ajan yönetir (haftalık koşu yeniden sıralar, günlük koşu
<3 kalınca doldurur). Satır biçimi: başlık önerisi · hedef sorgu (hacim) · neden şimdi · iç-link hedefi.
Sıra = planlanan yayın günü (haftalık koşu 2026-10-22): 22 → 23 → 26 → 27 → 28 → 29 → 30 Ekim → 2 Kasım.
**Tarihli satır** (📅) o gün yayınlanmalı: günlük koşu (03:00 UTC) sıranın kaydığını görürse o satırı EN ÜSTE taşır.

**KURAL (2026-10-14):** her konunun hedef sorgusu Trends'te **hacim ≥ 5** olmalı ("mevduat faizi" = 100) ve
satırda `(hacim N)` yazmalı. Ölçüm: `agent/state/measure_topics.py` (QS listesini değiştir) ya da `opportunity_finder.py`
(önbellek `data/learning/`). Hacim < 5 → satır açılmaz. **İstisna (10-22):** izinli olay ailesi (TCMB, Fed, TÜİK TÜFE,
ABD CPI, ABD NFP) önizlemeleri — GSC'de tık getirdiği kanıtlı (28g 31 tık). JOLTS/PCE/ISM/GDP hayır.
**Ölçülüp İPTAL edilenler:** "bitcoin mi altın mı" 0,1 · "mevduat mı altın mı" 0 · "altın ne zaman düşer" 1,5 ·
"hazine bonosu" 2,6 · "eurobond nedir" 2,4 · "geçici vergi hesaplama" 0,7 · "gss primi 2026" 0,5 · "kira geliri
beyannamesi" 2,8 (zirve Mart 32 → Şubat'ta yeniden ölç) · "aile destek programı" 1,5.

## Kuyruk
- [x] **Findeks kredi notu nedir, nasıl yükselir? Not aralıkları ve kredi onayına etkisi** · hedef: "findeks
  kredi notu" (hacim 12,5) + "findeks" (124) · neden: kredi kümesi (konut/ihtiyaç/taşıt kredisi araçlarıyla); not
  aralıklarını KKB'nin kendi sayfasından al · iç-link: /kredi-hesaplama, /konut-kredisi-hesaplama, /ihtiyac-kredisi-hesaplama → /blog/findeks-kredi-notu-nedir-nasil-yukselir (2026-10-22)
- [x] **TEFAS nedir, fon nasıl alınır? 2026'da TEFAS'tan yatırım fonu alma rehberi** · hedef: "tefas" (hacim 160,
  zirve 409 Eylül) + "fon getirileri" (14) · neden: hacimli, sitede karşılığı yok (keyword-map K14); adım adım alım
  (banka/aracı kurum), valör/saat kuralları, stopaj (stopaj yazısına link), fon türleri tablosu; getiri rakamı
  verirsen TEFAS'tan tarihli; tek fon önerme · iç-link: /blog/yatirim-fonu-nedir-nasil-secilir,
  /blog/stopaj-nedir-2026-stopaj-oranlari, /blog/para-piyasasi-fonu-nedir-getirisi-stopaj-mevduat-farki, /mevduat-faizi-hesaplama → /blog/tefas-nedir-fon-nasil-alinir (2026-10-23)
- [x] 📅 26 Ekim **Fed Faiz Kararı 28 Ekim 2026: Beklenti, Senaryolar ve Dolar/Altın Etkisi** · slug:
  `fed-faiz-karari-28-ekim-2026-beklentiler` · hedef: "fed faiz kararı" (hacim 80,9, zirve 656 Eylül) · frontmatter:
  `sonuc: "fed:2026-10-28"` + `sonucBaslik: "Fed 28 Ekim Kararı Açıklandı: Faiz {karar}, Bant %{bant}"`
  (Fed yer tutucuları: bant, bp, karar — `src/data/event-result.ts`) · Mevcut faiz aralığı ve 16 Eylül kararı `data/fomc-2026.json`'dan; piyasa
  beklentisi YALNIZ CME FedWatch / Reuters anketi, tarihli; karar saati TSİ 21:00 · iç-link: /fed-faiz-takvimi,
  /blog/fed-faiz-karari-ne-olur-beklentiler, /blog/fed-faiz-karari-sonrasi-piyasa-tepkisi, /dolar-getiri, /altin-getiri → /blog/fed-faiz-karari-28-ekim-2026-beklentiler (2026-10-26)
- [x] **Geçici vergi nedir? 2026 geçici vergi dönemleri, oranı ve beyan tarihleri** · hedef: "geçici vergi" (hacim
  46,1, zirve Şubat 161) · neden: 3. dönem (Temmuz-Eylül) beyanı Kasım'da — son günü GİB'den doğrula (dönemi izleyen 2.
  ayın 17'si kuralı); oranlar KV %25 / GV tarifesi; mahsup ve iade; 2026'da kaldırılma/değişiklik haberi varsa YALNIZ
  RG/GİB'le · iç-link: /kurumlar-vergisi-hesaplama, /gelir-vergisi-hesaplama, /vergi-dilimi-hesaplama → /blog/gecici-vergi-nedir-2026-donemleri-orani-beyan-tarihleri (2026-10-27)
- [ ] **SGK hizmet dökümü nasıl alınır ve nasıl okunur? e-Devlet adım adım (2026)** · hedef: "sgk hizmet dökümü"
  (hacim 30,1) · neden: hacimli how-to, sitede yok; belge sütunlarının anlamı (prim günü, işyeri, eksik gün kodları —
  kodları SGK'nın resmi listesinden), barkodlu belge, emeklilik için ne işe yarar. /emeklilik-hesaplama (week T18) canlıysa
  oraya bağla, hesaplamayı yazıda TEKRARLAMA · iç-link: /emeklilik-hesaplama (yayındaysa), /bagkur-primi-hesaplama,
  /en-dusuk-emekli-maasi
- [ ] **Ek gösterge nedir? 2026 memur ek gösterge tablosu, 3600 ek gösterge ve maaşa etkisi** · hedef: "ek gösterge"
  (hacim 43,7) · neden: memur kümesi (/memur-zammi-hesaplama) — 657 DMK ek gösterge cetveli ve 3600 ek gösterge
  düzenlemesini (7417 s.K.) mevzuat.gov.tr'den; tutar örneği verirsen güncel katsayıyla (`data/emekli-memur.json`) ·
  iç-link: /memur-zammi-hesaplama, /en-dusuk-emekli-maasi, /emekli-zammi-hesaplama
- [ ] **Katılım hesabı nedir? Kâr payı nasıl hesaplanır, mevduattan farkı ve stopajı** · hedef: "katılım hesabı"
  (hacim 6,9) · neden: mevduat kümesi tamamlayıcı; kâr payı oranı örneği verirsen bankanın kendi sayfasından tarihli,
  TKBB/BDDK kaynaklı; tek banka önerme · iç-link: /mevduat-faizi-hesaplama, /blog/stopaj-nedir-2026-stopaj-oranlari,
  /blog/para-piyasasi-fonu-nedir-getirisi-stopaj-mevduat-farki
- [ ] 📅 30 Ekim **Ekim 2026 Enflasyonu 3 Kasım'da Açıklanıyor: Beklenti, Kira Artışı, Emekli Zammı ve 2027 Zamlarına
  Etkisi** · slug: `ekim-2026-enflasyon-beklentisi-3-kasim` · hedef: "enflasyon beklentisi" (hacim 45,6) + "ekim ayı
  enflasyon" (6,9, zirve Kasım 143) + "enflasyon ne zaman" (22,5) · frontmatter `sonuc: "tufe:2026-10"` +
  `sonucBaslik: "Ekim 2026 Enflasyonu Açıklandı: Aylık %{aylik}, Yıllık %{yillik}"`. Beklenti rakamı YALNIZ TCMB
  Piyasa Katılımcıları Anketi / AA Finans anketinden, tarihli. 3 Kasım "büyük gün" merkezi: /kira-artis-orani-hesaplama,
  /emekli-zammi-hesaplama, /memur-zammi-hesaplama, /yeniden-degerleme-orani, /mtv-hesaplama,
  /blog/2027-zamlari-yeniden-degerleme-orani-rehberi, /enflasyon-hesaplama linkleri. **Erken yayın (RC 2026-10-27):** "ekim ayı enflasyon
  beklentisi" aramaları şimdiden geliyor (GSC p13,8, yanlış yazıya); Google'ın dizine alması için olaydan ≥3 gün önce.
  AA Finans anketi sonradan çıkarsa 2 Kasım günlük koşusu yazıdaki beklenti rakamını güncellesin.

## Sonraki hafta adayları
- 📅 ABD NFP (Ekim verisi) ve ABD CPI (Ekim verisi) önizlemeleri — tarihleri BLS takviminden; olaydan 1-2 gün önce.
- Kredi kartı faiz hesaplama → yazı DEĞİL, araç (week T20).
- Emekli promosyonu → yazı DEĞİL, veri sayfası (week T17). Emeklilik yaşı → araç (week T18).
- Çocuk parası (27,5) → /dogum-yardimi kapsıyor; yazı açma (tools.ts'e anahtar kelime).
- (10-18) "Damga vergisi 2026" → kanonik /damga-vergisi-hesaplama/. Aynı sorguya yazı açma.
- Kasım 2026 kira artış oranı (TÜİK 3 Kasım) → yazı DEĞİL, /kira-artis-orani-hesaplama otomatik güncellenir.
- ÖTV (hacim 308) dev baş terim — "ötv hesaplama" 9,2 (zirve Aralık) → araç adayı (Kasım sonu).
- BES devlet katkısı (hacim 14, zirve Ocak) — mevcut bes yazısını güçlendir, yeni yazı açma.
- Beyanname (246) + kira geliri beyanı — Şubat sezonu; Ocak'ta ölç ve yaz.

## Yazılanlar
- [x] **Para piyasası fonu nedir? 2026'da getirisi, stopajı ve mevduatla farkı** · hedef: "para piyasası fonu"
  (hacim 35, son 4 hafta 48 — yükseliyor) · neden: faiz yüksekken mevduata alternatif arayan talep; getiri
  rakamı verirsen kaynak (TEFAS/fon raporu) + tarih göster, tek fon önerme, tavsiye değil · iç-link:
  /blog/yatirim-fonu-nedir-nasil-secilir, /mevduat-faizi-hesaplama, stopaj yazısı (yayındaysa) → /blog/para-piyasasi-fonu-nedir-getirisi-stopaj-mevduat-farki (2026-10-19)
- [x] **Altın hesabı nedir, mantıklı mı? Altın hesabı, fiziki altın ve altın fonu karşılaştırması** · hedef:
  "altın hesabı" (hacim 38) · neden: altın kümesi en güçlü kümemiz; makas, vergi, saklama, banka riski tablosu;
  altin-fonu yazısıyla çakışmasın (o yazı FON, bu yazı HESAP) · iç-link: /altin-getiri, /altin-hesaplama,
  /blog/altin-fonu-nedir-gram-altindan-farki → /blog/altin-hesabi-nedir-mantikli-mi-fiziki-altin-fon-karsilastirma (2026-10-20)
- [x] **Kredi yapılandırma 2026: kredi kartı ve kredi borcu nasıl yapılandırılır?** · hedef: "kredi yapılandırma"
  (hacim 50) · neden: hacimli, sitede yok; BDDK düzenlemesini (azami vade, faiz) YALNIZ resmi kaynaktan yaz;
  haber sitelerinde çelişen "yeni yapılandırma paketi" iddialarını yazma · iç-link: /kredi-hesaplama,
  /blog/kredi-karti-borcundan-kurtulma, asgari ödeme yazısı (yayındaysa) → /blog/kredi-yapilandirma-2026-kredi-karti-borcu-nasil-yapilandirilir (2026-10-21)
- [x] **Kredi kartı asgari ödeme tutarı 2026: oran nasıl belirlenir, eksik ödersen ne olur?** · hedef: "kredi
  kartı asgari ödeme" (hacim 30, son 4 hafta 68 — yükseliyor) · neden: hacimli + sitede karşılığı yok; BDDK/TCMB
  asgari ödeme oranlarını (kart limitine göre) ve gecikme/akdi faiz azami oranlarını TCMB'nin güncel duyurusundan
  doğrula, tarih yaz; örnek hesap tablosu (20 bin / 50 bin borç) · iç-link: /blog/kredi-karti-borcundan-kurtulma,
  /kredi-hesaplama, /bilesik-faiz-hesaplama → /blog/kredi-karti-asgari-odeme-tutari-2026 (2026-10-16)
- [x] **Stopaj nedir? 2026'da mevduat, fon ve hisse kazancında stopaj oranları** · hedef: "stopaj oranı"
  (hacim 16), "stopaj nedir" (hacim 14) · neden: evergreen, sitede stopaj yazısı yok; oranları YALNIZ Resmî
  Gazete/GİB kaynağıyla yaz (mevduat stopajı 2025-2026'da birkaç kez değişti — en güncel CB kararını doğrula,
  emin olunmayan oranı yazma); tablo: araç → oran → kaynak/tarih · iç-link: /mevduat-faizi-hesaplama,
  /blog/vergi-avantajli-yatirim-araclari, /blog/yatirim-fonu-nedir-nasil-secilir → /blog/stopaj-nedir-2026-stopaj-oranlari (2026-10-15)
- [x] **Halka arza katılmak kazandırıyor mu? 2026 halka arzlarının ilk gün, 1 ay ve bugünkü getirisi** · hedef:
  "halka arz kazandırır mı", "halka arza katılmak mantıklı mı", "2026 halka arz getirileri" · neden: B261006-1
  kümesine veri-temelli karar yazısı; `data/halka-arz-getiri.json`'daki GERÇEK rakamlarla (2026 ort. getiri,
  en iyi/en kötü 3 arz, kişi başı lot örneği); 10-13 · iç-link: /halka-arz-getiri, /halka-arz, en az 5
  `/halka-arz/<slug>` şirket sayfası, /blog/halka-arza-nasil-katilinir-esit-dagitim-lot-hesabi → /blog/halka-arz-kazandirir-mi-2026-halka-arz-getirileri (2026-10-14)
- [x] **2027'de neler zamlanacak? Yeniden değerleme oranı rehberi: MTV, harçlar, cezalar, vergi dilimleri** ·
  hedef: "2027 zamları", "yeniden değerleme oranı 2027", "2027de neler zamlanacak" · neden: RC 10-10'da
  /yeniden-degerleme-orani + /mtv-hesaplama canlıya alındı (Eylül Yİ-ÜFE ile tahmin %27,8) — bu yazı kümenin
  blog girişi, Kasım-Ocak zam sezonuna 3-6 hafta önce pozisyon; rakamları SAYFADAKİ veriden al, uydurma ·
  iç-link: /yeniden-degerleme-orani, /mtv-hesaplama, /emekli-zammi-hesaplama, /asgari-ucret-hesaplama → /blog/2027-zamlari-yeniden-degerleme-orani-rehberi (2026-10-13)
- [x] **ABD Ekim 2026 CPI verisi (Eylül enflasyonu): beklenti, Fed'e etkisi, dolar ve altın** · hedef:
  "abd enflasyon verisi ekim 2026", "cpi verisi ne zaman" · neden: CPI açıklaması Ekim ortası — yazmadan önce
  tarihi BLS takviminden/ekonomik takvimden doğrula ve metne kesin tarihi yaz (bilinmiyorsa "Ekim ortası"); 10-12'de
  yayın (olaydan 1-3 gün önce); 10 Eylül'deki "ABD Eylül 2026 CPI" yazısıyla çakışmasın diye "Ekim" adlandırması;
  makro açıklayıcılar en iyi blog sayfalarımız · iç-link: /ekonomik-takvim, /fed-faiz-takvimi, /altin-getiri → /blog/abd-ekim-2026-cpi-verisi-fed-dolar-altin (2026-10-12)
- [x] **Euro mu dolar mı? TL bazında 10 yıllık getiri karşılaştırması** · hedef: "euro mu dolar mı
  2026" · neden: B261006-2 (T2 /euro-getiri ile; 10-09) · iç-link: /euro-getiri (yayındaysa), /dolar-getiri → /blog/euro-mi-dolar-mi-10-yillik-getiri-karsilastirma (2026-10-09)
- [x] **Gümüş mü altın mı? Son 10 yılda TL bazında hangisi kazandırdı** · hedef: "gümüş mü altın mı",
  "gümüş yatırımı mantıklı mı" · neden: B261006-2 getiri kümesi (T1 /gumus-getiri ile birlikte; 10-08) · iç-link:
  /gumus-getiri (yayındaysa), /altin-getiri, /altin-dolar-borsa → /blog/gumus-mi-altin-mi-10-yillik-getiri-karsilastirma (2026-10-08)
- [x] **Halka arza nasıl katılınır? Eşit dağıtım, oransal dağıtım ve lot hesabı (2026 rehberi)** · hedef:
  "halka arza nasıl katılınır", "halka arz eşit dağıtım nedir" · neden: B261006-1 halka arz kümesinin
  rehber sayfası, şirket sayfaları buna bağlanacak · iç-link: /halka-arz, /halka-arz-getiri, ALBTN yazısı → /blog/halka-arza-nasil-katilinir-esit-dagitim-lot-hesabi (2026-10-07)
