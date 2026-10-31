// =====================================================================
//  kits/defter.js — "EKONOMİ DEFTERİ" (ParaFOMO'nun el çizimi anlatım serisi, 2026-10-31).
//  Kimlik: düz krem kâğıt (paper) ya da kareli defter (notebook), koyu mürekkep çizgi,
//  keçeli kalemle "taşan" boyama (dolgu çizgiden hafif kayık), fosforlu kalem vurgusu, Caveat el yazısı (OFL).
//  Karakterler büyük kafalı, YÜZLÜ ve ifadeli (mutlu/üzgün/şaşkın); ana karakter sarı kapüşonlu, gözlüklü.
//  Mekânlar Türkiye: simitçi, pazar, banka kuyruğu. Hepsi kodla çizilir; dış görsel yok.
// =====================================================================
const DF = { page: '#FBFAF3', grid: 'rgba(86,140,205,0.20)', margin: 'rgba(222,78,72,0.55)', pen: '#2A2520', penSoft: '#6B6255', paper: '#F3EFD8', paperB: '#EADFC4',
  hi: 'rgba(255,226,64,0.62)', hiG: 'rgba(120,226,170,0.55)', hiP: 'rgba(255,140,190,0.45)', yellow: '#FFC94D', green: '#2BB194',
  red: '#E3483B', skin: '#FFE0C2', hair: '#3A2A22', cream: '#FFF6DF', simit: '#C8823A', sesame: '#F7E7B5', money: '#9ED3A8',
  cover: '#1E6B61', kraft: '#D9B98C', shadow: 'rgba(30,40,70,0.18)' };
const CAV = 'Caveat, "DejaVu Sans", sans-serif';

// ---- el çizgisi (tükenmez: ince, hafif titrek)
function dWob(P, closed, seed = 1, amp = 1.2, step = 10) {
  const R = resample(P, closed, step);
  return R.map((p, i) => [p[0] + amp * (Math.sin(i * 0.71 + seed * 1.9) + 0.4 * Math.sin(i * 1.53 + seed * 2.7)),
                          p[1] + amp * (Math.cos(i * 0.47 + seed * 2.1) + 0.4 * Math.sin(i * 1.11 + seed * 0.9))]);
}
function dPath(P, closed) {
  ctx.beginPath(); if (P.length < 2) return;
  ctx.moveTo(P[0][0], P[0][1]);
  for (let i = 1; i < P.length - 1; i++) { const mx = (P[i][0] + P[i + 1][0]) / 2, my = (P[i][1] + P[i + 1][1]) / 2; ctx.quadraticCurveTo(P[i][0], P[i][1], mx, my); }
  ctx.lineTo(P[P.length - 1][0], P[P.length - 1][1]); if (closed) ctx.closePath();
}
// d(P, o): o = { w, c, fill, closed, seed, prog, amp } — dolgu keçeli kalem gibi çizgiden 5 px kayık basılır
function d(P, o = {}) {
  const closed = !!o.closed, sd = o.seed ?? 1;
  let Q = dWob(P, closed, sd, o.amp ?? 1.2);
  if (o.fill) {
    ctx.save(); ctx.translate(o.off ?? 5, (o.off ?? 5) * 0.6); dPath(dWob(P, true, sd + 50, 2.2), true);
    ctx.fillStyle = o.fill; ctx.globalAlpha *= o.fa ?? 0.92; ctx.fill(); ctx.restore();
  }
  if (o.prog != null && o.prog < 1) { if (o.prog <= 0) return; Q = subPath(Q, o.prog); }
  if (o.c === false) return;
  dPath(Q, closed && (o.prog == null || o.prog >= 1));
  ctx.strokeStyle = o.c ?? DF.pen; ctx.lineWidth = o.w ?? 3.6; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke();
}
const dEll = (cx, cy, rx, ry, o = {}) => d(ellipsePts(cx, cy, rx, ry, o.rot ?? 0, 44), { ...o, closed: true });
const dRect = (x, y, w, hh, r, o = {}) => d(rrectPts(x, y, w, hh, r, 5), { ...o, closed: true });
const dLine = (x1, y1, x2, y2, o = {}) => d([[x1, y1], [x2, y2]], o);
function dText(str, x, y, size, o = {}) {
  ctx.save(); ctx.font = `${o.weight ?? 700} ${size}px ${CAV}`; ctx.fillStyle = o.c ?? DF.pen; ctx.textAlign = o.align ?? 'center';
  ctx.textBaseline = o.base ?? 'alphabetic'; ctx.globalAlpha *= o.al ?? 1;
  if (o.rot) { ctx.translate(x, y); ctx.rotate(o.rot); ctx.fillText(str, 0, 0); } else ctx.fillText(str, x, y);
  const w = ctx.measureText(str).width; ctx.restore(); return w;
}
// fosforlu kalem: soldan sağa sürülür (prog), kenarları düzensiz
function marker(x, y, w, hh, o = {}) {
  const p = clamp(o.prog ?? 1); if (p <= 0) return;
  ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = o.c ?? DF.hi;
  const sd = o.seed ?? 3, ww = w * p; ctx.beginPath();
  for (let i = 0; i <= 12; i++) { const xx = x + ww * i / 12; ctx.lineTo(xx, y - hh / 2 + Math.sin(i * 1.7 + sd) * 3); }
  for (let i = 12; i >= 0; i--) { const xx = x + ww * i / 12; ctx.lineTo(xx, y + hh / 2 + Math.cos(i * 1.3 + sd) * 3); }
  ctx.closePath(); ctx.fill(); ctx.restore();
}
// yazıyı fosforla vurgula
function hiText(str, x, y, size, o = {}) {
  ctx.save(); ctx.font = `${o.weight ?? 700} ${size}px ${CAV}`; const w = ctx.measureText(str).width; ctx.restore();
  const al = o.align ?? 'center', x0 = al === 'center' ? x - w / 2 : al === 'right' ? x - w : x;
  marker(x0 - 14, y - size * 0.3, w + 28, size * 0.62, { prog: o.prog ?? 1, c: o.hc, seed: o.seed });
  return dText(str, x, y, size, o);
}

// ---- kareli defter sayfası (spiral üstte). o: { tint } — sahneye göre hafif renkli kâğıt
function notebook(o = {}) {
  fillAll(o.tint ?? DF.page);
  ctx.save(); ctx.strokeStyle = DF.grid; ctx.lineWidth = 2;
  for (let x = 24; x < W; x += 54) { ctx.beginPath(); ctx.moveTo(x, 120); ctx.lineTo(x, H); ctx.stroke(); }
  for (let y = 120; y < H; y += 54) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  ctx.strokeStyle = DF.margin; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(96, 120); ctx.lineTo(96, H); ctx.stroke();
  ctx.restore();
  spiral();
}
function spiral() {   // üst kenarda delikler + metal halkalar
  ctx.save();
  ctx.fillStyle = 'rgba(0,0,0,0.06)'; ctx.fillRect(0, 0, W, 120);
  for (let x = 60; x < W; x += 74) {
    ctx.fillStyle = '#2B2E36'; ctx.beginPath(); ctx.ellipse(x, 92, 11, 11, 0, 0, TAU); ctx.fill();
    ctx.strokeStyle = '#9AA0AB'; ctx.lineWidth = 7; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(x - 4, 92); ctx.bezierCurveTo(x - 16, 50, x + 18, 18, x + 10, 6); ctx.stroke();
    ctx.strokeStyle = 'rgba(255,255,255,0.7)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(x - 7, 80); ctx.bezierCurveTo(x - 14, 50, x + 12, 22, x + 7, 10); ctx.stroke();
  }
  ctx.restore();
}
// ---- düz krem kâğıt (Kaan 2026-10-31: kareli defter yerine sade kâğıt). o: { tint }
function paper(o = {}) {
  fillAll(o.tint ?? DF.paper);
  const g = ctx.createRadialGradient(W / 2, H * 0.45, 300, W / 2, H * 0.45, 1250);   // kenarlara doğru hafif koyulaşan kâğıt
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(120,90,40,0.16)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}
// başlık kartı: ParaFOMO yeşili zemin + krem el çizimi çift çerçeve (lacivert süslü çerçeve DEĞİL)
function titleCard(title, sub, o = {}) {
  fillAll(DF.cover);
  dRect(70, 230, W - 140, 1300, 18, { c: DF.cream, w: 4, seed: 81 }); dRect(92, 252, W - 184, 1256, 14, { c: 'rgba(255,246,223,0.5)', w: 2.5, seed: 82 });
  dText('EKONOMİ', 540, 720, 170, { c: DF.cream }); dText('DEFTERİ', 540, 880, 170, { c: DF.cream });
  dLine(330, 930, 750, 930, { c: DF.yellow, w: 5, seed: 83 });
  if (o.no) dText(`#${o.no}`, 540, 1010, 70, { c: DF.yellow, weight: 600 });
  if (title) hiText(title, 540, 1200, o.tsize ?? 100, { c: '#fff', hc: 'rgba(255,201,77,0.85)', prog: o.prog ?? 1 });
  if (sub) dText(sub, 540, 1310, 62, { c: 'rgba(255,255,255,0.85)', weight: 500 });
  dText('ParaFOMO', 540, 1470, 54, { c: 'rgba(255,246,223,0.75)', weight: 600 });
}
// sayfa başlığı: el yazısı + altında fosfor
function pageTitle(str, o = {}) {
  hiText(str, o.x ?? 560, o.y ?? 300, o.size ?? 100, { prog: o.prog ?? 1, hc: o.hc, seed: 7 });
  if (o.no) dText(`Ekonomi Defteri #${o.no}`, W - 70, 150, 44, { c: DF.penSoft, align: 'right', weight: 500 });
}
// köşeye yapışkan not
function sticky(x, y, w, hh, lines, o = {}) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot ?? -0.04);
  ctx.fillStyle = DF.shadow; ctx.fillRect(8, 10, w, hh);
  ctx.fillStyle = o.c ?? '#FFF08A'; ctx.fillRect(0, 0, w, hh);
  ctx.fillStyle = 'rgba(0,0,0,0.05)'; ctx.fillRect(0, 0, w, 26);
  lines.forEach((s, i) => dText(s, w / 2, 26 + (i + 1) * (o.size ?? 58), o.size ?? 58, { c: o.tc ?? DF.pen }));
  ctx.restore();
}

// =====================================================================
//  Karakter (büyük kafalı). (x, y) = ayakların ortası; s ölçek (~300 px boy @1).
//  o: { pose: idle|walk|give|cheer|sad|think|point, k, face: 1/-1, mood: happy|sad|wow|calm, hoodie, hair, glasses, t, seed }
//  Dönüş: { hand, handB, head }
// =====================================================================
function kid(x, y, s, o = {}) {
  const f = o.face ?? 1, t = o.t ?? TT, sd = o.seed ?? 1, k = clamp(o.k ?? 1), pose = o.pose || 'idle';
  const ph = t * TAU * 1.8 + sd;
  let bob = Math.sin(t * TAU * 0.6 + sd) * 2 * s, tilt = 0;
  let aF = [0.25, 0.3], aB = [-0.2, 0.25], lF = [0.06, 0], lB = [-0.06, 0];
  if (pose === 'walk') {
    const sw = Math.sin(ph);
    lF = [0.45 * sw, Math.max(0, -sw) * 0.4]; lB = [-0.45 * sw, Math.max(0, sw) * 0.4];
    aF = [-0.5 * sw, 0.3]; aB = [0.5 * sw, 0.3]; bob = Math.abs(Math.cos(ph)) * 6 * s;
  } else if (pose === 'give' || pose === 'point') {
    aF = [lerp(0.25, 1.5, k), lerp(0.3, 0.05, k)];
  } else if (pose === 'cheer') {
    const j = Math.abs(Math.sin(t * TAU * 1.3 + sd));
    aF = [lerp(0.25, 2.6, k), lerp(0.3, -0.3, k)]; aB = [lerp(-0.2, -2.6, k), lerp(0.25, 0.3, k)]; bob += j * 16 * s * k;
  } else if (pose === 'sad') {
    aF = [0.08, 0.05]; aB = [-0.06, 0.05]; tilt = 0.12 * k;
  } else if (pose === 'think') {
    aF = [lerp(0.25, 2.1, k), lerp(0.3, 2.2, k)]; tilt = -0.08 * k;
  }
  const hipY = y - 72 * s - bob, shY = y - 158 * s - bob;
  const seg = (p, a, Ln) => [p[0] + f * Math.sin(a) * Ln, p[1] + Math.cos(a) * Ln];
  const limb = (p0, a, L1, L2) => { const p1 = seg(p0, a[0], L1), p2 = seg(p1, a[0] + a[1], L2); return [p0, p1, p2]; };
  const W0 = 3.4 * s + 1.2, hood = o.hoodie ?? DF.yellow;
  const legB = limb([x - f * 14 * s, hipY], [lB[0], -lB[1]], 36 * s, 36 * s), legF = limb([x + f * 14 * s, hipY], [lF[0], -lF[1]], 36 * s, 36 * s);
  const armB = limb([x - f * 30 * s, shY + 14 * s], aB, 40 * s, 38 * s), armF = limb([x + f * 30 * s, shY + 14 * s], aF, 40 * s, 38 * s);
  const shoe = (p) => dEll(p[0] + f * 10 * s, p[1] - 4 * s, 17 * s, 9 * s, { fill: '#30343F', w: W0 * 0.8, seed: sd + 9, off: 2 });
  // arka kol + bacaklar (pantolon: lacivert kalın çizgi)
  d(armB, { w: W0 * 4.2, c: hood, seed: sd + 1 }); d(armB, { w: W0, seed: sd + 1 });
  dEll(armB[2][0], armB[2][1], 9 * s, 9 * s, { fill: DF.skin, w: W0 * 0.8, seed: sd + 2, off: 2 });
  for (const lg of [legB, legF]) { d(lg, { w: W0 * 5, c: '#3C5A99', seed: sd + 3 }); d(lg, { w: W0, seed: sd + 4 }); shoe(lg[2]); }
  // gövde: kapüşonlu (yuvarlak hatlı)
  d([[x - 36 * s, shY + 6 * s], [x + 36 * s, shY + 6 * s], [x + 40 * s, hipY + 6 * s], [x - 40 * s, hipY + 6 * s]], { closed: true, fill: hood, w: W0, seed: sd + 5 });
  dLine(x - 14 * s, shY + 40 * s, x + 14 * s, shY + 40 * s, { w: W0 * 0.7, seed: sd + 6 });   // kanguru cebi
  d([[x - 22 * s, shY + 40 * s], [x - 26 * s, shY + 64 * s], [x + 26 * s, shY + 64 * s], [x + 22 * s, shY + 40 * s]], { w: W0 * 0.7, seed: sd + 7 });
  // kafa (büyük), saç, yüz
  const hx = x + f * tilt * 30 * s, hy = shY - 62 * s + tilt * 20 * s, R = 64 * s;
  dEll(hx, hy, R, R * 0.96, { fill: DF.skin, w: W0, seed: sd + 8, rot: tilt * f });
  d([[hx - R * 0.95, hy - R * 0.15], [hx - R * 0.7, hy - R * 0.85], [hx - R * 0.1, hy - R * 1.05], [hx + R * 0.55, hy - R * 0.9], [hx + R * 0.98, hy - R * 0.2],
     [hx + R * 0.55, hy - R * 0.55], [hx + R * 0.1, hy - R * 0.45], [hx - R * 0.35, hy - R * 0.62]], { closed: true, fill: o.hair ?? DF.hair, w: W0, seed: sd + 10, off: 2 });
  const ex = hx + f * R * 0.18, ey = hy + R * 0.05, mood = o.mood ?? (pose === 'sad' ? 'sad' : pose === 'cheer' ? 'happy' : 'calm');
  const blink = (Math.sin(t * 2.3 + sd * 5) > 0.985) ? 0.15 : 1;
  for (const dx of [-0.32, 0.32]) {
    ctx.fillStyle = DF.pen; ctx.beginPath(); ctx.ellipse(ex + dx * R, ey, 6 * s, (mood === 'wow' ? 9 : 7) * s * blink, 0, 0, TAU); ctx.fill();
    const by = ey - 20 * s + (mood === 'sad' ? 3 * s : 0), bt = mood === 'sad' ? (dx < 0 ? 4 : -4) * s : mood === 'wow' ? -5 * s : 0;
    dLine(ex + dx * R - 11 * s, by + bt, ex + dx * R + 11 * s, by - bt, { w: W0 * 0.7, seed: sd + 20 });
  }
  if (o.glasses !== false) for (const dx of [-0.32, 0.32]) dEll(ex + dx * R, ey, 17 * s, 15 * s, { w: W0 * 0.75, seed: sd + 22 });
  const my = hy + R * 0.42;
  if (mood === 'happy') d([[ex - 16 * s, my - 4 * s], [ex, my + 9 * s], [ex + 16 * s, my - 4 * s]], { w: W0 * 0.8, seed: sd + 24 });
  else if (mood === 'sad') d([[ex - 14 * s, my + 6 * s], [ex, my - 4 * s], [ex + 14 * s, my + 6 * s]], { w: W0 * 0.8, seed: sd + 24 });
  else if (mood === 'wow') dEll(ex, my + 2 * s, 7 * s, 9 * s, { fill: '#B5473F', w: W0 * 0.7, seed: sd + 24, off: 0 });
  else dLine(ex - 10 * s, my, ex + 10 * s, my + 1 * s, { w: W0 * 0.8, seed: sd + 24 });
  if (mood === 'happy') for (const dx of [-0.6, 0.55]) { ctx.fillStyle = 'rgba(255,120,120,0.35)'; ctx.beginPath(); ctx.ellipse(ex + dx * R, ey + 20 * s, 10 * s, 6 * s, 0, 0, TAU); ctx.fill(); }
  // ön kol
  d(armF, { w: W0 * 4.2, c: hood, seed: sd + 12 }); d(armF, { w: W0, seed: sd + 12 });
  dEll(armF[2][0], armF[2][1], 9 * s, 9 * s, { fill: DF.skin, w: W0 * 0.8, seed: sd + 13, off: 2 });
  return { hand: armF[2], handB: armB[2], head: [hx, hy] };
}

// =====================================================================
//  Eşyalar (Türkiye)
// =====================================================================
function simit(x, y, s = 1, seed = 1) {
  dEll(x, y, 46 * s, 40 * s, { fill: DF.simit, w: 3 * s, seed });
  dEll(x, y, 16 * s, 13 * s, { fill: DF.page, w: 2.6 * s, seed: seed + 1, off: 0 });
  for (let i = 0; i < 14; i++) { const a = i / 14 * TAU + seed, r = 30 * s; ctx.fillStyle = DF.sesame; ctx.beginPath();
    ctx.ellipse(x + Math.cos(a) * r, y + Math.sin(a) * r * 0.85, 3.2 * s, 1.8 * s, a, 0, TAU); ctx.fill(); }
}
// simitçi tezgâhı (cam kutulu araba); (x, y) = tekerlek tabanı ortası. Dönüş: { topY }
function simitCart(x, y, s = 1, o = {}) {
  const Wc = 380 * s;
  dEll(x - Wc * 0.32, y - 34 * s, 34 * s, 34 * s, { fill: '#5B6170', w: 3.4 * s, seed: 61 }); dEll(x + Wc * 0.32, y - 34 * s, 34 * s, 34 * s, { fill: '#5B6170', w: 3.4 * s, seed: 62 });
  dRect(x - Wc / 2, y - 260 * s, Wc, 200 * s, 10 * s, { fill: DF.red, w: 3.6 * s, seed: 63 });
  dRect(x - Wc / 2 + 18 * s, y - 360 * s, Wc - 36 * s, 110 * s, 6 * s, { fill: 'rgba(200,230,245,0.55)', w: 3 * s, seed: 64, off: 0 });
  const n = o.n ?? 4, gap = (Wc - 130 * s) / Math.max(1, n - 1), sc = Math.min(0.62, 0.62 * 4 / n);
  for (let i = 0; i < n; i++) simit(x - Wc / 2 + 65 * s + i * gap, y - 300 * s, sc * s, 70 + i);
  dRect(x - 120 * s, y - 210 * s, 240 * s, 70 * s, 8 * s, { fill: DF.cream, w: 3 * s, seed: 66 });
  dText(o.sign ?? 'SİMİT', x, y - 158 * s, 62 * s, { c: DF.red });
  return { topY: y - 360 * s };
}
function bill(x, y, s = 1, rot = 0, o = {}) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
  dRect(-50 * s, -26 * s, 100 * s, 52 * s, 5 * s, { fill: DF.money, w: 3 * s, seed: o.seed ?? 3, off: 3 });
  dEll(0, 0, 16 * s, 16 * s, { w: 2.4 * s, seed: (o.seed ?? 3) + 1 });
  dText('₺', 0, 10 * s, 30 * s);
  ctx.restore();
}
function coin(x, y, s = 1) { dEll(x, y, 22 * s, 22 * s, { fill: DF.yellow, w: 3 * s }); dText('₺', x, y + 10 * s, 30 * s); }
function priceTag(x, y, s, label, o = {}) {   // ipten sallanan etiket
  const sw = (o.swing ?? 0) * Math.sin(TT * TAU * 0.9);
  ctx.save(); ctx.translate(x, y); ctx.rotate(sw);
  dLine(0, -70 * s, 0, -10 * s, { w: 2.5 * s, c: DF.penSoft });
  d([[-70 * s, 0], [70 * s, 0], [92 * s, 45 * s], [70 * s, 90 * s], [-70 * s, 90 * s]], { closed: true, fill: o.fill ?? DF.cream, w: 3.6 * s, seed: 21 });
  dEll(-48 * s, 45 * s, 8 * s, 8 * s, { w: 2.6 * s, off: 0 });
  if (label) dText(label, 12 * s, 70 * s, 70 * s, { c: o.c ?? DF.pen });
  ctx.restore();
}
function bank(x, y, s = 1, o = {}) {   // (x, y) = taban ortası
  dRect(x - 180 * s, y - 230 * s, 360 * s, 230 * s, 6 * s, { fill: '#E6EEF8', w: 3.6 * s, seed: 31 });
  for (let i = 0; i < 3; i++) dRect(x - 140 * s + i * 100 * s, y - 180 * s, 76 * s, 80 * s, 4 * s, { fill: 'rgba(160,200,235,0.7)', w: 3 * s, seed: 32 + i, off: 2 });
  dRect(x - 40 * s, y - 90 * s, 80 * s, 90 * s, 4 * s, { fill: DF.green, w: 3 * s, seed: 36 });
  dRect(x - 190 * s, y - 300 * s, 380 * s, 70 * s, 6 * s, { fill: DF.green, w: 3.6 * s, seed: 38 });
  dText(o.label ?? 'BANKA', x, y - 248 * s, 56 * s, { c: '#fff' });
}
function arrow(x1, y1, x2, y2, o = {}) {
  const pr = o.prog ?? 1; if (pr <= 0) return;
  const ex = x1 + (x2 - x1) * pr, ey = y1 + (y2 - y1) * pr, a = Math.atan2(ey - y1, ex - x1), Lh = o.head ?? 24;
  d([[x1, y1], [(x1 + ex) / 2 + (o.bend ?? 0), (y1 + ey) / 2 - (o.bend ?? 0)], [ex, ey]], { w: o.w ?? 4.5, c: o.c, seed: o.seed ?? 61 });
  d([[ex - Lh * Math.cos(a - 0.45), ey - Lh * Math.sin(a - 0.45)], [ex, ey], [ex - Lh * Math.cos(a + 0.45), ey - Lh * Math.sin(a + 0.45)]], { w: o.w ?? 4.5, c: o.c, seed: (o.seed ?? 61) + 1 });
}
// defter grafiği: kareli zemine oturan eksenler + kalemle çizilen seriler
function chart(x, y, w, hh, series, o = {}) {
  dLine(x, y, x, y - hh, { w: 4, seed: 71 }); dLine(x, y, x + w, y, { w: 4, seed: 72 });
  arrow(x, y - hh + 10, x, y - hh - 30, { w: 4, head: 18, seed: 73 }); arrow(x + w - 10, y, x + w + 30, y, { w: 4, head: 18, seed: 74 });
  for (const sr of series) {
    const P = sr.v.map((v, i) => [x + (i / (sr.v.length - 1)) * w, y - v * hh]);
    d(P, { w: sr.w ?? 7, c: sr.c, prog: sr.prog ?? 1, seed: sr.seed ?? 75, amp: 1.0 });
    if (sr.label && (sr.prog ?? 1) > 0.95) { const e = P[P.length - 1]; dText(sr.label, e[0] - 6, e[1] - 26, 64, { c: sr.c, align: 'right' }); }
  }
}
// defter kapağı (seri açılışı): yeşil karton kapak + beyaz etiket
function cover(title, sub, o = {}) {
  fillAll(DF.cover);
  ctx.save(); ctx.globalAlpha = 0.08; for (let i = 0; i < 60; i++) { ctx.fillStyle = i % 2 ? '#000' : '#fff'; ctx.fillRect(0, i * 34, W, 2); } ctx.restore();
  spiral();
  ctx.save(); ctx.translate(540, 760); ctx.rotate(-0.02);
  ctx.fillStyle = 'rgba(0,0,0,0.22)'; ctx.fillRect(-372, -232, 760, 480);
  ctx.fillStyle = DF.page; ctx.fillRect(-380, -240, 760, 480);
  ctx.strokeStyle = DF.margin; ctx.lineWidth = 3; ctx.strokeRect(-356, -216, 712, 432);
  ctx.restore();
  dText('EKONOMİ', 540, 700, 150, { c: DF.pen }); dText('DEFTERİ', 540, 840, 150, { c: DF.pen });
  if (o.no) dText(`sayfa ${o.no}`, 540, 940, 60, { c: DF.red, weight: 600 });
  if (title) hiText(title, 540, 1180, o.tsize ?? 96, { c: '#fff', hc: 'rgba(255,201,77,0.9)', prog: o.prog ?? 1 });
  if (sub) dText(sub, 540, 1280, 60, { c: 'rgba(255,255,255,0.85)', weight: 500 });
  dText('ParaFOMO', 540, H - 300, 58, { c: 'rgba(255,255,255,0.7)', weight: 600 });
}
// sayfa çevirme geçişi: eski sayfa spirale doğru yukarı katlanır. drawOld(): eski sahneyi çizer.
function pageFlip(drawOld, fx) {
  const e = EZ.io(clamp(fx)), sy = 1 - e;
  if (sy <= 0.002) return;
  ctx.save(); ctx.translate(0, 0); ctx.scale(1, sy); drawOld(); ctx.restore();
  ctx.save(); ctx.globalAlpha = 0.35 * (1 - Math.abs(0.5 - e) * 1.2);   // katlanan sayfanın altına gölge
  const gy = H * sy, g = ctx.createLinearGradient(0, gy, 0, gy + 90);
  g.addColorStop(0, 'rgba(20,30,60,0.6)'); g.addColorStop(1, 'rgba(20,30,60,0)'); ctx.fillStyle = g; ctx.fillRect(0, gy, W, 90); ctx.restore();
}
// buzdolabı (beyaz eşya); (x, y) = taban ortası, ~480 px boy @1
function fridge(x, y, s = 1, o = {}) {
  const w = 220 * s, h = 480 * s;
  dRect(x - w / 2, y - h, w, h, 18 * s, { fill: o.fill ?? '#DDE9EF', w: 3.6 * s, seed: 91 });
  dLine(x - w / 2 + 6 * s, y - h * 0.68, x + w / 2 - 6 * s, y - h * 0.68, { w: 3.2 * s, seed: 92 });
  dLine(x - w / 2 + 28 * s, y - h + 40 * s, x - w / 2 + 28 * s, y - h * 0.68 - 30 * s, { w: 7 * s, c: '#8C98A4', seed: 93 });
  dLine(x - w / 2 + 28 * s, y - h * 0.68 + 30 * s, x - w / 2 + 28 * s, y - h * 0.68 + 130 * s, { w: 7 * s, c: '#8C98A4', seed: 94 });
  dEll(x - w * 0.3, y - 4 * s, 14 * s, 6 * s, { fill: '#30343F', w: 2 * s, off: 0 }); dEll(x + w * 0.3, y - 4 * s, 14 * s, 6 * s, { fill: '#30343F', w: 2 * s, off: 0 });
}
// el çizimi saat; ibreler TT ile döner (o.speed: tur/sn)
function clock(x, y, r, o = {}) {
  dEll(x, y, r, r, { fill: o.fill ?? DF.cream, w: 4, seed: 95 });
  for (let i = 0; i < 12; i++) { const a = i / 12 * TAU; dLine(x + Math.cos(a) * r * 0.82, y + Math.sin(a) * r * 0.82, x + Math.cos(a) * r * 0.92, y + Math.sin(a) * r * 0.92, { w: 3, seed: 96 + i }); }
  const sp = o.speed ?? 0.5, a1 = TT * TAU * sp - Math.PI / 2, a2 = TT * TAU * sp / 12 - Math.PI / 2;
  dLine(x, y, x + Math.cos(a1) * r * 0.75, y + Math.sin(a1) * r * 0.75, { w: 4.5, seed: 110 });
  dLine(x, y, x + Math.cos(a2) * r * 0.5, y + Math.sin(a2) * r * 0.5, { w: 6, seed: 111 });
  dEll(x, y, 6, 6, { fill: DF.pen, w: 2, off: 0 });
}
