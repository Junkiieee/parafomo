#!/usr/bin/env node
// Kodla çizilmiş animasyonu (canvas) kare kare MP4'e çevirir.
//   node scripts/anim/render.mjs <page.html> <frames> <fps> <out.mp4>
// Sayfa window.renderFrame(f) sunmalı; her kare JPEG olarak ffmpeg'e borulanır (diske PNG yazılmaz).
// Sunucuyu yormamak için çağıran taraf `nice -n 19 ionice -c3` ve /tmp/shorts_frames.lock kullanır.
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.ANIM_NODE || '/root/.cache/parafomo/anim-node/node_modules/playwright-core');

const [page_, framesS, fpsS, out] = process.argv.slice(2);
const frames = +framesS, fps = +fpsS;
if (!page_ || !frames || !fps || !out) { console.error('kullanım: render.mjs <page.html> <frames> <fps> <out.mp4>'); process.exit(2); }

const ff = spawn('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(fps),
  '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-threads', '1', out],
  { stdio: ['pipe', 'inherit', 'inherit'] });

const browser = await chromium.launch({ args: ['--disable-gpu', '--renderer-process-limit=1'] });
try {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', (e) => { console.error('[anim] sayfa hatası:', e.message); process.exitCode = 1; });
  await page.goto(pathToFileURL(page_).href);
  await page.waitForFunction(() => window.ANIM_READY === true, null, { timeout: 30000 });
  const t0 = Date.now();
  for (let f = 0; f < frames; f++) {
    const b64 = await page.evaluate((i) => window.renderFrame(i), f);
    if (!ff.stdin.write(Buffer.from(b64, 'base64'))) await new Promise((r) => ff.stdin.once('drain', r));
    if (f % 150 === 0) console.log(`[anim] kare ${f}/${frames} (${((Date.now() - t0) / 1000).toFixed(0)} sn)`);
  }
} finally {
  await browser.close();
  ff.stdin.end();
}
const code = await new Promise((r) => ff.on('close', r));
if (code !== 0) { console.error('[anim] ffmpeg hata kodu', code); process.exit(1); }
console.log('[anim] ✅', out);
