// =====================================================================
//  EKONOMİ DEFTERİ #1: ENFLASYON NASIL OLUR? — kits/defter.js
//  Sahneler satır başlangıçlarına bağlı (cue); eylemler gerçek kelime zamanına (wAt).
//  Tutarlar ÖRNEK (10 → 15 ₺), ekranda "örnek" yazar; istatistik iddiası yok.
// =====================================================================
BR.capFont = `700 86px ${CAV}`; BR.capText = DF.pen; BR.capStroke = 'rgba(251,250,243,0.95)'; BR.capHi = DF.yellow;
const SCN = ['hook', 'trade', 'money', 'same', 'price', 'chart', 'cta'];
const sAt = (i) => (i === 0 ? -1.2 : cue(SCN[i]) - 0.15);
const lt = (i) => TT - sAt(i);
const ease = (x) => EZ.io(clamp(x));
function wAt(id, w) {
  const l = L(id), ws = (l.cap || '').toLocaleLowerCase('tr-TR').split(/\s+/), i = ws.findIndex((x) => x.includes(w));
  if (i < 0) return l.t0;
  return l.words && l.words[i] != null ? l.words[i] : l.t0 + (l.t1 - l.t0) * i / ws.length;
}
const MERT = { hoodie: DF.yellow, seed: 1 };

// 0 — defter kapağı: "EKONOMİ DEFTERİ · sayfa 1"
function sHook(t) {
  titleCard('Enflasyon nasıl olur?', 'Simit neden her yıl pahalanıyor?', { no: 1, prog: clamp((t - 0.3) / 0.7) });
  simit(820, 480, 1.4, 5);
  priceTag(600, 470, 0.7, TT > wAt('hook', 'pahalan') + 0.3 ? '15 ₺' : '10 ₺', { swing: 0.06 });
}
// 1 — alışveriş: Mert simitçiye para verir, simidi alır
function sTrade(t) {
  paper(); pageTitle('Her şey bir alışveriş', { no: 1, prog: clamp(t / 0.6) });
  const tA = wAt('trade', 'mert'), tM = wAt('trade', '10'), tB = wAt('trade', 'karşılığında');
  const walkK = ease((TT - sAt(1)) / Math.max(0.8, tA - sAt(1) + 0.4)), ax = lerp(-160, 290, walkK);
  const giveK = ease((TT - tM + 0.4) / 0.4), takeK = ease((TT - tB) / 0.4);
  const bk = clamp((TT - tB + 0.5) / 0.4) * (1 - clamp((TT - tB - 1.2) / 0.4));
  const vendor = kid(800, 1230, 1.05, { pose: 'give', k: ease(bk), face: -1, hoodie: '#F4F4F0', hair: '#8A8A8A', glasses: false, mood: 'happy', seed: 2 });
  simitCart(800, 1400, 1.0);
  sticky(130, 400, 300, 170, ['örnek fiyat:', 'simit 10 ₺'], { size: 54 });
  const mert = kid(ax, 1400, 1.3, { ...MERT, pose: walkK < 1 ? 'walk' : 'give', k: giveK * (1 - takeK * 0.6), face: 1, mood: TT > tB ? 'happy' : 'calm' });
  const mt = ease((TT - tM) / 0.8);
  if (TT > tM - 0.4 && mt < 1) bill(lerp(mert.hand[0], vendor.hand[0], mt), lerp(mert.hand[1], vendor.hand[1], mt) - Math.sin(mt * Math.PI) * 150, 1.0, mt * 0.6);
  if (mt >= 1) bill(vendor.handB[0] - 10, vendor.handB[1] + 6, 0.6, 0.3);
  const bt = ease((TT - tB) / 0.8);
  if (TT > tB - 0.3) simit(lerp(vendor.hand[0], mert.hand[0] + 20, bt), lerp(vendor.hand[1], mert.hand[1], bt) - Math.sin(bt * Math.PI) * 120, 0.8, 7);
  if (TT > tM) hiText('para →', 600, 660, 96, { c: DF.red, prog: clamp((TT - tM) / 0.4), hc: DF.hiP });
  if (TT > tB) hiText('← simit', 600, 770, 96, { c: DF.green, prog: clamp((TT - tB) / 0.4), hc: DF.hiG });
}
// 2 — ceplere daha çok para: bankadan para yağar, herkes sevinir
function sMoney(t) {
  paper(); pageTitle('Ceplerde daha çok para', { no: 1, prog: clamp(t / 0.6) });
  bank(540, 800, 1.05, { label: 'KREDİ' });
  const xs = [190, 420, 660, 890], hoods = [DF.green, '#F29BB8', '#8DB8E8', DF.yellow];
  for (let i = 0; i < 26; i++) {
    const t0 = wAt('money', 'cebine') - sAt(2) + i * 0.1, u = (t - t0) / 1.3; if (u < 0 || u > 1.6) continue;
    const r = mulberry32(i * 7 + 3), tx = xs[i % 4] + (r() - 0.5) * 60;
    bill(lerp(540 + (r() - 0.5) * 200, tx, Math.min(u, 1)), lerp(820, 1060, Math.min(u, 1)), 0.55, Math.sin(u * 6 + i) * 0.5, { seed: i });
  }
  xs.forEach((x, i) => {
    const k = ease((TT - wAt('money', 'para') + 0.6 - i * 0.25) / 0.5);
    kid(x, 1400, 0.9, { pose: 'cheer', k, face: i % 2 ? -1 : 1, hoodie: hoods[i], hair: i === 1 ? '#7A4A2A' : DF.hair, glasses: i === 3, mood: k > 0.3 ? 'happy' : 'calm', seed: 20 + i });
  });
}
// 3 — ama simit aynı: tablada 5 simit, kuyruk uzar
function sSame(t) {
  paper(); pageTitle('Ama simit aynı', { no: 1, prog: clamp(t / 0.6) });
  simitCart(300, 1400, 0.95, { n: 5 });
  sticky(110, 420, 340, 170, ['hâlâ', '5 simit'], { size: 64, c: '#FFD6E4' });
  const hoods = ['#8DB8E8', DF.green, DF.yellow, '#F29BB8', '#C7B4F0'];
  for (let i = 0; i < 5; i++) {
    const k = ease((t - 0.1 - i * 0.3) / 1.2), x = lerp(1300 + i * 80, 570 + i * 105, k);
    kid(x, 1400 + (i % 2) * 18, 0.78, { pose: k < 1 ? 'walk' : 'idle', face: -1, hoodie: hoods[i], glasses: i === 2, mood: k >= 1 ? 'wow' : 'calm', seed: 40 + i });
  }
}
// 4 — fiyat yükselir: etiket 10'dan 15'e
function sPrice(t) {
  paper(); pageTitle('Fiyat yükselir', { no: 1, prog: clamp(t / 0.6) });
  simit(540, 1120, 3.0, 51);
  priceTag(540, 620, 1.9, '', { swing: 0.04 });
  const cut = clamp((TT - wAt('price', 'yükselir')) / 0.5), nw = clamp((TT - wAt('price', '15')) / 0.5);
  ctx.save(); ctx.translate(540, 620); ctx.rotate(0.04 * Math.sin(TT * TAU * 0.9));
  dText('10 ₺', 40, 136, 110, { c: nw > 0.5 ? DF.penSoft : DF.pen });
  if (cut > 0) dLine(-90, 100, -90 + 220 * cut, 66, { w: 9, c: DF.red, seed: 55 });
  if (nw > 0) dText('15 ₺', 130, 20, 130, { c: DF.red, al: nw, rot: -0.12 });
  ctx.restore();
  for (let i = 0; i < 3; i++) arrow(250 + i * 290, 1400, 250 + i * 290 + 40, 1280, { prog: ease((TT - wAt('price', 'yükselir') - 0.3 - i * 0.2) / 0.5), c: DF.red, w: 6, seed: 60 + i * 3 });
  dText('örnek', 900, 470, 54, { c: DF.penSoft, rot: 0.1 });
  const m = kid(170, 1400, 0.85, { ...MERT, pose: 'sad', k: nw, face: 1, mood: nw > 0.3 ? 'sad' : 'wow' });
}
// 5 — grafik: para hızlı, mal yavaş → aradaki fark enflasyon
function sChart(t) {
  paper(); pageTitle('Enflasyon = para > mal', { no: 1, prog: clamp(t / 0.6) });
  const p1 = ease((TT - wAt('chart', 'para,')) / 1.6), p2 = ease((TT - wAt('chart', 'maldan')) / 1.6);
  const para = [0.08, 0.16, 0.27, 0.4, 0.55, 0.72, 0.9], mal = [0.08, 0.13, 0.18, 0.23, 0.28, 0.33, 0.38];
  const X = 160, Y = 1320, Wc = 780, Hc = 760, gap = clamp((TT - wAt('chart', 'fiyatlar')) / 0.6);
  if (gap > 0) {   // aradaki alan: fosforla boyanır
    ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.globalAlpha = gap; ctx.beginPath();
    para.forEach((v, i) => { const x = X + i / 6 * Wc, y = Y - v * Hc; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    for (let i = 6; i >= 0; i--) ctx.lineTo(X + i / 6 * Wc, Y - mal[i] * Hc);
    ctx.closePath(); ctx.fillStyle = DF.hi; ctx.fill(); ctx.restore();
    dText('enflasyon', X + Wc * 0.74, Y - 0.40 * Hc, 80, { c: DF.pen, al: gap, rot: -0.35 });
  }
  chart(X, Y, Wc, Hc, [{ v: para, c: DF.red, prog: p1, label: 'para', seed: 75 }, { v: mal, c: DF.green, prog: p2, label: 'mal', seed: 77 }]);
  dText('zaman', X + Wc - 40, Y + 70, 58, { c: DF.penSoft });
}
// 6 — kapanış: defter sayfasında el yazısı + ABONE OL
function sCta(t) {
  paper(); const a = clamp(t / 0.5);
  dText('Paranı', 560, 560, 140, { al: a }); dText('enflasyona karşı', 560, 700, 110, { al: a });
  hiText('koru', 560, 860, 160, { c: DF.red, prog: clamp((t - 0.3) / 0.6) });
  hiText('parafomo.com', 560, 1040, 100, { prog: clamp((t - 0.7) / 0.6), hc: DF.hiG });
  kid(870, 1400, 0.9, { ...MERT, pose: 'cheer', k: clamp((t - 0.2) / 0.5), face: -1, mood: 'happy' });
  const b = clamp(spring(Math.max(0, t - 0.2), 0.9, { k: 200, damp: 0.45 }));
  if (b > 0.01) { ctx.save(); ctx.translate(440, 1240); ctx.scale(b, b);
    ctx.fillStyle = BR.red; ctx.beginPath(); ctx.roundRect(-210, -58, 420, 116, 20); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.moveTo(-150, -24); ctx.lineTo(-150, 24); ctx.lineTo(-110, 0); ctx.closePath(); ctx.fill();
    ctx.font = `56px ${ANTON}`; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText('ABONE OL', -86, 4); ctx.restore(); }
}
const SDRAW = [sHook, sTrade, sMoney, sSame, sPrice, sChart, sCta];
const curI = () => { let i = 0; for (let k = 0; k < SCN.length; k++) if (TT >= sAt(k)) i = k; return i; };
function drawPiece() {
  const i = curI(), fx = i > 0 ? clamp((TT - sAt(i)) / 0.4) : 1;
  if (fx < 1) { SDRAW[i - 1](lt(i - 1)); ctx.save(); ctx.globalAlpha = fx; ctx.translate(0, (1 - EZ.o3(fx)) * 160); }   // yeni kâğıt alttan kayar
  SDRAW[i](lt(i));
  if (fx < 1) ctx.restore();
  overlayGrain('multiply', 0.55);
}
function drawOverlay() { const i = curI(); if (i > 0 && i < 6) captions(1540); }
