// =====================================================================
//  scenes.js — veriyle çalışan izometrik sahne kütüphanesi (günlük Shorts/Reels hattı).
//  Her sahne: SC[type](d, t, al) — d = veri, t = sahnenin yerel zamanı (sn), al = geçiş saydamlığı.
//  İkonlar: isoIcon(name, s, t) — altın, para, ev, araba, banka, takvim, grafik, yüzde, kart, kumbara.
//  Kural: rakamlar yalnız veri alanından gelir (dönüştürücü sayı kapısından geçirir), sahne rakam uydurmaz.
// =====================================================================
const PALC = ['#3D8BD9', '#9B86F0', '#FF7A30', '#B8BEC0', '#E3C14D', '#E05A8A'];
const TINT = { '#3D8BD9': '#12223A', '#9B86F0': '#1E1A33', '#FF7A30': '#3A1E10', '#B8BEC0': '#22282B', '#E3C14D': '#3A3010',
  '#E05A8A': '#3A1424', '#2BB194': '#12302A', '#FFC94D': '#3A2E10', '#63D491': '#14321F' };
const tint = (c) => TINT[c] || PAL.face;

// ---- sayı biçimi: value sayı, unit '₺' | '%' | '$' | '€' | 'x' | '' (+ isteğe bağlı suffix: "bin", "milyon")
function fmtNum(v, dec) {
  const d = dec ?? (Math.abs(v - Math.round(v)) < 1e-9 ? 0 : (Math.abs(v * 10 - Math.round(v * 10)) < 1e-9 ? 1 : 2));
  return v.toLocaleString('tr-TR', { minimumFractionDigits: d, maximumFractionDigits: d });
}
function fmtVal(v, unit, o = {}) {
  const n = fmtNum(v, o.dec), sx = o.suffix ? ' ' + o.suffix : '';
  if (unit === '₺' || unit === '$' || unit === '€') return unit + n + sx;
  if (unit === '%') return '%' + n;
  if (unit === 'x') return n + 'x';
  return n + sx + (unit ? ' ' + unit : '');
}
const decOf = (v) => (Math.abs(v - Math.round(v)) < 1e-9 ? 0 : (Math.abs(v * 10 - Math.round(v * 10)) < 1e-9 ? 1 : 2));
// yazıyı genişliğe sığdır: font boyutunu küçültür
function fitFont(str, maxW, size, fam, weight = '') {
  ctx.save(); let s = size;
  for (; s > 18; s -= 2) { ctx.font = `${weight} ${s}px ${fam}`; if (ctx.measureText(str).width <= maxW) break; }
  ctx.restore(); return `${weight} ${s}px ${fam}`;
}
// *vurgulu* kelimeleri altın yazan, satır kıran metin bloğu (ortalı)
function richBlock(str, cx, y, maxW, size, lh, al = 1) {
  const words = str.split(/\s+/).filter(Boolean);
  ctx.save(); ctx.font = `${size}px ${ANTON}`;
  const sp = size * 0.28, lines = [[]];
  let w = 0;
  for (const raw of words) {
    const hot = /^\*.*\*[.,!?:;]*$/.test(raw), word = raw.replace(/\*/g, '').toLocaleUpperCase('tr-TR');
    const ww = ctx.measureText(word).width;
    if (w > 0 && w + sp + ww > maxW) { lines.push([]); w = 0; }
    lines[lines.length - 1].push({ word, hot, ww }); w += (w > 0 ? sp : 0) + ww;
  }
  lines.forEach((ln, i) => {
    const tw = ln.reduce((a, b) => a + b.ww, 0) + sp * (ln.length - 1);
    let x = cx - tw / 2;
    for (const it of ln) { txt(it.word, x, y + i * lh, `${size}px ${ANTON}`, it.hot ? BR.gold : BR.white, { al }); x += it.ww + sp; }
  });
  ctx.restore();
  return lines.length;
}

// =====================================================================
//  İzometrik ikonlar (merkez: dünya orijini; s ölçek; t yerel zaman → yaylı giriş)
// =====================================================================
const GOLDC = '#FFC94D', GOLDF = '#3A2E10';
const drop = (t, t0, hgt = 260) => (1 - spring(t, t0, { k: 150, damp: 0.6 })) * hgt;
const ICONS = {
  coins(s, t) {
    const stack = (x, y, n, t0) => { for (let k = 0; k < n; k++) { const z = k * 15 * s + drop(t, t0 + k * 0.06, 200); if (t < t0 + k * 0.06) continue; isoCyl(x, y, z, 78 * s, 12 * s, { edge: GOLDC, fill: GOLDF }); } return n * 15 * s; };
    stack(-70 * s, -60 * s, 4, 0.0);
    const top = stack(40 * s, 30 * s, 7, 0.15);
    if (t > 0.6) { const fp = faceOf([40 * s - 40 * s, 30 * s - 40 * s, top + 1], [1, 0, 0], [0, 1, 0]); isoText(fp, '₺', 22 * s, 62 * s, 64 * s, { color: GOLDC, font: ANTON }); }
  },
  gold(s, t) {
    const bar = (x, y, z, t0) => { if (t < t0) return; const dz = drop(t, t0, 220); isoBox(x, y, z + dz, 150 * s, 66 * s, 34 * s, { r: 6 * s, seg: 3, edge: GOLDC, fill: GOLDF, creaseC: GOLDC });
      const fp = faceOf([x + 30 * s, y + 14 * s, z + dz + 34 * s], [1, 0, 0], [0, 1, 0]); faceRR(fp, 0, 0, 90 * s, 38 * s, 6 * s, { stroke: '#8A6A20' }); };
    bar(-160 * s, -40 * s, 0, 0.0); bar(-160 * s, 40 * s, 0, 0.08); bar(10 * s, -40 * s, 0, 0.16); bar(10 * s, 40 * s, 0, 0.24);
    bar(-75 * s, -0 * s, 36 * s, 0.4); bar(-75 * s, 72 * s, 36 * s, 0.48); bar(-30 * s, 30 * s, 72 * s, 0.62);
  },
  cash(s, t) {
    for (let k = 0; k < 6; k++) { const t0 = k * 0.07; if (t < t0) continue; const z = k * 12 * s + drop(t, t0, 200), rot = (k % 2 ? 8 : -6) * s;
      isoBox(-120 * s + rot, -60 * s - rot, z, 240 * s, 120 * s, 10 * s, { r: 6 * s, seg: 2, edge: BR.brand, fill: '#12302A', creaseC: BR.brand }); }
    if (t > 0.5) { const z = 72 * s, fp = faceOf([-120 * s + 8 * s, -60 * s + 8 * s, z], [1, 0, 0], [0, 1, 0]);
      faceRR(fp, 10 * s, 10 * s, 204 * s, 84 * s, 8 * s, { stroke: BR.brand }); isoText(fp, '₺', 96 * s, 76 * s, 60 * s, { color: BR.light, font: ANTON }); }
  },
  house(s, t) {
    const dz = drop(t, 0, 260), W0 = 200 * s, H0 = 130 * s, R = 90 * s, x0 = -100 * s, y0 = -100 * s, z0 = dz;
    isoPlates(x0 - 30 * s, y0 - 30 * s, -14 * s, W0 + 60 * s, W0 + 60 * s, [{ h: 10 * s, r: 20 * s }]);
    isoBox(x0, y0, z0, W0, W0, H0, { r: 4 * s, seg: 2, edge: BR.edge });
    const front = faceOf([x0, y0 + W0, z0 + H0], [1, 0, 0], [0, 0, -1]);
    faceRR(front, 120 * s, 50 * s, 46 * s, 80 * s, 4 * s, { stroke: GOLDC });
    faceRR(front, 30 * s, 40 * s, 56 * s, 44 * s, 4 * s, { stroke: BR.edge });
    const side = faceOf([x0 + W0, y0, z0 + H0], [0, 1, 0], [0, 0, -1]);
    faceRR(side, 40 * s, 40 * s, 56 * s, 44 * s, 4 * s, { stroke: BR.edge }); faceRR(side, 116 * s, 40 * s, 56 * s, 44 * s, 4 * s, { stroke: BR.edge });
    const rt = clamp(spring(t, 0.35, { k: 160, damp: 0.6 })), zt = z0 + H0, rz = zt + R * rt;
    const P = (x, y, z) => iso(x, y, z);
    // sağ üçgen alın, sonra ön çatı yüzü
    polyPath([P(x0 + W0 + 10 * s, y0 - 10 * s, zt), P(x0 + W0 + 10 * s, y0 + W0 + 10 * s, zt), P(x0 + W0 + 10 * s, y0 + W0 / 2, rz)], true);
    ctx.fillStyle = PAL.face; ctx.fill(); hair(BR.edge); ctx.stroke();
    polyPath([P(x0 - 10 * s, y0 + W0 / 2, rz), P(x0 + W0 + 10 * s, y0 + W0 / 2, rz), P(x0 + W0 + 10 * s, y0 + W0 + 10 * s, zt), P(x0 - 10 * s, y0 + W0 + 10 * s, zt)], true);
    ctx.fillStyle = '#3A1E10'; ctx.fill(); hair('#FF7A30'); ctx.stroke();
  },
  car(s, t) {
    const dz = drop(t, 0, 240), x0 = -150 * s, y0 = -60 * s;
    isoPlates(x0 - 40 * s, y0 - 40 * s, -14 * s, 380 * s, 200 * s, [{ h: 10 * s, r: 20 * s }]);
    isoBox(x0, y0, dz + 26 * s, 300 * s, 120 * s, 56 * s, { r: 24 * s, edge: '#3D8BD9', fill: '#12223A', creaseC: '#3D8BD9' });
    if (t > 0.25) isoBox(x0 + 80 * s, y0 + 8 * s, dz + 82 * s + drop(t, 0.25, 120), 140 * s, 104 * s, 46 * s, { r: 20 * s, edge: '#3D8BD9', fill: '#12223A', creaseC: '#3D8BD9' });
    const side = faceOf([x0, y0 + 120 * s + 1, dz + 40 * s], [1, 0, 0], [0, 0, -1]);
    for (const u of [62, 238]) faceEll(side, u * s, 14 * s, 30 * s, 30 * s, { fill: '#0B0F11', stroke: BR.edge });
    for (const u of [62, 238]) faceEll(side, u * s, 14 * s, 11 * s, 11 * s, { stroke: BR.edge });
  },
  bank(s, t) {
    const dz = drop(t, 0, 200), x0 = -150 * s, y0 = -90 * s;
    isoPlates(x0 - 20 * s, y0 - 20 * s, 0, 340 * s, 220 * s, [{ h: 14 * s, r: 10 * s }, { h: 12 * s, gap: 2 * s, inset: 12 * s, r: 8 * s }]);
    const zc = 28 * s;
    if (t > 0.15) for (let i = 0; i < 5; i++) { const zz = zc + drop(t, 0.15 + i * 0.06, 140); if (t < 0.15 + i * 0.06) continue; isoCyl(x0 + 30 * s + i * 60 * s, y0 + 150 * s, zz, 14 * s, 150 * s); }
    if (t > 0.5) { const zr = zc + 150 * s + drop(t, 0.5, 160); isoBox(x0, y0, zr, 300 * s, 180 * s, 22 * s, { r: 4 * s, edge: GOLDC, fill: GOLDF, creaseC: GOLDC });
      const fp = faceOf([x0, y0 + 180 * s, zr + 22 * s], [1, 0, 0], [0, 0, -1]);
      polyPath([isoP(fp(0, -2 * s)), isoP(fp(150 * s, -70 * s)), isoP(fp(300 * s, -2 * s))], true); ctx.fillStyle = GOLDF; ctx.fill(); hair(GOLDC); ctx.stroke();
      isoText(fp, '₺', 136 * s, -14 * s, 46 * s, { color: GOLDC, font: ANTON }); }
  },
  calendar(s, t) {
    const dz = drop(t, 0, 220), x0 = -110 * s;
    isoPlates(x0 - 40 * s, -40 * s, -14 * s, 300 * s, 140 * s, [{ h: 10 * s, r: 20 * s }]);
    const S = isoPanelY(x0, 0, dz, 220 * s, 240 * s, 24 * s, { r: 16 * s, edge: BR.edge });
    const fp = faceOf([x0, 24 * s, dz + 240 * s], [1, 0, 0], [0, 0, -1]);
    faceRR(fp, 0, 0, 220 * s, 50 * s, 12 * s, { fill: '#5A1410', stroke: BR.red });
    for (const u of [50, 170]) faceEll(fp, u * s, 0, 8 * s, 8 * s, { fill: PAL.face, stroke: BR.edge });
    for (let r = 0; r < 4; r++) for (let c = 0; c < 5; c++) { const on = r === 2 && c === 3 && t > 0.6;
      faceRR(fp, 16 * s + c * 40 * s, 66 * s + r * 42 * s, 30 * s, 30 * s, 5 * s, on ? { fill: '#12302A', stroke: BR.brand } : { stroke: PAL.inner }); }
  },
  chart(s, t) {
    isoPlates(-170 * s, -80 * s, -14 * s, 360 * s, 180 * s, [{ h: 10 * s, r: 20 * s }]);
    [70, 130, 210].forEach((h, i) => { const k = spring(t, 0.1 + i * 0.12, { k: 140, damp: 0.6 }); if (k <= 0.01) return;
      isoBox(-130 * s + i * 100 * s, -40 * s, 0, 64 * s, 64 * s, h * s * k, { r: 6 * s, edge: i === 2 ? BR.brand : BR.edge, fill: i === 2 ? '#12302A' : PAL.face, creaseC: i === 2 ? BR.brand : PAL.inner }); });
    const a = clamp((t - 0.5) / 0.5); if (a > 0) { const P3 = [[-150, 60, 90], [-20, 60, 150], [60, 60, 140], [150, 60, 300]].map((p) => [p[0] * s, p[1] * s, p[2] * s]);
      const n = 1 + a * (P3.length - 1), Q = P3.slice(0, Math.floor(n)); const f = n - Math.floor(n); if (f > 0 && Math.floor(n) < P3.length) { const p0 = P3[Math.floor(n) - 1], p1 = P3[Math.floor(n)]; Q.push(vadd(p0, vsc(vsub(p1, p0), f))); }
      line3(Q, GOLDC, 5); }
  },
  percent(s, t) {
    const dz = drop(t, 0, 220);
    isoCyl(0, 0, dz, 130 * s, 40 * s, { edge: '#FF7A30', fill: '#3A1E10' });
    const fp = faceOf([-90 * s, -40 * s, dz + 40 * s], [1, 0, 0], [0, 1, 0]); isoText(fp, '%', 30 * s, 110 * s, 150 * s, { color: '#FF7A30', font: ANTON });
  },
  card(s, t) {
    const dz = drop(t, 0, 220);
    isoBox(-150 * s, -95 * s, dz, 300 * s, 190 * s, 10 * s, { r: 18 * s, edge: '#9B86F0', fill: '#1E1A33', creaseC: '#9B86F0' });
    const fp = faceOf([-150 * s, -95 * s, dz + 10 * s], [1, 0, 0], [0, 1, 0]);
    faceRR(fp, 30 * s, 50 * s, 56 * s, 44 * s, 6 * s, { fill: GOLDF, stroke: GOLDC });
    isoText(fp, '•••• 2026', 30 * s, 150 * s, 30 * s, { color: '#C9C2F0' });
  },
  piggy(s, t) {   // kumbara: yuvarlak gövde + bozuk para yarığı + düşen bozuk para
    const dz = drop(t, 0, 220);
    isoPlates(-150 * s, -110 * s, -14 * s, 300 * s, 220 * s, [{ h: 10 * s, r: 20 * s }]);
    isoBox(-120 * s, -80 * s, dz + 10 * s, 240 * s, 160 * s, 150 * s, { r: 70 * s, seg: 8, edge: '#E05A8A', fill: '#3A1424', creaseC: '#E05A8A' });
    const top = faceOf([-120 * s, -80 * s, dz + 160 * s], [1, 0, 0], [0, 1, 0]); faceRR(top, 90 * s, 70 * s, 60 * s, 12 * s, 6 * s, { fill: '#0B0F11', stroke: '#E05A8A' });
    const c = 1 - clamp((t - 0.5) / 0.6); if (t > 0.5 && c > 0) isoCyl(0, -4 * s, dz + 160 * s + c * 160 * s, 34 * s, 8 * s, { edge: GOLDC, fill: GOLDF });
  },
};
function isoIcon(name, s, t) { (ICONS[name] || ICONS.coins)(s, t); }

// =====================================================================
//  Sahneler
// =====================================================================
const SC = {};
// büyük rakam + ikon (kanca için ideal): { icon, value, unit, suffix, label, count }
SC.big_number = (d, t, al) => {
  ctx.save(); ctx.globalAlpha = al;
  setIso({ ox: 470, oy: 900, u: 1 }); isoIcon(d.icon, 1.15, t);
  const k = d.count === false || Math.abs(d.value) < 100 ? 1 : EZ.o3((t - 0.2) / 0.9);   // küçük oranlar saymaz (%0,02 gibi ara değer olmasın)
  const v = d.value * k, str = fmtVal(v, d.unit, { dec: decOf(d.value), suffix: d.suffix });
  const pop = 1 + 0.08 * kick(t, 1.1, { k: 300, damp: 0.4 });
  ctx.save(); ctx.translate(470, 1250); ctx.scale(pop, pop);
  txt(str, 0, 0, fitFont(fmtVal(d.value, d.unit, { suffix: d.suffix }), 880, 170, ANTON), BR.gold, { align: 'center' });
  ctx.restore();
  if (d.label) txt(d.label.toLocaleUpperCase('tr-TR'), 470, 1322, fitFont(d.label.toLocaleUpperCase('tr-TR'), 860, 40, OSW, 500), BR.muted, { align: 'center', al: clamp((t - 0.4) / 0.4) });
  ctx.restore();
};
// ikon + kısa güçlü cümle ( *vurgu* altın ): { icon, text }
SC.icon_text = (d, t, al) => {
  ctx.save(); ctx.globalAlpha = al;
  setIso({ ox: 470, oy: 860, u: 1 }); isoIcon(d.icon, 1.1, t);
  const a = clamp(spring(t, 0.3, { k: 140, damp: 0.8 }));
  ctx.globalAlpha = al * a; richBlock(d.text || '', 470, 1190 + (1 - a) * 20, 860, 78, 88, 1);
  ctx.restore();
};
// patlatılmış katmanlar: { total:{label,value}, parts:[{label,value,hl}], unit }
SC.layers = (d, t, al) => {
  ctx.save(); ctx.globalAlpha = al;
  const parts = d.parts.slice(0, 5), tot = d.total?.value || parts.reduce((a, p) => a + p.value, 0);
  const KZ = 300 / tot, FW = 230, GAP = 40, open = spring(t, 0.7, { k: 70, damp: 0.7 });
  setIso({ ox: 390, oy: 1080, u: 1 });
  isoPlates(-30, -30, -18, FW + 60, FW + 60, [{ h: 10, r: 30 }]);
  const cols = parts.map((p, i) => (p.hl ? BR.brand : PALC[i % PALC.length]));
  let z = drop(t, 0, 400); const slots = [];
  for (let i = parts.length - 1; i >= 0; i--) {   // alttan üste: son parça en altta
    const p = parts[i], h = Math.max(9, p.value * KZ), shown = t > 0.9 + i * 0.35;
    isoBox(0, 0, z, FW, FW, h, { r: 16, edge: shown ? cols[i] : PAL.edge, fill: shown ? tint(cols[i]) : PAL.face, creaseC: shown ? cols[i] : PAL.inner });
    slots.push({ i, z, h }); z += h + GAP * open;
  }
  const ta = clamp(spring(t, 0.15, { k: 120, damp: 0.8 })) * (1 - clamp((t - 0.6) / 0.3));
  if (ta > 0.01 && d.total) { const p = iso(FW, 0, 150); txt((d.total.label || '').toLocaleUpperCase('tr-TR'), p[0] + 60, p[1] - 30, `500 26px ${DMONO}`, BR.muted, { al: ta * al });
    txt(fmtVal(d.total.value, d.unit), p[0] + 56, p[1] + 50, `84px ${ANTON}`, BR.gold, { al: ta * al }); }
  const labs = slots.slice().sort((a, b) => a.i - b.i).map((s) => ({ ...s, y: iso(FW, 0, s.z + s.h / 2)[1] }));
  for (let k = 1; k < labs.length; k++) if (labs[k].y < labs[k - 1].y + 100) labs[k].y = labs[k - 1].y + 100;
  const LX0 = 680;
  for (const s of labs) {
    const a = clamp(spring(t, 0.9 + s.i * 0.35, { k: 150, damp: 0.75 })); if (a <= 0.01) continue;
    const p = parts[s.i], c = cols[s.i], q = iso(FW, 0, s.z + s.h / 2);
    ctx.save(); ctx.globalAlpha = al * a;
    polyPath([[q[0] + 8, q[1]], [LX0 - 30, s.y], [LX0 - 12, s.y]], false); hair(c); ctx.stroke();
    ctx.beginPath(); ctx.arc(q[0] + 6, q[1], 5, 0, TAU); ctx.fillStyle = c; ctx.fill();
    const nm = String(s.i + 1).padStart(2, '0') + ' ' + (p.label || '').toLocaleUpperCase('tr-TR');
    txt(nm, LX0, s.y - 16, fitFont(nm, 380, 24, DMONO, 500), c);
    txt(fmtVal(p.value, d.unit), LX0, s.y + 42, `${p.hl ? 58 : 50}px ${ANTON}`, p.hl ? BR.light : BR.gold);
    ctx.restore();
  }
  ctx.restore();
};
// izometrik sütunlar: { items:[{label,value}], unit, hl: index }
SC.bars = (d, t, al) => {
  ctx.save(); ctx.globalAlpha = al;
  const it = d.items.slice(0, 6), n = it.length, P = n <= 3 ? 170 : n <= 5 ? 128 : 106, CW = P * 0.6, MH = 340;
  const mx = Math.max(...it.map((x) => Math.abs(x.value))) || 1, span = (n - 1) * P + CW;
  setIso({ ox: 470 - span / 2 + CW / 2 - 30, oy: 1010 - span / 4, u: 1 });
  isoPlates(-30, -30, -16, span + 60, CW + 60, [{ h: 10, r: 24 }]);
  it.forEach((x, i) => {
    const k = spring(t, 0.15 + i * 0.12, { k: 130, damp: 0.62 }); if (k <= 0.005) return;
    const hl = d.hl === i, c = hl ? BR.brand : (d.hl == null && i === n - 1 ? BR.brand : PALC[0]), h = Math.max(8, Math.abs(x.value) / mx * MH) * k;
    isoBox(i * P, 0, 0, CW, CW, h, { r: 8, seg: 3, edge: c, fill: tint(c), creaseC: c });
    const p = iso(i * P + CW / 2, 0, h + 10), a = clamp((k - 0.3) / 0.7);
    const fs = n <= 3 ? 64 : n <= 5 ? 46 : 38;
    txt(fmtVal(x.value * EZ.o3(k), d.unit, { dec: decOf(x.value), suffix: d.suffix }), p[0], p[1] - 46, `${fs}px ${ANTON}`, hl || (d.hl == null && i === n - 1) ? BR.light : BR.gold, { align: 'center', al: a });
    const lb = (x.label || '').toLocaleUpperCase('tr-TR');
    txt(lb, p[0], p[1] - 46 - fs - 4, fitFont(lb, P + 40, 24, DMONO, 500), BR.muted, { align: 'center', al: a });
  });
  ctx.restore();
};
// iki şey karşı karşıya: { a:{label,value}, b:{label,value}, unit, note } — a önde-solda, b arkada-sağda; etiketler en son
SC.compare = (d, t, al) => {
  ctx.save(); ctx.globalAlpha = al;
  const mx = Math.max(Math.abs(d.a.value), Math.abs(d.b.value)) || 1, MH = 360, CW = 160;
  setIso({ ox: 330, oy: 1060, u: 1 });
  isoPlates(-40, -330, -16, CW + 80, 330 + CW + 40, [{ h: 10, r: 26 }]);
  const cols = [[d.b, BR.brand, -300, 0.45], [d.a, '#FF7A30', 0, 0.15]];   // çizim sırası: arkadaki (b) önce
  const tops = [];
  for (const [x, c, Y, t0] of cols) {
    const k = spring(t, t0, { k: 110, damp: 0.62 }); if (k <= 0.005) { tops.push(null); continue; }
    const h = Math.max(10, Math.abs(x.value) / mx * MH) * k;
    isoBox(0, Y, 0, CW, CW, h, { r: 14, edge: c, fill: tint(c), creaseC: c });
    tops.push({ x, c, p: iso(CW / 2, Y + CW / 2, h + 12), a: clamp((k - 0.3) / 0.7) });
  }
  for (const o of tops) {
    if (!o) continue;
    const v = fmtVal(o.x.value, d.unit, { suffix: d.suffix }), lb = (o.x.label || '').toLocaleUpperCase('tr-TR');
    txt(v, o.p[0], o.p[1] - 40, fitFont(v, 300, 76, ANTON), o.c === BR.brand ? BR.light : '#FF9A5A', { align: 'center', al: o.a * al });
    txt(lb, o.p[0], o.p[1] - 122, fitFont(lb, 300, 30, DMONO, 500), BR.muted, { align: 'center', al: o.a * al });
  }
  if (d.note) { const a = clamp(spring(t, 1.0, { k: 160, damp: 0.5 }));
    if (a > 0.01) { ctx.save(); ctx.translate(470, 1340); ctx.scale(0.7 + 0.3 * a, 0.7 + 0.3 * a); ctx.globalAlpha = al * clamp(a);
      const nt = d.note.toLocaleUpperCase('tr-TR'), f = fitFont(nt, 640, 64, ANTON); ctx.font = f; const w = ctx.measureText(nt).width;
      ctx.fillStyle = BR.red; ctx.beginPath(); ctx.roundRect(-w / 2 - 30, -62, w + 60, 100, 14); ctx.fill(); txt(nt, 0, 14, f, BR.white, { align: 'center' }); ctx.restore(); } }
  ctx.restore();
};
// 3 adım merdiveni + altında numaralı liste: { items:[str, str, str] }
SC.steps = (d, t, al) => {
  ctx.save(); ctx.globalAlpha = al;
  const it = d.items.slice(0, 3), cols = [BR.edge, '#3D8BD9', BR.brand];
  setIso({ ox: 300, oy: 960, u: 1 });
  isoPlates(-30, -330, -16, 210, 510, [{ h: 10, r: 24 }]);
  for (let i = it.length - 1; i >= 0; i--) {   // arkadan öne (büyük -y arkada)
    const k = spring(t, 0.15 + i * 0.45, { k: 130, damp: 0.6 }); if (k <= 0.005) continue;
    const Y = -150 * i, h = (60 + i * 100) * k;
    isoBox(0, Y, 0, 150, 150, h, { r: 14, edge: cols[i], fill: tint(cols[i]), creaseC: cols[i] });
    const fp = faceOf([20, Y + 20, h], [1, 0, 0], [0, 1, 0]); isoText(fp, '0' + (i + 1), 22, 86, 60, { color: cols[i], font: ANTON });
  }
  it.forEach((s, i) => {
    const a = clamp(spring(t, 0.35 + i * 0.45, { k: 150, damp: 0.8 })); if (a <= 0.01) return;
    const y = 1196 + i * 80, tx = s.toLocaleUpperCase('tr-TR');
    txt('0' + (i + 1), 90 + (1 - a) * 20, y, `56px ${ANTON}`, cols[i] === BR.edge ? BR.muted : cols[i], { al: al * a });
    txt(tx, 170 + (1 - a) * 20, y, fitFont(tx, 740, 56, ANTON), BR.white, { al: al * a });
  });
  ctx.restore();
};
// kapanış: { l1, l2 } (+ CTA kartı)
SC.cta = (d, t, al) => {
  ctx.save(); ctx.globalAlpha = al * 0.35; setIso({ ox: 470, oy: 760, u: 1 }); isoIcon(d.icon || 'coins', 1.0, t + 2); ctx.restore();
  ctaCard(-1e9, { l1: d.l1, l2: d.l2, sub: d.sub, al, t });
};
