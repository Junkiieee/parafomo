# Blog konu kuyruğu

`scripts/daily-content.sh` (Pzt-Cum 06:00 UTC) "Kuyruk" bölümündeki EN ÜSTTEKİ `- [ ]` satırı yazar ve
`- [x] ... → /blog/<slug> (tarih)` yapar. Kuyruğu ajan yönetir (haftalık koşu yeniden sıralar, günlük koşu
<3 kalınca doldurur). Satır biçimi: başlık önerisi · hedef sorgu · neden şimdi · iç-link hedefi.
Sıra = planlanan yayın günü (haftalık koşu 2026-10-08): 08 → 09 → 12 → 13 → 14 → 15 → 16 → 19 Ekim.

## Kuyruk
- [ ] **Gümüş mü altın mı? Son 10 yılda TL bazında hangisi kazandırdı** · hedef: "gümüş mü altın mı",
  "gümüş yatırımı mantıklı mı" · neden: B261006-2 getiri kümesi (T1 /gumus-getiri ile birlikte; 10-08) · iç-link:
  /gumus-getiri (yayındaysa), /altin-getiri, /altin-dolar-borsa
- [ ] **Euro mu dolar mı? TL bazında 10 yıllık getiri karşılaştırması** · hedef: "euro mu dolar mı
  2026" · neden: B261006-2 (T2 /euro-getiri ile; 10-09) · iç-link: /euro-getiri (yayındaysa), /dolar-getiri
- [ ] **ABD Ekim 2026 CPI verisi (Eylül enflasyonu): beklenti, Fed'e etkisi, dolar ve altın** · hedef:
  "abd enflasyon verisi ekim 2026", "cpi verisi ne zaman" · neden: CPI açıklaması Ekim ortası — yazmadan önce
  tarihi BLS takviminden/ekonomik takvimden doğrula ve metne kesin tarihi yaz (bilinmiyorsa "Ekim ortası"); 10-12'de
  yayın (olaydan 1-3 gün önce); 10 Eylül'deki "ABD Eylül 2026 CPI" yazısıyla çakışmasın diye "Ekim" adlandırması;
  makro açıklayıcılar en iyi blog sayfalarımız · iç-link: /ekonomik-takvim, /fed-faiz-takvimi, /altin-getiri
- [ ] **Halka arza katılmak kazandırıyor mu? 2026 halka arzlarının ilk gün, 1 ay ve bugünkü getirisi** · hedef:
  "halka arz kazandırır mı", "halka arza katılmak mantıklı mı", "2026 halka arz getirileri" · neden: B261006-1
  kümesine veri-temelli karar yazısı; `data/halka-arz-getiri.json`'daki GERÇEK rakamlarla (2026 ort. getiri,
  en iyi/en kötü 3 arz, kişi başı lot örneği); 10-13 · iç-link: /halka-arz-getiri, /halka-arz, en az 5
  `/halka-arz/<slug>` şirket sayfası, /blog/halka-arza-nasil-katilinir-esit-dagitim-lot-hesabi
- [ ] **Bitcoin mi altın mı? TL bazında 1, 3 ve 5 yıllık getiri ve en büyük düşüşler** · hedef: "bitcoin mi
  altın mı", "bitcoin mi altın mı daha mantıklı" · neden: B261006-2 (T3 /bitcoin-getiri ile; 10-14); karar niyeti
  · iç-link: /bitcoin-getiri (yayındaysa), /altin-getiri, /blog/bitcoin-nedir-nasil-alinir
- [ ] **100 bin TL mevduatta mı, altında mı, dolarda mı? Son 1-5 yılda gerçekte ne kazandırdı** · hedef:
  "mevduat mı altın mı", "parayı nerede değerlendirmeli 2026" · neden: karar niyeti + kendi getiri verimiz
  (altin/dolar/bist-getiri.json; mevduat için TCMB ortalama mevduat faizi — kaynak göster, yaklaşık de);
  10-15 · iç-link: /mevduat-faizi-hesaplama, /altin-dolar-borsa, /altin-getiri, /dolar-getiri
- [ ] **Stopaj nedir? 2026'da mevduat, fon ve hisse kazancında stopaj oranları** · hedef: "stopaj nedir",
  "mevduat stopaj oranı 2026", "fon stopajı" · neden: evergreen yüksek talep, sitede stopaj yazısı yok; oranları
  YALNIZ Resmî Gazete/GİB kaynağıyla yaz, emin olunmayan oranı yazma; 10-16 · iç-link: /mevduat-faizi-hesaplama,
  /blog/vergi-avantajli-yatirim-araclari, /blog/yatirim-fonu-nedir-nasil-secilir
- [ ] **TCMB 22 Ekim PPK öncesi son durum: piyasa beklentisi ve senaryolar** · hedef: "tcmb faiz kararı
  22 ekim beklenti" · neden: karar 22 Ekim — 19-21 Ekim'de yayın; 30 Eylül yazısı (tcmb-ekim-2026, 28g 5 tık)
  sıralanıyor → YENİ yazı yerine o yazıyı güncellemek daha güvenli olabilir (cannibalization): yazmadan önce
  karar ver, yeni yazıysa başlık "son durum/son anket" odaklı olsun ve eski yazıya link versin · iç-link:
  /tcmb-faiz-takvimi, /mevduat-faizi-hesaplama, /blog/tcmb-ekim-2026-faiz-karari-ppk-beklentiler

## Sonraki hafta adayları (haftalık koşu sıralar)
- Fed 28 Ekim FOMC önizlemesi (26-27 Ekim) · Kasım 2026 kira artış oranı tahmini (TÜİK 3 Kasım; 30 Ekim-2 Kasım)
  · TÜİK Ekim enflasyonu önizlemesi (31 Ekim-2 Kasım).

## Yazılanlar
- [x] **Halka arza nasıl katılınır? Eşit dağıtım, oransal dağıtım ve lot hesabı (2026 rehberi)** · hedef:
  "halka arza nasıl katılınır", "halka arz eşit dağıtım nedir" · neden: B261006-1 halka arz kümesinin
  rehber sayfası, şirket sayfaları buna bağlanacak · iç-link: /halka-arz, /halka-arz-getiri, ALBTN yazısı → /blog/halka-arza-nasil-katilinir-esit-dagitim-lot-hesabi (2026-10-07)
