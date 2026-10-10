// ParaFOMO — build sonrası iç link normalizasyonu.
//
// Site `trailingSlash: 'always'` ile yayında; sonda '/' olmayan her iç link
// (/blog, /kategori/borsa, /blog/x#y ...) bir yönlendirme hop'u demek ve Google'a
// kopya URL keşfettiriyordu (GSC'de /fed-faiz-takvimi ile /fed-faiz-takvimi/ ayrı
// satırlar, 2026-10-10). Bu entegrasyon dist/ içindeki bütün HTML'de iç linkleri
// sonda '/' ile yazar — elle/ajanla yazılan içerik de otomatik kapsanır.
//
// Kapsam: href="/yol" ve tırnak içindeki "https://parafomo.com/yol" (og:url,
// JSON-LD). Son parçasında nokta olan (dosya: .png, .xml, .json) yollara dokunmaz.
import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SKIP_PREFIXES = ['/cdn-cgi/', '/_astro/'];

function fixPath(path) {
  // path: '/a/b' (sorgu/hash hariç)
  if (path === '' || path.endsWith('/')) return path;
  if (SKIP_PREFIXES.some((p) => path.startsWith(p))) return path;
  const last = path.slice(path.lastIndexOf('/') + 1);
  if (last.includes('.')) return path;
  return path + '/';
}

// href="/yol?x#y" veya href="https://parafomo.com/yol"
const HREF_RE = /(href=)(["'])((?:https:\/\/(?:www\.)?parafomo\.com)?)(\/[^"'?#\s]*)([^"'\s]*)\2/g;
// "https://parafomo.com/yol" (meta content, JSON-LD); href zaten yukarıda işlendi
const ABS_RE = /(["'])(https:\/\/parafomo\.com)(\/[^"'?#\s<>]*)([^"'\s<>]*)\1/g;

export function normalizeHtml(html) {
  let out = html.replace(HREF_RE, (m, attr, q, host, path, rest) => {
    if (path.startsWith('//')) return m; // protokol-bağıl dış link
    return `${attr}${q}${host === 'https://www.parafomo.com' ? 'https://parafomo.com' : host}${fixPath(path)}${rest}${q}`;
  });
  out = out.replace(ABS_RE, (m, q, host, path, rest) => `${q}${host}${fixPath(path)}${rest}${q}`);
  return out;
}

async function* htmlFiles(dir) {
  for (const ent of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, ent.name);
    if (ent.isDirectory()) yield* htmlFiles(p);
    else if (ent.name.endsWith('.html')) yield p;
  }
}

export default function trailingSlashLinks() {
  return {
    name: 'parafomo-trailing-slash-links',
    hooks: {
      'astro:build:done': async ({ dir, logger }) => {
        const root = fileURLToPath(dir);
        let files = 0;
        let changed = 0;
        for await (const f of htmlFiles(root)) {
          files++;
          const src = await readFile(f, 'utf-8');
          const out = normalizeHtml(src);
          if (out !== src) {
            changed++;
            await writeFile(f, out);
          }
        }
        logger.info(`iç linkler '/' ile normalize edildi: ${changed}/${files} HTML`);
      },
    },
  };
}
