// =====================================================================
//  kits/dalio.js — "ekonomi makinesi" el çizimi anlatım kiti (referans: How The Economic Machine Works).
//  Krem/ten rengi dokulu kâğıt, el titremeli mürekkep çizgi, yüzsüz sade insanlar, soluk zeytin/hardal/kırmızı,
//  el yazısı büyük harf (Amatic SC, OFL), lacivert süslü başlık kartı. Hepsi kodla çizilir (görsel dosyası yok).
//  person(x, y, s, o) → poz verilebilen figür; props: bill, coin, bread, priceTag, bank, stall, chart, arrow.
// =====================================================================
const DL = { paper: '#F3EFD8', tan: '#D8BB95', navy: '#16203A', ink: '#2A2520', inkSoft: '#6B6255', olive: '#A9AC8E', oliveD: '#7E8266',
  cream: '#FBF8EA', mustard: '#E0B13A', red: '#B4473A', money: '#A9C79A', bread: '#D9A866', skin: '#F4EBD9' };
const AMATIC = 'Amatic, "DejaVu Sans", sans-serif';

// ---- el çizgisi: noktaları yeniden örnekle, pürüzsüz deterministik titreşim ekle, yumuşak eğriyle çiz
function wobblePts(P, closed, seed = 1, amp = 1.4, step = 12) {
  const R = resample(P, closed, step);
  return R.map((p, i) => [p[0] + amp * (Math.sin(i * 0.61 + seed * 1.7) + 0.5 * Math.sin(i * 1.37 + seed * 3.1)),
                          p[1] + amp * (Math.cos(i * 0.53 + seed * 2.3) + 0.5 * Math.sin(i * 1.19 + seed * 0.7))]);
}
function smoothPath(P, closed) {
  ctx.beginPath(); if (P.length < 2) return;
  ctx.moveTo(P[0][0], P[0][1]);
  for (let i = 1; i < P.length - 1; i++) { const mx = (P[i][0] + P[i + 1][0]) / 2, my = (P[i][1] + P[i + 1][1]) / 2; ctx.quadraticCurveTo(P[i][0], P[i][1], mx, my); }
  ctx.lineTo(P[P.length - 1][0], P[P.length - 1][1]); if (closed) ctx.closePath();
}
// h(P, o): o = { w, c (çizgi), fill, closed, seed, prog (0..1 çizilerek belirme), amp }
function h(P, o = {}) {
  const closed = !!o.closed;
  let Q = wobblePts(P, closed, o.seed ?? 1, o.amp ?? 1.4);
  if (o.fill) { smoothPath(Q, true); ctx.fillStyle = o.fill; ctx.fill(); }
  if (o.prog != null && o.prog < 1) { if (o.prog <= 0) return; Q = subPath(Q, o.prog); }
  if (o.c === false) return;
  smoothPath(Q, closed && (o.prog == null || o.prog >= 1));
  ctx.strokeStyle = o.c ?? DL.ink; ctx.lineWidth = o.w ?? 4; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke();
}
const hEll = (cx, cy, rx, ry, o = {}) => h(ellipsePts(cx, cy, rx, ry, o.rot ?? 0, 40), { ...o, closed: true });
const hRect = (x, y, w, hh, r, o = {}) => h(rrectPts(x, y, w, hh, r, 5), { ...o, closed: true });
const hLine = (x1, y1, x2, y2, o = {}) => h([[x1, y1], [x2, y2]], o);
function hText(str, x, y, size, o = {}) {
  ctx.save(); ctx.font = `${o.weight ?? 700} ${size}px ${AMATIC}`; ctx.fillStyle = o.c ?? DL.ink; ctx.textAlign = o.align ?? 'center';
  ctx.textBaseline = o.base ?? 'alphabetic'; ctx.globalAlpha *= o.al ?? 1;
  if (o.rot) { ctx.translate(x, y); ctx.rotate(o.rot); ctx.fillText(str, 0, 0); } else ctx.fillText(str, x, y);
  const w = ctx.measureText(str).width; ctx.restore(); return w;
}
function paperBg(color) { fillAll(color); }

// =====================================================================
//  İnsan figürü. (x, y) = ayakların ortası; s ölçek (~300 px boy @1). Yüz yok (referanstaki gibi).
//  o: { pose: idle|walk|give|cheer|sad|think|point, k: poza geçiş 0..1, face: 1 sağa / -1 sola, t, shirt, hat, seed }
//  Dönüş: { hand: ön el [x,y], handB: arka el, head: [x,y] }
// =====================================================================
function person(x, y, s, o = {}) {
  const f = o.face ?? 1, t = o.t ?? TT, sd = o.seed ?? 1, k = clamp(o.k ?? 1), pose = o.pose || 'idle';
  const ph = t * TAU * 1.7 + sd;
  let bob = Math.sin(t * TAU * 0.5 + sd) * 1.5 * s, lean = 0, headDrop = 0;
  // açılar (radyan, aşağıdan; + = yüzün baktığı yön)
  let aF = [0.12, 0.18], aB = [-0.1, 0.12], lF = [0.05, 0], lB = [-0.05, 0];
  if (pose === 'walk') {
    const sw = Math.sin(ph);
    lF = [0.42 * sw, Math.max(0, -sw) * 0.5]; lB = [-0.42 * sw, Math.max(0, sw) * 0.5];
    aF = [-0.38 * sw, 0.25]; aB = [0.38 * sw, 0.25]; bob = Math.abs(Math.cos(ph)) * 5 * s;
  } else if (pose === 'give' || pose === 'point') {
    aF = [lerp(0.12, 1.42, k), lerp(0.18, pose === 'point' ? 0.0 : 0.08, k)];
  } else if (pose === 'cheer') {
    const j = Math.abs(Math.sin(t * TAU * 1.2 + sd));
    aF = [lerp(0.12, 2.75, k), lerp(0.18, -0.25, k)]; aB = [lerp(-0.1, -2.75, k), lerp(0.12, 0.25, k)]; bob += j * 14 * s * k;
  } else if (pose === 'sad') {
    aF = [0.05, 0.05]; aB = [-0.03, 0.05]; headDrop = 10 * s * k; lean = 0.06 * k;
  } else if (pose === 'think') {
    aF = [lerp(0.12, 2.0, k), lerp(0.18, 2.3, k)];
  }
  const hipY = y - 120 * s - bob, shY = y - 222 * s - bob, hx = x + f * lean * 40 * s;
  const seg = (p, a, L) => [p[0] + f * Math.sin(a) * L, p[1] + Math.cos(a) * L];
  const limb = (p0, a, L1, L2) => { const p1 = seg(p0, a[0], L1), p2 = seg(p1, a[0] + a[1], L2); return [p0, p1, p2]; };
  const legB = limb([x - f * 9 * s, hipY], [lB[0], -lB[1]], 58 * s, 60 * s), legF = limb([x + f * 9 * s, hipY], [lF[0], -lF[1]], 58 * s, 60 * s);
  const armB = limb([hx - f * 15 * s, shY + 10 * s], aB, 50 * s, 48 * s), armF = limb([hx + f * 15 * s, shY + 10 * s], aF, 50 * s, 48 * s);
  const W = 4.2 * s + 1;
  const shoe = (p) => hEll(p[0] + f * 9 * s, p[1] - 3 * s, 15 * s, 7 * s, { fill: DL.ink, w: W * 0.6, seed: sd + 9 });
  h(armB, { w: W, seed: sd + 1 }); hEll(armB[2][0], armB[2][1], 6 * s, 6 * s, { fill: DL.skin, w: W * 0.7, seed: sd + 2 });
  h(legB, { w: W, seed: sd + 3 }); shoe(legB[2]);
  h(legF, { w: W, seed: sd + 4 }); shoe(legF[2]);
  // gövde (gömlek) + bel çizgisi
  h([[hx - 25 * s, shY], [hx + 25 * s, shY], [x + 21 * s, hipY + 6 * s], [x - 21 * s, hipY + 6 * s]], { closed: true, fill: o.shirt ?? DL.olive, w: W, seed: sd + 5 });
  hLine(x - 20 * s, hipY - 4 * s, x + 20 * s, hipY - 4 * s, { w: W * 0.6, seed: sd + 6, c: DL.inkSoft });
  // boyun + baş
  const hy = shY - 44 * s + headDrop;
  hLine(hx, shY, hx + f * lean * 20 * s, hy + 28 * s, { w: W, seed: sd + 7 });
  hEll(hx + f * lean * 30 * s, hy, 23 * s, 29 * s, { fill: DL.skin, w: W, seed: sd + 8, rot: f * lean });
  if (o.hat) {   // fötr şapka
    const cx = hx + f * lean * 30 * s;
    hRect(cx - 19 * s, hy - 52 * s, 38 * s, 28 * s, 9 * s, { fill: o.hat === true ? DL.oliveD : o.hat, w: W, seed: sd + 10 });
    hLine(cx - 34 * s, hy - 24 * s, cx + 34 * s, hy - 24 * s, { w: W * 1.3, seed: sd + 11 });
  }
  h(armF, { w: W, seed: sd + 12 }); hEll(armF[2][0], armF[2][1], 6 * s, 6 * s, { fill: DL.skin, w: W * 0.7, seed: sd + 13 });
  return { hand: armF[2], handB: armB[2], head: [hx, hy] };
}

// =====================================================================
//  Eşyalar
// =====================================================================
function bill(x, y, s = 1, rot = 0, o = {}) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
  hRect(-46 * s, -24 * s, 92 * s, 48 * s, 5 * s, { fill: DL.money, w: 3 * s, seed: o.seed ?? 3 });
  hRect(-36 * s, -15 * s, 72 * s, 30 * s, 3 * s, { w: 2 * s, c: DL.oliveD, seed: (o.seed ?? 3) + 1 });
  hText('₺', 0, 13 * s, 34 * s, { c: DL.ink });
  ctx.restore();
}
function coin(x, y, s = 1) { hEll(x, y, 20 * s, 20 * s, { fill: DL.mustard, w: 3 * s }); hText('₺', x, y + 10 * s, 26 * s); }
function bread(x, y, s = 1, seed = 1) {
  hEll(x, y, 58 * s, 30 * s, { fill: DL.bread, w: 3.5 * s, seed });
  for (let i = -1; i <= 1; i++) h([[x + i * 26 * s - 10 * s, y - 14 * s], [x + i * 26 * s + 8 * s, y + 6 * s]], { w: 3 * s, seed: seed + i + 5, c: DL.inkSoft });
}
function priceTag(x, y, s, label, o = {}) {   // ipten sallanan etiket
  const sw = (o.swing ?? 0) * Math.sin(TT * TAU * 0.9);
  ctx.save(); ctx.translate(x, y); ctx.rotate(sw);
  hLine(0, -70 * s, 0, -10 * s, { w: 2.5 * s, c: DL.inkSoft });
  h([[-70 * s, 0], [70 * s, 0], [90 * s, 45 * s], [70 * s, 90 * s], [-70 * s, 90 * s]], { closed: true, fill: o.fill ?? DL.cream, w: 4 * s, seed: 21 });
  hEll(-48 * s, 45 * s, 8 * s, 8 * s, { w: 3 * s });
  if (label) hText(label, 12 * s, 72 * s, 70 * s, { c: o.c ?? DL.ink });
  ctx.restore();
}
function bank(x, y, s = 1, o = {}) {   // (x, y) = taban ortası
  hRect(x - 170 * s, y - 24 * s, 340 * s, 24 * s, 3 * s, { fill: DL.cream, seed: 31 });
  for (let i = 0; i < 5; i++) hRect(x - 140 * s + i * 66 * s, y - 170 * s, 22 * s, 146 * s, 3 * s, { fill: DL.cream, seed: 32 + i });
  hRect(x - 160 * s, y - 196 * s, 320 * s, 26 * s, 3 * s, { fill: DL.cream, seed: 38 });
  h([[x - 170 * s, y - 196 * s], [x, y - 270 * s], [x + 170 * s, y - 196 * s]], { closed: true, fill: DL.olive, seed: 39 });
  hText(o.label ?? 'BANKA', x, y - 207 * s, 40 * s);
}
function stall(x, y, s = 1, o = {}) {   // fırın tezgâhı: tente + tabela + raf; (x, y) = tezgâh önü taban
  const W0 = 420 * s;
  hRect(x - W0 / 2, y - 150 * s, W0, 150 * s, 4 * s, { fill: DL.cream, seed: 41 });
  for (let i = 0; i < 7; i++) h([[x - W0 / 2 + i * W0 / 7, y - 420 * s], [x - W0 / 2 + (i + 1) * W0 / 7, y - 420 * s], [x - W0 / 2 + (i + 1) * W0 / 7 - 6 * s, y - 360 * s], [x - W0 / 2 + i * W0 / 7 - 6 * s, y - 360 * s]],
    { closed: true, fill: i % 2 ? DL.cream : DL.red, w: 3.5 * s, seed: 42 + i });
  hLine(x - W0 / 2 + 8 * s, y - 360 * s, x - W0 / 2 + 8 * s, y - 150 * s, { w: 5 * s }); hLine(x + W0 / 2 - 8 * s, y - 360 * s, x + W0 / 2 - 8 * s, y - 150 * s, { w: 5 * s });
  hRect(x - 110 * s, y - 470 * s, 220 * s, 56 * s, 6 * s, { fill: DL.mustard, seed: 50 });
  hText(o.sign ?? 'FIRIN', x, y - 428 * s, 50 * s);
  return { shelfY: y - 150 * s };
}
function arrow(x1, y1, x2, y2, o = {}) {
  const pr = o.prog ?? 1; if (pr <= 0) return;
  const ex = x1 + (x2 - x1) * pr, ey = y1 + (y2 - y1) * pr, a = Math.atan2(ey - y1, ex - x1), L = o.head ?? 26;
  h([[x1, y1], [(x1 + ex) / 2 + (o.bend ?? 0), (y1 + ey) / 2 - (o.bend ?? 0)], [ex, ey]], { w: o.w ?? 5, c: o.c, seed: o.seed ?? 61 });
  h([[ex - L * Math.cos(a - 0.45), ey - L * Math.sin(a - 0.45)], [ex, ey], [ex - L * Math.cos(a + 0.45), ey - L * Math.sin(a + 0.45)]], { w: o.w ?? 5, c: o.c, seed: (o.seed ?? 61) + 1 });
}
// el çizimi grafik: eksenler + seriler (değerler 0..1, soldan sağa), prog ile çizilerek belirir
function chart(x, y, w, hh, series, o = {}) {
  hLine(x, y, x, y - hh, { w: 4, seed: 71 }); hLine(x, y, x + w, y, { w: 4, seed: 72 });
  for (const sr of series) {
    const P = sr.v.map((v, i) => [x + (i / (sr.v.length - 1)) * w, y - v * hh]);
    h(P, { w: sr.w ?? 7, c: sr.c, prog: sr.prog ?? 1, seed: sr.seed ?? 73, amp: 1.2 });
    if (sr.label && (sr.prog ?? 1) > 0.95) { const e = P[P.length - 1]; hText(sr.label, e[0] - 10, e[1] - 22, 58, { c: sr.c, align: 'right' }); }
  }
}
// lacivert süslü çerçeve (başlık / kapanış kartı)
function ornateFrame(c = DL.cream) {
  const m = 64;
  hRect(m, m + 120, W - 2 * m, H - 2 * m - 360, 0, { c, w: 4, seed: 81 });
  for (const [cx, cy] of [[m, m + 120], [W - m, m + 120], [m, H - m - 240], [W - m, H - m - 240]]) hEll(cx, cy, 14, 14, { c, w: 4, seed: 82 });
}
