# Blog konu kuyruğu

`scripts/daily-content.sh` (Pzt-Cum 06:00 UTC) "Kuyruk" bölümündeki EN ÜSTTEKİ `- [ ]` satırı yazar ve
`- [x] ... → /blog/<slug> (tarih)` yapar. Kuyruğu ajan yönetir (haftalık koşu yeniden sıralar, günlük koşu
<3 kalınca doldurur). Satır biçimi: başlık önerisi · hedef sorgu (hacim) · neden şimdi · iç-link hedefi.
Sıra = planlanan yayın günü (haftalık koşu 2026-10-15): 15 → 16 → 19 → 20 → 21 → 22 → 23 Ekim.

**KURAL (2026-10-14):** her konunun hedef sorgusu Trends'te **hacim ≥ 5** olmalı ("mevduat faizi" = 100) ve
satırda `(hacim N)` yazmalı. Ölçüm: `agent/state/measure_topics.py` kalıbı ya da `opportunity_finder.py`
(önbellek `data/learning/`). Hacim < 5 → satır açılmaz.
**Ölçülüp İPTAL edilenler (10-15):** "bitcoin mi altın mı" 0,1 · "mevduat mı altın mı" 0 · "altın ne zaman
düşer" 1,5 · "hazine bonosu" 2,6 · "eurobond nedir" 2,4 → "X mi Y mi" karar sorguları Trends'te ölçülemez düzeyde.
**TCMB 22 Ekim:** yeni yazı AÇILMAZ — mevcut /blog/tcmb-ekim-2026-faiz-karari-ppk-beklentiler güncellenir (week.md T5).

## Kuyruk
- [ ] **Stopaj nedir? 2026'da mevduat, fon ve hisse kazancında stopaj oranları** · hedef: "stopaj oranı"
  (hacim 16), "stopaj nedir" (hacim 14) · neden: evergreen, sitede stopaj yazısı yok; oranları YALNIZ Resmî
  Gazete/GİB kaynağıyla yaz (mevduat stopajı 2025-2026'da birkaç kez değişti — en güncel CB kararını doğrula,
  emin olunmayan oranı yazma); tablo: araç → oran → kaynak/tarih · iç-link: /mevduat-faizi-hesaplama,
  /blog/vergi-avantajli-yatirim-araclari, /blog/yatirim-fonu-nedir-nasil-secilir
- [ ] **Kredi kartı asgari ödeme tutarı 2026: oran nasıl belirlenir, eksik ödersen ne olur?** · hedef: "kredi
  kartı asgari ödeme" (hacim 30, son 4 hafta 68 — yükseliyor) · neden: hacimli + sitede karşılığı yok; BDDK/TCMB
  asgari ödeme oranlarını (kart limitine göre) ve gecikme/akdi faiz azami oranlarını TCMB'nin güncel duyurusundan
  doğrula, tarih yaz; örnek hesap tablosu (20 bin / 50 bin borç) · iç-link: /blog/kredi-karti-borcundan-kurtulma,
  /kredi-hesaplama, /bilesik-faiz-hesaplama
- [ ] **Para piyasası fonu nedir? 2026'da getirisi, stopajı ve mevduatla farkı** · hedef: "para piyasası fonu"
  (hacim 35, son 4 hafta 48 — yükseliyor) · neden: faiz yüksekken mevduata alternatif arayan talep; getiri
  rakamı verirsen kaynak (TEFAS/fon raporu) + tarih göster, tek fon önerme, tavsiye değil · iç-link:
  /blog/yatirim-fonu-nedir-nasil-secilir, /mevduat-faizi-hesaplama, stopaj yazısı (yayındaysa)
- [ ] **Altın hesabı nedir, mantıklı mı? Altın hesabı, fiziki altın ve altın fonu karşılaştırması** · hedef:
  "altın hesabı" (hacim 38) · neden: altın kümesi en güçlü kümemiz; makas, vergi, saklama, banka riski tablosu;
  altin-fonu yazısıyla çakışmasın (o yazı FON, bu yazı HESAP) · iç-link: /altin-getiri, /altin-hesaplama,
  /blog/altin-fonu-nedir-gram-altindan-farki
- [ ] **Kredi yapılandırma 2026: kredi kartı ve kredi borcu nasıl yapılandırılır?** · hedef: "kredi yapılandırma"
  (hacim 50) · neden: hacimli, sitede yok; BDDK düzenlemesini (azami vade, faiz) YALNIZ resmi kaynaktan yaz;
  haber sitelerinde çelişen "yeni yapılandırma paketi" iddialarını yazma · iç-link: /kredi-hesaplama,
  /blog/kredi-karti-borcundan-kurtulma, asgari ödeme yazısı (yayındaysa)
- [ ] **Damga vergisi 2026: oranlar, maktu tutarlar ve 2027'de ne kadar artacak?** · hedef: "damga vergisi"
  (hacim 86) · neden: zam sezonu kümesi — maktu tutarlar her yıl yeniden değerleme oranıyla artar; 2026 oran/
  tutarlarını GİB'den doğrula, 2027 tahmini data/yeniden-degerleme.json'dan (tahmin olduğunu yaz) · iç-link:
  /yeniden-degerleme-orani, /blog/2027-zamlari-yeniden-degerleme-orani-rehberi, /vergi-dilimi-hesaplama
- [ ] **Findeks kredi notu nedir, nasıl yükselir? Not aralıkları ve kredi onayına etkisi** · hedef: "findeks
  kredi notu" (hacim 12,5) · neden: kredi kümesi (konut/ihtiyaç kredisi araçlarıyla birlikte); not aralıklarını
  KKB'nin kendi sayfasından al · iç-link: /kredi-hesaplama, /konut-kredisi-hesaplama (yayındaysa)

## Sonraki hafta adayları (haftalık koşu sıralar — hacmi ölç)
- Kasım 2026 kira artış oranı (TÜİK 3 Kasım) → yazı DEĞİL, /kira-artis-orani-hesaplama otomatik güncellenir.
- ÖTV (hacim 308) dev baş terim — yalnız uzun kuyruk varyantı ölçülürse ("araç ötv hesaplama"?).
- BES devlet katkısı (hacim 14, zirve Ocak) — mevcut bes yazısını güçlendir, yeni yazı açma.
- Repo nedir (7,8), tahvil nedir (6,5) — yazılar ZATEN var; yeni yazı açma.

## Yazılanlar
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
