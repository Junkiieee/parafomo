// @ts-check
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import trailingSlashLinks from './src/integrations/trailing-slash-links.mjs';
import coverVariants from './src/integrations/cover-variants.mjs';
import rehypeTableScroll from './src/integrations/rehype-table-scroll.mjs';
import stripPipelineFiles from './src/integrations/strip-pipeline-files.mjs';

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
  if (isNaN(d)) return null;
  // Yalnız-tarih değerler 12:00Z'ye çevriliyordu → build sabahsa lastmod gelecekte kalıyordu (denetim 2026-10-22).
  return d.getTime() > Date.now() ? new Date() : d;
};
const updatedOf = (f) => {
  const d = readJson(f);
  if (!d) return null;
  if (d.updated) return asDate(d.updated);
  if (d.guncellenme) return asDate(d.guncellenme);
  // TCMB/Fed takvimi: açıklanmış son kararın günü
  const ms = [...(d.meetings ?? []), ...(d.meetings2027 ?? [])].filter((m) => m.result)
    .map((m) => `${m.decisionDate}T${m.tsiTime ?? '14:00'}:00+03:00`).sort();
  return ms.length ? asDate(ms.at(-1)) : null;
};
const YD = ['yeniden-degerleme.json'];
// Yıllık takvim dosyaları (tcmb-2026.json, tcmb-2027.json …): hepsi okunur — yeni yıl dosyası eklenince lastmod onu
// da görür (yıl geçişi denetimi 2026-11-03: yalnız 2026 dosyası okunuyordu).
const yillik = (onek) => readdirSync(dataDir).filter((f) => new RegExp(`^${onek}-\\d{4}\\.json$`).test(f));
const TUFE = ['tufe-aylik.json'];
const FAIZ = ['faiz-oranlari.json'];
const DATA_PAGES = {
  'engelli-maasi': ['tufe-aylik.json', 'asgari-ucret.json'],
  'dogum-yardimi': YD,
  'evde-bakim-maasi': ['asgari-ucret.json', 'tufe-aylik.json'],
  'veraset-ve-intikal-vergisi-hesaplama': YD,
  'noter-ucretleri': YD,
  'tapu-harci-hesaplama': YD,
  'arac-muayene-ucreti': YD,
  'damga-vergisi-hesaplama': YD,
  'tasit-kredisi-hesaplama': FAIZ,
  // Asgari ücrete bağlı sayfalar, ÖTV ve değer artışı: sitemap'te lastmod'ları yoktu (denetim 2026-11-03).
  'asgari-ucret-hesaplama': ['asgari-ucret.json'], 'bagkur-primi-hesaplama': ['asgari-ucret.json'],
  'gss-primi-hesaplama': ['asgari-ucret.json'], 'otv-hesaplama': YD,
  'deger-artis-kazanci-hesaplama': ['yiufe-endeks.json', 'yeniden-degerleme.json'],
  'yeniden-degerleme-orani': YD, 'mtv-hesaplama': YD, 'pasaport-ehliyet-harci': YD, 'trafik-cezalari-hesaplama': YD,
  'emlak-vergisi-hesaplama': YD, 'gelir-vergisi-hesaplama': YD, 'vergi-dilimi-hesaplama': YD,
  'emekli-zammi-hesaplama': TUFE, 'memur-zammi-hesaplama': TUFE, 'en-dusuk-emekli-maasi': TUFE,
  'enflasyon-hesaplama': TUFE, 'enflasyon-takvimi': TUFE, 'kidem-tazminati-hesaplama': TUFE,
  'kira-artis-orani-hesaplama': ['kira-artis-2026.json'],
  'mevduat-faizi-hesaplama': FAIZ, 'konut-kredisi-hesaplama': FAIZ, 'ihtiyac-kredisi-hesaplama': FAIZ, 'kredi-hesaplama': FAIZ,
  'altin-getiri': ['altin-getiri.json'], 'dolar-getiri': ['dolar-getiri.json'], 'euro-getiri': ['euro-getiri.json'],
  'bist-getiri': ['bist-getiri.json'], 'gumus-getiri': ['gumus-getiri.json'], 'bitcoin-getiri': ['bitcoin-getiri.json'],
  'altin-dolar-borsa': ['altin-getiri.json', 'dolar-getiri.json', 'bist-getiri.json', 'euro-getiri.json', 'gumus-getiri.json', 'bitcoin-getiri.json'],
  'altin-fiyatlari': ['altin-fiyat.json'], 'altin-hesaplama': ['altin-fiyat.json'], 'altin-kac-gram': ['altin-fiyat.json'],
  'dolar-endeksi': ['dxy.json'], 'abd-tahvil-faizi': ['us-tahvil.json'], 'halka-arz': ['halka-arz.json'], 'halka-arz-getiri': ['halka-arz-getiri.json'],
  'tcmb-faiz-takvimi': yillik('tcmb'), 'fed-faiz-takvimi': yillik('fomc'), 'ekonomik-takvim': ['economic-calendar.json'],
};
const lastmodByPage = {};
for (const [page, files] of Object.entries(DATA_PAGES)) {
  const ds = files.map(updatedOf).filter(Boolean);
  if (ds.length) lastmodByPage[page] = new Date(Math.max(...ds)).toISOString();
}
// Olay yazıları (frontmatter `sonuc:`) — karar/veri açıklandıysa lastmod o gün (src/data/event-result.ts ile aynı kaynak)
// src/data/tuik.ts usualReleaseDate ile aynı kural: izleyen ayın 3'ü, hafta sonuysa ilk iş günü.
const usualTuikDate = (y, mo) => {
  const d = new Date(Date.UTC(mo === 12 ? y + 1 : y, mo === 12 ? 0 : mo, 3));
  while (d.getUTCDay() === 0 || d.getUTCDay() === 6) d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10);
};
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
      // src/data/event-result.ts ile aynı kural: TÜİK takvimindeki gün, yoksa izleyen ayın 3'ü; saat 10:00 TSİ.
      const [y, mo] = key.split('-').map(Number);
      const ay = `${AYLAR_TR[mo - 1]} ${y}`;
      const rel = readdirSync(dataDir).filter((f) => /^tuik-enflasyon-\d{4}\.json$/.test(f))
        .flatMap((f) => readJson(f)?.releases ?? []).find((r) => r.covers === ay)?.date
        ?? usualTuikDate(y, mo);
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

// Liste sayfaları: anasayfa ve /blog/ en yeni yazıyla, /kategori/<slug>/ o kategorinin en yeni yazısıyla değişir.
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
// Halka arz şirket sayfaları: kaynağın (halkarz.com) şirket güncellemesi "GG.AA.YYYY SS:dd" TSİ ya da ilk görülme;
// işlem gören şirketin getirisi her gün yenilendiği için onlarda getiri dosyasının zamanı.
const ipoReturns = readJson('halka-arz-getiri.json');
const ipoRetCodes = new Set((ipoReturns?.all_items ?? ipoReturns?.items ?? []).map((r) => r.code));
const trStamp = (v) => {
  const m = /^(\d{2})\.(\d{2})\.(\d{4}) (\d{2}):(\d{2})$/.exec(v ?? '');
  return m ? asDate(`${m[3]}-${m[2]}-${m[1]}T${m[4]}:${m[5]}:00+03:00`) : null;
};
const lastmodByIpo = {};
for (const [slug, it] of Object.entries(readJson('halka-arz-sirketler.json')?.items ?? {})) {
  const ds = [
    trStamp(it.updated_src),
    it.first_seen ? asDate(it.first_seen) : null,
    it.bist_code && ipoRetCodes.has(it.bist_code) && ipoReturns?.updated ? asDate(ipoReturns.updated) : null,
  ].filter(Boolean);
  if (ds.length) lastmodByIpo[slug] = new Date(Math.max(...ds)).toISOString();
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
      // /portfoy/ altı ya noindex (şifre sıfırlama) ya app.parafomo.com'a 301 — sitemap'te yeri yok (GSC 2026-10-10)
      filter: (page) => !page.includes('/portfoy/'),
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
    rehypePlugins: [rehypeTableScroll],
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
