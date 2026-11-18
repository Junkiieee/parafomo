/* ParaFOMO Uygulamalar — çerez onayı + GA4 (Consent Mode v2). Sitedeki CerezOnay/Analytics ile aynı kural
   (KVKK çerez rehberi 2025): onay gelene kadar analiz/reklam çerezi YAZILMAZ; "Reddet" en az "Kabul et" kadar
   görünür; ön işaret yok, duvar yok.
   Seçim: 'pf-cerez' = 'kabul' | 'red'. Sitede (parafomo.com) verilen seçim .parafomo.com çerezinden okunur
   (localStorage alan adına özel; uygulama sitenin seçimini göremiyordu). Burada verilen seçim de hem bu alan
   adının localStorage'ına hem ortak çereze yazılır.
   Bu dosya <head>'de gtag.js'ten ÖNCE, eşzamanlı yüklenir: consent 'default' config'ten önce kuyruğa girmeli. */
(function () {
  var GA = 'G-4KNGH3574V';
  var KEY = 'pf-cerez';
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  window.gtag = gtag;

  function cerezOku() {
    var m = document.cookie.match(/(?:^|;\s*)pf-cerez=(kabul|red)(?:;|$)/);
    return m ? m[1] : null;
  }
  function secim() {
    var c = cerezOku();
    if (c) return c;
    try { var v = localStorage.getItem(KEY); return v === 'kabul' || v === 'red' ? v : null; } catch (e) { return null; }
  }
  function izin(v) {
    var d = v === 'kabul' ? 'granted' : 'denied';
    return { analytics_storage: d, ad_storage: d, ad_user_data: d, ad_personalization: d };
  }

  gtag('consent', 'default', Object.assign(izin('red'), { wait_for_update: 500 }));
  var ilk = secim();
  if (ilk === 'kabul') gtag('consent', 'update', izin('kabul'));
  gtag('js', new Date());
  gtag('config', GA);

  function kaydet(v) {
    try { localStorage.setItem(KEY, v); } catch (e) { /* depolama kapalı */ }
    var alan = /(^|\.)parafomo\.com$/.test(location.hostname) ? '; Domain=.parafomo.com' : '';
    document.cookie = KEY + '=' + v + alan + '; Path=/; Max-Age=31536000; SameSite=Lax' +
      (location.protocol === 'https:' ? '; Secure' : '');
    gtag('consent', 'update', izin(v));
  }

  function bant() {
    if (document.getElementById('cerez-bant')) return;
    var el = document.createElement('div');
    el.id = 'cerez-bant';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-live', 'polite');
    el.setAttribute('aria-label', 'Çerez tercihi');
    el.style.cssText = 'position:fixed;left:12px;right:12px;bottom:12px;z-index:60;max-width:640px;margin:0 auto;' +
      'background:var(--surface,#fff);color:var(--ink,#111);border:1px solid var(--line,#dde5e1);border-radius:14px;' +
      'padding:12px 14px;box-shadow:0 8px 30px rgba(0,0,0,.18);font-size:.86rem;line-height:1.45';
    el.innerHTML = '<p style="margin:0">Uygulamayı geliştirmek için <strong>analiz</strong> çerezleri kullanmak ' +
      'istiyoruz. Reddedersen yalnız zorunlu çerezler kullanılır. <a href="https://parafomo.com/cerez-politikasi/" ' +
      'style="color:var(--brand-deep,#1e6b7f)">Ayrıntılar</a></p>' +
      '<div style="display:flex;gap:8px;margin-top:10px">' +
      '<button type="button" data-cerez="red">Reddet</button><button type="button" data-cerez="kabul">Kabul et</button></div>';
    var bs = el.querySelectorAll('button');
    for (var i = 0; i < bs.length; i++) {
      bs[i].style.cssText = 'flex:1;min-height:40px;border-radius:10px;border:1px solid var(--line,#cfd8d4);cursor:pointer;' +
        'background:var(--bg,#f6faf8);color:var(--ink,#111);font:inherit;font-weight:700';
    }
    el.addEventListener('click', function (e) {
      var b = e.target.closest && e.target.closest('[data-cerez]');
      if (!b) return;
      kaydet(b.getAttribute('data-cerez'));
      el.remove();
    });
    document.body.appendChild(el);
  }

  if (!ilk) {
    // Onay bandı sayfa yüklendikten sonra (ilk çizimi geciktirmesin). Sitedeki seçim varsa hiç görünmez.
    var goster = function () { setTimeout(bant, 400); };
    if (document.readyState === 'complete') goster();
    else window.addEventListener('load', goster, { once: true });
  } else if (!cerezOku()) {
    kaydet(ilk);   // yalnız bu alan adında kayıtlı eski seçim → ortak çereze de yaz
  }
})();
