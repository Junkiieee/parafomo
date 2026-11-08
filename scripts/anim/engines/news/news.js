// =====================================================================
//  news — piyasa bülteni paketi (Lemo-Opuscar "news-package" stilinden uyarlandı, MIT © 2026 LemoLab).
//  Veriyle sürülür: TL.data.scenes = [{type, head, data, line}] · TL.lines = [{id,t0,t1,cap,words[]}].
//  Parçalar: köşe PARAFOMO plakası · kalıcı alt bant · tabela gibi dönen rakamlar · bant silme geçişi ·
//  kelime-senkron altyazı. 0. kare kanca sahnesi yerleşmiş hâlde (kapak karesi boş olmaz).
//  Sözleşme (scripts/anim/render.mjs): window.ANIM_READY + window.renderFrame(f) → base64 JPEG.
// =====================================================================
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const seg = (t, a, b) => clamp((t - a) / (b - a));
const eio = (t) => { t = clamp(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
const eo = (t) => 1 - Math.pow(1 - clamp(t), 3);
const back = (t, s = 1.8) => { t = clamp(t) - 1; return 1 + t * t * ((s + 1) * t + s); };
const hash = (n) => { n = Math.sin(n * 127.1 + 311.7) * 43758.5453; return n - Math.floor(n); };

const cv = document.getElementById('c'); cv.width = W; cv.height = H;
const ctx = cv.getContext('2d');
const C = { ink: '#121417', ink2: '#1B1E23', ink3: '#22262C', acc: '#F2CF1D', gold: '#D4B064', paper: '#F4F1E8', olive: '#6E5A1E', red: '#FE6B3D', grey: '#8A8F99', dim: '#5B606B' };
const GD = TL.data, GS = GD.scenes || [], LINES = TL.lines;
const Lx = Object.fromEntries(LINES.map((l) => [l.id, l]));
const UP = (s) => String(s || '').toLocaleUpperCase('tr-TR');
const f = (px, fam = 'Bar', wg = 800) => `${wg} ${px}px ${fam}`;
function txt(s, x, y, px, c, al = 'left', fam = 'Bar', wg = 800, track = 0) {
  ctx.save(); ctx.font = f(px, fam, wg); ctx.fillStyle = c; ctx.textAlign = al; ctx.textBaseline = 'middle';
  ctx.letterSpacing = track + 'px'; ctx.fillText(s, x, y); ctx.restore();
}
function fitPx(s, maxW, px, fam = 'Bar', wg = 800, min = 24, track = 0) {
  ctx.save(); ctx.letterSpacing = track + 'px';
  ctx.font = f(px, fam, wg); while (ctx.measureText(s).width > maxW && px > min) { px -= 2; ctx.font = f(px, fam, wg); }
  ctx.restore(); return px;
}
function wrap(s, maxW, px, fam = 'Bar', wg = 800) {   // kelimeleri satırlara böl
  ctx.save(); ctx.font = f(px, fam, wg);
  const out = []; let cur = '';
  for (const w of String(s).split(/\s+/)) {
    const nx = cur ? cur + ' ' + w : w;
    if (cur && ctx.measureText(nx.replace(/\*/g, '')).width > maxW) { out.push(cur); cur = w; } else cur = nx;
  }
  if (cur) out.push(cur); ctx.restore(); return out;
}
const pop = (t, t0, d = 0.32) => back(seg(t, t0, t0 + d), 1.8);
const rr = (x, y, w, h, r) => { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); };

// ---- sayı biçimi (scenes.js fmtVal ile aynı kural) ----
const decOf = (v) => (Math.abs(v - Math.round(v)) < 1e-9 ? 0 : (Math.abs(v * 10 - Math.round(v * 10)) < 1e-9 ? 1 : 2));
const fmtNum = (v, d) => Number(v).toLocaleString('tr-TR', { minimumFractionDigits: d ?? decOf(v), maximumFractionDigits: d ?? decOf(v) });
function fmtVal(v, unit, o = {}) {
  v = Number(v) || 0;
  const money = unit === '₺' || unit === '$' || unit === '€';
  const n = fmtNum(money && Math.abs(v) >= 100 ? Math.round(v) : v, money && Math.abs(v) >= 100 ? 0 : undefined);
  const sx = o.suffix && !o.noSuffix ? ' ' + o.suffix : '';
  if (money) return unit + n + sx;
  if (unit === '%') return '%' + n;
  if (unit === 'x') return n + 'x';
  return n + sx + (unit ? ' ' + unit : '');
}

// ---- zamanlama: sahne başı + konuşulan kelime anı ----
const N = GS.length;
const lineOf = (i) => Lx[GS[i] && GS[i].line] || LINES[Math.min(i, LINES.length - 1)];
const CUT = GS.map((sc, i) => (i === 0 ? 0 : lineOf(i).t0 - 0.16));
const norm = (w) => String(w).toLocaleLowerCase('tr-TR').replace(/^[^\p{L}\p{N}%₺$€]+|[^\p{L}\p{N}%₺$€]+$/gu, '');
function wordsOf(l) { const ws = l.cap.split(/\s+/); return ws.map((w, i) => ({ w: norm(w), t: l.words && l.words[i] != null ? l.words[i] : l.t0 + (l.t1 - l.t0) * i / ws.length })); }
function numTime(i, v, fb) {   // satırda o rakamın söylendiği an (yoksa / çok geçse fb): ekran uzun süre boş kalmaz
  const T0 = i === 0 ? 0 : CUT[i] + 0.16, r = numTime0(i, v, fb);
  return r - T0 > 2.5 ? fb : r;
}
function numTime0(i, v, fb) {
  if (v == null) return fb;
  const l = lineOf(i), cands = [fmtNum(Number(v)), fmtNum(Math.round(Number(v)))];
  const hit = wordsOf(l).find((o) => cands.some((c) => o.w === c || o.w.endsWith(c) || o.w.startsWith(c + "'")));
  return hit ? hit.t : fb;
}
function textTime(i, s, fb) {   // satırda o metnin ilk kelimesinin söylendiği an
  const k = norm(String(s || '').split(/\s+/)[0] || ''); if (k.length < 3) return fb;
  const hit = wordsOf(lineOf(i)).find((o) => o.w.startsWith(k.slice(0, Math.max(3, k.length - 2))));
  return hit ? hit.t : fb;
}
const NUMERIC = new Set(['big_number', 'layers', 'bars', 'compare']);

// ---------- paket parçaları ----------
function plate(cx, cy, s) {   // marka plakası: paralelkenar, sol mürekkep + altın çubuk
  ctx.save(); ctx.translate(cx, cy); ctx.scale(s, s);
  const w = 560, h = 170, sk = 40;
  ctx.fillStyle = C.acc; ctx.beginPath(); ctx.moveTo(-w / 2 + sk, -h / 2); ctx.lineTo(w / 2 + sk, -h / 2); ctx.lineTo(w / 2 - sk, h / 2); ctx.lineTo(-w / 2 - sk, h / 2); ctx.closePath(); ctx.fill();
  ctx.fillStyle = C.ink; ctx.fillRect(-w / 2 - 10, -h / 2 + 18, 18, h - 36); ctx.fillStyle = C.gold; ctx.fillRect(-w / 2 + 16, -h / 2 + 18, 8, h - 36);
  ctx.font = f(120); ctx.textBaseline = 'middle'; ctx.textAlign = 'center'; ctx.fillStyle = C.ink; ctx.fillText('PARAFOMO', 18, 6);
  ctx.restore();
}
function cornerTag(s, t, t0) {   // ÖRNEK etiketi (0,2 sn'de açılır)
  if (t < t0) return; const k = t0 <= 0 ? 1 : eo(seg(t, t0, t0 + 0.2));
  ctx.save(); ctx.font = f(26, 'Mono', 600); ctx.letterSpacing = '2px'; const w = ctx.measureText(s).width + 40; ctx.restore();
  ctx.save(); ctx.translate(60, 92); ctx.scale(1, k); ctx.strokeStyle = C.gold; ctx.lineWidth = 3; rr(0, -32, w, 64, 4); ctx.stroke();
  txt(s, 20, 2, 26, C.gold, 'left', 'Mono', 600, 2); ctx.restore();
}
function eyebrow(s, x, y, t, t0) {
  if (t < t0 || !s) return; ctx.save(); ctx.globalAlpha = t0 <= 0 ? 1 : eo(seg(t, t0, t0 + 0.25));
  txt(s, x, y, fitPx(s, 960, 26, 'Mono', 500, 18, 3), C.gold, 'left', 'Mono', 500, 3); ctx.restore();
}
function title(s, y, t, t0, px = 100) {
  if (!s) return;
  const lines = wrap(s, 960, px); if (lines.length > 2) px = 76;
  const L2 = wrap(s, 960, px).slice(0, 2);
  const k = t0 <= 0 ? 1 : eo(seg(t, t0, t0 + 0.3));
  ctx.save(); ctx.globalAlpha = k; ctx.translate(0, (1 - k) * 24);
  L2.forEach((l, j) => txt(l, 60, y + j * px * 0.98, fitPx(l, 960, px), C.paper));
  ctx.restore(); return L2.length;
}
// alt bant: sekme = üst etiket + bölüm sayacı, başlık = videonun konusu (sabit), kaynak satırı spec'ten
const STRAP_TAB = UP(GD.eyebrow || 'PARAFOMO BÜLTEN');
const STRAP_HEAD = META.title || '';
function strap(t, i) {
  const y = 1250, x = 60;
  ctx.save();
  const t0 = CUT[i], flash = i > 0 ? clamp(1 - (t - t0) / 0.25) : 0;
  const tab = STRAP_TAB + `  ${String(i + 1).padStart(2, '0')}/${String(Math.max(1, N - 1)).padStart(2, '0')}`;
  const tpx = fitPx(tab, 820, 30, 'Mono', 600, 20, 2);
  ctx.font = f(tpx, 'Mono', 600); ctx.letterSpacing = '2px'; const tw = Math.min(960, ctx.measureText(tab).width + 44); ctx.letterSpacing = '0px';
  ctx.fillStyle = flash > 0 ? `rgb(${lerp(242, 255, flash)},${lerp(207, 255, flash)},${lerp(29, 255, flash)})` : C.acc; ctx.fillRect(x, y, tw, 56);
  txt(tab, x + 22, y + 29, tpx, C.ink, 'left', 'Mono', 600, 2);
  ctx.fillStyle = C.paper; ctx.fillRect(x, y + 56, 860, 118); ctx.fillStyle = C.ink2; ctx.fillRect(x + 860, y + 56, 100, 118);
  ctx.fillStyle = C.acc; ctx.fillRect(x + 880, y + 96, 60, 8); ctx.fillRect(x + 880, y + 112, 40, 8);
  ctx.beginPath(); ctx.rect(x, y + 56, 860, 118); ctx.clip();
  let px = fitPx(STRAP_HEAD, 810, 56, 'Bar', 800, 40);
  ctx.font = f(px);
  if (ctx.measureText(STRAP_HEAD).width > 810) {   // iki satır
    const L2 = wrap(STRAP_HEAD, 810, 46).slice(0, 2);
    L2.forEach((l, j) => txt(l, x + 28, y + 90 + j * 50, fitPx(l, 810, 46), C.ink));
  } else txt(STRAP_HEAD, x + 28, y + 115, px, C.ink);
  ctx.restore();
  if (META.source && NUMERIC.has(GS[i].type)) {
    ctx.save(); ctx.globalAlpha = 0.75; const s = 'KAYNAK: ' + UP(META.source);
    txt(s, 1020, y + 205, fitPx(s, 960, 22, 'Mono', 500, 16, 1), C.gold, 'right', 'Mono', 500, 1); ctx.restore();
  }
}
// altyazı: kelime-senkron, söylenen kelime tam opak, anahtar kelime vurgu renginde
const CHUNKS = [];
for (const l of LINES) {
  const ws = l.cap.split(/\s+/), ts = l.words && l.words.length === ws.length ? l.words : ws.map((_, i) => l.t0 + (l.t1 - l.t0) * i / ws.length);
  let cur = [], t0 = ts[0];
  const flush = (tEnd) => { if (cur.length) CHUNKS.push({ id: l.id, t0, t1: tEnd, words: cur }); cur = []; };
  ws.forEach((w, i) => {
    const len = cur.map((x) => x.w).join(' ').length + w.length + 1;
    if (cur.length && (len > 27 || /[;:,.]$/.test(cur[cur.length - 1].w))) { flush(ts[i]); t0 = ts[i]; }
    cur.push({ w, t: ts[i] });
  });
  flush(l.t1 + 0.25);
}
const EMPH = new Set();
for (const sc of GS) for (const m of String((sc.data || {}).text || '').matchAll(/\*([^*]+)\*/g)) m[1].split(/\s+/).forEach((w) => EMPH.add(norm(w)));
const KEY = /\d|₺|%|abone/i;
const isKey = (w) => KEY.test(w) || EMPH.has(norm(w));
function caption(t) {
  let ch = null; for (const k of CHUNKS) if (t >= k.t0 - 0.05 && t < k.t1) ch = k;
  if (!ch) return;
  const y = 1560, k = eo(seg(t, ch.t0, ch.t0 + 0.18));
  const words = ch.words.map((o) => o.w.replace(/[;:]$/, ''));
  let px = 78; ctx.save(); ctx.font = f(px);
  const width = () => { const sp = ctx.measureText(' ').width; return words.reduce((a, w) => a + ctx.measureText(w).width, 0) + sp * (words.length - 1); };
  while (width() > 980 && px > 50) { px -= 2; ctx.font = f(px); }
  const sp = ctx.measureText(' ').width, ws = words.map((w) => ctx.measureText(w).width);
  let x = 540 - width() / 2; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  words.forEach((w, i) => {
    const said = t >= ch.words[i].t - 0.02;
    ctx.globalAlpha = (said ? 1 : 0.5) * k; ctx.lineWidth = 12; ctx.strokeStyle = C.ink; ctx.strokeText(w, x, y + (1 - k) * 20);
    ctx.fillStyle = isKey(w) ? C.acc : C.paper; ctx.fillText(w, x, y + (1 - k) * 20); x += ws[i] + sp;
  });
  ctx.restore();
}
// tabela: eski ve yeni değer aynı panoda, karakter karakter döner
function flapBoard(cx, cy, oldS, newS, tf, t, maxW = 960) {
  const n = Math.max(oldS.length, newS.length), gap = 10;
  const tw = Math.min(150, (maxW - gap * (n - 1)) / n), th = tw * 1.53, px = tw * 1.37;
  const os = oldS.padStart(n, ' '), ns = newS.padStart(n, ' '), x0 = cx - (n * (tw + gap) - gap) / 2;
  for (let i = 0; i < n; i++) {
    const x = x0 + i * (tw + gap), y = cy - th / 2, ti = tf + i * 0.05, p = tf == null ? 1 : seg(t, ti, ti + 0.18);
    const a = os[i], b = ns[i];
    const tile = (ch, half, sy = 1) => {
      ctx.save(); ctx.beginPath(); ctx.rect(x, y + half * th / 2, tw, th / 2); ctx.clip();
      const hy = y + th / 2; ctx.translate(0, hy); ctx.scale(1, sy); ctx.translate(0, -hy);
      ctx.fillStyle = half ? C.ink2 : C.ink3; rr(x, y, tw, th, 8); ctx.fill();
      if (ch !== ' ') { ctx.font = f(/[.,]/.test(ch) ? px : px); ctx.fillStyle = /[₺$€%]/.test(ch) ? C.gold : C.paper; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(ch, x + tw / 2, y + th / 2 + px * 0.04); }
      ctx.restore();
    };
    if (p <= 0 || a === b) { tile(p >= 1 ? b : a, 0); tile(p >= 1 ? b : a, 1); }
    else if (p >= 1) { tile(b, 0); tile(b, 1); }
    else if (p < 0.5) { tile(b, 0); tile(a, 1); tile(a, 0, 1 - p * 2); }
    else { tile(b, 0); tile(a, 1); tile(b, 1, (p - 0.5) * 2); }
    ctx.fillStyle = C.ink; ctx.fillRect(x, y + th / 2 - 2, tw, 4);
  }
  return th;
}
function pill(s, x, y, t, t0, o = {}) {   // vurgu renginde kutu (soldan kayarak gelir)
  if (t0 > 0 && t < t0) return;
  const k = t0 <= 0 ? 1 : pop(t, t0);
  const px = fitPx(s, (o.maxW || 960) - 52, o.px || 58);
  ctx.save(); ctx.font = f(px); const w = ctx.measureText(s).width + 52; ctx.restore();
  const bx = o.al === 'right' ? x - w : o.al === 'center' ? x - w / 2 : x;
  ctx.save(); ctx.globalAlpha = clamp(k); ctx.translate((1 - k) * 60, 0);
  ctx.fillStyle = o.c || C.acc; rr(bx, y - 50, w, 100, 6); ctx.fill(); txt(s, bx + 26, y + 1, px, C.ink); ctx.restore();
}
function stamp(s, cx, cy, t, t0, rot = -0.12) {   // damga: 1,9×'ten 0,16 sn'de iner, halka yayılır
  if (t < t0) return;
  const k = t0 <= 0 ? 1 : seg(t, t0, t0 + 0.16), sc = lerp(1.9, 1, eo(k));
  const px = fitPx(s, 420, 84);
  ctx.save(); ctx.font = f(px); const w = ctx.measureText(s).width + 70; ctx.restore();
  ctx.save(); ctx.translate(cx, cy); ctx.rotate(rot); ctx.scale(sc, sc); ctx.globalAlpha = clamp(k * 2);
  ctx.fillStyle = C.acc; rr(-w / 2, -70, w, 140, 6); ctx.fill(); ctx.strokeStyle = C.ink; ctx.lineWidth = 5; rr(-w / 2 + 14, -56, w - 28, 112, 4); ctx.stroke();
  txt(s, 0, 6, px, C.ink, 'center'); ctx.restore();
  if (t0 > 0 && t < t0 + 0.5) { const e = seg(t, t0, t0 + 0.5); ctx.save(); ctx.globalAlpha = 1 - e; ctx.strokeStyle = C.acc; ctx.lineWidth = 5; ctx.beginPath(); ctx.ellipse(cx, cy, w / 2 + 10 + e * 260, 80 + e * 90, rot, 0, 6.28); ctx.stroke(); ctx.restore(); }
}
function bandWipe(t, T, drawOld, drawNew) {   // dikey bant (vurgu 84 + mürekkep 5 + altın 14) soldan sağa süpürür
  const p = eio(seg(t, T - 0.15, T + 0.15)), bx = lerp(-120, W + 120, p);
  ctx.save(); ctx.beginPath(); ctx.rect(bx, 0, W - bx + 1, H); ctx.clip(); drawOld(); ctx.restore();
  ctx.save(); ctx.beginPath(); ctx.rect(0, 0, bx, H); ctx.clip(); drawNew(); ctx.restore();
  ctx.fillStyle = C.gold; ctx.fillRect(bx - 14, 0, 14, H); ctx.fillStyle = C.ink; ctx.fillRect(bx - 19, 0, 5, H); ctx.fillStyle = C.acc; ctx.fillRect(bx - 103, 0, 84, H);
}
function bg(t, seed) {   // mürekkep panel + ışık kanatları + ızgara
  ctx.fillStyle = C.ink; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.globalAlpha = 0.07; ctx.fillStyle = C.paper;
  for (let i = 0; i < 4; i++) { const x = ((hash(seed + i) * 1400 + t * 18 * (i % 2 ? 1 : -1)) % 1600) - 300; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x + 120, 0); ctx.lineTo(x - 260, H); ctx.lineTo(x - 380, H); ctx.fill(); }
  ctx.restore();
  ctx.strokeStyle = 'rgba(212,176,100,0.10)'; ctx.lineWidth = 1; for (let y = 200; y < 1200; y += 80) { ctx.beginPath(); ctx.moveTo(60, y); ctx.lineTo(1020, y); ctx.stroke(); }
}
// basit çizgi ikonlar (vurgu renginde)
function icon(name, cx, cy, s, t, t0) {
  const k = t0 <= 0 ? 1 : pop(t, t0, 0.4);
  ctx.save(); ctx.translate(cx, cy); ctx.scale(s * clamp(k, 0, 1.2), s * clamp(k, 0, 1.2)); ctx.globalAlpha = clamp(k);
  ctx.strokeStyle = C.acc; ctx.fillStyle = C.acc; ctx.lineWidth = 10; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  const R = (x, y, w, h) => { ctx.beginPath(); ctx.roundRect(x, y, w, h, 10); ctx.stroke(); };
  switch (name) {
    case 'calendar': R(-90, -80, 180, 170); ctx.fillRect(-90, -80, 180, 44); ctx.beginPath(); ctx.moveTo(-50, -105); ctx.lineTo(-50, -60); ctx.moveTo(50, -105); ctx.lineTo(50, -60); ctx.stroke();
      for (let r = 0; r < 2; r++) for (let c = 0; c < 3; c++) ctx.fillRect(-60 + c * 48, -10 + r * 44, 24, 24); break;
    case 'percent': ctx.beginPath(); ctx.moveTo(70, -90); ctx.lineTo(-70, 90); ctx.stroke(); ctx.beginPath(); ctx.arc(-55, -55, 30, 0, 6.28); ctx.stroke(); ctx.beginPath(); ctx.arc(55, 55, 30, 0, 6.28); ctx.stroke(); break;
    case 'chart': ctx.beginPath(); ctx.moveTo(-100, -90); ctx.lineTo(-100, 90); ctx.lineTo(100, 90); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(-70, 50); ctx.lineTo(-20, 10); ctx.lineTo(20, 30); ctx.lineTo(80, -60); ctx.stroke(); ctx.beginPath(); ctx.moveTo(50, -62); ctx.lineTo(82, -62); ctx.lineTo(82, -30); ctx.stroke(); break;
    case 'card': R(-110, -70, 220, 140); ctx.fillRect(-110, -35, 220, 26); ctx.fillRect(-80, 25, 60, 14); break;
    case 'house': ctx.beginPath(); ctx.moveTo(-100, -5); ctx.lineTo(0, -95); ctx.lineTo(100, -5); ctx.stroke(); R(-75, -20, 150, 110); R(-22, 30, 44, 60); break;
    case 'car': ctx.beginPath(); ctx.moveTo(-110, 40); ctx.lineTo(-110, 0); ctx.lineTo(-70, -10); ctx.lineTo(-40, -55); ctx.lineTo(45, -55); ctx.lineTo(75, -10); ctx.lineTo(110, 0); ctx.lineTo(110, 40); ctx.closePath(); ctx.stroke();
      ctx.beginPath(); ctx.arc(-60, 45, 24, 0, 6.28); ctx.stroke(); ctx.beginPath(); ctx.arc(60, 45, 24, 0, 6.28); ctx.stroke(); break;
    case 'bank': ctx.beginPath(); ctx.moveTo(-110, -40); ctx.lineTo(0, -100); ctx.lineTo(110, -40); ctx.closePath(); ctx.stroke();
      for (const x of [-70, -23, 23, 70]) { ctx.beginPath(); ctx.moveTo(x, -20); ctx.lineTo(x, 60); ctx.stroke(); } ctx.beginPath(); ctx.moveTo(-115, 85); ctx.lineTo(115, 85); ctx.stroke(); break;
    case 'piggy': ctx.beginPath(); ctx.ellipse(0, 10, 105, 75, 0, 0, 6.28); ctx.stroke(); ctx.fillRect(-25, -72, 50, 12); ctx.beginPath(); ctx.arc(45, -10, 8, 0, 6.28); ctx.fill(); break;
    case 'gold': for (const [x, y] of [[-60, 40], [60, 40], [0, -30]]) { ctx.beginPath(); ctx.moveTo(x - 55, y + 30); ctx.lineTo(x - 35, y - 30); ctx.lineTo(x + 35, y - 30); ctx.lineTo(x + 55, y + 30); ctx.closePath(); ctx.stroke(); } break;
    case 'cash': R(-120, -60, 240, 120); ctx.beginPath(); ctx.arc(0, 0, 32, 0, 6.28); ctx.stroke(); break;
    default:   // coins + bilinmeyen
      for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.ellipse(0, 60 - i * 40, 90, 26, 0, 0, 6.28); ctx.stroke(); }
  }
  ctx.restore();
}

// ---------- sahne tipleri: (d, t, i, T0, first) ----------
const GTOP = 400;   // üst etiket satırı; başlık 490
const SC = {};
SC.big_number = (d, t, i, T0, first) => {
  const val = fmtVal(d.value, d.unit, { suffix: d.suffix, noSuffix: true });
  const tf = first ? null : numTime(i, d.value, T0 + 0.35) - 0.12;
  const th = flapBoard(540, 820, ' '.repeat(val.length), val, tf, t);
  if (d.suffix) txt(UP(d.suffix), 1020, 820 + th / 2 + 50, 64, C.gold, 'right', 'Bar', 800);
  if (d.label) pill(UP(d.label), 60, 1080, t, first ? 0 : (tf ?? T0) + 0.45, { px: 52 });
};
SC.compare = (d, t, i, T0, first) => {
  const a = d.a || {}, b = d.b || {}, u = d.unit || '';
  const va = Math.abs(Number(a.value) || 0), vb = Math.abs(Number(b.value) || 0), mx = Math.max(va, vb, 1e-9);
  const base = 1150, sc = 440 / mx;
  const tA = first ? 0 : numTime(i, a.value, T0 + 0.3) - 0.1, tB = first ? 0 : numTime(i, b.value, T0 + 0.9) - 0.1;
  const bar = (x, v, lab, s, t0, col) => {
    if (!first && t < t0) return; const k = first ? 1 : eo(seg(t, t0, t0 + 0.5)), h = Math.max(6, v * sc) * k;
    ctx.fillStyle = col; ctx.fillRect(x, base - h, 300, h);
    txt(s, x + 150, base - h - 50, fitPx(s, 420, 72), col === C.acc ? C.acc : C.paper, 'center');
    txt(UP(lab), x + 150, base + 40, fitPx(UP(lab), 420, 32, 'Mono', 600, 18, 2), C.gold, 'center', 'Mono', 600, 2);
  };
  ctx.fillStyle = C.paper; ctx.fillRect(60, base, 960, 4);
  bar(140, va, a.label, fmtVal(a.value, u), tA, C.grey);
  bar(640, vb, b.label, fmtVal(b.value, u), tB, C.acc);
  if (d.note) {
    const nv = (String(d.note).match(/\d[\d.,]*/) || [])[0];
    const tn = first ? 0 : Math.max(tB + 0.6, textTime(i, nv, tB + 0.8) - 0.1);
    const hiH = Math.max(va, vb) * sc, hiX = va > vb ? 290 : 790;   // damga uzun çubuğun gövdesine iner ("X DAHA YÜKSEK" doğru sütunda)
    if (hiH >= 170) stamp(UP(d.note), hiX, base - hiH / 2, t, tn, -0.1);
    else stamp(UP(d.note), 540, 640, t, tn, -0.06);
  }
};
SC.layers = (d, t, i, T0, first) => {
  const parts = (d.parts || []).slice(0, 4), u = d.unit || '', tot = d.total || {};
  const sum = parts.reduce((s, p) => s + Math.abs(Number(p.value) || 0), 0) || 1;
  const val = fmtVal(tot.value, u);
  const tT = first ? null : numTime(i, tot.value, T0 + 0.4) - 0.12;
  txt(UP(tot.label || ''), 60, 600, 32, C.gold, 'left', 'Mono', 600, 2);
  flapBoard(540, 730, ' '.repeat(val.length), val, tT, t, 760);
  // yatay yığın çubuk: parçalar sırayla dolar, vurgulanan parça vurgu renginde
  const y = 900, hgt = 120; let x = 60;
  parts.forEach((p, j) => {
    const w = 960 * Math.abs(Number(p.value) || 0) / sum, t0 = first ? 0 : numTime(i, p.value, T0 + 0.3 + j * 0.5) - 0.1;
    const k = first ? 1 : eo(seg(t, t0, t0 + 0.45));
    ctx.fillStyle = p.hl ? C.acc : (j % 2 ? C.dim : C.grey); ctx.fillRect(x, y, Math.max(2, w * k - 6), hgt);
    if (k > 0.3) {
      ctx.save(); ctx.globalAlpha = clamp((k - 0.3) / 0.4);
      const cx = x + Math.max(w, 1) / 2, al = w < 260 ? (j === parts.length - 1 ? 'right' : 'left') : 'center', tx = al === 'center' ? cx : al === 'right' ? x + w - 6 : x;
      const vs = fmtVal(p.value, u), ls = UP(p.label || '');
      txt(vs, tx, y + hgt + 60, fitPx(vs, Math.max(w, 300), 64), p.hl ? C.acc : C.paper, al);
      txt(ls, tx, y + hgt + 120, fitPx(ls, Math.max(w, 300), 30, 'Mono', 600, 16, 2), C.gold, al, 'Mono', 600, 2);
      ctx.restore();
    }
    x += w;
  });
};
SC.bars = (d, t, i, T0, first) => {
  const items = (d.items || []).slice(0, 5), u = d.unit || '', n = Math.max(1, items.length);
  const mx = Math.max(...items.map((o) => Math.abs(Number(o.value) || 0)), 1e-9);
  const base = 1150, sc = 440 / mx, gap = 40, bw = Math.min(300, (960 - gap * (n - 1) - 40) / n);
  const x0 = 540 - (n * bw + (n - 1) * gap) / 2;
  ctx.fillStyle = C.paper; ctx.fillRect(60, base, 960, 4);
  items.forEach((o, j) => {
    const t0 = first ? 0 : numTime(i, o.value, T0 + 0.3 + j * 0.45) - 0.1;
    if (!first && t < t0) return;
    const k = first ? 1 : eo(seg(t, t0, t0 + 0.5)), h = Math.max(6, Math.abs(Number(o.value) || 0) * sc) * k, x = x0 + j * (bw + gap);
    const hl = d.hl === j, col = hl ? C.acc : C.grey;
    ctx.fillStyle = col; ctx.fillRect(x, base - h, bw, h);
    const s = fmtVal(o.value, u, { suffix: d.suffix });
    txt(s, x + bw / 2, base - h - 46, fitPx(s, bw + gap - 6, 66), hl ? C.acc : C.paper, 'center');
    txt(UP(o.label), x + bw / 2, base + 40, fitPx(UP(o.label), bw + gap - 6, 30, 'Mono', 600, 16, 2), C.gold, 'center', 'Mono', 600, 2);
  });
};
SC.steps = (d, t, i, T0, first, titleLines) => {
  const items = (d.items || []).slice(0, 4), n = Math.max(1, items.length);
  const l = lineOf(i);
  const top = titleLines > 1 ? 690 : 620, rowH = Math.min(150, (1170 - top - 84) / n);
  const k = first ? 1 : eo(seg(t, T0 + 0.05, T0 + 0.55)), dx = lerp(1100, 0, k), rot = lerp(0.25, -0.015, k);
  const hgt = 84 + n * rowH + 20, cy = top + hgt / 2;
  ctx.save(); ctx.translate(540 + dx, cy); ctx.rotate(rot); ctx.scale(lerp(0.3, 1, k), lerp(0.3, 1, k));
  ctx.fillStyle = C.paper; ctx.fillRect(-480, -hgt / 2, 960, hgt); ctx.fillStyle = C.ink; ctx.fillRect(-480, -hgt / 2, 960, 84);
  txt('KONTROL LİSTESİ', -450, -hgt / 2 + 42, 34, C.acc, 'left', 'Mono', 600, 3);
  items.forEach((s, j) => {
    const span = (l.t1 - l.t0), tt = first ? 0 : textTime(i, s, l.t0 + span * (j + 0.5) / n) + 0.1;
    const y = -hgt / 2 + 84 + rowH * (j + 0.5) + 10, bs = Math.min(84, rowH - 30);
    ctx.strokeStyle = C.ink; ctx.lineWidth = 6; ctx.strokeRect(-440, y - bs / 2, bs, bs);
    if (t > tt) { const kk = first ? 1 : eo(seg(t, tt, tt + 0.22)); ctx.strokeStyle = C.olive; ctx.lineWidth = 14; ctx.lineCap = 'round';
      const bx = -440, by = y - bs / 2; ctx.beginPath(); ctx.moveTo(bx + bs * 0.2, by + bs * 0.5);
      ctx.lineTo(bx + bs * 0.2 + bs * 0.25 * clamp(kk * 2), by + bs * 0.5 + bs * 0.28 * clamp(kk * 2));
      if (kk > 0.5) ctx.lineTo(bx + bs * 0.45 + bs * 0.6 * (kk - 0.5) * 2, by + bs * 0.78 - bs * 0.75 * (kk - 0.5) * 2); ctx.stroke(); }
    const done = t > tt;
    txt(s, -440 + bs + 34, y + 4, fitPx(s, 960 - bs - 100, Math.min(76, rowH * 0.6)), done ? C.ink : '#6B6F78');
  });
  ctx.restore();
};
SC.icon_text = (d, t, i, T0, first, titleLines) => {
  const top = titleLines > 1 ? 700 : 640;
  icon(d.icon, 540, top + 90, 1.0, t, first ? 0 : T0 + 0.1);
  const raw = String(d.text || ''), px0 = 92;
  let px = px0, L = wrap(raw, 940, px); while (L.length > 3 && px > 60) { px -= 6; L = wrap(raw, 940, px); }
  const y0 = top + 290;
  // vurgulanan kelimeler (*...*) konuşulduğu an sarı kutuya girer
  let star = false;
  L.forEach((ln, j) => {
    const toks = ln.split(/\s+/); ctx.save(); ctx.font = f(px);
    const plain = toks.map((w) => w.replace(/\*/g, '')), sp = ctx.measureText(' ').width;
    const tw = plain.reduce((a, w) => a + ctx.measureText(w).width, 0) + sp * (toks.length - 1);
    let x = 540 - tw / 2; const y = y0 + j * px * 1.12;
    const k = first ? 1 : eo(seg(t, T0 + 0.2 + j * 0.15, T0 + 0.5 + j * 0.15));
    toks.forEach((w, q) => {
      const st = w.startsWith('*'); if (st) star = true; const em = star; if (w.endsWith('*') || w.endsWith('*,') || w.endsWith('*.')) star = false;
      const p = plain[q], ww = ctx.measureText(p).width;
      if (em) {
        const tk = first ? 1 : eo(seg(t, textTime(i, p, T0 + 0.6) - 0.05, textTime(i, p, T0 + 0.6) + 0.2));
        ctx.globalAlpha = k; ctx.fillStyle = C.acc; ctx.fillRect(x - 8, y - px * 0.52, (ww + 16) * tk, px * 1.0);
        ctx.fillStyle = tk > 0.5 ? C.ink : C.acc;
      } else { ctx.globalAlpha = k; ctx.fillStyle = C.paper; }
      ctx.textBaseline = 'middle'; ctx.textAlign = 'left'; ctx.fillText(p, x, y + (1 - k) * 30); x += ww + sp;
    });
    ctx.restore();
  });
};
SC.cta = (d, t, i, T0, first) => {
  const tAb = textTime(i, 'abone', T0 + 1.2);
  eyebrow('SIRADAKİ BÜLTEN', 60, 330, t, first ? 0 : T0 + 0.15);
  const l1 = UP(d.l1 || ''), l2 = UP(d.l2 || '');
  const k1 = first ? 1 : eo(seg(t, T0 + 0.2, T0 + 0.5)), k2 = first ? 1 : eo(seg(t, T0 + 0.4, T0 + 0.7));
  ctx.save(); ctx.globalAlpha = k1; txt(l1, 60, 450, fitPx(l1, 960, 130), C.paper); ctx.restore();
  ctx.save(); ctx.globalAlpha = k2; txt(l2, 60, 590, fitPx(l2, 960, 130), C.acc); ctx.restore();
  const k = first ? 1 : eo(seg(t, T0 + 0.3, T0 + 0.7));
  ctx.save(); ctx.globalAlpha = k; plate(540, lerp(1150, 900, k), 0.85); ctx.restore();
  const kb = first ? 1 : seg(t, tAb - 0.1, tAb + 0.06), s = lerp(1.9, 1, eo(kb));
  if (first || t > tAb - 0.1) { ctx.save(); ctx.translate(540, 1110); ctx.rotate(-0.04); ctx.scale(s, s); ctx.globalAlpha = clamp(kb * 2);
    ctx.fillStyle = C.red; rr(-230, -64, 460, 128, 10); ctx.fill(); txt('ABONE OL', 0, 6, 88, C.paper, 'center'); ctx.restore(); }
  if (d.sub && (first || t > tAb + 0.3)) { const sub = UP(d.sub); ctx.save(); ctx.globalAlpha = first ? 1 : eo(seg(t, tAb + 0.3, tAb + 0.6));
    txt(sub, 540, 1240, fitPx(sub, 960, 32, 'Mono', 600, 18, 3), C.gold, 'center', 'Mono', 600, 3); ctx.restore(); }
};

function picture(i, t) {
  const sc = GS[i], first = i === 0, T0 = first ? 0 : CUT[i] + 0.16;
  bg(t, i + 1);
  let tl = 1;
  if (sc.type !== 'cta') {
    eyebrow(UP(sc.head ? GD.eyebrow : ''), 60, GTOP, t, first ? 0 : T0);
    tl = title(sc.head || '', 490, t, first ? 0 : T0 + 0.05) || 1;
  }
  (SC[sc.type] || SC.icon_text)(sc.data || {}, t, i, T0, first, tl);
  if (META.ornek && NUMERIC.has(sc.type)) cornerTag('ÖRNEK HESAP', t, first ? 0 : T0);
  if (sc.type !== 'cta') strap(t, i);
  plate(900, 120, 0.3);   // köşe logosu (0. karede de var)
}

function render(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1;
  if (!N) { bg(t, 1); caption(t); return; }
  let i = 0; for (let k = 1; k < N; k++) if (t >= CUT[k] - 0.15) i = k;
  const T = CUT[i], inWipe = i > 0 && t < T + 0.15;
  if (inWipe) bandWipe(t, T, () => picture(i - 1, t), () => picture(i, t)); else picture(i, t);
  caption(t);
}
window.render = render;
window.renderFrame = (fr) => { render(fr / FPS); return cv.toDataURL('image/jpeg', 0.92).split(',')[1]; };
(async () => {
  for (const s of [f(80), f(40, 'Bar', 600), f(30, 'Mono', 500), f(30, 'Mono', 600)]) await document.fonts.load(s, 'ÇĞİÖŞÜçğıöşü₺%0123456789');
  window.ANIM_READY = true;
})();
