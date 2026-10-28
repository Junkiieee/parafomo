// Google News site haritası: build anından önceki 48 saatte yayımlanan ya da güncellenen yazılar (en çok 1000).
// Google News yalnız son 2 günün yazılarını ister; hiç yazı yoksa da geçerli XML döner (boş <urlset>).
// robots.txt'de ilan edilir; scripts/gsc-sitemap.py ana site haritasıyla birlikte Search Console'a gönderir.
// Başlık ve güncellenme PostLayout ile aynı kuralla: olay yazısının sonucu açıklandıysa sonucBaslik + o gün.
import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { SITE } from '../site.config';
import { eventResult, fillTitle } from '../data/event-result';

const WINDOW_MS = 48 * 60 * 60 * 1000;
const MAX_URLS = 1000;

const xml = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&apos;');
// W3C datetime, saniye hassasiyeti (2026-10-28T09:30:00Z)
const w3c = (d: Date) => d.toISOString().replace(/\.\d{3}Z$/, 'Z');

export const GET: APIRoute = async () => {
  const now = Date.now();
  // Yalnız tarih yazılmış gelecek günler (TSİ gece yarısı ~ UTC akşamı) build anına çekilir.
  const clamp = (d: Date) => (d.getTime() > now ? new Date(now) : d);
  const fresh = (d: Date) => now - d.getTime() <= WINDOW_MS;

  const posts = await getCollection('blog', ({ data }) => !data.draft);
  const items = posts
    .map((post) => {
      const { title: rawTitle, pubDate, updatedDate, sonuc, sonucBaslik } = post.data;
      const ev = eventResult(sonuc);
      const title = (ev?.done && fillTitle(sonucBaslik, ev.vars)) || rawTitle;
      const base = updatedDate ?? pubDate;
      const evModified = ev?.done ? new Date(ev.date + 'T12:00:00Z') : null;
      const pub = clamp(pubDate);
      const modified = clamp(evModified && evModified > base ? evModified : base);
      return { id: post.id, title, pub, modified, date: modified > pub ? modified : pub };
    })
    .filter((p) => fresh(p.pub) || fresh(p.modified))
    .sort((a, b) => b.date.getTime() - a.date.getTime())
    .slice(0, MAX_URLS);

  const urls = items
    .map(
      (p) =>
        `<url><loc>${xml(new URL(`/blog/${p.id}/`, SITE.url).href)}</loc><news:news><news:publication><news:name>${xml(SITE.name)}</news:name><news:language>tr</news:language></news:publication><news:publication_date>${w3c(p.date)}</news:publication_date><news:title>${xml(p.title)}</news:title></news:news></url>`,
    )
    .join('\n');

  const body = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
${urls ? urls + '\n' : ''}</urlset>
`;
  return new Response(body, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
