// =====================================================================
//  EKONOMİ DEFTERİ #5: KİRA ARTIŞ ORANI NASIL HESAPLANIR? (Short, 9:16) — kits/defter.js
//  Rakamlar data/kira-artis-2026.json (Kasım 2026 tavanı %31,23 = 12 aylık TÜFE ort., TBK md. 344) ve
//  data/tufe-aylik.json (Ekim 2026 yıllık %29,77). Örnek: 20.000 × 1,3123 = 26.246 ₺.
// =====================================================================
BR.capFont = `700 86px ${CAV}`; BR.capText = DF.pen; BR.capStroke = 'rgba(251,250,243,0.95)'; BR.capHi = DF.yellow;
const SCN = ['hook', 'rule', 'calc', 'avg', 'cap', 'cta'];
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
const fmt = (v) => Math.round(v).toLocaleString('tr-TR');
function house(x, y, s = 1) {
  dRect(x - 70 * s, y - 110 * s, 140 * s, 110 * s, 4 * s, { fill: '#F4D9B0', w: 3.4 * s, seed: 211 });
  d([[x - 92 * s, y - 104 * s], [x, y - 180 * s], [x + 92 * s, y - 104 * s]], { closed: true, fill: DF.red, w: 3.4 * s, seed: 212 });
  dRect(x - 18 * s, y - 60 * s, 36 * s, 60 * s, 3 * s, { fill: DF.green, w: 3 * s, seed: 213 });
  dRect(x - 55 * s, y - 92 * s, 28 * s, 26 * s, 2 * s, { fill: 'rgba(160,200,235,0.8)', w: 2.4 * s, seed: 214 });
}
// takvim yaprağı (12 ay)
function months(x, y, k) {
  const AY = ['Kas', 'Ara', 'Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki'];
  for (let i = 0; i < 12; i++) {
    const kk = clamp(k * 12 - i); if (kk <= 0) continue;
    const cx = x + (i % 4) * 190, cy = y + Math.floor(i / 4) * 150;
    fade(kk, () => { dRect(cx - 75, cy - 60, 150, 120, 8, { fill: '#FFFDF4', w: 3, seed: 500 + i }); dText(AY[i], cx, cy + 16, 48); });
  }
}

// 0 — başlık kartı
function sHook(t) {
  titleCard('Kira artışı', 'Nasıl hesaplanır?', { no: 5, prog: clamp((t - 0.3) / 0.7) });
}
// 1 — kural: son 12 ayın TÜFE ortalaması → %31,23
function sRule(t) {
  paper(); pageTitle('Kanunun kuralı', { no: 5, prog: clamp(t / 0.6) });
  dText('TBK md. 344', 900, 420, 40, { c: DF.penSoft, rot: 0.06 });
  const k12 = KW('rule', '12', 0.4), kO = KW('rule', 'ortalaması', 0.5), kR = KW('rule', '%31,23', 0.5);
  months(255, 560, clamp((TT - wAt('rule', '12')) / 1.4) * k12);
  if (kO > 0) { dLine(170, 960, 910, 960, { w: 5, seed: 520, prog: kO }); dText('ortalama', 540, 1040, 60, { c: DF.penSoft, al: kO }); }
  if (kR > 0) hiText('%31,23', 540, 1200, 150, { c: DF.red, prog: kR, hc: DF.hiP });
  fade(kR, () => dText('Kasım 2026 tavanı', 540, 1290, 52, { c: DF.penSoft }));
}
// 2 — hesap: 20.000 × 1,3123 = 26.246 (örnek)
function sCalc(t) {
  paper(); pageTitle('Hesap tek çarpma', { no: 5, prog: clamp(t / 0.6) });
  const k1 = KS('calc', 0.5), k2 = KW('calc', '1,3123', 0.5), k3 = KW('calc', '26.246', 0.6);
  fade(k1, () => { house(260, 760, 1.1); dText('20.000 ₺', 260, 850, 64); dText('bugünkü kira', 260, 910, 40, { c: DF.penSoft }); });
  fade(k2, () => sticky(560, 560, 420, 170, ['× 1,3123'], { size: 84, c: '#FFF08A', rot: 0.04 }));
  if (k3 > 0) { arrow(400, 1000, 640, 1000, { prog: k3, w: 6, head: 22, c: DF.green, seed: 531 });
    fade(k3, () => { house(800, 1130, 1.25); dText('26.246 ₺', 800, 1230, 72, { c: DF.green }); hiText('en fazla', 800, 1310, 56, { c: DF.green, hc: DF.hiG, prog: k3 }); }); }
  kid(180, 1420, 0.8, { ...MERT, pose: 'think', k: 1, face: 1, mood: k3 > 0.5 ? 'wow' : 'calm' });
  dText('örnek', 900, 440, 48, { c: DF.penSoft, rot: 0.1 });
}
// 3 — yıllık enflasyon ≠ 12 aylık ortalama
function sAvg(t) {
  paper(); pageTitle('Yıllık enflasyon değil', { no: 5, prog: clamp(t / 0.6), size: 90 });
  const kY = KW('avg', '%29,77', 0.5), kA = KW('avg', '%31,23', 0.5), kG = KW('avg', 'geriden', 0.6);
  // iki sütun
  const base = 1050, sc = 16;
  if (kY > 0) { const h = 29.77 * sc * kY; dRect(220, base - h, 220, h, 6, { fill: '#BFE3D2', w: 3.4, seed: 541 });
    dText('%29,77', 330, base - h - 30, 66); dText('yıllık', 330, base + 70, 50, { c: DF.penSoft }); dText('Ekim', 330, base + 125, 40, { c: DF.penSoft }); }
  if (kA > 0) { const h = 31.23 * sc * kA; dRect(640, base - h, 220, h, 6, { fill: '#F6C1B9', w: 3.4, seed: 542 });
    dText('%31,23', 750, base - h - 30, 66, { c: DF.red }); dText('12 ay ort.', 750, base + 70, 50, { c: DF.penSoft }); dText('kira tavanı', 750, base + 125, 40, { c: DF.penSoft }); }
  dLine(160, base, 920, base, { w: 4, seed: 543 });
  if (kG > 0) hiText('ortalama geriden gelir', 540, 1330, 70, { prog: kG, hc: DF.hi });
}
// 4 — tavan = üst sınır, pazarlık mümkün
function sCap(t) {
  paper(); pageTitle('Bu bir tavan', { no: 5, prog: clamp(t / 0.6) });
  const kT = KW('cap', 'tavan', 0.5), kD = KW('cap', 'düşük', 0.5);
  if (kT > 0) { dLine(170, 640, 910, 640, { w: 7, c: DF.red, seed: 551, prog: kT }); dText('%31,23 tavan', 540, 600, 60, { c: DF.red, al: kT }); }
  fade(kD, () => { arrow(540, 690, 540, 860, { w: 5, head: 20, c: DF.green, seed: 552 }); sticky(330, 880, 420, 150, ['daha düşük', 'olabilir'], { size: 56, c: '#D9F2E4', rot: -0.03 }); });
  kid(300, 1300, 0.9, { ...MERT, pose: 'give', k: kD, face: 1, mood: kD > 0.3 ? 'happy' : 'calm' });
  kid(780, 1300, 0.9, { hoodie: DF.cover, seed: 2, pose: 'idle', k: 1, face: -1, mood: kD > 0.3 ? 'happy' : 'calm', glasses: true });
  dText('kiracı', 300, 1380, 52, { c: DF.penSoft });
  dText('ev sahibi', 780, 1380, 52, { c: DF.penSoft });
}
// 5 — kapanış: hesaplayıcı + ABONE OL
function sCta(t) {
  paper(); const a = clamp(t / 0.5);
  dText('Kendi kiranı', 560, 520, 104, { al: a }); dText('hesapla:', 560, 650, 104, { al: a });
  hiText('parafomo.com', 560, 830, 120, { prog: clamp((t - 0.3) / 0.6), hc: DF.hiG });
  dText('kira artış hesaplayıcısı', 560, 940, 60, { c: DF.penSoft, al: a });
  kid(870, 1400, 0.9, { ...MERT, pose: 'cheer', k: clamp((t - 0.2) / 0.5), face: -1, mood: 'happy' });
  const b = clamp(spring(Math.max(0, t - 0.2), 0.9, { k: 200, damp: 0.45 }));
  if (b > 0.01) { ctx.save(); ctx.translate(440, 1180); ctx.scale(b, b);
    ctx.fillStyle = BR.red; ctx.beginPath(); ctx.roundRect(-210, -58, 420, 116, 20); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.moveTo(-150, -24); ctx.lineTo(-150, 24); ctx.lineTo(-110, 0); ctx.closePath(); ctx.fill();
    ctx.font = `56px ${ANTON}`; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText('ABONE OL', -86, 4); ctx.restore(); }
}
const SDRAW = [sHook, sRule, sCalc, sAvg, sCap, sCta];
const curI = () => { let i = 0; for (let k = 0; k < SCN.length; k++) if (TT >= sAt(k)) i = k; return i; };
function drawPiece() {
  const i = curI(), fx = i > 0 ? clamp((TT - sAt(i)) / 0.4) : 1;
  if (fx < 1) { SDRAW[i - 1](lt(i - 1)); ctx.save(); ctx.globalAlpha = fx; ctx.translate(0, (1 - EZ.o3(fx)) * 160); }
  SDRAW[i](lt(i));
  if (fx < 1) ctx.restore();
  overlayGrain('multiply', 0.55);
}
function drawOverlay() { const i = curI(); if (i > 0 && i < 5) captions(1540); }
