// =====================================================================
//  EKONOMİ DEFTERİ #6: ASGARİ ÜCRET NASIL BELİRLENİR? (Short, 9:16) — kits/defter.js. Pazar uzun bölümün habercisi.
//  Kaynak: İş Kanunu md. 39 (karar RG'de yayımlanınca yürürlük); Asgari Ücret Yönetmeliği md. 8 (15 üye: 5 kamu,
//  5 işçi, 5 işveren; ≥10 üyeyle toplanır, oy çokluğu, eşitlikte başkanın tarafı). 2026: brüt 33.030 → net 28.075,50
//  (data/asgari-ucret.json; %14 SGK + %1 işsizlik). 2027 tutarı TAHMİN EDİLMEZ.
// =====================================================================
BR.capFont = `700 86px ${CAV}`; BR.capText = DF.pen; BR.capStroke = 'rgba(251,250,243,0.95)'; BR.capHi = DF.yellow;
const SCN = ['hook', 'masa', 'oy', 'brut', 'takvim', 'cta'];
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
const KS = (id, dd = 0.5, off = 0) => ease((TT - L(id).t0 - off) / dd);
const fade = (k, fn) => { if (k <= 0) return; ctx.save(); ctx.globalAlpha *= k; fn(); ctx.restore(); };
function stack(x, y, n, s = 1, seed = 700) { for (let i = 0; i < n; i++) bill(x + (i % 2) * 4 * s, y - i * 14 * s, 1.5 * s, 0, { seed: seed + i }); }
const TARAF = [
  { ad: 'işçi', c: DF.yellow, w: 'işçi,' },
  { ad: 'işveren', c: '#6C8FD8', w: 'işveren,' },
  { ad: 'devlet', c: DF.green, w: 'devlet' },
];

// 0 — başlık kartı
function sHook(t) {
  titleCard('Asgari ücret', 'nasıl belirlenir?', { no: 6, prog: clamp((t - 0.3) / 0.7) });
  priceTag(830, 430, 0.85, '₺', { swing: 0.07, c: DF.red });
}
// 1 — 15 kişilik masa: 3 sıra × 5 kişi
function sMasa(t) {
  paper(); pageTitle('15 kişilik masa', { no: 6, prog: clamp(t / 0.6) });
  const rows = [640, 920, 1200];
  TARAF.forEach((g, r) => {
    const k = KW('masa', g.w, 0.5);
    fade(k, () => {
      dText(g.ad, 140, rows[r] - 40, 64, { c: DF.pen, align: 'left' });
      dText('5', 140, rows[r] + 40, 70, { c: DF.penSoft, align: 'left' });
      for (let i = 0; i < 5; i++) kid(400 + i * 135, rows[r] + 70, 0.45, { hoodie: g.c, seed: 20 + r * 5 + i, face: i % 2 ? -1 : 1, mood: 'calm', k: 1 });
    });
  });
  const kT = KW('masa', 'toplam', 0.5);
  if (kT > 0) hiText('= 15 kişi', 540, 1380, 92, { c: DF.red, prog: kT, hc: DF.hiP });
}
// 2 — oy çokluğu; eşitlikte başkanın tarafı; başkanı Bakanlık belirler
function sOy(t) {
  paper(); pageTitle('Karar: oy çokluğu', { no: 6, prog: clamp(t / 0.6), size: 92 });
  // sandık
  const bx = 540, by = 1000;
  dRect(bx - 170, by - 180, 340, 220, 10, { fill: DF.cream, w: 4, seed: 501 });
  dRect(bx - 70, by - 196, 140, 20, 4, { fill: DF.pen, w: 2, seed: 502 });
  dText('OY', bx, by - 50, 90, { c: DF.red });
  const kO = KW('oy', 'çokluğuyla', 0.4);
  for (let i = 0; i < 6; i++) {
    const p = clamp((TT - wAt('oy', 'karar') - i * 0.22) / 0.6);
    if (p <= 0 || kO <= 0) continue;
    const x = lerp(240 + i * 120, bx, ease(p)), y = lerp(560, by - 200, ease(p)) - Math.sin(p * Math.PI) * 60;
    if (p < 1) { ctx.save(); ctx.translate(x, y); ctx.rotate((1 - p) * (i % 2 ? 0.4 : -0.4)); dRect(-34, -22, 68, 44, 3, { fill: '#fff', w: 2.6, seed: 510 + i }); dText('✓', 0, 14, 36, { c: DF.green }); ctx.restore(); }
  }
  const kE = KW('oy', 'eşit', 0.5), kB = KW('oy', 'bakanlık', 0.5);
  fade(kE, () => sticky(90, 1110, 440, 170, ['eşitlikte:', 'başkanın tarafı'], { size: 54, c: '#FFF08A', rot: -0.04 }));
  fade(kB, () => sticky(560, 1130, 430, 170, ['başkanı', 'Bakanlık seçer'], { size: 54, c: '#D9F2E4', rot: 0.04 }));
}
// 3 — brütten nete: 33.030 − %15 = 28.075,50
function sBrut(t) {
  paper(); pageTitle('2026: brütten nete', { no: 6, prog: clamp(t / 0.6), size: 92 });
  const kB = KW('brut', 'brüt', 0.5), kS = KW('brut', '%14', 0.5), kI = KW('brut', '%1', 0.5, 1), kN = KW('brut', '28.075,50', 0.6);
  fade(kB, () => { stack(270, 900, 12, 1.0, 600); dText('brüt', 270, 990, 52, { c: DF.penSoft }); dText('33.030 ₺', 270, 1060, 66); });
  if (kS > 0) arrow(420, 760, 640, 760, { prog: kS, w: 6, head: 22, c: DF.red, seed: 611 });
  fade(kS, () => sticky(380, 420, 300, 120, ['−%14 SGK'], { size: 54, c: '#FFD6E4', rot: -0.05 }));
  fade(kI, () => sticky(690, 450, 320, 120, ['−%1 işsizlik'], { size: 54, c: '#FFD6E4', rot: 0.05 }));
  fade(kN, () => { stack(800, 900, 10, 1.0, 640); dText('net', 800, 990, 52, { c: DF.penSoft }); hiText('28.075,50 ₺', 800, 1060, 66, { c: DF.green, hc: DF.hiG }); });
  fade(kN, () => dText('gelir ve damga vergisi yok', 540, 1150, 46, { c: DF.penSoft }));
  kid(540, 1440, 0.7, { pose: kN > 0.3 ? 'cheer' : 'think', k: 1, face: 1, mood: kN > 0.3 ? 'happy' : 'calm', seed: 3 });
}
// 4 — takvim: Resmî Gazete → 1 Ocak; 2027 → Aralık
function sTakvim(t) {
  paper(); pageTitle('Takvim', { no: 6, prog: clamp(t / 0.6) });
  const kR = KW('takvim', 'resmî', 0.5), kO = KW('takvim', '1', 0.5), k27 = KW('takvim', '2027', 0.5);
  fade(kR, () => { dRect(110, 520, 380, 300, 8, { fill: DF.cream, w: 4, seed: 701 }); dText('RESMÎ', 300, 620, 58, { c: DF.red }); dText('GAZETE', 300, 690, 58, { c: DF.red }); dText('karar yayımlanır', 300, 770, 40, { c: DF.penSoft }); });
  if (kO > 0) arrow(500, 670, 590, 670, { prog: kO, w: 6, head: 22, seed: 711 });
  fade(kO, () => { dRect(600, 520, 360, 300, 8, { fill: '#fff', w: 4, seed: 702 }); dRect(600, 520, 360, 70, 8, { fill: DF.red, w: 4, seed: 703 }); dText('OCAK', 780, 575, 50, { c: '#fff' }); dText('1', 780, 760, 150); });
  fade(kO, () => dText('yeni ücret başlar', 780, 880, 44, { c: DF.penSoft }));
  if (k27 > 0) hiText('2027: Aralık\'ta aynı masa', 540, 1080, 80, { c: DF.pen, prog: k27 });
  fade(k27, () => dText('(tutar henüz belli değil)', 540, 1170, 46, { c: DF.penSoft }));
  kid(540, 1430, 0.8, { pose: 'point', k: k27, face: 1, mood: 'calm', seed: 4 });
}
// 5 — kapanış: Pazar uzun bölüm + ABONE OL
function sCta(t) {
  paper(); const a = clamp(t / 0.5);
  dText('Artışlar ve', 560, 520, 96, { al: a }); dText('masanın perde arkası:', 560, 640, 90, { al: a });
  hiText('Pazar 12:00', 560, 820, 130, { c: DF.red, prog: clamp((t - 0.3) / 0.6) });
  dText('uzun bölüm', 560, 930, 80, { c: DF.penSoft, al: a });
  hiText('parafomo.com', 560, 1080, 96, { prog: clamp((t - 0.7) / 0.6), hc: DF.hiG });
  kid(870, 1400, 0.9, { pose: 'cheer', k: clamp((t - 0.2) / 0.5), face: -1, mood: 'happy', seed: 1 });
  const b = clamp(spring(Math.max(0, t - 0.2), 0.9, { k: 200, damp: 0.45 }));
  if (b > 0.01) { ctx.save(); ctx.translate(440, 1260); ctx.scale(b, b);
    ctx.fillStyle = BR.red; ctx.beginPath(); ctx.roundRect(-210, -58, 420, 116, 20); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.moveTo(-150, -24); ctx.lineTo(-150, 24); ctx.lineTo(-110, 0); ctx.closePath(); ctx.fill();
    ctx.font = `56px ${ANTON}`; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText('ABONE OL', -86, 4); ctx.restore(); }
}
const SDRAW = [sHook, sMasa, sOy, sBrut, sTakvim, sCta];
const curI = () => { let i = 0; for (let k = 0; k < SCN.length; k++) if (TT >= sAt(k)) i = k; return i; };
function drawPiece() {
  const i = curI(), fx = i > 0 ? clamp((TT - sAt(i)) / 0.4) : 1;
  if (fx < 1) { SDRAW[i - 1](lt(i - 1)); ctx.save(); ctx.globalAlpha = fx; ctx.translate(0, (1 - EZ.o3(fx)) * 160); }
  SDRAW[i](lt(i));
  if (fx < 1) ctx.restore();
  overlayGrain('multiply', 0.55);
}
function drawOverlay() { const i = curI(); if (i > 0 && i < 5) captions(1540); }
