// ParaFOMO — kapak görseli WebP varyantları.
//
// public/covers/<slug>.jpg 1600x900 JPG'dir (~200 KB); kartlarda 640px, yazı
// hero'sunda en fazla ~760px gösterilir. Mobil LCP'yi 5-6 sn'ye çıkarıyordu
// (Lighthouse 2026-10-13). Bu entegrasyon config aşamasında (sayfalar render
// edilmeden ve public/ kopyalanmadan önce) her kapak için
// public/covers/w/<slug>-{640,1280}.webp üretir. Bileşenler varyantın varlığını
// kontrol edip <picture> kullanır; sharp çalışmazsa JPG'ye düşer, build bozulmaz.
// Varyantlar git'e girmez (.gitignore) — her build yeniden/eksikse üretir.
import { mkdir, readdir, stat } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const COVER_WIDTHS = [640, 1280];

export default function coverVariants() {
  return {
    name: 'parafomo-cover-variants',
    hooks: {
      'astro:config:setup': async ({ config, logger }) => {
        const src = join(fileURLToPath(config.publicDir), 'covers');
        const out = join(src, 'w');
        let sharp;
        try {
          sharp = (await import('sharp')).default;
        } catch (e) {
          logger.warn(`sharp yüklenemedi, kapaklar JPG kalacak: ${e.message}`);
          return;
        }
        let files;
        try {
          files = (await readdir(src)).filter((f) => f.endsWith('.jpg'));
        } catch {
          return;
        }
        await mkdir(out, { recursive: true });
        let made = 0;
        for (const f of files) {
          const slug = f.slice(0, -4);
          const srcStat = await stat(join(src, f));
          for (const w of COVER_WIDTHS) {
            const target = join(out, `${slug}-${w}.webp`);
            const fresh = await stat(target).then((s) => s.mtimeMs >= srcStat.mtimeMs, () => false);
            if (fresh) continue;
            try {
              await sharp(join(src, f)).resize({ width: w, withoutEnlargement: true }).webp({ quality: 72 }).toFile(target);
              made++;
            } catch (e) {
              logger.warn(`${f} → ${w}px üretilemedi: ${e.message}`);
            }
          }
        }
        if (made) logger.info(`kapak varyantı üretildi: ${made} dosya (${files.length} kapak)`);
      },
    },
  };
}
