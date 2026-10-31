// =====================================================================
//  EKONOMİ DEFTERİ #3: %30 İNDİRİM GERÇEK Mİ? — kits/defter.js
//  Örnek: kulaklık 1.000 ₺ → 11.11'den 2 hafta önce 1.500 ₺ (%50 zam) → 11.11'de %30 indirim = 1.050 ₺.
//  1.050 / 1.000 − 1 = %5 pahalı. Zam 1.000'e (+500), indirim 1.500'e (−450) uygulanır. Tutarlar ÖRNEK.
// =====================================================================
BR.capFont = `700 86px ${CAV}`; BR.capText = DF.pen; BR.capStroke = 'rgba(251,250,243,0.95)'; BR.capHi = DF.yellow;
const SCN = ['hook', 'price', 'sale', 'compare', 'rule', 'tip', 'cta'];
const sAt = (i) => (i === 0 ? -1.2 : cue(SCN[i]) - 0.15);
const lt = (i) => TT - sAt(i);
const ease = (x) => EZ.io(clamp(x));
function wAt(id, w) {
  const l = L(id), ws = (l.cap || '').toLocaleLowerCase('tr-TR').split(/\s+/), i = ws.findIndex((x) => x.includes(w));
  if (i < 0) return l.t0;
  return l.words && l.words[i] != null ? l.words[i] : l.t0 + (l.t1 - l.t0) * i / ws.length;
}
const MERT = { hoodie: DF.yellow, seed: 1 };

// ---- bu bölümün proplari
function headphones(x, y, s = 1, o = {}) {   // (x, y) = kulak yastıklarının ortası
  const P = []; for (let i = 0; i <= 24; i++) { const a = Math.PI + i / 24 * Math.PI; P.push([x + Math.cos(a) * 112 * s, y - 10 * s + Math.sin(a) * 130 * s]); }
  d(P, { w: 18 * s, c: '#3B4252', seed: 201 });
  dRect(x - 156 * s, y - 40 * s, 84 * s, 140 * s, 32 * s, { fill: o.c ?? DF.red, w: 3.6 * s, seed: 203 });
  dRect(x + 72 * s, y - 40 * s, 84 * s, 140 * s, 32 * s, { fill: o.c ?? DF.red, w: 3.6 * s, seed: 204 });
  dRect(x - 84 * s, y - 18 * s, 22 * s, 96 * s, 9 * s, { fill: '#3B4252', w: 3 * s, seed: 205, off: 0 });
  dRect(x + 62 * s, y - 18 * s, 22 * s, 96 * s, 9 * s, { fill: '#3B4252', w: 3 * s, seed: 206, off: 0 });
}
function burst(x, y, r, k, l1, l2) {   // kırmızı yıldız "İNDİRİM" damgası
  if (k <= 0.01) return;
  ctx.save(); ctx.translate(x, y); ctx.scale(k, k); ctx.rotate(-0.1);
  const P = []; for (let i = 0; i < 26; i++) { const a = i / 26 * TAU, rr = i % 2 ? r * 0.8 : r; P.push([Math.cos(a) * rr, Math.sin(a) * rr]); }
  d(P, { closed: true, fill: DF.red, w: 4, seed: 210 });
  dText(l1, 0, r * 0.1, r * 0.62, { c: '#fff' });
  if (l2) dText(l2, 0, r * 0.48, r * 0.3, { c: '#fff' });
  ctx.restore();
}
// fiyat etiketi: eski fiyat çizilir, yeni fiyat kırmızı yazılır
function tagPrices(x, y, s, oldP, newP, cut, nw, o = {}) {
  priceTag(x, y, s, '', { swing: 0.04 });
  ctx.save(); ctx.translate(x, y); ctx.rotate(0.04 * Math.sin(TT * TAU * 0.9));
  dText(oldP, 26 * s, 64 * s, 44 * s, { c: nw > 0.5 ? DF.penSoft : DF.pen });
  if (cut > 0) dLine(-40 * s, 54 * s, -40 * s + 132 * s * cut, 36 * s, { w: 5 * s, c: DF.red, seed: o.seed ?? 55 });
  if (nw > 0) dText(newP, 100 * s, -22 * s, 64 * s, { c: o.nc ?? DF.red, al: nw, rot: -0.12 });
  ctx.restore();
}
function phone(x, y, s = 1) {   // (x, y) = ekranın sol üstü; 300x520 @1
  dRect(x - 20 * s, y - 50 * s, 340 * s, 620 * s, 40 * s, { fill: '#30343F', w: 4 * s, seed: 220 });
  ctx.fillStyle = DF.cream; ctx.fillRect(x, y, 300 * s, 520 * s);
  dLine(x + 120 * s, y - 25 * s, x + 180 * s, y - 25 * s, { w: 6 * s, c: '#5B6170', seed: 221 });
}

// 0 — başlık kartı
function sHook(t) {
  titleCard('%30 indirim gerçek mi?', 'Önce zam, sonra indirim', { no: 3, prog: clamp((t - 0.3) / 0.7) });
  headphones(820, 470, 0.65);
  burst(260, 430, 95, clamp(spring(Math.max(0, t - 0.2), 0.9, { k: 160, damp: 0.5 })), '%30', 'İNDİRİM');
}
// 1 — fiyat 1.000 → 1.500 (11.11'den 2 hafta önce)
function sPrice(t) {
  paper(); pageTitle('Kulaklığın fiyatı', { no: 3, prog: clamp(t / 0.6) });
  headphones(540, 690, 1.5);
  const cut = clamp((TT - wAt('price', '1.500')) / 0.5), nw = clamp((TT - wAt('price', '1.500') - 0.3) / 0.5);
  tagPrices(740, 1090, 1.5, '1.000 ₺', '1.500 ₺', cut, nw);
  const kS = ease((TT - wAt('price', 'hafta')) / 0.5);
  if (kS > 0) { ctx.save(); ctx.globalAlpha = kS; sticky(110, 420, 330, 170, ["11.11'e", '2 hafta var'], { size: 56, c: '#FFD6E4', rot: -0.05 }); ctx.restore(); }
  for (let i = 0; i < 2; i++) arrow(1000, 1220 - i * 120, 1000, 1120 - i * 120, { prog: ease((TT - wAt('price', '1.500') - 0.2 - i * 0.2) / 0.4), c: DF.red, w: 6, head: 20, seed: 60 + i * 3 });
  dText('örnek', 900, 470, 50, { c: DF.penSoft, rot: 0.1 });
  kid(200, 1400, 0.85, { ...MERT, pose: 'think', k: 1, face: 1, mood: nw > 0.3 ? 'wow' : 'happy' });
}
// 2 — 11.11: %30 İNDİRİM damgası, 1.500 → 1.050
function sSale(t) {
  paper(); pageTitle('11.11 geldi!', { no: 3, prog: clamp(t / 0.6) });
  headphones(400, 760, 1.2);
  const tB = wAt('sale', '%30'), kB = clamp(spring(Math.max(0, TT - tB + 0.15), 0, { k: 180, damp: 0.45 }));
  burst(800, 640, 170, TT > tB - 0.15 ? kB : 0, '%30', 'İNDİRİM');
  const cut = clamp((TT - wAt('sale', '1.050')) / 0.4), nw = clamp((TT - wAt('sale', '1.050') - 0.2) / 0.5);
  tagPrices(560, 1020, 1.5, '1.500 ₺', '1.050 ₺', cut, nw, { nc: DF.green, seed: 57 });
  const kC = ease((TT - wAt('sale', 'kocaman')) / 0.5);
  kid(880, 1400, 0.85, { ...MERT, pose: 'cheer', k: kC, face: -1, mood: kC > 0.3 ? 'happy' : 'calm' });
}
// 3 — üç sütun: önce 1.000 · zamlı 1.500 · indirimli 1.050 → +%5
function sCompare(t) {
  paper(); pageTitle('İki hafta önceye bak', { no: 3, prog: clamp(t / 0.6) });
  const base = 1300, k = 0.5, xs = [110, 340, 570], ww = 190;
  const g = [ease((TT - wAt('compare', 'iki')) / 0.7), ease((t - 0.1) / 0.7), ease((TT - wAt('compare', 'indirimli')) / 0.7)];
  const v = [1000, 1500, 1050], fills = [DF.money, '#F4B7A6', DF.yellow], labs = ['2 hafta önce', 'zamlı', '11.11'];
  dLine(70, base, 790, base, { w: 4, seed: 153 });
  for (let i = 0; i < 3; i++) {
    const h = v[i] * k * g[i];
    if (g[i] > 0) dRect(xs[i], base - h, ww, Math.max(h, 1), 8, { fill: fills[i], w: 4, seed: 151 + i });
    if (g[i] > 0.9) dText(`${v[i].toLocaleString('tr-TR')} ₺`, xs[i] + ww / 2, base - h - 26, 56, { c: i === 1 ? DF.penSoft : DF.pen });
    dText(labs[i], xs[i] + ww / 2, base + 64, 50, { c: DF.penSoft });
  }
  const kP = ease((TT - wAt('compare', 'pahalı')) / 0.5);
  if (kP > 0) {
    dLine(xs[0], base - 1000 * k, xs[2] + ww + 20, base - 1000 * k, { w: 3, c: DF.red, prog: kP, seed: 156 });
    marker(xs[2], base - 1000 * k - 25 * 0.5 - 1, ww, 25, { prog: kP, c: DF.hiP });
    hiText('+%5 pahalı', xs[2] + ww / 2 + 60, base - 1050 * k - 110, 72, { c: DF.red, prog: kP, hc: DF.hiP });
  }
  if (g[1] > 0.5 && g[2] > 0.5) dLine(xs[1] + 10, base - 1500 * k + 20, xs[1] + ww - 10, base - 20, { w: 5, c: DF.red, prog: clamp((TT - wAt('compare', 'indirimli') - 0.4) / 0.5), seed: 158 });
  kid(930, 1400, 0.8, { ...MERT, pose: 'sad', k: kP, face: -1, mood: kP > 0.3 ? 'sad' : 'wow' });
}
// 4 — kural: yüzdeler aynı tabana uygulanmaz
function sRule(t) {
  paper(); pageTitle('Yüzdenin tabanı', { no: 3, prog: clamp(t / 0.6) });
  const k1 = ease((TT - wAt('rule', 'zam')) / 0.5), k2 = ease((TT - wAt('rule', 'indirim')) / 0.5), k3 = ease((TT - wAt('rule', 'indirim') - 1.3) / 0.5);
  dText('aynı taban değil!', 540, 470, 70, { c: DF.red, al: clamp((t - 0.3) / 0.5), rot: -0.03 });
  if (k1 > 0) { dText('zam:', 300, 640, 66, { al: k1, c: DF.penSoft, align: 'right' }); hiText('1.000 × %50 = +500', 340, 640, 76, { prog: k1, hc: DF.hiP, align: 'left' }); }
  if (k2 > 0) { dText('indirim:', 300, 800, 66, { al: k2, c: DF.penSoft, align: 'right' }); hiText('1.500 × %30 = −450', 340, 800, 76, { prog: k2, hc: DF.hiG, align: 'left' }); }
  if (k3 > 0) {
    dLine(160, 860, 960, 860, { w: 4, prog: k3, seed: 171 });
    dText('fark:', 300, 960, 66, { al: k3, c: DF.penSoft, align: 'right' }); hiText('+50 ₺ = %5 zam', 340, 960, 84, { c: DF.red, prog: k3, align: 'left' });
  }
  sticky(120, 1080, 520, 200, ['%50 zam + %30 indirim', '≠ eski fiyat'], { size: 54, c: '#FFF08A', rot: -0.03 });
  kid(860, 1400, 0.85, { ...MERT, pose: k2 > 0 ? 'point' : 'think', k: k2, face: -1, mood: k3 > 0.3 ? 'wow' : 'calm' });
}
// 5 — ipucu: fiyat geçmişi + ekran görüntüsü
function sTip(t) {
  paper(); pageTitle('Alışverişten önce', { no: 3, prog: clamp(t / 0.6) });
  const px = 140, py = 480, s = 1.05;
  phone(px, py, s);
  dText('fiyat geçmişi', px + 150 * s, py + 60 * s, 46, { c: DF.penSoft });
  const kG = ease((TT - wAt('tip', 'geçmişine')) / 1.2);
  const vals = [1000, 1000, 1000, 1500, 1500, 1050], X0 = px + 25 * s, X1 = px + 275 * s, Yb = py + 440 * s;
  const P = vals.map((v, i) => [X0 + (X1 - X0) * i / 5, Yb - (v - 800) * 0.42 * s]);
  dLine(X0, Yb, X1, Yb, { w: 3, seed: 230 });
  if (kG > 0) d(P, { w: 6, c: DF.red, prog: kG, seed: 231, amp: 0.8 });
  if (kG > 0.95) { dText('1.000', P[0][0] + 20, P[0][1] - 18, 36); dText('1.500', P[3][0] + 10, P[3][1] - 18, 36, { c: DF.red }); dText('1.050', P[5][0] - 4, P[5][1] - 18, 36, { c: DF.green, align: 'right' }); }
  const tE = wAt('tip', 'ekran'), fl = clamp((TT - tE) / 0.12) * (1 - clamp((TT - tE - 0.15) / 0.35));
  if (fl > 0) { ctx.save(); ctx.globalAlpha = fl * 0.9; ctx.fillStyle = '#fff'; ctx.fillRect(px, py, 300 * s, 520 * s); ctx.restore(); }
  const kS = ease((TT - tE - 0.3) / 0.5);
  if (kS > 0) { ctx.save(); ctx.globalAlpha = kS; sticky(560, 560, 400, 210, ['ekran görüntüsü', 'kaydedildi ✓'], { size: 54, c: '#C9F2DD', rot: 0.04 }); ctx.restore(); }
  kid(800, 1400, 0.9, { ...MERT, pose: 'point', k: ease((TT - wAt('tip', 'bak')) / 0.5), face: -1, mood: 'happy' });
}
// 6 — kapanış + ABONE OL
function sCta(t) {
  paper(); const a = clamp(t / 0.5);
  dText('Etikete değil,', 560, 560, 120, { al: a }); dText('fiyat geçmişine', 560, 700, 110, { al: a });
  hiText('bak', 560, 860, 160, { c: DF.red, prog: clamp((t - 0.3) / 0.6) });
  hiText('parafomo.com', 560, 1040, 100, { prog: clamp((t - 0.7) / 0.6), hc: DF.hiG });
  dText('sonraki sayfa →', 560, 1420, 70, { c: DF.penSoft, al: clamp((t - 1.0) / 0.5) });
  kid(870, 1400, 0.9, { ...MERT, pose: 'cheer', k: clamp((t - 0.2) / 0.5), face: -1, mood: 'happy' });
  const b = clamp(spring(Math.max(0, t - 0.2), 0.9, { k: 200, damp: 0.45 }));
  if (b > 0.01) { ctx.save(); ctx.translate(440, 1240); ctx.scale(b, b);
    ctx.fillStyle = BR.red; ctx.beginPath(); ctx.roundRect(-210, -58, 420, 116, 20); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.moveTo(-150, -24); ctx.lineTo(-150, 24); ctx.lineTo(-110, 0); ctx.closePath(); ctx.fill();
    ctx.font = `56px ${ANTON}`; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText('ABONE OL', -86, 4); ctx.restore(); }
}
const SDRAW = [sHook, sPrice, sSale, sCompare, sRule, sTip, sCta];
const curI = () => { let i = 0; for (let k = 0; k < SCN.length; k++) if (TT >= sAt(k)) i = k; return i; };
function drawPiece() {
  const i = curI(), fx = i > 0 ? clamp((TT - sAt(i)) / 0.4) : 1;
  if (fx < 1) { SDRAW[i - 1](lt(i - 1)); ctx.save(); ctx.globalAlpha = fx; ctx.translate(0, (1 - EZ.o3(fx)) * 160); }   // yeni kâğıt alttan kayar
  SDRAW[i](lt(i));
  if (fx < 1) ctx.restore();
  overlayGrain('multiply', 0.55);
}
function drawOverlay() { const i = curI(); if (i > 0 && i < 6) captions(1540); }
