// =====================================================================
//  EKONOMİ DEFTERİ · UZUN BÖLÜM 1: ENFLASYON NEDİR? (16:9, 1920x1080) — kits/defter.js
//  Sahneler satır başlangıçlarına bağlı (cue); eylemler gerçek kelime zamanına (wAt).
//  Tutarlar ÖRNEK ("örnek" etiketli). Tek gerçek veri: TÜİK Ekim 2022 yıllık TÜFE %85,51.
//  Hesaplar: 30.000/1,3 ≈ 23.077 · 1,03^12 ≈ 1,4258 · ln2/ln1,3 ≈ 2,64 yıl (≈2 yıl 8 ay) · 1,40/1,30−1 ≈ %7,69
// =====================================================================
BR.capFont = `700 64px ${CAV}`; BR.capText = DF.pen; BR.capStroke = 'rgba(251,250,243,0.95)'; BR.capHi = DF.yellow;
const SCN = ['hook', 'plan', 'def1', 'def3', 'def4', 'm1', 'm3', 'm4', 'm7', 't1', 'c0', 'p1', 'w0', 'w4', 'b1', 'b4', 'r1', 'k0', 's1', 's3'];
const sAt = (i) => (i === 0 ? -1.2 : cue(SCN[i]) - 0.15);
const lt = (i) => TT - sAt(i);
const ease = (x) => EZ.io(clamp(x));
function wAt(id, w) {
  const l = L(id), ws = (l.cap || '').toLocaleLowerCase('tr-TR').split(/\s+/), i = ws.findIndex((x) => x.includes(w));
  if (i < 0) return l.t0;
  return l.words && l.words[i] != null ? l.words[i] : l.t0 + (l.t1 - l.t0) * i / ws.length;
}
const KW = (id, w, dd = 0.5) => ease((TT - wAt(id, w)) / dd);          // kelime söylenince 0→1
const KS = (id, dd = 0.5, off = 0) => ease((TT - L(id).t0 - off) / dd); // satır başlayınca 0→1
const ON = (id) => TT >= L(id).t0 - 0.15;
const MERT = { hoodie: DF.yellow, seed: 1 };
const GY = 900;   // karakterlerin bastığı zemin
const TAG = 'Ekonomi Defteri · Uzun Bölüm 1';
const PT = (str, t) => pageTitle(str, { no: 1, tag: TAG, prog: clamp(t / 0.6) });
const fade = (k, fn) => { if (k <= 0) return; ctx.save(); ctx.globalAlpha *= k; fn(); ctx.restore(); };

// ---- bu bölümün eşyaları
function tomato(x, y, s = 1) {
  dEll(x, y, 50 * s, 44 * s, { fill: DF.red, w: 3.4 * s, seed: 201 });
  d([[x - 18 * s, y - 40 * s], [x, y - 54 * s], [x + 18 * s, y - 40 * s]], { w: 5 * s, c: DF.green, seed: 202 });
}
function house(x, y, s = 1) {
  dRect(x - 70 * s, y - 110 * s, 140 * s, 110 * s, 4 * s, { fill: '#F4D9B0', w: 3.4 * s, seed: 211 });
  d([[x - 92 * s, y - 104 * s], [x, y - 180 * s], [x + 92 * s, y - 104 * s]], { closed: true, fill: DF.red, w: 3.4 * s, seed: 212 });
  dRect(x - 18 * s, y - 60 * s, 36 * s, 60 * s, 3 * s, { fill: DF.green, w: 3 * s, seed: 213 });
}
function bus(x, y, s = 1) {
  dRect(x - 110 * s, y - 130 * s, 220 * s, 110 * s, 14 * s, { fill: '#8DB8E8', w: 3.4 * s, seed: 221 });
  for (let i = 0; i < 3; i++) dRect(x - 95 * s + i * 66 * s, y - 116 * s, 52 * s, 42 * s, 4 * s, { fill: '#E6F2FB', w: 2.5 * s, seed: 222 + i, off: 0 });
  dEll(x - 62 * s, y - 18 * s, 20 * s, 20 * s, { fill: '#30343F', w: 3 * s, seed: 226 }); dEll(x + 62 * s, y - 18 * s, 20 * s, 20 * s, { fill: '#30343F', w: 3 * s, seed: 227 });
}
function bag(x, y, s = 1) {
  d([[x - 30 * s, y - 130 * s], [x - 26 * s, y - 175 * s], [x + 26 * s, y - 175 * s], [x + 30 * s, y - 130 * s]], { w: 4 * s, seed: 232 });
  d([[x - 70 * s, y - 130 * s], [x + 70 * s, y - 130 * s], [x + 85 * s, y], [x - 85 * s, y]], { closed: true, fill: DF.kraft, w: 3.4 * s, seed: 231 });
}
function basket(x, y, s = 1, o = {}) {   // (x, y) = taban ortası
  const w = 260 * s, h = 150 * s, P = [];
  for (let i = 0; i <= 16; i++) { const a = Math.PI * i / 16; P.push([x - w * 0.42 * Math.cos(a), y - h - 110 * s * Math.sin(a)]); }
  d(P, { w: 5 * s, seed: 243 });
  d([[x - w / 2, y - h], [x + w / 2, y - h], [x + w * 0.4, y], [x - w * 0.4, y]], { closed: true, fill: o.fill ?? DF.kraft, w: 3.6 * s, seed: 241 });
  for (let i = 1; i < 4; i++) { const yy = y - h + i * h / 4, dx = w / 2 - w * 0.1 * i / 4; dLine(x - dx + 8 * s, yy, x + dx - 8 * s, yy, { w: 2 * s, c: 'rgba(42,37,32,0.45)', seed: 244 + i }); }
  if (o.label) dText(o.label, x, y - h / 2 + 18 * s, 54 * s, { c: DF.pen });
}
function jar(x, y, lvl, label, col, seed = 251) {
  dRect(x - 100, y - 10 - 270 * lvl, 200, 270 * lvl, 18, { fill: col, c: false, seed: seed + 1, off: 0 });
  dRect(x - 110, y - 300, 220, 300, 30, { w: 4, seed });
  dRect(x - 80, y - 330, 160, 34, 8, { fill: DF.kraft, w: 3.4, seed: seed + 2 });
  dText(label, x, y - 360, 60);
}
function pillow(x, y, s = 1) {
  dRect(x - 160 * s, y - 80 * s, 320 * s, 100 * s, 44 * s, { fill: '#EDE6F5', w: 3.4 * s, seed: 261 });
  d([[x - 60 * s, y - 40 * s], [x, y - 30 * s], [x + 60 * s, y - 40 * s]], { w: 2.4 * s, c: DF.penSoft, seed: 262 });
}
function bubble(x, y, w, h, text, o = {}) {
  d([[x - 24, y + h / 2 - 4], [x - 50, y + h / 2 + 44], [x + 12, y + h / 2 - 4]], { closed: true, fill: '#fff', w: 3.4, seed: (o.seed ?? 270) + 1 });
  dRect(x - w / 2, y - h / 2, w, h, 26, { fill: '#fff', w: 3.4, seed: o.seed ?? 270 });
  dText(text, x, y + (o.size ?? 48) * 0.33, o.size ?? 48, { c: o.c ?? DF.pen });
}
function check(x, y, k, s = 1) {
  if (k > 0) d([[x - 20 * s, y], [x - 4 * s, y + 18 * s], [x + 28 * s, y - 26 * s]], { w: 7 * s, c: DF.green, prog: k, seed: 271 });
}
function xMark(x, y, r, k) {
  if (k <= 0) return;
  dLine(x - r, y - r, x + r, y + r, { w: 8, c: DF.red, prog: clamp(k * 2), seed: 281 });
  dLine(x + r, y - r, x - r, y + r, { w: 8, c: DF.red, prog: clamp(k * 2 - 1), seed: 282 });
}
function pie(cx, cy, r, slices, prog = 1, hi = -1, hk = 0) {
  let a0 = -Math.PI / 2;
  slices.forEach((sl, i) => {
    const a1 = a0 + sl.v * TAU * prog, n = Math.max(3, Math.ceil(sl.v * 48)), am = (a0 + a1) / 2, pop = i === hi ? hk * 26 : 0;
    const ox = Math.cos(am) * pop, oy = Math.sin(am) * pop, P = [[cx + ox, cy + oy]];
    for (let j = 0; j <= n; j++) { const a = a0 + (a1 - a0) * j / n; P.push([cx + ox + Math.cos(a) * r, cy + oy + Math.sin(a) * r]); }
    d(P, { closed: true, fill: sl.c, w: 3.4, seed: 290 + i * 3, off: 3 });
    if (prog > 0.95) dText(sl.label, cx + ox + Math.cos(am) * r * 0.6, cy + oy + Math.sin(am) * r * 0.6 + 14, sl.v < 0.08 ? 34 : 44);
    a0 = a1;
  });
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
  dText(num, x + w / 2, y + h * 0.84, h * 0.58);
}
function card(x, y, w, h, k, seed, fill = DF.cream) {   // ölçeklenerek gelen not kartı
  if (k <= 0) return false;
  ctx.save(); ctx.globalAlpha *= k; ctx.translate(x + w / 2, y + h / 2); ctx.scale(0.88 + 0.12 * k, 0.88 + 0.12 * k); ctx.translate(-(x + w / 2), -(y + h / 2));
  dRect(x, y, w, h, 16, { fill, w: 4, seed });
  return true;
}
const endCard = () => ctx.restore();

// 0 — açılış kartı: simit 10 → 15
function sHook(t) {
  titleCard('Enflasyon nedir?', 'Simit neden her yıl pahalanıyor?', { no: 1, noText: 'UZUN BÖLÜM 1', prog: clamp((t - 0.3) / 0.7) });
  const up = TT > wAt('hook', '15') + 0.2;
  simit(1600, 690, 1.6, 5);
  priceTag(1600, 430, 0.95, up ? '15 ₺' : '10 ₺', { swing: 0.06, c: up ? DF.red : DF.pen });
  kid(330, 930, 0.95, { ...MERT, pose: up ? 'sad' : 'idle', k: 1, face: 1, mood: up ? 'wow' : 'calm' });
}
// 1 — bu sayfada: 5 başlık sırayla işaretlenir
function sPlan(t) {
  paper(); PT('Bu sayfada neler var?', t);
  const items = [['1. Enflasyon nedir?', 'nedir,'], ['2. Nasıl ölçülür?', 'ölçülür,'], ['3. Neden olur?', 'olur,'], ['4. Kimi vurur?', 'vurur'], ['5. Nasıl korunulur?', 'korunulur?']];
  items.forEach(([s, w], i) => {
    const k = KW('plan', w, 0.4), y = 320 + i * 118;
    dText(s, 260, y, 78, { align: 'left', al: Math.max(0.25, k) });
    dRect(170, y - 50, 54, 54, 8, { w: 3.4, seed: 330 + i }); check(197, y - 24, k, 1.1);
  });
  fade(KW('plan', 'örneklerle.', 0.5), () => sticky(1080, 250, 360, 150, ['örneklerle!'], { size: 64, rot: 0.05 }));
  kid(1550, GY, 1.15, { ...MERT, pose: 'point', k: KS('plan', 0.6), face: -1, mood: 'happy' });
}
// 2 — tanım: genel + sürekli, tek ürün değil
function sDef(t) {
  paper(); PT('Enflasyon nedir?', t);
  const a = clamp(t / 0.6);
  fade(a, () => { dRect(150, 230, 1620, 170, 16, { fill: DF.cream, w: 4, seed: 341 }); dText('Fiyatların genel düzeyinin sürekli artması', 960, 340, 82); });
  if (ON('def2')) {
    hiText('genel', 650, 530, 112, { c: DF.green, hc: DF.hiG, prog: KW('def2', 'genel') });
    fade(KW('def2', 'sürekli'), () => dText('+', 960, 530, 100, { c: DF.penSoft }));
    hiText('sürekli', 1270, 530, 112, { c: DF.red, hc: DF.hiP, prog: KW('def2', 'sürekli') });
    const kT = KW('def2', 'domatesin');
    fade(kT, () => { tomato(300, 760, 1.3); dText('sadece domates', 300, 870, 50, { c: DF.penSoft }); });
    xMark(300, 760, 70, KW('def2', 'değildir;', 0.6));
    [['market,', 820, bag], ['kira,', 1150, house], ['ulaşım', 1480, bus]].forEach(([w, x, fn], i) => {
      const k = KW('def2', w, 0.4);
      fade(k, () => { fn(x, 830, 1.05); arrow(x + 120, 800, x + 120, 680, { prog: k, c: DF.red, w: 5, seed: 345 + i * 2 }); });
    });
    const kH = KW('def2', 'birlikte', 0.6);
    if (kH > 0) { dLine(690, 885, 1620, 885, { w: 5, c: DF.green, prog: kH, seed: 352 }); hiText('hepsi birlikte', 1150, 950 - 10, 54, { prog: kH, hc: DF.hiG }); }
  }
}
// 3 — tek zam mı, sürekli artış mı?
function sStairs(t) {
  paper(); PT('Tek zam mı, sürekli artış mı?', t);
  dRect(130, 250, 790, 600, 16, { fill: 'rgba(255,255,255,0.35)', w: 3.4, seed: 361 }); dRect(1000, 250, 790, 600, 16, { fill: 'rgba(255,255,255,0.35)', w: 3.4, seed: 362 });
  dText('bir kere zam', 525, 330, 66, { c: DF.penSoft });
  d([[200, 760], [450, 760], [450, 560], [860, 560]], { w: 7, c: DF.pen, prog: KS('def3', 1.6), seed: 363 });
  const kx = KW('def3', 'değildir;', 0.6); xMark(525, 660, 90, kx);
  if (kx > 0.5) dText('enflasyon değil', 525, 830, 54, { c: DF.red });
  dText('ay be ay', 1395, 330, 66, { c: DF.penSoft });
  const P = []; for (let i = 0; i < 9; i++) { const x = 1060 + i * 78, y = 790 - i * 52; P.push([x, y], [x + 78, y]); if (i < 8) P.push([x + 78, y - 52]); }
  d(P, { w: 7, c: DF.red, prog: KW('def3', 'fiyatlar', 3.0), seed: 364 });
  const kE = KW('def3', 'enflasyondur.', 0.5);
  if (kE > 0) { hiText('enflasyon', 1395, 830, 64, { c: DF.red, prog: kE, hc: DF.hiP }); check(1700, 300, kE, 1.4); }
}
// 4 — aynı para, her ay daha az simit
function sCart(t) {
  paper(); PT('Aynı para, daha az şey', t);
  sticky(150, 250, 330, 170, ['her ay', 'aynı 100 ₺'], { size: 58, rot: -0.05 }); dText('örnek', 420, 470, 44, { c: DF.penSoft, rot: 0.1 });
  const months = [['Ocak', 6], ['Haziran', 5], ['Aralık', 4]];
  months.forEach(([m, n], i) => {
    const x = 800 + i * 400, k = KS('def4', 0.5, 0.4 + i * 0.9);
    fade(k, () => {
      basket(x, 840, 1.05);
      for (let j = 0; j < n; j++) simit(x - (n - 1) * 30 + j * 60, 670 - (j % 2) * 26, 0.62, 400 + i * 10 + j);
      dText(m, x, 900, 56, { c: DF.penSoft });
      dText(`${n} simit`, x, 450, 60, { c: i === 2 ? DF.red : DF.pen });
    });
  });
  const kd = KW('def4', 'az', 0.5);
  kid(330, GY, 1.05, { ...MERT, pose: 'give', k: 1 - kd * 0.7, face: 1, mood: kd > 0.3 ? 'sad' : 'calm' });
}
// 5 — TÜİK sepeti: kalemler sepete düşer
function sBasket(t) {
  paper(); PT('TÜİK enflasyonu nasıl ölçer?', t);
  const kL = KW('m1', 'tüik', 0.5);
  basket(960, 880, 1.7, { label: kL > 0.5 ? 'TÜİK sepeti' : '' });
  fade(KW('m2', 'yüzlerce'), () => sticky(1420, 250, 400, 160, ['yüzlerce', 'ürün ve hizmet'], { size: 54, c: '#D9F2E4', rot: 0.04 }));
  const its = [['ekmek,', 'ekmek'], ['kira,', 'kira'], ['elektrik,', 'elektrik'], ['akaryakıt,', 'akaryakıt'], ['giyim,', 'giyim'], ['ilaç.', 'ilaç']];
  its.forEach(([w, s], i) => {
    if (!ON('m2')) return;
    const k = KW('m2', w, 0.6), col = i % 3, row = Math.floor(i / 3);
    const x = 790 + col * 170, yT = 560 + row * 90, y = lerp(220, yT, k);
    fade(clamp(k * 3), () => { dRect(x - 80, y - 40, 160, 66, 10, { fill: ['#FFF08A', '#FFD6E4', '#D9F2E4'][i % 3], w: 3, seed: 370 + i }); dText(s, x, y + 10, 42); });
  });
  kid(330, GY, 1.0, { ...MERT, pose: 'think', k: KS('m1', 0.6), face: 1, mood: 'calm' });
}
// 6 — ağırlıklar (temsilî)
function sWeights(t) {
  paper(); PT('Her kalemin bir ağırlığı var', t);
  sticky(1500, 230, 300, 120, ['temsilî çizim'], { size: 50, rot: 0.05 });
  const rows = [['gıda', 1.0, 'gıdaya', DF.money], ['konut', 0.8, 'konuta', '#F4B7A6'], ['giyim', 0.3, null, '#C7D8F0'], ['eğitim', 0.16, null, '#C7D8F0'], ['iletişim', 0.14, null, '#C7D8F0']];
  rows.forEach(([nm, v, w, c], i) => {
    const y = 330 + i * 115, k = w ? KW('m3', w, 0.8) : KS('m3', 0.8, 0.5);
    dText(nm, 400, y + 16, 60, { align: 'right' });
    if (k > 0) dRect(440, y - 34, 900 * v * k, 70, 8, { fill: c, w: 3.4, seed: 380 + i });
  });
  const kB = KW('m3', 'endeksi', 0.6);
  if (kB > 0) { arrow(1380, 330, 1380, 470, { prog: kB, w: 4, seed: 390, c: DF.green }); hiText('büyük pay = daha çok etki', 1500, 560, 54, { prog: kB, hc: DF.hiG, align: 'left' }); }
}
// 7 — yıllık değişim + Ekim 2022 zirvesi + açıklama günü
function sYoy(t) {
  paper(); PT('Yıllık enflasyon nasıl açıklanır?', t);
  const kA = KS('m4', 0.5, 0.3), kB = KW('m4', 'geçen', 0.5);
  fade(kA, () => { basket(330, 800, 1.0, { label: '' }); dText('geçen yıl Ekim', 330, 880, 48, { c: DF.penSoft }); dText('1.000 ₺', 330, 500, 66); });
  fade(kB, () => { basket(760, 800, 1.0, { label: '' }); dText('bu yıl Ekim', 760, 880, 48, { c: DF.penSoft }); dText('1.300 ₺', 760, 500, 66, { c: DF.red }); });
  const kY = KW('m4', 'yıllık', 0.5);
  if (kY > 0) { arrow(420, 420, 680, 420, { prog: kY, bend: -30, seed: 401, c: DF.red }); hiText('+%30 yıllık', 545, 350, 62, { c: DF.red, prog: kY, hc: DF.hiP }); }
  dText('örnek', 545, 270, 44, { c: DF.penSoft, al: kA });
  fade(KS('m5', 0.5), () => {
    sticky(1080, 240, 620, 270, ['Ekim 2022', 'yıllık %85,5', 'son 24 yılın zirvesi'], { size: 62, c: '#FFD6E4', rot: -0.03 });
    dText('Kaynak: TÜİK', 1390, 560, 42, { c: DF.penSoft });
  });
  fade(KS('m6', 0.5), () => { calPage(1120, 620, 210, 230, '3', 'her ay'); clockAt(1560, 740, 110, 10, 0); dText('10:00', 1560, 900, 50); });
}
// 8 — senin enflasyonun: iki pasta (temsilî)
function sPersonal(t) {
  paper(); PT('Senin enflasyonun farklı olabilir', t);
  const k1 = KS('m7', 1.0), k2 = KW('m7', 'kira', 1.0), kh = KW('m7', 'benzemez.', 0.5);
  pie(520, 580, 230, [{ v: 0.25, c: DF.money, label: 'gıda' }, { v: 0.15, c: '#F4B7A6', label: 'konut' }, { v: 0.15, c: '#8DB8E8', label: 'ulaşım' }, { v: 0.45, c: '#E9E2CF', label: 'diğer' }], k1);
  dText('ortalama sepet', 520, 880, 56, { c: DF.penSoft });
  if (k2 > 0) {
    pie(1220, 580, 230, [{ v: 0.4, c: '#F4B7A6', label: 'kira' }, { v: 0.3, c: DF.money, label: 'gıda' }, { v: 0.04, c: '#8DB8E8', label: '' }, { v: 0.26, c: '#E9E2CF', label: 'diğer' }], k2, 0, kh);
    dText("Mert'in sepeti", 1220, 880, 56, { c: DF.penSoft });
  }
  sticky(1530, 240, 280, 110, ['temsilî'], { size: 50, rot: 0.05 });
  kid(1700, GY, 0.85, { ...MERT, pose: 'point', k: kh, face: -1, mood: kh > 0.3 ? 'wow' : 'calm' });
}
// 9 — akrabalar: dezenflasyon, deflasyon, hiperenflasyon, çekirdek
function sKinds(t) {
  paper(); PT('Enflasyonun akrabaları', t);
  const C = [['Dezenflasyon', 't2', ['enflasyon yavaşlar', 'fiyatlar yine ↑']], ['Deflasyon', 't3', ['fiyatlar düşer', 'harcama ertelenir']],
             ['Hiperenflasyon', 't4', ['kontrolden çıkar', 'aylık %50+']], ['Çekirdek', 't5', ['oynaklar çıkınca', 'asıl eğilim']]];
  C.forEach(([nm, id, notes], i) => {
    const x = 110 + i * 440, y = 250, w = 400, h = 600, k = KS(id, 0.6);
    if (k <= 0) { dRect(x, y, w, h, 16, { w: 2.5, c: 'rgba(42,37,32,0.25)', seed: 410 + i }); dText('?', x + w / 2, y + h / 2 + 40, 140, { c: 'rgba(42,37,32,0.18)' }); return; }
    if (!card(x, y, w, h, k, 410 + i)) return;
    dText(nm, x + w / 2, y + 80, nm.length > 12 ? 54 : 62, { c: i === 2 ? DF.red : DF.pen });
    const gx = x + 50, gy = y + 400, gw = w - 100, gh = 240, p = KS(id, 1.6, 0.4);
    dLine(gx, gy, gx + gw, gy, { w: 3, seed: 420 + i }); dLine(gx, gy, gx, gy - gh, { w: 3, seed: 424 + i });
    if (i === 0) [0.9, 0.7, 0.5].forEach((v, j) => { const kk = clamp(p * 3 - j); if (kk > 0) dRect(gx + 30 + j * 95, gy - gh * v * kk, 60, gh * v * kk, 6, { fill: '#F4B7A6', w: 3, seed: 430 + j }); });
    if (i === 1) d([[gx + 10, gy - gh * 0.8], [gx + gw * 0.5, gy - gh * 0.55], [gx + gw - 10, gy - gh * 0.25]], { w: 6, c: DF.green, prog: p, seed: 440 });
    if (i === 2) { const P = []; for (let j = 0; j <= 20; j++) { const u = j / 20; P.push([gx + 10 + u * (gw - 20), gy - gh * (Math.exp(u * 3.2) - 1) / (Math.exp(3.2) - 1)]); } d(P, { w: 7, c: DF.red, prog: p, seed: 445 }); }
    if (i === 3) { basket(x + w / 2, gy, 0.7); ['enerji', 'gıda', 'altın'].forEach((s, j) => { const kk = clamp(p * 3 - j); if (kk > 0) { const yy = y + 150, xx = x + 80 + j * 120; dText(s, xx, yy, 36); dLine(xx - 40, yy - 12, xx + 40, yy - 12, { w: 4, c: DF.red, prog: kk, seed: 450 + j }); } }); }
    notes.forEach((s, j) => dText(s, x + w / 2, y + 470 + j * 56, 44, { c: j ? DF.penSoft : DF.pen }));
    endCard();
  });
}
// 10 — üç sebep: solda kartlar, sağda o anki sebebin sahnesi
function sCauses(t) {
  paper(); PT('Enflasyon neden olur?', t);
  const act = ON('c5') ? 2 : ON('c3') ? 1 : ON('c1') ? 0 : -1;
  ['1 · talep', '2 · maliyet', '3 · beklenti'].forEach((s, i) => {
    const k = KS('c0', 0.4, i * 0.35), y = 250 + i * 210;
    if (!card(80, y, 440, 170, k, 460 + i, i === act ? '#FFF6C8' : DF.cream)) return;
    if (i === act) hiText(s, 300, y + 108, 70, { hc: DF.hi, prog: clamp((TT - L(['c1', 'c3', 'c5'][i]).t0) / 0.5) }); else dText(s, 300, y + 108, 70, { c: act > i ? DF.penSoft : DF.pen });
    endCard();
  });
  if (act === 0) {
    const kK = KW('c2', 'kredi', 0.5);
    bank(800, 880, 0.8, { label: kK > 0.5 ? 'KREDİ' : 'BANKA' });
    const xs = [1150, 1380, 1610], t0 = wAt('c1', 'para');
    for (let i = 0; i < 18; i++) {
      const u = (TT - t0 - i * 0.12) / 1.2; if (u < 0 || u > 1.5) continue;
      const r = mulberry32(i * 7 + 3), tx = xs[i % 3] + (r() - 0.5) * 50;
      bill(lerp(800 + (r() - 0.5) * 120, tx, Math.min(u, 1)), lerp(640, 760, Math.min(u, 1)) - Math.sin(Math.min(u, 1) * Math.PI) * 120, 0.5, Math.sin(u * 6 + i) * 0.5, { seed: i });
    }
    xs.forEach((x, i) => { const k = ease((TT - t0 + 0.4 - i * 0.2) / 0.5); kid(x, GY, 0.75, { pose: 'cheer', k, face: i ? -1 : 1, hoodie: [DF.green, '#F29BB8', '#8DB8E8'][i], glasses: i === 2, mood: k > 0.3 ? 'happy' : 'calm', seed: 20 + i }); });
    sticky(1080, 250, 300, 130, ['mal aynı'], { size: 60, c: '#D9F2E4', rot: -0.04 });
    const up = TT > wAt('c1', 'yükseltir.');
    priceTag(1640, 330, 1.0, up ? '15 ₺' : '10 ₺', { swing: 0.05, c: up ? DF.red : DF.pen });
  } else if (act === 1) {
    const kP = KS('c3', 0.5);
    fade(kP, () => { priceTag(1200, 300, 1.35, 'fiyat', { swing: 0.04 }); });
    [['elektrik,', 'elektrik', 720], ['akaryakıt', 'akaryakıt', 1080], ['döviz', 'döviz', 1440]].forEach(([w, s, x], i) => {
      const k = KW('c3', w, 0.5);
      fade(k, () => { sticky(x - 140, 660, 280, 120, [s + ' ↑'], { size: 56, c: ['#FFF08A', '#FFD6E4', '#D9F2E4'][i], rot: (i - 1) * 0.04 }); });
      if (k > 0) arrow(x, 650, lerp(x, 1200, 0.55), 470, { prog: KW('c3', 'yansıtır.', 0.6), c: DF.red, w: 5, seed: 470 + i * 2 });
    });
    const kU = KW('c4', 'kurdaki', 0.5);
    fade(kU, () => { hiText('ithal girdi → kur ↑ → fiyat ↑', 1180, 880, 60, { c: DF.red, prog: kU, hc: DF.hiP }); });
  } else if (act === 2) {
    const xs = [780, 1200, 1620];
    xs.forEach((x, i) => {
      const k = KW('c5', 'zam', 0.4);
      kid(x, GY, 0.78, { pose: i === 1 ? 'point' : 'idle', k: 1, face: i === 2 ? -1 : 1, hoodie: ['#C7B4F0', DF.yellow, '#8DB8E8'][i], glasses: i === 1, mood: 'wow', seed: 40 + i });
      fade(clamp(k * 1.5 - i * 0.3), () => bubble(x + 40, 470, 300, 100, 'zam gelecek!', { seed: 480 + i * 3 }));
    });
    const kL = KW('c5', 'gerçekleştirir.', 1.2);
    if (kL > 0) { const P = []; for (let j = 0; j <= 40; j++) { const a = -Math.PI * 0.9 + j / 40 * Math.PI * 1.8; P.push([1200 + Math.cos(a) * 520, 330 + Math.sin(a) * 60]); } d(P, { w: 5, c: DF.red, prog: kL, seed: 490 }); hiText('kendini gerçekleştirir', 1200, 300, 54, { c: DF.red, prog: kL, hc: DF.hiP }); }
  } else {
    kid(1200, GY, 1.0, { ...MERT, pose: 'think', k: 1, face: -1, mood: 'calm' });
  }
}
// 11 — Merkez Bankası: faiz zinciri
function sTcmb(t) {
  paper(); PT('Merkez Bankası ne yapar?', t);
  bank(420, 880, 1.1, { label: 'TCMB' });
  fade(KW('p1', 'hedefi', 0.5), () => sticky(130, 240, 330, 150, ['uzun vadeli', 'hedef: %5'], { size: 56, c: '#D9F2E4', rot: -0.05 }));
  const B = [['faiz ↑', 'p2', 'faizi.'], ['kredi pahalı · mevduat cazip', 'p2', 'kredi'], ['borç ↓ · birikim ↑ · harcama ↓', 'p3', 'insanlar'], ['fiyat artışı soğur', 'p3', 'soğur.']];
  B.forEach(([s, id, w], i) => {
    const k = KW(id, w, 0.5), y = 250 + i * 160;
    if (!card(860, y, 900, 110, k, 500 + i, i === 3 ? '#D9F2E4' : DF.cream)) return;
    dText(s, 1310, y + 74, 58, { c: i === 3 ? DF.green : DF.pen }); endCard();
    if (i > 0 && k > 0.5) arrow(1310, y - 48, 1310, y - 4, { w: 4, head: 16, seed: 505 + i, prog: k });
  });
  fade(KS('p4', 0.5), () => { clockAt(700, 330, 80, 4, 40); dText('etkisi aylar sürer', 700, 470, 48, { c: DF.red }); });
}
// 12 — kimi vurur: maaş sütunu erir, yastık altı
function sSalary(t) {
  paper(); PT('Enflasyon kimi vurur?', t);
  const kS = KW('w0', 'sabit', 0.5), kN = KW('w0', 'nakit', 0.5);
  hiText('sabit gelirli', 330, 320, 64, { prog: kS, hc: DF.hiP });
  hiText('nakit tutan', 330, 420, 64, { prog: kN, hc: DF.hiP });
  const k1 = KS('w1', 0.8), k2 = KW('w2', 'yaklaşık', 0.8);
  if (k1 > 0) {
    const n1 = Math.round(14 * k1); for (let i = 0; i < n1; i++) bill(820, 850 - i * 22, 1.5, 0, { seed: 520 + i });
    if (k1 > 0.9) { dText('30.000 ₺', 820, 500, 64); dText('maaş', 820, 920, 48, { c: DF.penSoft }); }
    fade(KW('w1', '%30', 0.5), () => sticky(1360, 240, 420, 160, ['fiyatlar', 'yılda %30 ↑'], { size: 56, c: '#FFD6E4', rot: 0.04 }));
    dText('örnek', 1700, 440, 44, { c: DF.penSoft, al: KW('w1', '%30', 0.5) });
  }
  if (k2 > 0) {
    arrow(920, 600, 1060, 640, { prog: k2, c: DF.red, seed: 540 });
    const n2 = Math.round(14 / 1.3); for (let i = 0; i < Math.round(n2 * k2); i++) bill(1170, 850 - i * 22, 1.5, 0, { seed: 560 + i });
    if (k2 > 0.9) { hiText('≈23.000 ₺', 1170, 570, 64, { c: DF.red, hc: DF.hiP }); dText('alım gücü', 1170, 920, 48, { c: DF.penSoft }); }
  }
  const kY = KS('w3', 0.6);
  fade(kY, () => {
    pillow(1600, 860, 1.0);
    for (let i = 0; i < 4; i++) { const melt = clamp((TT - L('w3').t0 - 0.6 - i * 0.3) / 1.2); ctx.save(); ctx.globalAlpha *= 1 - melt * 0.8; bill(1520 + i * 55, 760 - i * 8 + melt * 30, 1.0 * (1 - melt * 0.4), 0.1 * i, { seed: 580 + i }); ctx.restore(); }
    dText('yastık altı', 1600, 920, 48, { c: DF.penSoft });
  });
  kid(330, GY, 0.95, { ...MERT, pose: k2 > 0.3 ? 'sad' : 'idle', k: k2, face: 1, mood: k2 > 0.3 ? 'sad' : 'calm' });
}
// 13 — borçlu neden kazanabilir + kıyas
function sDebt(t) {
  paper(); PT('Borçlu neden kazanabilir?', t);
  const k1 = KS('w4', 0.6), k2 = KW('w4', 'değeri', 0.8), k3 = KW('w4', 'hafifler.', 0.5);
  if (k1 > 0) {
    dText('bugün', 400, 350, 56, { align: 'right', c: DF.penSoft });
    dRect(440, 300, 1000 * k1, 80, 8, { fill: '#F4B7A6', w: 3.4, seed: 600 });
    if (k1 > 0.9) dText('borç: aynı tutar', 940, 356, 52);
  }
  if (k2 > 0) {
    dText('1 yıl sonra', 400, 490, 56, { align: 'right', c: DF.penSoft });
    dRect(440, 440, 1000, 80, 8, { w: 3, c: 'rgba(42,37,32,0.45)', seed: 601 });
    dRect(440, 440, 1000 * lerp(1, 1 / 1.3, k2), 80, 8, { fill: '#F4B7A6', w: 3.4, seed: 602 });
    if (k3 > 0) hiText('gerçek yükü hafifler', 1480, 500, 54, { c: DF.green, prog: k3, hc: DF.hiG, align: 'left' });
  }
  ['maaş zammı', 'kira artışı', 'faiz oranı'].forEach((s, i) => {
    const k = KW('w5', s.split(' ')[0], 0.5);
    fade(k, () => sticky(220 + i * 470, 620, 400, 190, [s, 'vs enflasyon'], { size: 58, c: ['#FFF08A', '#FFD6E4', '#D9F2E4'][i], rot: (i - 1) * 0.04 }));
  });
  kid(1730, GY, 0.85, { ...MERT, pose: 'cheer', k: k3 * (1 - KS('w5', 0.5)), face: -1, mood: 'happy' });
}
// 14 — bileşik etki: 12 ay sütun + düz çizgi
function sCompound(t) {
  paper(); PT('Bileşik etki', t);
  fade(KS('b1', 0.5, 0.6), () => sticky(1520, 230, 280, 120, ['sinsi!'], { size: 62, c: '#FFD6E4', rot: 0.06 }));
  const base = 830, X0 = 200, dx = 100, sc = 1000;
  const kb = ON('b2') ? clamp((TT - wAt('b2', '12')) / 2.4) : 0;
  dLine(X0 - 30, base, X0 + 12 * dx + 10, base, { w: 4, seed: 610 });
  for (let m = 1; m <= 12; m++) {
    const k = clamp(kb * 12 - (m - 1)); if (k <= 0) continue;
    const v = Math.pow(1.03, m) - 1, x = X0 + (m - 1) * dx;
    dRect(x, base - v * sc * k, 64, v * sc * k, 6, { fill: '#F4B7A6', w: 3, seed: 620 + m });
    dText(String(m), x + 32, base + 50, 40, { c: DF.penSoft });
  }
  const kl = KW('b2', '%36', 0.8);
  if (kl > 0) {
    dLine(X0, base - 0.03 * sc, X0 + 11 * dx + 64, base - 0.36 * sc, { w: 4, c: DF.penSoft, prog: kl, seed: 640 });
    dText('%36', X0 + 11 * dx + 150, base - 0.36 * sc + 20, 54, { c: DF.penSoft });
    xMark(X0 + 11 * dx + 150, base - 0.36 * sc, 40, KW('b2', 'değil,', 0.5));
  }
  const kr = KW('b2', '%42,6', 0.5);
  if (kr > 0) hiText('≈%42,6', X0 + 11 * dx + 30, base - 0.426 * sc - 40, 70, { c: DF.red, prog: kr, hc: DF.hiP });
  fade(KS('b3', 0.6), () => { dText('1,03 × 1,03 × … (12 kez) ≈ 1,426', 780, 300, 58); dText('her zam, zamlı fiyatın üstüne', 780, 370, 48, { c: DF.penSoft }); });
  kid(1720, GY, 0.85, { ...MERT, pose: 'think', k: 1, face: -1, mood: kr > 0.3 ? 'wow' : 'calm' });
}
// 15 — iki katına çıkma süresi
function sDouble(t) {
  paper(); PT('Fiyatlar kaç yılda ikiye katlanır?', t);
  sticky(1420, 230, 380, 140, ['yıllık %30', '(örnek)'], { size: 54, rot: -0.04 });
  const y = 680, x0 = 300, sx = 450, kT = KS('b4', 1.2, 0.3);
  arrow(x0 - 40, y, lerp(x0, x0 + 3 * sx + 80, kT), y, { prog: 1, w: 5, seed: 650 });
  for (let i = 0; i <= 3; i++) if (kT * 3 >= i) { dLine(x0 + i * sx, y - 14, x0 + i * sx, y + 14, { w: 4, seed: 651 + i }); dText(`${i}. yıl`, x0 + i * sx, y + 70, 46, { c: DF.penSoft }); }
  simit(x0, 520, 1.1, 660); priceTag(x0, 300, 0.75, '10 ₺', { swing: 0.04 });
  const tD = Math.log(2) / Math.log(1.3), u = clamp((TT - wAt('b4', 'ikiye')) / 2.0) * tD, xd = x0 + u * sx;
  if (u > 0) {
    dEll(xd, y, 14, 14, { fill: DF.red, w: 3, seed: 665 });
    dText(`${Math.round(10 * Math.pow(1.3, u))} ₺`, xd, y - 40, 52, { c: DF.red });
  }
  const kD = KW('b4', '20', 0.6);
  if (kD > 0) { simit(x0 + tD * sx, 520, 1.1, 670); priceTag(x0 + tD * sx, 300, 0.75, '20 ₺', { swing: 0.04, c: DF.red }); hiText('≈2 yıl 8 ay', x0 + tD * sx, 820, 60, { prog: kD, hc: DF.hiP }); }
}
// 16 — reel getiri: iki kavanoz + doğru formül
function sReal(t) {
  paper(); PT('Reel getiri', t);
  const kJ = KS('r1', 0.6), k1 = KW('r2', 'mevduat', 0.8), k2 = KW('r2', 'enflasyon', 0.8);
  fade(kJ, () => { jar(350, 870, 0.4 * k1 / 0.45, 'faiz %40', DF.money, 680); jar(720, 870, 0.3 * k2 / 0.45, 'enflasyon %30', '#F4B7A6', 690); });
  const kX = KW('r2', 'değil.', 0.5);
  if (kX > 0) { dText('%10', 1350, 330, 90, { c: DF.penSoft }); xMark(1350, 300, 60, kX); }
  const kF = KW('r3', 'doğru', 0.6), kR = KW('r3', '%7,7.', 0.5);
  fade(kF, () => dText('1,40 ÷ 1,30 − 1', 1350, 480, 90));
  if (kR > 0) hiText('≈ %7,7 reel', 1350, 600, 90, { c: DF.green, prog: kR, hc: DF.hiG });
  fade(KS('r4', 0.5), () => sticky(1080, 670, 560, 140, ['stopajdan sonra', 'net getiriyi hesapla'], { size: 50, c: '#FFF08A', rot: 0.03 }));
  fade(KS('r5', 0.5), () => hiText('enflasyon > getiri → alım gücü ↓', 960, 905, 60, { c: DF.red, hc: DF.hiP, prog: KS('r5', 0.8) }));
}
// 17 — 4 ilke
function sRules(t) {
  paper(); PT('Enflasyondan korunmanın 4 ilkesi', t);
  fade(KW('k0', 'tavsiyesi', 0.5), () => sticky(1440, 230, 380, 130, ['yatırım tavsiyesi', 'değildir'], { size: 46, c: '#FFD6E4', rot: 0.05 }));
  const R = [['k1', 'Kendi enflasyonunu bil'], ['k2', 'Parayı nakit bekletme'], ['k3', 'Gelirini enflasyona bağla'], ['k4', 'Tek varlığa yüklenme, panik yapma']];
  R.forEach(([id, s], i) => {
    const y = 380 + i * 135, k = KS(id, 0.5);
    dRect(160, y - 52, 58, 58, 8, { w: 3.4, seed: 700 + i });
    dText(`${i + 1}. ${s}`, 260, y, 72, { align: 'left', al: Math.max(0.2, k) });
    check(189, y - 24, k, 1.1);
  });
  kid(1640, GY, 1.05, { ...MERT, pose: 'point', k: KS('k1', 0.6), face: -1, mood: 'happy' });
}
// 18 — özet kartları
function sSummary(t) {
  paper(); PT('Özet', t);
  const S = [['genel + sürekli', 's1', 'genel'], ['TÜİK sepeti', 's1', 'sepetle'], ['talep · maliyet · beklenti', 's1', 'talep,'],
             ['sabit gelir erir', 's2', 'eritir,'], ['bileşik büyür', 's2', 'bileşik'], ['reel hesapla', 's2', 'reel']];
  S.forEach(([s, id, w], i) => {
    const k = KW(id, w, 0.5), x = 150 + (i % 3) * 560, y = 270 + Math.floor(i / 3) * 290;
    fade(k, () => sticky(x, y, 500, 140, [s], { size: s.length > 18 ? 48 : 60, c: ['#FFF08A', '#FFD6E4', '#D9F2E4'][i % 3], rot: ((i * 7) % 5 - 2) * 0.015 }));
  });
}
// 19 — kapanış: araç linki + sonraki sayfa + ABONE OL
function sCta(t) {
  paper(); const a = clamp(t / 0.5);
  hiText('parafomo.com', 960, 290, 120, { prog: clamp((t - 0.3) / 0.6), hc: DF.hiG });
  dText('/enflasyon-hesaplama', 960, 390, 70, { c: DF.penSoft, al: a });
  const k4 = KS('s4', 0.6);
  if (k4 > 0) {
    dText('sonraki sayfa:', 760, 560, 70, { c: DF.penSoft, al: k4 }); hiText('FAİZ', 1060, 560, 110, { c: DF.red, prog: k4, hc: DF.hiP });
    const b = clamp(spring(Math.max(0, TT - L('s4').t0 - 0.3), 0.9, { k: 200, damp: 0.45 }));
    if (b > 0.01) { ctx.save(); ctx.translate(960, 760); ctx.scale(b, b);
      ctx.fillStyle = BR.red; ctx.beginPath(); ctx.roundRect(-210, -58, 420, 116, 20); ctx.fill();
      ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.moveTo(-150, -24); ctx.lineTo(-150, 24); ctx.lineTo(-110, 0); ctx.closePath(); ctx.fill();
      ctx.font = `56px ${ANTON}`; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText('ABONE OL', -86, 4); ctx.restore(); }
  }
  kid(1600, GY, 1.0, { ...MERT, pose: 'cheer', k: clamp((t - 0.2) / 0.5), face: -1, mood: 'happy' });
  kid(330, GY, 0.9, { pose: 'cheer', k: k4, face: 1, hoodie: DF.green, glasses: false, mood: 'happy', seed: 30 });
}
// kapak (1280x720'e küçülür): solda simit + 10→15, sağda iki kelime
function drawThumb() {
  paper({ tint: '#F6F1DA' });
  simit(560, 700, 3.4, 5);
  priceTag(560, 300, 1.7, '', { swing: 0 });
  ctx.save(); ctx.translate(560, 300);
  dText('10 ₺', 10, 120, 100, { c: DF.penSoft }); dLine(-80, 90, 110, 60, { w: 9, c: DF.red, seed: 55 });
  dText('15 ₺', 120, 20, 120, { c: DF.red, rot: -0.12 }); ctx.restore();
  hiText('PARAN', 1420, 430, 230, { c: DF.pen, hc: DF.hi });
  hiText('ERİYOR!', 1420, 680, 230, { c: DF.red, hc: DF.hiP });
  kid(1050, 1060, 1.15, { ...MERT, pose: 'sad', k: 1, face: 1, mood: 'wow', t: 0.3 });
  ctx.fillStyle = DF.cover; ctx.fillRect(0, 0, 640, 110);
  dText('EKONOMİ DEFTERİ', 320, 78, 64, { c: DF.cream });
  overlayGrain('multiply', 0.5);
}
const SDRAW = [sHook, sPlan, sDef, sStairs, sCart, sBasket, sWeights, sYoy, sPersonal, sKinds, sCauses, sTcmb, sSalary, sDebt, sCompound, sDouble, sReal, sRules, sSummary, sCta];
const curI = () => { let i = 0; for (let k = 0; k < SCN.length; k++) if (TT >= sAt(k)) i = k; return i; };
function drawPiece() {
  if (THUMB) { drawThumb(); return; }
  const i = curI(), fx = i > 0 ? clamp((TT - sAt(i)) / 0.45) : 1;
  if (fx < 1) { SDRAW[i - 1](lt(i - 1)); ctx.save(); ctx.globalAlpha = fx; ctx.translate(0, (1 - EZ.o3(fx)) * 100); }   // yeni sayfa alttan kayar
  SDRAW[i](lt(i));
  if (fx < 1) ctx.restore();
  overlayGrain('multiply', 0.55);
}
function drawOverlay() { if (THUMB) return; const i = curI(); if (i > 0) captions(1010); }
