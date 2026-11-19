// ParaFOMO — video/sosyal hattının iç dosyalarını yayından çıkarır.
//
// public/social/ hem sitede kullanılan görselleri (og kartları .png, Instagram'ın URL'den çektiği
// -ig.jpg ve Reel .mp4) hem de hattın kendi kayıtlarını tutuyor: short-*.json (sunucu yolları,
// QA notları, video kimlikleri) ve .srt altyazılar. Bu kayıtlar betiklerce yerelden okunur
// (public/social/...), hiçbir sayfa ya da dış servis URL'den istemez; ama dist/'e kopyalanıp
// herkese açık yayınlanıyordu (~660 dosya, denetim 2026-11-03). Build bitince dist/'ten silinir;
// public/ ve git'teki asılları olduğu gibi kalır.
import { readdir, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const STRIP = /\.(?:json|srt)$/i;

async function walk(dir) {
  let removed = 0;
  let entries;
  try {
    entries = await readdir(dir, { withFileTypes: true });
  } catch {
    return 0;
  }
  for (const e of entries) {
    const p = join(dir, e.name);
    if (e.isDirectory()) removed += await walk(p);
    else if (STRIP.test(e.name)) {
      await rm(p, { force: true });
      removed++;
    }
  }
  return removed;
}

export default function stripPipelineFiles() {
  return {
    name: 'parafomo-strip-pipeline-files',
    hooks: {
      'astro:build:done': async ({ dir, logger }) => {
        const n = await walk(join(fileURLToPath(dir), 'social'));
        if (n) logger.info(`dist/social: hattın iç kayıtları yayından çıkarıldı (${n} dosya)`);
      },
    },
  };
}
