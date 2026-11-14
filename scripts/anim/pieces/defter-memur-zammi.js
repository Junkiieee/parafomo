// =====================================================================
//  EKONOMİ DEFTERİ #7: MEMUR ZAMMI NASIL HESAPLANIR? (Short, 9:16) — kits/defter.js
//  Kaynak: 8. Dönem Toplu Sözleşme, Kamu Görevlileri Hakem Kurulu (RG 27.08.2025): 2026 2. yarı %7, 2027 1. yarı %5
//  (src/data/zam2027.ts). TÜFE aylık (data/tufe-aylik.json): Tem 1,78 · Ağu 1,84 · Eyl 1,84 · Eki 2,58 → birikimli %8,28.
//  Örnek (etiketli): 6 ay %12 → fark 1,12 ÷ 1,07 − 1 = %4,67 → Ocak (1,0467 × 1,05) − 1 = %9,91. Ocak oranı TAHMİN EDİLMEZ.
// =====================================================================
BR.capFont = `700 86px ${CAV}`; BR.capText = DF.pen; BR.capStroke = 'rgba(251,250,243,0.95)'; BR.capHi = DF.yellow;
const SCN = ['hook', 'iki', 'ts', 'fark', 'carp', 'kesin', 'cta'];
const sAt = (i) => (i === 0 ? -1.2 : cue(SCN[i]) - 0.15);
const lt = (i) => TT - sAt(i);
const ease = (x) => EZ.io(clamp(x));
function wAt(id, w, nth = 0) {
  const l = L(id), ws = (l.cap || '').toLocaleLowerCase('tr-TR').split(/\s+/);
  let i = -1; for (let k = 0, c = 0; k < ws.length; k++) if (ws[k].includes(w)) { if (c === nth) { i = k; break; } c++; }
  if (i < 0) return l.t0;
  return l.words && l.words[i] != null ? l.words[i] : l.t0 + (l.t1 - l.t0) * i / ws.length;
}
const KW = (id, w, dd = 0.5, nth = 0) => ease((TT - wAt(id, w, nth)) / dd);
const fade = (k, fn) => { if (k <= 0) return; ctx.save(); ctx.globalAlpha *= k; fn(); ctx.restore(); };
const dashed = (fn) => { ctx.save(); ctx.setLineDash([18, 14]); fn(); ctx.restore(); };
const MEMUR = '#6C8FD8';

// 0 — başlık kartı
function sHook(t) {
  titleCard('Memur zammı', 'nasıl hesaplanır?', { no: 7, prog: clamp((t - 0.3) / 0.7) });
  priceTag(830, 430, 0.85, '%', { swing: 0.07, c: DF.red });
}
// 1 — Ocak zammı = 2 parça
function sIki(t) {
  paper(); pageTitle('Ocak zammı: 2 parça', { no: 7, prog: clamp(t / 0.6), size: 92 });
  // "iki" denince iki numaralı boş not belirir; yazılar söylendikçe üstüne açılır (sahne boş beklemesin)
  const kN = KW('iki', 'iki', 0.4), k1 = KW('iki', 'toplu', 0.5), k2 = KW('iki', 'enflasyon', 0.5);
  const N1 = [100, 520, 420, 330], N2 = [560, 560, 420, 330], o1 = { size: 78, c: '#FFF08A', rot: -0.05 }, o2 = { size: 78, c: '#FFD6E4', rot: 0.05 };
  fade(kN, () => { sticky(...N1, ['1'], o1); sticky(...N2, ['2'], o2); });
  fade(k1, () => sticky(...N1, ['1', 'toplu', 'sözleşme'], o1));
  fade(k2, () => sticky(...N2, ['2', 'enflasyon', 'farkı'], o2));
  kid(540, 1430, 0.85, { pose: k2 > 0.3 ? 'point' : 'think', k: 1, face: 1, mood: 'calm', seed: 5, hoodie: MEMUR });
}
// 2 — toplu sözleşme: 2026 2. yarı %7, 2027 1. yarı %5
function sTs(t) {
  paper(); pageTitle('Toplu sözleşme', { no: 7, prog: clamp(t / 0.6) });
  dRect(140, 450, 800, 640, 10, { fill: '#fff', w: 4, seed: 801 });
  dText('8. Dönem Toplu Sözleşme', 540, 550, 62, { c: DF.pen });
  dText('Hakem Kurulu kararı, 2025', 540, 615, 44, { c: DF.penSoft, weight: 500 });
  dLine(210, 655, 870, 655, { w: 3, seed: 802 });
  const k7 = KW('ts', '%7', 0.5), k5 = KW('ts', '%5', 0.5);
  fade(k7, () => { dText('2026 · 2. yarı', 220, 790, 66, { align: 'left' }); hiText('%7', 800, 790, 110, { c: DF.red, prog: k7 }); });
  fade(k5, () => { dText('2027 · 1. yarı', 220, 960, 66, { align: 'left' }); hiText('%5', 800, 960, 110, { c: DF.red, prog: k5, hc: DF.hiG }); });
  kid(860, 1440, 0.7, { pose: 'point', k: k7, face: -1, mood: 'calm', seed: 6, hoodie: MEMUR });
}
// 3 — enflasyon farkı: Temmuz–Aralık birikimli çubuk, %7 çizgisi; Tem–Eki gerçek dilimler (bileşik) = %8,28
const AY = [['Tem', 1.78], ['Ağu', 1.84], ['Eyl', 1.84], ['Eki', 2.58]];
const SEG = (() => { let c = 1, prev = 0; return AY.map(([ad, m]) => { c *= 1 + m / 100; const cum = (c - 1) * 100, s = { ad, h: cum - prev, top: cum }; prev = cum; return s; }); })();
function sFark(t) {
  paper(); pageTitle('Enflasyon farkı', { no: 7, prog: clamp(t / 0.6) });
  const X0 = 250, BW = 230, Y0 = 1320, K = 58, yOf = (p) => Y0 - p * K;
  const y7 = yOf(7), yTop = yOf(12.6);
  const kF = KW('fark', 'temmuz', 0.5), k7 = KW('fark', '%7', 0.5), kA = KW('fark', 'aşarsa', 0.5), kE = KW('fark', 'eklenir', 0.5);
  const kG = clamp((TT - wAt('fark', 'temmuz', 1)) / 1.4), k83 = KW('fark', '%8,3', 0.5);
  // çerçeve: 6 ay (Kas, Ara henüz yok → kesikli, "?")
  fade(kF, () => {
    dashed(() => dRect(X0, yTop, BW, Y0 - yTop, 6, { w: 3.4, c: DF.penSoft, seed: 811 }));
    dText('?', X0 + BW / 2, yTop + 90, 70, { c: DF.penSoft });
    dText('Temmuz → Aralık', X0 + BW / 2, Y0 + 70, 50, { c: DF.penSoft });
  });
  // Tem–Eki gerçek dilimler, sırayla dolar
  SEG.forEach((s, i) => {
    const p = clamp(kG * SEG.length - i); if (p <= 0) return;
    const yb = yOf(s.top - s.h), yt = yb - s.h * K * ease(p);
    dRect(X0 + 8, yt, BW - 16, yb - yt, 4, { fill: i % 2 ? '#FFD978' : DF.yellow, w: 3, seed: 820 + i, off: 3 });
    if (p > 0.6) dText(s.ad, X0 - 20, (yb + yt) / 2 + 16, 44, { c: DF.pen, align: 'right' });
  });
  // %7 çizgisi
  fade(k7, () => {
    ctx.save(); ctx.strokeStyle = DF.red; dashed(() => dLine(X0 - 40, y7, 980, y7, { w: 5, c: DF.red, seed: 830 })); ctx.restore();
    dText('sözleşme %7', 960, y7 + 60, 54, { c: DF.red, align: 'right' });
  });
  // %7'nin üstü = fark
  if (kA > 0) marker(X0 + 4, (y7 + yTop) / 2, BW - 8, y7 - yTop - 10, { prog: kA, c: DF.hiP, seed: 9 });
  fade(kA, () => { arrow(700, y7 - 190, X0 + BW + 20, (y7 + yTop) / 2, { w: 5, head: 20, c: DF.pen, seed: 840, bend: -20 }); hiText('aşan kısım = fark', 760, y7 - 210, 60, { hc: DF.hiP }); });
  fade(kE, () => sticky(590, 430, 380, 150, ['Ocak maaşına', 'eklenir'], { size: 54, c: '#FFF08A', rot: 0.04 }));
  // Tem–Eki gerçek: %8,3
  fade(k83, () => { dLine(X0 + BW + 10, yOf(SEG[3].top), 610, yOf(SEG[3].top), { w: 3, c: DF.pen, seed: 850 }); hiText('4 ayda %8,3', 790, yOf(SEG[3].top) + 18, 70, { c: DF.pen, hc: DF.hi, prog: k83 }); });
}
// 4 — toplanmaz, çarpılır + ÖRNEK hesap
function sCarp(t) {
  paper(); pageTitle('Toplanmaz, çarpılır', { no: 7, prog: clamp(t / 0.6), size: 92 });
  const kT = KW('carp', 'toplanmaz', 0.4), kC = KW('carp', 'çarpılır', 0.4), kO = KW('carp', 'örnek', 0.4);
  const k12 = KW('carp', '%12', 0.5), kF = KW('carp', '%4,67', 0.5), kZ = KW('carp', '%9,91', 0.6);
  fade(kT, () => { dText('+', 310, 605, 300, { c: DF.pen }); dLine(240, 450, 420, 630, { w: 9, c: DF.red, seed: 860 }); dLine(420, 450, 240, 630, { w: 9, c: DF.red, seed: 861 }); });
  fade(kC, () => { dEll(730, 540, 115, 115, { w: 7, c: DF.green, seed: 862 }); dText('×', 710, 605, 300, { c: DF.green }); });
  // ÖRNEK damgası
  fade(kO, () => { ctx.save(); ctx.translate(840, 740); ctx.rotate(-0.12); dRect(-140, -52, 280, 104, 10, { w: 5, c: DF.red, seed: 863 }); dText('ÖRNEK', 0, 26, 74, { c: DF.red }); ctx.restore(); });
  fade(k12, () => dText('6 ay enflasyon: %12', 130, 880, 66, { align: 'left' }));
  fade(kF, () => dText('fark: 1,12 ÷ 1,07 → %4,67', 130, 1010, 66, { align: 'left' }));
  fade(kZ, () => hiText('Ocak: 1,0467 × 1,05 → %9,91', 130, 1150, 66, { align: 'left', prog: kZ, hc: DF.hiG }));
  kid(880, 1450, 0.62, { pose: kZ > 0.3 ? 'cheer' : 'think', k: 1, face: -1, mood: kZ > 0.3 ? 'happy' : 'calm', seed: 7, hoodie: MEMUR });
}
// 5 — kesin oran: Aralık enflasyonu → Ocak; memur emeklisi aynı oran
function sKesin(t) {
  paper(); pageTitle('Kesin oran ne zaman?', { no: 7, prog: clamp(t / 0.6), size: 90 });
  const kR = KW('kesin', 'aralık', 0.5), kB = KW('kesin', 'belli', 0.5), kM = KW('kesin', 'emeklisi', 0.5);
  fade(kR, () => { dRect(100, 480, 400, 300, 8, { fill: DF.cream, w: 4, seed: 871 }); dText('ARALIK', 300, 590, 66, { c: DF.red }); dText('enflasyonu', 300, 670, 54); dText('açıklanır', 300, 740, 46, { c: DF.penSoft }); });
  if (kB > 0) arrow(510, 630, 590, 630, { prog: kB, w: 6, head: 22, seed: 872 });
  fade(kB, () => { dRect(600, 480, 380, 300, 8, { fill: '#fff', w: 4, seed: 873 }); dRect(600, 480, 380, 70, 8, { fill: DF.red, w: 4, seed: 874 }); dText('OCAK', 790, 535, 50, { c: '#fff' }); dText('kesin zam', 790, 690, 70); });
  fade(kM, () => sticky(150, 900, 520, 170, ['memur emeklisi:', 'aynı oran'], { size: 60, c: '#D9F2E4', rot: -0.03 }));
  kid(820, 1440, 0.75, { pose: kM > 0.3 ? 'cheer' : 'idle', k: kM, face: -1, mood: kM > 0.3 ? 'happy' : 'calm', seed: 8, hair: '#C9C4BC', glasses: true, hoodie: '#8FB996' });
}
// 6 — kapanış: hesaplayıcı + ABONE OL
function sCta(t) {
  paper(); const a = clamp(t / 0.5);
  dText('Güncel tahmin ve', 560, 520, 96, { al: a }); dText('kendi maaşın:', 560, 640, 96, { al: a });
  hiText('parafomo.com', 560, 820, 120, { c: DF.red, prog: clamp((t - 0.3) / 0.6) });
  dText('memur zammı hesaplayıcısı', 560, 940, 70, { c: DF.penSoft, al: a });
  kid(870, 1400, 0.9, { pose: 'cheer', k: clamp((t - 0.2) / 0.5), face: -1, mood: 'happy', seed: 1, hoodie: MEMUR });
  const b = clamp(spring(Math.max(0, t - 0.2), 0.9, { k: 200, damp: 0.45 }));
  if (b > 0.01) { ctx.save(); ctx.translate(440, 1260); ctx.scale(b, b);
    ctx.fillStyle = BR.red; ctx.beginPath(); ctx.roundRect(-210, -58, 420, 116, 20); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.moveTo(-150, -24); ctx.lineTo(-150, 24); ctx.lineTo(-110, 0); ctx.closePath(); ctx.fill();
    ctx.font = `56px ${ANTON}`; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText('ABONE OL', -86, 4); ctx.restore(); }
}
const SDRAW = [sHook, sIki, sTs, sFark, sCarp, sKesin, sCta];
const curI = () => { let i = 0; for (let k = 0; k < SCN.length; k++) if (TT >= sAt(k)) i = k; return i; };
function drawPiece() {
  const i = curI(), fx = i > 0 ? clamp((TT - sAt(i)) / 0.4) : 1;
  if (fx < 1) { SDRAW[i - 1](lt(i - 1)); ctx.save(); ctx.globalAlpha = fx; ctx.translate(0, (1 - EZ.o3(fx)) * 160); }
  SDRAW[i](lt(i));
  if (fx < 1) ctx.restore();
  overlayGrain('multiply', 0.55);
}
function drawOverlay() { const i = curI(); if (i > 0 && i < SCN.length - 1) captions(1540); }
