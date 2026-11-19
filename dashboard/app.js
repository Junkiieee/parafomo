'use strict';
// Parafomo Panel v2 — telefona uygulama gibi eklenen sade panel (PWA).
// Veri: GET /api/durum. Yazan uçlar X-Dash: 1 başlığı ister. Tüm metinler esc() ile basılır.

const TZ = 'Europe/Istanbul';
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const sayi = (n) => (n == null || Number.isNaN(Number(n)) ? '–' : Number(n).toLocaleString('tr-TR'));
const YT_ID = /^[\w-]{6,20}$/;

const BASLIK = { ozet: 'Özet', icerik: 'İçerik', web: 'Web sitesi', gorevler: 'Görevler', kontrol: 'Kontrol' };
const MOTOR = { iso: 'İzometrik', hf: 'HyperFrames', dossier: 'Dosya', news: 'Haber', defter: 'Ekonomi Defteri', klasik: 'Klasik' };
const IKON = {
  yt: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M21.6 7.2a2.5 2.5 0 0 0-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4A2.5 2.5 0 0 0 2.4 7.2 26 26 0 0 0 2 12a26 26 0 0 0 .4 4.8 2.5 2.5 0 0 0 1.8 1.8C5.8 19 12 19 12 19s6.2 0 7.8-.4a2.5 2.5 0 0 0 1.8-1.8A26 26 0 0 0 22 12a26 26 0 0 0-.4-4.8zM10 15V9l5.2 3z"/></svg>',
  ig: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.5" cy="6.5" r="1.3" fill="currentColor"/></svg>',
  ok: '<svg class="ok" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  tik: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12l5 5 9-10" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
};

let S = null;           // son durum (/api/durum)
let sekme = 'ozet';
let taslak = '';        // "Bana yaz" kutusundaki yazı (yeniden çizimde kaybolmasın)
let ekGorsel = null;    // eklenecek görsel (data URL)
let sonYukleme = 0;

try { sekme = localStorage.getItem('pf-sekme') || 'ozet'; } catch (e) { /* özel mod */ }
if (!BASLIK[sekme]) sekme = 'ozet';

// ---------------------------------------------------------------- yardımcılar
async function api(yol, secenek = {}) {
  const r = await fetch(yol, {
    credentials: 'same-origin',
    ...secenek,
    headers: { 'Content-Type': 'application/json', 'X-Dash': '1', ...(secenek.headers || {}) },
  });
  if (r.status === 401 && yol !== '/api/giris') {
    S = null;
    girisGoster();
    throw new Error('Giriş gerekli');
  }
  let j = {};
  try { j = await r.json(); } catch (e) { /* gövdesiz yanıt */ }
  // 422 (ör. çok uzun metin) detail'i dizi döner → "[object Object]" yerine okunur mesaj
  const detay = Array.isArray(j.detail) ? (r.status === 422 ? 'Gönderdiğin metin ya da görsel çok büyük.' : '') : j.detail;
  if (!r.ok) throw new Error(detay || `Bir sorun oldu (${r.status}).`);
  return j;
}
const gonder = (yol, govde) => api(yol, { method: 'POST', body: JSON.stringify(govde || {}) });

let bildirimZamani;
function bildir(metin) {
  const b = $('#bildirim');
  b.textContent = metin;
  b.classList.add('goster');
  clearTimeout(bildirimZamani);
  bildirimZamani = setTimeout(() => b.classList.remove('goster'), 2800);
}

const bicim = (d, o) => new Intl.DateTimeFormat('tr-TR', { timeZone: TZ, ...o }).format(d);
const gunAnahtari = (d) => new Intl.DateTimeFormat('en-CA', { timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit' }).format(d);
const saat = (iso) => bicim(new Date(iso), { hour: '2-digit', minute: '2-digit' });

function gunAdi(iso) {
  const d = new Date(iso);
  const k = gunAnahtari(d);
  const t = bicim(d, { day: 'numeric', month: 'long', weekday: 'long' });
  if (k === gunAnahtari(new Date())) return `Bugün · ${t}`;
  if (k === gunAnahtari(new Date(Date.now() + 864e5))) return `Yarın · ${t}`;
  return t;
}

function zamanMetni(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const k = gunAnahtari(d);
  if (k === gunAnahtari(new Date())) return `bugün ${saat(iso)}`;
  if (k === gunAnahtari(new Date(Date.now() - 864e5))) return `dün ${saat(iso)}`;
  if (k === gunAnahtari(new Date(Date.now() + 864e5))) return `yarın ${saat(iso)}`;
  return `${bicim(d, { day: 'numeric', month: 'short' })} ${saat(iso)}`;
}

function kisaTarih(s) {
  if (/^\d{4}-\d{2}-\d{2}$/.test(s || '')) return bicim(new Date(`${s}T12:00:00+03:00`), { day: 'numeric', month: 'short' });
  return s || '';
}

function fark(yeni, eski) {
  if (yeni == null || !eski) return '';
  const p = Math.round(((yeni - eski) / eski) * 100);
  if (p === 0) return '<span class="fark">±%0</span>';
  return `<span class="fark ${p > 0 ? 'yukari' : 'asagi'}">${p > 0 ? '▲' : '▼'} %${Math.abs(p)}</span>`;
}

const acikMi = (anahtar) => (S?.kontrol || []).find((k) => k.anahtar === anahtar)?.acik !== false;

// ---------------------------------------------------------------- giriş
function girisGoster(hata = '') {
  $('#ust').hidden = true;
  $('#sekmeler').hidden = true;
  perdeKapat();
  const ekran = $('#ekran');
  ekran.className = '';
  ekran.innerHTML = `
    <div class="giris"><form class="kutu" id="girisFormu">
      <img src="/logo.png" alt="" width="54" height="54">
      <h1>Parafomo Panel</h1>
      <input class="gizli" type="text" name="username" autocomplete="username" value="kaan" tabindex="-1" aria-hidden="true">
      <input type="password" id="sifre" name="password" autocomplete="current-password" placeholder="Şifre" required aria-label="Şifre">
      <button class="btn ana genis" type="submit">Giriş yap</button>
      <p class="hata" id="girisHata">${esc(hata)}</p>
    </form></div>`;
  $('#girisFormu').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.disabled = true;
    try {
      await gonder('/api/giris', { sifre: $('#sifre').value });
      await yukle();
    } catch (err) {
      $('#girisHata').textContent = err.message;
      btn.disabled = false;
    }
  });
  setTimeout(() => $('#sifre')?.focus(), 60);
}

// ---------------------------------------------------------------- yükle + çiz
async function yukle(sessiz = false) {
  const btn = $('#yenile');
  btn?.classList.add('donuyor');
  try {
    S = await api('/api/durum');
    sonYukleme = Date.now();
    $('#ust').hidden = false;
    $('#sekmeler').hidden = false;
    $('#ekran').className = 'ekran';
    // yazarken yeniden çizip imleci kaçırma
    if (!(sessiz && document.activeElement?.id === 'istekMetin')) ciz();
    if (S.toplaniyor) setTimeout(() => yukle(true), 15000);
  } catch (err) {
    if (err.message !== 'Giriş gerekli' && !sessiz) bildir(err.message);
  } finally {
    btn?.classList.remove('donuyor');
  }
}

let hizliZamanlayici = null;
function cevapBekleniyor() {   // cevap beklenirken 20 sn'de bir yenile (normalde 5 dk)
  if (!S) return false;
  return (S.istekler || []).some((i) => i.durum === 'yeni' || i.durum === 'okundu')
    || Object.values(S.kanallar || {}).some((k) => k.onay && !k.onay.not);
}

function ciz() {
  if (!S) return;
  clearTimeout(hizliZamanlayici);
  if (cevapBekleniyor()) hizliZamanlayici = setTimeout(() => { if (document.visibilityState === 'visible') yukle(true); }, 20000);
  $('#baslik').textContent = BASLIK[sekme];
  $$('#sekmeler button').forEach((b) => b.classList.toggle('acik', b.dataset.sekme === sekme));
  $('#gorevNokta').hidden = !((S.gorevler || []).some((g) => !g.yaptim) || (S.harcamalar || []).some((h) => !h.karar));
  const CIZ = { ozet: ozetHtml, icerik: icerikHtml, web: webHtml, gorevler: gorevlerHtml, kontrol: kontrolHtml };
  $('#ekran').innerHTML = (CIZ[sekme] || ozetHtml)();
  $$('.cubuk i[data-h]').forEach((i) => { i.style.height = `${Math.max(3, Number(i.dataset.h))}%`; });
  $$('.ilerleme i[data-w]').forEach((i) => { i.style.width = `${Math.min(100, Math.max(1, Number(i.dataset.w)))}%`; });
  const ta = $('#istekMetin');
  if (ta) {
    ta.value = taslak;
    ta.addEventListener('input', () => { taslak = ta.value; });
  }
  if (ekGorsel && $('#ekAlan')) {
    $('#ekAlan').hidden = false;
    $('#ekOnizleme').src = ekGorsel;
  }
}

function sekmeSec(s) {
  sekme = s;
  try { localStorage.setItem('pf-sekme', s); } catch (e) { /* özel mod */ }
  ciz();
  window.scrollTo(0, 0);
}

// ---------------------------------------------------------------- ortak parçalar
function gunlukHtml() {
  const g = S.gunluk;
  if (!g || !(g.maddeler || []).length) return '';
  return `<div class="kart gunluk"><div class="t">${esc(kisaTarih(g.tarih))} · Claude'dan not</div>
    <ul>${g.maddeler.map((m) => `<li>${esc(m)}</li>`).join('')}</ul></div>`;
}

function planHtml(ad) {
  const k = S.kanallar?.[ad];
  if (!k) return '';
  const cip = k.onay ? '<span class="cip iyi">Onaylandı</span>' : '<span class="cip uyari">Onayını bekliyor</span>';
  const alt = k.onay
    ? `<p class="soluk kucuk">${esc(zamanMetni(k.onay.zaman))} onayladın. Değişiklik istersen Kontrol → Bana yaz.</p>
       ${k.onay.not ? `<div class="cevap-kutu"><b>Claude:</b> ${esc(k.onay.not)}</div>` : '<div class="cevap-kutu soluk">Onayın iletildi, en geç 10 dakikada buraya yazarım.</div>'}`
    : `<div class="butonlar"><button type="button" class="btn ana" data-plan-onay="${esc(ad)}">Planı onayla</button>
       <button type="button" class="btn" data-plan-degis="${esc(ad)}">Değişiklik iste</button></div>`;
  return `<details class="kart plan">
    <summary><div class="sol"><span>${esc(k.baslik)} planı ${cip}</span><span class="hedef">Hedef: ${esc(k.hedef)}</span></div>${IKON.ok}</summary>
    <div class="govde">
      <p class="teshis">${esc(k.teshis)}</p>
      <ol>${(k.plan || []).map((m) => `<li>${esc(m)}</li>`).join('')}</ol>
      <div class="hedefler"><div><b>Hedef:</b> ${esc(k.hedef)}</div>${k.ara_hedef ? `<div><b>Ara hedef:</b> ${esc(k.ara_hedef)}</div>` : ''}</div>
      ${alt}
    </div></details>`;
}

// igGider=false: bu yuva Instagram'a gitmez (günde 1 Reel: günün ilk yayını; sunucu yuva.ig ile bildirir)
function kanalIkonlari(igGider = true) {
  const ig = acikMi('instagram') && igGider;
  return `<span class="kanal yt${acikMi('youtube') ? '' : ' kapali'}" title="YouTube">${IKON.yt}</span>`
    + `<span class="kanal ig${ig ? '' : ' kapali'}" title="${igGider ? 'Instagram' : "Instagram'a gitmez (günde 1 Reel)"}">${IKON.ig}</span>`;
}

function durumCipi(v) {
  return {
    onaylandi: '<span class="cip iyi">Hazır</span>',
    bekliyor: '<span class="cip uyari">Onay bekliyor</span>',
    hata: '<span class="cip kotu">Hata</span>',
    reddedildi: '<span class="cip">Çıkarıldı</span>',
    yayinlandi: '<span class="cip marka">Yayında</span>',
  }[v.durum] || '';
}

const kapak = (v) => (v.video
  ? `<img class="kapak" src="/api/video/${Number(v.no)}.jpg" alt="" loading="lazy">`
  : '<div class="kapak yer">▶</div>');

// ---------------------------------------------------------------- ÖZET (hedef panosu)
function kpiDegeri(yol) {
  return String(yol || '').split('.').reduce((o, k) => (o == null ? o : o[k]), S.kpi || {});
}

// Site kayıtları (veritabanından; çerez onayından etkilenmez). Test kayıtları collect.py'de ayıklanır.
function kayitDetay() {
  const k = S.kpi?.kayit;
  if (!k) return '';
  return `zam alarmı ${sayi(k.zam_onayli)} · bülten ${sayi(k.bulten_onayli)} onaylı · onay bekleyen ${sayi(k.bekleyen)}`
    + ` · son 7 gün yeni ${sayi(k.yeni_7g)} · portföy üyesi ${sayi(k.uye)}`;
}

function ozetHtml() {
  const hedefler = (S.hedefler || []).map((h) => {
    const v = h.kpi ? kpiDegeri(h.kpi) : h.simdi;
    const yuzde = h.hedef ? (100 * (Number(v) || 0)) / h.hedef : 0;
    const ek = String(h.kpi || '').startsWith('kayit.') ? kayitDetay() : '';
    return `<div class="hedef-s"><div class="ust-s"><span class="ad">${esc(h.baslik)}</span>
      <span class="deger">${sayi(v)} <small>/ ${sayi(h.hedef)} ${esc(h.birim || '')}</small></span></div>
      <div class="ilerleme"><i data-w="${yuzde.toFixed(1)}"></i></div>
      <div class="not-s">${esc(h.not || '')}${h.tarih ? ` · hedef tarihi ${esc(kisaTarih(h.tarih))}` : ''}</div>
      ${ek ? `<div class="not-s">${esc(ek)}</div>` : ''}${h.uyari ? `<div class="not-s uyari">${esc(h.uyari)}</div>` : ''}</div>`;
  }).join('');
  const cipDurum = (d) => ({ hazir: 'iyi', calisiyor: 'iyi', deneniyor: 'marka', sirada: '', bekliyor: 'uyari', durdu: 'kotu', sonuc: 'iyi' }[d] ?? '');
  const DURUM = { hazir: 'Hazır', calisiyor: 'Çalışıyor', deneniyor: 'Deneniyor', sirada: 'Sırada', bekliyor: 'Görev bekliyor', durdu: 'Durduruldu', sonuc: 'Sonuç var' };
  const gelir = (S.gelir || []).map((g) => `<div class="gelir-s"><div><div class="ad">${esc(g.yol)}</div><div class="ac">${esc(g.aciklama || '')}</div></div>
    <span class="cip ${cipDurum(g.durum)}">${esc(DURUM[g.durum] || g.durum || '')}</span></div>`).join('');
  // Deneme sayacı (sunucu: gun/sure/gecikti; panel.py deneme ile başlangıç + ölçüt yazılır)
  const sayac = (f) => (f.gun ? `<span class="cip ${f.gecikti ? 'kotu' : ''}">${f.gecikti ? 'süre doldu' : `gün ${Number(f.gun)}/${Number(f.sure)}`}</span>` : '');
  const fikirler = (S.fikirler || []).map((f) => `<div class="fikir-s"><div><div class="ad">${esc(f.baslik)}</div><div class="ac">${esc(f.sonuc || f.neden || '')}</div>
    ${f.olcut && f.durum === 'deneniyor' ? `<div class="ac"><b>Ölçüt:</b> ${esc(f.olcut)}</div>` : ''}</div>
    <div class="cipler">${sayac(f)}<span class="cip ${cipDurum(f.durum)}">${esc(DURUM[f.durum] || f.durum || '')}</span></div></div>`).join('');
  const nGorev = (S.gorevler || []).filter((g) => !g.yaptim).length + (S.harcamalar || []).filter((h) => !h.karar).length;
  return `${gunlukHtml()}
  ${nGorev ? `<button type="button" class="btn ana gorev-git" data-sekme="gorevler">Senden bekleyen ${nGorev} iş var →</button>` : ''}
  <h2>Hedefe ilerleme</h2><div class="kart liste">${hedefler || '<div class="bos">Hedefler yazılıyor.</div>'}</div>
  <h2>Para kazanma yolları</h2><div class="kart liste">${gelir || '<div class="bos">Hazırlanıyor.</div>'}</div>
  <h2>Denemeler <small>fikir → deneme → sonuç</small></h2><div class="kart liste">${fikirler || '<div class="bos">Hazırlanıyor.</div>'}</div>`;
}

// ---------------------------------------------------------------- GÖREVLER (Kaan'ın işleri + harcama onayı)
function gorevlerHtml() {
  const g = S.gorevler || [];
  const h = S.harcamalar || [];
  const harc = h.map((x) => `<div class="kart harcama"><div class="ust-s"><span class="tutar">${sayi(x.tutar)} TL</span></div>
    <div class="ad">${esc(x.baslik)}</div><p class="soluk kucuk">${esc(x.neden || '')}</p>
    ${x.karar ? `<p class="kucuk"><span class="cip ${x.karar.durum === 'onaylandi' ? 'iyi' : 'kotu'}">${x.karar.durum === 'onaylandi' ? 'Onayladın' : 'Reddettin'}</span></p>`
      : `<div class="butonlar"><button type="button" class="btn ana" data-harcama="${esc(x.id)}" data-karar="onayla">Onayla</button>
         <button type="button" class="btn" data-harcama="${esc(x.id)}" data-karar="reddet">Reddet</button></div>`}</div>`).join('');
  return `<p class="oto-not">Bunlar yalnız senin yapabileceğin işler (hesap açma, başvuru, paylaşım). Her birinin adımlarını yazdım; "Yaptım" deyince kontrol edip kapatırım.</p>
    <h2>Senin görevlerin <small>${g.filter((x) => !x.yaptim).length} açık</small></h2>
    ${g.map(gorevHtml).join('') || '<div class="kart bos">Şu an senden beklenen bir şey yok.</div>'}
    ${h.length ? `<h2>Harcama onayı <small>aylık sınır 1.000 TL</small></h2>${harc}` : ''}`;
}

// ---------------------------------------------------------------- İÇERİK
function icerikHtml() {
  const yt = S.kpi?.youtube || {};
  const ig = S.kpi?.instagram || {};
  const ic = S.icerik || {};
  const erisim = (ic.yayinlanan || []).map((v) => v.ig_erisim).filter((x) => x != null);
  const igOrt = erisim.length ? Math.round(erisim.reduce((a, b) => a + b, 0) / erisim.length) : null;

  const gunler = [];
  for (const y of ic.yuvalar || []) {
    const ad = gunAdi(y.zaman);
    let g = gunler[gunler.length - 1];
    if (!g || g.ad !== ad) { g = { ad, yuvalar: [] }; gunler.push(g); }
    g.yuvalar.push(y);
  }
  const takvim = gunler.slice(0, 5).map((g) => `<div class="gun"><div class="gun-ad">${esc(g.ad)}</div>
    <div class="kart liste">${g.yuvalar.map(yuvaHtml).join('')}</div></div>`).join('');

  return `${gunlukHtml()}
  <div class="metrikler">
    <div class="kart metrik"><div class="e">YouTube</div><div class="d">${sayi(yt.abone)}<small>abone</small></div>
      <div class="a">${sayi(yt.son?.izlenme)} izlenme/hafta ${fark(yt.son?.izlenme, yt.onceki?.izlenme)}</div></div>
    <div class="kart metrik"><div class="e">Instagram</div><div class="d">${sayi(ig.takipci)}<small>takipçi</small></div>
      <div class="a">Reel başına ort. ${sayi(igOrt)} kişi</div></div>
  </div>
  ${planHtml('youtube')}
  ${planHtml('instagram')}
  ${senaryolarHtml()}
  ${(ic.bekleyen || []).length ? `<h2>Onayını bekleyenler</h2><div class="kart liste">${ic.bekleyen.map((v) => videoSatiri(v)).join('')}</div>` : ''}
  ${(ic.sorunlu || []).length ? `<h2>Sorunlu</h2><div class="kart liste">${ic.sorunlu.map((v) => videoSatiri(v)).join('')}</div>` : ''}
  <h2>Sıradaki yayınlar <small>her gün ${esc((ic.saatler || []).join(' ve '))}</small></h2>
  ${takvim || '<div class="kart bos">Planlı yayın yok.</div>'}
  <h2>Uzun videolar <small>YouTube</small></h2>
  <div class="kart liste">${(ic.uzun || []).map(uzunHtml).join('') || '<div class="bos">Yok.</div>'}</div>
  <h2>Yayınlananlar <small>son 12 video</small></h2>
  <div class="kart liste">${(ic.yayinlanan || []).map(yayinHtml).join('') || '<div class="bos">Henüz yok.</div>'}</div>`;
}

function senaryolarHtml() {
  const lst = S.senaryolar || [];
  if (!lst.length) return '';
  return `<h2>Senaryo taslakları <small>onayınla üretime girer</small></h2>${lst.map((x) => {
    const uretildi = x.karar && x.karar.durum === 'uretildi';
    const cip = uretildi ? '<span class="cip marka">Üretildi</span>' : x.karar ? '<span class="cip iyi">Onaylandı</span>' : '<span class="cip uyari">Onayını bekliyor</span>';
    const alt = x.karar
      ? `${uretildi ? '' : `<p class="soluk kucuk">${esc(zamanMetni(x.karar.zaman))} onayladın.</p>`}${x.karar.not ? `<div class="cevap-kutu"><b>Claude:</b> ${esc(x.karar.not)}</div>` : ''}`
      : `<div class="butonlar"><button type="button" class="btn ana" data-senaryo-onay="${esc(x.id)}">Senaryoyu onayla</button>
         <button type="button" class="btn" data-senaryo-degis="${esc(x.id)}">Değişiklik iste</button></div>`;
    return `<details class="kart plan senaryo"><summary><div class="sol"><span>${esc(x.baslik)} ${cip}</span>
      <span class="hedef">${esc(x.kalip)} · ${esc(x.sure)}</span></div>${IKON.ok}</summary><div class="govde">
      <p class="teshis">Kanca kartı (ilk 2 sn): <b>${esc(x.kanca_karti)}</b></p>
      ${x.duygu ? `<p class="teshis"><b>Duygu yolu:</b> ${esc(x.duygu)}</p>` : ''}
      <ol>${(x.satirlar || []).map((m) => `<li>${esc(m)}</li>`).join('')}</ol>
      <p class="teshis"><b>Görüntü:</b> ${esc(x.gorsel)}</p>
      <div class="hedefler">${(x.kaynak || []).map((k) => `<div>${esc(k)}</div>`).join('')}</div>${alt}</div></details>`;
  }).join('')}`;
}

function yuvaHtml(y) {
  const v = y.video;
  if (!v) {
    return `<div class="satir bos-yuva"><div class="saat">${saat(y.zaman)}</div>
      <div class="govde"><div class="bas soluk">${esc(y.not || 'Boş')}</div></div></div>`;
  }
  return `<button type="button" class="satir" data-video="${Number(v.no)}"><div class="saat">${saat(y.zaman)}</div>${kapak(v)}
    <div class="govde"><div class="bas">${esc(v.baslik)}</div>
    <div class="alt">${durumCipi(v)}${kanalIkonlari(y.ig !== false)}</div></div></button>`;
}

function videoSatiri(v) {
  return `<button type="button" class="satir" data-video="${Number(v.no)}">${kapak(v)}
    <div class="govde"><div class="bas">${esc(v.baslik)}</div><div class="alt">${durumCipi(v)}${kanalIkonlari()}</div></div></button>`;
}

function yayinHtml(v) {
  const oy = v.oy === '+' ? ' · 👍' : v.oy === '-' ? ' · 👎' : '';
  return `<button type="button" class="satir" data-video="${Number(v.no)}">${kapak(v)}
    <div class="govde"><div class="bas">${esc(v.baslik)}</div>
    <div class="alt"><span>${esc(zamanMetni(v.yayinlandi))}${oy}</span>
      <span class="kanal yt" title="YouTube izlenme">${IKON.yt}<span class="sayi">${sayi(v.izlenme)}</span></span>
      <span class="kanal ig" title="Instagram erişim">${IKON.ig}<span class="sayi">${sayi(v.ig_erisim)}</span></span></div></div></button>`;
}

function uzunHtml(u) {
  const cip = {
    planlandi: '<span class="cip iyi">Planlandı</span>', yayinda: '<span class="cip marka">Yayında</span>',
    hazirlanacak: '<span class="cip">Hazırlanacak</span>', hazir: '<span class="cip">Hazır</span>',
  }[u.durum] || '';
  const img = u.kapak
    ? `<img class="kapak yatay" src="/api/uzun/${encodeURIComponent(u.slug)}.jpg" alt="" loading="lazy">`
    : '<div class="kapak yatay yer">▶</div>';
  const zaman = u.zaman ? `${bicim(new Date(u.zaman), { day: 'numeric', month: 'long' })} ${saat(u.zaman)}` : '';
  const ic = `${img}<div class="govde"><div class="bas">${esc(u.baslik)}</div><div class="alt">${cip}<span>${esc(zaman)}</span>
    ${u.izlenme != null ? `<span class="kanal yt">${IKON.yt}<span class="sayi">${sayi(u.izlenme)}</span></span>` : ''}</div></div>`;
  return u.yt && YT_ID.test(u.yt)
    ? `<a class="satir" href="https://youtu.be/${u.yt}" target="_blank" rel="noopener">${ic}</a>`
    : `<div class="satir">${ic}</div>`;
}

function videoBul(no) {
  const ic = S?.icerik || {};
  for (const y of ic.yuvalar || []) if (y.video && y.video.no === no) return { v: y.video, zaman: y.zaman, ig: y.ig };
  for (const v of [...(ic.bekleyen || []), ...(ic.sorunlu || []), ...(ic.yayinlanan || [])]) if (v.no === no) return { v };
  return null;
}

function videoAc(no) {
  const b = videoBul(no);
  if (!b) return;
  const { v, zaman, ig } = b;
  let html = v.video
    ? `<video controls playsinline preload="metadata" poster="/api/video/${Number(v.no)}.jpg" src="/api/video/${Number(v.no)}.mp4"></video>`
    : '<p class="bos">Video dosyası yok.</p>';
  html += `<h3>${esc(v.baslik)}</h3><div class="bilgi">
    ${zaman ? `<span>${esc(gunAdi(zaman))}, ${saat(zaman)}</span>` : ''}
    ${zaman && ig !== undefined ? `<span>${ig ? 'YouTube + Instagram' : "YouTube (Instagram'a gitmez: günde 1 Reel)"}</span>` : ''}
    ${v.yayinlandi ? `<span>${esc(zamanMetni(v.yayinlandi))} yayınlandı</span>` : ''}
    <span>${esc(MOTOR[v.motor] || v.motor || '')}</span><span>#${Number(v.no)}</span></div>`;
  if (v.durum === 'yayinlandi') {
    html += `<div class="rakamlar"><div><b>${sayi(v.izlenme)}</b><span>YouTube izlenme</span></div>
      <div><b>${sayi(v.ig_erisim)}</b><span>Instagram erişim</span></div></div><div class="butonlar">
      ${v.yt && YT_ID.test(v.yt) ? `<a class="btn" href="https://youtube.com/shorts/${v.yt}" target="_blank" rel="noopener">YouTube'da aç</a>` : ''}
      ${v.ig && /^https:\/\/(www\.)?instagram\.com\//.test(v.ig) ? `<a class="btn" href="${esc(v.ig)}" target="_blank" rel="noopener">Instagram'da aç</a>` : ''}</div>
      <div class="butonlar"><button type="button" class="btn${v.oy === '+' ? ' ana' : ''}" data-eylem="begen" data-no="${Number(v.no)}">👍 Beğendim</button>
      <button type="button" class="btn${v.oy === '-' ? ' ana' : ''}" data-eylem="begenme" data-no="${Number(v.no)}">👎 Beğenmedim</button></div>`;
  } else if (v.durum === 'bekliyor') {
    html += `<div class="butonlar"><button type="button" class="btn ana" data-eylem="onayla" data-no="${Number(v.no)}">Onayla</button>
      <button type="button" class="btn tehlike" data-eylem="cikar" data-no="${Number(v.no)}">Yayından çıkar</button></div>`;
  } else if (v.durum === 'onaylandi') {
    html += `<p class="soluk kucuk">Bu video otomatik çıkacak. İstemiyorsan çıkar; yerine sıradaki video geçer.</p>
      <div class="butonlar"><button type="button" class="btn tehlike" data-eylem="cikar" data-no="${Number(v.no)}">Yayından çıkar</button></div>`;
  } else if (v.durum === 'hata') {
    html += `<p class="soluk kucuk">${esc(v.hata || 'Yayın sırasında bir hata oldu.')}</p>`;
  }
  perdeAc(html);
}

// ---------------------------------------------------------------- WEB
function webHtml() {
  const w = S.kpi?.web || {};
  const hs = w.haftalar || [];
  const enCok = Math.max(1, ...hs.map((h) => h.tik || 0));
  const wb = S.web || {};
  const grafik = hs.length ? `<div class="kart grafik"><div class="gb"><span>Haftalık Google tıkı · son 8 hafta</span></div>
    <div class="cubuklar" role="img" aria-label="Haftalık Google tık sayıları">${hs.map((h, i) => `<div class="cubuk${i === hs.length - 1 ? ' son' : ''}">
      <i data-h="${Math.round(((h.tik || 0) / enCok) * 100)}"></i><span>${sayi(h.tik)}</span></div>`).join('')}</div></div>` : '';
  const k = S.kpi?.kayit || {};
  // GA4 17 Kasım'dan beri yalnız çerez onaylıları sayıyor (seri kırık): kıyas yalnız iki pencere aynı taraftaysa
  const ga4Kiyas = w.ziyaret_kiyas !== false;
  const ga4 = w.ziyaret_7g == null ? '' : `<p class="oto-not">GA4 ziyaret (7 gün): ${sayi(w.ziyaret_7g)}${ga4Kiyas
    ? ` · önceki ${sayi(w.ziyaret_onceki)} ${fark(w.ziyaret_7g, w.ziyaret_onceki)}` : ''}${w.ga4_not
    ? ` · <span class="uyari-yazi">${esc(w.ga4_not)}${ga4Kiyas ? '' : ' Önceki haftayla kıyaslanmaz.'}</span>` : ''}</p>`;
  return `<div class="metrikler uc">
    <div class="kart metrik"><div class="e">Google tık</div><div class="d">${sayi(w.son?.tik)}</div><div class="a">önceki ${sayi(w.onceki?.tik)} ${fark(w.son?.tik, w.onceki?.tik)}</div></div>
    <div class="kart metrik"><div class="e">Gösterim</div><div class="d">${sayi(w.son?.gosterim)}</div><div class="a">önceki ${sayi(w.onceki?.gosterim)} ${fark(w.son?.gosterim, w.onceki?.gosterim)}</div></div>
    <div class="kart metrik"><div class="e">Kayıt (onaylı)</div><div class="d">${sayi(k.onayli)}</div><div class="a">7 günde ${sayi(k.yeni_7g)} yeni ${fark(k.yeni_7g, k.yeni_onceki_7g)}</div></div>
  </div>
  <p class="oto-not">Google: son 7 gün, veri 2–3 gün geriden gelir. Kayıt: ${esc(kayitDetay() || 'alınamadı')}.</p>
  ${w.insan_7g != null ? `<p class="oto-not">Sitede görüntülenen sayfa (7 gün, çerezsiz sayım): <b>${sayi(w.insan_7g)}</b> · önceki ${sayi(w.insan_onceki)} ${fark(w.insan_7g, w.insan_onceki)}
    · Cloudflare, Türkiye'den tarayıcılar; eğilim içindir.</p>` : ''}
  ${ga4}
  ${grafik}
  ${planHtml('web')}
  <h2>Yapılacak</h2>
  <div class="kart liste">${(wb.yapilacak || []).map(yapilacakHtml).join('') || '<div class="bos">Liste boş.</div>'}</div>
  <h2>Yapıldı <small>son 3 hafta</small></h2>
  <div class="kart liste">${(wb.yapildi || []).map(yapildiHtml).join('') || '<div class="bos">Henüz yok.</div>'}</div>
  ${wb.oto_guncelleme_7g ? `<p class="oto-not">Ayrıca son 7 günde ${sayi(wb.oto_guncelleme_7g)} otomatik veri güncellemesi yapıldı (altın/döviz fiyatları, halka arz takvimi vb.).</p>` : ''}`;
}

function yapilacakHtml(x) {
  const d = x.durum || 'sirada';
  const isaret = d === 'yapildi' ? `<span class="isaret yapildi">${IKON.tik}</span>` : `<span class="isaret${d === 'yapiliyor' ? ' yapiliyor' : ''}"></span>`;
  return `<div class="is">${isaret}<div class="govde">${esc(x.baslik)}<div class="ust-bilgi"><span>${esc(kisaTarih(x.tarih))}</span>
    ${d === 'yapiliyor' ? '<span class="cip uyari">Yapılıyor</span>' : ''}</div></div></div>`;
}

function yapildiHtml(x) {
  const link = x.link && /^\/[\w\-/]*$/.test(x.link) ? `https://parafomo.com${x.link}` : null;
  const ic = `${esc(x.baslik)}${link ? ' <span class="ok-dis">↗</span>' : ''}`;
  return `<div class="is"><span class="isaret yapildi">${IKON.tik}</span><div class="govde">
    ${link ? `<a href="${link}" target="_blank" rel="noopener">${ic}</a>` : ic}
    <div class="ust-bilgi"><span>${esc(kisaTarih(x.tarih))}</span>${x.oto ? '<span>otomatik</span>' : ''}</div></div></div>`;
}

// ---------------------------------------------------------------- KONTROL
function kontrolHtml() {
  const istekler = S.istekler || [];
  return `<h2>Otomatik sistem</h2>
  <div class="kart liste">${(S.kontrol || []).map(anahtarHtml).join('')}</div>
  <h2>Bana yaz</h2>
  <p class="dinleme${S.claude?.cevrimici ? ' acik' : ''}">${S.claude?.cevrimici
    ? '● Claude çevrimiçi: panelde yazdığın ve yaptığın her şey en geç 10 dakikada bana ulaşır.'
    : '○ Claude şu an çevrimdışı: yazdıklarını ilk fırsatta, en geç sabah işlerim.'}</p>
  <div class="kart yaz">
    <textarea id="istekMetin" maxlength="4000" placeholder="İstek, fikir ya da düzeltme yaz. Okuyup cevabını buraya yazarım."></textarea>
    <div class="ek" id="ekAlan" hidden><img id="ekOnizleme" alt=""><span>Görsel eklendi</span>
      <button type="button" class="link-btn" id="gorselSil">Kaldır</button></div>
    <input type="file" id="gorselDosya" accept="image/*" hidden>
    <div class="butonlar"><button type="button" class="btn" id="gorselSec">Görsel ekle</button>
      <button type="button" class="btn ana" id="gonder">Gönder</button></div>
  </div>
  ${istekler.length ? `<h2>Yazdıkların</h2><div class="kart liste">${istekler.map(istekHtml).join('')}</div>` : ''}
  <div class="alt-bilgi">Sayılar ${S.kpi?.guncellendi ? esc(zamanMetni(S.kpi.guncellendi)) : '—'} güncellendi.
    ${(S.kpi?.hatalar || []).length ? '<br>Bazı sayılar alınamadı, eski değer gösteriliyor.' : ''}<br>
    <button type="button" class="link-btn" id="cikis">Çıkış yap</button></div>`;
}

function gorevHtml(g) {
  const link = g.link && /^https:\/\//.test(g.link) ? `<a class="btn" href="${esc(g.link)}" target="_blank" rel="noopener">Sayfayı aç</a>` : '';
  return `<div class="kart gorev"><div class="ad"><span>${esc(g.baslik)}</span>${g.sure ? `<span class="cip">${esc(g.sure)}</span>` : ''}</div>
    ${g.neden ? `<p class="soluk kucuk">${esc(g.neden)}</p>` : ''}
    ${(g.adimlar || []).length ? `<ol class="adimlar">${g.adimlar.map((a) => `<li>${esc(a)}</li>`).join('')}</ol>` : `<p>${esc(g.nasil || '')}</p>`}
    ${link ? `<div class="butonlar">${link}</div>` : ''}
    ${g.yaptim ? `<p class="kucuk soluk">${esc(zamanMetni(g.yaptim))} "yaptım" dedin; kontrol edip kapatacağım.</p>`
      : `<div class="butonlar"><button type="button" class="btn" data-gorev="${esc(g.id)}">Yaptım</button></div>`}</div>`;
}

function anahtarHtml(k) {
  return `<div class="anahtar"><div class="govde"><div class="ad">${esc(k.ad)}</div><div class="acik">${esc(k.aciklama)}</div></div>
    <label class="dugme"><input type="checkbox" data-kontrol="${esc(k.anahtar)}" data-ad="${esc(k.ad)}" ${k.acik ? 'checked' : ''} aria-label="${esc(k.ad)}"><span></span></label></div>`;
}

function istekHtml(i) {
  const cip = {
    yeni: '<span class="cip uyari">Okunmadı</span>', okundu: '<span class="cip marka">Okundu</span>',
    yapiliyor: '<span class="cip marka">Yapılıyor</span>', yapildi: '<span class="cip iyi">Yapıldı</span>',
    yapilmayacak: '<span class="cip">Yapılmayacak</span>',
  }[i.durum] || '';
  const id = Number(i.id);
  return `<div class="istek"><div class="ib"><span>${esc(zamanMetni(i.zaman))}</span>${cip}</div>
    ${i.metin ? `<div class="im">${esc(i.metin)}</div>` : ''}
    ${i.gorsel ? `<a href="/api/istek/${id}/gorsel" target="_blank"><img class="ig" src="/api/istek/${id}/gorsel" alt="Eklediğin görsel" loading="lazy"></a>` : ''}
    ${i.cevap ? `<div class="cevap-kutu"><b>Claude:</b> ${esc(i.cevap)}</div>` : ''}</div>`;
}

// ---------------------------------------------------------------- perde
function perdeAc(html) {
  $('#perdeIc').innerHTML = html;
  $('#perde').hidden = false;
  document.body.style.overflow = 'hidden';
}
function perdeKapat() {
  $('#perde video')?.pause();
  $('#perde').hidden = true;
  $('#perdeIc').innerHTML = '';
  document.body.style.overflow = '';
}

// ---------------------------------------------------------------- eylemler
async function videoEylem(no, ad) {
  if (ad === 'cikar' && !window.confirm('Bu video yayından çıkarılsın mı? Yerine sıradaki video geçer.')) return;
  try {
    await gonder(`/api/video/${Number(no)}/${ad}`);
    bildir({ cikar: 'Video yayından çıkarıldı.', onayla: 'Onaylandı, sıraya girdi.', begen: 'Beğendin olarak kaydedildi.', begenme: 'Beğenmedin olarak kaydedildi.' }[ad]);
    perdeKapat();
    await yukle(true);
  } catch (err) { bildir(err.message); }
}

async function gorselHazirla(dosya) {
  const url = URL.createObjectURL(dosya);
  try {
    const img = await new Promise((ok, red) => { const i = new Image(); i.onload = () => ok(i); i.onerror = red; i.src = url; });
    const olcek = Math.min(1, 1600 / Math.max(img.naturalWidth, img.naturalHeight));
    const c = document.createElement('canvas');
    c.width = Math.round(img.naturalWidth * olcek);
    c.height = Math.round(img.naturalHeight * olcek);
    c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
    return c.toDataURL('image/jpeg', 0.85);
  } finally { URL.revokeObjectURL(url); }
}

async function istekGonder() {
  const metin = ($('#istekMetin')?.value || '').trim();
  if (!metin && !ekGorsel) { bildir('Önce bir şey yaz.'); return; }
  const btn = $('#gonder');
  btn.disabled = true;
  try {
    await gonder('/api/istek', { metin, gorsel: ekGorsel });
    taslak = '';
    ekGorsel = null;
    bildir('Gönderildi. Okuyup cevabını buraya yazacağım.');
    await yukle(true);
  } catch (err) {
    bildir(err.message);
    btn.disabled = false;
  }
}

document.addEventListener('click', async (e) => {
  const t = e.target.closest('button, [data-kapat]');
  if (!t) return;
  if (t.dataset.kapat !== undefined) { perdeKapat(); return; }
  if (t.dataset.sekme) { sekmeSec(t.dataset.sekme); return; }
  if (t.dataset.video) { videoAc(Number(t.dataset.video)); return; }
  if (t.dataset.eylem) { videoEylem(t.dataset.no, t.dataset.eylem); return; }
  if (t.dataset.planOnay) {
    if (!window.confirm('Bu plan onaylansın mı? Onaylayınca uygulamaya geçerim.')) return;
    try { await gonder(`/api/plan/${encodeURIComponent(t.dataset.planOnay)}/onayla`); bildir('Plan onaylandı.'); await yukle(true); } catch (err) { bildir(err.message); }
    return;
  }
  if (t.dataset.planDegis) {
    taslak = `${S?.kanallar?.[t.dataset.planDegis]?.baslik || ''} planı: `;
    sekmeSec('kontrol');
    setTimeout(() => { const ta = $('#istekMetin'); if (ta) { ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length); ta.scrollIntoView({ block: 'center' }); } }, 80);
    return;
  }
  if (t.dataset.senaryoOnay) {
    if (!window.confirm('Bu senaryo onaylansın mı? Onaylayınca videosunu üretirim.')) return;
    try { await gonder(`/api/senaryo/${encodeURIComponent(t.dataset.senaryoOnay)}/onayla`); bildir('Senaryo onaylandı.'); await yukle(true); } catch (err) { bildir(err.message); }
    return;
  }
  if (t.dataset.senaryoDegis) {
    taslak = `${t.dataset.senaryoDegis} senaryosu: `;
    sekmeSec('kontrol');
    setTimeout(() => { const ta = $('#istekMetin'); if (ta) { ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length); ta.scrollIntoView({ block: 'center' }); } }, 80);
    return;
  }
  if (t.dataset.harcama) {
    const onay = t.dataset.karar === 'onayla';
    if (!window.confirm(onay ? 'Bu harcama onaylansın mı?' : 'Bu harcama reddedilsin mi?')) return;
    try { await gonder(`/api/harcama/${encodeURIComponent(t.dataset.harcama)}/${t.dataset.karar}`); bildir(onay ? 'Harcama onaylandı.' : 'Harcama reddedildi.'); await yukle(true); } catch (err) { bildir(err.message); }
    return;
  }
  if (t.dataset.gorev) {
    try { await gonder(`/api/gorev/${encodeURIComponent(t.dataset.gorev)}/yaptim`); bildir('Teşekkürler, kontrol edeceğim.'); await yukle(true); } catch (err) { bildir(err.message); }
    return;
  }
  switch (t.id) {
    case 'yenile':
      try { const r = await gonder('/api/yenile'); if (r.basladi) bildir('Sayılar güncelleniyor…'); } catch (err) { if (err.message !== 'Giriş gerekli') bildir(err.message); return; }
      await yukle();
      break;
    case 'gorselSec': $('#gorselDosya')?.click(); break;
    case 'gorselSil': ekGorsel = null; ciz(); break;
    case 'gonder': istekGonder(); break;
    case 'cikis':
      if (!window.confirm('Çıkış yapılsın mı?')) return;
      try { await gonder('/api/cikis'); } catch (err) { /* yine de çık */ }
      S = null;
      girisGoster();
      break;
    default: break;
  }
});

document.addEventListener('change', async (e) => {
  const inp = e.target;
  if (inp.matches('input[data-kontrol]')) {
    const acik = inp.checked;
    const ad = inp.dataset.ad;
    if (!acik && !window.confirm(`"${ad}" kapatılsın mı?`)) { inp.checked = true; return; }
    inp.disabled = true;
    try {
      const r = await gonder('/api/kontrol', { anahtar: inp.dataset.kontrol, acik });
      S.kontrol = r.kontrol;
      bildir(`${ad} ${acik ? 'açıldı' : 'kapatıldı'}.`);
      ciz();
    } catch (err) {
      inp.checked = !acik;
      inp.disabled = false;
      bildir(err.message);
    }
    return;
  }
  if (inp.id === 'gorselDosya' && inp.files?.[0]) {
    try { ekGorsel = await gorselHazirla(inp.files[0]); ciz(); } catch (err) { bildir('Görsel okunamadı.'); }
  }
});

// kırık kapak görseli → yer tutucu
document.addEventListener('error', (e) => {
  const t = e.target;
  if (t.tagName === 'IMG' && t.classList.contains('kapak')) {
    const d = document.createElement('div');
    d.className = `${t.className} yer`;
    d.textContent = '▶';
    t.replaceWith(d);
  }
}, true);

document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !$('#perde').hidden) perdeKapat(); });
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && S && Date.now() - sonYukleme > 30000) yukle(true);
});
setInterval(() => { if (document.visibilityState === 'visible' && S) yukle(true); }, 5 * 60 * 1000);

if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
yukle();
