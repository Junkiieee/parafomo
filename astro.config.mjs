// @ts-check
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';

import cloudflare from '@astrojs/cloudflare';

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

// https://astro.build/config
export default defineConfig({
  site: SITE,

  // Cloudflare statik sunumu sonda '/' zorluyor; canonical/sitemap ile uyum için 'always'.
  trailingSlash: 'always',

  integrations: [
    mdx(),
    sitemap({
      changefreq: 'weekly',
      priority: 0.7,
      serialize(item) {
        const m = item.url.match(/\/blog\/([^/]+)\/?$/);
        if (m && lastmodBySlug[m[1]]) {
          item.lastmod = lastmodBySlug[m[1]];
          item.changefreq = 'monthly';
          item.priority = 0.8;
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
    inlineStylesheets: 'auto',
  },

  adapter: cloudflare()
});