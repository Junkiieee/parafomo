// @ts-check
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import trailingSlashLinks from './src/integrations/trailing-slash-links.mjs';
import coverVariants from './src/integrations/cover-variants.mjs';

// Yayına alırken bu adresi kendi alan adınla değiştir.
const SITE = 'https://parafomo.com';

// Sitemap lastmod için yazı slug'ı → son güncelleme tarihi haritası.
// Frontmatter'dan updatedDate (yoksa pubDate) okunur.
const blogDir = fileURLToPath(new URL('./src/content/blog', import.meta.url));
const lastmodBySlug = {};
try {
  for (const file of readdirSync(blogDir)) {
    if (!/\.mdx?$/.test(file)) continue;
    const slug = file.replace(/\.mdx?$/, '');
    const raw = readFileSync(`${blogDir}/${file}`, 'utf-8');
    const fm = raw.split(/^---\s*$/m)[1] ?? '';
    const pub = fm.match(/^\s*pubDate:\s*['"]?([0-9-]+)/m)?.[1];
    const upd = fm.match(/^\s*updatedDate:\s*['"]?([0-9-]+)/m)?.[1];
    const date = upd || pub;
    if (date) lastmodBySlug[slug] = new Date(date).toISOString();
  }
} catch {
  // içerik klasörü yoksa sessiz geç
}

// Veri sayfaları + olay yazıları için lastmod: beslendikleri veri dosyasının güncellenme zamanı.
// Neden: araç sayfalarının sitemap'te hiç lastmod'u yoktu; TÜİK/TCMB günü rakam değişse de Google'a
// "bu sayfa değişti" sinyali gitmiyordu. lastmod yalnız veri gerçekten değişince ilerler (doğru sinyal).
const dataDir = fileURLToPath(new URL('./data', import.meta.url));
const readJson = (f) => {
  try { return JSON.parse(readFileSync(`${dataDir}/${f}`, 'utf-8')); } catch { return null; }
};
const asDate = (v) => {
  const d = new Date(String(v).length === 10 ? `${v}T12:00:00Z` : v);
  return isNaN(d) ? null : d;
};
const updatedOf = (f) => {
  const d = readJson(f);
  if (!d) return null;
  if (d.updated) return asDate(d.updated);
  // TCMB/Fed takvimi: açıklanmış son kararın günü
  const ms = [...(d.meetings ?? []), ...(d.meetings2027 ?? [])].filter((m) => m.result).map((m) => m.decisionDate).sort();
  return ms.length ? asDate(`${ms.at(-1)}T20:00:00Z`) : null;
};
const YD = ['yeniden-degerleme.json'];
const TUFE = ['tufe-aylik.json'];
const FAIZ = ['faiz-oranlari.json'];
const DATA_PAGES = {
  'damga-vergisi-hesaplama': YD,
  'tasit-kredisi-hesaplama': FAIZ,
  'yeniden-degerleme-orani': YD, 'mtv-hesaplama': YD, 'pasaport-ehliyet-harci': YD, 'trafik-cezalari-hesaplama': YD,
  'emlak-vergisi-hesaplama': YD, 'gelir-vergisi-hesaplama': YD, 'vergi-dilimi-hesaplama': YD,
  'emekli-zammi-hesaplama': TUFE, 'memur-zammi-hesaplama': TUFE, 'en-dusuk-emekli-maasi': TUFE,
  'enflasyon-hesaplama': TUFE, 'enflasyon-takvimi': TUFE, 'kidem-tazminati-hesaplama': TUFE,
  'kira-artis-orani-hesaplama': ['kira-artis-2026.json'],
  'mevduat-faizi-hesaplama': FAIZ, 'konut-kredisi-hesaplama': FAIZ, 'ihtiyac-kredisi-hesaplama': FAIZ, 'kredi-hesaplama': FAIZ,
  'altin-getiri': ['altin-getiri.json'], 'dolar-getiri': ['dolar-getiri.json'], 'euro-getiri': ['euro-getiri.json'],
  'bist-getiri': ['bist-getiri.json'], 'gumus-getiri': ['gumus-getiri.json'], 'bitcoin-getiri': ['bitcoin-getiri.json'],
  'altin-dolar-borsa': ['benchmarks.json'], 'halka-arz': ['halka-arz.json'], 'halka-arz-getiri': ['halka-arz-getiri.json'],
  'tcmb-faiz-takvimi': ['tcmb-2026.json'], 'fed-faiz-takvimi': ['fomc-2026.json'], 'ekonomik-takvim': ['economic-calendar.json'],
};
const lastmodByPage = {};
for (const [page, files] of Object.entries(DATA_PAGES)) {
  const ds = files.map(updatedOf).filter(Boolean);
  if (ds.length) lastmodByPage[page] = new Date(Math.max(...ds)).toISOString();
}
// Olay yazıları (frontmatter `sonuc:`) — karar/veri açıklandıysa lastmod o gün (src/data/event-result.ts ile aynı kaynak)
const eventDate = (sonuc) => {
  const [tur, key] = sonuc.split(':');
  if (tur === 'tcmb' || tur === 'fed') {
    const files = readdirSync(dataDir).filter((f) => f.startsWith(tur === 'tcmb' ? 'tcmb-' : 'fomc-') && f.endsWith('.json'));
    for (const f of files) {
      const d = readJson(f) ?? {};
      const m = [...(d.meetings ?? []), ...(d.meetings2027 ?? [])].find((x) => x.decisionDate === key);
      if (m?.result) return asDate(`${key}T20:00:00Z`);
    }
  } else if (tur === 'tufe') {
    if ((readJson('tufe-aylik.json')?.months ?? []).some((x) => x.ay === key)) {
      const [y, mo] = key.split('-').map(Number);
      return asDate(mo === 12 ? `${y + 1}-01-05` : `${y}-${String(mo + 1).padStart(2, '0')}-05`);
    }
  }
  return null;
};
try {
  for (const file of readdirSync(blogDir)) {
    if (!/\.mdx?$/.test(file)) continue;
    const fm = readFileSync(`${blogDir}/${file}`, 'utf-8').split(/^---\s*$/m)[1] ?? '';
    const sonuc = fm.match(/^\s*sonuc:\s*['"]?([a-z]+:[0-9-]+)/m)?.[1];
    const ed = sonuc ? eventDate(sonuc) : null;
    const slug = file.replace(/\.mdx?$/, '');
    if (ed && (!lastmodBySlug[slug] || ed > new Date(lastmodBySlug[slug]))) lastmodBySlug[slug] = ed.toISOString();
  }
} catch {
  // sessiz geç
}

// https://astro.build/config
export default defineConfig({
  site: SITE,
  // Cloudflare statik sunumu sonda '/' zorluyor; canonical/sitemap ile uyum için 'always'.
  trailingSlash: 'always',
  integrations: [
    coverVariants(),
    mdx(),
    trailingSlashLinks(),
    sitemap({
      changefreq: 'weekly',
      priority: 0.7,
      // robots.txt /portfoy/'yu engelliyor; sitemap'te olmaları çelişkili sinyal (GSC 2026-10-10)
      filter: (page) => !page.includes('/portfoy/'),
      serialize(item) {
        const m = item.url.match(/\/blog\/([^/]+)\/?$/);
        if (m && lastmodBySlug[m[1]]) {
          item.lastmod = lastmodBySlug[m[1]];
          item.changefreq = 'monthly';
          item.priority = 0.8;
        }
        const pg = item.url.match(/^https?:\/\/[^/]+\/([^/]+)\/?$/);
        if (pg && lastmodByPage[pg[1]]) {
          item.lastmod = lastmodByPage[pg[1]];
          item.changefreq = 'daily';
          item.priority = 0.9;
        }
        return item;
      },
    }),
  ],
  markdown: {
    shikiConfig: {
      theme: 'github-dark',
      wrap: true,
    },
  },
  build: {
    // Sayfa başına CSS ~15 KB; ayrı dosya istekleri mobilde render'ı blokluyordu (Lighthouse 2026-10-13).
    inlineStylesheets: 'always',
  },
});
