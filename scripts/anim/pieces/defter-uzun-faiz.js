// =====================================================================
//  EKONOMİ DEFTERİ · UZUN BÖLÜM 2: FAİZ NEDİR? (16:9, 1920x1080) — kits/defter.js
//  Sahneler satır başlangıçlarına bağlı (cue); eylemler gerçek kelime zamanına (wAt).
//  Tutarlar ÖRNEK ("örnek" etiketli). Gerçek veri kartları kaynaklı: TCMB PPK 22 Ekim 2026 (%36), TCMB haftalık
//  mevduat/kredi faizleri (Ekim 2026: 3 aya kadar mevduat %37,6; ihtiyaç kredisi yıllık bileşik %61,5),
//  kredi kartı azami akdi faiz aylık %3,25–4,25 (Kasım 2026), enflasyon hedefi %5.
//  Hesaplar: 10.000×1,4=14.000 · basit 2y 18.000 · bileşik 2y 19.600 · ln2/ln1,4≈2,06 yıl · 100.000×0,4×92/365≈10.082
//           · 1,04¹²−1≈%60 · taksit 100.000/12ay/%4 ≈ 10.655 (toplam ≈127.860) · 1,40/1,30−1≈%7,7 · 50.000×0,36×90/365≈4.438
// =====================================================================
BR.capFont = `700 64px ${CAV}`; BR.capText = DF.pen; BR.capStroke = 'rgba(251,250,243,0.95)'; BR.capHi = DF.yellow;
const SCN = ['hook', 'plan', 'd1', 'd2', 'd3', 'b1', 'b3', 'm1', 'm3', 'k1', 'k3', 'k4', 'v1', 'p1', 'p3', 'tb1', 'e1', 'r1', 'f1', 'h1', 'i0', 's1', 's3'];
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
const TAG = 'Ekonomi Defteri · Uzun Bölüm 2';
const PT = (str, t) => pageTitle(str, { no: 2, tag: TAG, prog: clamp(t / 0.6) });
const fade = (k, fn) => { if (k <= 0) return; ctx.save(); ctx.globalAlpha *= k; fn(); ctx.restore(); };
const fmt = (v) => Math.round(v).toLocaleString('tr-TR');

// ---- bu bölümün eşyaları
function house(x, y, s = 1) {
  dRect(x - 70 * s, y - 110 * s, 140 * s, 110 * s, 4 * s, { fill: '#F4D9B0', w: 3.4 * s, seed: 211 });
  d([[x - 92 * s, y - 104 * s], [x, y - 180 * s], [x + 92 * s, y - 104 * s]], { closed: true, fill: DF.red, w: 3.4 * s, seed: 212 });
  dRect(x - 18 * s, y - 60 * s, 36 * s, 60 * s, 3 * s, { fill: DF.green, w: 3 * s, seed: 213 });
}
function stack(x, y, n, s = 1, seed = 700) {   // n banknot üst üste; (x, y) taban
  for (let i = 0; i < n; i++) bill(x + (i % 2) * 4 * s, y - i * 14 * s, 1.5 * s, 0, { seed: seed + i });
}
function jar(x, y, lvl, label, col, seed = 251) {
  dRect(x - 100, y - 10 - 270 * lvl, 200, 270 * lvl, 18, { fill: col, c: false, seed: seed + 1, off: 0 });
  dRect(x - 110, y - 300, 220, 300, 30, { w: 4, seed });
  dRect(x - 80, y - 330, 160, 34, 8, { fill: DF.kraft, w: 3.4, seed: seed + 2 });
  dText(label, x, y - 360, 60);
}
function check(x, y, k, s = 1) {
  if (k > 0) d([[x - 20 * s, y], [x - 4 * s, y + 18 * s], [x + 28 * s, y - 26 * s]], { w: 7 * s, c: DF.green, prog: k, seed: 271 });
}
function xMark(x, y, r, k) {
  if (k <= 0) return;
  dLine(x - r, y - r, x + r, y + r, { w: 8, c: DF.red, prog: clamp(k * 2), seed: 281 });
  dLine(x + r, y - r, x - r, y + r, { w: 8, c: DF.red, prog: clamp(k * 2 - 1), seed: 282 });
}
function clockAt(x, y, r, hh, mm) {
  dEll(x, y, r, r, { fill: DF.cream, w: 4, seed: 301 });
  for (let i = 0; i < 12; i++) { const a = i / 12 * TAU; dLine(x + Math.cos(a) * r * 0.8, y + Math.sin(a) * r * 0.8, x + Math.cos(a) * r * 0.92, y + Math.sin(a) * r * 0.92, { w: 3, seed: 302 + i }); }
  const ah = ((hh % 12) + mm / 60) / 12 * TAU - Math.PI / 2, am = mm / 60 * TAU - Math.PI / 2;
  dLine(x, y, x + Math.cos(ah) * r * 0.5, y + Math.sin(ah) * r * 0.5, { w: 7, seed: 315 });
  dLine(x, y, x + Math.cos(am) * r * 0.75, y + Math.sin(am) * r * 0.75, { w: 4.5, seed: 316 });
  dEll(x, y, 6, 6, { fill: DF.pen, w: 2, off: 0 });
}
function calPage(x, y, w, h, num, label) {
  dRect(x, y, w, h, 10, { fill: '#fff', w: 4, seed: 321 });
  dRect(x, y, w, h * 0.26, 10, { fill: DF.red, w: 4, seed: 322, off: 0 });
  dText(label, x + w / 2, y + h * 0.19, 40, { c: '#fff' });
  dText(num, x + w / 2, y + h * 0.84, h * 0.5);
}
function card(x, y, w, h, k, seed, fill = DF.cream) {
  if (k <= 0) return false;
  ctx.save(); ctx.globalAlpha *= k; ctx.translate(x + w / 2, y + h / 2); ctx.scale(0.88 + 0.12 * k, 0.88 + 0.12 * k); ctx.translate(-(x + w / 2), -(y + h / 2));
  dRect(x, y, w, h, 16, { fill, w: 4, seed });
  return true;
}
const endCard = () => ctx.restore();
function creditCard(x, y, s = 1, o = {}) {
  dRect(x - 160 * s, y - 100 * s, 320 * s, 200 * s, 18 * s, { fill: o.fill ?? '#C7B4F0', w: 3.6 * s, seed: 821 });
  ctx.fillStyle = 'rgba(42,37,32,0.75)'; ctx.fillRect(x - 160 * s, y - 60 * s, 320 * s, 34 * s);
  dRect(x - 120 * s, y + 10 * s, 70 * s, 50 * s, 6 * s, { fill: DF.yellow, w: 2.5 * s, seed: 822 });
  dText('•••• 2026', x + 40 * s, y + 80 * s, 34 * s, { c: DF.pen });
}
function balance(x, y, tilt) {   // terazi; tilt −1..1 (+ = sağ kefe ağır). Dönüş: kefe merkezleri
  dLine(x, y, x, y - 260, { w: 8, seed: 801 }); dRect(x - 120, y, 240, 24, 8, { fill: DF.kraft, w: 3.4, seed: 802 });
  const a = tilt * 0.16;
  ctx.save(); ctx.translate(x, y - 260); ctx.rotate(a);
  dLine(-380, 0, 380, 0, { w: 8, seed: 803 });
  for (const s of [-1, 1]) { dLine(s * 380, 0, s * 380, 110, { w: 3, c: DF.penSoft, seed: 804 }); dRect(s * 380 - 120, 110, 240, 26, 8, { fill: DF.cream, w: 3.4, seed: 806 + s }); }
  ctx.restore();
  const pan = (s) => [x + Math.cos(a) * s * 380, y - 260 + Math.sin(a) * s * 380 + 110];
  return { left: pan(-1), right: pan(1) };
}
function pedal(x, y, label, pressed, col) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(0.05 + pressed * 0.25);
  dRect(-70, -90, 140, 90, 14, { fill: col, w: 3.6, seed: 811 }); ctx.restore();
  dLine(x, y, x, y + 26, { w: 6, seed: 812 }); dText(label, x, y + 72, 44);
}
function flow(x, y, w, items, keys, o = {}) {   // dikey akış kartları: items[i] keys[i] (0..1) ile gelir
  items.forEach((s, i) => {
    const k = keys[i], yy = y + i * (o.gap ?? 150);
    if (!card(x, yy, w, 100, k, 500 + i, i === items.length - 1 ? (o.lastFill ?? '#D9F2E4') : DF.cream)) return;
    dText(s, x + w / 2, yy + 66, o.size ?? 50, { c: i === items.length - 1 ? (o.lastC ?? DF.green) : DF.pen }); endCard();
    if (i > 0 && k > 0.5) arrow(x + w / 2, yy - 44, x + w / 2, yy - 6, { w: 4, head: 16, seed: 505 + i, prog: k });
  });
}

// 0 — açılış kartı: 10.000 → 14.000 (yeşil) / 10.000 → 16.000 (kırmızı)
function sHook(t) {
  titleCard('Faiz nedir?', 'Paranın kirası: mevduat, kredi, politika faizi', { no: 2, noText: 'UZUN BÖLÜM 2', prog: clamp((t - 0.3) / 0.7) });
  bank(1600, 900, 0.9, { label: 'BANKA' });
  const k1 = KW('hook', '14.000', 0.5), k2 = KW('hook', '16.000', 0.5);
  fade(k1, () => { dText('yatırırsan', 250, 400, 44, { c: DF.cream }); priceTag(250, 495, 0.85, '14.000 ₺', { swing: 0.05, c: DF.green }); });
  fade(k2, () => { dText('çekersen', 570, 400, 44, { c: DF.cream }); priceTag(570, 495, 0.85, '16.000 ₺', { swing: 0.05, c: DF.red }); });
  kid(330, 930, 0.95, { ...MERT, pose: k2 > 0.3 ? 'think' : 'idle', k: 1, face: 1, mood: k2 > 0.3 ? 'wow' : 'calm' });
}
// 1 — bu sayfada
function sPlan(t) {
  paper(); PT('Bu sayfada neler var?', t);
  const items = [['1. Faiz nedir?', 'olduğunu,'], ['2. Basit ve bileşik faiz', 'bileşik'], ['3. Mevduat ve kredi faizi', 'kredi'], ['4. Politika faizi', 'politika'], ['5. Reel faiz', 'reel'], ['6. Faiz ve dolar', 'dolar']];
  items.forEach(([s, w], i) => {
    const k = KW('plan', w, 0.4), y = 300 + i * 105;
    dText(s, 260, y, 72, { align: 'left', al: Math.max(0.25, k) });
    dRect(170, y - 48, 54, 54, 8, { w: 3.4, seed: 330 + i }); check(197, y - 22, k, 1.1);
  });
  fade(KW('plan', 'örneklerle', 0.5), () => sticky(1080, 250, 360, 150, ['örneklerle!'], { size: 64, rot: 0.05 }));
  kid(1550, GY, 1.15, { ...MERT, pose: 'point', k: KS('plan', 0.6), face: -1, mood: 'happy' });
}
// 2 — kira ↔ faiz
function sRent(t) {
  paper(); PT('Faiz nedir?', t);
  const a = clamp(t / 0.6);
  fade(a, () => { dRect(150, 230, 1620, 150, 16, { fill: DF.cream, w: 4, seed: 341 }); dText('Parayı bir süreliğine kullanmanın bedeli', 960, 330, 76); });
  const kH = KW('d1', 'ev', 0.6), kP = KW('d1', 'para', 0.6);
  fade(kH, () => { house(520, 820, 1.5); priceTag(520, 420, 0.95, 'kira', { swing: 0.04 }); dText('ev kiralarsın → kira ödersin', 520, 930, 50, { c: DF.penSoft }); });
  fade(kP, () => { stack(1340, 840, 9, 1.1, 700); priceTag(1340, 420, 0.95, 'faiz', { swing: 0.04, c: DF.red }); dText('para kiralarsın → faiz ödersin', 1340, 930, 50, { c: DF.penSoft }); });
  if (kH > 0.5 && kP > 0.5) dText('=', 960, 760, 120, { c: DF.penSoft, al: Math.min(kH, kP) });
}
// 3 — borç alan · banka · borç veren
function sBank(t) {
  paper(); PT('Banka aracıdır', t);
  bank(960, 880, 1.2, { label: 'BANKA' });
  const kA = KS('d2', 0.5), kV = KW('d2', 'veren', 0.5), kM = KW('d2', 'mevduata', 0.5), kK = KW('d2', 'krediye', 0.5), kF = KW('d2', 'arası', 0.6);
  kid(330, GY, 1.0, { ...MERT, pose: 'idle', k: 1, face: 1, mood: kK > 0.3 ? 'sad' : 'calm' });
  fade(kA, () => dText('borç alan', 330, 980, 46, { c: DF.penSoft }));
  kid(1590, GY, 1.0, { pose: 'idle', k: 1, face: -1, hoodie: DF.green, glasses: false, mood: kM > 0.3 ? 'happy' : 'calm', seed: 30 });
  fade(kV, () => dText('borç veren', 1590, 980, 46, { c: DF.penSoft }));
  if (kM > 0) { arrow(1480, 560, 1180, 560, { prog: kM, w: 5, seed: 351, c: DF.green }); dText('mevduat', 1330, 520, 44, { c: DF.penSoft, al: kM }); arrow(1180, 660, 1480, 660, { prog: kM, w: 5, seed: 352, c: DF.green }); hiText('faiz %40', 1330, 740, 54, { c: DF.green, prog: kM, hc: DF.hiG }); }
  if (kK > 0) { arrow(740, 560, 440, 560, { prog: kK, w: 5, seed: 353, c: DF.red }); dText('kredi', 590, 520, 44, { c: DF.penSoft, al: kK }); arrow(440, 660, 740, 660, { prog: kK, w: 5, seed: 354, c: DF.red }); hiText('faiz %60', 590, 740, 54, { c: DF.red, prog: kK, hc: DF.hiP }); }
  fade(kF, () => sticky(760, 230, 400, 150, ['aradaki fark =', 'bankanın kazancı'], { size: 46, c: '#FFF08A', rot: 0.03 }));
  dText('oranlar örnek', 1700, 300, 40, { c: DF.penSoft, rot: 0.08, al: kM });
}
// 4 — %40 ne demek + oranı belirleyen 3 şey
function sRate(t) {
  paper(); PT('Yüzde 40 ne demek?', t);
  const k = KW('d3', '40', 0.5), kk = KW('d3', '140', 0.5);
  fade(k, () => { coin(520, 520, 2.4); dText('100 ₺', 520, 650, 64); });
  if (kk > 0) { arrow(640, 520, 860, 520, { prog: kk, w: 6, seed: 361, c: DF.green }); clockAt(750, 400, 60, 12, 0); dText('1 yıl', 750, 300, 44, { c: DF.penSoft }); }
  fade(kk, () => { coin(980, 520, 2.4); coin(1080, 500, 1.4); dText('140 ₺', 1020, 650, 64, { c: DF.green }); hiText('+40 ₺ kira', 1020, 740, 54, { c: DF.green, hc: DF.hiG }); });
  if (ON('d4')) {
    const C = [['süre', 'süre', (x, y) => clockAt(x, y, 54, 3, 0)], ['risk', 'riski', (x, y) => { dEll(x, y, 54, 54, { fill: '#FFD6E4', w: 4, seed: 371 }); dText('!', x, y + 22, 64, { c: DF.red }); }], ['enflasyon beklentisi', 'enflasyon', (x, y) => arrow(x - 30, y + 40, x + 30, y - 40, { w: 6, c: DF.red, seed: 372 })]];
    dText('Oranı ne belirler?', 1500, 300, 56, { c: DF.penSoft, al: KS('d4', 0.5) });
    C.forEach(([s, w, fn], i) => { const kc = KW('d4', w, 0.5), y = 420 + i * 170; if (!card(1270, y - 60, 470, 130, kc, 380 + i)) return; fn(1340, y + 5); dText(s, 1560, y + 18, 44); endCard(); });
  }
  if (ON('d5')) fade(KW('d5', '100', 0.5), () => sticky(140, 800, 760, 130, ['100 baz puan = 1 puan  (%37 → %36)'], { size: 44, c: '#FFF08A', rot: -0.02 }));
}
// 5 — basit vs bileşik: iki sütun
function sSimple(t) {
  paper(); PT('Basit mi, bileşik mi?', t);
  dText('BASİT', 520, 290, 60, { c: DF.penSoft }); dText('BİLEŞİK', 1400, 290, 60, { c: DF.penSoft });
  const Y = 860, cols = [[380, '0. yıl', 10, 10000, KW('b1', '10.000', 0.5)], [540, '1. yıl', 14, 14000, KW('b1', '4.000', 0.5)], [700, '2. yıl', 18, 18000, KW('b1', '18.000', 0.5)]];
  cols.forEach(([x, lab, n, v, k], i) => fade(k, () => { stack(x, Y, n, 0.9, 400 + i * 20); dText(fmt(v) + ' ₺', x, Y - n * 13 - 40, 40); dText(lab, x, Y + 78, 40, { c: DF.penSoft }); }));
  const r0 = KS('b2', 0.5), r2 = KW('b2', '19.600', 0.5);
  [[1260, '0. yıl', 10, 10000, r0], [1420, '1. yıl', 14, 14000, r0], [1580, '2. yıl', 20, 19600, r2]].forEach(([x, lab, n, v, k], i) => fade(k, () => { stack(x, Y, n, 0.9, 460 + i * 20); dText(fmt(v) + ' ₺', x, Y - n * 13 - 40, 40, { c: i === 2 ? DF.green : DF.pen }); dText(lab, x, Y + 78, 40, { c: DF.penSoft }); }));
  fade(KW('b1', '4.000', 0.5), () => sticky(300, 360, 440, 120, ['her yıl 4.000 ₺ (örnek)'], { size: 40, rot: -0.03 }));
  fade(KW('b2', '5.600', 0.5), () => sticky(1180, 360, 440, 120, ['2. yıl: 14.000 × %40 = 5.600 ₺'], { size: 38, c: '#D9F2E4', rot: 0.03 }));
  if (r2 > 0.9) { dEll(1580, Y - 300, 110, 60, { w: 5, c: DF.red, prog: clamp((TT - wAt('b2', '19.600') - 0.5) / 0.6), seed: 481 }); }
}
// 6 — bileşik zamanla büyür: grafik + dost/düşman
function sCompound(t) {
  paper(); PT('Bileşik: zamanla büyür', t);
  const basit = [0.19, 0.26, 0.33, 0.41, 0.48, 0.56], bil = [0.19, 0.26, 0.36, 0.51, 0.71, 1.0];
  const X = 160, Y = 860, Wc = 760, Hc = 560, p1 = KS('b3', 1.4, 0.2), p2 = KS('b3', 1.8, 0.6);
  chart(X, Y, Wc, Hc, [{ v: basit, c: DF.penSoft, prog: p1, label: 'basit', seed: 75 }, { v: bil, c: DF.red, prog: p2, label: 'bileşik', seed: 77 }]);
  for (let i = 0; i <= 5; i++) dText(`${i}`, X + i / 5 * Wc, Y + 50, 36, { c: DF.penSoft });
  dText('yıl', X + Wc + 20, Y + 50, 36, { c: DF.penSoft }); dText('%40 · örnek', X + 120, Y - Hc - 20, 40, { c: DF.penSoft });
  fade(KW('b3', 'ikiye', 0.5), () => sticky(1100, 260, 520, 150, ['≈ 2 yıl 1 ayda', 'para ikiye katlanır'], { size: 50, c: '#FFD6E4', rot: 0.03 }));
  const kD = KW('b4', 'mevduatta', 0.5), kB = KW('b4', 'kredi', 0.5);
  fade(kD, () => sticky(1060, 480, 360, 140, ['mevduatta', 'dost 🙂'], { size: 50, c: '#D9F2E4', rot: -0.04 }));
  fade(kB, () => sticky(1460, 480, 400, 140, ['kart borcunda', 'düşman'], { size: 50, c: '#FFD6E4', rot: 0.04 }));
  kid(1250, GY, 0.9, { ...MERT, pose: kB > 0.3 ? 'sad' : 'cheer', k: Math.max(kD, kB), face: 1, mood: kB > 0.3 ? 'sad' : kD > 0.3 ? 'happy' : 'calm' });
  kid(1660, GY, 0.9, { pose: kB > 0.3 ? 'sad' : 'idle', k: kB, face: -1, hoodie: '#F29BB8', glasses: false, mood: kB > 0.3 ? 'sad' : 'calm', seed: 41 });
}
// 7 — mevduat: Mert bankaya verir, faiz döner + gerçek veri
function sDeposit(t) {
  paper(); PT('Mevduat faizi', t);
  const vb = bank(1000, 880, 1.1, { label: 'MEVDUAT' });
  const kG = KS('m1', 0.6), kF = KW('m1', 'faiz', 0.5);
  const m = kid(420, GY, 1.0, { ...MERT, pose: 'give', k: kG, face: 1, mood: kF > 0.3 ? 'happy' : 'calm' });
  const mt = ease((TT - L('m1').t0 - 0.2) / 0.9);
  if (mt > 0 && mt < 1) bill(lerp(m.hand[0], 900, mt), lerp(m.hand[1], 760, mt) - Math.sin(mt * Math.PI) * 120, 1.1, mt * 0.5);
  if (kF > 0) { arrow(880, 620, 560, 620, { prog: kF, w: 6, seed: 391, c: DF.green, bend: 40 }); hiText('faiz', 660, 500, 60, { c: DF.green, prog: kF, hc: DF.hiG }); }
  dText('bankaya borç veriyorsun', 420, 990, 44, { c: DF.penSoft, al: kG });
  fade(KW('m2', '37,6', 0.6), () => { sticky(1280, 260, 560, 250, ['3 aya kadar vade', 'ortalama yıllık %37,6', 'TCMB · Ekim 2026'], { size: 52, c: '#D9F2E4', rot: 0.03 }); });
  fade(KW('m2', 'vadeye', 0.5), () => dText('oran vadeye göre değişir', 1560, 600, 44, { c: DF.penSoft }));
}
// 8 — brüt mü net mi: 100.000 → ≈10.000 faiz → stopaj
function sNet(t) {
  paper(); PT('Brüt mü, net mi?', t);
  fade(KW('m3', 'çeyreği', 0.5), () => sticky(1300, 250, 520, 150, ['3 ay = yılın çeyreği', 'faiz = oran × 92 ÷ 365'], { size: 44, rot: 0.03 }));
  const k1 = KS('m3', 0.6), k2 = KW('m4', '10.000', 0.6), k3 = KW('m4', 'stopaj', 0.6), k4 = KW('m4', 'azı', 0.5);
  const base = 840, sc = 0.0052;
  fade(k1, () => { dRect(260, base - 100000 * sc, 240, 100000 * sc, 8, { fill: '#C7D8F0', w: 4, seed: 601 }); dText('100.000 ₺', 380, base - 100000 * sc - 30, 54); dText('ana para · 3 ay', 380, base + 60, 44, { c: DF.penSoft }); });
  if (k2 > 0) { dRect(620, base - 10000 * sc * 8 * k2, 240, 10000 * sc * 8 * k2, 8, { fill: DF.money, w: 4, seed: 602 }); if (k2 > 0.9) dText('≈ +10.000 ₺', 740, base - 10000 * sc * 8 - 30, 54, { c: DF.green }); dText('brüt faiz', 740, base + 60, 44, { c: DF.penSoft, al: k2 }); }
  if (k3 > 0) {
    ctx.save(); ctx.globalAlpha *= k3; dRect(980, base - 10000 * sc * 8, 240, 10000 * sc * 8 * 0.18, 8, { fill: '#F4B7A6', w: 4, seed: 603 }); dText('stopaj', 1100, base - 10000 * sc * 8 - 30, 50, { c: DF.red });
    dRect(980, base - 10000 * sc * 8 * 0.82, 240, 10000 * sc * 8 * 0.82, 8, { fill: DF.money, w: 4, seed: 604 }); if (k4 <= 0) dText('net', 1100, base + 60, 44, { c: DF.penSoft }); ctx.restore();
    dLine(1100, base - 10000 * sc * 8 * 0.82 - 4, 1100, base - 10000 * sc * 8 * 0.82 + 4, { w: 6, c: DF.red, seed: 605 });
  }
  fade(k4, () => hiText('net = brüt faiz − stopaj', 1100, base + 62, 46, { c: DF.red, hc: DF.hiP }));
  dText('örnek · yıllık %40', 760, 300, 40, { c: DF.penSoft, rot: -0.06, al: k1 });
  dLine(200, base, 1300, base, { w: 4, seed: 606 });
  if (ON('m5')) fade(KW('m5', 'hoş', 0.5), () => sticky(1300, 440, 520, 190, ['"hoş geldin faizi":', 'ilk ay yüksek, sonra düşer', 'yenilemede oranı kontrol et'], { size: 40, c: '#FFD6E4', rot: 0.03 }));
}
// 9 — kredi: banka verir, faiz döner + gerçek veri
function sCredit(t) {
  paper(); PT('Kredi faizi', t);
  const vb = bank(1000, 880, 1.1, { label: 'KREDİ' });
  const kG = KS('k1', 0.6), kF = KW('k1', 'faizi', 0.5), kU = KW('k1', 'üstündedir', 0.5);
  const m = kid(420, GY, 1.0, { ...MERT, pose: 'give', k: kG, face: 1, mood: kF > 0.3 ? 'sad' : 'calm' });
  const mt = ease((TT - L('k1').t0 - 0.2) / 0.9);
  if (mt > 0 && mt < 1) bill(lerp(900, m.hand[0], mt), lerp(760, m.hand[1], mt) - Math.sin(mt * Math.PI) * 120, 1.1, mt * 0.5);
  if (kF > 0) { arrow(560, 620, 880, 620, { prog: kF, w: 6, seed: 411, c: DF.red, bend: -40 }); hiText('faiz ↑', 660, 500, 60, { c: DF.red, prog: kF, hc: DF.hiP }); }
  dText('bankadan borç alıyorsun', 420, 990, 44, { c: DF.penSoft, al: kG });
  fade(kU, () => dText('kredi faizi > mevduat faizi', 1560, 600, 44, { c: DF.penSoft }));
  fade(KW('k2', '4', 0.6), () => sticky(1280, 250, 560, 250, ['ihtiyaç kredisi', 'aylık ≈%4 → yıllık bileşik %61,5', 'TCMB · Ekim 2026'], { size: 46, c: '#FFD6E4', rot: 0.03 }));
}
// 10 — örnek kredi: 12 taksit
function sLoan(t) {
  paper(); PT('Örnek kredi: 100.000 ₺, 12 ay, aylık %4', t);
  sticky(1480, 230, 360, 120, ['vergiler hariç', 'örnek'], { size: 40, rot: 0.05 });
  const kT = KW('k3', 'taksit', 0.4), kS = KW('k3', '128.000', 0.6), base = 760;
  for (let i = 0; i < 12; i++) {
    const k = clamp(kT * 12 - i); if (k <= 0) continue;
    const x = 200 + i * 125;
    dRect(x, base - 330 * k, 90, 330 * k, 8, { fill: '#F4B7A6', w: 3.4, seed: 620 + i });
    dText(`${i + 1}`, x + 45, base + 46, 36, { c: DF.penSoft });
    if (k > 0.95) dText('10.655', x + 45, base - 350, 30, { rot: -0.6, align: 'left' });
  }
  dLine(170, base, 1720, base, { w: 4, seed: 640 }); dText('ay', 1740, base + 46, 36, { c: DF.penSoft });
  if (kS > 0) { marker(190, base - 165, 1540 * kS, 330, { prog: kS, c: DF.hiP }); hiText('toplam ≈ 128.000 ₺', 960, 920, 64, { c: DF.red, prog: kS, hc: DF.hiP }); dText('faiz ≈ 28.000 ₺', 1500, 920, 48, { c: DF.penSoft, al: kS }); }
}
// 11 — kredi kartı: asgari ödeme + aylık ≠ yıllık
function sCard(t) {
  paper(); PT('Kredi kartı faizi', t);
  creditCard(400, 560, 1.4);
  const kK = KW('k4', 'tamamını', 0.5), kF = KW('k4', 'işler', 0.5), kY = KW('k4', '3,25', 0.6);
  fade(kK, () => { dText('borcun tamamı ödenmedi', 400, 790, 46, { c: DF.penSoft }); });
  if (kF > 0) { arrow(620, 560, 820, 560, { prog: kF, w: 6, seed: 651, c: DF.red }); hiText('kalan borca aylık faiz', 1100, 575, 54, { c: DF.red, prog: kF, hc: DF.hiP }); }
  fade(kY, () => sticky(1320, 240, 520, 220, ['yasal tavan (akdi)', 'aylık %3,25 – %4,25', 'TCMB · Kasım 2026'], { size: 46, c: '#FFF08A', rot: 0.03 }));
  if (ON('k5')) {
    const x1 = KW('k5', 'değildir', 0.5), x2 = KW('k5', '60', 0.5);
    dText('aylık %4 = yıllık %4', 1100, 760, 70, { al: KS('k5', 0.5) }); xMark(1100, 735, 70, x1);
    if (x2 > 0) hiText('yıllık bileşik ≈ %60', 1100, 900, 72, { c: DF.red, prog: x2, hc: DF.hiP });
  }
  kid(1700, GY, 0.85, { ...MERT, pose: 'point', k: KS('k5', 0.5), face: -1, mood: kF > 0.3 ? 'wow' : 'calm' });
}
// 12 — politika faizi: TCMB → bankalar + zincir
function sPolicy(t) {
  paper(); PT('Politika faizi: bankaların bankası', t);
  bank(520, 600, 1.15, { label: 'TCMB' });
  const kR = KW('p1', 'repo', 0.6);
  [260, 520, 780].forEach((x, i) => { bank(x, 940, 0.55, { label: 'BANKA' }); if (kR > 0) arrow(520, 610, x, 760, { prog: kR, w: 4, seed: 661 + i, c: DF.penSoft }); });
  fade(kR, () => dText('1 haftalık repo faizi', 520, 222, 44, { c: DF.penSoft }));
  if (ON('p2')) flow(1080, 250, 760, ['politika faizi ↑', 'bankaların maliyeti ↑', 'mevduat & kredi faizi ↑'], [KS('p2', 0.5), KW('p2', 'maliyeti', 0.5), KW('p2', 'çekilir', 0.5)], { gap: 170, lastFill: '#FFD6E4', lastC: DF.red });
}
// 13 — TCMB ne yaptı: basamak + takvim + hedef
function sDecision(t) {
  paper(); PT('TCMB ne yaptı?', t);
  const k1 = KS('p3', 1.2), k2 = KW('p3', '36', 0.5), k3 = KW('p3', '10', 0.5);
  const X = 200, Y = 780;
  dLine(X, Y, X + 900, Y, { w: 4, seed: 671 });
  const steps = [[38, '2025 sonu'], [37, '22 Oca 2026'], [36, '22 Eki 2026']];
  steps.forEach(([r, lab], i) => {
    const kk = clamp(k1 * 3 - i); if (kk <= 0) return;
    const y = Y - (r - 34) * 110, x0 = X + i * 300, x1 = x0 + 300 * kk;
    dLine(x0, y, x1, y, { w: 8, c: i === 2 ? DF.red : DF.pen, seed: 672 + i });
    if (i > 0) dLine(x0, y - 110, x0, y, { w: 3, c: DF.penSoft, seed: 680 + i });
    dText(`%${r}`, x0 + 150, y - 30, 48, { c: i === 2 ? DF.red : DF.pen, al: kk }); dText(lab, x0 + 150, Y + 50, 36, { c: DF.penSoft, al: kk });
  });
  fade(k2, () => sticky(1180, 240, 560, 220, ['22 Ekim 2026', '%37 → %36 (−1 puan)', 'TCMB PPK'], { size: 52, c: '#FFD6E4', rot: 0.03 }));
  fade(k3, () => { calPage(1280, 520, 200, 220, '10', 'Aralık'); dText('sonraki karar', 1380, 790, 40, { c: DF.penSoft }); });
  fade(KW('p4', '5', 0.6), () => { sticky(1540, 520, 300, 150, ['hedef', '%5'], { size: 60, c: '#D9F2E4', rot: -0.04 }); });
  fade(KS('p4', 0.5), () => dText('derdi enflasyon', 1690, 790, 40, { c: DF.penSoft }));
}
// 14 — faiz enflasyonu nasıl düşürür: iki zincir + pedallar
function sTransmission(t) {
  paper(); PT('Faiz enflasyonu nasıl düşürür?', t);
  flow(120, 240, 560, ['faiz ↑', 'kredi pahalı · mevduat cazip', 'harcama ↓ · birikim ↑', 'fiyat artışı yavaşlar'], [KS('e1', 0.5), KW('e1', 'pahalanır', 0.5), KW('e1', 'mevduat', 0.5), KW('e2', 'yavaşlar', 0.5)], { gap: 125, size: 42 });
  if (ON('e3')) flow(1240, 240, 560, ['faiz ↓', 'kredi ucuz · harcama ↑', 'ekonomi canlanır', 'fiyat baskısı ↑'], [KS('e3', 0.5), KW('e3', 'ucuzlar', 0.5), KW('e3', 'canlanır', 0.5), KW('e3', 'baskı', 0.5)], { gap: 125, size: 42, lastFill: '#FFD6E4', lastC: DF.red });
  fade(KW('e2', 'aylar', 0.5), () => { clockAt(960, 420, 80, 4, 40); dText('etkisi aylar sürer', 960, 560, 44, { c: DF.penSoft }); });
  if (ON('e4')) {
    const kg = KW('e4', 'gaz', 0.4), kf = KW('e4', 'fren', 0.4);
    fade(KS('e4', 0.4), () => { pedal(860, 860, 'gaz: faiz ↓', kg * (1 - kf), DF.money); pedal(1060, 860, 'fren: faiz ↑', kf, '#F4B7A6'); });
  }
  if (ON('e5')) fade(KW('e5', 'aktarım', 0.5), () => { dText('kredi → harcama → fiyat', 960, 630, 40, { c: DF.penSoft }); hiText('aktarım mekanizması', 960, 685, 46, { hc: DF.hi }); });
}
// 15 — reel faiz
function sReal(t) {
  paper(); PT('Reel faiz', t);
  const k1 = KW('r2', 'mevduat', 0.8), k2 = KW('r2', 'enflasyon', 0.8);
  fade(KS('r1', 0.6), () => { jar(350, 870, 0.4 * k1 / 0.45, 'faiz %40', DF.money, 680); jar(720, 870, 0.3 * k2 / 0.45, 'enflasyon %30', '#F4B7A6', 690); dText('örnek', 535, 940, 40, { c: DF.penSoft }); });
  const kX = KW('r2', 'değil;', 0.5);
  if (kX > 0) { dText('%10', 1350, 330, 90, { c: DF.penSoft }); xMark(1350, 300, 60, kX); }
  fade(KW('r2', '1,40', 0.6), () => dText('1,40 ÷ 1,30 − 1', 1350, 480, 90));
  const kR = KW('r2', '7,7', 0.5);
  if (kR > 0) hiText('≈ %7,7 reel', 1350, 600, 90, { c: DF.green, prog: kR, hc: DF.hiG });
  fade(KS('r3', 0.5), () => hiText('enflasyon > faiz → reel faiz eksi', 1350, 760, 56, { c: DF.red, hc: DF.hiP, prog: KS('r3', 0.8) }));
  fade(KS('r4', 0.5), () => sticky(1080, 820, 560, 130, ['enflasyonun üstünde mi,', 'altında mı?'], { size: 44, c: '#FFF08A', rot: 0.02 }));
  kid(1750, GY, 0.85, { ...MERT, pose: KS('r3', 0.5) > 0.3 ? 'think' : 'idle', k: 1, face: -1, mood: KS('r3', 0.5) > 0.3 ? 'wow' : 'calm' });
}
// 16 — faiz, dolar, altın: terazi + Fed
function sFx(t) {
  paper(); PT('Faiz, dolar ve altın', t);
  const up = KW('f1', 'yüksekse', 0.8), dn = KW('f2', 'düşerse', 0.8);
  const tilt = -0.9 * up * (1 - dn) + 0.9 * dn;   // önce TL ağır (sol), sonra döviz/altın ağır (sağ)
  const B = balance(620, 880, tilt);
  for (let i = 0; i < 4; i++) coin(B.left[0] - 45 + i * 30, B.left[1] - 30 - (i % 2) * 20, 1.0);
  dText('TL faizi', B.left[0], B.left[1] + 70, 44, { c: DF.penSoft });
  dEll(B.right[0] - 30, B.right[1] - 32, 26, 26, { fill: DF.yellow, w: 3, seed: 701 }); dText('$', B.right[0] + 30, B.right[1] - 18, 50, { c: DF.green });
  dText('döviz · altın', B.right[0], B.right[1] + 70, 44, { c: DF.penSoft });
  fade(up * (1 - dn), () => sticky(1100, 250, 520, 150, ['faiz yüksek →', 'TL cazip, dövize talep ↓'], { size: 44, c: '#D9F2E4', rot: 0.03 }));
  fade(dn, () => sticky(1100, 250, 520, 150, ['faiz düşük →', 'döviz ve altına talep ↑'], { size: 44, c: '#FFD6E4', rot: 0.03 }));
  fade(KW('f2', 'tek', 0.5), () => dText('tek sebep değil, en güçlülerinden biri', 1360, 450, 40, { c: DF.penSoft }));
  if (ON('f3')) {
    const kf = KS('f3', 0.6), ka = KW('f3', 'dolara', 0.6);
    fade(kf, () => bank(1500, 900, 0.9, { label: 'FED' }));
    if (ka > 0) { arrow(1240, 760, 1400, 760, { prog: ka, w: 6, seed: 711, c: DF.green }); hiText('dolar faizi ↑ → para dolara', 1480, 600, 48, { c: DF.green, prog: ka, hc: DF.hiG }); }
    fade(KW('f3', 'altını', 0.5), () => dText('altın ve gelişen ülke paraları baskılanır', 1480, 930, 36, { c: DF.penSoft }));
  }
}
// 17 — formül
function sFormula(t) {
  paper(); PT('Faiz nasıl hesaplanır?', t);
  fade(KS('h1', 0.6), () => { dRect(150, 250, 1620, 160, 16, { fill: DF.cream, w: 4, seed: 721 }); dText('faiz = ana para × yıllık oran × gün ÷ 365', 960, 355, 76); });
  if (ON('h2')) {
    const a = KS('h2', 0.5), r = KW('h2', '4.438', 0.5);
    dText('50.000 × 0,36 × 90 ÷ 365', 960, 560, 90, { al: a });
    if (r > 0) hiText('≈ 4.438 ₺', 960, 700, 100, { c: DF.green, prog: r, hc: DF.hiG });
    dText('örnek · 90 gün, yıllık %36', 960, 790, 40, { c: DF.penSoft, al: a });
  }
  if (ON('h2b')) fade(KS('h2b', 0.5), () => { ctx.save(); ctx.globalAlpha *= 1; dRect(150, 250, 1620, 160, 16, { fill: DF.cream, w: 4, seed: 721 }); dText('bileşik: ana para × (1 + oran)^yıl  →  10.000 × 1,40² = 19.600 ₺', 960, 355, 60); ctx.restore(); });
  fade(KS('h3', 0.5), () => hiText('parafomo.com/faiz-hesaplama', 960, 920, 60, { hc: DF.hiG, prog: KS('h3', 0.8) }));
  kid(1750, GY, 0.85, { ...MERT, pose: 'point', k: KS('h3', 0.5), face: -1, mood: 'happy' });
}
// 18 — 4 ilke
function sRules(t) {
  paper(); PT('Faizle ilgili 4 ilke', t);
  fade(KW('i0', 'tavsiyesi', 0.5), () => sticky(1440, 230, 380, 130, ['yatırım tavsiyesi', 'değildir'], { size: 46, c: '#FFD6E4', rot: 0.05 }));
  const R = [['i1', 'Her faizi yıllığa çevir, enflasyonla kıyasla'], ['i2', 'Borçta bileşik faiz düşmandır: asgariyle döndürme'], ['i3', 'Mevduatta vade ve stopaj sonrası net getiri'], ['i4', 'Faiz kararlarını takip et: zamanlama fark yaratır']];
  R.forEach(([id, s], i) => {
    const y = 380 + i * 135, k = KS(id, 0.5);
    dRect(160, y - 52, 58, 58, 8, { w: 3.4, seed: 700 + i });
    dText(`${i + 1}. ${s}`, 260, y, 64, { align: 'left', al: Math.max(0.2, k) });
    check(189, y - 24, k, 1.1);
  });
  kid(1640, GY, 1.05, { ...MERT, pose: 'point', k: KS('i1', 0.6), face: -1, mood: 'happy' });
}
// 19 — özet
function sSummary(t) {
  paper(); PT('Özet', t);
  const S = [['faiz = paranın kirası', 's1', 'kirasıdır.'], ['basit: ana paraya', 's1', 'basit'], ['bileşik: faizin faizine', 's1', 'bileşik'],
             ['mevduatta kazan, kredide öde', 's2', 'mevduatta'], ['referans: politika faizi', 's2', 'politika'], ['gerçek kazanç: reel faiz', 's2', 'reel']];
  S.forEach(([s, id, w], i) => {
    const k = KW(id, w, 0.5), x = 150 + (i % 3) * 560, y = 270 + Math.floor(i / 3) * 290;
    fade(k, () => sticky(x, y, 500, 140, [s], { size: s.length > 22 ? 42 : 52, c: ['#FFF08A', '#FFD6E4', '#D9F2E4'][i % 3], rot: ((i * 7) % 5 - 2) * 0.015 }));
  });
}
// 20 — kapanış
function sCta(t) {
  paper(); const a = clamp(t / 0.5);
  hiText('parafomo.com', 960, 290, 120, { prog: clamp((t - 0.3) / 0.6), hc: DF.hiG });
  dText('/faiz-hesaplama', 960, 390, 70, { c: DF.penSoft, al: a });
  const k4 = KS('s4', 0.6);
  if (k4 > 0) {
    dText('sonraki sayfa:', 700, 560, 70, { c: DF.penSoft, al: k4 }); hiText('ASGARİ ÜCRET', 1130, 560, 100, { c: DF.red, prog: k4, hc: DF.hiP });
    const b = clamp(spring(Math.max(0, TT - L('s4').t0 - 0.3), 0.9, { k: 200, damp: 0.45 }));
    if (b > 0.01) { ctx.save(); ctx.translate(960, 760); ctx.scale(b, b);
      ctx.fillStyle = BR.red; ctx.beginPath(); ctx.roundRect(-210, -58, 420, 116, 20); ctx.fill();
      ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.moveTo(-150, -24); ctx.lineTo(-150, 24); ctx.lineTo(-110, 0); ctx.closePath(); ctx.fill();
      ctx.font = `56px ${ANTON}`; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText('ABONE OL', -86, 4); ctx.restore(); }
  }
  kid(1600, GY, 1.0, { ...MERT, pose: 'cheer', k: clamp((t - 0.2) / 0.5), face: -1, mood: 'happy' });
  kid(330, GY, 0.9, { pose: 'cheer', k: k4, face: 1, hoodie: DF.green, glasses: false, mood: 'happy', seed: 30 });
}
// kapak (1280x720'e küçülür): banka + para destesi, sağda iki kelime
function drawThumb() {
  paper({ tint: '#F6F1DA' });
  bank(520, 900, 1.5, { label: 'BANKA' });
  stack(950, 900, 14, 1.5, 730);
  priceTag(950, 420, 1.3, '%40', { swing: 0, c: DF.red });
  hiText('PARANIN', 1460, 430, 230, { c: DF.pen, hc: DF.hi });
  hiText('KİRASI', 1460, 680, 230, { c: DF.red, hc: DF.hiP });
  dText('%40 → ?', 1460, 860, 110, { c: DF.penSoft });
  kid(250, 1060, 1.15, { ...MERT, pose: 'think', k: 1, face: 1, mood: 'wow', t: 0.3 });
  ctx.fillStyle = DF.cover; ctx.fillRect(0, 0, 640, 110);
  dText('EKONOMİ DEFTERİ', 320, 78, 64, { c: DF.cream });
  overlayGrain('multiply', 0.5);
}
// 11b — sabit mi değişken mi + vergiler
function sFixed(t) {
  paper(); PT('Sabit mi, değişken mi?', t);
  const kS = KW('v1', 'sabitse', 0.5), kD = KW('v1', 'değişken', 0.5), kU = KW('v1', 'yükselirse', 0.5);
  if (card(120, 250, 780, 520, kS, 731)) {
    dText('SABİT FAİZ', 510, 330, 60); dLine(200, 560, 820, 560, { w: 7, c: DF.green, seed: 732 });
    for (let i = 0; i < 6; i++) dRect(215 + i * 100, 500, 60, 60, 6, { fill: DF.money, w: 2.5, seed: 740 + i });
    dText('taksit baştan belli', 510, 700, 48, { c: DF.penSoft }); endCard();
  }
  if (card(1020, 250, 780, 520, kD, 735)) {
    dText('DEĞİŞKEN FAİZ', 1410, 330, 60);
    const P = []; for (let i = 0; i <= 24; i++) { const u = i / 24; P.push([1100 + u * 620, 560 - Math.sin(u * 7) * 40 - (kU > 0.5 ? u * 90 : 0)]); }
    d(P, { w: 7, c: DF.red, seed: 736 });
    dText(kU > 0.5 ? 'faiz yükselirse taksit artar' : 'endekse göre yeniden belirlenir', 1410, 700, 48, { c: DF.penSoft }); endCard();
  }
  fade(KS('v2', 0.5), () => sticky(140, 800, 700, 130, ['Türkiye: konut ve ihtiyaç kredisi çoğunlukla sabit'], { size: 38, c: '#D9F2E4', rot: -0.02 }));
  fade(KW('v3', 'vergi', 0.5), () => sticky(1040, 800, 760, 130, ['+ vergi ve fon kesintileri → ilan edilen faiz ≠ toplam maliyet'], { size: 36, c: '#FFD6E4', rot: 0.02 }));
}
// 13b — devlete borç: tahvil
function sBond(t) {
  paper(); PT('Devlete borç: tahvil faizi', t);
  const kG = KS('tb1', 0.6), kF = KW('tb1', 'faiz', 0.5);
  bank(1000, 880, 1.1, { label: 'HAZİNE' });
  const m = kid(420, GY, 1.0, { pose: 'give', k: kG, face: 1, hoodie: DF.green, glasses: false, mood: kF > 0.3 ? 'happy' : 'calm', seed: 30 });
  const mt = ease((TT - L('tb1').t0 - 0.2) / 0.9);
  if (mt > 0 && mt < 1) bill(lerp(m.hand[0], 900, mt), lerp(m.hand[1], 760, mt) - Math.sin(mt * Math.PI) * 120, 1.1, mt * 0.5);
  if (kF > 0) { arrow(880, 620, 560, 620, { prog: kF, w: 6, seed: 751, c: DF.green, bend: 40 }); hiText('tahvil faizi', 640, 500, 56, { c: DF.green, prog: kF, hc: DF.hiG }); }
  dText('yatırımcı', 420, 990, 44, { c: DF.penSoft, al: kG });
  fade(KW('tb2', 'abd', 0.6), () => sticky(1280, 250, 560, 190, ['en çok izlenen faiz:', "ABD 10 yıllık tahvil"], { size: 48, c: '#FFF08A', rot: 0.03 }));
  if (ON('tb3')) {
    const a = KW('tb3', 'mevduat', 0.5), b = KW('tb3', 'tahvil', 0.5);
    fade(a, () => { dText('kısa vade (mevduat)', 1500, 560, 40, { c: DF.penSoft }); dText('→ politika faizi', 1500, 610, 44); });
    fade(b, () => { dText('uzun vade (kredi, tahvil)', 1500, 700, 40, { c: DF.penSoft }); dText('→ enflasyon beklentisi', 1500, 750, 44, { c: DF.red }); });
  }
  fade(KW('tb4', 'kur', 0.5), () => sticky(1240, 820, 600, 120, ['dolar faizi ≠ TL faizi: kur beklentisini kat'], { size: 36, c: '#D9F2E4', rot: 0.02 }));
}
const SDRAW = [sHook, sPlan, sRent, sBank, sRate, sSimple, sCompound, sDeposit, sNet, sCredit, sLoan, sCard, sFixed, sPolicy, sDecision, sBond, sTransmission, sReal, sFx, sFormula, sRules, sSummary, sCta];
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
