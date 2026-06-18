# ParaFOMO 💸

> Parana akıl kat. — Yatırım, borsa, kripto ve kişisel finans üzerine sade, güvenilir ve bağımsız Türkçe içerik.

Astro ile geliştirilmiş, SEO odaklı, hızlı bir finans blog/yayın sitesi. Hedef: **organik içerik motoruyla günlük 1.000+ ziyaretçi.**

## 🚀 Teknoloji

- [Astro 6](https://astro.build) — statik, çok hızlı, mükemmel SEO
- İçerik: Markdown/MDX content collections
- Otomatik **sitemap**, **RSS**, **robots.txt**, **JSON-LD** yapısal veri
- Sıfır JS bağımlılığı (sadece minik aydınlatma scriptleri)

## 📦 Kurulum

```bash
npm install
npm run dev      # http://localhost:4321
npm run build    # dist/ üretir
npm run preview  # build önizleme
```

> Node **22+** gerekir.

## ✍️ Yeni yazı ekleme

`src/content/blog/` altına `.md` dosyası ekle. Frontmatter şablonu:

```markdown
---
title: "Başlık (arama yapılan soruyu içersin)"
description: "150-160 karakter, anahtar kelimeli SEO açıklaması."
pubDate: 2026-06-18
category: "Yatırım"   # Yatırım | Borsa | Kripto | Kişisel Finans | Ekonomi | Emeklilik
tags: ["etiket1", "etiket2"]
readingTime: 8
featured: false        # anasayfada öne çıkar
---

İçerik buraya (H2/H3 başlıklar, tablolar, listeler, özet).
```

Editöryel takvim ve hedef anahtar kelimeler: [`docs/keywords.md`](docs/keywords.md)
İçerik kalite standardı: [`docs/content-playbook.md`](docs/content-playbook.md)

## 🌐 Yayına alma (deploy)

Statik çıktı her yerde çalışır. Önerilen: **Cloudflare Pages** (ücretsiz, hızlı CDN).

**Cloudflare Pages:**
1. GitHub reposunu bağla
2. Build komutu: `npm run build` — Output dizini: `dist`
3. Environment: `NODE_VERSION=22`
4. Domain'i bağla (`parafomo.com`)

**Netlify / Vercel:** Repo bağla, ayarlar `netlify.toml` içinde hazır.

### Yayın sonrası ŞART olan SEO adımları
1. **Google Search Console**'a domaini ekle + doğrula
2. `https://parafomo.com/sitemap-index.xml` adresini Search Console'a gönder
3. Analytics: hosting panelinden `PUBLIC_GA_ID` (GA4) gir ya da Cloudflare Web Analytics aç

## 🤖 Günlük otomasyon

Her gün yeni SEO içeriği üreten zamanlanmış ajan repodaki backlog'u kullanır.
Detaylar: [`docs/growth-plan.md`](docs/growth-plan.md)

## ⚠️ Yasal

İçerikler bilgilendirme amaçlıdır, yatırım tavsiyesi değildir.
