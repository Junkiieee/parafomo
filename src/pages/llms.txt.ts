// llms.txt — yapay zekâ arama motorları (ChatGPT, Perplexity vb.) için site haritası özeti (llmstxt.org biçimi).
// Eskiden public/llms.txt elle tutuluyordu ve ~65 aracın yalnız 8'ini listeliyordu (zam sezonu ve sosyal hak
// araçları yoktu; denetim 2026-11-03). Artık araç listesi src/data/tools.ts'ten gelir: yeni araç kendiliğinden girer.
import type { APIRoute } from 'astro';
import { SITE, CATEGORIES } from '../site.config';
import { GRUPLAR } from '../data/tools';

const abs = (path: string) => new URL(path, SITE.url).href;

export const GET: APIRoute = () => {
  const araclar = GRUPLAR.filter((g) => g.araclar.length > 0)
    .map((g) => `## ${g.baslik}\n${g.araclar.map((t) => `- [${t.ad}](${abs(t.href)}): ${t.aciklama}`).join('\n')}`)
    .join('\n\n');

  const uretim = new Date().toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Europe/Istanbul' });
  const body = `# ParaFOMO

> ParaFOMO (parafomo.com), Türk tasarruf sahiplerinin enflasyon karşısında birikimini veriyle korumasına yardım eden Türkçe kişisel finans sitesidir. Altın, gümüş, dolar, euro, BIST 100 ve bitcoin için TL bazında tarihsel getiri tabloları; TCMB, TÜİK enflasyon ve Fed takvimleri; halka arz takvimi ve getiri karnesi; güncel oranlarla maaş, zam, vergi, kredi ve faiz hesaplayıcıları sunar. Yatırım tavsiyesi vermez; geçmiş veriyi kaynağıyla gösterir.

Veriler kaynağı açıklandıkça otomatik güncellenir: altın, dolar endeksi ve ABD tahvil faizleri Pazartesi–Cumartesi gün içinde birkaç kez; getiri serileri, faiz oranları, TÜFE ve resmî tutarlar kendi açıklama günlerinde (kaynaklar: Yahoo Finance fiyat serileri, TCMB, TÜİK, Fed, SGK, Resmî Gazete, halkarz.com). Her sayfada "son güncelleme" tarihi ve yöntem notu bulunur; ayrıntı: ${abs('/metodoloji/')}

${araclar}

## Uygulamalar (ücretsiz, reklamsız)
- [Portföy takip](https://app.parafomo.com/portfoy/): altın, BIST hissesi ve gümüş pozisyonları için değer grafiği, enflasyon sonrası reel getiri ve fiyat alarmı
- [Birikim simülatörü](https://app.parafomo.com/birikim/): düzenli aylık alımın gerçek 15 yıllık veriyle sonucu, enflasyon karşılaştırmalı; üyelik gerekmez

## Rehberler
- [Blog](${abs('/blog/')}): yatırım araçları, vergi, BES, enflasyon ve kişisel finans rehberleri
${CATEGORIES.map((c) => `- [${c.name}](${abs(`/kategori/${c.slug}/`)}): ${c.desc}`).join('\n')}

## Hakkında
- [Hakkımızda](${abs('/hakkimizda/')})
- [Editoryal politika](${abs('/editoryal-politika/')})
- [Metodoloji](${abs('/metodoloji/')})
- [Haftalık bülten](${abs('/bulten/')})

_Bu liste her yayında yeniden üretilir · son üretim: ${uretim}_
`;
  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
