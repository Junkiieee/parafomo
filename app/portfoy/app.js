/* ParaFOMO Portföy — app.parafomo.com/portfoy/ SPA.
   Veri + üyelik: api.parafomo.com (JWT, localStorage). Build adımı yok.
   Örnek mod (demo): API'ye dokunmadan tüm arayüzü temsilî veriyle gezdirir. */

const API_BASE = safeGet('pf_api_base') || 'https://api.parafomo.com';
const TOKEN_KEY = 'pf_token';
const GOOGLE_CLIENT_ID = '1020605001020-3o64jftksul1tkqj2gov24j7qj4o18f4.apps.googleusercontent.com';

const TYPE = {
  bist:   { tick: s => s, name: s => symbolName(s), unit: 'adet', q: 'Adet', cls: 'bist',   label: 'Hisse' },
  gold:   { tick: () => 'ALTIN',  name: () => 'Gram altın (24 ayar)', unit: 'gram', q: 'Gram', cls: 'gold',   label: 'Altın' },
  silver: { tick: () => 'GÜMÜŞ', name: () => 'Gram gümüş',           unit: 'gram', q: 'Gram', cls: 'silver', label: 'Gümüş' },
  usd:    { tick: () => 'USD', name: () => 'Amerikan doları', unit: '$',   q: 'Dolar miktarı ($)', cls: 'usd',  label: 'Dolar' },
  eur:    { tick: () => 'EUR', name: () => 'Euro',            unit: '€',   q: 'Euro miktarı (€)',  cls: 'eur',  label: 'Euro' },
  btc:    { tick: () => 'BTC', name: () => 'Bitcoin',         unit: 'BTC', q: 'Miktar (BTC)',      cls: 'btc',  label: 'Bitcoin' },
  eth:    { tick: () => 'ETH', name: () => 'Ethereum',        unit: 'ETH', q: 'Miktar (ETH)',      cls: 'eth',  label: 'Ethereum' },
  cash:   { tick: () => 'TL',  name: () => 'Nakit (TL)',      unit: '₺',   q: 'Tutar (₺)',         cls: 'cash', label: 'Nakit', fixed: true },
};
const ALLOC_CLASS = { bist: 'bist', gold: 'gold', silver: 'silver', usd: 'fx', eur: 'fx', btc: 'crypto', eth: 'crypto', cash: 'cash' };
const ALLOC_META = [
  ['gold', 'Altın'], ['bist', 'Hisse'], ['silver', 'Gümüş'],
  ['fx', 'Döviz'], ['crypto', 'Kripto'], ['cash', 'Nakit'],
];
const GOAL_KIND = {
  try:    { label: '₺ değer',          fmt: v => nf0.format(v) + ' ₺' },
  usd:    { label: 'dolar karşılığı',  fmt: v => nf0.format(v) + ' $' },
  gold_g: { label: 'gram altın',       fmt: v => nf1.format(v) + ' g' },
};

let state = {
  user: null, summary: null, history: [], watchlist: [], alerts: [], goals: [], txns: [],
  tufe: null, bench: null, symbols: [], demo: false, refreshTimer: 0, chartRange: 'all',
  unit: (safeGet('pf_unit') === 'usd' || safeGet('pf_unit') === 'gold') ? safeGet('pf_unit') : 'try',
  view: 'ozet', // ozet | varliklar | takip | analiz
};

/* ---------- yardımcılar ---------- */
function safeGet(k) { try { return localStorage.getItem(k); } catch { return null; } }
function safeSet(k, v) { try { v === null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch {} }
const token = () => safeGet(TOKEN_KEY);

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
const nf2 = new Intl.NumberFormat('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const nf1 = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 1 });
const nf0 = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 0 });
const nfq = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 4 });
const nfc = new Intl.NumberFormat('tr-TR', { notation: 'compact', maximumFractionDigits: 1 });
const money = v => v == null ? '—' : nf2.format(v) + ' ₺';
const signedMoney = v => v == null ? '—' : (v > 0 ? '+' : v < 0 ? '−' : '') + nf2.format(Math.abs(v)) + ' ₺';
const signedPct = v => v == null ? '' : (v > 0 ? '+' : v < 0 ? '−' : '') + '%' + nf2.format(Math.abs(v));
const signedPct1 = v => v == null ? '' : (v > 0 ? '+' : v < 0 ? '−' : '') + '%' + nf1.format(Math.abs(v));
const plClass = v => v == null || v === 0 ? 'pl-flat' : v > 0 ? 'pl-gain' : 'pl-loss';
/* Birim görünümü: ₺ / $ / gram altın — tutarları seçili birimde göster. */
function unitRate(s) {
  if (state.unit === 'usd' && s.usd_try) return { r: s.usd_try, suf: ' $', nf: nf2 };
  if (state.unit === 'gold' && s.gold_gram_try) return { r: s.gold_gram_try, suf: ' g', nf: nf1 };
  return { r: 1, suf: ' ₺', nf: nf2 };
}
const fmtU = (v, u) => v == null ? '—' : u.nf.format(v / u.r) + u.suf;
const signedU = (v, u) => v == null ? '—' : (v > 0 ? '+' : v < 0 ? '−' : '') + u.nf.format(Math.abs(v) / u.r) + u.suf;
const trDate = iso => new Date((iso.length === 7 ? iso + '-15' : iso) + 'T12:00:00')
  .toLocaleDateString('tr-TR', iso.length === 7 ? { month: 'short', year: 'numeric' } : { day: 'numeric', month: 'short' });

function toast(msg, isErr) {
  const el = document.createElement('div');
  el.className = 'toast' + (isErr ? ' toast-err' : '');
  el.textContent = msg;
  document.getElementById('toasts').appendChild(el);
  setTimeout(() => el.remove(), 4200);
}

async function api(path, opts = {}) {
  opts.headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers);
  const t = token();
  if (t) opts.headers.Authorization = 'Bearer ' + t;
  let res;
  try { res = await fetch(API_BASE + path, opts); }
  catch { throw new Error('Sunucuya ulaşılamadı. Bağlantını kontrol edip tekrar dene.'); }
  if (res.status === 401 && t) { logout(false); throw new Error('Oturumun sona erdi. Tekrar giriş yap.'); }
  if (res.status === 204) return null;
  let body = null;
  try { body = await res.json(); } catch {}
  if (!res.ok) {
    const d = body && body.detail;
    throw new Error(typeof d === 'string' ? d : 'İşlem tamamlanamadı (' + res.status + ').');
  }
  return body;
}

function symbolName(code) {
  const hit = state.symbols.find(s => s.c === code);
  return hit ? hit.n : 'BIST hissesi';
}
async function loadSymbols() {
  if (state.symbols.length) return;
  try { state.symbols = await (await fetch('/bist-symbols.json')).json(); } catch { state.symbols = []; }
}
async function loadTufe() {
  if (state.tufe) return;
  try {
    const d = await (await fetch('/tufe-aylik.json')).json();
    state.tufe = (d.months || []).map(m => [m.ay, m.aylik]).reverse(); // eski → yeni
  } catch { state.tufe = []; }
}
// BIST kodu → parafomo.com/halka-arz/<slug> (deploy-app.sh data/halka-arz-sirketler.json'dan üretir)
async function loadIpoMap() {
  if (state.ipoMap) return;
  try { state.ipoMap = await (await fetch('/halka-arz-map.json')).json(); } catch { state.ipoMap = {}; }
}
async function loadBench() {
  if (state.bench) return;
  try {
    const d = await (await fetch('/benchmarks.json')).json();
    const months = d.months || [];
    state.bench = { months, idx: new Map(months.map((m, i) => [m.ay, i])) };
  } catch { state.bench = { months: [], idx: new Map() }; }
}

/* Alış ayından SONRAKİ ayların TÜFE zinciri (maliyeti bugünkü liraya taşır). */
function tufeFactor(ym) {
  const months = state.tufe;
  if (!months || !months.length) return null;
  const idx = new Map(months.map((m, i) => [m[0], i]));
  let from;
  if (idx.has(ym)) from = idx.get(ym) + 1;
  else if (ym < months[0][0]) from = 0;           // seri başından önce → kısmi
  else return 1;                                   // içinde bulunduğumuz ay
  let f = 1;
  for (let i = from; i < months.length; i++) f *= 1 + months[i][1] / 100;
  return f;
}

/* Reel (enflasyon sonrası) getiri — portföy geneli. */
function realReturn(s) {
  if (!state.tufe || !state.tufe.length || !s.holdings.length) return null;
  const first = state.tufe[0][0];
  let adjCost = 0, value = 0, dated = 0, undated = 0, partial = false;
  for (const h of s.holdings) {
    if (h.current_value == null) continue;
    value += h.current_value;
    if (!h.purchase_date) { adjCost += h.cost_value; undated++; continue; }
    const ym = h.purchase_date.slice(0, 7);
    if (ym < first) partial = true;
    adjCost += h.cost_value * (tufeFactor(ym) ?? 1);
    dated++;
  }
  if (!dated || adjCost <= 0) return { dated: 0, undated };
  const pl = value - adjCost;
  return { pl, pct: pl / adjCost * 100, dated, undated, partial };
}

/* "Ne olsaydı" kıyası: alış tarihli pozisyonların maliyeti aynı tarihte tek
   varlığa gitseydi (gram altın / dolar / BIST 100) bugün ne olurdu? */
function benchReturn(s) {
  const b = state.bench;
  if (!b || !b.months.length || !s.holdings.length) return null;
  const latest = b.months[b.months.length - 1];
  const rowFor = ym => {            // tam ay yoksa en yakın önceki aya düş
    if (ym >= latest.ay) return latest;
    for (let k = 0; k < 3; k++) {
      const i = b.idx.get(ym);
      if (i != null) return b.months[i];
      const [yy, mm] = ym.split('-').map(Number);
      ym = mm === 1 ? `${yy - 1}-12` : `${yy}-${String(mm - 1).padStart(2, '0')}`;
    }
    return null;
  };
  let cost = 0, userVal = 0, excluded = 0, n = 0;
  const alt = { gold: 0, usd: 0, xu100: 0 };
  for (const h of s.holdings) {
    if (!h.purchase_date || h.current_value == null) continue;
    const ym = h.purchase_date.slice(0, 7);
    const row = rowFor(ym);
    if (!row || row.xu100 == null) { excluded++; continue; }
    cost += h.cost_value;
    userVal += h.current_value;
    alt.gold += h.cost_value * (latest.gold / row.gold);
    alt.usd += h.cost_value * (latest.usd / row.usd);
    alt.xu100 += h.cost_value * (latest.xu100 / row.xu100);
    n++;
  }
  if (!n || cost <= 0) return null;
  const tf = (() => {   // aynı alt küme için TÜFE
    let a = 0;
    for (const h of s.holdings) {
      if (!h.purchase_date || h.current_value == null) continue;
      const ym = h.purchase_date.slice(0, 7);
      const i = state.bench.idx.get(ym);
      if ((i == null && ym < state.bench.months[0].ay) || (i != null && state.bench.months[i].xu100 == null)) continue;
      if (i == null && ym < state.bench.months[0].ay) continue;
      a += h.cost_value * (tufeFactor(ym) ?? 1);
    }
    return a > 0 ? (a / cost - 1) * 100 : null;
  })();
  return {
    n, excluded,
    user: (userVal / cost - 1) * 100,
    gold: (alt.gold / cost - 1) * 100,
    usd: (alt.usd / cost - 1) * 100,
    xu100: (alt.xu100 / cost - 1) * 100,
    tufe: tf,
  };
}

/* ---------- tema ---------- */
function applyTheme() {
  const t = safeGet('pf_theme');
  if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t;
  else delete document.documentElement.dataset.theme;
}
function cycleTheme() {
  const cur = safeGet('pf_theme');
  const next = cur === 'dark' ? 'light' : cur === 'light' ? null : 'dark';
  safeSet('pf_theme', next);
  applyTheme();
}
const isDark = () =>
  document.documentElement.dataset.theme === 'dark' ||
  (document.documentElement.dataset.theme !== 'light' && matchMedia('(prefers-color-scheme: dark)').matches);

/* ---------- oturum ---------- */
function logout(announce = true) {
  safeSet(TOKEN_KEY, null);
  state.user = state.summary = null;
  state.history = []; state.watchlist = []; state.alerts = []; state.goals = []; state.txns = []; state.demo = false;
  clearInterval(state.refreshTimer);
  renderAuth();
  if (announce) toast('Çıkış yapıldı.');
}
async function onAuthed(tok) {
  safeSet(TOKEN_KEY, tok);
  state.demo = false;
  await enterApp();
}

/* ---------- örnek (demo) modu ---------- */
const DEMO = {
  // Maliyetler gerçek ay-sonu serileriyle (benchmarks.json) tutarlı seçildi —
  // "ne olsaydı" kıyası demo'da da anlamlı görünsün.
  holdings: [
    { id: -1, asset_type: 'gold',   symbol: 'GOLD',  quantity: 25,  cost_price: 5400, purchase_date: '2025-10-20', note: 'düğün altınları', current_price: 6644.8, change_pct: 0.4 },
    { id: -2, asset_type: 'bist',   symbol: 'THYAO', quantity: 40,  cost_price: 246,  purchase_date: '2025-12-15', note: null, current_price: 287.5, change_pct: 0 },
    { id: -3, asset_type: 'bist',   symbol: 'ASELS', quantity: 15,  cost_price: 298,  purchase_date: '2026-07-10', note: null, current_price: 351.2, change_pct: 0 },
    { id: -4, asset_type: 'silver', symbol: 'SILVER', quantity: 200, cost_price: 53.2, purchase_date: '2025-08-18', note: null, current_price: 96.4, change_pct: 0.6 },
    { id: -5, asset_type: 'usd',  symbol: 'USD',  quantity: 1000,  cost_price: 42.95, purchase_date: '2025-12-28', note: null, current_price: 49.4, change_pct: 0.1 },
    { id: -6, asset_type: 'btc',  symbol: 'BTC',  quantity: 0.01,  cost_price: 3465000, purchase_date: '2026-04-20', note: null, current_price: 4122800, change_pct: 0.9 },
    { id: -7, asset_type: 'cash', symbol: 'CASH', quantity: 25000, cost_price: 1, purchase_date: '2026-08-01', note: 'acil durum fonu', current_price: 1, change_pct: 0 },
  ],
  watchlist: [
    { id: -1, asset_type: 'bist', symbol: 'TUPRS', current_price: 184.3, change_pct: 0 },
    { id: -2, asset_type: 'bist', symbol: 'EREGL', current_price: 54.15, change_pct: 0 },
  ],
};
function buildDemo() {
  const holdings = DEMO.holdings.map(h => {
    const cost_value = h.quantity * h.cost_price;
    const current_value = h.quantity * h.current_price;
    const profit_loss = current_value - cost_value;
    return Object.assign({}, h, {
      cost_value, current_value, profit_loss,
      profit_loss_pct: profit_loss / cost_value * 100,
      day_change: h.change_pct ? current_value - current_value / (1 + h.change_pct / 100) : 0,
    });
  });
  const total_cost = holdings.reduce((a, h) => a + h.cost_value, 0);
  const total_value = holdings.reduce((a, h) => a + h.current_value, 0);
  const total_day_change = holdings.reduce((a, h) => a + (h.day_change || 0), 0);
  state.summary = {
    holdings, total_cost, total_value,
    total_profit_loss: total_value - total_cost,
    total_profit_loss_pct: (total_value - total_cost) / total_cost * 100,
    total_day_change, total_day_change_pct: total_day_change / total_value * 100,
    priced_at: new Date().toISOString(),
    usd_try: 49.4, gold_gram_try: 6644.8,
    realized_pl_total: 2040, realized_pl_year: 2040,
  };
  state.txns = [
    { id: -9, asset_type: 'silver', symbol: 'SILVER', side: 'sell', quantity: 50, price: 94, trade_date: '2026-09-18', realized_pl: 2040, note: null },
    ...DEMO.holdings.map((h, i) => ({ id: -10 - i, asset_type: h.asset_type, symbol: h.symbol, side: 'buy', quantity: h.quantity, price: h.cost_price, trade_date: h.purchase_date, realized_pl: null, note: null })),
  ];
  const hist = []; let v = total_value;
  for (let i = 0; i < 90; i++) {
    hist.unshift({ day: new Date(Date.now() - i * 864e5).toISOString().slice(0, 10), total_value: Math.round(v), total_cost });
    const wave = Math.sin(i / 7) * 0.004 + (((i * 2654435761) % 97) / 97 - 0.5) * 0.012;
    v = v / (1 + 0.0022 + wave);
  }
  state.history = hist;
  state.watchlist = DEMO.watchlist.slice();
  state.alerts = [{ id: -1, asset_type: 'gold', symbol: 'GOLD', kind: 'price', direction: 'above', threshold: 7000, repeat: false, armed: true, active: true, triggered_at: null, triggered_price: null }];
  state.goals = [{ id: -1, kind: 'gold_g', target: 100, title: 'Yüz gram hedefi' }];
  state.user = { email: 'ornek@parafomo.com', display_name: 'Örnek Portföy', monthly_email: true };
}
function startDemo() {
  state.demo = true;
  buildDemo();
  Promise.all([loadSymbols(), loadTufe(), loadBench(), loadIpoMap()]).then(renderApp);
}
function demoNudge() {
  toast('Örnek görünümdesin — kendi pozisyonların için ücretsiz kayıt ol.');
}

/* ---------- giriş ekranı ---------- */
function renderAuth(mode = 'signin') {
  document.title = 'ParaFOMO Portföy';
  document.getElementById('bar-right').innerHTML = themeBtnHtml();
  bindThemeBtn();
  const main = document.getElementById('main');
  main.classList.remove('masked');
  main.innerHTML = `
  <div class="landing">
    <section class="pitch">
      <h1>Altının, hissen, gümüşün — tek ekranda.</h1>
      <p>Pozisyonlarını bir kez ekle; canlı fiyatla toplam değerini, değer grafiğini ve
      <strong>enflasyondan arındırılmış gerçek kârını</strong> her açtığında hazır bul.
      "Dolara koysaydım ne olurdu?" kıyası, hedefler, fiyat alarmı ve ay sonu özeti — hepsi ücretsiz.</p>
      <div class="sample" aria-hidden="true">
        <p class="sample-cap">Örnek portföy</p>
        <div class="total num">348.260 ₺ <span class="pl-gain" style="font-size:.55em">+%12,4</span></div>
        <div class="alloc" style="margin:14px 0 0">
          <div class="alloc-bar">
            <span class="f-gold" style="flex:52"></span><span class="f-bist" style="flex:36"></span><span class="f-silver" style="flex:12"></span>
          </div>
          <div class="alloc-legend">
            <span><span class="dot s-gold"></span>Altın<span class="pct">%52</span></span>
            <span><span class="dot s-bist"></span>Hisse<span class="pct">%36</span></span>
            <span><span class="dot s-silver"></span>Gümüş<span class="pct">%12</span></span>
          </div>
        </div>
      </div>
      <p class="try-demo"><button type="button" class="btn btn-quiet" id="demo-btn">Kaydolmadan gez: örnek portföy</button></p>
    </section>
    <section class="auth-card" aria-label="Giriş">
      <div class="auth-tabs" role="tablist">
        <button role="tab" aria-selected="${mode === 'signin'}" data-mode="signin">Giriş yap</button>
        <button role="tab" aria-selected="${mode === 'signup'}" data-mode="signup">Kayıt ol</button>
      </div>
      <form id="auth-form">${authFormHtml(mode)}</form>
      <p class="form-error" id="auth-err" role="alert"></p>
      <div class="auth-alt">ya da</div>
      <div class="gsi-slot" id="gsi"></div>
      <p class="auth-foot" id="auth-foot">${mode === 'signin'
        ? '<button type="button" id="to-reset">Şifreni mi unuttun?</button>'
        : 'Kayıt olarak <a href="/kvkk/">kullanım ve gizlilik koşullarını</a> kabul etmiş olursun.'}</p>
    </section>
  </div>`;

  main.querySelectorAll('.auth-tabs button').forEach(b =>
    b.addEventListener('click', () => renderAuth(b.dataset.mode)));
  main.querySelector('#demo-btn').addEventListener('click', startDemo);
  const resetLink = main.querySelector('#to-reset');
  if (resetLink) resetLink.addEventListener('click', () => renderReset());

  main.querySelector('#auth-form').addEventListener('submit', async e => {
    e.preventDefault();
    const f = e.target, err = main.querySelector('#auth-err');
    const btn = f.querySelector('button[type=submit]');
    err.textContent = ''; btn.disabled = true;
    try {
      const body = { email: f.email.value.trim(), password: f.password.value };
      let out;
      if (mode === 'signup') {
        const dn = f.display_name.value.trim();
        if (dn) body.display_name = dn;
        out = await api('/auth/register', { method: 'POST', body: JSON.stringify(body) });
      } else {
        out = await api('/auth/login', { method: 'POST', body: JSON.stringify(body) });
      }
      await onAuthed(out.access_token);
    } catch (ex) { err.textContent = ex.message; btn.disabled = false; }
  });

  mountGoogle();
}

function authFormHtml(mode) {
  return (mode === 'signup' ? `
    <label class="field"><span>Adın (isteğe bağlı)</span>
      <input name="display_name" autocomplete="name" maxlength="120"></label>` : '') + `
    <label class="field"><span>E-posta</span>
      <input name="email" type="email" required autocomplete="email" inputmode="email"></label>
    <label class="field"><span>Şifre</span>
      <input name="password" type="password" required minlength="8"
        autocomplete="${mode === 'signup' ? 'new-password' : 'current-password'}">
      ${mode === 'signup' ? '<span class="hint">En az 8 karakter.</span>' : ''}</label>
    <button class="btn btn-primary" type="submit" style="width:100%">${mode === 'signup' ? 'Hesap oluştur' : 'Giriş yap'}</button>`;
}

function renderReset() {
  const card = document.querySelector('.auth-card');
  card.innerHTML = `
    <h2 style="margin:0 0 6px;font-size:1.15rem">Şifre sıfırlama</h2>
    <p style="color:var(--muted);font-size:.92rem;margin:0 0 18px">E-postanı yaz; sıfırlama bağlantısını gönderelim.</p>
    <form id="reset-form">
      <label class="field"><span>E-posta</span><input name="email" type="email" required autocomplete="email"></label>
      <button class="btn btn-primary" type="submit" style="width:100%">Bağlantıyı gönder</button>
    </form>
    <p class="form-error" id="auth-err" role="alert"></p>
    <p class="auth-foot"><button type="button" id="back-signin">Girişe dön</button></p>`;
  card.querySelector('#back-signin').addEventListener('click', () => renderAuth('signin'));
  card.querySelector('#reset-form').addEventListener('submit', async e => {
    e.preventDefault();
    const err = card.querySelector('#auth-err');
    try {
      await api('/auth/request-password-reset', { method: 'POST', body: JSON.stringify({ email: e.target.email.value.trim() }) });
      card.innerHTML = '<p style="margin:8px 0">Bu adrese kayıtlı bir hesap varsa sıfırlama bağlantısı az önce gönderildi. Gelen kutunu (ve spam klasörünü) kontrol et.</p><p class="auth-foot"><button type="button" id="back-signin">Girişe dön</button></p>';
      card.querySelector('#back-signin').addEventListener('click', () => renderAuth('signin'));
    } catch (ex) { err.textContent = ex.message; }
  });
}

function mountGoogle() {
  const slot = document.getElementById('gsi');
  if (!slot || !GOOGLE_CLIENT_ID) return;
  const render = () => {
    try {
      google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: async resp => {
          try {
            const out = await api('/auth/google', { method: 'POST', body: JSON.stringify({ credential: resp.credential }) });
            await onAuthed(out.access_token);
          } catch (ex) { toast(ex.message, true); }
        },
      });
      google.accounts.id.renderButton(slot, { theme: isDark() ? 'filled_black' : 'outline', size: 'large', text: 'continue_with', locale: 'tr', width: 280 });
    } catch { slot.closest('.auth-card')?.querySelector('.auth-alt')?.remove(); slot.remove(); }
  };
  if (window.google?.accounts?.id) return render();
  const s = document.createElement('script');
  s.src = 'https://accounts.google.com/gsi/client'; s.async = true;
  s.onload = render;
  s.onerror = () => { slot.closest('.auth-card')?.querySelector('.auth-alt')?.remove(); slot.remove(); };
  document.head.appendChild(s);
}

/* ---------- uygulama ---------- */
async function enterApp() {
  await Promise.all([loadSymbols(), loadTufe(), loadBench(), loadIpoMap()]);
  try {
    const [me, summary, history, watchlist, alerts, goals, txns] = await Promise.all([
      api('/auth/me'), api('/portfolio/summary'), api('/portfolio/history'),
      api('/portfolio/watchlist'), api('/portfolio/alerts'), api('/portfolio/goals'),
      api('/portfolio/transactions'),
    ]);
    state.user = me; state.summary = summary; state.history = history || [];
    state.watchlist = watchlist || []; state.alerts = alerts || []; state.goals = goals || [];
    state.txns = txns || [];
  } catch (ex) {
    if (token()) toast(ex.message, true);
    return renderAuth();
  }
  renderApp();
  clearInterval(state.refreshTimer);
  state.refreshTimer = setInterval(() => {
    if (document.visibilityState === 'visible') refreshData(true);
  }, 90000);
}

async function refreshData(silent) {
  if (state.demo) return;
  try {
    const [summary, history, watchlist, alerts, goals, txns] = await Promise.all([
      api('/portfolio/summary'), api('/portfolio/history'),
      api('/portfolio/watchlist'), api('/portfolio/alerts'), api('/portfolio/goals'),
      api('/portfolio/transactions'),
    ]);
    state.summary = summary; state.history = history || [];
    state.watchlist = watchlist || []; state.alerts = alerts || []; state.goals = goals || [];
    state.txns = txns || [];
    renderApp();
  } catch (ex) { if (!silent) toast(ex.message, true); }
}

function themeBtnHtml() {
  return `<button class="btn-icon" id="theme-btn" title="Tema değiştir" aria-label="Tema değiştir">
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
  </button>`;
}
function bindThemeBtn() {
  document.getElementById('theme-btn')?.addEventListener('click', cycleTheme);
}

const ICONS = {
  refresh: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 12a9 9 0 1 1-2.6-6.3M21 3v6h-6"/></svg>',
  eye: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>',
  share: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v7a1.5 1.5 0 0 0 1.5 1.5h13A1.5 1.5 0 0 0 20 19v-7M12 15V3m0 0L7.5 7.5M12 3l4.5 4.5"/></svg>',
  csv: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 3v12m0 0 4-4m-4 4-4-4M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/></svg>',
  bell: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 9a6 6 0 1 0-12 0c0 6-2.5 7-2.5 7h17S18 15 18 9Zm-4.3 10a2 2 0 0 1-3.4 0"/></svg>',
  x: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="m6 6 12 12M18 6 6 18"/></svg>',
  edit: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>',
  user: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-3.6 4.4-5 8-5s6.5 1.4 8 5"/></svg>',
  plus: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>',
  target: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1" fill="currentColor"/></svg>',
};

/* ---------- gezinme (mobil alt çubuk / masaüstü üst sekmeler) ---------- */
const NAV = [
  ['ozet', 'Özet', '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13h3l3-8 4 15 3-9h5"/></svg>'],
  ['varliklar', 'Varlıklar', '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><ellipse cx="12" cy="5.5" rx="8" ry="3"/><path d="M4 5.5v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6"/><path d="M4 11.5v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6"/></svg>'],
  ['takip', 'Takip', '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>'],
  ['analiz', 'Analiz', '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 20v-7M10 20V4M15 20v-9M20 20V8"/></svg>'],
];
function navHtml() {
  const tab = ([k, label, ic]) =>
    `<button class="tab${state.view === k ? ' on' : ''}" data-view="${k}" ${state.view === k ? 'aria-current="page"' : ''}>${ic}<span>${label}</span></button>`;
  return `<nav class="tabs" aria-label="Bölümler">
    ${NAV.slice(0, 2).map(tab).join('')}
    <button class="tab-add" id="nav-add" aria-label="Pozisyon ekle" title="Pozisyon ekle">${ICONS.plus}<span class="ta-label">Pozisyon ekle</span></button>
    ${NAV.slice(2).map(tab).join('')}
  </nav>`;
}
function miniBarHtml(s, U) {
  const d = s.total_day_change;
  return `<div class="minibar num" aria-label="Portföy özeti satırı">
    <span class="mb-total">${fmtU(s.total_value, U)}</span>
    ${d != null ? `<span class="${plClass(d)}">${signedU(d, U)} bugün</span>` : ''}
  </div>`;
}

function renderApp() {
  const s = state.summary, u = state.user;
  document.title = !state.demo && s.total_value != null && s.holdings.length
    ? nf0.format(s.total_value) + ' ₺ — ParaFOMO Portföy' : 'ParaFOMO Portföy';

  document.getElementById('bar-right').innerHTML = `
    ${themeBtnHtml()}
    ${state.demo ? '<button class="btn btn-quiet" id="exit-demo">Örnekten çık</button>' : `
    <div class="menu">
      <button class="btn-icon" id="user-btn" aria-haspopup="true" aria-expanded="false" aria-label="Hesap menüsü">${ICONS.user}</button>
      <ul class="menu-list" id="user-menu" hidden>
        <li class="who">${esc(u.display_name || u.email)}</li>
        <li><button id="account-btn">Hesap ayarları</button></li>
        <li><a href="/">Tüm uygulamalar</a></li>
        <li><a href="/kvkk/">Kullanım &amp; gizlilik</a></li>
        <li><button id="logout-btn">Çıkış yap</button></li>
      </ul>
    </div>`}`;
  bindThemeBtn();
  if (state.demo) {
    document.getElementById('exit-demo').addEventListener('click', () => { state.demo = false; renderAuth('signup'); });
  } else {
    const ub = document.getElementById('user-btn'), um = document.getElementById('user-menu');
    ub.addEventListener('click', () => { um.hidden = !um.hidden; ub.setAttribute('aria-expanded', String(!um.hidden)); });
    document.getElementById('logout-btn').addEventListener('click', () => logout());
    document.getElementById('account-btn').addEventListener('click', () => { um.hidden = true; openAccountDialog(); });
  }

  const main = document.getElementById('main');
  const demoBanner = state.demo ? `
    <div class="demo-banner">
      <span>Örnek görünümdesin — rakamlar temsilî. Beğendiysen 1 dakikada kendi portföyünü kur.</span>
      <button class="btn btn-primary" id="demo-signup">Ücretsiz kayıt ol</button>
    </div>` : '';

  if (!s.holdings.length && !state.txns.length && !state.watchlist.length) {
    main.classList.remove('masked');
    main.innerHTML = demoBanner + `
      <div class="empty">
        <h2>Portföyün henüz boş</h2>
        <p>İlk pozisyonunu ekle: bir hissenin adedini, altının gramını ya da gümüşünü.
        Gerisini biz hesaplayalım — güncel değer, değer grafiği, enflasyon sonrası gerçek kâr.</p>
        <button class="btn btn-primary" id="add-btn">Pozisyon ekle</button>
      </div>`;
    main.querySelector('#add-btn').addEventListener('click', () => openHoldingDialog());
    main.querySelector('#demo-signup')?.addEventListener('click', () => { state.demo = false; renderAuth('signup'); });
    return;
  }

  const masked = safeGet('pf_masked') === '1';
  main.classList.toggle('masked', masked);
  const U = unitRate(s);

  let body;
  if (state.view === 'varliklar') body = varliklarHtml(s, U);
  else if (state.view === 'takip') body = watchHtml() + alertsHtml();
  else if (state.view === 'analiz') body = analizHtml(s, U);
  else body = ozetHtml(s, U, masked);

  main.innerHTML = demoBanner + (state.view === 'ozet' ? '' : miniBarHtml(s, U)) + body + navHtml();

  // ortak bağlar
  main.querySelector('#demo-signup')?.addEventListener('click', () => { state.demo = false; renderAuth('signup'); });
  main.querySelectorAll('.tabs .tab').forEach(b => b.addEventListener('click', () => {
    if (state.view === b.dataset.view) return;
    state.view = b.dataset.view;
    renderApp();
    window.scrollTo(0, 0);
  }));
  main.querySelector('#nav-add')?.addEventListener('click', () => openHoldingDialog());
  main.querySelector('#add-btn')?.addEventListener('click', () => openHoldingDialog());

  if (state.view === 'ozet') {
    main.querySelectorAll('.unit-chips button').forEach(b => b.addEventListener('click', () => {
      state.unit = b.dataset.unit;
      safeSet('pf_unit', state.unit === 'try' ? null : state.unit);
      renderApp();
    }));
    main.querySelector('#mask-btn')?.addEventListener('click', () => {
      const now = safeGet('pf_masked') !== '1';
      safeSet('pf_masked', now ? '1' : null);
      main.classList.toggle('masked', now);
      main.querySelector('#mask-btn').setAttribute('aria-pressed', String(now));
    });
    main.querySelector('#refresh-btn')?.addEventListener('click', () => state.demo ? toast('Örnek modda fiyatlar temsilî.') : refreshData());
    main.querySelector('#share-btn')?.addEventListener('click', shareCard);
    bindChart();
    bindGoals();
  } else if (state.view === 'varliklar') {
    main.querySelector('#csv-btn')?.addEventListener('click', exportCsv);
    main.querySelectorAll('.hrow').forEach(r =>
      r.addEventListener('click', () => {
        const h = state.summary.holdings.find(x => x.id === Number(r.dataset.id));
        if (h) openDetailDialog(h);
      }));
    bindTxns();
  } else if (state.view === 'takip') {
    bindWatch();
    bindAlerts();
  }
}

/* ---------- görünümler ---------- */
function ozetHtml(s, U, masked) {
  if (!s.holdings.length) {
    return `<div class="empty">
      <h2>Portföyün henüz boş</h2>
      <p>İlk pozisyonunu ekle: bir hissenin adedini, altının gramını ya da dolarını.
      Gerisini biz hesaplayalım — güncel değer, değer grafiği, enflasyon sonrası gerçek kâr.</p>
      <button class="btn btn-primary" id="add-btn">Pozisyon ekle</button>
    </div>`;
  }
  const pricedAt = s.priced_at ? new Date(s.priced_at) : null;
  const timeStr = pricedAt ? pricedAt.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }) : '';
  const unitLabel = { try: '₺', usd: '$', gold: 'g' };
  const [lira, kurus] = U.nf.format((s.total_value ?? 0) / U.r).split(',');
  const equiv = [];
  if (state.unit !== 'try') equiv.push(nf0.format(s.total_value) + ' ₺');
  if (state.unit !== 'usd' && s.usd_try) equiv.push(nf0.format(s.total_value / s.usd_try) + ' $');
  if (state.unit !== 'gold' && s.gold_gram_try) equiv.push(nf1.format(s.total_value / s.gold_gram_try) + ' gram altın');
  return `
  <section class="hero" aria-label="Portföy özeti">
    <div class="hero-top">
      <span class="hero-label">Toplam değer</span>
      <span class="hero-tools">
        <span class="chips unit-chips" role="tablist" aria-label="Para birimi görünümü">
          ${['try', 'usd', 'gold'].filter(k => k === 'try' || (k === 'usd' ? s.usd_try : s.gold_gram_try)).map(k =>
            `<button role="tab" aria-selected="${state.unit === k}" data-unit="${k}" title="${k === 'try' ? 'Türk lirası' : k === 'usd' ? 'Dolar karşılığı' : 'Gram altın karşılığı'}">${unitLabel[k]}</button>`).join('')}
        </span>
        <button class="btn-icon" id="mask-btn" aria-pressed="${masked}" title="Tutarları gizle/göster" aria-label="Tutarları gizle/göster">${ICONS.eye}</button>
      </span>
    </div>
    <p class="hero-value num">${lira}<span class="kurus">${kurus != null ? ',' + kurus : ''}</span><span class="suf${state.unit === 'gold' ? ' gold' : ''}">${U.suf}${state.unit === 'gold' ? ' altın' : ''}</span></p>
    ${equiv.length ? `<p class="hero-equiv num">≈ ${equiv.join(' ya da ')}</p>` : ''}
    <div class="hero-stats num">
      <span>Bugün<b class="${plClass(s.total_day_change)}">${signedU(s.total_day_change, U)}${s.total_day_change_pct != null ? ' (' + signedPct(s.total_day_change_pct) + ')' : ''}</b></span>
      <span>Toplam kâr/zarar<b class="${plClass(s.total_profit_loss)}">${signedU(s.total_profit_loss, U)} (${signedPct(s.total_profit_loss_pct)})</b></span>
    </div>
    <div class="hero-meta">
      <span>Fiyatlar ${timeStr} itibarıyla · reel getiri ve kıyas Analiz'de</span>
      <span class="hero-mtools">
        <button class="btn-icon" id="refresh-btn" title="Fiyatları yenile" aria-label="Fiyatları yenile">${ICONS.refresh}</button>
        <button class="btn-icon" id="share-btn" title="Portföy kartını paylaş (tutarsız, sadece yüzdeler)" aria-label="Portföy kartını paylaş">${ICONS.share}</button>
      </span>
    </div>
  </section>
  ${chartHtml()}
  <section class="alloc-sec" aria-label="Dağılım">
    <div class="holdings-head"><h2>Dağılım</h2></div>
    ${allocHtml(s, U)}
  </section>
  <section class="goals-sec" aria-label="Hedefler">
    <div class="holdings-head"><h2>Hedefler</h2></div>
    ${goalsHtml(s)}
  </section>`;
}

function varliklarHtml(s, U) {
  const pos = s.holdings.length ? `
    <section class="holdings" aria-label="Pozisyonlar">
      <div class="holdings-head">
        <h2>Pozisyonlar</h2>
        <div class="tools">
          <button class="btn-icon" id="csv-btn" title="CSV indir" aria-label="Pozisyonları CSV olarak indir">${ICONS.csv}</button>
        </div>
      </div>
      <div class="hhead" aria-hidden="true">
        <span>Varlık</span><span class="r">Adet / gram</span><span class="r">Güncel</span><span class="r">Değer</span><span class="r">Kâr/zarar</span><span></span>
      </div>
      <div id="hlist">${s.holdings.slice().sort((a, b) => (b.current_value ?? b.cost_value) - (a.current_value ?? a.cost_value)).map(h => rowHtml(h, s.total_value, U)).join('')}</div>
    </section>` : `
    <div class="empty">
      <h2>Henüz pozisyon yok</h2>
      <p>İlk pozisyonunu ekle: bir hissenin adedini, altının gramını ya da dolarını.</p>
      <button class="btn btn-primary" id="add-btn">Pozisyon ekle</button>
    </div>`;
  return pos + txnsHtml();
}

/* ---------- içerik köprüsü: sahip olunan varlığa göre parafomo.com veri sayfaları ---------- */
const SITE = 'https://parafomo.com';
const relUrl = (path, campaign = 'ilgili-veri') =>
  `${SITE}${path}?utm_source=app&utm_medium=portfoy&utm_campaign=${campaign}`;
const RELATED = {
  gold:   [['/altin-getiri/', 'Altın getirisi', 'Yıllara göre TL ve dolar bazında getiri'],
           ['/altin-hesaplama/', 'Altın hesaplama', 'Gram, çeyrek, bilezik bugün kaç TL']],
  silver: [['/gumus-getiri/', 'Gümüş getirisi', 'Yıllara göre TL bazında getiri']],
  bist:   [['/bist-getiri/', 'BIST 100 getirisi', 'Endeksin yıllara göre getirisi'],
           ['/halka-arz/', 'Halka arz takvimi', 'Süren ve yaklaşan arzlar, ilk gün getirileri']],
  usd:    [['/dolar-getiri/', 'Dolar getirisi', 'Doların yıllara göre TL getirisi']],
  eur:    [['/euro-getiri/', 'Euro getirisi', 'Euronun yıllara göre TL getirisi']],
  btc:    [['/bitcoin-getiri/', 'Bitcoin getirisi', 'Yıllara göre TL bazında getiri']],
  cash:   [['/mevduat-faizi-hesaplama/', 'Güncel mevduat faizleri', 'Nakdin bankada ne kazanır (TCMB, haftalık)']],
};
function ipoLink(symbol) {
  const slug = state.ipoMap && state.ipoMap[symbol];
  return slug ? [`/halka-arz/${slug}/`, `${symbol} halka arz sayfası`, 'Arz fiyatı, ilk gün ve güncel getiri'] : null;
}
function relatedHtml(s) {
  const types = [...new Set(s.holdings.map(h => h.asset_type))];
  const cards = [];
  const seen = new Set();
  for (const t of types) for (const r of (RELATED[t] || [])) if (!seen.has(r[0])) { seen.add(r[0]); cards.push([t, ...r]); }
  for (const h of s.holdings.filter(h => h.asset_type === 'bist')) {
    const r = ipoLink(h.symbol);
    if (r && !seen.has(r[0])) { seen.add(r[0]); cards.push(['bist', ...r]); }
  }
  if (!cards.length) return '';
  return `<section class="related" aria-label="İlgili veri">
    <div class="holdings-head"><h2>İlgili veri</h2></div>
    <p class="bench-sub">Portföyündeki varlıklar için ParaFOMO'daki güncel tablolar ve hesaplayıcılar.</p>
    <div class="rel-grid">${cards.map(([t, path, title, sub]) => `
      <a class="rel-card" href="${relUrl(path)}" target="_blank" rel="noopener">
        <span class="tick tick-${TYPE[t].cls}">${esc(TYPE[t].label)}</span>
        <b>${esc(title)}</b><span>${esc(sub)}</span>
      </a>`).join('')}
    </div>
  </section>`;
}

function analizHtml(s, U) {
  if (!s.holdings.length) {
    return `<section class="analiz" aria-label="Analiz">
      <div class="holdings-head"><h2>Analiz</h2></div>
      <p class="analiz-empty">Analiz için önce bir pozisyon ekle — reel getiri, yıllık iç verim ve "ne olsaydı" kıyası burada toplanır.</p>
    </section>`;
  }
  const stat = (l, v, cls = '', title = '', m = true) =>
    `<div class="stat"${title ? ` title="${title}"` : ''}><span>${l}</span><b class="num ${m ? 'm ' : ''}${cls}">${v}</b></div>`;
  const bits = [];
  bits.push(stat('Toplam kâr/zarar', `${signedU(s.total_profit_loss, U)} (${signedPct(s.total_profit_loss_pct)})`, plClass(s.total_profit_loss)));
  const rr = realReturn(s);
  if (rr && rr.dated) {
    bits.push(stat('Enflasyon sonrası (reel)', `${(rr.undated || rr.partial) ? '≈ ' : ''}${signedU(rr.pl, U)} (${signedPct(rr.pct)})`, plClass(rr.pl),
      `Maliyetin, alış tarihinden bugüne TÜİK TÜFE ile bugünkü liraya çevrilmiş hâline göre kâr/zarar.${rr.undated ? ' Alış tarihi olmayan ' + rr.undated + ' pozisyon düzeltilmeden katıldı.' : ''}${rr.partial ? ' Çok eski alışlarda TÜFE serisi ' + (state.tufe[0] ? state.tufe[0][0] : '') + ' başlangıçlı.' : ''}`));
  } else {
    bits.push(stat('Enflasyon sonrası (reel)', 'alış tarihi ekle', 'pl-flat',
      'Pozisyonlarına alış tarihi eklersen maliyetini TÜFE ile bugüne taşıyıp gerçek (reel) kârını gösteririz.', false));
  }
  const x = portfolioXirr(s);
  if (x != null && Math.abs(x) < 500)
    bits.push(stat('Yıllık iç verim (XIRR)', signedPct1(x), plClass(x),
      'Para-ağırlıklı yıllık getiri: işlem defterindeki tüm giriş-çıkışlar ve bugünkü değere göre.', false));
  const hist = state.history;
  if (hist.length >= 8) {
    const last = hist[hist.length - 1];
    const cutoff = new Date(Date.now() - 7 * 864e5).toISOString().slice(0, 10);
    const base = [...hist].reverse().find(p => p.day <= cutoff) || hist[0];
    if (base && base.total_value > 0)
      bits.push(stat('Son 7 gün', signedPct1((last.total_value / base.total_value - 1) * 100), plClass(last.total_value - base.total_value), '', false));
  }
  const ranked = s.holdings.filter(h => h.profit_loss_pct != null)
    .sort((a, b) => b.profit_loss_pct - a.profit_loss_pct);
  if (ranked.length >= 2) {
    const best = ranked[0], worst = ranked[ranked.length - 1];
    bits.push(stat('En iyi pozisyon', `${esc(TYPE[best.asset_type].tick(best.symbol))} ${signedPct1(best.profit_loss_pct)}`, 'pl-gain', '', false));
    if (worst.profit_loss_pct < 0)
      bits.push(stat('En zayıf pozisyon', `${esc(TYPE[worst.asset_type].tick(worst.symbol))} ${signedPct1(worst.profit_loss_pct)}`, 'pl-loss', '', false));
  }
  if (s.realized_pl_total)
    bits.push(stat('Realize (satışlardan)', signedU(s.realized_pl_total, U), plClass(s.realized_pl_total),
      `Satışlardan realize edilen kâr/zarar (ortalama maliyete göre). Bu yıl: ${signedMoney(s.realized_pl_year)}`));
  return `<section class="analiz" aria-label="Analiz">
    <div class="holdings-head"><h2>Analiz</h2></div>
    <div class="a-stats">${bits.join('')}</div>
    ${benchHtml(s)}
  </section>
  ${relatedHtml(s)}`;
}

/* ---------- XIRR (para-ağırlıklı yıllık getiri) ---------- */
function xirr(flows) {
  if (flows.length < 2) return null;
  const t0 = flows[0].t, YEAR = 31557600000;
  const f = r => flows.reduce((a, x) => a + x.v / Math.pow(1 + r, (x.t - t0) / YEAR), 0);
  let lo = -0.95, hi = 9, flo = f(lo), fhi = f(hi);
  if (!isFinite(flo) || !isFinite(fhi) || flo * fhi > 0) return null;
  for (let i = 0; i < 90; i++) {
    const m = (lo + hi) / 2, fm = f(m);
    if (flo * fm <= 0) { hi = m; fhi = fm; } else { lo = m; flo = fm; }
  }
  return (lo + hi) / 2 * 100;
}
function portfolioXirr(s) {
  if (!state.txns.length || s.total_value == null) return null;
  const flows = state.txns.map(x => ({
    t: new Date((x.trade_date || (x.created_at || '').slice(0, 10) || '') + 'T12:00:00').getTime(),
    v: x.side === 'buy' ? -x.quantity * x.price : x.quantity * x.price,
  })).filter(x => isFinite(x.t)).sort((a, b) => a.t - b.t);
  if (!flows.length) return null;
  if (Date.now() - flows[0].t < 45 * 864e5) return null; // kısa geçmişte yıllıklaştırma yanıltır
  flows.push({ t: Date.now(), v: s.total_value });
  return xirr(flows);
}

/* ---------- hedefler ---------- */
function goalProgress(g, s) {
  if (!s.total_value) return null;
  if (g.kind === 'try') return { cur: s.total_value };
  if (g.kind === 'usd') return s.usd_try ? { cur: s.total_value / s.usd_try } : null;
  if (g.kind === 'gold_g') return s.gold_gram_try ? { cur: s.total_value / s.gold_gram_try } : null;
  return null;
}
function goalsHtml(s) {
  const items = state.goals;
  const addBtn = items.length < 3
    ? `<button class="goal-add" id="goal-add">${ICONS.target} <b>Hedef ${items.length ? 'ekle' : 'koy'}</b> <span>— "100 gram altın" ya da "1 milyon ₺" gibi</span></button>`
    : '';
  if (!items.length) return `<div class="goals">${addBtn}</div>`;
  return `<div class="goals">
    ${items.map(g => {
      const k = GOAL_KIND[g.kind] || GOAL_KIND.try;
      const p = goalProgress(g, s);
      const pct = p ? Math.min(100, p.cur / g.target * 100) : null;
      return `<div class="goal num" data-id="${g.id}">
        <div class="goal-top">
          <span class="goal-name">${esc(g.title || 'Hedef')} <small>· ${k.fmt(g.target)}</small></span>
          <span class="goal-pct">${pct != null ? '%' + nf0.format(pct) : '—'}
            <button class="goal-del" data-id="${g.id}" title="Hedefi sil" aria-label="Hedefi sil">${ICONS.x}</button></span>
        </div>
        <div class="goal-bar" role="img" aria-label="İlerleme ${pct != null ? '%' + nf0.format(pct) : 'bilinmiyor'}">
          <span style="width:${pct ?? 0}%"></span>
        </div>
        ${p ? `<div class="goal-sub">şu an ${k.fmt(p.cur)}</div>` : ''}
      </div>`;
    }).join('')}
    ${addBtn}
  </div>`;
}
function bindGoals() {
  document.getElementById('goal-add')?.addEventListener('click', openGoalDialog);
  document.querySelectorAll('.goal-del').forEach(b => b.addEventListener('click', async e => {
    e.stopPropagation();
    if (state.demo) return demoNudge();
    try {
      await api('/portfolio/goals/' + b.dataset.id, { method: 'DELETE' });
      state.goals = state.goals.filter(g => g.id !== Number(b.dataset.id));
      renderApp();
    } catch (ex) { toast(ex.message, true); }
  }));
}
function openGoalDialog() {
  document.getElementById('goal-dlg')?.remove();
  const dlg = document.createElement('dialog');
  dlg.id = 'goal-dlg';
  dlg.innerHTML = `
    <div class="dlg-head"><h2>Hedef koy</h2>
      <button class="btn-icon" id="gdlg-x" aria-label="Kapat">${ICONS.x}</button></div>
    <form id="goal-form">
      <div class="seg" role="radiogroup" aria-label="Hedef türü">
        <label><input type="radio" name="kind" value="try" checked><span>₺ değer</span></label>
        <label><input type="radio" name="kind" value="gold_g"><span>Gram altın</span></label>
        <label><input type="radio" name="kind" value="usd"><span>Dolar</span></label>
      </div>
      <label class="field"><span>Hedef tutar</span>
        <input name="target" type="number" step="any" min="1" required inputmode="decimal" placeholder="1000000"></label>
      <label class="field"><span>Ad (isteğe bağlı)</span>
        <input name="title" maxlength="80" placeholder="Ev peşinatı, düğün, yüz gram…"></label>
      <p class="form-error" id="gdlg-err" role="alert"></p>
      <div class="dlg-actions"><span class="grow"></span>
        <button type="button" class="btn btn-quiet" id="gdlg-cancel">Vazgeç</button>
        <button type="submit" class="btn btn-primary">Hedefi kaydet</button>
      </div>
    </form>`;
  document.body.appendChild(dlg);
  dlg.showModal();
  dlg.addEventListener('close', () => dlg.remove());
  dlg.querySelector('#gdlg-x').addEventListener('click', () => dlg.close());
  dlg.querySelector('#gdlg-cancel').addEventListener('click', () => dlg.close());
  dlg.querySelector('#goal-form').addEventListener('submit', async e => {
    e.preventDefault();
    if (state.demo) { dlg.close(); return demoNudge(); }
    const err = dlg.querySelector('#gdlg-err');
    try {
      const g = await api('/portfolio/goals', { method: 'POST', body: JSON.stringify({
        kind: e.target.kind.value,
        target: parseFloat(e.target.target.value.replace(',', '.')),
        title: e.target.title.value.trim() || null,
      })});
      state.goals.push(g);
      dlg.close();
      renderApp();
    } catch (ex) { err.textContent = ex.message; }
  });
}

/* ---------- değer grafiği ---------- */
const CH = { w: 720, h: 190, l: 10, r: 64, t: 14, b: 26 };
function filteredHistory() {
  const all = state.history || [];
  if (state.chartRange === 'all') return all;
  const days = state.chartRange === '1a' ? 31 : 92;
  const cutoff = new Date(Date.now() - days * 864e5).toISOString().slice(0, 10);
  return all.filter(p => p.day >= cutoff);
}
function chartHtml() {
  const all = state.history || [];
  if (all.length < 2) {
    return `<section class="chart chart-empty" aria-label="Değer grafiği">
      <p>Değer grafiğin burada çizilecek — portföyünü her gün kapanışta kaydediyoruz,
      yarından itibaren çizgi oluşmaya başlar.</p></section>`;
  }
  const hist = filteredHistory();
  if (hist.length < 2) { state.chartRange = 'all'; return chartHtml(); }
  const vs = hist.map(p => p.total_value);
  let min = Math.min(...vs), max = Math.max(...vs);
  // maliyet çizgisi makul banttaysa eksene dahil et (yoksa görünmez kalır)
  const cs = hist.map(p => p.total_cost);
  const cmin = Math.min(...cs), cmax = Math.max(...cs);
  if (cmin >= min * 0.6 && cmax <= max * 1.4) { min = Math.min(min, cmin); max = Math.max(max, cmax); }
  const span = (max - min) || max * 0.05 || 1;
  const x = i => CH.l + (CH.w - CH.l - CH.r) * (i / (hist.length - 1));
  const y = v => CH.t + (CH.h - CH.t - CH.b) * (1 - (v - min + span * 0.08) / (span * 1.16));
  const pts = vs.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`);
  const line = 'M' + pts.join(' L');
  const area = line + ` L${x(vs.length - 1).toFixed(1)},${CH.h - CH.b} L${x(0).toFixed(1)},${CH.h - CH.b} Z`;
  // kesikli maliyet çizgisi: yatırdığın toplam (görünür aralığa kırpılmış)
  const costPath = 'M' + hist.map((p, i) =>
    `${x(i).toFixed(1)},${Math.min(CH.h - CH.b, Math.max(CH.t, y(p.total_cost))).toFixed(1)}`).join(' L');
  const last = hist[hist.length - 1], first = hist[0];
  const period = last.total_value - first.total_value;
  const chips = all.length > 32 ? `
    <span class="chips" role="tablist" aria-label="Dönem">
      ${[['1a', '1A'], ['3a', '3A'], ['all', 'Tümü']].map(([k, l]) =>
        `<button role="tab" aria-selected="${state.chartRange === k}" data-range="${k}">${l}</button>`).join('')}
    </span>` : '';
  return `<section class="chart" aria-label="Değer grafiği">
    <div class="chart-head">
      <h2>Değer grafiği</h2>
      <span class="chart-tools">${chips}<span class="chart-sub num">${trDate(first.day)} – ${trDate(last.day)} · <b class="${plClass(period)}">${signedMoney(period)}</b> · <small>kesikli: maliyet</small></span></span>
    </div>
    <div class="chart-box">
      <svg viewBox="0 0 ${CH.w} ${CH.h}" preserveAspectRatio="none" role="img" aria-label="Portföy değerinin günlük seyri">
        <path class="c-area" d="${area}"/>
        <path class="c-paid" d="${costPath}" vector-effect="non-scaling-stroke"/>
        <path class="c-line" d="${line}" vector-effect="non-scaling-stroke"/>
        <line class="c-cross" x1="0" x2="0" y1="${CH.t}" y2="${CH.h - CH.b}" visibility="hidden"/>
        <circle class="c-dot" r="4.5" visibility="hidden"/>
        <text class="yv num" x="${CH.w - 6}" y="${y(max) + 4}" text-anchor="end">${nfc.format(max)} ₺</text>
        <text class="yv num" x="${CH.w - 6}" y="${y(min) + 4}" text-anchor="end">${nfc.format(min)} ₺</text>
      </svg>
      <div class="c-tip num" hidden></div>
    </div>
  </section>`;
}
function bindChart() {
  const sec = document.querySelector('.chart');
  if (!sec) return;
  sec.querySelectorAll('.chips button').forEach(b => b.addEventListener('click', () => {
    state.chartRange = b.dataset.range;
    renderApp();
  }));
  const box = sec.querySelector('.chart-box');
  if (!box) return;
  const svg = box.querySelector('svg'), tip = box.querySelector('.c-tip');
  const cross = svg.querySelector('.c-cross'), dot = svg.querySelector('.c-dot');
  const hist = filteredHistory();
  const vs = hist.map(p => p.total_value);
  let min = Math.min(...vs), max = Math.max(...vs);
  // maliyet çizgisi makul banttaysa eksene dahil et (yoksa görünmez kalır)
  const cs = hist.map(p => p.total_cost);
  const cmin = Math.min(...cs), cmax = Math.max(...cs);
  if (cmin >= min * 0.6 && cmax <= max * 1.4) { min = Math.min(min, cmin); max = Math.max(max, cmax); }
  const span = (max - min) || max * 0.05 || 1;
  const xOf = i => CH.l + (CH.w - CH.l - CH.r) * (i / (hist.length - 1));
  const yOf = v => CH.t + (CH.h - CH.t - CH.b) * (1 - (v - min + span * 0.08) / (span * 1.16));
  function show(clientX) {
    const rect = svg.getBoundingClientRect();
    const fx = (clientX - rect.left) / rect.width * CH.w;
    const i = Math.max(0, Math.min(hist.length - 1,
      Math.round((fx - CH.l) / (CH.w - CH.l - CH.r) * (hist.length - 1))));
    const p = hist[i], px = xOf(i), py = yOf(p.total_value);
    cross.setAttribute('x1', px); cross.setAttribute('x2', px); cross.setAttribute('visibility', 'visible');
    dot.setAttribute('cx', px); dot.setAttribute('cy', py); dot.setAttribute('visibility', 'visible');
    tip.hidden = false;
    tip.innerHTML = `<b>${trDate(p.day)}</b><br>Değer ${money(p.total_value)}<br><span>Maliyet ${money(p.total_cost)}</span>`;
    const bx = px / CH.w * rect.width;
    tip.style.left = Math.max(4, Math.min(rect.width - tip.offsetWidth - 4, bx - tip.offsetWidth / 2)) + 'px';
  }
  function hide() { cross.setAttribute('visibility', 'hidden'); dot.setAttribute('visibility', 'hidden'); tip.hidden = true; }
  box.addEventListener('pointermove', e => show(e.clientX));
  box.addEventListener('pointerdown', e => show(e.clientX));
  box.addEventListener('pointerleave', hide);
}

/* ---------- "ne olsaydı" kıyası ---------- */
function benchHtml(s) {
  const b = benchReturn(s);
  if (!b) return '';
  const rows = [
    { key: 'user', label: 'Senin portföyün', v: b.user, me: true },
    { key: 'gold', label: 'Hepsi gram altında', v: b.gold },
    { key: 'xu100', label: 'Hepsi BIST 100\'de', v: b.xu100 },
    { key: 'usd', label: 'Hepsi dolarda', v: b.usd },
  ];
  if (b.tufe != null) rows.push({ key: 'tufe', label: 'Enflasyon (TÜFE)', v: b.tufe, dim: true });
  const maxAbs = Math.max(...rows.map(r => Math.abs(r.v)), 1);
  return `<section class="bench" aria-label="Ne olsaydı kıyası">
    <div class="holdings-head"><h2>Ne olsaydı?</h2></div>
    <p class="bench-sub">Alış tarihli ${b.n} pozisyonunun maliyeti, aynı tarihlerde tek bir varlığa gitseydi:${b.excluded ? ` <span title="Kıyas serisi dışında kalan ${b.excluded} pozisyon hariç.">(${b.excluded} pozisyon hariç)</span>` : ''}</p>
    <div class="bench-rows num">
      ${rows.map(r => `
        <div class="bench-row${r.me ? ' me' : ''}${r.dim ? ' dim' : ''}">
          <span class="bench-label">${r.label}</span>
          <span class="bench-track"><span class="bench-fill" style="width:${(Math.abs(r.v) / maxAbs * 100).toFixed(1)}%"></span></span>
          <b class="${plClass(r.v)}">${signedPct1(r.v)}</b>
        </div>`).join('')}
    </div>
  </section>`;
}

function allocHtml(s, U) {
  const sums = {};
  for (const h of s.holdings) {
    const k = ALLOC_CLASS[h.asset_type] || 'bist';
    sums[k] = (sums[k] || 0) + (h.current_value ?? h.cost_value ?? 0);
  }
  const total = Object.values(sums).reduce((a, b) => a + b, 0);
  if (!total) return '';
  const order = ALLOC_META.filter(([k]) => sums[k] > 0);
  return `<div class="alloc">
    <div class="alloc-bar" role="img" aria-label="Dağılım: ${order.map(([k, l]) => l + ' %' + nf0.format(sums[k] / total * 100)).join(', ')}">
      ${order.map(([k, l]) => `<span class="f-${k}" style="flex:${(sums[k] / total * 1000).toFixed(0)}" title="${l}: ${money(sums[k])}"></span>`).join('')}
    </div>
    <div class="alloc-legend num">
      ${order.map(([k, l]) => `<span><span class="dot d-${k}" style="background:var(--a-${k})"></span>${l} <b>${fmtU(sums[k], U)}</b><span class="pct">%${nf0.format(sums[k] / total * 100)}</span></span>`).join('')}
    </div>
  </div>`;
}

function rowHtml(h, totalValue, U) {
  const t = TYPE[h.asset_type];
  const isCash = h.asset_type === 'cash';
  const dayStr = !isCash && h.change_pct != null ? signedPct(h.change_pct) : '';
  const w = totalValue && h.current_value != null ? h.current_value / totalValue * 100 : null;
  return `
  <button class="hrow num" data-id="${h.id}" title="Detay ve grafik için tıkla">
    <span class="asset c-asset">
      <span class="tick tick-${t.cls}">${esc(t.tick(h.symbol))}</span>
      <span class="aname"><b>${esc(t.name(h.symbol))}</b>${h.note ? `<small>${esc(h.note)}</small>` : ''}</span>
    </span>
    <span class="r c-qty"><span class="cell-main">${nfq.format(h.quantity)} ${t.unit}</span>${isCash ? '' : `<span class="cell-sub">maliyet ${money(h.cost_price)}</span>`}</span>
    <span class="r c-price">${isCash ? '' : `<span class="cell-main">${money(h.current_price)}</span><span class="cell-sub ${plClass(h.change_pct)}">${dayStr}</span>`}</span>
    <span class="r c-value"><span class="cell-main">${fmtU(h.current_value, U)}</span>${w != null ? `<span class="cell-sub" title="Portföydeki payı">pay %${nf0.format(w)}</span>` : ''}</span>
    <span class="r c-pl">${isCash ? '<span class="pl-flat">—</span>' : `<span class="${plClass(h.profit_loss)}">${signedU(h.profit_loss, U)}</span><span class="cell-sub ${plClass(h.profit_loss)}">${h.profit_loss_pct != null ? signedPct(h.profit_loss_pct) : ''}</span>`}</span>
    <span class="edit-ic" aria-hidden="true">${ICONS.edit}</span>
  </button>`;
}

/* ---------- varlık detayı (grafikli) ---------- */
function openDetailDialog(h) {
  document.getElementById('detail-dlg')?.remove();
  const t = TYPE[h.asset_type];
  const isBist = h.asset_type === 'bist';
  const ranges = isBist ? [['3mo', '3A'], ['1y', '1Y'], ['5y', '5Y']] : [['1y', '1Y'], ['5y', '5Y']];
  let range = isBist ? '1y' : '5y';
  const histQ = isBist ? '&symbol=' + encodeURIComponent(h.symbol) : '';
  const dlg = document.createElement('dialog');
  dlg.id = 'detail-dlg';
  dlg.className = 'dlg-wide';
  const stat = (l, v, cls = '') => `<div class="stat"><span>${l}</span><b class="num ${cls}">${v}</b></div>`;
  dlg.innerHTML = `
    <div class="dlg-head">
      <h2><span class="tick tick-${t.cls}">${esc(t.tick(h.symbol))}</span> <span style="margin-left:6px">${esc(t.name(h.symbol))}</span></h2>
      <button class="btn-icon" id="ddlg-x" aria-label="Kapat">${ICONS.x}</button>
    </div>
    <div class="stats">
      ${stat('Miktar', nfq.format(h.quantity) + ' ' + t.unit)}
      ${stat('Birim maliyet', money(h.cost_price))}
      ${stat('Güncel fiyat', money(h.current_price))}
      ${stat('Değer', money(h.current_value))}
      ${stat('Kâr/zarar', signedMoney(h.profit_loss) + (h.profit_loss_pct != null ? ' (' + signedPct(h.profit_loss_pct) + ')' : ''), plClass(h.profit_loss))}
      ${stat('Bugün', h.change_pct != null ? signedPct(h.change_pct) : '—', plClass(h.change_pct))}
    </div>
    <div class="detail-chart" ${h.asset_type === 'cash' ? 'hidden' : ''}>
      <div class="chart-head">
        <span class="chart-sub" id="dch-sub">Fiyat geçmişi yükleniyor…</span>
        <span class="chips" role="tablist" aria-label="Dönem">
          ${ranges.map(([k, l]) => `<button role="tab" aria-selected="${range === k}" data-range="${k}">${l}</button>`).join('')}
        </span>
      </div>
      <div class="chart-box" id="dch-box"></div>
    </div>
    <div class="dnews" id="dnews" hidden></div>
    ${(() => {
      const links = [...(RELATED[h.asset_type] || []).slice(0, 1), ...(isBist && ipoLink(h.symbol) ? [ipoLink(h.symbol)] : [])];
      return links.length ? `<p class="drel">ParaFOMO'da: ${links.map(([p, t]) =>
        `<a href="${relUrl(p, 'detay')}" target="_blank" rel="noopener">${esc(t)} →</a>`).join(' · ')}</p>` : '';
    })()}
    <div class="dlg-actions">
      ${h.asset_type !== 'cash' ? `<button type="button" class="btn-icon" id="ddlg-alert" title="Fiyat alarmı kur" aria-label="Fiyat alarmı kur">${ICONS.bell}</button>` : ''}
      <span class="grow"></span>
      <button type="button" class="btn btn-quiet" id="ddlg-sell">Sat</button>
      <button type="button" class="btn btn-quiet" id="ddlg-edit">Düzenle</button>
      <button type="button" class="btn btn-primary" id="ddlg-close">Kapat</button>
    </div>`;
  document.body.appendChild(dlg);
  dlg.showModal();
  dlg.addEventListener('close', () => dlg.remove());
  dlg.querySelector('#ddlg-x').addEventListener('click', () => dlg.close());
  dlg.querySelector('#ddlg-close').addEventListener('click', () => dlg.close());
  dlg.querySelector('#ddlg-edit').addEventListener('click', () => { dlg.close(); openHoldingDialog(h); });
  dlg.querySelector('#ddlg-sell').addEventListener('click', () => { dlg.close(); openSellDialog(h); });
  dlg.querySelector('#ddlg-alert')?.addEventListener('click', () => { dlg.close(); openAlertDialog(h.asset_type, h.symbol, h.current_price); });

  async function loadNews() {
    if (h.asset_type === 'cash') return;
    try {
      const q = h.asset_type === 'bist'
        ? '&symbol=' + encodeURIComponent(h.symbol) + '&name=' + encodeURIComponent(TYPE.bist.name(h.symbol))
        : '';
      const r = await (await fetch(API_BASE + '/public/news?asset_type=' + h.asset_type + q)).json();
      if (!r.items || !r.items.length) return;
      const el = dlg.querySelector('#dnews');
      el.hidden = false;
      el.innerHTML = '<h3>İlgili haberler</h3>' + r.items.map(n =>
        `<a href="${esc(n.u)}" target="_blank" rel="noopener">${esc(n.t)}<small>${esc((n.d || '').slice(5, 16))}</small></a>`).join('');
    } catch {}
  }
  async function load() {
    const box = dlg.querySelector('#dch-box'), sub = dlg.querySelector('#dch-sub');
    if (h.asset_type === 'cash') return;
    if (h.asset_type === 'eth') {
      box.innerHTML = '<p class="dch-note">Ethereum fiyat grafiği yakında — canlı fiyat ve alarm çalışıyor.</p>';
      sub.textContent = '';
      return;
    }
    box.innerHTML = '<p class="dch-note">Yükleniyor…</p>';
    try {
      const r = await (await fetch(API_BASE + '/public/history?asset_type=' + h.asset_type + histQ + '&range=' + range)).json();
      if (!r.points || r.points.length < 2) throw 0;
      drawMini(box, r.points, h);
      const f = r.points[0], l = r.points[r.points.length - 1];
      const chg = (l.p / f.p - 1) * 100;
      const span = f.t.slice(0, 4) !== l.t.slice(0, 4);   // yıl değişiyorsa yılı göster
      const fmt = iso => span
        ? new Date((iso.length === 7 ? iso + '-15' : iso) + 'T12:00:00').toLocaleDateString('tr-TR', { month: 'short', year: 'numeric' })
        : trDate(iso);
      sub.innerHTML = `${fmt(f.t)} – ${fmt(l.t)} · <b class="num ${plClass(chg)}">${signedPct1(chg)}</b>${r.granularity === 'monthly' ? ' <small>(aylık)</small>' : ''}`;
    } catch {
      box.innerHTML = '<p class="dch-note">Geçmiş veri şu an alınamadı.</p>';
      sub.textContent = '';
    }
  }
  dlg.querySelectorAll('.chips button').forEach(b => b.addEventListener('click', () => {
    range = b.dataset.range;
    dlg.querySelectorAll('.chips button').forEach(x => x.setAttribute('aria-selected', String(x === b)));
    load();
  }));
  load();
  loadNews();
}

function drawMini(box, points, h) {
  const W = 640, H = 170, L = 8, R = 58, T = 12, B = 22;
  const vs = points.map(p => p.p);
  let min = Math.min(...vs), max = Math.max(...vs);
  if (h.cost_price >= min * 0.7 && h.cost_price <= max * 1.3) {
    min = Math.min(min, h.cost_price); max = Math.max(max, h.cost_price);
  }
  const span = (max - min) || max * 0.05 || 1;
  const x = i => L + (W - L - R) * (i / (points.length - 1));
  const y = v => T + (H - T - B) * (1 - (v - min + span * 0.08) / (span * 1.16));
  const line = 'M' + vs.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' L');
  const costIn = h.cost_price >= min && h.cost_price <= max;
  // alış noktası: tarih aralıktaysa işaretle
  let buyDot = '';
  if (h.purchase_date) {
    const pd = h.purchase_date.slice(0, points[0].t.length);
    const bi = points.findIndex(p => p.t >= pd);
    if (bi > 0) buyDot = `<circle class="c-buy" cx="${x(bi)}" cy="${y(h.cost_price)}" r="4.5"><title>Alış: ${trDate(h.purchase_date)} · ${money(h.cost_price)}</title></circle>`;
  }
  // etiket çarpışmalarını önle: maliyet çizgisi min/max'a çok yakınsa o ucu gizle
  const yc = costIn ? y(h.cost_price) : null;
  const showMax = yc == null || Math.abs(yc - y(max)) > 14;
  const showMin = yc == null || Math.abs(yc - y(min)) > 14;
  box.innerHTML = `
    <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Fiyat geçmişi">
      <path class="c-line" d="${line}" vector-effect="non-scaling-stroke"/>
      ${costIn ? `<line class="c-cost" x1="${L}" x2="${W - R}" y1="${yc}" y2="${yc}"/>
      <text class="yv num" x="${W - 6}" y="${yc + 4}" text-anchor="end">maliyet</text>` : ''}
      ${buyDot}
      <line class="c-cross" x1="0" x2="0" y1="${T}" y2="${H - B}" visibility="hidden"/>
      <circle class="c-dot" r="4" visibility="hidden"/>
      ${showMax ? `<text class="yv num" x="${W - 6}" y="${y(max) + 4}" text-anchor="end">${nfc.format(max)}</text>` : ''}
      ${showMin ? `<text class="yv num" x="${W - 6}" y="${y(min) + 4}" text-anchor="end">${nfc.format(min)}</text>` : ''}
    </svg>
    <div class="c-tip num" hidden></div>`;
  const svg = box.querySelector('svg'), tip = box.querySelector('.c-tip');
  const cross = svg.querySelector('.c-cross'), dot = svg.querySelector('.c-dot');
  function show(clientX) {
    const rect = svg.getBoundingClientRect();
    const fx = (clientX - rect.left) / rect.width * W;
    const i = Math.max(0, Math.min(points.length - 1, Math.round((fx - L) / (W - L - R) * (points.length - 1))));
    const p = points[i], px = x(i), py = y(p.p);
    cross.setAttribute('x1', px); cross.setAttribute('x2', px); cross.setAttribute('visibility', 'visible');
    dot.setAttribute('cx', px); dot.setAttribute('cy', py); dot.setAttribute('visibility', 'visible');
    tip.hidden = false;
    tip.innerHTML = `<b>${trDate(p.t)}</b><br>${money(p.p)}`;
    const bx = px / W * rect.width;
    tip.style.left = Math.max(4, Math.min(rect.width - tip.offsetWidth - 4, bx - tip.offsetWidth / 2)) + 'px';
  }
  function hide() { cross.setAttribute('visibility', 'hidden'); dot.setAttribute('visibility', 'hidden'); tip.hidden = true; }
  box.addEventListener('pointermove', e => show(e.clientX));
  box.addEventListener('pointerleave', hide);
}

/* ---------- işlem defteri ---------- */
let txnsExpanded = false;
function txnsHtml() {
  const items = state.txns;
  if (!items.length) return '';
  const shown = txnsExpanded ? items : items.slice(0, 8);
  const row = x => {
    const t = TYPE[x.asset_type];
    const d = x.trade_date || (x.created_at ? x.created_at.slice(0, 10) : null);
    const dStr = d ? (d.slice(0, 4) === String(new Date().getFullYear()) ? trDate(d)
      : new Date(d + 'T12:00:00').toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric' })) : '';
    return `<div class="trow num">
      <span class="side side-${x.side}">${x.side === 'buy' ? 'AL' : 'SAT'}</span>
      <span class="asset"><span class="tick tick-${t.cls}">${esc(t.tick(x.symbol))}</span>
        <span class="aname"><b>${nfq.format(x.quantity)} ${t.unit} · ${money(x.price)}</b>
        ${x.note ? `<small>${esc(x.note)}</small>` : ''}</span></span>
      <span class="r"><span class="cell-sub">${dStr}</span>
        ${x.realized_pl != null ? `<span class="${plClass(x.realized_pl)}">${signedMoney(x.realized_pl)}</span>` : ''}</span>
    </div>`;
  };
  return `<section class="txns" aria-label="İşlem geçmişi">
    <div class="holdings-head">
      <h2>İşlemler</h2>
      <div class="tools">
        <button class="btn-icon" id="txn-csv" title="İşlemleri CSV indir" aria-label="İşlemleri CSV olarak indir">${ICONS.csv}</button>
      </div>
    </div>
    ${shown.map(row).join('')}
    ${items.length > 8 ? `<button class="show-all" id="txn-more">${txnsExpanded ? 'Daha az göster' : `Tümünü göster (${items.length})`}</button>` : ''}
  </section>`;
}
function bindTxns() {
  document.getElementById('txn-more')?.addEventListener('click', () => { txnsExpanded = !txnsExpanded; renderApp(); });
  document.getElementById('txn-csv')?.addEventListener('click', () => {
    const head = ['tarih', 'islem', 'tur', 'sembol', 'miktar', 'birim_fiyat', 'tutar', 'realize_kz', 'not'];
    const rows = state.txns.map(x => [
      x.trade_date || (x.created_at || '').slice(0, 10), x.side === 'buy' ? 'ALIM' : 'SATIM',
      TYPE[x.asset_type].label, x.symbol, x.quantity, x.price,
      Math.round(x.quantity * x.price * 100) / 100, x.realized_pl ?? '', x.note ?? '',
    ]);
    const csv = '﻿' + [head, ...rows]
      .map(r => r.map(v => '"' + String(v).replace(/"/g, '""') + '"').join(';')).join('\r\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    a.download = 'parafomo-islemler-' + new Date().toISOString().slice(0, 10) + '.csv';
    a.click();
    URL.revokeObjectURL(a.href);
  });
}

/* ---------- satış ---------- */
function openSellDialog(h) {
  document.getElementById('sell-dlg')?.remove();
  const t = TYPE[h.asset_type];
  const dlg = document.createElement('dialog');
  dlg.id = 'sell-dlg';
  dlg.innerHTML = `
    <div class="dlg-head"><h2>${t.fixed ? 'Nakit çek' : 'Satış kaydet'}</h2>
      <button class="btn-icon" id="sdlg-x" aria-label="Kapat">${ICONS.x}</button></div>
    <p style="margin:0 0 14px"><span class="tick tick-${t.cls}">${esc(t.tick(h.symbol))}</span>
      <b style="margin-left:8px">${esc(t.name(h.symbol))}</b>
      <span class="cell-sub num" style="display:inline;margin-left:8px">elinde ${nfq.format(h.quantity)} ${t.unit}</span></p>
    <form id="sell-form">
      <label class="field"><span>Satılan ${t.unit === 'gram' ? 'gram' : 'adet'}
        — <button type="button" class="linklike" id="sell-all">tümünü sat (${nfq.format(h.quantity)})</button></span>
        <input name="quantity" type="number" step="any" min="0.0001" max="${h.quantity}" required inputmode="decimal"></label>
      <div ${t.fixed ? 'hidden' : ''}>
        <label class="field"><span>Satış fiyatı (₺)</span>
          <input name="price" type="number" step="any" min="0.0001" required inputmode="decimal" value="${t.fixed ? 1 : (h.current_price != null ? Math.round(h.current_price * 100) / 100 : '')}"></label>
        <p class="price-hint num">Ortalama maliyetin ${money(h.cost_price)} — realize kâr/zarar buna göre hesaplanır.</p>
      </div>
      <label class="field"><span>Satış tarihi</span>
        <input name="trade_date" type="date" max="${new Date().toISOString().slice(0, 10)}" value="${new Date().toISOString().slice(0, 10)}"></label>
      <label class="field"><span>Not (isteğe bağlı)</span><input name="note" maxlength="280"></label>
      <p class="form-error" id="sdlg-err" role="alert"></p>
      <div class="dlg-actions"><span class="grow"></span>
        <button type="button" class="btn btn-quiet" id="sdlg-cancel">Vazgeç</button>
        <button type="submit" class="btn btn-primary">Satışı kaydet</button>
      </div>
    </form>`;
  document.body.appendChild(dlg);
  dlg.showModal();
  dlg.addEventListener('close', () => dlg.remove());
  dlg.querySelector('#sdlg-x').addEventListener('click', () => dlg.close());
  dlg.querySelector('#sdlg-cancel').addEventListener('click', () => dlg.close());
  dlg.querySelector('#sell-all').addEventListener('click', () => {
    dlg.querySelector('[name=quantity]').value = h.quantity;
  });
  dlg.querySelector('#sell-form').addEventListener('submit', async e => {
    e.preventDefault();
    if (state.demo) { dlg.close(); return demoNudge(); }
    const err = dlg.querySelector('#sdlg-err');
    const btn = e.target.querySelector('button[type=submit]');
    btn.disabled = true;
    try {
      const txn = await api('/portfolio/transactions', { method: 'POST', body: JSON.stringify({
        asset_type: h.asset_type, symbol: h.symbol, side: 'sell',
        quantity: parseFloat(e.target.quantity.value.replace(',', '.')),
        price: parseFloat(e.target.price.value.replace(',', '.')),
        trade_date: e.target.trade_date.value || null,
        note: e.target.note.value.trim() || null,
      })});
      dlg.close();
      toast(`Satış kaydedildi — realize ${signedMoney(txn.realized_pl)}.`);
      await refreshData();
    } catch (ex) { err.textContent = ex.message; btn.disabled = false; }
  });
}

/* ---------- izleme listesi ---------- */
function watchHtml() {
  const items = state.watchlist;
  return `<section class="watch" aria-label="İzleme listesi">
    <div class="holdings-head">
      <h2>İzleme listesi</h2>
      <button class="btn btn-quiet" id="watch-add">${ICONS.plus} Varlık izle</button>
    </div>
    ${items.length ? `<div class="wlist">${items.map(w => {
      const t = TYPE[w.asset_type];
      return `<div class="wrow num" data-id="${w.id}">
        <span class="asset">
          <span class="tick tick-${t.cls}">${esc(t.tick(w.symbol))}</span>
          <span class="aname"><b>${esc(t.name(w.symbol))}</b></span>
        </span>
        <span class="r"><span class="cell-main">${money(w.current_price)}</span>
          <span class="cell-sub ${plClass(w.change_pct)}">${w.change_pct != null ? signedPct(w.change_pct) : ''}</span></span>
        <span class="w-tools">
          <button class="btn-icon w-alert" data-id="${w.id}" title="Fiyat alarmı kur" aria-label="${esc(t.name(w.symbol))} için alarm kur">${ICONS.bell}</button>
          <button class="btn-icon w-own" data-id="${w.id}" title="Pozisyon olarak ekle" aria-label="${esc(t.name(w.symbol))} pozisyonu ekle">${ICONS.plus}</button>
          <button class="btn-icon w-del" data-id="${w.id}" title="Listeden çıkar" aria-label="${esc(t.name(w.symbol))} izlemeden çıkar">${ICONS.x}</button>
        </span>
      </div>`;
    }).join('')}</div>`
    : '<p class="watch-empty">Henüz izlediğin varlık yok. Almayı düşündüğün hisseyi ya da altını buraya ekle; fiyatı ve gün değişimini portföyünle yan yana gör.</p>'}
  </section>`;
}
function bindWatch() {
  const sec = document.querySelector('.watch');
  if (!sec) return;
  sec.querySelector('#watch-add').addEventListener('click', openWatchDialog);
  sec.querySelectorAll('.w-del').forEach(b => b.addEventListener('click', async () => {
    if (state.demo) return demoNudge();
    try {
      await api('/portfolio/watchlist/' + b.dataset.id, { method: 'DELETE' });
      state.watchlist = state.watchlist.filter(w => w.id !== Number(b.dataset.id));
      renderApp();
    } catch (ex) { toast(ex.message, true); }
  }));
  sec.querySelectorAll('.w-own').forEach(b => b.addEventListener('click', () => {
    const w = state.watchlist.find(x => x.id === Number(b.dataset.id));
    if (w) openHoldingDialog(null, { asset_type: w.asset_type, symbol: w.symbol });
  }));
  sec.querySelectorAll('.w-alert').forEach(b => b.addEventListener('click', () => {
    const w = state.watchlist.find(x => x.id === Number(b.dataset.id));
    if (w) openAlertDialog(w.asset_type, w.symbol, w.current_price);
  }));
}

/* ---------- alarmlar ---------- */
function alertText(a) {
  if (a.kind === 'day_pct') {
    return `günde %${nf1.format(a.threshold)}+ ${a.direction === 'above' ? 'yükseliş' : 'düşüş'}`;
  }
  return `${money(a.threshold)} ${a.direction === 'above' ? 'üstü' : 'altı'}`;
}
function alertsHtml() {
  const items = state.alerts;
  if (!items.length) return '';
  const act = items.filter(a => a.active), done = items.filter(a => !a.active).slice(0, 5);
  const row = a => {
    const t = TYPE[a.asset_type];
    let sub;
    if (!a.active) sub = `tetiklendi${a.triggered_price ? ' · ' + money(a.triggered_price) : ''}${a.triggered_at ? ' · ' + new Date(a.triggered_at).toLocaleDateString('tr-TR') : ''}`;
    else if (a.repeat && !a.armed) sub = 'tetiklendi — koşul düzelince kendini yeniden kurar';
    else sub = 'bekliyor — tetiklenince e-posta gelir' + (a.repeat ? ' · tekrarlayan' : '');
    return `<div class="arow num" data-id="${a.id}">
      <span class="asset"><span class="tick tick-${t.cls}">${esc(t.tick(a.symbol))}</span>
        <span class="aname"><b>${alertText(a)}</b><small>${sub}</small></span>
      </span>
      <button class="btn-icon a-del" data-id="${a.id}" title="Alarmı sil" aria-label="Alarmı sil">${ICONS.x}</button>
    </div>`;
  };
  return `<section class="alerts" aria-label="Fiyat alarmları">
    <div class="holdings-head"><h2>Fiyat alarmları</h2></div>
    ${act.map(row).join('')}${done.length ? `<div class="alerts-done">${done.map(row).join('')}</div>` : ''}
  </section>`;
}
function bindAlerts() {
  document.querySelectorAll('.a-del').forEach(b => b.addEventListener('click', async () => {
    if (state.demo) return demoNudge();
    try {
      await api('/portfolio/alerts/' + b.dataset.id, { method: 'DELETE' });
      state.alerts = state.alerts.filter(a => a.id !== Number(b.dataset.id));
      renderApp();
    } catch (ex) { toast(ex.message, true); }
  }));
}

function openAlertDialog(assetType, symbol, currentPrice) {
  document.getElementById('alert-dlg')?.remove();
  const t = TYPE[assetType];
  const dlg = document.createElement('dialog');
  dlg.id = 'alert-dlg';
  dlg.innerHTML = `
    <div class="dlg-head"><h2>Fiyat alarmı kur</h2>
      <button class="btn-icon" id="adlg-x" aria-label="Kapat">${ICONS.x}</button></div>
    <p style="margin:0 0 14px"><span class="tick tick-${t.cls}">${esc(t.tick(symbol))}</span>
      <b style="margin-left:8px">${esc(t.name(symbol))}</b>
      ${currentPrice != null ? `<span class="cell-sub num" style="display:inline;margin-left:8px">şu an ${money(currentPrice)}</span>` : ''}</p>
    <form id="alert-form">
      <div class="seg" role="radiogroup" aria-label="Alarm türü">
        <label><input type="radio" name="kind" value="price" checked><span>Fiyat eşiği</span></label>
        <label><input type="radio" name="kind" value="day_pct"><span>Günlük değişim</span></label>
      </div>
      <div class="seg" role="radiogroup" aria-label="Yön" id="dir-seg">
        <label><input type="radio" name="direction" value="above" checked><span id="dir-above">Üstüne çıkınca</span></label>
        <label><input type="radio" name="direction" value="below"><span id="dir-below">Altına inince</span></label>
      </div>
      <label class="field"><span id="th-label">Eşik fiyat (₺)</span>
        <input name="threshold" type="number" step="any" min="0.0001" required inputmode="decimal" value="${currentPrice != null ? Math.round(currentPrice * 100) / 100 : ''}"></label>
      <label class="check"><input type="checkbox" name="repeat">
        <span>Tekrarlayan: tetiklenince kapanmasın, koşul düzelince yeniden kurulsun</span></label>
      <p class="hint" style="font-size:.85rem;color:var(--muted);margin:10px 0 14px">Eşik aşılınca <b>${esc(state.user?.email || '')}</b> adresine e-posta gönderilir. Kontrol sıklığı ~15 dakika.</p>
      <p class="form-error" id="adlg-err" role="alert"></p>
      <div class="dlg-actions"><span class="grow"></span>
        <button type="button" class="btn btn-quiet" id="adlg-cancel">Vazgeç</button>
        <button type="submit" class="btn btn-primary">Alarmı kur</button>
      </div>
    </form>`;
  document.body.appendChild(dlg);
  dlg.showModal();
  dlg.addEventListener('close', () => dlg.remove());
  dlg.querySelector('#adlg-x').addEventListener('click', () => dlg.close());
  dlg.querySelector('#adlg-cancel').addEventListener('click', () => dlg.close());
  const form = dlg.querySelector('#alert-form');
  form.querySelectorAll('input[name=kind]').forEach(r => r.addEventListener('change', () => {
    const pct = r.value === 'day_pct';
    dlg.querySelector('#th-label').textContent = pct ? 'Eşik değişim (%)' : 'Eşik fiyat (₺)';
    dlg.querySelector('#dir-above').textContent = pct ? 'Yükselirse' : 'Üstüne çıkınca';
    dlg.querySelector('#dir-below').textContent = pct ? 'Düşerse' : 'Altına inince';
    form.threshold.value = pct ? 5 : (currentPrice != null ? Math.round(currentPrice * 100) / 100 : '');
  }));
  form.addEventListener('submit', async e => {
    e.preventDefault();
    if (state.demo) { dlg.close(); return demoNudge(); }
    const err = dlg.querySelector('#adlg-err');
    try {
      const a = await api('/portfolio/alerts', { method: 'POST', body: JSON.stringify({
        asset_type: assetType, symbol,
        kind: form.kind.value,
        direction: form.direction.value,
        threshold: parseFloat(form.threshold.value.replace(',', '.')),
        repeat: form.repeat.checked,
      })});
      state.alerts.unshift(a);
      dlg.close();
      toast('Alarm kuruldu — eşik aşılınca e-posta gelecek.');
      renderApp();
    } catch (ex) { err.textContent = ex.message; }
  });
}

function openWatchDialog() {
  document.getElementById('watch-dlg')?.remove();
  const dlg = document.createElement('dialog');
  dlg.id = 'watch-dlg';
  dlg.innerHTML = `
    <div class="dlg-head"><h2>Varlık izle</h2>
      <button class="btn-icon" id="wdlg-x" aria-label="Kapat">${ICONS.x}</button></div>
    <form id="watch-form">
      <div class="seg seg-wrap" role="radiogroup" aria-label="Varlık türü">
        ${Object.entries(TYPE).filter(([k]) => k !== 'cash').map(([k, t], i) => `
          <label><input type="radio" name="asset_type" value="${k}" ${i === 0 ? 'checked' : ''}><span>${t.label}</span></label>`).join('')}
      </div>
      <div id="wsymbol-wrap">
        <label class="field suggest"><span>Hisse</span>
          <input name="symbol_q" placeholder="Kod ya da şirket adı" autocomplete="off" required>
          <input type="hidden" name="symbol">
          <ul id="wsym-list" hidden></ul>
        </label>
      </div>
      <p class="form-error" id="wdlg-err" role="alert"></p>
      <div class="dlg-actions"><span class="grow"></span>
        <button type="button" class="btn btn-quiet" id="wdlg-cancel">Vazgeç</button>
        <button type="submit" class="btn btn-primary">İzlemeye al</button>
      </div>
    </form>`;
  document.body.appendChild(dlg);
  dlg.showModal();
  dlg.addEventListener('close', () => dlg.remove());
  dlg.querySelector('#wdlg-x').addEventListener('click', () => dlg.close());
  dlg.querySelector('#wdlg-cancel').addEventListener('click', () => dlg.close());
  const form = dlg.querySelector('#watch-form');
  const wrap = dlg.querySelector('#wsymbol-wrap');
  wireSymbolSearch(form, dlg.querySelector('#wsym-list'), null);
  form.querySelectorAll('input[name=asset_type]').forEach(r => r.addEventListener('change', () => {
    wrap.hidden = r.value !== 'bist';
    form.symbol_q.required = r.value === 'bist';
  }));
  form.addEventListener('submit', async e => {
    e.preventDefault();
    if (state.demo) { dlg.close(); return demoNudge(); }
    const err = dlg.querySelector('#wdlg-err');
    try {
      const assetType = form.asset_type.value;
      let symbol = assetType === 'bist' ? resolveSymbol(form) : assetType;
      const w = await api('/portfolio/watchlist', { method: 'POST', body: JSON.stringify({ asset_type: assetType, symbol }) });
      if (!state.watchlist.some(x => x.id === w.id)) state.watchlist.push(w);
      dlg.close();
      renderApp();
    } catch (ex) { err.textContent = ex.message; }
  });
}

/* ---------- hesap ayarları ---------- */
function openAccountDialog() {
  if (state.demo) return demoNudge();
  document.getElementById('acct-dlg')?.remove();
  const u = state.user;
  const dlg = document.createElement('dialog');
  dlg.id = 'acct-dlg';
  dlg.innerHTML = `
    <div class="dlg-head"><h2>Hesap ayarları</h2>
      <button class="btn-icon" id="acct-x" aria-label="Kapat">${ICONS.x}</button></div>
    <p class="cell-sub" style="margin:-8px 0 16px">${esc(u.email)}</p>
    <form id="acct-form">
      <label class="field"><span>Adın</span>
        <input name="display_name" maxlength="120" value="${esc(u.display_name || '')}" autocomplete="name"></label>
      <label class="check"><input type="checkbox" name="monthly_email" ${u.monthly_email ? 'checked' : ''}>
        <span>Ay sonu portföy özetini e-postayla gönder</span></label>
      <p class="form-error" id="acct-err" role="alert"></p>
      <div class="dlg-actions" style="margin-top:14px"><span class="grow"></span>
        <button type="submit" class="btn btn-primary">Kaydet</button>
      </div>
    </form>
    <div class="danger-zone">
      <button type="button" class="btn btn-danger" id="del-open">Hesabı kalıcı olarak sil…</button>
      <div id="del-confirm" hidden>
        <p>Hesabın ve <b>tüm verilerin</b> (pozisyonlar, geçmiş, alarmlar, hedefler) kalıcı silinir.
        Bu geri alınamaz. Onaylamak için e-postanı yaz:</p>
        <label class="field"><input id="del-email" type="email" placeholder="${esc(u.email)}" autocomplete="off"></label>
        <button type="button" class="btn btn-danger" id="del-go" disabled>Evet, hesabımı sil</button>
      </div>
    </div>`;
  document.body.appendChild(dlg);
  dlg.showModal();
  dlg.addEventListener('close', () => dlg.remove());
  dlg.querySelector('#acct-x').addEventListener('click', () => dlg.close());
  dlg.querySelector('#acct-form').addEventListener('submit', async e => {
    e.preventDefault();
    const err = dlg.querySelector('#acct-err');
    try {
      const me = await api('/auth/me', { method: 'PATCH', body: JSON.stringify({
        display_name: e.target.display_name.value,
        monthly_email: e.target.monthly_email.checked,
      })});
      state.user = me;
      dlg.close();
      toast('Hesap ayarların kaydedildi.');
      renderApp();
    } catch (ex) { err.textContent = ex.message; }
  });
  const delOpen = dlg.querySelector('#del-open'), delBox = dlg.querySelector('#del-confirm');
  const delMail = dlg.querySelector('#del-email'), delGo = dlg.querySelector('#del-go');
  delOpen.addEventListener('click', () => { delBox.hidden = false; delOpen.hidden = true; delMail.focus(); });
  delMail.addEventListener('input', () => {
    delGo.disabled = delMail.value.trim().toLowerCase() !== u.email.toLowerCase();
  });
  delGo.addEventListener('click', async () => {
    delGo.disabled = true;
    try {
      await api('/auth/me', { method: 'DELETE' });
      dlg.close();
      safeSet(TOKEN_KEY, null);
      state.user = state.summary = null;
      renderAuth();
      toast('Hesabın ve tüm verilerin silindi. Görüşmek üzere.');
    } catch (ex) { toast(ex.message, true); delGo.disabled = false; }
  });
}

/* BIST sembol arama — ekleme/izleme kiplerinde ortak */
function wireSymbolSearch(form, list, onPick) {
  const symQ = form.symbol_q, symHidden = form.symbol;
  symQ.addEventListener('input', () => {
    symHidden.value = '';
    const q = symQ.value.trim().toLocaleLowerCase('tr-TR');
    if (q.length < 1) { list.hidden = true; return; }
    const qU = symQ.value.trim().toLocaleUpperCase('tr-TR');
    const hits = state.symbols.filter(s => s.c.startsWith(qU) || s.n.toLocaleLowerCase('tr-TR').includes(q)).slice(0, 8);
    if (!hits.length) { list.hidden = true; return; }
    list.innerHTML = hits.map(s => `<li><button type="button" data-c="${s.c}"><b>${esc(s.c)}</b><small>${esc(s.n)}</small></button></li>`).join('');
    list.hidden = false;
    list.querySelectorAll('button').forEach(b => b.addEventListener('click', () => {
      const code = b.dataset.c;
      symQ.value = code + ' — ' + symbolName(code);
      symHidden.value = code;
      list.hidden = true;
      if (onPick) onPick(code);
    }));
  });
  symQ.addEventListener('blur', () => setTimeout(() => { list.hidden = true; }, 180));
}
function resolveSymbol(form) {
  let symbol = form.symbol.value;
  if (!symbol) {
    const typed = form.symbol_q.value.trim().toLocaleUpperCase('tr-TR').split(' ')[0];
    if (state.symbols.some(s => s.c === typed)) symbol = typed;
    else throw new Error('Hisseyi listeden seç — kod ya da şirket adı yazınca öneriler açılır.');
  }
  return symbol;
}

function exportCsv() {
  const s = state.summary;
  if (!s || !s.holdings.length) return;
  const head = ['tur', 'sembol', 'ad', 'miktar', 'birim_maliyet', 'guncel_fiyat', 'maliyet_degeri', 'guncel_deger', 'kar_zarar', 'kar_zarar_yuzde', 'gun_degisim_yuzde', 'alis_tarihi', 'not'];
  const rows = s.holdings.map(h => [
    TYPE[h.asset_type].label, h.symbol, TYPE[h.asset_type].name(h.symbol),
    h.quantity, h.cost_price, h.current_price ?? '', h.cost_value, h.current_value ?? '',
    h.profit_loss ?? '', h.profit_loss_pct ?? '', h.change_pct ?? '',
    h.purchase_date ?? '', h.note ?? '',
  ]);
  const csv = '﻿' + [head, ...rows]
    .map(r => r.map(v => '"' + String(v).replace(/"/g, '""') + '"').join(';')).join('\r\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  a.download = 'parafomo-portfoy-' + new Date().toISOString().slice(0, 10) + '.csv';
  a.click();
  URL.revokeObjectURL(a.href);
  toast('Portföy CSV olarak indirildi.');
}

/* ---------- paylaşım kartı (tutar YOK, yalnız yüzde + dağılım) ---------- */
async function shareCard() {
  const s = state.summary;
  if (!s || !s.holdings.length) return;
  try { await document.fonts.load('700 120px "IBM Plex Sans"'); await document.fonts.load('500 44px "IBM Plex Sans"'); } catch {}
  const W = 1080, H = 1350;
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  const c = cv.getContext('2d');
  if (!c.roundRect) c.roundRect = function (x, y, w, h) { this.rect(x, y, w, h); return this; };
  const F = w => `${w} "IBM Plex Sans", sans-serif`;
  c.fillStyle = '#0C1514'; c.fillRect(0, 0, W, H);
  c.fillStyle = '#E9F0EE'; c.font = F('700 56px'); c.fillText('parafomo', 80, 130);
  const wmW = c.measureText('parafomo').width;
  c.font = F('600 34px'); c.fillStyle = '#4FD8BE';
  c.fillText('portföy', 80 + wmW + 26, 126);
  c.font = F('500 36px'); c.fillStyle = '#8DA29D';
  c.fillText(new Date().toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' }), 80, 196);
  const pct = s.total_profit_loss_pct, up = pct >= 0;
  c.fillStyle = '#8DA29D'; c.font = F('500 44px');
  c.fillText('Portföyüm, alıştan bu yana', 80, 380);
  c.fillStyle = up ? '#46C879' : '#F0776A'; c.font = F('700 170px');
  c.fillText((up ? '+' : '−') + '%' + nf1.format(Math.abs(pct)), 72, 560);
  const rr = realReturn(s);
  c.font = F('500 44px'); c.fillStyle = '#8DA29D';
  if (rr && rr.dated) {
    c.fillText('Enflasyon sonrası (reel): ' + (rr.pct >= 0 ? '+' : '−') + '%' + nf1.format(Math.abs(rr.pct)), 80, 650);
  } else if (s.total_day_change_pct != null) {
    const d = s.total_day_change_pct;
    c.fillText('Bugün ' + (d >= 0 ? '+' : '−') + '%' + nf2.format(Math.abs(d)), 80, 650);
  }
  const sums = {};
  for (const h of s.holdings) {
    const k = ALLOC_CLASS[h.asset_type] || 'bist';
    sums[k] = (sums[k] || 0) + (h.current_value ?? h.cost_value ?? 0);
  }
  const tot = Object.values(sums).reduce((a, b) => a + b, 0) || 1;
  const COLORS = { bist: '#0891B2', gold: '#BA851F', silver: '#7488D8', fx: '#2F9E6A', crypto: '#C95CB0', cash: '#556763' };
  const order = ALLOC_META.filter(([k]) => sums[k] > 0);
  let bx = 80; const bw = W - 160, by = 760, bh = 34;
  for (const [k] of order) {
    const w = (sums[k] / tot) * (bw - (order.length - 1) * 6);
    c.fillStyle = COLORS[k];
    c.beginPath(); c.roundRect(bx, by, w, bh, 8); c.fill();
    bx += w + 6;
  }
  let ly = by + 110;
  for (const [k, label] of order) {
    c.fillStyle = COLORS[k];
    c.beginPath(); c.roundRect(80, ly - 30, 26, 26, 7); c.fill();
    c.fillStyle = '#E9F0EE'; c.font = F('600 40px');
    c.fillText(label, 126, ly - 6);
    c.fillStyle = '#8DA29D'; c.font = F('500 40px');
    c.fillText('%' + nf0.format(sums[k] / tot * 100), 126 + c.measureText(label).width + 60, ly - 6);
    ly += 70;
  }
  c.strokeStyle = '#233431'; c.lineWidth = 2;
  c.beginPath(); c.moveTo(80, H - 170); c.lineTo(W - 80, H - 170); c.stroke();
  c.fillStyle = '#E9F0EE'; c.font = F('600 40px');
  c.fillText('app.parafomo.com', 80, H - 96);
  c.fillStyle = '#8DA29D'; c.font = F('500 34px');
  c.fillText('Ücretsiz portföy takibi — altın, hisse, gümüş', 80, H - 44);

  cv.toBlob(async blob => {
    if (!blob) return;
    const file = new File([blob], 'parafomo-portfoy-karti.png', { type: 'image/png' });
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      try { await navigator.share({ files: [file], title: 'Portföyüm — ParaFOMO' }); return; } catch {}
    }
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = file.name;
    a.click();
    URL.revokeObjectURL(a.href);
    toast('Kart indirildi — tutar yok, yalnız yüzdeler.');
  }, 'image/png');
}

/* ---------- pozisyon ekle / düzenle ---------- */
function openHoldingDialog(existing, preset) {
  document.getElementById('holding-dlg')?.remove();
  const isEdit = Boolean(existing);
  const dlg = document.createElement('dialog');
  dlg.id = 'holding-dlg';
  const presetType = preset?.asset_type || 'bist';
  dlg.innerHTML = `
    <div class="dlg-head">
      <h2>${isEdit ? 'Pozisyonu düzenle' : 'Pozisyon ekle'}</h2>
      <button class="btn-icon" value="cancel" id="dlg-x" aria-label="Kapat">${ICONS.x}</button>
    </div>
    <form id="holding-form">
      ${isEdit ? `<p style="margin:0 0 6px"><span class="tick tick-${TYPE[existing.asset_type].cls}">${esc(TYPE[existing.asset_type].tick(existing.symbol))}</span>
        <b style="margin-left:8px">${esc(TYPE[existing.asset_type].name(existing.symbol))}</b></p>
        <p class="cell-sub" style="margin:0 0 14px">Bu düzeltmeler işlem defterine yazılmaz; alım/satım için pozisyon detayını kullan.</p>` : `
      <div class="seg seg-wrap" role="radiogroup" aria-label="Varlık türü">
        ${Object.entries(TYPE).map(([k, t]) => `
          <label><input type="radio" name="asset_type" value="${k}" ${k === presetType ? 'checked' : ''}><span>${t.label}</span></label>`).join('')}
      </div>
      <div id="symbol-wrap" ${presetType !== 'bist' ? 'hidden' : ''}>
        <label class="field suggest"><span>Hisse</span>
          <input name="symbol_q" placeholder="Kod ya da şirket adı: THYAO, Aselsan…" autocomplete="off" ${presetType === 'bist' ? 'required' : ''}
            value="${preset && preset.asset_type === 'bist' ? esc(preset.symbol + ' — ' + symbolName(preset.symbol)) : ''}">
          <input type="hidden" name="symbol" value="${preset && preset.asset_type === 'bist' ? esc(preset.symbol) : ''}">
          <ul id="sym-list" hidden></ul>
        </label>
      </div>`}
      <label class="field"><span id="qty-label">${(isEdit ? TYPE[existing.asset_type] : TYPE[presetType]).q}</span>
        <input name="quantity" type="number" step="any" min="0.0001" required inputmode="decimal" value="${isEdit ? existing.quantity : ''}"></label>
      <div id="cost-wrap" ${!isEdit && TYPE[presetType].fixed ? 'hidden' : ''}>
        <label class="field"><span>Birim maliyet (₺)</span>
          <input name="cost_price" type="number" step="any" min="0.0001" required inputmode="decimal" value="${isEdit ? existing.cost_price : (TYPE[presetType].fixed ? 1 : '')}"></label>
        <p class="price-hint" id="price-hint"></p>
      </div>
      <label class="field"><span>Alış tarihi (önerilir — reel getiri ve kıyas bununla hesaplanır)</span>
        <input name="purchase_date" type="date" max="${new Date().toISOString().slice(0, 10)}" value="${isEdit && existing.purchase_date ? existing.purchase_date : ''}"></label>
      <label class="field"><span>Not (isteğe bağlı)</span>
        <input name="note" maxlength="280" value="${isEdit ? esc(existing.note || '') : ''}"></label>
      <p class="form-error" id="dlg-err" role="alert"></p>
      <div class="dlg-actions">
        ${isEdit ? '<button type="button" class="btn btn-danger" id="del-btn">Pozisyonu sil</button>' : ''}
        <span class="grow"></span>
        <button type="button" class="btn btn-quiet" id="dlg-cancel">Vazgeç</button>
        <button type="submit" class="btn btn-primary">${isEdit ? 'Kaydet' : 'Ekle'}</button>
      </div>
    </form>`;
  document.body.appendChild(dlg);
  dlg.showModal();
  dlg.addEventListener('close', () => dlg.remove());
  dlg.querySelector('#dlg-x').addEventListener('click', () => dlg.close());
  dlg.querySelector('#dlg-cancel').addEventListener('click', () => dlg.close());

  const form = dlg.querySelector('#holding-form');
  const err = dlg.querySelector('#dlg-err');
  const hint = dlg.querySelector('#price-hint');

  async function showLivePrice(assetType, symbol) {
    if (state.demo) return;
    hint.textContent = 'Güncel fiyat alınıyor…';
    try {
      const q = assetType === 'bist' ? '&symbol=' + encodeURIComponent(symbol) : '';
      const r = await (await fetch(API_BASE + '/public/price?asset_type=' + assetType + q)).json();
      if (r.price != null) {
        hint.innerHTML = `Güncel fiyat: <b class="num">${money(r.price)}</b> — <button type="button" id="use-price">maliyete yaz</button>`;
        hint.querySelector('#use-price').addEventListener('click', () => { form.cost_price.value = r.price; });
      } else hint.textContent = '';
    } catch { hint.textContent = ''; }
  }

  if (!isEdit) {
    const symWrap = dlg.querySelector('#symbol-wrap');
    const qtyLabel = dlg.querySelector('#qty-label');
    const costWrap = dlg.querySelector('#cost-wrap');
    form.querySelectorAll('input[name=asset_type]').forEach(r => r.addEventListener('change', () => {
      const t = TYPE[r.value];
      symWrap.hidden = r.value !== 'bist';
      form.symbol_q.required = r.value === 'bist';
      qtyLabel.textContent = t.q;
      hint.textContent = '';
      costWrap.hidden = Boolean(t.fixed);
      if (t.fixed) form.cost_price.value = 1;
      else if (r.value !== 'bist') showLivePrice(r.value);
    }));
    wireSymbolSearch(form, dlg.querySelector('#sym-list'), code => showLivePrice('bist', code));
    if (preset) {
      if (preset.asset_type === 'bist') showLivePrice('bist', preset.symbol);
      else showLivePrice(preset.asset_type);
    }
  } else if (existing.current_price != null) {
    hint.innerHTML = `Güncel fiyat: <b class="num">${money(existing.current_price)}</b>`;
  }

  if (isEdit) {
    dlg.querySelector('#del-btn').addEventListener('click', async () => {
      if (state.demo) { dlg.close(); return demoNudge(); }
      if (!confirm(TYPE[existing.asset_type].name(existing.symbol) + ' pozisyonu silinsin mi? Bu geri alınamaz.')) return;
      try {
        await api('/portfolio/holdings/' + existing.id, { method: 'DELETE' });
        dlg.close();
        toast('Pozisyon silindi.');
        await refreshData();
      } catch (ex) { err.textContent = ex.message; }
    });
  }

  form.addEventListener('submit', async e => {
    e.preventDefault();
    if (state.demo) { dlg.close(); return demoNudge(); }
    err.textContent = '';
    const btn = form.querySelector('button[type=submit]');
    btn.disabled = true;
    try {
      const qty = parseFloat(form.quantity.value.replace(',', '.'));
      const cost = parseFloat(form.cost_price.value.replace(',', '.'));
      const date = form.purchase_date.value || null;
      const note = form.note.value.trim() || null;
      if (isEdit) {
        await api('/portfolio/holdings/' + existing.id, {
          method: 'PATCH',
          body: JSON.stringify({ quantity: qty, cost_price: cost, purchase_date: date, note }),
        });
        toast('Pozisyon güncellendi.');
      } else {
        const assetType = form.asset_type.value;
        let symbol = assetType === 'bist' ? resolveSymbol(form) : assetType;
        await api('/portfolio/transactions', {
          method: 'POST',
          body: JSON.stringify({ asset_type: assetType, symbol, side: 'buy', quantity: qty, price: cost, trade_date: date, note }),
        });
        toast('Alım deftere işlendi. Aynı varlığı tekrar alırsan ortalama maliyet hesaplanır.');
      }
      dlg.close();
      await refreshData();
    } catch (ex) { err.textContent = ex.message; btn.disabled = false; }
  });
}

/* ---------- başlangıç ---------- */
document.addEventListener('click', e => {
  const um = document.getElementById('user-menu');
  if (um && !um.hidden && !e.target.closest('.menu')) um.hidden = true;
});
if ('serviceWorker' in navigator) {
  try { navigator.serviceWorker.register('/sw.js'); } catch {}
}
applyTheme();
if (token()) enterApp(); else renderAuth();
