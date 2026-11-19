// /ads.txt — yalnız PUBLIC_ADSENSE_CLIENT (ca-pub-…) tanımlıysa üretilir (denetim 2026-11-19, gelir-huni-8).
// Değişken boşken getStaticPaths boş döner → dosya hiç oluşmaz, /ads.txt 404 kalır (sahte kimlikli ads.txt yayına çıkmaz).
// Dinamik rota bilerek: statik `ads.txt.ts` her build'de dosya üretirdi. robots.txt / llms.txt statik rotaları önceliklidir.
import type { APIRoute, GetStaticPaths } from 'astro';

const CLIENT = String(import.meta.env.PUBLIC_ADSENSE_CLIENT ?? '').trim();
const ON = /^ca-pub-\d{10,20}$/.test(CLIENT);

export const getStaticPaths: GetStaticPaths = () => (ON ? [{ params: { adsdosya: 'ads' } }] : []);

export const GET: APIRoute = () =>
  new Response(`google.com, ${CLIENT.replace(/^ca-/, '')}, DIRECT, f08c47fec0942fa0\n`, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
