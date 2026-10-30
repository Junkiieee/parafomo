// =====================================================================
//  EKONOMİ MAKİNESİ: ENFLASYON NASIL OLUR? — el çizimi anlatım (kits/dalio.js).
//  Sahneler satır başlangıçlarına bağlı (cue). Tutarlar ÖRNEK (10 → 15 ₺), ekranda "ÖRNEK" yazar; istatistik iddiası yok.
// =====================================================================
BR.capFont = `700 82px ${AMATIC}`; BR.capText = DL.ink; BR.capStroke = 'rgba(251,248,234,0.9)';
const SCN = ['hook', 'trade', 'money', 'same', 'price', 'chart', 'cta'];
const sAt = (i) => (i === 0 ? -1.2 : cue(SCN[i]) - 0.15);
const lt = (i) => TT - sAt(i);
const ease = (x) => EZ.io(clamp(x));
// seslendirmedeki kelimenin başladığı an (gerçek kelime zamanı; yoksa satır içinde orantılı)
function wAt(id, w) {
  const l = L(id), ws = (l.cap || '').toLocaleLowerCase('tr-TR').split(/\s+/), i = ws.findIndex((x) => x.includes(w));
  if (i < 0) return l.t0;
  return l.words && l.words[i] != null ? l.words[i] : l.t0 + (l.t1 - l.t0) * i / ws.length;
}

function header(str, al = 1, c = DL.ink) { hText(str, 540, 330, 104, { c, al }); hLine(380, 356, 700, 356, { w: 4, c, seed: 5 }); }

// 0 — başlık kartı (lacivert, süslü çerçeve, madalyonda fiyat etiketi)
function sHook(t) {
  paperBg(DL.navy); ornateFrame(DL.cream);
  hEll(540, 520, 92, 112, { c: DL.cream, w: 4, seed: 91 });
  ctx.save(); ctx.beginPath(); ctx.ellipse(540, 520, 88, 108, 0, 0, TAU); ctx.clip();
  bread(540, 560, 1.0, 3); priceTag(540, 450, 0.55, TT > wAt('hook', 'pahalan') + 0.3 ? '₺15' : '₺10', { swing: 0.06, fill: DL.cream });
  ctx.restore();
  hLine(330, 652, 450, 652, { c: DL.cream, w: 3, seed: 92 }); hLine(630, 652, 750, 652, { c: DL.cream, w: 3, seed: 93 });
  hText('EKONOMİ', 540, 850, 190, { c: DL.cream }); hText('MAKİNESİ', 540, 1020, 190, { c: DL.cream });
  hLine(330, 1080, 750, 1080, { c: DL.cream, w: 3, seed: 94 });
  hText('ENFLASYON NASIL OLUR?', 540, 1180, 92, { c: DL.mustard });
}
// 1 — alışveriş: Ali fırıncıya para verir ("10 lira verir"), ekmeği alır ("ekmeği alır")
function sTrade(t) {
  paperBg(DL.paper); header('HER ŞEY BİR ALIŞVERİŞ');
  const tA = wAt('trade', 'ali'), tM = wAt('trade', '10'), tB = wAt('trade', 'karşılığında');
  const walkK = ease((TT - sAt(1)) / Math.max(0.8, tA - sAt(1) + 0.4)), ax = lerp(-160, 300, walkK);
  const giveK = ease((TT - tM + 0.4) / 0.4), takeK = ease((TT - tB) / 0.4);
  // fırıncı tezgâhın ARKASINDA: önce fırıncı, sonra tezgâh
  const bk = clamp((TT - tB + 0.5) / 0.4) * (1 - clamp((TT - tB - 1.2) / 0.4));
  const baker = person(850, 1390, 1.15, { pose: 'give', k: ease(bk), face: -1, shirt: '#E6DDC4', hat: DL.cream, seed: 2 });
  const st = stall(790, 1390, 1.12);
  for (let i = 0; i < 3; i++) bread(700 + i * 90, st.shelfY - 30, 0.62, 10 + i);
  hText('ÖRNEK FİYAT: ₺10', 790, 1330, 58, { c: DL.inkSoft });
  const ali = person(ax, 1390, 1.4, { pose: walkK < 1 ? 'walk' : 'give', k: giveK * (1 - takeK * 0.6), face: 1, hat: true, shirt: DL.olive, seed: 1 });
  const mt = ease((TT - tM) / 0.8);   // para: Ali → fırıncı
  if (TT > tM - 0.4 && mt < 1) bill(lerp(ali.hand[0], baker.hand[0], mt), lerp(ali.hand[1], baker.hand[1], mt) - Math.sin(mt * Math.PI) * 150, 1.1, mt * 0.6);
  if (mt >= 1) bill(baker.handB[0] - 10, baker.handB[1] + 6, 0.7, 0.3);
  const bt = ease((TT - tB) / 0.8);    // ekmek: fırıncı → Ali
  if (TT > tB - 0.3) bread(lerp(baker.hand[0], ali.hand[0] + 30, bt), lerp(baker.hand[1], ali.hand[1], bt) - Math.sin(bt * Math.PI) * 120, 0.75, 7);
  if (TT > tM) hText('PARA →', 540, 640, 96, { c: DL.red, al: clamp((TT - tM) / 0.4) });
  if (TT > tB) hText('← MAL', 540, 740, 96, { c: DL.oliveD, al: clamp((TT - tB) / 0.4) });
}
// 2 — ceplere daha çok para: bankadan para yağar, insanlar sevinir
function sMoney(t) {
  paperBg(DL.tan); header('CEPLERDE DAHA ÇOK PARA');
  bank(540, 760, 1.1, { label: 'KREDİ · PARA' });
  const xs = [170, 405, 640, 880];
  for (let i = 0; i < 26; i++) {   // para yağmuru
    const t0 = wAt('money', 'cebine') - sAt(2) + i * 0.1, u = (t - t0) / 1.3; if (u < 0 || u > 1.6) continue;
    const r = mulberry32(i * 7 + 3), tx = xs[i % 4] + (r() - 0.5) * 60;
    const y = lerp(800, 1040, Math.min(u, 1)), x = lerp(540 + (r() - 0.5) * 200, tx, Math.min(u, 1));
    bill(x, y, 0.55, Math.sin(u * 6 + i) * 0.5, { seed: i });
  }
  xs.forEach((x, i) => {
    const k = ease((TT - wAt('money', 'para') + 0.6 - i * 0.25) / 0.5);
    person(x, 1420, 1.05, { pose: 'cheer', k, face: i % 2 ? -1 : 1, shirt: [DL.olive, '#C9B48A', '#8FA3A8', '#D7A79A'][i], hat: i === 2, seed: 20 + i });
  });
}
// 3 — ama ekmek aynı: tezgâhta 5 ekmek, kuyruk uzar
function sSame(t) {
  paperBg(DL.paper); header('AMA EKMEK AYNI');
  const st = stall(300, 1390, 1.0);
  for (let i = 0; i < 5; i++) bread(150 + i * 75, st.shelfY - 26, 0.55, 30 + i);
  hText('5 EKMEK', 300, 1335, 72, { c: DL.red });
  for (let i = 0; i < 5; i++) {
    const t0 = 0.1 + i * 0.3, k = ease((t - t0) / 1.2), x = lerp(1300 + i * 80, 590 + i * 125, k);
    person(x, 1400 + (i % 2) * 20, 0.95, { pose: k < 1 ? 'walk' : 'idle', face: -1, shirt: ['#C9B48A', DL.olive, '#8FA3A8', '#D7A79A', DL.olive][i], hat: i % 3 === 0, seed: 40 + i });
  }
}
// 4 — fiyat yükselir: etiket 10'dan 15'e
function sPrice(t) {
  paperBg(DL.paper); header('FİYAT YÜKSELİR');
  bread(540, 1120, 2.2, 51);
  priceTag(540, 640, 1.9, '', { swing: 0.04 });
  const cut = clamp((TT - wAt('price', 'yükselir')) / 0.5), nw = clamp((TT - wAt('price', '15')) / 0.5);
  ctx.save(); ctx.translate(540, 640); ctx.rotate(0.04 * Math.sin(TT * TAU * 0.9));
  hText('₺10', 20, 140, 120, { c: nw > 0.5 ? DL.inkSoft : DL.ink });
  if (cut > 0) hLine(-80, 100, -80 + 200 * cut, 70, { w: 9, c: DL.red, seed: 55 });
  if (nw > 0) hText('₺15', 120, 30, 130, { c: DL.red, al: nw, rot: -0.12 });
  ctx.restore();
  for (let i = 0; i < 3; i++) arrow(250 + i * 290, 1380, 250 + i * 290 + 40, 1260, { prog: ease((TT - wAt('price', 'yükselir') - 0.3 - i * 0.2) / 0.5), c: DL.red, w: 6, seed: 60 + i * 3 });
  hText('ÖRNEK', 900, 470, 50, { c: DL.inkSoft, rot: 0.1 });
}
// 5 — grafik: para hızlı, mal yavaş → aradaki fark enflasyon
function sChart(t) {
  paperBg(DL.paper); header('ENFLASYON = PARA > MAL');
  const p1 = ease((TT - wAt('chart', 'para,')) / 1.6), p2 = ease((TT - wAt('chart', 'maldan')) / 1.6);
  const para = [0.08, 0.16, 0.27, 0.4, 0.55, 0.72, 0.9], mal = [0.08, 0.13, 0.18, 0.23, 0.28, 0.33, 0.38];
  const X = 140, Y = 1300, Wc = 800, Hc = 760;
  const gap = clamp((TT - wAt('chart', 'fiyatlar')) / 0.6);
  if (gap > 0) {   // aradaki alan: taranmış
    ctx.save(); ctx.globalAlpha = gap * 0.5; ctx.beginPath();
    para.forEach((v, i) => { const x = X + i / 6 * Wc, y = Y - v * Hc; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    for (let i = 6; i >= 0; i--) ctx.lineTo(X + i / 6 * Wc, Y - mal[i] * Hc);
    ctx.closePath(); ctx.fillStyle = DL.mustard; ctx.fill(); ctx.restore();
    hText('ENFLASYON', X + Wc * 0.62, Y - 0.5 * Hc, 74, { c: DL.ink, al: gap, rot: -0.35 });
  }
  chart(X, Y, Wc, Hc, [{ v: para, c: DL.red, prog: p1, label: 'PARA', seed: 75 }, { v: mal, c: DL.oliveD, prog: p2, label: 'MAL', seed: 77 }]);
  hText('ZAMAN →', X + Wc - 60, Y + 70, 54, { c: DL.inkSoft });
}
// 6 — kapanış (lacivert kart + marka ABONE OL)
function sCta(t) {
  paperBg(DL.navy); ornateFrame(DL.cream);
  const a = clamp(t / 0.5);
  hText('PARANI', 540, 640, 150, { c: DL.cream, al: a }); hText('ENFLASYONA KARŞI', 540, 780, 110, { c: DL.cream, al: a });
  hText('KORU', 540, 920, 150, { c: DL.mustard, al: a });
  hLine(330, 980, 750, 980, { c: DL.cream, w: 3, seed: 95 });
  hText('parafomo.com', 540, 1090, 96, { c: DL.cream, al: clamp((t - 0.4) / 0.5) });
  const b = clamp(spring(Math.max(0, t), 0.9, { k: 200, damp: 0.45 }));
  if (b > 0.01) { ctx.save(); ctx.translate(540, 1240); ctx.scale(b, b);
    ctx.fillStyle = BR.red; ctx.beginPath(); ctx.roundRect(-210, -58, 420, 116, 20); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.moveTo(-150, -24); ctx.lineTo(-150, 24); ctx.lineTo(-110, 0); ctx.closePath(); ctx.fill();
    ctx.font = `56px ${ANTON}`; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText('ABONE OL', -86, 4); ctx.restore(); }
}
const SDRAW = [sHook, sTrade, sMoney, sSame, sPrice, sChart, sCta];
const curI = () => { let i = 0; for (let k = 0; k < SCN.length; k++) if (TT >= sAt(k)) i = k; return i; };
function drawPiece() {
  const i = curI(), fx = i > 0 ? clamp((TT - sAt(i)) / 0.35) : 1;
  if (fx < 1) { SDRAW[i - 1](lt(i - 1)); ctx.save(); ctx.globalAlpha = fx; }
  // yeni sahne: kâğıt yaprağı gibi alttan kayarak gelir
  ctx.save(); if (fx < 1) ctx.translate(0, (1 - EZ.o3(fx)) * 160);
  SDRAW[i](lt(i)); ctx.restore();
  if (fx < 1) ctx.restore();
  overlayGrain('multiply', 1.0);
}
function drawOverlay() { const i = curI(); if (i > 0 && i < 6) captions(1488); }
