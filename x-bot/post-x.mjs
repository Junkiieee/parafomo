#!/usr/bin/env node
/**
 * ParaFOMO — X (Twitter) yerel paylaşım botu.
 *
 * Local makinede çalışır. Senin GERÇEK, kalıcı tarayıcı profilinle (bir kez elle
 * giriş yaparsın) X'e girer ve siteden (RSS) gelen EN YENİ yazıyı paylaşır.
 * İnsan temposu: rastgele gecikmeler, tuş tuş yazma. Günde tek paylaşım, dedup'lı.
 *
 * NOT: Tarayıcı otomasyonu X kullanım şartlarına aykırıdır; düşük hacim + gerçek
 * oturum riski azaltır ama sıfırlamaz. Sorumluluk kullanıcıdadır.
 *
 * Komutlar:
 *   node post-x.mjs --login   → tarayıcıyı aç, X'e elle giriş yap, pencereyi kapat
 *   node post-x.mjs --dry     → tweet'i derle ve YAZDIR (paylaşmaz)
 *   node post-x.mjs           → en yeni yazıyı paylaş (henüz paylaşılmadıysa)
 */
import { chromium } from 'playwright';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';

const __dir = dirname(fileURLToPath(import.meta.url));
const PROFILE_DIR = join(__dir, '.profile');       // kalıcı oturum (gitignore'lu)
const POSTED_FILE = join(__dir, 'posted.json');    // dedup kaydı (gitignore'lu)
const RSS_URL = 'https://parafomo.com/rss.xml';
const SITE = 'parafomo.com';

const args = process.argv.slice(2);
const MODE = args.includes('--login') ? 'login'
  : args.includes('--plan') ? 'plan'
  : args.includes('--dry') ? 'dry' : 'post';

// --- yardımcılar ---
const rnd = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const jitter = (base, spread) => sleep(rnd(base, base + spread));
const log = (...a) => console.log(`[${new Date().toLocaleTimeString('tr-TR')}]`, ...a);

function loadPosted() {
  try { return JSON.parse(readFileSync(POSTED_FILE, 'utf8')); } catch { return []; }
}
function savePosted(list) {
  writeFileSync(POSTED_FILE, JSON.stringify(list.slice(-200), null, 2));
}

// --- RSS'ten yazıları çek ---
function parseItem(item) {
  const pick = (tag) => {
    const m = item.match(new RegExp(`<${tag}>([\\s\\S]*?)</${tag}>`));
    return m ? decode(m[1].replace(/<!\[CDATA\[|\]\]>/g, '').trim()) : '';
  };
  const cats = [...item.matchAll(/<category>([\s\S]*?)<\/category>/g)].map((m) => decode(m[1].trim()));
  return { title: pick('title'), link: pick('link'), description: pick('description'), categories: cats };
}
async function allPosts() {
  const res = await fetch(RSS_URL, { headers: { 'User-Agent': 'Mozilla/5.0' } });
  const xml = await res.text();
  return xml.split('<item>').slice(1).map(parseItem).filter((p) => p.title && p.link);
}
async function latestPost() {
  return (await allPosts())[0] || {};
}
function decode(s) {
  return s.replace(/&apos;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, '&')
          .replace(/&lt;/g, '<').replace(/&gt;/g, '>');
}

// --- tweet metnini derle (<=280, link ~23 sayılır) ---
function buildTweet(post) {
  const tagWords = { faiz: '#faiz', enflasyon: '#enflasyon', dolar: '#dolar', altın: '#altın',
    borsa: '#borsa', kripto: '#kripto', Fed: '#Fed', ekonomi: '#ekonomi', temettü: '#temettü',
    PCE: '#PCE', ABD: '', euro: '#euro' };
  const tags = [];
  for (const c of post.categories) {
    const t = tagWords[c];
    if (t && !tags.includes(t)) tags.push(t);
    if (tags.length >= 2) break;
  }
  if (!tags.includes('#finans')) tags.push('#finans');
  const hashtags = tags.slice(0, 3).join(' ');

  const LINK_COST = 23;
  const base = `${post.title}\n\n`;
  const tail = `\n\n${post.link}\n${hashtags}`;
  const tailLen = 1 + 1 + LINK_COST + 1 + hashtags.length; // \n\n + link(23) + \n + tags
  let hook = post.description;
  const budget = 280 - base.length - tailLen - 2;
  if (hook.length > budget) hook = hook.slice(0, Math.max(0, budget - 1)).replace(/\s+\S*$/, '') + '…';
  return `${post.title}\n\n${hook}\n\n${post.link}\n${hashtags}`;
}

// --- insan gibi yazma ---
async function humanType(page, locator, text) {
  for (const ch of text) {
    await locator.pressSequentially(ch, { delay: rnd(35, 95) });
    if (ch === ' ' && Math.random() < 0.12) await sleep(rnd(150, 600)); // ara ara duraksa
    if (ch === '\n') await sleep(rnd(200, 500));
  }
}

async function launch(headless) {
  // channel:'chrome' → bundled Chromium yerine kurulu gerçek Chrome (daha az bot sinyali)
  // args/ignoreDefaultArgs → Playwright'in "ben otomasyonum" sinyalini (navigator.webdriver,
  // --enable-automation infobar) kaldırır; X'in otomasyon tespitini zorlaştırır.
  const opts = {
    headless,
    viewport: { width: 1280, height: 860 },
    locale: 'tr-TR',
    timezoneId: 'Europe/Istanbul',
    args: ['--disable-blink-features=AutomationControlled', '--start-maximized'],
    ignoreDefaultArgs: ['--enable-automation'],
  };
  let ctx;
  try {
    ctx = await chromium.launchPersistentContext(PROFILE_DIR, { ...opts, channel: 'chrome' });
  } catch {
    log('Chrome bulunamadı, bundled Chromium kullanılıyor.');
    ctx = await chromium.launchPersistentContext(PROFILE_DIR, opts);
  }
  // navigator.webdriver vb. izleri her sayfada gizle (ek güvence)
  await ctx.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    // eklenti/dil sinyalleri gerçekçi olsun
    Object.defineProperty(navigator, 'languages', { get: () => ['tr-TR', 'tr', 'en-US'] });
  });
  return ctx;
}

async function isLoggedIn(page) {
  await page.goto('https://x.com/home', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await sleep(rnd(2500, 5000));
  return page.url().includes('/home');
}

// --- mod: login ---
async function doLogin() {
  const ctx = await launch(false);
  const page = ctx.pages()[0] || await ctx.newPage();
  await page.goto('https://x.com/login', { waitUntil: 'domcontentloaded' });
  log('Tarayıcı açıldı. X hesabına GİRİŞ YAP. Giriş bitince bu pencereyi kapat.');
  log('(Oturum .profile klasörüne kaydedilecek; bir daha giriş istemez.)');
  // pencere kapanana kadar bekle
  await new Promise((resolve) => ctx.on('close', resolve));
  log('Oturum kaydedildi. Artık "node post-x.mjs" ile paylaşım yapabilirsin.');
}

// --- mod: post ---
async function doPost(dry) {
  const post = await latestPost();
  if (!post.title || !post.link) { log('RSS okunamadı/boş, çıkılıyor.'); return; }

  const posted = loadPosted();
  if (posted.includes(post.link)) { log('En yeni yazı zaten paylaşılmış:', post.link); return; }

  const text = buildTweet(post);
  log('Hazırlanan tweet (' + text.length + ' karakter):\n----\n' + text + '\n----');
  if (dry) { log('--dry modu: paylaşılmadı.'); return; }

  // çalışmaya başlamadan önce rastgele bekle (sabit saat = bot sinyali)
  const warm = rnd(5, 40);
  log(`İnsan temposu: ${warm} dk rastgele bekleme...`);
  await sleep(warm * 60 * 1000);

  const ctx = await launch(false);
  const page = ctx.pages()[0] || await ctx.newPage();
  try {
    if (!(await isLoggedIn(page))) {
      log('GİRİŞ YOK. Önce: node post-x.mjs --login');
      await ctx.close(); return;
    }
    await sleep(rnd(2000, 6000));

    // biraz "gez" — doğrudan compose yerine ana akışta dur
    await page.mouse.wheel(0, rnd(200, 600));
    await jitter(1500, 3000);

    const box = page.locator('[data-testid="tweetTextarea_0"]').first();
    await box.click();
    await jitter(600, 1500);
    await humanType(page, box, text);
    await jitter(1500, 4000);

    // Gönder butonu (inline) — bazı arayüzlerde tweetButton
    const btn = page.locator('[data-testid="tweetButtonInline"], [data-testid="tweetButton"]').first();
    await btn.waitFor({ state: 'visible', timeout: 15000 });
    await jitter(800, 2000);
    await btn.click();

    await sleep(rnd(4000, 8000));
    posted.push(post.link);
    savePosted(posted);
    log('✅ Paylaşıldı ve kaydedildi:', post.link);
  } catch (e) {
    log('HATA:', e.message);
  } finally {
    await sleep(rnd(1500, 3000));
    await ctx.close();
  }
}

// --- mod: plan (tarayıcı yok; tüm yazılar için tweet metni döker → X'te elle planla) ---
async function doPlan() {
  const posts = await allPosts();
  console.log(`# ParaFOMO — Planlanacak tweet'ler (${posts.length} yazı)\n`);
  console.log('Her birini X "Planlanmış gönderi" ile farklı gün/saate koy (günde 1 öneri).\n');
  posts.forEach((p, i) => {
    console.log(`──────── ${i + 1}/${posts.length} ────────`);
    console.log(buildTweet(p));
    console.log('');
  });
}

(async () => {
  if (MODE === 'login') return doLogin();
  if (MODE === 'plan') return doPlan();
  return doPost(MODE === 'dry');
})();
