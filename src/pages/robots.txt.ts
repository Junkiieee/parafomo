import type { APIRoute } from 'astro';
import { SITE } from '../site.config';

// /portfoy/ engeli kaldırıldı (2026-11-03): engelli yolda Googlebot ne /portfoy/panel/ → app.parafomo.com 301'ini
// ne de /portfoy/sifre-sifirla/ noindex'ini görebiliyordu; eski URL'ler "engellendi ama dizinde" kalabiliyordu.
// Bu yoldaki sayfalar noindex ya da 301; sitemap filtresi (astro.config) onları yine dışarıda tutar.
const robots = `User-agent: *
Allow: /

Sitemap: ${new URL('sitemap-index.xml', SITE.url).href}
Sitemap: ${new URL('news-sitemap.xml', SITE.url).href}
`;

export const GET: APIRoute = () =>
  new Response(robots, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
