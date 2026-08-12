# ParaFOMO Büyüme Ajanı — Kalıcı Öğrenimler (biriken bilgi)

Kararlarını buna göre ver. Kanıtlanmış kazananı ikiye katla, kaybedeni tekrarlama.
Yeni ders: `python3 agent/exp.py learn --channel <k> --text "..."` veya deney kapatınca otomatik.

## Başlangıç öğrenimleri (proje geçmişinden — doğrulanmış)
- [2026-08-04][infra] Asıl darboğaz ÜRETİM değil; OTORİTE + DAĞITIM. Daha çok içerik üretmek ≠ büyüme. Enerjiyi duyurma/otorite/yeni-alan'a ver.
- [2026-08-04][youtube] 16.000+ Shorts izlenmesi siteye ~0 ziyaretçi getirdi → Shorts→site huni YAPISAL olarak zayıf. YouTube hedefi önce abone+izlenme büyütmek; site-huni ikincil.
- [2026-08-04][web] "Ekonomik takvim" sayfası (veri vardı, sayfa yoktu) hızlı kazanım oldu → veriyle beslenen, kendi başına trafik çeken HEDEF SAYFALAR yüksek kaldıraç.
- [2026-08-04][web] GSC'de yüksek gösterim + 0 tıklama + pozisyon 10-30 olan sorgu = en isabetli SEO fırsatı (hedefli sayfa/başlık/iç-link ile ilk sayfaya çek).
- [2026-08-04][infra] Dış veri kaynakları sessizce bozulabilir (Truncgil v4 fiyatları boşalttı → v3 + Yahoo). Kartlarda/verilerde boşluk görürsen kaynağı doğrula.
- [2026-08-06][infra] Truncgil v3 today.json artık DA bozuk (truncated JSON, retry sonrası bile crash ediyordu). bist-card.py FX/altını Yahoo'ya fallback yaptı (USDTRY=X, EURTRY=X, GC=F/31.1035*usdtry); Truncgil non-fatal. Ders: tek dış kaynağa fatal bağlanma, her fetch degrade edebilmeli.
- [2026-08-06][web] İç-link kümesi taktiği: head-term için pillar+satellite ayır, satelliti pillar'a head-anchor'la bağla (cannibalization çözümü), en yüksek learning-skorlu ilgili sayfadan pillar'a link ver (PageRank yoğunlaştırma). Fed kümesinde uygulandı (deney 2026-08-06-1).
- [2026-08-09][instagram] Tek-olay freshness hamlesi, zaten page-1'de (pos ~5) ama ÇOK DÜŞÜK hacimli (5 gös) bir sorguda ölçülebilir kazanç getirmedi: sorunun kendisi düşük-hacim; olay-günü patlaması bize ulaşmadı. Ders: düşük-hacimli tekil-olay sorgularına freshness yatırımı düşük kaldıraç — hacmi GSC'de kanıtlı (10+ gös) sorgulara odaklan.
- [2026-08-10][instagram] Head-term 'fed faiz kararı' page-1'i NEWS+TIMING sayfaları (Cumhuriyet/Habertürk/Bigpara 'ne zaman/saat kaçta/ne oldu') tutuyor; evergreen explainer'ı iç-link ile ilk sayfaya taşımak yetmiyor — darboğaz PageRank değil, arama-niyeti eşleşmesi. Timing-niyet için /fed-faiz-takvimi doğru silah; explainer 'nedir' slice'ına + sinonim sorgulara (abd faiz kararı) odaklanmalı.
- [2026-08-12][youtube] Tek seferlik freshness+iç-link nudge'ı page-2 'nedir' teriminde 5 günde pozisyon oynatmıyor (3. teyit: 08-05-1 NFP, 08-06-1 Fed, 08-07-2 endeks-fonu hepsi inconclusive/düz). On-page mikro-nudge DÜŞÜK kaldıraç; kanıtlı yüksek kaldıraç = YENİ hedef veri sayfası (ekonomik-takvim WIN). Mevcut sıralamayı itmek yerine havuzu yeni sayfayla büyütmeye devam.
