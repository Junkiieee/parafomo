# İçerik Kalite Playbook'u

Her makale bu standartları karşılamalı. Amaç: Google'da sıralanan **ve** okuyucuya gerçek değer katan içerik. Yapay/şişirilmiş metin üretme — Google bunu cezalandırır (Helpful Content).

## Altın kural
> Her yazı, hedef arama sorgusunu soran kişinin sorusunu **tam ve net** cevaplamalı. Okuyan kişi "tamam, anladım, işime yaradı" demeli.

## Yapısal standartlar
- **Uzunluk:** 900–1.600 kelime (konunun derinliğine göre).
- **Başlık (title):** Arama sorgusunu içersin, 60 karakteri geçmesin, merak uyandırsın.
- **Description:** 150–160 karakter, anahtar kelimeli, tıklatan.
- **Giriş:** İlk 2 cümlede sorunu/soruyu netleştir, çözüm vaadi ver. Klişe giriş yok.
- **H2/H3 hiyerarşisi:** Taranabilir, mantıklı bölümler. En az 4-6 H2.
- **Tablo:** Mümkünse bir karşılaştırma tablosu (Google öne çıkarır, snippet alır).
- **Listeler:** Adım adım / madde madde aksiyon.
- **Özet bölümü:** Sonda "Özet" başlığı + 3-4 maddelik çıkarım.
- **SSS (FAQ):** Frontmatter'daki `faq` alanına 3-5 soru-cevap ekle (hedef kelimeyle ilgili gerçek sorular). Site bunu otomatik görünür SSS bölümü + Google FAQPage yapısal verisi olarak basar → arama sonuçlarında açılır kutu şansı. Cevaplar 1-3 cümle, net.
- **Yasal not:** Sonda "yatırım tavsiyesi değildir" uyarısı.

## SEO standartları
- Hedef anahtar kelime: title, ilk paragraf, en az bir H2 ve description içinde geçsin (doğal şekilde, spam değil).
- Eş anlamlı/yan kelimeleri (LSI) doğal kullan.
- **İç linkleme:** Her yeni yazıda ilgili 2-3 eski yazıya link ver (markdown link ile `/blog/slug`). Bu, hem SEO hem ortalama oturum süresi için kritik.
- Görsel/şema yerine metin-içi mini tablolar ve örnekler kullan (statik site, görsel üretimi yok).

## Ton
- Sade, samimi, "sen" dili. Jargonu açıkla.
- Tarafsız ve bağımsız. Belirli ürün/şirket önermez, kategori/yöntem anlatır.
- Gerçekçi: "hızlı zengin ol" vaadi yok; risk dürüstçe söylenir.
- Türkiye bağlamı (TL, enflasyon, BES, BIST) göz önünde.

## Tekrar/çakışma kontrolü
- Yeni yazı, mevcut bir yazının kopyası olmamalı. Aynı niyetli iki yazı varsa birleştir.
- `docs/keywords.md` "Yayınlananlar" listesini kontrol et.

## Frontmatter şablonu
```markdown
---
title: ""
description: ""
pubDate: YYYY-MM-DD
category: ""   # Yatırım | Borsa | Kripto | Kişisel Finans | Ekonomi | Emeklilik
tags: []
readingTime: 8
featured: false
faq:
  - q: "Soru 1?"
    a: "Kısa, net cevap (1-3 cümle)."
  - q: "Soru 2?"
    a: "Kısa, net cevap."
  - q: "Soru 3?"
    a: "Kısa, net cevap."
---
```
