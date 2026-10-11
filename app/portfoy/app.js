/* ParaFOMO Portföy — app.parafomo.com/portfoy/ SPA.
   Veri + üyelik: api.parafomo.com (JWT, localStorage). Build adımı yok.
   Örnek mod (demo): API'ye dokunmadan tüm arayüzü temsilî veriyle gezdirir. */

const API_BASE = safeGet('pf_api_base') || 'https://api.parafomo.com';
const TOKEN_KEY = 'pf_token';
const GOOGLE_CLIENT_ID = '1020605001020-3o64jftksul1tkqj2gov24j7qj4o18f4.apps.googleusercontent.com';

const TYPE = {
  bist:   { tick: s => s, name: s => symbolName(s), unit: 'adet', cls: 'bist',   label: 'Hisse' },
  gold:   { tick: () => 'ALTIN',  name: () => 'Gram altın (24 ayar)', unit: 'gram', cls: 'gold',   label: 'Altın' },
  silver: { tick: () => 'GÜMÜŞ', name: () => 'Gram gümüş',           unit: 'gram', cls: 'silver', label: 'Gümüş' },
};

let state = {
  user: null, summary: null, history: [], watchlist: [], alerts: [],
  tufe: null, symbols: [], demo: false, refreshTimer: 0,
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
const plClass = v => v == null || v === 0 ? 'pl-flat' : v > 0 ? 'pl-gain' : 'pl-loss';
const trDate = iso => new Date(iso + 'T12:00:00').toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' });

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
    // en yeni başta geliyor → eskiden yeniye sıralı [ [ "YYYY-MM", aylık% ], ... ]
    state.tufe = (d.months || []).map(m => [m.ay, m.aylik]).reverse();
  } catch { state.tufe = []; }
}

/* Reel (enflasyon sonrası) getiri: alış tarihli pozisyonların maliyeti,
   alış ayından SONRAKİ aylık TÜFE değişimleriyle bugüne taşınır. */
function realReturn(s) {
  if (!state.tufe || !state.tufe.length || !s.holdings.length) return null;
  const months = state.tufe;                     // [["2022-10", 3.54], ...] eski→yeni
  const idx = new Map(months.map((m, i) => [m[0], i]));
  const first = months[0][0];
  let adjCost = 0, value = 0, dated = 0, undated = 0, partial = false;
  for (const h of s.holdings) {
    if (h.current_value == null) continue;
    value += h.current_value;
    if (!h.purchase_date) { adjCost += h.cost_value; undated++; continue; }
    const ym = h.purchase_date.slice(0, 7);
    let from = idx.has(ym) ? idx.get(ym) + 1 : null; // alış ayından SONRAKİ ay
    if (from === null) {
      if (ym < first) { from = 0; partial = true; }  // seri başından önce → kısmi
      else { adjCost += h.cost_value; undated++; continue; } // içinde bulunduğumuz ay
    }
    let f = 1;
    for (let i = from; i < months.length; i++) f *= 1 + months[i][1] / 100;
    adjCost += h.cost_value * f;
    dated++;
  }
  if (!dated || adjCost <= 0) return { dated: 0, undated };
  const pl = value - adjCost;
  return { pl, pct: pl / adjCost * 100, dated, undated, partial };
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
  state.history = []; state.watchlist = []; state.alerts = []; state.demo = false;
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
  holdings: [
    { id: -1, asset_type: 'gold',   symbol: 'GOLD',  quantity: 25,  cost_price: 5100, purchase_date: '2026-03-14', note: 'düğün altınları', current_price: 6644.8, change_pct: 0.4 },
    { id: -2, asset_type: 'bist',   symbol: 'THYAO', quantity: 40,  cost_price: 231,  purchase_date: '2026-05-02', note: null, current_price: 287.5, change_pct: 0 },
    { id: -3, asset_type: 'bist',   symbol: 'ASELS', quantity: 15,  cost_price: 298,  purchase_date: '2026-07-21', note: null, current_price: 351.2, change_pct: 0 },
    { id: -4, asset_type: 'silver', symbol: 'SILVER', quantity: 200, cost_price: 71,  purchase_date: '2026-01-09', note: null, current_price: 96.4, change_pct: 0.6 },
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
  };
  // 90 günlük temsilî seri: maliyete doğru geriye, hafif dalgalı
  const hist = []; let v = total_value;
  for (let i = 0; i < 90; i++) {
    hist.unshift({ day: new Date(Date.now() - i * 864e5).toISOString().slice(0, 10), total_value: Math.round(v), total_cost });
    const wave = Math.sin(i / 7) * 0.004 + (((i * 2654435761) % 97) / 97 - 0.5) * 0.012;
    v = v / (1 + 0.0022 + wave);
  }
  state.history = hist;
  state.watchlist = DEMO.watchlist.slice();
  state.alerts = [{ id: -1, asset_type: 'gold', symbol: 'GOLD', direction: 'above', threshold: 7000, active: true, triggered_at: null, triggered_price: null }];
  state.user = { email: 'ornek@parafomo.com', display_name: 'Örnek Portföy' };
}
function startDemo() {
  state.demo = true;
  buildDemo();
  Promise.all([loadSymbols(), loadTufe()]).then(renderApp);
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
      <h1>Altının, hissen, gümüşün — <em>tek ekranda.</em></h1>
      <p>Pozisyonlarını bir kez ekle; canlı fiyatla toplam değerini, değer grafiğini ve
      <strong>enflasyondan arındırılmış gerçek kârını</strong> her açtığında hazır bul.
      Fiyat alarmı kur, e-postayla haber verelim. Ücretsiz.</p>
      <div class="sample" aria-hidden="true">
        <p class="sample-cap">Örnek portföy</p>
        <div class="total num">348.260 ₺ <span class="pl-gain" style="font-size:.55em">+%12,4</span></div>
        <div class="alloc" style="margin:14px 0 0">
          <div class="alloc-bar">
            <span class="f-gold" style="flex:52"></span><span class="f-bist" style="flex:36"></span><span class="f-silver" style="flex:12"></span>
          </div>
          <div class="alloc-legend">
            <span><span class="dot" style="background:var(--a-gold)"></span>Altın<span class="pct">%52</span></span>
            <span><span class="dot" style="background:var(--a-bist)"></span>Hisse<span class="pct">%36</span></span>
            <span><span class="dot" style="background:var(--a-silver)"></span>Gümüş<span class="pct">%12</span></span>
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
        : 'Kayıt olarak <a href="https://parafomo.com/gizlilik/" rel="noopener">gizlilik ilkelerini</a> kabul etmiş olursun.'}</p>
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
  await Promise.all([loadSymbols(), loadTufe()]);
  try {
    const [me, summary, history, watchlist, alerts] = await Promise.all([
      api('/auth/me'), api('/portfolio/summary'), api('/portfolio/history'),
      api('/portfolio/watchlist'), api('/portfolio/alerts'),
    ]);
    state.user = me; state.summary = summary; state.history = history || [];
    state.watchlist = watchlist || []; state.alerts = alerts || [];
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
    const [summary, history, watchlist, alerts] = await Promise.all([
      api('/portfolio/summary'), api('/portfolio/history'),
      api('/portfolio/watchlist'), api('/portfolio/alerts'),
    ]);
    state.summary = summary; state.history = history || [];
    state.watchlist = watchlist || []; state.alerts = alerts || [];
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
};

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
        <li><a href="/">Tüm uygulamalar</a></li>
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
  }

  const main = document.getElementById('main');
  const demoBanner = state.demo ? `
    <div class="demo-banner">
      <span>Örnek görünümdesin — rakamlar temsilî. Beğendiysen 1 dakikada kendi portföyünü kur.</span>
      <button class="btn btn-primary" id="demo-signup">Ücretsiz kayıt ol</button>
    </div>` : '';

  if (!s.holdings.length) {
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
  const pricedAt = s.priced_at ? new Date(s.priced_at) : null;
  const timeStr = pricedAt ? pricedAt.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }) : '';
  const [lira, kurus] = nf2.format(s.total_value ?? 0).split(',');
  const rr = realReturn(s);

  const equiv = [];
  if (s.usd_try) equiv.push(nf0.format(s.total_value / s.usd_try) + ' $');
  if (s.gold_gram_try) equiv.push(nf1.format(s.total_value / s.gold_gram_try) + ' gram altın');

  main.innerHTML = demoBanner + `
    <section class="summary" aria-label="Portföy özeti">
      <p class="sum-label">Toplam değer
        <button class="btn-icon" id="mask-btn" aria-pressed="${masked}" title="Tutarları gizle/göster" aria-label="Tutarları gizle/göster">${ICONS.eye}</button>
      </p>
      <p class="sum-value num">${lira}<span class="kurus">,${kurus} ₺</span></p>
      ${equiv.length ? `<p class="sum-equiv num">≈ ${equiv.join(' ya da ')}</p>` : ''}
      <div class="sum-row num">
        <span class="sum-item">Bugün<b class="${plClass(s.total_day_change)}">${signedMoney(s.total_day_change)}${s.total_day_change_pct != null ? ' (' + signedPct(s.total_day_change_pct) + ')' : ''}</b></span>
        <span class="sum-item">Toplam kâr/zarar<b class="${plClass(s.total_profit_loss)}">${signedMoney(s.total_profit_loss)} (${signedPct(s.total_profit_loss_pct)})</b></span>
        ${rr && rr.dated
          ? `<span class="sum-item" title="Maliyetin, alış tarihinden bugüne TÜİK TÜFE ile bugünkü liraya çevrilmiş hâline göre kâr/zarar.${rr.undated ? ' Alış tarihi olmayan ' + rr.undated + ' pozisyon düzeltilmeden katıldı.' : ''}${rr.partial ? ' Çok eski alışlarda seri Ekim 2022 başlangıçlı.' : ''}">Enflasyon sonrası (reel)<b class="${plClass(rr.pl)}">${(rr.undated || rr.partial) ? '≈ ' : ''}${signedMoney(rr.pl)} (${signedPct(rr.pct)})</b></span>`
          : `<span class="sum-item" title="Pozisyonlarına alış tarihi eklersen maliyetini TÜFE ile bugüne taşıyıp gerçek (reel) kârını gösteririz.">Enflasyon sonrası (reel)<b class="pl-flat">alış tarihi ekle</b></span>`}
      </div>
      <div class="sum-meta">
        <span>Fiyatlar ${timeStr} itibarıyla.</span>
        <button class="btn-icon" id="refresh-btn" title="Fiyatları yenile" aria-label="Fiyatları yenile">${ICONS.refresh}</button>
        <button class="btn-icon" id="share-btn" title="Portföy kartını paylaş (tutarsız, sadece yüzdeler)" aria-label="Portföy kartını paylaş">${ICONS.share}</button>
      </div>
      ${allocHtml(s)}
    </section>
    ${chartHtml()}
    <section class="holdings" aria-label="Pozisyonlar">
      <div class="holdings-head">
        <h2>Pozisyonlar</h2>
        <div class="tools">
          <button class="btn-icon" id="csv-btn" title="CSV indir" aria-label="Pozisyonları CSV olarak indir">${ICONS.csv}</button>
          <button class="btn btn-primary" id="add-btn">Pozisyon ekle</button>
        </div>
      </div>
      <div class="hhead" aria-hidden="true">
        <span>Varlık</span><span class="r">Adet / gram</span><span class="r">Güncel</span><span class="r">Değer</span><span class="r">Kâr/zarar</span><span></span>
      </div>
      <div id="hlist">${s.holdings.slice().sort((a, b) => (b.current_value ?? b.cost_value) - (a.current_value ?? a.cost_value)).map(h => rowHtml(h, s.total_value)).join('')}</div>
    </section>
    ${watchHtml()}
    ${alertsHtml()}`;

  main.querySelector('#demo-signup')?.addEventListener('click', () => { state.demo = false; renderAuth('signup'); });
  main.querySelector('#add-btn').addEventListener('click', () => openHoldingDialog());
  main.querySelector('#refresh-btn').addEventListener('click', () => state.demo ? toast('Örnek modda fiyatlar temsilî.') : refreshData());
  main.querySelector('#csv-btn').addEventListener('click', exportCsv);
  main.querySelector('#share-btn').addEventListener('click', shareCard);
  main.querySelector('#mask-btn').addEventListener('click', () => {
    const now = safeGet('pf_masked') !== '1';
    safeSet('pf_masked', now ? '1' : null);
    main.classList.toggle('masked', now);
    main.querySelector('#mask-btn').setAttribute('aria-pressed', String(now));
  });
  main.querySelectorAll('.hrow').forEach(r =>
    r.addEventListener('click', () => {
      const h = state.summary.holdings.find(x => x.id === Number(r.dataset.id));
      if (h) openHoldingDialog(h);
    }));
  bindChart();
  bindWatch();
  bindAlerts();
}

/* ---------- değer grafiği ---------- */
const CH = { w: 720, h: 190, l: 10, r: 64, t: 14, b: 26 };
function chartHtml() {
  const hist = state.history;
  if (!hist || hist.length < 2) {
    return `<section class="chart chart-empty" aria-label="Değer grafiği">
      <p>Değer grafiğin burada çizilecek — portföyünü her gün kapanışta kaydediyoruz,
      yarından itibaren çizgi oluşmaya başlar.</p></section>`;
  }
  const vs = hist.map(p => p.total_value);
  const min = Math.min(...vs), max = Math.max(...vs);
  const span = (max - min) || max * 0.05 || 1;
  const x = i => CH.l + (CH.w - CH.l - CH.r) * (hist.length === 1 ? 0.5 : i / (hist.length - 1));
  const y = v => CH.t + (CH.h - CH.t - CH.b) * (1 - (v - min + span * 0.08) / (span * 1.16));
  const pts = vs.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`);
  const line = 'M' + pts.join(' L');
  const area = line + ` L${x(vs.length - 1).toFixed(1)},${CH.h - CH.b} L${x(0).toFixed(1)},${CH.h - CH.b} Z`;
  const last = hist[hist.length - 1], first = hist[0];
  const period = last.total_value - first.total_value;
  return `<section class="chart" aria-label="Değer grafiği">
    <div class="chart-head">
      <h2>Değer grafiği</h2>
      <span class="chart-sub num">${trDate(first.day)} – ${trDate(last.day)} · <b class="${plClass(period)}">${signedMoney(period)}</b></span>
    </div>
    <div class="chart-box">
      <svg viewBox="0 0 ${CH.w} ${CH.h}" preserveAspectRatio="none" role="img" aria-label="Portföy değerinin günlük seyri">
        <path class="c-area" d="${area}"/>
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
  const box = document.querySelector('.chart-box');
  if (!box) return;
  const svg = box.querySelector('svg'), tip = box.querySelector('.c-tip');
  const cross = svg.querySelector('.c-cross'), dot = svg.querySelector('.c-dot');
  const hist = state.history;
  const vs = hist.map(p => p.total_value);
  const min = Math.min(...vs), max = Math.max(...vs);
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

function allocHtml(s) {
  const sums = { bist: 0, gold: 0, silver: 0 };
  for (const h of s.holdings) sums[h.asset_type] += h.current_value ?? h.cost_value ?? 0;
  const total = sums.bist + sums.gold + sums.silver;
  if (!total) return '';
  const order = [['gold', 'Altın'], ['bist', 'Hisse'], ['silver', 'Gümüş']].filter(([k]) => sums[k] > 0);
  return `<div class="alloc">
    <div class="alloc-bar" role="img" aria-label="Dağılım: ${order.map(([k, l]) => l + ' %' + nf0.format(sums[k] / total * 100)).join(', ')}">
      ${order.map(([k]) => `<span class="f-${k}" style="flex:${(sums[k] / total * 1000).toFixed(0)}" title="${TYPE[k].label}: ${money(sums[k])}"></span>`).join('')}
    </div>
    <div class="alloc-legend num">
      ${order.map(([k, l]) => `<span><span class="dot" style="background:var(--a-${k})"></span>${l} <b>${money(sums[k])}</b><span class="pct">%${nf0.format(sums[k] / total * 100)}</span></span>`).join('')}
    </div>
  </div>`;
}

function rowHtml(h, totalValue) {
  const t = TYPE[h.asset_type];
  const dayStr = h.change_pct != null ? signedPct(h.change_pct) : '';
  const w = totalValue && h.current_value != null ? h.current_value / totalValue * 100 : null;
  return `
  <button class="hrow num" data-id="${h.id}" title="Düzenlemek için tıkla">
    <span class="asset c-asset">
      <span class="tick tick-${t.cls}">${esc(t.tick(h.symbol))}</span>
      <span class="aname"><b>${esc(t.name(h.symbol))}</b>${h.note ? `<small>${esc(h.note)}</small>` : ''}</span>
    </span>
    <span class="r c-qty"><span class="cell-main">${nfq.format(h.quantity)} ${t.unit}</span><span class="cell-sub">maliyet ${money(h.cost_price)}</span></span>
    <span class="r c-price"><span class="cell-main">${money(h.current_price)}</span><span class="cell-sub ${plClass(h.change_pct)}">${dayStr}</span></span>
    <span class="r c-value"><span class="cell-main">${money(h.current_value)}</span>${w != null ? `<span class="cell-sub" title="Portföydeki payı">pay %${nf0.format(w)}</span>` : ''}</span>
    <span class="r c-pl"><span class="${plClass(h.profit_loss)}">${signedMoney(h.profit_loss)}</span><span class="cell-sub ${plClass(h.profit_loss)}">${h.profit_loss_pct != null ? signedPct(h.profit_loss_pct) : ''}</span></span>
    <span class="edit-ic" aria-hidden="true">${ICONS.edit}</span>
  </button>`;
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
function alertsHtml() {
  const items = state.alerts;
  if (!items.length) return '';
  const act = items.filter(a => a.active), done = items.filter(a => !a.active).slice(0, 5);
  const row = a => {
    const t = TYPE[a.asset_type];
    return `<div class="arow num" data-id="${a.id}">
      <span class="asset"><span class="tick tick-${t.cls}">${esc(t.tick(a.symbol))}</span>
        <span class="aname"><b>${money(a.threshold)} ${a.direction === 'above' ? 'üstü' : 'altı'}</b>
        ${a.active ? '<small>bekliyor — tetiklenince e-posta gelir</small>'
          : `<small>tetiklendi${a.triggered_price ? ' · ' + money(a.triggered_price) : ''}${a.triggered_at ? ' · ' + new Date(a.triggered_at).toLocaleDateString('tr-TR') : ''}</small>`}</span>
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
      <div class="seg" role="radiogroup" aria-label="Yön">
        <label><input type="radio" name="direction" value="above" checked><span>Üstüne çıkınca</span></label>
        <label><input type="radio" name="direction" value="below"><span>Altına inince</span></label>
      </div>
      <label class="field"><span>Eşik fiyat (₺)</span>
        <input name="threshold" type="number" step="any" min="0.0001" required inputmode="decimal" value="${currentPrice != null ? Math.round(currentPrice * 100) / 100 : ''}"></label>
      <p class="hint" style="font-size:.85rem;color:var(--muted);margin:-6px 0 14px">Eşik aşılınca <b>${esc(state.user?.email || '')}</b> adresine e-posta gönderilir; alarm tek seferliktir.</p>
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
  dlg.querySelector('#alert-form').addEventListener('submit', async e => {
    e.preventDefault();
    if (state.demo) { dlg.close(); return demoNudge(); }
    const err = dlg.querySelector('#adlg-err');
    try {
      const a = await api('/portfolio/alerts', { method: 'POST', body: JSON.stringify({
        asset_type: assetType, symbol,
        direction: e.target.direction.value,
        threshold: parseFloat(e.target.threshold.value.replace(',', '.')),
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
      <div class="seg" role="radiogroup" aria-label="Varlık türü">
        ${Object.entries(TYPE).map(([k, t], i) => `
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
  // zemin
  c.fillStyle = '#0C1514'; c.fillRect(0, 0, W, H);
  // marka
  c.fillStyle = '#E9F0EE'; c.font = F('700 56px'); c.fillText('parafomo', 80, 130);
  c.strokeStyle = '#2BB194'; c.lineWidth = 3;
  const wmW = c.measureText('parafomo').width;
  c.font = F('600 34px'); c.fillStyle = '#4FD8BE';
  c.fillText('portföy', 80 + wmW + 26, 126);
  c.font = F('500 36px'); c.fillStyle = '#8DA29D';
  c.fillText(new Date().toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' }), 80, 196);
  // büyük yüzde
  const pct = s.total_profit_loss_pct, up = pct >= 0;
  c.fillStyle = '#8DA29D'; c.font = F('500 44px');
  c.fillText('Portföyüm, alıştan bu yana', 80, 380);
  c.fillStyle = up ? '#46C879' : '#F0776A'; c.font = F('700 170px');
  c.fillText((up ? '+' : '−') + '%' + nf1.format(Math.abs(pct)), 72, 560);
  if (s.total_day_change_pct != null) {
    c.font = F('500 44px'); c.fillStyle = '#8DA29D';
    const d = s.total_day_change_pct;
    c.fillText('Bugün ' + (d >= 0 ? '+' : '−') + '%' + nf2.format(Math.abs(d)), 80, 650);
  }
  // dağılım çubuğu (koyu tema doğrulanmış renkler)
  const sums = { bist: 0, gold: 0, silver: 0 };
  for (const h of s.holdings) sums[h.asset_type] += h.current_value ?? h.cost_value ?? 0;
  const tot = sums.bist + sums.gold + sums.silver || 1;
  const COLORS = { bist: '#0891B2', gold: '#BA851F', silver: '#7488D8' };
  const order = [['gold', 'Altın'], ['bist', 'Hisse'], ['silver', 'Gümüş']].filter(([k]) => sums[k] > 0);
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
  // altbilgi
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
      ${isEdit ? `<p style="margin:0 0 14px"><span class="tick tick-${TYPE[existing.asset_type].cls}">${esc(TYPE[existing.asset_type].tick(existing.symbol))}</span>
        <b style="margin-left:8px">${esc(TYPE[existing.asset_type].name(existing.symbol))}</b></p>` : `
      <div class="seg" role="radiogroup" aria-label="Varlık türü">
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
      <label class="field"><span id="qty-label">${(isEdit ? TYPE[existing.asset_type] : TYPE[presetType]).unit === 'gram' ? 'Gram' : 'Adet'}</span>
        <input name="quantity" type="number" step="any" min="0.0001" required inputmode="decimal" value="${isEdit ? existing.quantity : ''}"></label>
      <label class="field"><span>Birim maliyet (₺)</span>
        <input name="cost_price" type="number" step="any" min="0.0001" required inputmode="decimal" value="${isEdit ? existing.cost_price : ''}"></label>
      <p class="price-hint" id="price-hint"></p>
      <label class="field"><span>Alış tarihi (önerilir — reel getiri bununla hesaplanır)</span>
        <input name="purchase_date" type="date" max="${new Date().toISOString().slice(0, 10)}" value="${isEdit && existing.purchase_date ? existing.purchase_date : ''}"></label>
      <label class="field"><span>Not (isteğe bağlı)</span>
        <input name="note" maxlength="280" value="${isEdit ? esc(existing.note || '') : ''}"></label>
      <p class="form-error" id="dlg-err" role="alert"></p>
      <div class="dlg-actions">
        ${isEdit ? `<button type="button" class="btn btn-danger" id="del-btn">Pozisyonu sil</button>
                    <button type="button" class="btn-icon" id="alert-btn" title="Bu varlığa fiyat alarmı kur" aria-label="Fiyat alarmı kur">${ICONS.bell}</button>` : ''}
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
    form.querySelectorAll('input[name=asset_type]').forEach(r => r.addEventListener('change', () => {
      const t = TYPE[r.value];
      symWrap.hidden = r.value !== 'bist';
      form.symbol_q.required = r.value === 'bist';
      qtyLabel.textContent = t.unit === 'gram' ? 'Gram' : 'Adet';
      hint.textContent = '';
      if (r.value !== 'bist') showLivePrice(r.value);
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
    dlg.querySelector('#alert-btn').addEventListener('click', () => {
      dlg.close();
      openAlertDialog(existing.asset_type, existing.symbol, existing.current_price);
    });
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
        await api('/portfolio/holdings', {
          method: 'POST',
          body: JSON.stringify({ asset_type: assetType, symbol, quantity: qty, cost_price: cost, purchase_date: date, note }),
        });
        toast('Pozisyon eklendi. Aynı varlığı tekrar eklersen ortalama maliyet hesaplanır.');
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
