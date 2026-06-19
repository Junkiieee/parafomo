# ParaFOMO Büyüme Planı — Hedef: Günlük 1.000 Ziyaretçi

## Gerçekçi zaman çizelgesi
Organik SEO bir maraton. Tahmini eğri (istikrarlı içerik + doğru teknik SEO ile):

| Dönem | Beklenen günlük ziyaretçi | Ana kaynak |
|-------|---------------------------|------------|
| Hafta 1-2 | 5-30 | Sosyal + ilk indeksleme |
| Hafta 3-6 | 30-150 | Long-tail anahtar kelimeler sıralanmaya başlar |
| Hafta 7-12 | 150-500 | İçerik birikimi + iç linkleme + otorite |
| Ay 4-6 | 500-1.000+ | Olgunlaşan SEO + tekrar gelen kitle + bülten |

> Not: Bu bir tahmindir, garanti değildir. Hız; niş rekabeti, içerik kalitesi ve dağıtım çabasına bağlı. Tek değişmez kural: **istikrar.**

## İki motor

### 1. SEO motoru (asıl, uzun vade)
- **Her gün 1 yeni, kaliteli, anahtar kelime hedefli makale** (otomasyon üretir).
- İç linkleme ağı (her yazı eski yazılara link verir).
- Teknik SEO: sitemap, hız, yapısal veri, mobil — hepsi hazır.
- Search Console takibi: hangi sorgu tıklanıyor → o konuda daha derin içerik.

### 2. Dağıtım motoru (kısa vade ilk trafik)
- Her yeni yazı için X (Twitter) thread + Instagram carousel/post taslağı.
- İlgili topluluklar: Reddit (r/borsa, r/Turkey финans), Ekşi Sözlük, finans Facebook/Telegram grupları (spam değil, değer katarak).
- Bülten: her yazıyı abonelere gönder → tekrar gelen trafik.

## Günlük otomasyon ne yapar?
Zamanlanmış ajan her gün:
1. `docs/keywords.md`'den sıradaki konuyu alır.
2. `docs/content-playbook.md` standardında makaleyi yazar (`src/content/blog/`).
3. İlgili eski yazılara iç link ekler.
4. `keywords.md`'yi günceller (konuyu yayınlananlara taşır).
5. `npm run build` ile doğrular.
6. Repoya commit'ler (push → otomatik deploy).
7. O günün **sosyal medya paylaşım taslağını** ve **senin yapman gereken 1-2 işi** günlük nota yazar (`docs/daily-log.md`).

## 🔴 Kullanıcının (senin) yapman gerekenler

### Tek seferlik kurulum (önce bunlar)
- [x] **Domain** al → `parafomo.com` ✅ (canlı, HTTP 200)
- [x] **GitHub** hesabı aç → repoyu yükle ✅
- [x] **Cloudflare Pages** → repoyu bağla, build `npm run build`, output `dist`, `NODE_VERSION=22` ✅ (deploy çalışıyor)
- [x] **Domain'i hosting'e bağla** (DNS) ✅ (parafomo.com yönleniyor)
- [x] **Google Search Console** → domain doğrulandı + `sitemap-index.xml` gönderildi ✅
- [x] **Analytics** → GA4 kuruldu, ölçüm kimliği `G-4KNGH3574V` koda fallback olarak gömüldü, canlıda gtag basılıyor ✅
- [x] **Sosyal hesaplar** → X (@parafomo) + Instagram (@parafomo) açıldı ✅
- [ ] **Bülten** → MailerLite/Buttondown (ücretsiz) hesabı aç, form linkini Claude'a ver.

### Her gün (5-10 dk, otomasyonun ürettiğini dağıt)
- [ ] `docs/daily-log.md`'deki günün sosyal taslağını X + Instagram'da paylaş.
- [ ] 1-2 ilgili toplulukta (değer katarak) yazıyı paylaş.
- [ ] Gelen yorum/DM'lere yanıt ver (topluluk = sadakat).

## Başarı metrikleri (haftalık bak)
- Search Console: gösterim (impressions) ↑, tıklama ↑, ortalama pozisyon ↓ (iyiye).
- Analytics: günlük ziyaretçi, ortalama oturum süresi, en çok okunan yazılar.
- Bülten: abone sayısı ↑.

## İçerik ötesi büyüme kaldıraçları (sonraki faz)
- En çok tıklanan yazıları periyodik güncelle (tazelik sinyali).
- "Pillar + cluster" yapısı: ana rehber + ona bağlı alt yazılar.
- Backlink: kaliteli içerikle doğal atıf; finans forumlarında referans olma.
- Basit araçlar (faiz/bileşik getiri hesaplayıcı) → yüksek trafik mıknatısı.
