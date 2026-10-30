// =====================================================================
//  NET MAAŞIN ANATOMİSİ — izometrik "patlatılmış görünüm" + 12 aylık izometrik sütun grafiği.
//  Bölüm 1: 75.000 ₺'lik brüt blok düşer, katmanlarına ayrılır; her kesinti anlatıldığı an öne kayar, numaralı
//  etiketi gelir (01-05). Bölüm 2: aynı brüt 12 ay; sütun boyu sabit (brüt), kırmızı kesinti payı Nisan ve
//  Temmuz'da büyür. Sayılar TL.data'dan (sitenin hesaplayıcısı), elle yazılmaz.
// =====================================================================
const D = TL.data;
const KZ = 320 / D.brut;                 // dünya birimi / ₺ (blok boyu)
const MINH = 9;
const LAY = D.layers;                    // üstten alta: sgk, iss, gv, dmg, net
const STACK = LAY.slice().reverse();     // alttan üste çizim sırası
const FW = 250;                          // ayak izi (kare)
const GAP = 40;
const ISO1 = { ox: 400, oy: 1080, u: 1 };

function layerH(l) { return Math.max(MINH, l.v * KZ); }

function sceneStack(alpha) {
  ctx.save(); ctx.globalAlpha = alpha;
  setIso(ISO1);
  const drop = (1 - spring(TT, 0.15, { k: 120, damp: 0.6 })) * 500;
  const open = spring(TT, cue('split') + 0.35, { k: 70, damp: 0.7 });
  const cur = curLine();
  // zemin plakası
  isoPlates(-30, -30, -18, FW + 60, FW + 60, [{ h: 10, r: 30 }], {});
  let z = drop, slots = [];
  STACK.forEach((l, i) => {
    const h = layerH(l), shown = TT >= cue(l.key), act = cur && cur.id === l.key;
    const pull = l.key === 'net' ? 0 : spring(TT, cue(l.key), { k: 110, damp: 0.6 }) * 46 - (TT > L(l.key).t1 + 0.3 ? spring(TT, L(l.key).t1 + 0.3, { k: 90, damp: 0.8 }) * 46 : 0);
    const col = shown ? l.col : PAL.edge, fill = shown ? l.fill : PAL.face;
    isoBox(0, pull, z, FW, FW, h, { r: 18, edge: act ? l.col : col, fill, creaseC: shown ? l.col : PAL.inner });
    if (act || (l.key === 'net' && TT >= cue('net'))) {   // aktif katman: üst yüzde ince parlak çerçeve
      const top = faceOf([0, pull, z + h], [1, 0, 0], [0, 1, 0]);
      faceRR(top, 14, 14, FW - 28, FW - 28, 10, { stroke: l.col });
    }
    slots.push({ l, z, h, pull });
    z += h + GAP * open;
  });
  // brüt etiketi (açılmadan önce)
  const ba = clamp(spring(TT, 0.5, { k: 120, damp: 0.8 })) * (1 - clamp((TT - cue('split') - 0.2) / 0.4));
  if (ba > 0.01) {
    const p = iso(FW, 0, drop + 320 * 0.5);
    polyPath([[p[0] + 12, p[1]], [p[0] + 60, p[1]]], false); hair(BR.gold); ctx.stroke();
    txt('BRÜT MAAŞ', p[0] + 76, p[1] - 30, `500 28px ${DMONO}`, BR.muted, { al: ba });
    txt(tl(D.brut), p[0] + 72, p[1] + 52, `92px ${ANTON}`, BR.gold, { al: ba });
  }
  // numaralı etiketler (patlatılmış görünüm): katman ortasından sağa kılavuz çizgisi, en az 96 px aralık
  const labs = slots.slice().reverse().map((s, i) => ({ ...s, n: i + 1, y: iso(FW, s.pull, s.z + s.h / 2)[1] }));
  for (let i = 1; i < labs.length; i++) if (labs[i].y < labs[i - 1].y + 100) labs[i].y = labs[i - 1].y + 100;
  const LX0 = 708;
  for (const s of labs) {
    const a = clamp(spring(TT, cue(s.l.key) + 0.1, { k: 150, damp: 0.75 }));
    if (a <= 0.01) continue;
    const act = cur && cur.id === s.l.key, p = iso(FW, s.pull, s.z + s.h / 2);
    ctx.save(); ctx.globalAlpha = alpha * a * (act || s.l.key === 'net' ? 1 : 0.62);
    polyPath([[p[0] + 8, p[1]], [LX0 - 30, s.y], [LX0 - 12, s.y]], false); hair(s.l.col); ctx.stroke();
    ctx.beginPath(); ctx.arc(p[0] + 6, p[1], 5, 0, TAU); ctx.fillStyle = s.l.col; ctx.fill();
    txt(String(s.n).padStart(2, '0') + ' ' + s.l.name, LX0, s.y - 16, `500 25px ${DMONO}`, s.l.col);
    txt(tl(s.l.v), LX0, s.y + 44 + (1 - a) * 14, `${s.l.key === 'net' ? 62 : 54}px ${ANTON}`, s.l.key === 'net' ? BR.light : BR.gold);
    ctx.restore();
  }
  ctx.restore();
}

// ---- bölüm 2: 12 ay, aynı brüt
const ISO2 = { ox: 190, oy: 1010, u: 1 };
const CP = 54, CW = 40, CH = 320;        // aralık, sütun eni, brüt sütun boyu (dünya)
function netAt(i) {
  const v = D.net_by_month, s2 = spring(TT, cue('apr') + 2.6, { k: 80, damp: 0.7 }), s3 = spring(TT, cue('aug') + 0.3, { k: 80, damp: 0.7 });
  const stage2 = i < 6 ? v[i] : v[5];
  return lerp(lerp(v[0], stage2, s2), v[i], s3);
}
function colTop(i) { return iso(i * CP + CW / 2, 0, CH + 30); }
function sceneChart(alpha) {
  ctx.save(); ctx.globalAlpha = alpha;
  setIso(ISO2);
  isoPlates(-26, -30, -16, 12 * CP + 36, CW + 60, [{ h: 10, r: 24 }]);
  const floor = faceOf([0, CW + 6, -6], [1, 0, 0], [0, 1, 0]);
  for (let i = 0; i < 12; i++) {
    const rise = spring(TT, cue('turn') + 0.15 + i * 0.05, { k: 140, damp: 0.6 });
    if (rise <= 0.005) continue;
    const net = netAt(i), hn = net / D.brut * CH * rise, hk = (D.brut - net) / D.brut * CH * rise;
    isoBox(i * CP, 0, 0, CW, CW, hn, { r: 6, seg: 3, edge: BR.brand, fill: '#12302A', creaseC: BR.brand });
    isoBox(i * CP, 0, hn, CW, CW, hk, { r: 6, seg: 3, edge: '#FF7A30', fill: '#5A2A12', creaseC: '#FF7A30' });
    isoText(faceOf([i * CP + 2, CW + 22, -6], [1, 0, 0], [0, 1, 0]), D.months[i], 0, 0, 17, { color: PAL.textD, font: DMONO });
  }
  // açıklama
  const la = clamp(spring(TT, cue('turn') + 0.8, { k: 120, damp: 0.8 })) * (1 - clamp((TT - cue('diff')) / 0.3));
  if (la > 0.01) {
    ctx.save(); ctx.globalAlpha = alpha * la;
    ctx.fillStyle = BR.brand; ctx.fillRect(80, 1250, 26, 26); txt('NET (ELE GEÇEN)', 120, 1272, `500 24px ${DMONO}`, '#D5DDDA');
    ctx.fillStyle = '#FF7A30'; ctx.fillRect(80, 1294, 26, 26); txt('SGK + VERGİLER', 120, 1316, `500 24px ${DMONO}`, '#D5DDDA');
    ctx.restore();
  }
  // değer çağrıları: Ocak, Nisan, Ağustos (+ dilim etiketleri)
  const call = (i, t0, lab, col) => {
    const a = clamp(spring(TT, t0, { k: 150, damp: 0.7 })); if (a <= 0.01) return;
    const p = colTop(i);
    ctx.save(); ctx.globalAlpha = alpha * a;
    polyPath([[p[0], p[1] - 4], [p[0], p[1] - 60]], false); hair(col); ctx.stroke();
    txt(lab, p[0] - 4, p[1] - 76, `500 22px ${DMONO}`, BR.muted);
    txt(tl(D.net_by_month[i]), p[0] - 6, p[1] - 106 + (1 - a) * 12, `50px ${ANTON}`, col);
    ctx.restore();
  };
  call(0, cue('turn') + 0.9, 'OCAK · %15', BR.light);
  call(3, cue('apr') + 2.7, 'NİSAN · %20', BR.gold);
  call(7, cue('aug') + 1.9, 'AĞUSTOS · %27', '#FF7A30');
  ctx.restore();
}

function diffBadge() {
  const a = clamp(spring(TT, cue('diff') + 0.1, { k: 180, damp: 0.5 }));
  if (a <= 0.01 || TT > cue('cta') + 0.4) return;
  ctx.save(); ctx.translate(470, 1340); ctx.scale(0.6 + 0.4 * a, 0.6 + 0.4 * a); ctx.globalAlpha = clamp(a);
  ctx.fillStyle = BR.red; ctx.beginPath(); ctx.roundRect(-330, -70, 660, 130, 16); ctx.fill();
  txt('AYDA −' + tl(D.net_by_month[0] - D.net_by_month[11]), 0, 26, `76px ${ANTON}`, BR.white, { align: 'center' });
  ctx.restore();
}

function drawPiece() {
  fillAll(BR.bg);
  const tSwitch = cue('turn');
  const fadeOut = 1 - clamp((TT - tSwitch + 0.1) / 0.45);
  const z = 1 + 0.03 * clamp(TT / Math.max(1, tSwitch));   // yavaş itme
  if (fadeOut > 0.01) {
    ctx.save(); ctx.translate(470, 900); ctx.scale(z, z); ctx.translate(-470, -900);
    sceneStack(fadeOut); ctx.restore();
    brandHeader('MAAŞININ ANATOMİSİ', 0.05, { sub: 'Brüt 75.000 ₺ · Ocak 2026' });
  }
  if (TT >= tSwitch - 0.1) {
    const fin = clamp((TT - tSwitch + 0.1) / 0.45);
    sceneChart(fin);
    if (fin > 0.01) brandHeader('AYNI MAAŞ, FARKLI NET', tSwitch, { sub: 'Brüt 75.000 ₺ · 12 ay' });
    diffBadge();
  }
  ctaCard(cue('cta'));
  if (TT < cue('cta')) captions();
}
