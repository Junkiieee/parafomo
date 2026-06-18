import type { APIRoute } from 'astro';
import { SITE } from '../site.config';

const robots = `User-agent: *
Allow: /

Sitemap: ${new URL('sitemap-index.xml', SITE.url).href}
`;

export const GET: APIRoute = () =>
  new Response(robots, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
