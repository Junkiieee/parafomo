// =====================================================================
//  EKONOMİ DEFTERİ #4: FAİZ NEDİR? (Short, 9:16) — kits/defter.js. Pazar uzun bölümün habercisi.
//  Tutarlar ÖRNEK: 10.000 ₺ · yıllık %40 → 1 yıl 14.000 · 2 yıl bileşik 14.000 × 1,4 = 19.600 (basit olsaydı 18.000).
// =====================================================================
BR.capFont = `700 86px ${CAV}`; BR.capText = DF.pen; BR.capStroke = 'rgba(251,250,243,0.95)'; BR.capHi = DF.yellow;
const SCN = ['hook', 'rent', 'rate', 'comp', 'key', 'cta'];
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
const fade = (k, fn) => { if (k <= 0) return; ctx.save(); ctx.globalAlpha *= k; fn(); ctx.restore(); };
const MERT = { hoodie: DF.yellow, seed: 1 };
function house(x, y, s = 1) {
  dRect(x - 70 * s, y - 110 * s, 140 * s, 110 * s, 4 * s, { fill: '#F4D9B0', w: 3.4 * s, seed: 211 });
  d([[x - 92 * s, y - 104 * s], [x, y - 180 * s], [x + 92 * s, y - 104 * s]], { closed: true, fill: DF.red, w: 3.4 * s, seed: 212 });
  dRect(x - 18 * s, y - 60 * s, 36 * s, 60 * s, 3 * s, { fill: DF.green, w: 3 * s, seed: 213 });
}
function stack(x, y, n, s = 1, seed = 700) { for (let i = 0; i < n; i++) bill(x + (i % 2) * 4 * s, y - i * 14 * s, 1.5 * s, 0, { seed: seed + i }); }
const fmt = (v) => Math.round(v).toLocaleString('tr-TR');

// 0 — başlık kartı
function sHook(t) {
  titleCard('Faiz nedir?', 'Paranın kirası', { no: 4, prog: clamp((t - 0.3) / 0.7) });
  bank(820, 480, 0.55, { label: 'BANKA' });
  priceTag(300, 430, 0.85, '%', { swing: 0.07, c: DF.red });
}
// 1 — kira = faiz: Mert bankaya verir (kirayı banka öder) / bankadan alır (kirayı Mert öder)
function sRent(t) {
  paper(); pageTitle('Faiz = paranın kirası', { no: 4, prog: clamp(t / 0.6), size: 92 });
  const kH = KW('rent', 'kirasıdır', 0.5);
  fade(kH, () => { house(230, 640, 0.9); dText('kira', 230, 720, 48, { c: DF.penSoft }); dText('=', 400, 600, 90, { c: DF.penSoft }); stack(560, 640, 6, 0.8, 300); dText('faiz', 560, 720, 48, { c: DF.penSoft }); });
  bank(560, 1400, 1.0, { label: 'BANKA' });
  const kY = KW('rent', 'yatırırsa', 0.5), kC = KW('rent', 'çekerse', 0.5);
  const m = kid(190, 1400, 1.1, { ...MERT, pose: 'give', k: Math.max(kY, kC), face: 1, mood: kC > 0.3 ? 'sad' : kY > 0.3 ? 'happy' : 'calm' });
  if (kY > 0 && kC < 0.5) { const mt = ease((TT - wAt('rent', 'yatırırsa')) / 0.8); bill(lerp(m.hand[0], 420, Math.min(mt, 1)), lerp(m.hand[1], 1180, Math.min(mt, 1)) - Math.sin(Math.min(mt, 1) * Math.PI) * 100, 1.0, mt * 0.4);
    hiText('kirayı banka öder', 540, 960, 64, { c: DF.green, prog: KW('rent', 'banka', 0.5), hc: DF.hiG }); }
  if (kC > 0) { const mt = ease((TT - wAt('rent', 'çekerse')) / 0.8); bill(lerp(420, m.hand[0], Math.min(mt, 1)), lerp(1180, m.hand[1], Math.min(mt, 1)) - Math.sin(Math.min(mt, 1) * Math.PI) * 100, 1.0, mt * 0.4);
    hiText('kirayı Mert öder', 540, 1060, 64, { c: DF.red, prog: KW('rent', 'mert', 0.5), hc: DF.hiP }); }
  dText('10.000 ₺ · örnek', 880, 1000, 42, { c: DF.penSoft, rot: 0.08 });
}
// 2 — %40: 10.000 → 14.000
function sRate(t) {
  paper(); pageTitle('Yıllık %40 ne demek?', { no: 4, prog: clamp(t / 0.6), size: 92 });
  const k = KW('rate', '10.000', 0.5), kk = KW('rate', '4.000', 0.6);
  fade(k, () => { stack(300, 980, 10, 1.0, 320); dText('10.000 ₺', 300, 1060, 60); });
  if (kk > 0) { arrow(440, 820, 640, 820, { prog: kk, w: 6, head: 22, c: DF.green, seed: 331 }); clock(540, 640, 90, { speed: 0.5 }); dText('1 yıl', 540, 500, 48, { c: DF.penSoft }); }
  fade(kk, () => { stack(790, 980, 14, 1.0, 340); dText('14.000 ₺', 790, 1060, 60, { c: DF.green }); hiText('+4.000 ₺ kira', 790, 1150, 66, { c: DF.green, hc: DF.hiG }); });
  kid(540, 1400, 0.9, { ...MERT, pose: 'cheer', k: kk, face: 1, mood: kk > 0.3 ? 'happy' : 'calm' });
  dText('örnek', 900, 500, 44, { c: DF.penSoft, rot: 0.1 });
}
// 3 — bileşik: 14.000 × %40 = 5.600 → 19.600 (basit 18.000)
function sComp(t) {
  paper(); pageTitle('Faizin faizi', { no: 4, prog: clamp(t / 0.6) });
  const k1 = KS('comp', 0.5), k2 = KW('comp', '5.600', 0.5), k3 = KW('comp', '19.600', 0.5), k4 = KW('comp', 'bileşik', 0.5);
  fade(k1, () => { stack(260, 900, 10, 0.9, 360); dText('10.000', 260, 960, 50); dText('0. yıl', 260, 1020, 40, { c: DF.penSoft }); });
  fade(k1, () => { stack(540, 900, 14, 0.9, 380); dText('14.000', 540, 960, 50); dText('1. yıl', 540, 1020, 40, { c: DF.penSoft }); });
  fade(k2, () => { sticky(640, 380, 380, 150, ['14.000 × %40', '= 5.600 ₺'], { size: 50, c: '#D9F2E4', rot: 0.04 }); });
  fade(k3, () => { stack(820, 900, 20, 0.9, 400); dText('19.600', 820, 960, 50, { c: DF.green }); dText('2. yıl', 820, 1020, 40, { c: DF.penSoft }); });
  if (k3 > 0.9) { dText('basit olsaydı 18.000', 540, 1120, 46, { c: DF.penSoft, al: clamp((TT - wAt('comp', '19.600') - 0.6) / 0.5) }); }
  if (k4 > 0) hiText('bileşik faiz', 540, 1230, 92, { c: DF.red, prog: k4, hc: DF.hiP });
  kid(180, 1400, 0.85, { ...MERT, pose: 'think', k: 1, face: 1, mood: k3 > 0.5 ? 'wow' : 'calm' });
}
// 4 — politika faizi: TCMB → bankalar → kredi pahalı / mevduat cazip
function sKey(t) {
  paper(); pageTitle('Hepsinin referansı', { no: 4, prog: clamp(t / 0.6) });
  bank(540, 760, 0.9, { label: 'TCMB' });
  const kP = KW('key', 'politika', 0.5), kK = KW('key', 'kredi', 0.5), kM = KW('key', 'mevduat', 0.5);
  fade(kP, () => dText('politika faizi', 540, 860, 56, { c: DF.penSoft }));
  [250, 540, 830].forEach((x, i) => { bank(x, 1130, 0.42, { label: 'BANKA' }); if (kP > 0) arrow(540, 770, x, 990, { prog: kP, w: 4, c: DF.penSoft, seed: 420 + i }); });
  fade(kK, () => sticky(80, 1180, 420, 150, ['kredi', 'pahalanır ↑'], { size: 54, c: '#FFD6E4', rot: -0.04 }));
  fade(kM, () => sticky(580, 1180, 420, 150, ['mevduat', 'cazipleşir ↑'], { size: 54, c: '#D9F2E4', rot: 0.04 }));
}
// 5 — kapanış: Pazar uzun bölüm + ABONE OL
function sCta(t) {
  paper(); const a = clamp(t / 0.5);
  dText('Mevduat, kredi,', 560, 520, 96, { al: a }); dText('reel faiz, dolar:', 560, 640, 96, { al: a });
  hiText('Pazar 12:00', 560, 820, 130, { c: DF.red, prog: clamp((t - 0.3) / 0.6) });
  dText('uzun bölüm', 560, 930, 80, { c: DF.penSoft, al: a });
  hiText('parafomo.com', 560, 1080, 96, { prog: clamp((t - 0.7) / 0.6), hc: DF.hiG });
  kid(870, 1400, 0.9, { ...MERT, pose: 'cheer', k: clamp((t - 0.2) / 0.5), face: -1, mood: 'happy' });
  const b = clamp(spring(Math.max(0, t - 0.2), 0.9, { k: 200, damp: 0.45 }));
  if (b > 0.01) { ctx.save(); ctx.translate(440, 1260); ctx.scale(b, b);
    ctx.fillStyle = BR.red; ctx.beginPath(); ctx.roundRect(-210, -58, 420, 116, 20); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.moveTo(-150, -24); ctx.lineTo(-150, 24); ctx.lineTo(-110, 0); ctx.closePath(); ctx.fill();
    ctx.font = `56px ${ANTON}`; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText('ABONE OL', -86, 4); ctx.restore(); }
}
const SDRAW = [sHook, sRent, sRate, sComp, sKey, sCta];
const curI = () => { let i = 0; for (let k = 0; k < SCN.length; k++) if (TT >= sAt(k)) i = k; return i; };
function drawPiece() {
  const i = curI(), fx = i > 0 ? clamp((TT - sAt(i)) / 0.4) : 1;
  if (fx < 1) { SDRAW[i - 1](lt(i - 1)); ctx.save(); ctx.globalAlpha = fx; ctx.translate(0, (1 - EZ.o3(fx)) * 160); }
  SDRAW[i](lt(i));
  if (fx < 1) ctx.restore();
  overlayGrain('multiply', 0.55);
}
function drawOverlay() { const i = curI(); if (i > 0 && i < 5) captions(1540); }
