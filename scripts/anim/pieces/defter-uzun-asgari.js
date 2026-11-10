// =====================================================================
//  EKONOMİ DEFTERİ · UZUN BÖLÜM 3: ASGARİ ÜCRET NASIL BELİRLENİR? (16:9, 1920x1080) — kits/defter.js
//  Sahneler satır başlangıçlarına bağlı (cue); eylemler gerçek kelime zamanına (wAt).
//  Gerçek veri (data/asgari-ucret.json): 2026 brüt 33.030 · net 28.075,50 · işveren (teşviksiz) 40.874,63
//   (SGK işveren %21,75 + işsizlik %2) · destek 1.270/ay · net geçmiş Oca23 8.506,80 / 24 17.002 / 25 22.104 / 26 28.075,50
//   (artış %54,66 / 49 / 30 / 27) · açıklanma 22.12.2022, 27.12.2023, 24.12.2024, 23.12.2025 · TÜFE Ekim 2026 %29,77.
//  Kurallar: 4857 İş K. md. 39; Asgari Ücret Yönetmeliği md. 7 (en geç 2 yılda bir; ölçütler), md. 8 (beşer temsilci,
//   ≥10 üyeyle toplanır, oy çokluğu, eşitlikte başkanın tarafı), md. 11 (Resmî Gazete).
//  Hesaplar: 33.030×0,85=28.075,50 · ×0,14=4.624,20 · ×0,01=330,30 · ×1,2375=40.874,63 · 28.075,50/40.874,63≈0,69 · 33.030/30=1.101
// =====================================================================
BR.capFont = `700 64px ${CAV}`; BR.capText = DF.pen; BR.capStroke = 'rgba(251,250,243,0.95)'; BR.capHi = DF.yellow;
const SCN = ['hook', 'plan', 'a1', 'a4', 'c1', 'c3', 't1', 't3', 'n1', 'n3', 'w1', 'w2b', 'g1', 'g3', 'k1', 'y1', 's1', 's3'];
const sAt = (i) => (i === 0 ? -1.2 : cue(SCN[i]) - 0.15);
const lt = (i) => TT - sAt(i);
const ease = (x) => EZ.io(clamp(x));
function wAt(id, w) {
  const l = L(id), ws = (l.cap || '').toLocaleLowerCase('tr-TR').split(/\s+/), i = ws.findIndex((x) => x.includes(w));
  if (i < 0) return l.t0;
  return l.words && l.words[i] != null ? l.words[i] : l.t0 + (l.t1 - l.t0) * i / ws.length;
}
const KW = (id, w, dd = 0.5) => ease((TT - wAt(id, w)) / dd);
const KS = (id, dd = 0.5, off = 0) => ease((TT - L(id).t0 - off) / dd);
const ON = (id) => TT >= L(id).t0 - 0.15;
const MERT = { hoodie: DF.yellow, seed: 1 };
const GY = 900;
const TAG = 'Ekonomi Defteri · Uzun Bölüm 3';
const PT = (str, t) => pageTitle(str, { no: 3, tag: TAG, prog: clamp(t / 0.6) });
const fade = (k, fn) => { if (k <= 0) return; ctx.save(); ctx.globalAlpha *= k; fn(); ctx.restore(); };
const fmt = (v) => v.toLocaleString('tr-TR', { minimumFractionDigits: v % 1 ? 2 : 0, maximumFractionDigits: 2 });

// ---- bu bölümün eşyaları
function stack(x, y, n, s = 1, seed = 700) { for (let i = 0; i < n; i++) bill(x + (i % 2) * 4 * s, y - i * 14 * s, 1.5 * s, 0, { seed: seed + i }); }
function check(x, y, k, s = 1) { if (k > 0) d([[x - 20 * s, y], [x - 4 * s, y + 18 * s], [x + 28 * s, y - 26 * s]], { w: 7 * s, c: DF.green, prog: k, seed: 271 }); }
function xMark(x, y, r, k) {
  if (k <= 0) return;
  dLine(x - r, y - r, x + r, y + r, { w: 8, c: DF.red, prog: clamp(k * 2), seed: 281 });
  dLine(x + r, y - r, x - r, y + r, { w: 8, c: DF.red, prog: clamp(k * 2 - 1), seed: 282 });
}
function calPage(x, y, w, h, num, label, o = {}) {
  dRect(x, y, w, h, 10, { fill: '#fff', w: 4, seed: o.seed ?? 321 });
  dRect(x, y, w, h * 0.26, 10, { fill: o.top ?? DF.red, w: 4, seed: (o.seed ?? 321) + 1, off: 0 });
  dText(label, x + w / 2, y + h * 0.19, o.ls ?? 40, { c: '#fff' });
  dText(num, x + w / 2, y + h * 0.8, o.ns ?? h * 0.46);
}
function card(x, y, w, h, k, seed, fill = DF.cream) {
  if (k <= 0) return false;
  ctx.save(); ctx.globalAlpha *= k; ctx.translate(x + w / 2, y + h / 2); ctx.scale(0.88 + 0.12 * k, 0.88 + 0.12 * k); ctx.translate(-(x + w / 2), -(y + h / 2));
  dRect(x, y, w, h, 16, { fill, w: 4, seed });
  return true;
}
const endCard = () => ctx.restore();
function seat(x, y, col, k, seed) {   // küçük üye: daire kafa + gövde
  if (k <= 0) return;
  ctx.save(); ctx.globalAlpha *= k;
  dEll(x, y - 58, 22, 22, { fill: DF.skin, w: 3, seed });
  d([[x - 26, y - 30], [x + 26, y - 30], [x + 30, y + 10], [x - 30, y + 10]], { closed: true, fill: col, w: 3, seed: seed + 1 });
  ctx.restore();
}
function group(cx, y, col, label, sub, k, seed) {   // 5 üye yan yana + etiket
  for (let i = 0; i < 5; i++) seat(cx - 140 + i * 70, y, col, clamp(k * 5 - i), seed + i * 3);
  fade(k, () => { dText(label, cx, y + 80, 52); if (sub) dText(sub, cx, y + 130, 40, { c: DF.penSoft }); });
}
function balance(x, y, tilt) {   // terazi; tilt −1..1 (+ = sağ kefe ağır)
  dLine(x, y, x, y - 260, { w: 8, seed: 801 }); dRect(x - 120, y, 240, 24, 8, { fill: DF.kraft, w: 3.4, seed: 802 });
  const a = tilt * 0.16;
  ctx.save(); ctx.translate(x, y - 260); ctx.rotate(a);
  dLine(-380, 0, 380, 0, { w: 8, seed: 803 });
  for (const s of [-1, 1]) { dLine(s * 380, 0, s * 380, 110, { w: 3, c: DF.penSoft, seed: 804 }); dRect(s * 380 - 120, 110, 240, 26, 8, { fill: DF.cream, w: 3.4, seed: 806 + s }); }
  ctx.restore();
  const pan = (s) => [x + Math.cos(a) * s * 380, y - 260 + Math.sin(a) * s * 380 + 110];
  return { left: pan(-1), right: pan(1) };
}
// yatay yığılmış çubuk: parts [{v, c, label}] toplam w genişliğe ölçeklenir; prog soldan dolar
function hbar(x, y, w, h, parts, total, prog, seed = 900) {
  let xx = x;
  parts.forEach((p, i) => {
    const pw = w * p.v / total, k = clamp(prog * parts.length - i);
    if (k <= 0) { xx += pw; return; }
    dRect(xx, y, pw * k, h, 6, { fill: p.c, w: 3.4, seed: seed + i, off: 2 });
    xx += pw;
  });
}

// 0 — açılış: başlık kartı + 28.075,50 etiketi
function sHook(t) {
  titleCard('Asgari ücret nasıl belirlenir?', 'Komisyon, brüt-net, işveren maliyeti', { no: 3, noText: 'UZUN BÖLÜM 3', tsize: 104, prog: clamp((t - 0.3) / 0.7) });
  const k1 = KW('hook', '28.075,50', 0.5), k2 = KW('hook', 'kim,', 0.5);
  fade(k1, () => sticky(110, 780, 330, 150, ['2026 net', '28.075,50 ₺'], { size: 50, c: '#D9F2E4', rot: -0.04 }));
  fade(k2, () => dText('kim? nasıl?', 1630, 860, 70, { c: DF.yellow, rot: 0.06 }));
}
// 1 — bu sayfada
function sPlan(t) {
  paper(); PT('Bu sayfada neler var?', t);
  const items = [['1. Asgari ücret nedir?', 'plan', 'olduğunu,'], ['2. Kim, nasıl belirliyor?', 'plan', 'belirlediğini,'], ['3. Brütten nete', 'plan', 'nete'],
                 ['4. İşverene maliyeti', 'plan', 'maliyetini'], ['5. Geçmiş yıllar', 'plan', 'artışları'], ['6. 2027 ne zaman?', 'plan2', '2027']];
  items.forEach(([s, id, w], i) => {
    const k = KW(id, w, 0.4), y = 300 + i * 105;
    dText(s, 260, y, 72, { align: 'left', al: Math.max(0.25, k) });
    dRect(170, y - 48, 54, 54, 8, { w: 3.4, seed: 330 + i }); check(197, y - 22, k, 1.1);
  });
  kid(1550, GY, 1.15, { ...MERT, pose: 'point', k: KS('plan', 0.6), face: -1, mood: 'happy' });
}
// 2 — en düşük yasal ücret: taban çizgisi
function sFloor(t) {
  paper(); PT('Asgari ücret nedir?', t);
  const kT = KW('a1', 'düşük', 0.6), kX = KW('a1', 'altında', 0.5);
  fade(kT, () => {
    dLine(160, 640, 1300, 640, { w: 10, c: DF.green, seed: 351 });
    hiText('yasal taban', 1080, 610, 60, { c: DF.green, hc: DF.hiG });
    stack(420, 630, 8, 1.0, 360); dText('asgari ücret', 420, 700, 50, { c: DF.penSoft });
  });
  fade(kX, () => { dRect(160, 660, 1140, 200, 10, { fill: 'rgba(227,72,59,0.10)', c: false, seed: 352, off: 0 }); dText('bunun altı yasak', 900, 790, 64, { c: DF.red }); xMark(1180, 770, 44, kX); });
  fade(KW('a2', '39.', 0.5), () => sticky(1400, 240, 420, 150, ['İş Kanunu', 'md. 39'], { size: 54, rot: 0.04 }));
  fade(KW('a2', 'aynıdır;', 0.5), () => sticky(1400, 440, 420, 190, ['herkese aynı:', 'sektör ve şehir', 'fark etmez'], { size: 44, c: '#D9F2E4', rot: -0.03 }));
  fade(KW('a3', 'sgk', 0.5), () => sticky(1400, 680, 420, 150, ['SGK priminin', 'alt sınırı da bu'], { size: 46, c: '#FFD6E4', rot: 0.02 }));
}
// 3 — aylık / günlük
function sDaily(t) {
  paper(); PT('Aylık brüt, günlük = aylık ÷ 30', t);
  const kA = KS('a4', 0.5), kG = KW('a4', 'otuzda', 0.5), kR = KW('a4', '1.101', 0.5);
  if (card(220, 300, 620, 360, kA, 371)) { dText('AYLIK BRÜT', 530, 390, 56, { c: DF.penSoft }); dText('33.030 ₺', 530, 540, 120); dText('2026', 530, 620, 44, { c: DF.penSoft }); endCard(); }
  if (kG > 0) { arrow(870, 480, 1060, 480, { prog: kG, w: 6, head: 22, seed: 372 }); dText('÷ 30', 965, 440, 60, { al: kG }); }
  if (card(1090, 300, 620, 360, kR, 373, '#D9F2E4')) { dText('GÜNLÜK BRÜT', 1400, 390, 56, { c: DF.penSoft }); dText('1.101 ₺', 1400, 540, 120, { c: DF.green }); dText('2026', 1400, 620, 44, { c: DF.penSoft }); endCard(); }
  kid(960, GY, 0.75, { ...MERT, pose: 'think', k: kG, face: 1, mood: kR > 0.3 ? 'happy' : 'calm' });
}
// 4 — komisyon: 3 grup × 5 üye
function sCommission(t) {
  paper(); PT('Asgari Ücret Tespit Komisyonu', t);
  fade(KW('c1', '15', 0.5), () => hiText('15 üye', 960, 270, 90, { hc: DF.hi }));
  group(400, 560, '#9FB8E8', 'Devlet', 'bakanlık + kamu kurumları', KW('c1', 'devletten,', 0.6), 400);
  group(960, 560, DF.yellow, 'İşçi', 'Türk-İş', KW('c1', 'işçi', 0.6), 430);
  group(1520, 560, '#F2A38F', 'İşveren', 'TİSK', KW('c1', 'işveren', 0.6), 460);
  fade(KW('c2', 'türk-iş,', 0.5), () => sticky(700, 760, 520, 120, ['en büyük işçi konfederasyonu'], { size: 38, c: '#FFF08A', rot: -0.02 }));
  fade(KW('c2', 'tisk', 0.5), () => sticky(1260, 760, 560, 120, ['en büyük işveren konfederasyonu'], { size: 38, c: '#FFD6E4', rot: 0.02 }));
}
// 5 — oylama: 10/15; devlet + bir taraf = karar
function sVote(t) {
  paper(); PT('Oylama nasıl işler?', t);
  const k10 = KW('c3', '10', 0.5), kE = KW('c3', 'eşit', 0.5), kJ = KS('c4', 0.8);
  // c4: devlet grubu işçi ya da işveren yanına kayar (örnek gösterim: işverenle)
  const gx = lerp(400, 1240, ease(kJ));
  group(gx, 560, '#9FB8E8', 'Devlet', '', 1, 400);
  group(kJ > 0 ? 400 : 960, 560, DF.yellow, 'İşçi', '', 1, 430);
  group(kJ > 0 ? 1600 : 1520, 560, '#F2A38F', 'İşveren', '', 1, 460);
  fade(k10, () => sticky(150, 230, 520, 150, ['en az 10 üyeyle', 'toplanır'], { size: 48, rot: -0.03 }));
  fade(KW('c3', 'çokluğuyla', 0.5), () => sticky(700, 230, 520, 150, ['oy çokluğuyla', 'karar'], { size: 48, c: '#D9F2E4', rot: 0.02 }));
  fade(kE, () => sticky(1250, 230, 560, 150, ['eşitlikte: başkanın', 'tarafı kazanır'], { size: 46, c: '#FFD6E4', rot: -0.02 }));
  if (kJ > 0.6) { hiText('10 oy → karar', 1420, 840, 72, { c: DF.green, hc: DF.hiG, prog: clamp((kJ - 0.6) / 0.4) }); dText('5 oy', 400, 840, 60, { c: DF.penSoft, al: kJ }); }
  fade(kJ, () => dText('(örnek gösterim)', 960, 930, 40, { c: DF.penSoft }));
}
// 6 — takvim akışı
function sCalendar(t) {
  paper(); PT("Takvim: Aralık'tan Ocak'a", t);
  fade(KW('t1', 'iki', 0.5), () => sticky(140, 240, 600, 150, ['yönetmelik: en geç', 'iki yılda bir'], { size: 48, rot: -0.03 }));
  fade(KW('t1', 'her', 0.5), () => sticky(780, 240, 520, 150, ['son yıllarda:', 'her yıl Aralık'], { size: 48, c: '#D9F2E4', rot: 0.02 }));
  const k1 = KW('t2', 'birkaç', 0.5), k2 = KW('t2', 'resmî', 0.5), k3 = KW('t2', '1', 0.5);
  if (k1 > 0) { calPage(160, 470, 300, 300, '?', 'ARALIK', { seed: 380 }); dText('toplantılar', 310, 830, 48, { c: DF.penSoft }); }
  if (k2 > 0) { arrow(490, 620, 690, 620, { prog: k2, w: 6, head: 22, seed: 381 });
    fade(k2, () => { dRect(720, 470, 420, 300, 10, { fill: '#fff', w: 4, seed: 382 }); dText('RESMÎ', 930, 570, 64, { c: DF.red }); dText('GAZETE', 930, 650, 64, { c: DF.red }); dText('karar yayımlanır', 930, 830, 48, { c: DF.penSoft }); }); }
  if (k3 > 0) { arrow(1170, 620, 1370, 620, { prog: k3, w: 6, head: 22, seed: 383 });
    fade(k3, () => { calPage(1400, 470, 300, 300, '1', 'OCAK', { seed: 384, top: DF.green }); dText('yeni tutar başlar', 1550, 830, 48, { c: DF.green }); }); }
}
// 7 — açıklama tarihleri + ara zam
function sDates(t) {
  paper(); PT('Açıklama günleri', t);
  const D = [['22', '2022'], ['27', '2023'], ['24', '2024'], ['23', '2025']];
  D.forEach(([dd, yy], i) => {
    const k = KW('t3', yy, 0.5); if (k <= 0) return;
    fade(k, () => { calPage(170 + i * 420, 280, 300, 320, dd, `ARALIK ${yy}`, { seed: 390 + i * 3, ls: 34 }); });
  });
  const kA = KW('t4', 'ara', 0.5);
  fade(kA, () => { sticky(420, 690, 1080, 170, ['ara zam: Temmuz 2022 ve Temmuz 2023', '(enflasyon çok yüksekken)'], { size: 50, c: '#FFD6E4', rot: -0.015 }); });
}
// 8 — brüt → net çubuğu
function sNet(t) {
  paper(); PT('Brütten nete (2026)', t);
  const kB = KS('n1', 0.6), kN = KW('n1', 'net', 0.6), kP = KW('n2', 'primleri:', 0.6);
  fade(kB, () => { dText('BRÜT', 160, 340, 56, { align: 'left', c: DF.penSoft }); dText('33.030 ₺', 1760, 340, 64, { align: 'right' }); });
  hbar(160, 370, 1600, 110, [{ v: 33030, c: '#E6EEF8' }], 33030, kB, 901);
  if (kN > 0) {
    hbar(160, 560, 1600, 110, [{ v: 28075.5, c: DF.money }, { v: 4624.2, c: '#F2A38F' }, { v: 330.3, c: '#C7B4F0' }], 33030, Math.max(kN * 0.34, kP), 910);
    fade(kN, () => { dText('NET', 160, 530, 56, { align: 'left', c: DF.green }); hiText('28.075,50 ₺', 760, 640, 76, { c: DF.pen, hc: 'rgba(255,255,255,0.75)' }); });
  }
  fade(KW('n2', 'sgk', 0.5), () => { dText('SGK %14', 1520, 730, 46, { c: DF.red }); });
  fade(KW('n2', 'işsizlik', 0.5), () => { dText('işsizlik %1', 1700, 780, 40, { c: '#7A5BC8' }); });
  fade(KW('n2b', '4.624,20', 0.5), () => sticky(150, 740, 760, 130, ['33.030 × %14 = 4.624,20 ₺', '33.030 × %1 = 330,30 ₺'], { size: 44, rot: -0.02 }));
}
// 9 — vergi istisnası: net = brüt × 0,85
function sTax(t) {
  paper(); PT('Vergi kesilmez', t);
  const kG = KW('n3', 'gelir', 0.5), kD = KW('n3', 'damga', 0.5), kI = KW('n3', 'istisna.', 0.5), kF = KW('n3', '%85', 0.6);
  if (card(200, 280, 600, 160, kG, 931)) { dText('gelir vergisi', 500, 380, 64); xMark(740, 360, 40, kI); endCard(); }
  if (card(200, 480, 600, 160, kD, 932)) { dText('damga vergisi', 500, 580, 64); xMark(740, 560, 40, kI); endCard(); }
  fade(kI, () => dText("2022'den beri istisna", 500, 730, 54, { c: DF.green }));
  fade(kF, () => { dRect(960, 330, 800, 260, 16, { fill: DF.cream, w: 4, seed: 933 }); hiText('net = brüt × 0,85', 1360, 480, 92, { hc: DF.hi, prog: kF }); dText('%14 SGK + %1 işsizlik = %15', 1360, 560, 40, { c: DF.penSoft }); });
  kid(1360, GY, 0.8, { ...MERT, pose: 'cheer', k: kF, face: -1, mood: kF > 0.3 ? 'happy' : 'calm' });
}
// 10 — işveren maliyeti çubuğu
function sEmployer(t) {
  paper(); PT('İşverene maliyeti (2026)', t);
  const kB = KS('w1', 0.6), kS = KW('w1', '%21,75', 0.5), kI = KW('w1', 'işsizlik', 0.5), kT = KW('w2', '40.874,63', 0.6);
  const parts = [{ v: 33030, c: '#E6EEF8' }, { v: 7184.03, c: '#F2A38F' }, { v: 660.6, c: '#C7B4F0' }];
  hbar(160, 420, 1600, 120, parts, 40874.63, kB * 0.34 + kS * 0.33 + kI * 0.33, 940);
  fade(kB, () => dText('brüt 33.030', 160 + 1600 * 33030 / 40874.63 / 2, 500, 48));
  fade(kS, () => dText('SGK %21,75', 160 + 1600 * (33030 + 3592) / 40874.63, 380, 40, { c: DF.red }));
  fade(kI, () => dText('%2', 1735, 380, 40, { c: '#7A5BC8' }));
  fade(kT, () => { hiText('40.874,63 ₺ / ay', 960, 680, 96, { hc: DF.hiP, c: DF.red, prog: kT }); dText('teşvik indirimi olmadan', 960, 760, 46, { c: DF.penSoft }); });
  kid(1660, GY, 0.7, { pose: 'think', k: kT, face: -1, hoodie: '#F2A38F', glasses: false, mood: kT > 0.3 ? 'wow' : 'calm', seed: 40 });
}
// 11 — 100 liranın 69'u + destek
function sShare(t) {
  paper(); PT("Her 100 liranın ~69'u işçiye", t);
  const k = KS('w2b', 0.6);
  for (let i = 0; i < 100; i++) {
    const kk = clamp(k * 100 / 60 - i / 60); if (kk <= 0) continue;
    const x = 220 + (i % 20) * 52, y = 300 + Math.floor(i / 20) * 70;
    dRect(x, y, 40, 54, 6, { fill: i < 69 ? DF.money : '#F2A38F', w: 2.4, seed: 950 + i, off: 1 });
  }
  fade(k, () => { dText('69 → işçinin cebi (net)', 1560, 380, 46, { c: DF.green }); dText('31 → prim ve kesintiler', 1560, 460, 46, { c: DF.red }); });
  fade(KW('w3', 'indirimi', 0.5), () => sticky(1300, 560, 520, 130, ['zamanında prim → indirim'], { size: 42, rot: 0.02 }));
  fade(KW('w3', '1.270', 0.5), () => sticky(1300, 720, 520, 150, ['devlet desteği 2026:', '1.270 ₺ / ay / kişi'], { size: 44, c: '#D9F2E4', rot: -0.02 }));
  fade(k, () => dText('teşviksiz hesap', 740, 700, 40, { c: DF.penSoft }));
}
// 12 — geçmiş yıllar: sütunlar
function sHistory(t) {
  paper(); PT('Net asgari ücret', t);
  const Y = [['Oca 2023', 8506.8, '2023', null], ['2024', 17002, '2024', '%49'], ['2025', 22104, '2025', '%30'], ['2026', 28075.5, '2026', '%27']];
  const base = 860, maxH = 520;
  Y.forEach(([lab, v, w, inc], i) => {
    const k = KW('g1', w, 0.6); if (k <= 0) return;
    const x = 260 + i * 330, h = maxH * v / 28075.5 * ease(k);
    dRect(x, base - h, 200, h, 8, { fill: i === 3 ? DF.money : '#CFE6D4', w: 3.4, seed: 960 + i, off: 2 });
    dText(fmt(v) + ' ₺', x + 100, base - h - 24, 46);
    const incTxt = inc ?? '%54,66', incW = inc ? inc : '%54,66,';
    dText(lab, x + 100, base + 56, 44, { c: DF.penSoft });
    fade(KW('g2', incW, 0.5), () => dText('+' + incTxt, x + 100, base - h - 84, 44, { c: DF.green }));
  });
  fade(KW('g2', 'temmuz', 0.5), () => sticky(1480, 230, 400, 150, ['artış = önceki', 'tutara göre'], { size: 44, rot: 0.03 }));
  fade(KW('g2b', '3,3', 0.5), () => sticky(1480, 420, 400, 150, ['2026 ≈ Oca 2023', '× 3,3'], { size: 48, c: '#D9F2E4', rot: -0.02 }));
}
// 13 — alım gücü: zam vs enflasyon + yıl içinde erime (şema)
function sPower(t) {
  paper(); PT('Asıl soru: alım gücü', t);
  const kZ = KW('g3', '%27;', 0.5), kE = KW('g3', '%29,77.', 0.5), kC = KS('g4', 0.8);
  if (card(160, 260, 460, 220, kZ, 971, '#D9F2E4')) { dText('2026 zammı', 390, 340, 50, { c: DF.penSoft }); dText('%27', 390, 440, 100, { c: DF.green }); endCard(); }
  if (card(660, 260, 460, 220, kE, 972, '#FFD6E4')) { dText('yıllık enflasyon (Ekim 2026)', 890, 340, 38, { c: DF.penSoft }); dText('%29,77', 890, 440, 100, { c: DF.red }); endCard(); }
  fade(kE, () => dText('kaynak: TÜİK', 890, 520, 34, { c: DF.penSoft }));
  if (kC > 0) {
    const v = []; for (let i = 0; i < 12; i++) v.push(0.85 - i * 0.05);
    chart(1220, 820, 560, 420, [{ v, c: DF.red, prog: kC, seed: 973 }]);
    dText('alım gücü', 1300, 380, 46, { c: DF.red, al: kC, align: 'left' });
    dText('Ocak', 1230, 870, 38, { c: DF.penSoft, al: kC }); dText('Aralık', 1760, 870, 38, { c: DF.penSoft, al: kC });
    dText('şema', 1700, 330, 36, { c: DF.penSoft, al: kC, rot: 0.08 });
  }
  kid(430, GY, 0.75, { ...MERT, pose: kC > 0.4 ? 'sad' : 'idle', k: 1, face: 1, mood: kC > 0.4 ? 'sad' : 'calm' });
}
// 14 — neye bakar: ölçütler + terazi
function sCriteria(t) {
  paper(); PT('Komisyon neye bakar?', t);
  const C = [['sosyal ve ekonomik durum', 'sosyal'], ['geçinme indeksleri', 'geçinme'], ['ödenen ücretlerin durumu', 'ücretlerin'], ['geçim şartları', 'geçim']];
  C.forEach(([s, w], i) => fade(KW('k1', w, 0.4), () => sticky(120 + (i % 2) * 520, 240 + Math.floor(i / 2) * 170, 480, 130, [s], { size: 42, c: ['#FFF08A', '#D9F2E4', '#FFD6E4', '#FFF08A'][i], rot: ((i * 3) % 5 - 2) * 0.012 })));
  fade(KW('k2', 'pazarlıkta', 0.5), () => dText('pazarlıkta konuşulanlar:', 640, 650, 46, { c: DF.penSoft }));
  ['geçen yıl enflasyonu', 'beklenen enflasyon', 'ödeme gücü'].forEach((s, i) => fade(KW('k2', ['geçen', 'beklenen', 'ödeyebileceği'][i], 0.4), () => dText('• ' + s, 300, 720 + i * 62, 48, { align: 'left' })));
  const kB = KS('k3', 0.6);
  if (kB > 0) {
    const tl = Math.sin(TT * 1.4) * 0.35 * kB;
    const p = balance(1340, 840, tl);
    dText('alım gücü', p.left[0], p.left[1] - 20, 44, { c: DF.green }); dText('maliyet', p.right[0], p.right[1] - 20, 44, { c: DF.red });
    dText('işçi', p.left[0], p.left[1] + 80, 38, { c: DF.penSoft }); dText('işveren', p.right[0], p.right[1] + 80, 38, { c: DF.penSoft });
    fade(KW('k3', 'devlet', 0.5), () => dText('devlet: ikisi + bütçe', 1340, 470, 48));
  }
}
// 15 — 2027: tahmin yok
function s2027(t) {
  paper(); PT('2027 ne zaman belli olur?', t);
  const kA = KS('y1', 0.5), kT = KW('y2', 'tahmin', 0.5), kS = KW('y2', 'parafomo.com', 0.6);
  fade(kA, () => { calPage(220, 280, 380, 400, '?', 'ARALIK 2026', { seed: 980, ls: 36 }); dText('komisyon toplanır', 410, 740, 46, { c: DF.penSoft }); });
  fade(kT, () => { sticky(720, 300, 480, 150, ['tahmin yok'], { size: 72, c: '#FFD6E4', rot: -0.04 }); });
  if (card(720, 520, 920, 260, kS, 981, '#D9F2E4')) {
    dText('parafomo.com/asgari-ucret-hesaplama', 1180, 610, 50, { c: DF.green });
    dText('açıklanınca güncellenir: brüt, net, işveren maliyeti', 1180, 700, 38, { c: DF.penSoft }); endCard();
  }
  kid(1790, GY, 0.7, { ...MERT, pose: 'think', k: kA, face: -1, mood: 'calm' });
}
// 16 — özet
function sSummary(t) {
  paper(); PT('Özet', t);
  const S = [['15 üyeli komisyon', 's1', '15'], ['oy çokluğuyla karar', 's1', 'çokluğuyla'], ['Resmî Gazete → 1 Ocak', 's1', 'resmî'],
             ['net = brüt × 0,85', 's2', '%85'], ['işveren ≈ brüt × 1,24', 's2', '1,24'], ['2027: Aralık\'ta', 's1', 'başlar.']];
  S.forEach(([s, id, w], i) => {
    const k = KW(id, w, 0.5), x = 150 + (i % 3) * 560, y = 270 + Math.floor(i / 3) * 290;
    fade(k, () => sticky(x, y, 500, 140, [s], { size: s.length > 20 ? 42 : 50, c: ['#FFF08A', '#FFD6E4', '#D9F2E4'][i % 3], rot: ((i * 7) % 5 - 2) * 0.015 }));
  });
}
// 17 — kapanış
function sCta(t) {
  paper(); const a = clamp(t / 0.5);
  hiText('parafomo.com', 960, 290, 120, { prog: clamp((t - 0.3) / 0.6), hc: DF.hiG });
  dText('/asgari-ucret-hesaplama', 960, 390, 70, { c: DF.penSoft, al: a });
  const k4 = KS('s4', 0.6);
  if (k4 > 0) {
    dText('sonraki sayfa:', 700, 560, 70, { c: DF.penSoft, al: k4 }); hiText('KİRA ARTIŞI', 1130, 560, 100, { c: DF.red, prog: k4, hc: DF.hiP });
    const b = clamp(spring(Math.max(0, TT - L('s4').t0 - 0.3), 0.9, { k: 200, damp: 0.45 }));
    if (b > 0.01) { ctx.save(); ctx.translate(960, 760); ctx.scale(b, b);
      ctx.fillStyle = BR.red; ctx.beginPath(); ctx.roundRect(-210, -58, 420, 116, 20); ctx.fill();
      ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.moveTo(-150, -24); ctx.lineTo(-150, 24); ctx.lineTo(-110, 0); ctx.closePath(); ctx.fill();
      ctx.font = `56px ${ANTON}`; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText('ABONE OL', -86, 4); ctx.restore(); }
  }
  kid(1600, GY, 1.0, { ...MERT, pose: 'cheer', k: clamp((t - 0.2) / 0.5), face: -1, mood: 'happy' });
}
// kapak (1280x720'e küçülür)
function drawThumb() {
  paper({ tint: '#F6F1DA' });
  for (let i = 0; i < 5; i++) seat(260 + i * 90, 820, '#9FB8E8', 1, 400 + i * 3);
  for (let i = 0; i < 5; i++) seat(260 + i * 90, 600, DF.yellow, 1, 430 + i * 3);
  for (let i = 0; i < 5; i++) seat(260 + i * 90, 380, '#F2A38F', 1, 460 + i * 3);
  priceTag(820, 420, 1.2, '?', { swing: 0, c: DF.red });
  hiText('ASGARİ ÜCRET', 1360, 400, 170, { c: DF.pen, hc: DF.hi });
  hiText('KİM BELİRLER?', 1360, 640, 150, { c: DF.red, hc: DF.hiP });
  dText('brüt → net → işveren', 1360, 820, 80, { c: DF.penSoft });
}
const SDRAW = [sHook, sPlan, sFloor, sDaily, sCommission, sVote, sCalendar, sDates, sNet, sTax, sEmployer, sShare, sHistory, sPower, sCriteria, s2027, sSummary, sCta];
const curI = () => { let i = 0; for (let k = 0; k < SCN.length; k++) if (TT >= sAt(k)) i = k; return i; };
function drawPiece() {
  if (THUMB) { drawThumb(); return; }
  const i = curI(), fx = i > 0 ? clamp((TT - sAt(i)) / 0.45) : 1;
  if (fx < 1) { SDRAW[i - 1](lt(i - 1)); ctx.save(); ctx.globalAlpha = fx; ctx.translate(0, (1 - EZ.o3(fx)) * 100); }
  SDRAW[i](lt(i));
  if (fx < 1) ctx.restore();
  overlayGrain('multiply', 0.55);
}
function drawOverlay() { if (THUMB) return; const i = curI(); if (i > 0) captions(1010); }
