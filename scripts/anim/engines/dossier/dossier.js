// =====================================================================
//  DOSSIER motoru — Lemo-Opuscar "halftone-dossier" stilinden (MIT, LemoLab) uyarlandı.
//  Krem kâğıt + nokta baskı + kalın slab başlık + delil kartları + lastik damga.
//  Girdi: TL = {dur, fps, lines:[{id,t0,t1,cap,words}], data:{eyebrow, scenes:[{type,head,data,line}]}},
//         META = {slug, ornek, fileNo}. Sözleşme: window.ANIM_READY + window.renderFrame(f) → base64 jpeg.
//  Rakamlar yalnız data'dan; biçim tr-TR. Her sahne kendi satırının t0'ında başlar.
// =====================================================================
const W = 1080, H = 1920, FPS = TL.fps || 30, DUR = TL.dur;
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const seg = (t, a, b) => clamp((t - a) / (b - a));
const eio = (t) => { t = clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
const eo = (t) => 1 - Math.pow(1 - clamp(t), 3);
const back = (t, s = 1.8) => { t = clamp(t) - 1; return 1 + t * t * ((s + 1) * t + s); };
function mulberry(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const hash = (n) => { n = Math.sin(n * 127.1 + 311.7) * 43758.5453; return n - Math.floor(n); };

const cv = document.getElementById('c'); cv.width = W; cv.height = H;
const MAIN = cv.getContext('2d');
const buf = document.createElement('canvas'); buf.width = W; buf.height = H; const BUF = buf.getContext('2d');
let ctx = BUF;
const C = { paper: '#F1E7D0', ink: '#1C2240', cob: '#2F5BCB', yel: '#F4C430', red: '#D7332A', soft: '#5A5F78' };
const TINTS = ['#C9D4F2', '#E5CFA3', '#CFE0C8', '#F3C9C0', '#DCD3EE', '#F2DDA8'];
const SHADOWS = [C.red, C.cob, C.red, C.yel, C.cob, C.red];
const WIPES = [C.ink, C.cob, C.yel, C.red];
const UP = (s) => String(s || '').toLocaleUpperCase('tr-TR');

// ---------- zaman çizelgesi ----------
const LINES = TL.lines, LBY = Object.fromEntries(LINES.map((l) => [l.id, l]));
const SCN = (TL.data.scenes || []).map((sc, i) => ({ ...sc, L: LBY[sc.line] || LINES[Math.min(i, LINES.length - 1)] }));
const CUT = SCN.map((sc, i) => (i === 0 ? 0 : sc.L.t0 - 0.16));
const endOf = (i) => (i + 1 < CUT.length ? CUT[i + 1] : DUR);
const capT = (i, x) => Math.min(x, endOf(i) - 0.9);   // vuruş sahne bitmeden görünsün
function toks(l) { return l.cap.split(/\s+/); }
function wtime(l, i) { const ws = toks(l); return l.words && l.words[i] != null ? l.words[i] : l.t0 + (l.t1 - l.t0) * i / ws.length; }
const norm = (w) => w.toLocaleLowerCase('tr-TR').split(/['’]/)[0].replace(/^[^0-9a-zçğıöşü%₺]+|[^0-9a-zçğıöşü%₺]+$/g, '');
const fmtN = (v) => Number(v).toLocaleString('tr-TR', { maximumFractionDigits: 2 });
// sayının söylendiği an (bulunamazsa satırın oranı kadar ilerisi)
function numTime(l, v, frac = 0.4) {
  if (v == null) return l.t0 + (l.t1 - l.t0) * frac;
  const want = fmtN(v), ws = toks(l);
  for (let i = 0; i < ws.length; i++) { const n = norm(ws[i]).replace(/^%/, ''); if (n === want) return wtime(l, i); }
  for (let i = 0; i < ws.length; i++) { if (norm(ws[i]).replace(/^%/, '').startsWith(want)) return wtime(l, i); }
  return l.t0 + (l.t1 - l.t0) * frac;
}
// bir kelimenin (ilk 4 harfi) söylendiği an
function wordTime(l, word, frac) {
  const key = norm(String(word).split(/\s+/)[0]).slice(0, 4), ws = toks(l);
  if (key.length >= 3) for (let i = 0; i < ws.length; i++) if (norm(ws[i]).startsWith(key)) return wtime(l, i);
  return l.t0 + (l.t1 - l.t0) * frac;
}
function valStr(v, unit, suffix) {
  const n = fmtN(v), s = suffix ? ' ' + suffix : '';
  if (unit === '%') return '%' + n + s;
  if (unit === 'x') return n + 'x';
  return n + s + (unit ? ' ' + unit : '');
}

// ---------- kâğıt dokusu (bir kez) ----------
const paperTex = document.createElement('canvas'); paperTex.width = W; paperTex.height = H;
{
  const p = paperTex.getContext('2d'), R = mulberry(7);
  p.fillStyle = '#fff'; p.fillRect(0, 0, W, H);
  const tile = document.createElement('canvas'); tile.width = 36; tile.height = 64;
  const tc = tile.getContext('2d');
  for (let y = 0; y < 64; y++) for (let x = 0; x < 36; x++) { const v = 228 + R() * 27; tc.fillStyle = `rgb(${v},${v - 4},${v - 12})`; tc.fillRect(x, y, 1, 1); }
  p.imageSmoothingEnabled = true; p.globalAlpha = 0.55; p.drawImage(tile, 0, 0, W, H); p.globalAlpha = 1;
  const id = p.getImageData(0, 0, W, H), d = id.data;
  for (let i = 0; i < d.length; i += 4) { const n = (R() - 0.5) * 10; d[i] += n; d[i + 1] += n; d[i + 2] += n - 2; }
  p.putImageData(id, 0, 0);
  const g = p.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.75);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(60,40,10,0.28)');
  p.fillStyle = g; p.fillRect(0, 0, W, H);
  p.fillStyle = 'rgba(80,60,30,0.08)'; p.fillRect(0, H * 0.5 - 2, W, 3);
  p.fillStyle = 'rgba(255,255,255,0.18)'; p.fillRect(0, H * 0.5 + 1, W, 2);
}

// ---------- yardımcılar ----------
const font = (px, fam = 'Slab', wgt = 400) => `${wgt} ${px}px ${fam}`;
function halftone(x0, y0, w, h, step, ang, color, dens, k = 0.68) {
  ctx.save(); ctx.beginPath(); ctx.rect(x0, y0, w, h); ctx.clip();
  ctx.fillStyle = color; ctx.beginPath();
  const ca = Math.cos(ang), sa = Math.sin(ang), cx = x0 + w / 2, cy = y0 + h / 2, R = Math.hypot(w, h) / 2 + step;
  for (let v = -R; v <= R; v += step) for (let u = -R; u <= R; u += step) {
    const x = cx + u * ca - v * sa, y = cy + u * sa + v * ca;
    if (x < x0 - step || x > x0 + w + step || y < y0 - step || y > y0 + h + step) continue;
    const r = clamp(dens(x, y)) * step * k; if (r < 0.6) continue;
    ctx.moveTo(x + r, y); ctx.arc(x, y, r, 0, 6.2832);
  }
  ctx.fill(); ctx.restore();
}
const radial = (cx, cy, r0, r1, a = 1) => (x, y) => a * (1 - clamp((Math.hypot(x - cx, y - cy) - r0) / (r1 - r0)));
const edge = (m, a = 1) => (x, y) => a * (1 - clamp(Math.min(x, y, W - x, H - y) / m));
const flat = (a) => () => a;

function fitPx(str, fam, wgt, maxW, maxPx, minPx = 30) {
  let px = maxPx; ctx.save();
  for (; px > minPx; px -= 4) { ctx.font = font(px, fam, wgt); if (ctx.measureText(str).width <= maxW) break; }
  ctx.restore(); return px;
}
// kelime kaydırma: en çok n satır, yazı boyu küçülerek
function wrapFit(str, fam, wgt, maxW, maxPx, maxLines, minPx = 40) {
  const words = String(str).split(/\s+/).filter(Boolean);
  for (let px = maxPx; px >= minPx; px -= 4) {
    ctx.save(); ctx.font = font(px, fam, wgt);
    const lines = []; let cur = '';
    let ok = true;
    for (const w of words) {
      const nx = cur ? cur + ' ' + w : w;
      if (ctx.measureText(nx.replace(/\*/g, '')).width <= maxW) cur = nx;
      else { if (!cur) { ok = false; break; } lines.push(cur); cur = w; if (ctx.measureText(w.replace(/\*/g, '')).width > maxW) { ok = false; break; } }
    }
    if (cur) lines.push(cur);
    ctx.restore();
    if (ok && lines.length <= maxLines) return { px, lines };
  }
  return { px: minPx, lines: [String(str)] };
}
// kayık baskılı başlık, harf harf zıplayarak
function headline(str, x, y, px, t0, t, o = {}) {
  if (t < t0) return;
  ctx.save(); ctx.font = font(px); ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
  const stag = o.stag ?? Math.min(0.045, 0.6 / Math.max(1, str.length)); let xx = x;
  for (let i = 0; i < str.length; i++) {
    const ch = str[i], w = ctx.measureText(ch).width, k = seg(t, t0 + i * stag, t0 + i * stag + 0.32);
    if (k > 0) {
      const dy = o.fast ? 0 : (1 - back(k, 2.2)) * -70, sq = 1 + (1 - k) * (o.fast ? 0.12 : 0.25);
      ctx.save(); ctx.translate(xx + w / 2, y + dy); ctx.scale(1 / sq, sq);
      ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = o.shadow || C.cob; ctx.fillText(ch, -w / 2 + 7, 7);
      ctx.globalCompositeOperation = 'source-over'; ctx.fillStyle = o.c || C.ink; ctx.fillText(ch, -w / 2, 0);
      ctx.restore();
    }
    xx += w + (o.track || 0);
  }
  ctx.restore();
}
// başlık bloğu: 1-3 satır, alt kenarını döndürür
function headBlock(str, t0, t, o = {}) {
  const { px, lines } = wrapFit(UP(str), 'Slab', 400, 960, o.max || 124, 3, 64);
  let y = 230 + px * 0.82;
  const fast = t0 < 0.3, lag = fast ? 0.08 : 0.22;   // açılış (kanca): başlık ilk yarım saniyede tam okunur
  lines.forEach((ln, i) => { headline(ln, 60, y, px, t0 + i * lag, t, { c: o.c, fast, stag: fast ? 0.012 : undefined, shadow: i === lines.length - 1 ? (o.shadow || C.cob) : C.cob }); y += px * 1.04; });
  return y - px * 1.04 + px * 0.25;
}
const off = document.createElement('canvas'); off.width = W; off.height = H; const oc = off.getContext('2d');
function dotText(str, x, y, px, fill, dots, o = {}) {
  oc.setTransform(1, 0, 0, 1, 0, 0); oc.clearRect(0, 0, W, H);
  oc.font = font(px, o.fam || 'Slab', o.wgt || 400); oc.textAlign = o.align || 'left'; oc.textBaseline = 'alphabetic';
  oc.fillStyle = fill; oc.fillText(str, x, y);
  oc.globalCompositeOperation = 'source-atop'; oc.fillStyle = dots; oc.beginPath();
  const st = o.step || 22, a = 0.26, ca = Math.cos(a), sa = Math.sin(a);
  for (let v = -H; v < H * 1.2; v += st) for (let u = -W; u < W * 1.6; u += st) {
    const X = u * ca - v * sa, Y = u * sa + v * ca; if (X < 0 || X > W || Y < y - px * 1.1 || Y > y + px * 0.3) continue;
    const dd = clamp((Y - (y - px)) / px) * 0.9; const r = dd * st * 0.62; if (r < 0.6) continue;
    oc.moveTo(X + r, Y); oc.arc(X, Y, r, 0, 6.2832);
  }
  oc.fill(); oc.globalCompositeOperation = 'source-over';
  ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.globalAlpha = 0.9; ctx.drawImage(off, 9, 9); ctx.restore();
  ctx.drawImage(off, 0, 0);
}
function rrect(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function monoText(s, x, y, px, c, al = 'left', track = 2) {
  ctx.save(); ctx.font = font(px, 'Mono', 600); ctx.fillStyle = c; ctx.textAlign = al; ctx.textBaseline = 'middle';
  ctx.letterSpacing = track + 'px'; ctx.fillText(s, x, y); ctx.restore();
}
function sans(s, x, y, px, c, al = 'left', wgt = 800) {
  ctx.save(); ctx.font = font(px, 'Sans', wgt); ctx.fillStyle = c; ctx.textAlign = al; ctx.textBaseline = 'middle'; ctx.fillText(s, x, y); ctx.restore();
}
const stampCache = {};
function stampImg(text, color, px = 96) {
  const key = text + color + px; if (stampCache[key]) return stampCache[key];
  const c = document.createElement('canvas'), g = c.getContext('2d'); g.font = font(px, 'Sans', 900);
  const tw = g.measureText(text).width, w = tw + 120, h = px + 90; c.width = w; c.height = h;
  g.strokeStyle = color; g.fillStyle = color; g.lineWidth = 9; g.beginPath(); g.roundRect(8, 8, w - 16, h - 16, 18); g.stroke();
  g.lineWidth = 4; g.beginPath(); g.roundRect(24, 24, w - 48, h - 48, 10); g.stroke();
  g.font = font(px, 'Sans', 900); g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, w / 2, h / 2 + 4);
  g.globalCompositeOperation = 'destination-out'; const R = mulberry(text.length * 31 + px);
  for (let i = 0; i < w * h / 55; i++) { g.globalAlpha = 0.3 + R() * 0.7; g.beginPath(); g.arc(R() * w, R() * h, 0.6 + R() * 2.4, 0, 6.2832); g.fill(); }
  stampCache[key] = c; return c;
}
let DARK = false;
function stamp(text, color, x, y, rot, t0, t, px) {
  if (DARK && color === C.red) color = C.yel;
  if (t < t0) return;
  ctx.save(); ctx.font = font(px, 'Sans', 900); const tw = ctx.measureText(text).width; ctx.restore();
  if (tw + 120 > 980) px = Math.floor(px * 860 / tw);   // ekrana sığsın
  const k = seg(t, t0, t0 + 0.09), s = k < 1 ? lerp(2.6, 1, k * k) : 1 + Math.exp(-(t - t0 - 0.09) * 14) * Math.sin((t - t0) * 40) * 0.05;
  const img = stampImg(text, color, px);
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s); ctx.globalAlpha = 0.93 * clamp(k * 3);
  ctx.globalCompositeOperation = DARK ? 'source-over' : 'multiply'; ctx.drawImage(img, -img.width / 2, -img.height / 2); ctx.restore();
}
const shakeOf = (t, t0, amp) => t < t0 ? 0 : amp * Math.pow(Math.max(0, 1 - (t - t0) / 0.45), 2);
const flashOf = (t, t0, a = 0.5) => t < t0 ? 0 : a * Math.max(0, 1 - (t - t0) / 0.22);
const pop = (t, t0, d = 0.38) => back(seg(t, t0, t0 + d), 2.0);
function card(x, y, w, h, rot, fill, t, seed) {
  const b = Math.floor(t * 10), j = (n) => (hash(seed * 13 + b * 7 + n) - 0.5) * 3;
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot + j(9) * 0.002);
  ctx.fillStyle = 'rgba(28,34,64,0.18)'; ctx.fillRect(-w / 2 + 14, -h / 2 + 16, w, h);
  ctx.fillStyle = fill; ctx.strokeStyle = C.ink; ctx.lineWidth = 6;
  ctx.beginPath(); ctx.moveTo(-w / 2 + j(1), -h / 2 + j(2)); ctx.lineTo(w / 2 + j(3), -h / 2 + j(4)); ctx.lineTo(w / 2 + j(5), h / 2 + j(6)); ctx.lineTo(-w / 2 + j(7), h / 2 + j(8)); ctx.closePath(); ctx.fill(); ctx.stroke();
  return () => ctx.restore();
}
function pin(x, y) { ctx.fillStyle = C.yel; ctx.strokeStyle = C.ink; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(x, y, 16, 0, 6.2832); ctx.fill(); ctx.stroke(); }
function ornekTag(x, y, rot = -0.1) {
  if (!META.ornek) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.fillStyle = C.yel; rrect(-90, -34, 180, 68, 12); ctx.fill();
  sans('örnek', 0, 2, 42, C.ink, 'center', 800); ctx.restore();
}
// mürekkep çizgi ikonları (merkez 0,0; ~±100 birim)
function icon(name, x, y, s = 1, col = C.ink) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 9; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  const box = (x0, y0, w, h, r = 10) => { ctx.beginPath(); ctx.roundRect(x0, y0, w, h, r); ctx.stroke(); };
  switch (name) {
    case 'calendar': box(-90, -80, 180, 170, 14); ctx.fillStyle = C.red; ctx.fillRect(-86, -76, 172, 44); ctx.fillStyle = col;
      for (let r = 0; r < 3; r++) for (let c = 0; c < 4; c++) ctx.fillRect(-66 + c * 38, -10 + r * 32, 20, 18);
      ctx.beginPath(); ctx.moveTo(-50, -100); ctx.lineTo(-50, -62); ctx.moveTo(50, -100); ctx.lineTo(50, -62); ctx.stroke(); break;
    case 'chart': ctx.beginPath(); ctx.moveTo(-90, -90); ctx.lineTo(-90, 90); ctx.lineTo(95, 90); ctx.stroke();
      ctx.strokeStyle = C.red; ctx.lineWidth = 12; ctx.beginPath(); ctx.moveTo(-70, 60); ctx.lineTo(-20, 10); ctx.lineTo(20, 35); ctx.lineTo(85, -60); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(50, -62); ctx.lineTo(88, -64); ctx.lineTo(84, -26); ctx.stroke(); break;
    case 'percent': ctx.font = font(220, 'Slab'); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = C.red; ctx.fillText('%', 0, 10); break;
    case 'house': ctx.beginPath(); ctx.moveTo(-100, -10); ctx.lineTo(0, -100); ctx.lineTo(100, -10); ctx.stroke(); box(-72, -20, 144, 112, 6);
      ctx.fillStyle = C.red; ctx.fillRect(-20, 30, 40, 58); break;
    case 'car': box(-100, -10, 200, 70, 18); ctx.beginPath(); ctx.moveTo(-62, -10); ctx.lineTo(-38, -62); ctx.lineTo(40, -62); ctx.lineTo(66, -10); ctx.stroke();
      ctx.fillStyle = C.ink; [-55, 55].forEach((cx) => { ctx.beginPath(); ctx.arc(cx, 68, 24, 0, 6.2832); ctx.fill(); }); break;
    case 'bank': ctx.beginPath(); ctx.moveTo(-105, -40); ctx.lineTo(0, -100); ctx.lineTo(105, -40); ctx.closePath(); ctx.stroke();
      for (let i = 0; i < 4; i++) ctx.fillRect(-78 + i * 48, -26, 18, 96); ctx.fillRect(-105, 78, 210, 14); break;
    case 'card': box(-110, -70, 220, 140, 16); ctx.fillRect(-106, -36, 212, 26); ctx.fillStyle = C.yel; ctx.fillRect(-84, 14, 44, 32); ctx.fillStyle = col; ctx.fillRect(10, 30, 76, 10); break;
    case 'piggy': ctx.beginPath(); ctx.ellipse(0, 10, 100, 72, 0, 0, 6.2832); ctx.stroke(); ctx.fillRect(-20, -66, 44, 10);
      ctx.beginPath(); ctx.arc(46, -8, 8, 0, 6.2832); ctx.fill(); ctx.fillRect(-60, 72, 18, 30); ctx.fillRect(40, 72, 18, 30); break;
    case 'gold': ctx.fillStyle = C.yel; [[-60, 20], [60, 20], [0, -50]].forEach(([cx, cy]) => { ctx.beginPath(); ctx.moveTo(cx - 70, cy + 34); ctx.lineTo(cx - 44, cy - 34); ctx.lineTo(cx + 44, cy - 34); ctx.lineTo(cx + 70, cy + 34); ctx.closePath(); ctx.fill(); ctx.stroke(); }); break;
    default:   // coins / cash / bilinmeyen → ₺ jetonu
      ctx.fillStyle = C.yel; ctx.beginPath(); ctx.arc(0, 0, 96, 0, 6.2832); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.arc(0, 0, 70, 0, 6.2832); ctx.lineWidth = 5; ctx.stroke();
      ctx.font = font(110, 'Sans', 900); ctx.fillStyle = C.ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('₺', 0, 6);
  }
  ctx.restore();
}

// ---------- HUD + altyazı ----------
let CHAP = [];
{ let d = 0; SCN.forEach((sc, i) => { CHAP[i] = sc.type === 'cta' ? 'SON' : sc.type === 'steps' ? 'KARAR' : 'DELİL ' + String(++d).padStart(2, '0'); }); }
function hud(t, dark, chap) {
  const ink = dark ? C.paper : C.ink;
  ctx.save(); ctx.lineWidth = 4; ctx.strokeStyle = ink; rrect(56, 70, 380, 58, 10); ctx.stroke();
  monoText('DOSYA ' + META.fileNo, 76, 100, 30, ink);
  ctx.fillStyle = C.yel; rrect(452, 70, 210, 58, 10); ctx.fill();
  monoText(chap, 470, 100, 28, C.ink);
  const on = Math.floor(t * 1.6) % 2 === 0;
  ctx.fillStyle = C.red; if (on) { ctx.beginPath(); ctx.arc(796, 99, 11, 0, 6.2832); ctx.fill(); }
  monoText('KAYIT', 816, 100, 28, ink); ctx.restore();
}
const CHUNKS = [];
for (const l of LINES) {
  const ws = toks(l), ts = ws.map((_, i) => wtime(l, i));
  let cur = [], t0 = ts[0];
  const flush = (tEnd) => { if (cur.length) CHUNKS.push({ t0, t1: tEnd, words: cur }); cur = []; };
  ws.forEach((w, i) => {
    const len = cur.map((x) => x.w).join(' ').length + w.length + 1;
    if (cur.length && (len > 26 || /[;:,.]$/.test(cur[cur.length - 1].w))) { flush(ts[i]); t0 = ts[i]; }
    cur.push({ w, t: ts[i] });
  });
  flush(l.t1 + 0.25);
}
const STARS = new Set();
SCN.forEach((sc) => { if (sc.type === 'icon_text') (String(sc.data.text).match(/\*([^*]+)\*/g) || []).forEach((m) => m.replace(/\*/g, '').split(/\s+/).forEach((w) => STARS.add(norm(w)))); });
const KEY = /\d|₺|%|ceza|zam|indirim|abone|fark|tarife|faiz|enflasyon|kira|maaş|vergi|oran|harç|tasarruf|yüzde|lira/i;
const isKey = (w) => KEY.test(w) || STARS.has(norm(w));
function chunkAt(t) { let c = null; for (const k of CHUNKS) if (t >= k.t0 - 0.05 && t < k.t1) c = k; return c; }
function caption(t, dark) {
  const ch = chunkAt(t); if (!ch) return;
  const k = pop(t, ch.t0, 0.25), y = 1500;
  ctx.save(); let px = 62; ctx.font = font(px, 'Sans', 900);
  const words = ch.words.map((o) => o.w.replace(/[;:]$/, ''));
  let sp = ctx.measureText(' ').width, ws = words.map((w) => ctx.measureText(w).width), tw = ws.reduce((a, b) => a + b, 0) + sp * (words.length - 1);
  if (tw > 900) { px = Math.floor(px * 900 / tw); ctx.font = font(px, 'Sans', 900); sp = ctx.measureText(' ').width; ws = words.map((w) => ctx.measureText(w).width); tw = ws.reduce((a, b) => a + b, 0) + sp * (words.length - 1); }
  const bw = tw + 90, bh = 112, x = 540 - bw / 2;
  ctx.translate(540, y); ctx.scale(lerp(0.6, 1, k), lerp(0.6, 1, k)); ctx.translate(-540, -y);
  ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = C.cob; rrect(x + 10, y - bh / 2 + 10, bw, bh, 56); ctx.fill();
  ctx.globalCompositeOperation = 'source-over'; ctx.fillStyle = dark ? C.paper : C.ink; rrect(x, y - bh / 2, bw, bh, 56); ctx.fill();
  let xx = 540 - tw / 2; ctx.textBaseline = 'middle';
  words.forEach((w, i) => {
    const said = t >= ch.words[i].t - 0.02;
    ctx.fillStyle = isKey(w) ? (dark ? C.red : C.yel) : (dark ? C.ink : C.paper);
    ctx.globalAlpha = said ? 1 : 0.45; ctx.fillText(w, xx, y + 4); xx += ws[i] + sp;
  });
  ctx.restore();
}

// ---------- sahne şablonları ----------
const YB = 1360;   // içerik alt sınırı (altyazı bandı 1444'te başlar)
function bg(i, dark) {
  if (dark) { ctx.fillStyle = C.ink; ctx.fillRect(0, 0, W, H);
    halftone(0, 0, W, H, 24, 0.45, '#2E3970', radial(540, 860, 120, 760, 1.0)); halftone(0, 0, W, H, 22, 1.2, '#3A2F60', edge(260, 0.8)); return; }
  const tint = TINTS[i % TINTS.length], ang = [0.3, 1.0, 0.6, 0.2, 0.8, 1.2][i % 6];
  halftone(0, 0, W, H, 22, ang, tint, i % 2 ? radial(540, 900, 200, 900, 0.7) : edge(260, 0.9));
}

function sBigNumber(sc, i, t, dark) {
  const l = sc.L, d = sc.data, T0 = CUT[i], ink = dark ? C.paper : C.ink;
  const yH = headBlock(sc.head, i ? T0 + 0.2 : 0.05, t, { c: ink, shadow: SHADOWS[i % 6] });
  const tV = numTime(l, d.value, 0.45);
  const cy = (yH + 40 + YB) / 2, ch = Math.min(640, YB - yH - 60);
  const k = pop(t, T0 + 0.1, 0.45), y = lerp(cy + 900, cy, k);
  const done = card(540, y, 880, ch, -0.035, C.paper, t, 3 + i);
  ctx.fillStyle = C.red; ctx.fillRect(-440, -ch / 2, 880, 92);
  sans(UP(TL.data.eyebrow || 'KAYIT'), 0, -ch / 2 + 48, fitPx(UP(TL.data.eyebrow || 'KAYIT'), 'Sans', 900, 780, 46), C.paper, 'center', 900);
  monoText('KAYIT NO  ' + META.fileNo, -380, -ch / 2 + 140, 26, C.soft);
  for (let r = 0; r < 2; r++) { ctx.fillStyle = 'rgba(28,34,64,0.22)'; ctx.fillRect(-380, -ch / 2 + 190 + r * 44, 420 + (r % 2) * 160, 14); }
  if (d.label) { const lp = fitPx(d.label, 'Sans', 800, 780, 44, 26); sans(d.label, -380, ch / 2 - 70, lp, C.soft, 'left', 800); }
  done();
  let shake = 0;
  if (t <= tV - 0.05 && t > T0 + 0.4) {   // rakam söylenene kadar: soru işareti nabzı
    const pz = 1 + 0.06 * Math.sin((t - T0) * 7);
    ctx.save(); ctx.translate(540, y + 60); ctx.scale(pz, pz); ctx.font = font(Math.min(200, ch * 0.34)); ctx.fillStyle = 'rgba(28,34,64,0.28)';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('?', 0, 0); ctx.restore();
  }
  if (t > tV - 0.05) {
    const s = valStr(d.value, d.unit, d.suffix), px = fitPx(s, 'Slab', 400, 800, Math.min(230, ch * 0.36), 70);
    const kk = seg(t, tV - 0.05, tV + 0.12), sc2 = lerp(1.9, 1, eo(kk)), ny = y + 40 + px * 0.35;
    ctx.save(); ctx.translate(540, ny - px * 0.35); ctx.scale(sc2, sc2); ctx.translate(-540, -(ny - px * 0.35));
    halftone(0, ny - px * 1.1, W, px * 1.4, 20, 0.8, 'rgba(244,196,48,0.9)', radial(540, ny - px * 0.4, 40, 460, 1));
    dotText(s, 540, ny, px, C.red, C.ink, { align: 'center', step: 20 });
    ctx.restore();
    shake = shakeOf(t, tV + 0.05, 16);
  }
  if (t > tV + 0.3) ornekTag(820, y + ch / 2 - 60);
  return { shake, flash: flashOf(t, tV, 0.35) };
}

function sLayers(sc, i, t, dark) {
  const l = sc.L, d = sc.data, T0 = CUT[i], ink = dark ? C.paper : C.ink, unit = d.unit || '';
  const yH = headBlock(sc.head, i ? T0 + 0.2 : 0.05, t, { c: ink, shadow: SHADOWS[i % 6] });
  const parts = (d.parts || []).slice(0, 5), n = parts.length;
  const rowH = Math.min(120, (YB - yH - 260) / (n + 1.4)), chH = rowH * (n + 1.4) + 120;
  const cy = Math.min((yH + 40 + YB) / 2, yH + 40 + chH / 2);
  const k = pop(t, T0 + 0.1, 0.42);
  const done = card(lerp(-700, 540, k), cy, 920, chH, 0.015, '#FFF6D8', t, 11 + i);
  monoText('DÖKÜM', -400, -chH / 2 + 50, 26, C.soft);
  let shake = 0, flash = 0; const tps = [];
  parts.forEach((p, j) => {
    const tl = T0 + 0.5 + j * 0.35, tp = Math.max(tl, numTime(l, p.value, 0.25 + 0.5 * j / Math.max(1, n))); tps.push(tp);
    if (t < tl - 0.1) return;
    const kk = pop(t, tl - 0.1, 0.3), kv = pop(t, tp - 0.08, 0.3), y = -chH / 2 + 110 + j * rowH + rowH / 2;
    ctx.save(); ctx.globalAlpha = clamp(kk * 1.5); ctx.translate((1 - kk) * 80, 0);
    if (p.hl && t > tp) { ctx.fillStyle = C.yel; ctx.fillRect(-420, y - rowH * 0.42, 840 * eo(seg(t, tp, tp + 0.3)), rowH * 0.84); }
    const lp = fitPx(p.label, 'Sans', 800, 470, 54, 30);
    sans(p.label, -400, y, lp, C.ink, 'left', 800);
    const vs = valStr(p.value, unit), vp = fitPx(vs, 'Sans', 900, 330, 62, 34);
    if (t >= tp - 0.08) { ctx.save(); ctx.globalAlpha = clamp(kv * 1.5); ctx.translate(400, y); ctx.scale(lerp(1.6, 1, clamp(kv)), lerp(1.6, 1, clamp(kv))); sans(vs, 0, 0, vp, p.hl ? C.red : C.ink, 'right', 900); ctx.restore(); }
    else sans('…', 400, y, vp, 'rgba(28,34,64,0.3)', 'right', 900);
    ctx.restore();
  });
  const tT = Math.max((tps[tps.length - 1] || T0) + 0.5, numTime(l, d.total && d.total.value, 0.8));
  if (d.total && t > tT - 0.1) {
    const y = -chH / 2 + 110 + n * rowH + rowH * 0.7;
    ctx.fillStyle = C.ink; ctx.fillRect(-420, y - rowH * 0.6, 840 * eo(seg(t, tT - 0.1, tT + 0.2)), 6);
    const kk = pop(t, tT, 0.3);
    ctx.save(); ctx.globalAlpha = clamp(kk * 1.5);
    sans(UP(d.total.label), -400, y, fitPx(UP(d.total.label), 'Sans', 900, 440, 54, 30), C.ink, 'left', 900);
    const vs = valStr(d.total.value, unit); sans(vs, 400, y, fitPx(vs, 'Sans', 900, 380, 76, 36), C.red, 'right', 900);
    ctx.restore(); flash = flashOf(t, tT, 0.25);
  }
  done();
  if (t > T0 + 0.6) ornekTag(860, cy - chH / 2 + 10, 0.08);
  const hl = parts.find((p) => p.hl);
  if (hl && d.total) { const ts = capT(i, tT + 0.5); stamp(valStr(hl.value, unit) + ' ' + UP(hl.label).slice(0, 14), C.red, 560, Math.min(YB - 90, cy + chH / 2 + 80), -0.1, ts, t, 72); shake = shakeOf(t, ts, 18); }
  return { shake, flash };
}

function sBars(sc, i, t, dark) {
  const l = sc.L, d = sc.data, T0 = CUT[i], ink = dark ? C.paper : C.ink;
  const yH = headBlock(sc.head, i ? T0 + 0.2 : 0.05, t, { c: ink, shadow: SHADOWS[i % 6] });
  const items = (d.items || []).slice(0, 6), n = items.length, max = Math.max(...items.map((x) => +x.value || 0), 1);
  const base = YB - 70, top = yH + 150, gap = 40, bw = Math.min(230, (920 - gap * (n - 1)) / n), x0 = 540 - (bw * n + gap * (n - 1)) / 2;
  ctx.fillStyle = ink; ctx.fillRect(60, base, 960 * eo(seg(t, T0 + 0.1, T0 + 0.5)), 6);
  let flash = 0, shake = 0;
  items.forEach((it, j) => {
    const tb = Math.max(T0 + 0.4 + j * 0.3, numTime(l, it.value, 0.25 + 0.55 * j / Math.max(1, n - 1)));
    const k = eo(seg(t, tb - 0.1, tb + 0.45)), hgt = (base - top) * (it.value / max) * k, x = x0 + j * (bw + gap), hl = j === d.hl;
    if (t > tb - 0.1) {
      ctx.fillStyle = hl ? C.red : C.cob; ctx.strokeStyle = C.ink; ctx.lineWidth = 5;
      ctx.fillRect(x, base - hgt, bw, hgt); ctx.strokeRect(x, base - hgt, bw, hgt);
      halftone(x, base - hgt, bw, hgt, 16, 0.7, hl ? '#8E1C16' : '#1C2F7A', (xx, yy) => 0.25 + 0.6 * (yy - (base - hgt)) / Math.max(1, hgt));
      const vs = valStr(it.value, d.unit, d.suffix), vp = fitPx(vs, 'Sans', 900, bw + gap - 6, 60, 26);
      ctx.save(); ctx.globalAlpha = clamp(k * 2); sans(vs, x + bw / 2, base - hgt - vp * 0.75, vp, hl ? C.red : ink, 'center', 900); ctx.restore();
      monoText(UP(it.label), x + bw / 2, base + 44, fitPx(UP(it.label), 'Mono', 600, bw + gap - 4, 40, 20), ink, 'center', 1);
      if (hl) { flash = Math.max(flash, flashOf(t, tb + 0.35, 0.3)); shake = Math.max(shake, shakeOf(t, tb + 0.35, 12)); }
    }
  });
  if (t > T0 + 0.6) ornekTag(900, top - 60, 0.08);
  return { shake, flash };
}

function cmpCard(x, y, w, h, rot, lab, val, col, t, t0, seed) {
  if (t < t0) return null;
  const k = pop(t, t0, 0.42), yy = lerp(y + 900, y, k);
  const done = card(x, yy, w, h, rot, C.paper, t, seed);
  ctx.fillStyle = col; ctx.fillRect(-w / 2, -h / 2, w, 110);
  const lp = fitPx(UP(lab), 'Sans', 900, w - 40, 50, 24); sans(UP(lab), 0, -h / 2 + 56, lp, C.paper, 'center', 900);
  const vp = fitPx(val, 'Slab', 400, w - 50, 150, 50);
  ctx.font = font(vp); ctx.fillStyle = col === C.red ? C.red : C.ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(val, 0, 40);
  ctx.fillStyle = 'rgba(28,34,64,0.15)'; ctx.fillRect(-w / 2 + 30, h / 2 - 60, w - 60, 4);
  done(); pin(x + w / 2 - 50, yy - h / 2 - 20);
  return [x + w / 2 - 50, yy - h / 2 - 20];
}
function sCompare(sc, i, t, dark) {
  const l = sc.L, d = sc.data, T0 = CUT[i], ink = dark ? C.paper : C.ink;
  const yH = headBlock(sc.head, i ? T0 + 0.2 : 0.05, t, { c: ink, shadow: SHADOWS[i % 6] });
  const tA = Math.max(T0 + 0.3, numTime(l, d.a.value, 0.3)), tB = Math.max(tA + 0.4, numTime(l, d.b.value, 0.6));
  const ch = Math.min(500, YB - yH - 280), cy = yH + 60 + ch / 2;
  const pa = cmpCard(285, cy, 420, ch, -0.05, d.a.label, valStr(d.a.value, d.unit), C.ink, t, tA - 0.1, 21 + i);
  const pb = cmpCard(800, cy + 30, 420, ch, 0.05, d.b.label, valStr(d.b.value, d.unit), C.red, t, tB - 0.1, 22 + i);
  if (pa && pb && t > tB + 0.25) {
    const k = eo(seg(t, tB + 0.25, tB + 0.7));
    ctx.save(); ctx.strokeStyle = C.red; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(pa[0], pa[1]);
    const ex = lerp(pa[0], pb[0], k), ey = lerp(pa[1], pb[1], k); ctx.quadraticCurveTo((pa[0] + ex) / 2, pa[1] + 120, ex, ey); ctx.stroke(); ctx.restore();
  }
  let shake = 0, flash = 0;
  if (d.note) {
    const m = String(d.note).match(/[\d.,]+/), tn = Math.max(tB + 0.6, m ? numTime(l, m[0].replace(/\./g, '').replace(',', '.'), 0.85) : l.t0 + (l.t1 - l.t0) * 0.85);
    const tn2 = capT(i, tn);
    stamp(UP(d.note), C.red, 545, Math.min(YB - 100, cy + ch / 2 + 150), -0.12, tn2, t, 100);
    shake = shakeOf(t, tn2, 24); flash = flashOf(t, tn2, 0.4);
  }
  if (t > tB + 0.3) ornekTag(700, cy + 30 - ch / 2 - 62, 0.06);
  return { shake, flash };
}

function sSteps(sc, i, t, dark) {
  const l = sc.L, d = sc.data, T0 = CUT[i], ink = dark ? C.paper : C.ink;
  const yH = headBlock(sc.head, i ? T0 + 0.15 : 0.05, t, { c: ink, shadow: SHADOWS[i % 6], max: 140 });
  const items = (d.items || []).slice(0, 4), n = items.length;
  const rh = Math.min(200, (YB - yH - 80) / n - 30), y0 = yH + 60 + rh / 2;
  let last = T0;
  items.forEach((it, j) => {
    const ta = Math.max(last + 0.45, T0 + 0.4, wordTime(l, it, 0.15 + 0.7 * j / n)); last = ta;
    if (t < ta - 0.2) return;
    const k = pop(t, ta - 0.2), y = y0 + j * (rh + 30);
    const done = card(lerp(-600, 540, k), y, 920, rh, j % 2 ? 0.015 : -0.015, '#FFF6D8', t, 31 + j + i * 5);
    const bs = Math.min(100, rh - 50);
    ctx.strokeStyle = C.ink; ctx.lineWidth = 6; ctx.strokeRect(-410, -bs / 2, bs, bs);
    const tc = ta + 0.35;
    if (t > tc) { const kc = eo(seg(t, tc, tc + 0.25)), s = bs / 100; ctx.save(); ctx.translate(-410, -bs / 2); ctx.scale(s, s);
      ctx.strokeStyle = C.red; ctx.lineWidth = 14; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(18, 50); ctx.lineTo(18 + 28 * clamp(kc * 2), 50 + 30 * clamp(kc * 2)); if (kc > 0.5) ctx.lineTo(46 + 70 * (kc - 0.5) * 2, 80 - 90 * (kc - 0.5) * 2); ctx.stroke(); ctx.restore(); }
    const tp = fitPx(it, 'Sans', 900, 900 - bs - 120, 66, 34);
    sans(it, -410 + bs + 40, 4, tp, C.ink, 'left', 900);
    done();
  });
  return { shake: 0, flash: 0 };
}

function sIconText(sc, i, t, dark) {
  const l = sc.L, d = sc.data, T0 = CUT[i], ink = dark ? C.paper : C.ink;
  const yH = headBlock(sc.head, i ? T0 + 0.2 : 0.05, t, { c: ink, shadow: SHADOWS[i % 6] });
  const k = pop(t, T0 + 0.25, 0.45), cs = 300, cyI = yH + 70 + cs / 2;
  const done = card(lerp(1500, 540, k), cyI, cs, cs, 0.04, C.paper, t, 51 + i);
  icon(d.icon, 0, 0, 1.15); done(); pin(540 + cs / 2 - 40, cyI - cs / 2 - 14);
  const raw = String(d.text || ''), { px, lines } = wrapFit(raw, 'Sans', 900, 940, 96, 4, 52);
  let y = cyI + cs / 2 + 60 + px * 0.6;
  ctx.save(); ctx.font = font(px, 'Sans', 900); ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
  const sp = ctx.measureText(' ').width;
  let idx = 0;
  lines.forEach((ln, li) => {
    const ws = ln.split(/\s+/), clean = ws.map((w) => w.replace(/\*/g, '')), wid = clean.map((w) => ctx.measureText(w).width);
    const tw = wid.reduce((a, b) => a + b, 0) + sp * (ws.length - 1); let x = 540 - tw / 2;
    let starOpen = false;
    ws.forEach((w, wi) => {
      const st = starOpen || w.startsWith('*'); if (w.startsWith('*')) starOpen = true; if (w.endsWith('*')) starOpen = false;
      const ta = T0 + 0.5 + idx * 0.07, kk = pop(t, ta, 0.3); idx++;
      if (t >= ta) {
        if (st) { const tsw = wordTime(l, clean[wi], 0.5), kh = eo(seg(t, tsw - 0.1, tsw + 0.25));
          if (kh > 0) { ctx.fillStyle = C.yel; ctx.fillRect(x - 10, y - px * 0.5, (wid[wi] + 20) * kh, px * 0.98); } }
        ctx.save(); ctx.globalAlpha = clamp(kk * 1.4); ctx.translate(0, (1 - kk) * 30);
        ctx.fillStyle = st ? C.red : ink; ctx.fillText(clean[wi], x, y + 4); ctx.restore();
      }
      x += wid[wi] + sp;
    });
    y += px * 1.12;
  });
  ctx.restore();
  return { shake: 0, flash: 0 };
}

function sCta(sc, i, t, dark) {
  const l = sc.L, d = sc.data, T0 = CUT[i], ink = dark ? C.paper : C.ink;
  const l1 = UP(d.l1 || 'SIRADAKİ'), l2 = UP(d.l2 || 'DOSYALAR');
  const px = Math.min(fitPx(l1, 'Slab', 400, 960, 120, 60), fitPx(l2, 'Slab', 400, 960, 120, 60));
  headline(l1, 60, 230 + px * 0.82, px, T0 + 0.2, t, { c: ink });
  headline(l2, 60, 230 + px * 1.86, px, T0 + 0.45, t, { c: ink, shadow: C.red });
  const yH = 230 + px * 2.1;
  const tAb = capT(i, wordTime(l, 'abone', 0.55));
  for (let j = 0; j < 3; j++) {
    const t0 = T0 + 0.5 + j * 0.35; if (t < t0) continue;
    const k = pop(t, t0), y = yH + 150 + j * 150;
    const done = card(lerp(1400, 540 + (j - 1) * 24, k), y, 860, 200, (j - 1) * 0.03, j % 2 ? '#E9D9B0' : '#F2E2BA', t, 41 + j);
    ctx.fillStyle = '#E9D9B0'; ctx.fillRect(-430, -130, 300, 56); ctx.strokeStyle = C.ink; ctx.lineWidth = 5; ctx.strokeRect(-430, -130, 300, 56);
    monoText('DOSYA ' + META.nextNo(j + 1), -410, -102, 24, C.ink);
    const rk = seg(t, t0 + 0.5, t0 + 0.8);
    ctx.fillStyle = C.ink; ctx.fillRect(-380, -20, 520 * eo(rk), 50); ctx.fillRect(-380, 46, 340 * eo(rk), 28);
    done();
  }
  const sy = Math.min(YB - 90, yH + 620);
  stamp('ABONE OL', C.red, 540, sy, -0.08, tAb, t, 120);
  if (d.sub && t > tAb + 0.4) { const k = pop(t, tAb + 0.4); ctx.save(); ctx.globalAlpha = clamp(k);
    const s = UP(d.sub); monoText(s, 540, Math.min(YB, sy + 130), fitPx(s, 'Mono', 600, 960, 30, 18), ink, 'center', 1); ctx.restore(); }
  return { shake: shakeOf(t, tAb, 22), flash: flashOf(t, tAb, 0.35) };
}
const TPL = { big_number: sBigNumber, layers: sLayers, bars: sBars, compare: sCompare, steps: sSteps, icon_text: sIconText, cta: sCta };

function wipe(t) {
  for (let i = 1; i < CUT.length; i++) {
    const T = CUT[i], a = T - 0.24, b = T + 0.24; if (t < a || t > b) continue;
    const step = 120, R = step * 0.75; ctx.fillStyle = WIPES[(i - 1) % WIPES.length]; ctx.beginPath();
    for (let y = 0; y <= H + step; y += step) for (let x = 0; x <= W + step; x += step) {
      const d = (x / W + y / H) / 2 * 0.12, p = (t - a - d) / (0.48 - 0.12);
      const r = R * clamp(p < 0.5 ? p * 2 : (1 - p) * 2) * 1.05; if (r < 1) continue;
      ctx.moveTo(x + r, y); ctx.arc(x, y, r, 0, 6.2832);
    }
    ctx.fill();
  }
}
function grain(t) {   // 3 karede bir değişir (dosya boyutu)
  const R = mulberry(Math.floor(t * FPS / 3) + 99);
  ctx.save();
  for (let i = 0; i < 220; i++) { ctx.fillStyle = R() < 0.75 ? 'rgba(250,244,228,0.6)' : 'rgba(28,34,64,0.35)'; ctx.fillRect(R() * W, R() * H, 1 + R() * 2.2, 1 + R() * 2.2); }
  ctx.restore();
}

function render(t, poster = false) {
  let i = 0; for (let k = 0; k < CUT.length; k++) if (t >= CUT[k]) i = k;
  const sc = SCN[i], dark = i === 0 && sc.type !== 'cta'; DARK = dark;
  ctx = BUF; ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = C.paper; ctx.fillRect(0, 0, W, H);
  bg(i, dark);
  const r = (TPL[sc.type] || sIconText)(sc, i, t, dark) || {};
  const end = i + 1 < CUT.length ? CUT[i + 1] : DUR;
  const zoom = lerp(1, 1.045, eio(seg(t, CUT[i], end)));
  ctx = MAIN; ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = dark ? C.ink : C.paper; ctx.fillRect(0, 0, W, H);
  const f = Math.floor(t * 60), sh = r.shake || 0, sx = (hash(f) - 0.5) * 2 * sh, sy = (hash(f + 7) - 0.5) * 2 * sh;
  ctx.save(); ctx.translate(540 + sx, 960 + sy); ctx.scale(zoom, zoom); ctx.translate(-540, -960);
  ctx.drawImage(buf, 0, 0); ctx.restore();
  hud(t, dark, CHAP[i]);
  if (!poster) caption(t, dark);
  ctx.globalCompositeOperation = 'multiply'; ctx.drawImage(paperTex, 0, 0); ctx.globalCompositeOperation = 'source-over';
  grain(t);
  if (r.flash > 0 && !poster) { ctx.fillStyle = `rgba(255,252,240,${Math.min(0.5, r.flash)})`; ctx.fillRect(0, 0, W, H); }
  wipe(t);
}
window.renderAt = render;
// kare 0 = kapak (yükleyici frame-0'ı Shorts kapağı yapar): kanca sahnesinin oturmuş hali
const POSTER_T = Math.max(0.5, endOf(0) - 0.45);
window.renderFrame = (f) => { render(f === 0 ? POSTER_T : f / FPS, f === 0); return cv.toDataURL('image/jpeg', 0.9).split(',')[1]; };
Promise.all([document.fonts.load(font(100)), document.fonts.load(font(30, 'Mono', 600)), document.fonts.load(font(60, 'Sans', 900)),
  document.fonts.load(font(60, 'Sans', 800))]).then(() => { window.ANIM_READY = true; });
