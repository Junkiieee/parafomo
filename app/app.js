/* ParaFOMO Portföy — app.parafomo.com SPA.
   Veri + üyelik: api.parafomo.com (JWT, localStorage). Build adımı yok. */

const API_BASE = safeGet('pf_api_base') || 'https://api.parafomo.com';
const TOKEN_KEY = 'pf_token';
const GOOGLE_CLIENT_ID = '1020605001020-3o64jftksul1tkqj2gov24j7qj4o18f4.apps.googleusercontent.com';

const TYPE = {
  bist:   { tick: s => s, name: s => symbolName(s), unit: 'adet', cls: 'bist',   label: 'Hisse' },
  gold:   { tick: () => 'ALTIN',  name: () => 'Gram altın (24 ayar)', unit: 'gram', cls: 'gold',   label: 'Altın' },
  silver: { tick: () => 'GÜMÜŞ', name: () => 'Gram gümüş',           unit: 'gram', cls: 'silver', label: 'Gümüş' },
};

let state = { user: null, summary: null, symbols: [], refreshTimer: 0 };

/* ---------- yardımcılar ---------- */
function safeGet(k) { try { return localStorage.getItem(k); } catch { return null; } }
function safeSet(k, v) { try { v === null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch {} }
const token = () => safeGet(TOKEN_KEY);

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
const nf2 = new Intl.NumberFormat('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const nf0 = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 0 });
const nfq = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 4 });
const money = v => v == null ? '—' : nf2.format(v) + ' ₺';
const signedMoney = v => v == null ? '—' : (v > 0 ? '+' : v < 0 ? '−' : '') + nf2.format(Math.abs(v)) + ' ₺';
const signedPct = v => v == null ? '' : (v > 0 ? '+' : v < 0 ? '−' : '') + '%' + nf2.format(Math.abs(v));
const plClass = v => v == null || v === 0 ? 'pl-flat' : v > 0 ? 'pl-gain' : 'pl-loss';

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

/* ---------- oturum ---------- */
function logout(announce = true) {
  safeSet(TOKEN_KEY, null);
  state.user = state.summary = null;
  clearInterval(state.refreshTimer);
  renderAuth();
  if (announce) toast('Çıkış yapıldı.');
}
async function onAuthed(tok) {
  safeSet(TOKEN_KEY, tok);
  await enterApp();
}

/* ---------- giriş ekranı ---------- */
function renderAuth(mode = 'signin') {
  document.title = 'ParaFOMO Portföy';
  document.getElementById('bar-right').innerHTML = themeBtnHtml();
  bindThemeBtn();
  const main = document.getElementById('main');
  main.innerHTML = `
  <div class="landing">
    <section class="pitch">
      <h1>Altının, hissen, gümüşün — <em>tek ekranda.</em></h1>
      <p>Pozisyonlarını bir kez ekle; güncel fiyatla toplam değerini, bugünkü değişimi ve
      alıştan bu yana kâr/zararını her açtığında hazır bul. Ücretsiz.</p>
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
      const dark = matchMedia('(prefers-color-scheme: dark)').matches && safeGet('pf_theme') !== 'light';
      google.accounts.id.renderButton(slot, { theme: dark ? 'filled_black' : 'outline', size: 'large', text: 'continue_with', locale: 'tr', width: 280 });
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
  await loadSymbols();
  try {
    const [me, summary] = await Promise.all([api('/auth/me'), api('/portfolio/summary')]);
    state.user = me; state.summary = summary;
  } catch (ex) {
    if (token()) { toast(ex.message, true); }
    return renderAuth();
  }
  renderApp();
  clearInterval(state.refreshTimer);
  state.refreshTimer = setInterval(() => {
    if (document.visibilityState === 'visible') refreshSummary(true);
  }, 90000);
}

async function refreshSummary(silent) {
  try {
    state.summary = await api('/portfolio/summary');
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

function renderApp() {
  const s = state.summary, u = state.user;
  document.title = s.total_value != null && s.holdings.length
    ? nf0.format(s.total_value) + ' ₺ — ParaFOMO Portföy' : 'ParaFOMO Portföy';

  document.getElementById('bar-right').innerHTML = `
    ${themeBtnHtml()}
    <div class="menu">
      <button class="btn-icon" id="user-btn" aria-haspopup="true" aria-expanded="false" aria-label="Hesap menüsü">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-3.6 4.4-5 8-5s6.5 1.4 8 5"/></svg>
      </button>
      <ul class="menu-list" id="user-menu" hidden>
        <li class="who">${esc(u.display_name || u.email)}</li>
        <li><button id="logout-btn">Çıkış yap</button></li>
      </ul>
    </div>`;
  bindThemeBtn();
  const ub = document.getElementById('user-btn'), um = document.getElementById('user-menu');
  ub.addEventListener('click', () => { um.hidden = !um.hidden; ub.setAttribute('aria-expanded', String(!um.hidden)); });
  document.getElementById('logout-btn').addEventListener('click', () => logout());

  const main = document.getElementById('main');
  if (!s.holdings.length) {
    main.innerHTML = `
      <div class="empty">
        <h2>Portföyün henüz boş</h2>
        <p>İlk pozisyonunu ekle: bir hissenin adedini, altının gramını ya da gümüşünü.
        Gerisini biz hesaplayalım — güncel değer, bugünkü değişim, kâr/zarar.</p>
        <button class="btn btn-primary" id="add-btn">Pozisyon ekle</button>
      </div>`;
    main.querySelector('#add-btn').addEventListener('click', () => openHoldingDialog());
    return;
  }

  const pricedAt = s.priced_at ? new Date(s.priced_at) : null;
  const timeStr = pricedAt ? pricedAt.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }) : '';
  const [lira, kurus] = nf2.format(s.total_value ?? 0).split(',');

  main.innerHTML = `
    <section class="summary" aria-label="Portföy özeti">
      <p class="sum-label">Toplam değer</p>
      <p class="sum-value num">${lira}<span class="kurus">,${kurus} ₺</span></p>
      <div class="sum-row num">
        <span class="sum-item">Bugün<b class="${plClass(s.total_day_change)}">${signedMoney(s.total_day_change)}${s.total_day_change_pct != null ? ' (' + signedPct(s.total_day_change_pct) + ')' : ''}</b></span>
        <span class="sum-item">Toplam kâr/zarar<b class="${plClass(s.total_profit_loss)}">${signedMoney(s.total_profit_loss)} (${signedPct(s.total_profit_loss_pct)})</b></span>
        <span class="sum-item">Maliyet<b>${money(s.total_cost)}</b></span>
      </div>
      <div class="sum-meta">
        <span>Fiyatlar ${timeStr} itibarıyla.</span>
        <button class="btn-icon" id="refresh-btn" title="Fiyatları yenile" aria-label="Fiyatları yenile">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 12a9 9 0 1 1-2.6-6.3M21 3v6h-6"/></svg>
        </button>
      </div>
      ${allocHtml(s)}
    </section>
    <section class="holdings" aria-label="Pozisyonlar">
      <div class="holdings-head">
        <h2>Pozisyonlar</h2>
        <button class="btn btn-primary" id="add-btn">Pozisyon ekle</button>
      </div>
      <div class="hhead" aria-hidden="true">
        <span>Varlık</span><span class="r">Adet / gram</span><span class="r">Güncel</span><span class="r">Değer</span><span class="r">Kâr/zarar</span><span></span>
      </div>
      <div id="hlist">${s.holdings.slice().sort((a, b) => (b.current_value ?? b.cost_value) - (a.current_value ?? a.cost_value)).map(rowHtml).join('')}</div>
    </section>`;

  main.querySelector('#add-btn').addEventListener('click', () => openHoldingDialog());
  main.querySelector('#refresh-btn').addEventListener('click', () => refreshSummary());
  main.querySelectorAll('.hrow').forEach(r =>
    r.addEventListener('click', () => {
      const h = state.summary.holdings.find(x => x.id === Number(r.dataset.id));
      if (h) openHoldingDialog(h);
    }));
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

function rowHtml(h) {
  const t = TYPE[h.asset_type];
  const dayStr = h.change_pct != null ? signedPct(h.change_pct) : '';
  return `
  <button class="hrow num" data-id="${h.id}" title="Düzenlemek için tıkla">
    <span class="asset c-asset">
      <span class="tick tick-${t.cls}">${esc(t.tick(h.symbol))}</span>
      <span class="aname"><b>${esc(t.name(h.symbol))}</b>${h.note ? `<small>${esc(h.note)}</small>` : ''}</span>
    </span>
    <span class="r c-qty"><span class="cell-main">${nfq.format(h.quantity)} ${t.unit}</span><span class="cell-sub">maliyet ${money(h.cost_price)}</span></span>
    <span class="r c-price"><span class="cell-main">${money(h.current_price)}</span><span class="cell-sub ${plClass(h.change_pct)}">${dayStr}</span></span>
    <span class="r c-value"><span class="cell-main">${money(h.current_value)}</span></span>
    <span class="r c-pl"><span class="${plClass(h.profit_loss)}">${signedMoney(h.profit_loss)}</span><span class="cell-sub ${plClass(h.profit_loss)}">${h.profit_loss_pct != null ? signedPct(h.profit_loss_pct) : ''}</span></span>
    <span class="edit-ic" aria-hidden="true"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg></span>
  </button>`;
}

/* ---------- pozisyon ekle / düzenle ---------- */
function openHoldingDialog(existing) {
  document.getElementById('holding-dlg')?.remove();
  const isEdit = Boolean(existing);
  const dlg = document.createElement('dialog');
  dlg.id = 'holding-dlg';
  dlg.innerHTML = `
    <div class="dlg-head">
      <h2>${isEdit ? 'Pozisyonu düzenle' : 'Pozisyon ekle'}</h2>
      <button class="btn-icon" value="cancel" id="dlg-x" aria-label="Kapat"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="m6 6 12 12M18 6 6 18"/></svg></button>
    </div>
    <form id="holding-form">
      ${isEdit ? `<p style="margin:0 0 14px"><span class="tick tick-${TYPE[existing.asset_type].cls}">${esc(TYPE[existing.asset_type].tick(existing.symbol))}</span>
        <b style="margin-left:8px">${esc(TYPE[existing.asset_type].name(existing.symbol))}</b></p>` : `
      <div class="seg" role="radiogroup" aria-label="Varlık türü">
        ${Object.entries(TYPE).map(([k, t], i) => `
          <label><input type="radio" name="asset_type" value="${k}" ${i === 0 ? 'checked' : ''}><span>${t.label}</span></label>`).join('')}
      </div>
      <div id="symbol-wrap">
        <label class="field suggest"><span>Hisse</span>
          <input name="symbol_q" placeholder="Kod ya da şirket adı: THYAO, Aselsan…" autocomplete="off" required>
          <input type="hidden" name="symbol">
          <ul id="sym-list" hidden></ul>
        </label>
      </div>`}
      <label class="field"><span id="qty-label">${isEdit ? (TYPE[existing.asset_type].unit === 'gram' ? 'Gram' : 'Adet') : 'Adet'}</span>
        <input name="quantity" type="number" step="any" min="0.0001" required inputmode="decimal" value="${isEdit ? existing.quantity : ''}"></label>
      <label class="field"><span>Birim maliyet (₺)</span>
        <input name="cost_price" type="number" step="any" min="0.0001" required inputmode="decimal" value="${isEdit ? existing.cost_price : ''}"></label>
      <p class="price-hint" id="price-hint"></p>
      <label class="field"><span>Alış tarihi (isteğe bağlı)</span>
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
    const symQ = form.symbol_q, symHidden = form.symbol, list = dlg.querySelector('#sym-list');

    form.querySelectorAll('input[name=asset_type]').forEach(r => r.addEventListener('change', () => {
      const t = TYPE[r.value];
      symWrap.hidden = r.value !== 'bist';
      symQ.required = r.value === 'bist';
      qtyLabel.textContent = t.unit === 'gram' ? 'Gram' : 'Adet';
      hint.textContent = '';
      if (r.value !== 'bist') showLivePrice(r.value);
    }));

    symQ.addEventListener('input', () => {
      symHidden.value = ''; hint.textContent = '';
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
        showLivePrice('bist', code);
      }));
    });
    symQ.addEventListener('blur', () => setTimeout(() => { list.hidden = true; }, 180));
  } else if (existing.current_price != null) {
    hint.innerHTML = `Güncel fiyat: <b class="num">${money(existing.current_price)}</b>`;
  }

  if (isEdit) {
    dlg.querySelector('#del-btn').addEventListener('click', async () => {
      if (!confirm(TYPE[existing.asset_type].name(existing.symbol) + ' pozisyonu silinsin mi? Bu geri alınamaz.')) return;
      try {
        await api('/portfolio/holdings/' + existing.id, { method: 'DELETE' });
        dlg.close();
        toast('Pozisyon silindi.');
        await refreshSummary();
      } catch (ex) { err.textContent = ex.message; }
    });
  }

  form.addEventListener('submit', async e => {
    e.preventDefault();
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
        let symbol = assetType === 'bist' ? form.symbol.value : assetType;
        if (assetType === 'bist' && !symbol) {
          const typed = form.symbol_q.value.trim().toLocaleUpperCase('tr-TR').split(' ')[0];
          if (state.symbols.some(s => s.c === typed)) symbol = typed;
          else throw new Error('Hisseyi listeden seç — kod ya da şirket adı yazınca öneriler açılır.');
        }
        await api('/portfolio/holdings', {
          method: 'POST',
          body: JSON.stringify({ asset_type: assetType, symbol, quantity: qty, cost_price: cost, purchase_date: date, note }),
        });
        toast('Pozisyon eklendi. Aynı varlığı tekrar eklersen ortalama maliyet hesaplanır.');
      }
      dlg.close();
      await refreshSummary();
    } catch (ex) { err.textContent = ex.message; btn.disabled = false; }
  });
}

/* ---------- başlangıç ---------- */
document.addEventListener('click', e => {
  const um = document.getElementById('user-menu');
  if (um && !um.hidden && !e.target.closest('.menu')) um.hidden = true;
});
applyTheme();
if (token()) enterApp(); else renderAuth();
