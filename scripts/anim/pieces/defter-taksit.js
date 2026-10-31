// =====================================================================
//  EKONOMİ DEFTERİ #2: TAKSİT Mİ PEŞİN Mİ? — kits/defter.js
//  Örnek: 12.000 ₺ peşin ya da 12 × 1.000 ₺ (vade farksız), fiyatlar ayda %2 artıyor (örnek oran).
//  Taksit k'nın bugünkü değeri = 1000 / 1,02^k  →  12. taksit ≈ 788 ₺, toplam ≈ 10.575 ₺ (%11,9 ucuz).
// =====================================================================
BR.capFont = `700 86px ${CAV}`; BR.capText = DF.pen; BR.capStroke = 'rgba(251,250,243,0.95)'; BR.capHi = DF.yellow;
const SCN = ['hook', 'offer', 'same', 'erode', 'total', 'rule', 'cta'];
const sAt = (i) => (i === 0 ? -1.2 : cue(SCN[i]) - 0.15);
const lt = (i) => TT - sAt(i);
const ease = (x) => EZ.io(clamp(x));
function wAt(id, w) {
  const l = L(id), ws = (l.cap || '').toLocaleLowerCase('tr-TR').split(/\s+/), i = ws.findIndex((x) => x.includes(w));
  if (i < 0) return l.t0;
  return l.words && l.words[i] != null ? l.words[i] : l.t0 + (l.t1 - l.t0) * i / ws.length;
}
const MERT = { hoodie: DF.yellow, seed: 1 };
const PV = Array.from({ length: 12 }, (_, k) => 1000 / Math.pow(1.02, k + 1));   // 980 … 788
const fmt = (v) => Math.round(v).toLocaleString('tr-TR');

// 0 — başlık kartı
function sHook(t) {
  titleCard('Taksit mi, peşin mi?', 'Taksitin gizli hesabı', { no: 2, prog: clamp((t - 0.3) / 0.7) });
  fridge(810, 575, 0.6);
  priceTag(560, 400, 0.85, '?', { swing: 0.07 });
}
// 1 — mağaza: iki seçenek kartı, altta buzdolabı + Mert düşünür
function optCard(x, y, w, hh, head, big, k, o = {}) {
  if (k <= 0) return;
  ctx.save(); ctx.globalAlpha = k; ctx.translate(x + w / 2, y + hh / 2); ctx.scale(0.85 + 0.15 * k, 0.85 + 0.15 * k); ctx.translate(-(x + w / 2), -(y + hh / 2));
  dRect(x, y, w, hh, 14, { fill: o.fill ?? DF.cream, w: 4, seed: o.seed ?? 120 });
  dText(head, x + w / 2, y + 80, 64, { c: DF.penSoft });
  hiText(big, x + w / 2, y + 200, 92, { hc: o.hc, prog: clamp(k * 1.4 - 0.3), seed: o.seed });
  ctx.restore();
}
function sOffer(t) {
  paper(); pageTitle('Mağazada iki seçenek', { no: 2, prog: clamp(t / 0.6) });
  const kP = ease((TT - wAt('offer', 'peşin')) / 0.5), kT = ease((TT - wAt('offer', 'ayda')) / 0.5);
  optCard(70, 410, 450, 290, 'PEŞİN', '12.000 ₺', kP, { seed: 121 });
  optCard(560, 410, 450, 290, 'TAKSİT', '12 × 1.000 ₺', kT, { seed: 122, hc: DF.hiG });
  if (kP > 0.5 && kT > 0.5) dText('ya da', 540, 575, 54, { c: DF.red, al: Math.min(kP, kT), rot: -0.12 });
  fridge(330, 1400, 1.0);
  const walkK = ease((TT - sAt(1)) / 1.4), ax = lerp(1250, 760, walkK);
  kid(ax, 1400, 1.2, { ...MERT, pose: walkK < 1 ? 'walk' : 'think', k: ease((TT - wAt('offer', 'peşin')) / 0.5), face: -1, mood: kT > 0.5 ? 'wow' : 'calm' });
}
// 2 — toplam aynı mı? saat döner
function sSame(t) {
  paper(); pageTitle('Toplam aynı mı?', { no: 2, prog: clamp(t / 0.6) });
  const a = clamp(t / 0.5);
  dText('12 × 1.000 ₺', 540, 560, 120, { al: a });
  dText('= 12.000 ₺', 540, 720, 120, { al: clamp((t - 0.4) / 0.5) });
  const kA = ease((TT - wAt('same', 'ama')) / 0.5);
  if (kA > 0) {
    clock(540, 1000, 150 * (0.6 + 0.4 * kA), { speed: 0.6 });
    hiText('ama zaman var', 540, 1260, 90, { c: DF.red, prog: kA, hc: DF.hiP });
  }
  kid(180, 1400, 0.85, { ...MERT, pose: 'think', k: 1, face: 1, mood: 'calm' });
}
// 3 — taksitler erir: 12 banknot, her ay biraz küçülür
function sErode(t) {
  paper(); pageTitle('Taksitler erir', { no: 2, prog: clamp(t / 0.6) });
  sticky(700, 380, 300, 170, ['fiyatlar', 'ayda %2 ↑'], { size: 56, c: '#FFD6E4', rot: 0.04 });
  dText('örnek', 850, 600, 46, { c: DF.penSoft, rot: 0.08 });
  const t0 = wAt('erode', 'artıyorsa') - sAt(3);
  for (let k = 0; k < 12; k++) {
    const c = k % 4, r = Math.floor(k / 4), x = 180 + c * 240, y = 720 + r * 230;
    const ap = ease((t - 0.2 - k * 0.12) / 0.4); if (ap <= 0) continue;
    const sh = ease((t - t0 - k * 0.08) / 0.8), sc = 1.55 * lerp(1, PV[k] / 1000, sh);
    ctx.save(); ctx.globalAlpha = ap; bill(x, y, sc, (k % 3 - 1) * 0.05, { seed: 130 + k }); ctx.restore();
    dText(`${k + 1}. ay`, x, y + 92, 40, { c: DF.penSoft, al: ap });
    if (sh > 0.05) dText(`${fmt(lerp(1000, PV[k], sh))} ₺`, x, y + 136, 48, { c: k === 11 ? DF.red : DF.pen, al: ap });
  }
  const kL = ease((TT - wAt('erode', '790')) / 0.5);
  if (kL > 0) { dEll(900, 1196, 140, 120, { w: 6, c: DF.red, prog: kL, seed: 141 }); }
}
// 4 — bugünün parasıyla: iki sütun
function sTotal(t) {
  paper(); pageTitle('Bugünün parasıyla', { no: 2, prog: clamp(t / 0.6) });
  const base = 1300, k = 0.058, g1 = ease((t - 0.2) / 0.8), g2 = ease((TT - wAt('total', 'aslında')) / 0.9);
  const h1 = 12000 * k * g1, h2 = 10575 * k * g2;
  dRect(150, base - h1, 230, Math.max(h1, 1), 8, { fill: '#F4B7A6', w: 4, seed: 151 });
  dRect(500, base - h2, 230, Math.max(h2, 1), 8, { fill: DF.money, w: 4, seed: 152 });
  dLine(100, base, 800, base, { w: 4, seed: 153 });
  if (g1 > 0.9) dText('12.000 ₺', 265, base - h1 - 30, 66);
  if (g2 > 0.9) dText('≈10.600 ₺', 615, base - h2 - 30, 66, { c: DF.green });
  dText('peşin', 265, base + 70, 60, { c: DF.penSoft }); dText('12 taksit', 615, base + 70, 60, { c: DF.penSoft });
  const kG = ease((TT - wAt('total', 'ucuz')) / 0.5);
  if (kG > 0) {
    marker(500, base - 12000 * k + (12000 - 10575) * k / 2, 230, (12000 - 10575) * k, { prog: kG, c: DF.hiG });
    dLine(500, base - 12000 * k, 730, base - 12000 * k, { w: 3, c: DF.penSoft, prog: kG, seed: 155 });
    hiText('%12 ucuz', 615, base - 12000 * k - 70, 78, { c: DF.green, prog: kG, hc: DF.hi });
  }
  kid(930, 1400, 0.8, { ...MERT, pose: 'cheer', k: kG, face: -1, mood: kG > 0.3 ? 'happy' : 'calm' });
}
// 5 — kural + vade farkı uyarısı
function sRule(t) {
  paper(); pageTitle('Bu örnekte kural', { no: 2, prog: clamp(t / 0.6) });
  const k1 = ease((TT - wAt('rule', 'azsa')) / 0.5), k2 = ease((TT - wAt('rule', 'fazlaysa')) / 0.5), k3 = ease((TT - wAt('rule', 'vade')) / 0.5);
  dText('peşin indirim %12\'den az', 540, 500, 76, { al: clamp((t - 0.3) / 0.5) });
  if (k1 > 0) { arrow(540, 525, 540, 590, { prog: k1, w: 4, head: 18, seed: 161 }); hiText('taksit', 540, 660, 92, { c: DF.green, prog: k1, hc: DF.hiG }); }
  dText('peşin indirim %12\'den fazla', 540, 790, 76, { al: Math.max(k2, clamp((TT - wAt('rule', 'azsa') - 0.6) / 0.5)) });
  if (k2 > 0) { arrow(540, 815, 540, 880, { prog: k2, w: 4, head: 18, seed: 162 }); hiText('peşin', 540, 950, 92, { c: DF.green, prog: k2, hc: DF.hiG }); }
  if (k3 > 0) {
    ctx.save(); ctx.globalAlpha = k3;
    sticky(90, 1060, 560, 230, ['Dikkat:', 'vade farkı varsa', 'hesap değişir!'], { size: 58, c: '#FFD6E4', rot: -0.03 });
    ctx.restore();
  }
  kid(860, 1400, 0.85, { ...MERT, pose: k3 > 0 ? 'point' : 'idle', k: k3, face: -1, mood: k3 > 0.3 ? 'wow' : 'happy' });
}
// 6 — kapanış + ABONE OL
function sCta(t) {
  paper(); const a = clamp(t / 0.5);
  dText('Önce hesap,', 560, 560, 130, { al: a }); dText('sonra', 560, 700, 110, { al: a });
  hiText('alışveriş', 560, 860, 150, { c: DF.red, prog: clamp((t - 0.3) / 0.6) });
  dText('sonraki sayfa →', 560, 1420, 70, { c: DF.penSoft, al: clamp((t - 1.0) / 0.5) });
  hiText('parafomo.com', 560, 1040, 100, { prog: clamp((t - 0.7) / 0.6), hc: DF.hiG });
  kid(870, 1400, 0.9, { ...MERT, pose: 'cheer', k: clamp((t - 0.2) / 0.5), face: -1, mood: 'happy' });
  const b = clamp(spring(Math.max(0, t - 0.2), 0.9, { k: 200, damp: 0.45 }));
  if (b > 0.01) { ctx.save(); ctx.translate(440, 1240); ctx.scale(b, b);
    ctx.fillStyle = BR.red; ctx.beginPath(); ctx.roundRect(-210, -58, 420, 116, 20); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.moveTo(-150, -24); ctx.lineTo(-150, 24); ctx.lineTo(-110, 0); ctx.closePath(); ctx.fill();
    ctx.font = `56px ${ANTON}`; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText('ABONE OL', -86, 4); ctx.restore(); }
}
const SDRAW = [sHook, sOffer, sSame, sErode, sTotal, sRule, sCta];
const curI = () => { let i = 0; for (let k = 0; k < SCN.length; k++) if (TT >= sAt(k)) i = k; return i; };
function drawPiece() {
  const i = curI(), fx = i > 0 ? clamp((TT - sAt(i)) / 0.4) : 1;
  if (fx < 1) { SDRAW[i - 1](lt(i - 1)); ctx.save(); ctx.globalAlpha = fx; ctx.translate(0, (1 - EZ.o3(fx)) * 160); }   // yeni kâğıt alttan kayar
  SDRAW[i](lt(i));
  if (fx < 1) ctx.restore();
  overlayGrain('multiply', 0.55);
}
function drawOverlay() { const i = curI(); if (i > 0 && i < 6) captions(1540); }
