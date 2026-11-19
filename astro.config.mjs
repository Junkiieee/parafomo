// @ts-check
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import trailingSlashLinks from './src/integrations/trailing-slash-links.mjs';
import coverVariants from './src/integrations/cover-variants.mjs';
import stripPipelineFiles from './src/integrations/strip-pipeline-files.mjs';
import { readJson, asDate, lastmodByPage, lastmodByIpo, dataDir } from './src/data/page-lastmod.mjs';

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
// Olay yazıları (frontmatter `sonuc:`) — karar/veri açıklandıysa lastmod açıklanma anı (src/data/event-result.ts ile aynı kaynak)
const AYLAR_TR = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
const eventDate = (sonuc) => {
  const [tur, key] = sonuc.split(':');
  if (tur === 'tcmb' || tur === 'fed') {
    const files = readdirSync(dataDir).filter((f) => f.startsWith(tur === 'tcmb' ? 'tcmb-' : 'fomc-') && f.endsWith('.json'));
    for (const f of files) {
      const d = readJson(f) ?? {};
      const m = [...(d.meetings ?? []), ...(d.meetings2027 ?? [])].find((x) => x.decisionDate === key);
      if (m?.result) return asDate(`${key}T${m.tsiTime ?? '14:00'}:00+03:00`);
    }
  } else if (tur === 'tufe') {
    if ((readJson('tufe-aylik.json')?.months ?? []).some((x) => x.ay === key)) {
      // event-result.ts ile aynı kural: TÜİK takvimindeki gün, yoksa izleyen ayın 3'ü; saat 10:00 TSİ
      // (eskiden "ayın 5'i" sabiti: Ekim 2026 verisi 3 Kasım'da açıklandı).
      const [y, mo] = key.split('-').map(Number);
      const ay = `${AYLAR_TR[mo - 1]} ${y}`;
      const rel = readdirSync(dataDir).filter((f) => /^tuik-enflasyon-\d{4}\.json$/.test(f))
        .flatMap((f) => readJson(f)?.releases ?? []).find((r) => r.covers === ay)?.date
        ?? (mo === 12 ? `${y + 1}-01-03` : `${y}-${String(mo + 1).padStart(2, '0')}-03`);
      return asDate(`${rel}T10:00:00+03:00`);
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

// Liste sayfaları: anasayfa ve /blog/ en yeni yazıyla, /kategori/<slug>/ o kategorinin en yeni yazısıyla değişir
// (dal 2026-11-03 a9ca5d89; sitemap'te lastmod'ları yoktu).
const categorySlugByName = {};
try {
  const cfg = readFileSync(fileURLToPath(new URL('./src/site.config.ts', import.meta.url)), 'utf-8');
  for (const m of cfg.matchAll(/\{\s*name:\s*'([^']+)',\s*slug:\s*'([^']+)'/g)) categorySlugByName[m[1]] = m[2];
} catch {
  // sessiz geç
}
const newestPost = { all: null, byCategory: {} };
try {
  for (const file of readdirSync(blogDir)) {
    if (!/\.mdx?$/.test(file)) continue;
    const fm = readFileSync(`${blogDir}/${file}`, 'utf-8').split(/^---\s*$/m)[1] ?? '';
    if (/^\s*draft:\s*true\b/m.test(fm)) continue;
    const lm = lastmodBySlug[file.replace(/\.mdx?$/, '')];
    if (!lm) continue;
    const cat = categorySlugByName[fm.match(/^\s*category:\s*['"]?([^'"\n]+?)['"]?\s*$/m)?.[1]];
    if (!newestPost.all || lm > newestPost.all) newestPost.all = lm;
    if (cat && (!newestPost.byCategory[cat] || lm > newestPost.byCategory[cat])) newestPost.byCategory[cat] = lm;
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
    stripPipelineFiles(),
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
        const path = new URL(item.url).pathname;
        if ((path === '/' || path === '/blog/') && newestPost.all) {
          item.lastmod = newestPost.all;
          item.changefreq = 'daily';
        }
        const kat = path.match(/^\/kategori\/([^/]+)\/$/);
        if (kat && newestPost.byCategory[kat[1]]) item.lastmod = newestPost.byCategory[kat[1]];
        // Halka arz şirket sayfaları (78): src/data/page-lastmod.mjs → lastmodByIpo
        const ipo = path.match(/^\/halka-arz\/([^/]+)\/$/);
        if (ipo && lastmodByIpo[ipo[1]]) item.lastmod = lastmodByIpo[ipo[1]];
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
