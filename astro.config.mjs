// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';

// Yayına alırken bu adresi kendi alan adınla değiştir.
const SITE = 'https://parafomo.com';

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
});
