// ParaFOMO — kapak görseli WebP (+ AVIF) varyantları.
//
// public/covers/<slug>.jpg 1600x900 JPG'dir (~200 KB); kartlarda 640px, yazı
// hero'sunda en fazla ~760px gösterilir. Mobil LCP'yi 5-6 sn'ye çıkarıyordu
// (Lighthouse 2026-10-13). Bu entegrasyon config aşamasında (sayfalar render
// edilmeden ve public/ kopyalanmadan önce) her kapak için
// public/covers/w/<slug>-{640,960,1280}.webp üretir. Bileşenler varyantın varlığını
// kontrol edip <picture> kullanır; sharp çalışmazsa JPG'ye düşer, build bozulmaz.
// Varyantlar git'e girmez (.gitignore) — her build yeniden/eksikse üretir.
//
// AVIF (2026-11-03): WebP'den ortalama ~%25 küçük (ör. 71 → 54 KB, aynı görünüm). Kodlaması yavaş
// (1280px'te kapak başına ~3 sn), bu yüzden her build'de en fazla AVIF_BUDGET_MS kadar üretilir,
// en yeni kapaktan başlayarak; kalanlar sonraki build'lere kalır (sunucuda günde ~10 build → birkaç günde
// tamamlanır, hiçbir build 30 sn'den fazla uzamaz). Bir kapağın AVIF'i bütün genişliklerde hazır
// olmadan <source type="image/avif"> basılmaz; AVIF desteklemeyen tarayıcı WebP'ye düşer.
import { existsSync } from 'node:fs';
import { mkdir, readdir, stat } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

// 960: telefonların çoğu (375-412px × DPR 1,75-2,6) 640'ı aşıp 1280'i indiriyordu (Lighthouse 2026-11-03).
export const COVER_WIDTHS = [640, 960, 1280];
const AVIF_BUDGET_MS = 30_000;

const variantPath = (slug, w, ext) => join(process.cwd(), 'public', 'covers', 'w', `${slug}-${w}.${ext}`);

/** Var olan WebP varyantlarından srcset; hiçbiri yoksa '' (bileşen JPG'ye düşer). */
export function coverSrcset(slug) {
  return COVER_WIDTHS.filter((w) => existsSync(variantPath(slug, w, 'webp')))
    .map((w) => `/covers/w/${slug}-${w}.webp ${w}w`)
    .join(', ');
}

/** AVIF srcset — yalnız bütün genişlikler hazırsa (yarım set yüksek DPR'de bulanık görsel seçtirirdi). */
export function coverAvifSrcset(slug) {
  if (!COVER_WIDTHS.every((w) => existsSync(variantPath(slug, w, 'avif')))) return '';
  return COVER_WIDTHS.map((w) => `/covers/w/${slug}-${w}.avif ${w}w`).join(', ');
}

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
        const fresh = (target, srcStat) => stat(target).then((s) => s.mtimeMs >= srcStat.mtimeMs, () => false);
        let made = 0;
        const stats = new Map();
        for (const f of files) {
          const slug = f.slice(0, -4);
          const srcStat = await stat(join(src, f));
          stats.set(f, srcStat);
          for (const w of COVER_WIDTHS) {
            const target = join(out, `${slug}-${w}.webp`);
            if (await fresh(target, srcStat)) continue;
            try {
              await sharp(join(src, f)).resize({ width: w, withoutEnlargement: true }).webp({ quality: 72 }).toFile(target);
              made++;
            } catch (e) {
              logger.warn(`${f} → ${w}px üretilemedi: ${e.message}`);
            }
          }
        }
        if (made) logger.info(`kapak varyantı üretildi: ${made} dosya (${files.length} kapak)`);

        // AVIF: süre bütçeli, en yeni kapak önce (yeni yazılar ilk günden hafif açılsın).
        const deadline = Date.now() + AVIF_BUDGET_MS;
        let avif = 0;
        let pending = 0;
        const newestFirst = [...files].sort((a, b) => stats.get(b).mtimeMs - stats.get(a).mtimeMs);
        for (const f of newestFirst) {
          const slug = f.slice(0, -4);
          for (const w of COVER_WIDTHS) {
            const target = join(out, `${slug}-${w}.avif`);
            if (await fresh(target, stats.get(f))) continue;
            if (Date.now() > deadline) {
              pending++;
              continue;
            }
            try {
              await sharp(join(src, f)).resize({ width: w, withoutEnlargement: true }).avif({ quality: 55, effort: 4 }).toFile(target);
              avif++;
            } catch (e) {
              logger.warn(`${f} → ${w}px AVIF üretilemedi: ${e.message}`);
            }
          }
        }
        if (avif || pending) logger.info(`AVIF: ${avif} dosya üretildi${pending ? `, ${pending} sonraki build'lere kaldı` : ''}`);
      },
    },
  };
}
