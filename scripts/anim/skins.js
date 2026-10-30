// =====================================================================
//  skins.js — aynı sahneyi farklı görsel dillerde çizer (SKIN_NAME, anim_build'den gelir).
//  Her kaplama: pal() renkleri ayarlar (yüklemede bir kez) · bg() zemini çizer · post(layer) sahne katmanını
//  efektle ana tuvale basar. Altyazı her zaman en üstte net çizilir (drawOverlay).
//  iso (varsayılan, koyu) · paper · riso · sketch · ink · pixel · blueprint · cutpaper
// =====================================================================
function mixC(a, b, k) {   // hex a → hex b, k = b'nin payı
  const h = (x) => [1, 3, 5].map((i) => parseInt(x.slice(i, i + 2), 16)), A = h(a), Bc = h(b);
  return '#' + A.map((v, i) => Math.round(v + (Bc[i] - v) * k).toString(16).padStart(2, '0')).join('');
}
if (!ctx) ctx = document.getElementById('c').getContext('2d');   // desenler yüklemede üretilebilsin
const _pat = {};
function patTile(key, w, h, draw) {   // tekrarlı desen (opak: gizli-çizgi işini yapar)
  if (_pat[key]) return _pat[key];
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'); draw(g, w, h);
  return (_pat[key] = ctx.createPattern(c, 'repeat'));
}
let _grain = null;
function grainCanvas(alpha = 0.06, dark = '#000') {   // tohumlu kâğıt dokusu (bir kez üretilir)
  if (_grain) return _grain;
  const c = document.createElement('canvas'); c.width = 540; c.height = 960; const g = c.getContext('2d'); const r = mulberry32(7);
  for (let i = 0; i < 26000; i++) { g.globalAlpha = r() * alpha; g.fillStyle = r() < 0.5 ? dark : '#fff'; g.fillRect(r() * 540, r() * 960, 1 + r() * 1.5, 1 + r() * 1.5); }
  for (let i = 0; i < 260; i++) { g.globalAlpha = alpha * 0.8; g.strokeStyle = dark; g.lineWidth = 0.6; g.beginPath(); const x = r() * 540, y = r() * 960; g.moveTo(x, y); g.lineTo(x + (r() - 0.5) * 30, y + (r() - 0.5) * 8); g.stroke(); }
  return (_grain = c);
}
function overlayGrain(op = 'multiply', a = 1) { ctx.save(); ctx.globalCompositeOperation = op; ctx.globalAlpha = a; ctx.drawImage(grainCanvas(), 0, 0, W, H); ctx.restore(); }
const plain = (layer) => ctx.drawImage(layer, 0, 0);
function lightPal(o) {   // açık zeminli kaplamalar için ortak metin/altyazı renkleri
  Object.assign(BR, { white: o.ink, muted: o.muted, capText: o.ink, capStroke: o.capStroke || 'rgba(255,255,255,0.75)', bg: o.paper });
  Object.assign(PAL, { paper: o.paper, face: o.face || o.paper, edge: o.edge || o.ink, inner: o.inner, text: o.ink, textD: o.muted });
  COL.dark = o.ink;
}

const SKINS = {
  iso: { pal() {}, bg() { fillAll(BR.bg); }, post: plain },

  paper: {
    pal() {
      lightPal({ paper: '#F3EEE3', face: '#FBF8F1', ink: '#23232A', edge: '#55555E', inner: '#CFC9BC', muted: '#6E6A60' });
      Object.assign(BR, { gold: '#C98200', light: '#1E8C6E', brand: '#1E9C7F' });
      GOLDC = '#C98200'; tint = (c) => mixC(c, '#FBF8F1', 0.8); GOLDF = tint(GOLDC); COL.orangeL = '#D9581A'; COL.cardText = '#5A4FA0'; COL.goldDim = '#B08A3A';
    },
    bg() { fillAll(BR.bg); },
    post(layer) { plain(layer); overlayGrain('multiply', 0.9); },
  },

  riso: {   // risograf: krem kâğıt, 3 mürekkep, noktalı tram, kayık baskı
    pal() {
      lightPal({ paper: '#F1E7D3', ink: '#1F2A6B', edge: '#2A3F99', inner: '#B7B3C8', muted: '#5A5872' });
      Object.assign(COL, { blue: '#0078BF', purple: '#765BA7', orange: '#FF6C2F', grey: '#8D8B9C', yellow: '#E8C300', pink: '#FF48B0', orangeL: '#FF6C2F', cardText: '#1F2A6B', goldDim: '#B89400' });
      Object.assign(BR, { gold: '#FF48B0', light: '#00A95C', brand: '#00A95C', red: '#FF48B0' });
      GOLDC = '#E8B800';
      tint = (c) => patTile('dot' + c, 12, 12, (g, w, h) => { g.fillStyle = '#F1E7D3'; g.fillRect(0, 0, w, h); g.fillStyle = c; g.globalAlpha = 0.85; g.beginPath(); g.arc(6, 6, 3.3, 0, TAU); g.fill(); });
      GOLDF = tint(GOLDC);
    },
    bg() { fillAll(BR.bg); },
    post(layer) {
      ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.globalAlpha = 0.45; ctx.filter = 'hue-rotate(140deg) saturate(2)';
      ctx.drawImage(layer, 4, 3); ctx.restore();   // ikinci mürekkep katmanı: kayık
      plain(layer); overlayGrain('multiply', 1);
    },
  },

  sketch: {   // eskiz defteri: çizgili kâğıt, tarama dolgu, titreyen kalem
    pal() {
      lightPal({ paper: '#F8F4EA', ink: '#2B2722', edge: '#2B2722', inner: '#B8B0A2', muted: '#6B645A' });
      Object.assign(BR, { gold: '#E07A10', light: '#1E8C6E', brand: '#1E9C7F' });
      GOLDC = '#D98A00'; COL.orangeL = '#D9581A'; COL.cardText = '#4A3F8C'; COL.goldDim = '#9C7A2A';
      tint = (c) => patTile('hatch' + c, 10, 10, (g, w, h) => { g.fillStyle = '#F8F4EA'; g.fillRect(0, 0, w, h); g.strokeStyle = c; g.globalAlpha = 0.7; g.lineWidth = 1.6;
        g.beginPath(); g.moveTo(-2, 12); g.lineTo(12, -2); g.moveTo(-2, 2); g.lineTo(2, -2); g.moveTo(8, 12); g.lineTo(12, 8); g.stroke(); });
      GOLDF = tint(GOLDC);
    },
    bg() {
      fillAll(BR.bg); ctx.save(); ctx.strokeStyle = 'rgba(70,120,200,0.18)'; ctx.lineWidth = 2;
      for (let y = 180; y < H; y += 64) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
      ctx.strokeStyle = 'rgba(220,60,60,0.35)'; ctx.beginPath(); ctx.moveTo(48, 0); ctx.lineTo(48, H); ctx.stroke(); ctx.restore();
    },
    post(layer) {   // 2 karede bir değişen yatay şerit kayması = el çizimi titremesi
      const r = mulberry32(1000 + B), S = 8;
      for (let y = 0; y < H; y += S) { const dx = (r() - 0.5) * 3.2; ctx.drawImage(layer, 0, y, W, S, dx, y, W, S); }
      overlayGrain('multiply', 0.7);
    },
  },

  ink: {   // mürekkep (sumi-e): pirinç kâğıdı, gri yıkama, mürekkep dağılması, kırmızı mühür
    pal() {
      lightPal({ paper: '#EDE5D3', ink: '#151515', edge: '#1A1A1A', inner: '#A39C8E', muted: '#5E584E' });
      Object.assign(COL, { blue: '#2E2E2E', purple: '#4A4A4A', orange: '#A8322A', grey: '#7A7A7A', yellow: '#5A5A5A', pink: '#666', orangeL: '#A8322A', cardText: '#2E2E2E', goldDim: '#555' });
      Object.assign(BR, { gold: '#A8322A', light: '#A8322A', brand: '#2A2A2A', red: '#A8322A' });
      GOLDC = '#1A1A1A';
      tint = (c) => mixC(c === '#A8322A' ? c : '#1A1A1A', '#EDE5D3', c === '#A8322A' ? 0.78 : 0.86 - 0.08 * (c.charCodeAt(2) % 3));
      GOLDF = tint('#333');
    },
    bg() { fillAll(BR.bg); },
    post(layer) {
      ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.globalAlpha = 0.5; ctx.filter = 'blur(5px)'; ctx.drawImage(layer, 0, 2); ctx.restore();   // mürekkep dağılması
      plain(layer); overlayGrain('multiply', 1.2);
      ctx.save(); ctx.translate(930, 220); ctx.rotate(-0.05); ctx.fillStyle = '#B3261E'; ctx.globalAlpha = 0.92;   // mühür
      ctx.beginPath(); ctx.roundRect(-58, -66, 116, 132, 10); ctx.fill();
      ctx.globalCompositeOperation = 'destination-out'; ctx.globalAlpha = 0.25; ctx.drawImage(grainCanvas(), -58, -66, 116, 132);
      ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1; ctx.fillStyle = '#F5EBDD'; ctx.textAlign = 'center';
      ctx.font = `48px ${ANTON}`; ctx.fillText('PARA', 0, -8); ctx.fillText('FOMO', 0, 46); ctx.restore();
    },
  },

  pixel: {   // piksel: koyu gece, parlak renkler, 4x pikselleştirme + tarama çizgisi
    pal() {
      Object.assign(PAL, { paper: '#1B1E3B', face: '#1B1E3B', edge: '#E8E8F0', inner: '#4A4F86', text: '#E8E8F0', textD: '#8C90C8' });
      Object.assign(BR, { bg: '#1B1E3B', gold: '#FFD23F', light: '#3CF07A', brand: '#3CF07A', muted: '#9CA0D8' });
      Object.assign(COL, { blue: '#41A6F6', purple: '#B55CF5', orange: '#FF8A2A', grey: '#9CA0D8', yellow: '#FFD23F', pink: '#FF5C9E', orangeL: '#FF8A2A', dark: '#0C0E1F' });
      GOLDC = '#FFD23F'; tint = (c) => mixC(c, '#1B1E3B', 0.62); GOLDF = tint(GOLDC);
    },
    bg() { fillAll(BR.bg); const r = mulberry32(3); ctx.save(); ctx.fillStyle = '#FFFFFF'; for (let i = 0; i < 70; i++) { ctx.globalAlpha = 0.3 + 0.5 * r(); const s = r() < 0.2 ? 8 : 4; ctx.fillRect(Math.floor(r() * 270) * 4, Math.floor(r() * 480) * 4, s, s); } ctx.restore(); },
    post(layer) {
      if (!this.small) { this.small = document.createElement('canvas'); this.small.width = W / 4; this.small.height = H / 4; }
      const g = this.small.getContext('2d'); g.clearRect(0, 0, W / 4, H / 4); g.imageSmoothingEnabled = true; g.drawImage(layer, 0, 0, W / 4, H / 4);
      ctx.save(); ctx.imageSmoothingEnabled = false; ctx.drawImage(this.small, 0, 0, W, H); ctx.restore();
      ctx.save(); ctx.fillStyle = 'rgba(0,0,0,0.16)'; for (let y = 0; y < H; y += 4) ctx.fillRect(0, y, W, 1); ctx.restore();
    },
  },

  blueprint: {   // mavi kopya: lacivert ızgara, beyaz teknik çizgi
    pal() {
      Object.assign(PAL, { paper: '#0F3D63', face: '#0F3D63', edge: '#E6F1FF', inner: '#5D86AE', text: '#E6F1FF', textD: '#9CC0E4' });
      Object.assign(BR, { bg: '#0F3D63', gold: '#FFD25A', light: '#7FE8CF', brand: '#7FE8CF', muted: '#A9C7E6', white: '#F4F9FF' });
      Object.assign(COL, { blue: '#8EC5FF', purple: '#C3B2FF', orange: '#FFB067', grey: '#D7E6F5', yellow: '#FFD25A', pink: '#FF9EC4', orangeL: '#FFB067', dark: '#0A2A45' });
      GOLDC = '#FFD25A'; tint = (c) => mixC(c, '#0F3D63', 0.8); GOLDF = tint(GOLDC);
    },
    bg() {
      fillAll(BR.bg); ctx.save();
      for (let x = 0; x <= W; x += 30) { ctx.strokeStyle = x % 150 ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.14)'; ctx.lineWidth = x % 150 ? 1 : 2; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
      for (let y = 0; y <= H; y += 30) { ctx.strokeStyle = y % 150 ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.14)'; ctx.lineWidth = y % 150 ? 1 : 2; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
      ctx.restore();
    },
    post: plain,
  },

  cutpaper: {   // kesik kâğıt: kraft zemin, çizgisiz renkli kâğıt yüzler, yumuşak gölge
    pal() {
      lightPal({ paper: '#E6D5B8', face: '#FFFBF2', ink: '#3A2A1A', edge: 'rgba(80,55,30,0.45)', inner: 'rgba(80,55,30,0.18)', muted: '#6E5A44' });
      Object.assign(COL, { blue: '#4F86C6', purple: '#8E7CC3', orange: '#E8743B', grey: '#A9A39A', yellow: '#E9B949', pink: '#E06C9F', orangeL: '#C9581F', cardText: '#3A2A1A', goldDim: '#B08A3A' });
      Object.assign(BR, { gold: '#C2410C', light: '#2E8B57', brand: '#3BAA7E' });
      GOLDC = '#E9B949'; tint = (c) => mixC(c, '#FFFBF2', 0.3); GOLDF = tint(GOLDC);
    },
    bg() { fillAll(BR.bg); },
    post(layer) {
      ctx.save(); ctx.filter = 'brightness(0) blur(7px)'; ctx.globalAlpha = 0.3; ctx.drawImage(layer, 9, 13); ctx.restore();
      plain(layer); overlayGrain('multiply', 1.1);
    },
  },
};
const SKIN = SKINS[typeof SKIN_NAME !== 'undefined' ? SKIN_NAME : 'iso'] || SKINS.iso;
SKIN.pal();
