// @ts-check
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import trailingSlashLinks from './src/integrations/trailing-slash-links.mjs';
import coverVariants from './src/integrations/cover-variants.mjs';
import { readJson, asDate, lastmodByPage, dataDir } from './src/data/page-lastmod.mjs';

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

// Veri sayfaları lastmod'u: src/data/page-lastmod.mjs (BaseLayout dateModified ile ortak kaynak).
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
      filter: (page) => !page.includes('/portfoy/') && !page.includes('/embed/'),   // embed: noindex iframe kutuları
      serialize(item) {
        const m = item.url.match(/\/blog\/([^/]+)\/?$/);
        if (m && lastmodBySlug[m[1]]) {
          item.lastmod = lastmodBySlug[m[1]];
          item.changefreq = 'monthly';
          item.priority = 0.8;
        }
        // İç içe altın sayfaları (/altin-fiyatlari/<tür>/) hiç lastmod almıyordu.
        if (/\/altin-fiyatlari\/[^/]+\/?$/.test(item.url) && lastmodByPage['altin-fiyatlari']) {
          item.lastmod = lastmodByPage['altin-fiyatlari'];
          item.changefreq = 'daily';
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
