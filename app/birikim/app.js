/* ParaFOMO Birikim Simülatörü — gerçek aylık serilerle DCA (düzenli alım) hesabı.
   Veri: /benchmarks.json (gram altın, gümüş, USD, XU100) + /tufe-aylik.json (TÜFE).
   Üyelik gerektirmez; her şey tarayıcıda hesaplanır. */

const nf0 = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 0 });
const nf1 = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 1 });
const nfc = new Intl.NumberFormat('tr-TR', { notation: 'compact', maximumFractionDigits: 1 });
const tl = v => nf0.format(v) + ' ₺';
const sp = v => (v >= 0 ? '+%' : '−%') + nf1.format(Math.abs(v));

const ASSETS = [
  { key: 'gold',   label: 'Gram altın', dot: 'var(--a-gold)' },
  { key: 'xu100',  label: 'BIST 100',   dot: 'var(--a-bist)' },
  { key: 'silver', label: 'Gram gümüş', dot: 'var(--a-silver)' },
  { key: 'usd',    label: 'Dolar',      dot: 'var(--brand)' },
];

let bench = null, tufe = null;
let amount = 5000, years = 5, chartAsset = 'gold';

function safeGet(k) { try { return localStorage.getItem(k); } catch { return null; } }
function safeSet(k, v) { try { v === null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch {} }

async function load() {
  const [b, t] = await Promise.all([
    fetch('/benchmarks.json').then(r => r.json()),
    fetch('/tufe-aylik.json').then(r => r.json()),
  ]);
  bench = b.months;                                     // eski → yeni
  tufe = (t.months || []).map(m => [m.ay, m.aylik]).reverse();
}

/* TÜFE zinciri: ym ayından (sonraki aydan başlayarak) bugüne çarpan. */
const tufeIdx = () => new Map(tufe.map((m, i) => [m[0], i]));
function tufeFactor(ym, idx) {
  let from;
  if (idx.has(ym)) from = idx.get(ym) + 1;
  else if (ym < tufe[0][0]) from = 0;
  else return 1;
  let f = 1;
  for (let i = from; i < tufe.length; i++) f *= 1 + tufe[i][1] / 100;
  return f;
}

/* DCA: son n ayın her birinde o ayın kapanışından alım; bugünkü fiyatla değer. */
function simulate() {
  const n = years * 12;
  const rows = bench.slice(-(n + 1));      // n alım ayı + en güncel ay (değerleme)
  if (rows.length < n + 1) return null;
  const buyMonths = rows.slice(0, n);
  const latest = rows[rows.length - 1];
  const invested = amount * n;
  const tIdx = tufeIdx();

  const out = ASSETS.map(a => {
    let units = 0, ok = true;
    for (const m of buyMonths) {
      if (m[a.key] == null) { ok = false; break; }
      units += amount / m[a.key];
    }
    if (!ok || latest[a.key] == null) return null;
    const value = units * latest[a.key];
    return { ...a, value, pct: (value / invested - 1) * 100 };
  }).filter(Boolean);

  // TÜFE serimiz Eki 2022'de başlıyor — daha eski dönemlerde endeksleme eksik
  // kalacağından satırı yalnız tam kapsanan dönemlerde gösteriyoruz.
  const tufeFull = buyMonths[0].ay >= tufe[0][0];
  let tufeVal = null;
  if (tufeFull) {
    tufeVal = 0;
    for (const m of buyMonths) tufeVal += amount * tufeFactor(m.ay, tIdx);
    out.push({ key: 'tufe', label: 'Enflasyona endeksli', dot: 'var(--muted)', dim: true, value: tufeVal, pct: (tufeVal / invested - 1) * 100 });
  }
  out.push({ key: 'cash', label: 'Yastık altı', dot: 'var(--line)', dim: true, value: invested, pct: 0 });

  out.sort((a, b) => b.value - a.value);
  return { invested, n, rows: out, start: buyMonths[0].ay, end: latest.ay, tufeVal, tufeFull };
}

/* Seçili varlık için ay ay birikim eğrisi. */
function curve(assetKey) {
  const n = years * 12;
  const rows = bench.slice(-(n + 1));
  let units = 0;
  const pts = [];
  for (let i = 0; i < rows.length; i++) {
    const price = rows[i][assetKey];
    if (price == null) return null;
    if (i < rows.length - 1) units += amount / price;   // son ay yalnız değerleme
    pts.push({ t: rows[i].ay, v: units * price, paid: amount * Math.min(i + 1, n) });
  }
  return pts;
}

const trAy = ym => {
  const [y, m] = ym.split('-');
  return ['', 'Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'][Number(m)] + ' ' + y;
};

function render() {
  const el = document.getElementById('results');
  const sim = simulate();
  if (!sim) { el.innerHTML = '<p class="sim-lead">Bu süre için yeterli veri yok.</p>'; return; }
  const best = sim.rows[0];
  el.innerHTML = `
    <p class="sim-lead"><b>${trAy(sim.start)}</b>'dan beri her ay <b>${tl(amount)}</b> biriktirseydin
    toplam <b>${tl(sim.invested)}</b> yatırmış olacaktın. En iyisi <b>${best.label.toLocaleLowerCase('tr-TR')}</b> olurdu:</p>
    <div class="rows num">
      ${sim.rows.map(r => `
        <div class="row${r.dim ? ' dim' : ''}">
          <span class="who"><span class="dot" style="background:${r.dot}"></span>${r.label}</span>
          <span class="track"><span class="fill" style="width:${(r.value / best.value * 100).toFixed(1)}%"></span></span>
          <span class="nums"><b>${tl(r.value)}</b><span>${sp(r.pct)}</span>
            ${!r.dim && sim.tufeVal ? `<span class="reel" title="Enflasyona endeksli tutara göre">reel ${sp((r.value / sim.tufeVal - 1) * 100)}</span>` : ''}</span>
        </div>`).join('')}
    </div>
    ${sim.tufeFull ? '' : '<p class="chart-cap">Enflasyon karşılaştırması bu dönem için gösterilmiyor: TÜFE serimiz Ekim 2022\'de başlıyor. 1 ve 3 yıllık dönemlerde "enflasyona endeksli" satırını görürsün.</p>'}
    <p class="share-row"><button class="btn btn-quiet" id="sim-share">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v7a1.5 1.5 0 0 0 1.5 1.5h13A1.5 1.5 0 0 0 20 19v-7M12 15V3m0 0L7.5 7.5M12 3l4.5 4.5"/></svg>
      Sonucu kart olarak paylaş</button></p>
    <section class="sim-chart" aria-label="Birikim eğrisi">
      <div class="chart-head">
        <h2>Ay ay birikim</h2>
        <span class="chips" role="tablist" aria-label="Varlık">
          ${ASSETS.map(a => `<button role="tab" aria-selected="${chartAsset === a.key}" data-a="${a.key}">${a.label}</button>`).join('')}
        </span>
      </div>
      <div class="chart-box" id="sim-box"></div>
      <p class="chart-cap">Düz çizgi: birikimin değeri · kesikli çizgi: o ana dek yatırdığın toplam.</p>
    </section>`;
  el.querySelectorAll('.chips button').forEach(b => b.addEventListener('click', () => {
    chartAsset = b.dataset.a;
    render();
  }));
  el.querySelector('#sim-share').addEventListener('click', () => shareCard(sim));
  drawCurve();
}

/* Paylaşım kartı: soru + ilk 4 satır + marka. */
async function shareCard(sim) {
  try { await document.fonts.load('700 100px "IBM Plex Sans"'); await document.fonts.load('500 44px "IBM Plex Sans"'); } catch {}
  const W = 1080, H = 1350;
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  const c = cv.getContext('2d');
  if (!c.roundRect) c.roundRect = function (x, y, w, h) { this.rect(x, y, w, h); return this; };
  const F = w => `${w} "IBM Plex Sans", sans-serif`;
  const COLORS = { gold: '#BA851F', xu100: '#0891B2', silver: '#7488D8', usd: '#2BB194', tufe: '#8DA29D', cash: '#556763' };
  c.fillStyle = '#0C1514'; c.fillRect(0, 0, W, H);
  c.fillStyle = '#E9F0EE'; c.font = F('700 56px'); c.fillText('parafomo', 80, 126);
  const wmW = c.measureText('parafomo').width;
  c.font = F('600 34px'); c.fillStyle = '#4FD8BE'; c.fillText('birikim', 80 + wmW + 26, 122);
  c.fillStyle = '#E9F0EE'; c.font = F('700 64px');
  c.fillText(`Ayda ${nf0.format(amount)} ₺, ${years} yıl.`, 80, 260);
  c.fillStyle = '#8DA29D'; c.font = F('500 42px');
  c.fillText(`${trAy(sim.start)}'dan beri düzenli alsaydın bugün:`, 80, 322);
  let ly = 430;
  const top = sim.rows.slice(0, 5);
  const maxV = top[0].value;
  for (const r of top) {
    c.fillStyle = COLORS[r.key] || '#8DA29D';
    c.beginPath(); c.roundRect(80, ly - 34, 26, 26, 7); c.fill();
    c.fillStyle = r.dim ? '#8DA29D' : '#E9F0EE'; c.font = F('600 40px');
    c.fillText(r.label, 126, ly - 8);
    c.fillStyle = r.dim ? '#556763' : (COLORS[r.key] || '#4FD8BE');
    c.beginPath(); c.roundRect(80, ly + 8, (W - 160) * (r.value / maxV), 22, 7); c.fill();
    c.fillStyle = '#E9F0EE'; c.font = F('700 44px');
    c.fillText(nf0.format(r.value) + ' ₺', 80, ly + 88);
    c.fillStyle = r.dim ? '#8DA29D' : (r.pct >= 0 ? '#46C879' : '#F0776A'); c.font = F('600 36px');
    c.fillText(sp(r.pct), 110 + c.measureText(nf0.format(r.value) + ' ₺').width + 180, ly + 86);
    ly += 160;
  }
  c.strokeStyle = '#233431'; c.lineWidth = 2;
  c.beginPath(); c.moveTo(80, H - 150); c.lineTo(W - 80, H - 150); c.stroke();
  c.fillStyle = '#E9F0EE'; c.font = F('600 40px');
  c.fillText('app.parafomo.com/birikim', 80, H - 84);
  c.fillStyle = '#8DA29D'; c.font = F('500 32px');
  c.fillText('Gerçek verilerle dene — ücretsiz, üyeliksiz', 80, H - 36);
  cv.toBlob(async blob => {
    if (!blob) return;
    const file = new File([blob], 'parafomo-birikim.png', { type: 'image/png' });
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      try { await navigator.share({ files: [file], title: 'Birikim Simülatörü — ParaFOMO' }); return; } catch {}
    }
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = file.name;
    a.click();
    URL.revokeObjectURL(a.href);
  }, 'image/png');
}

function drawCurve() {
  const box = document.getElementById('sim-box');
  const pts = curve(chartAsset);
  if (!pts) { box.innerHTML = ''; return; }
  const W = 720, H = 210, L = 8, R = 62, T = 12, B = 24;
  const max = Math.max(...pts.map(p => Math.max(p.v, p.paid)));
  const min = 0;
  const x = i => L + (W - L - R) * (i / (pts.length - 1));
  const y = v => T + (H - T - B) * (1 - v / (max * 1.06));
  const line = 'M' + pts.map((p, i) => `${x(i).toFixed(1)},${y(p.v).toFixed(1)}`).join(' L');
  const paid = 'M' + pts.map((p, i) => `${x(i).toFixed(1)},${y(p.paid).toFixed(1)}`).join(' L');
  box.innerHTML = `
    <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Birikimin ay ay değeri ve yatırılan toplam">
      <path class="c-paid" d="${paid}"/>
      <path class="c-line" d="${line}" vector-effect="non-scaling-stroke"/>
      <line class="c-cross" x1="0" x2="0" y1="${T}" y2="${H - B}" visibility="hidden"/>
      <circle class="c-dot" r="4.5" visibility="hidden"/>
      <text class="yv num" x="${W - 6}" y="${y(max) + 4}" text-anchor="end">${nfc.format(max)} ₺</text>
      <text class="yv num" x="${W - 6}" y="${H - B}" text-anchor="end">0</text>
    </svg>
    <div class="c-tip num" hidden></div>`;
  const svg = box.querySelector('svg'), tip = box.querySelector('.c-tip');
  const cross = svg.querySelector('.c-cross'), dot = svg.querySelector('.c-dot');
  function show(clientX) {
    const rect = svg.getBoundingClientRect();
    const fx = (clientX - rect.left) / rect.width * W;
    const i = Math.max(0, Math.min(pts.length - 1, Math.round((fx - L) / (W - L - R) * (pts.length - 1))));
    const p = pts[i], px = x(i), py = y(p.v);
    cross.setAttribute('x1', px); cross.setAttribute('x2', px); cross.setAttribute('visibility', 'visible');
    dot.setAttribute('cx', px); dot.setAttribute('cy', py); dot.setAttribute('visibility', 'visible');
    tip.hidden = false;
    tip.innerHTML = `<b>${trAy(p.t)}</b><br>Değer ${tl(p.v)}<br><span>Yatırılan ${tl(p.paid)}</span>`;
    const bx = px / W * rect.width;
    tip.style.left = Math.max(4, Math.min(rect.width - tip.offsetWidth - 4, bx - tip.offsetWidth / 2)) + 'px';
  }
  function hide() { cross.setAttribute('visibility', 'hidden'); dot.setAttribute('visibility', 'hidden'); tip.hidden = true; }
  box.addEventListener('pointermove', e => show(e.clientX));
  box.addEventListener('pointerleave', hide);
}

/* ---- kurulum ---- */
document.getElementById('theme-btn').addEventListener('click', () => {
  const cur = safeGet('pf_theme');
  const next = cur === 'dark' ? 'light' : cur === 'light' ? null : 'dark';
  safeSet('pf_theme', next);
  if (next) document.documentElement.dataset.theme = next;
  else delete document.documentElement.dataset.theme;
});
document.querySelectorAll('.period .chips button').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('.period .chips button').forEach(x => x.setAttribute('aria-selected', String(x === b)));
  years = Number(b.dataset.y);
  render();
}));
let amtTimer = 0;
document.getElementById('amount').addEventListener('input', e => {
  clearTimeout(amtTimer);
  amtTimer = setTimeout(() => {
    const v = parseFloat(String(e.target.value).replace(',', '.'));
    if (v >= 1) { amount = v; render(); }
  }, 350);
});
if ('serviceWorker' in navigator) { try { navigator.serviceWorker.register('/sw.js'); } catch {} }
load().then(render).catch(() => {
  document.getElementById('results').innerHTML = '<p class="sim-lead">Veri yüklenemedi — sayfayı yenilemeyi dene.</p>';
});
