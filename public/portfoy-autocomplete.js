/* ParaFOMO — BIST hisse arama/otomatik tamamlama (paylaşılan)
   Kullanıcı şirket ADI veya KODU yazınca doğru Yahoo ticker'ını seçer.
   Kök sorun: "TÜPRAŞ/TUPRAS" yazıldı ama doğru kod TUPRS → canlı veri gelmiyordu. */
(function () {
  var SYMS = null, loading = null;
  function load() {
    if (SYMS) return Promise.resolve(SYMS);
    if (loading) return loading;
    loading = fetch('/bist-symbols.json')
      .then(function (r) { return r.json(); })
      .then(function (d) { SYMS = d; return d; })
      .catch(function () { SYMS = []; return SYMS; });
    return loading;
  }
  var TR = { 'ç': 'c', 'Ç': 'c', 'ğ': 'g', 'Ğ': 'g', 'ı': 'i', 'İ': 'i', 'ö': 'o', 'Ö': 'o', 'ş': 's', 'Ş': 's', 'ü': 'u', 'Ü': 'u', 'â': 'a', 'î': 'i', 'û': 'u' };
  function norm(s) {
    s = (s || '').toString();
    var out = '';
    for (var i = 0; i < s.length; i++) { var ch = s[i]; out += (TR[ch] || ch); }
    return out.toLowerCase();
  }
  function match(list, q) {
    q = norm((q || '').trim());
    if (!q) return [];
    var starts = [], contains = [];
    for (var i = 0; i < list.length; i++) {
      var it = list[i], code = norm(it.c), name = norm(it.n);
      if (code.indexOf(q) === 0 || name.indexOf(q) === 0) starts.push(it);
      else if (code.indexOf(q) >= 0 || name.indexOf(q) >= 0) contains.push(it);
    }
    return starts.concat(contains).slice(0, 8);
  }
  // Kesin doğrulama: girilen metin geçerli bir koda çözülüyor mu?
  function resolve(list, raw) {
    var q = norm((raw || '').trim());
    if (!q) return null;
    for (var i = 0; i < list.length; i++) { if (norm(list[i].c) === q) return list[i]; }
    for (var j = 0; j < list.length; j++) { if (norm(list[j].n) === q) return list[j]; }
    var m = match(list, q);
    return m.length === 1 ? m[0] : null;
  }
  function injectCss() {
    if (document.getElementById('bist-ac-css')) return;
    var s = document.createElement('style'); s.id = 'bist-ac-css';
    s.textContent =
      '.bist-ac{position:absolute;left:0;right:0;top:100%;z-index:50;background:#fff;border:1px solid #d5d9e0;border-radius:10px;margin-top:4px;box-shadow:0 8px 24px rgba(0,0,0,.12);max-height:260px;overflow:auto}' +
      '.bist-ac-item{padding:9px 12px;cursor:pointer;font-size:.92rem;color:#1a2233;border-bottom:1px solid #f0f2f6}' +
      '.bist-ac-item:last-child{border-bottom:0}' +
      '.bist-ac-item b{color:#0b63d6;font-weight:700;margin-right:2px}' +
      '.bist-ac-item.active,.bist-ac-item:hover{background:#eef4ff}';
    document.head.appendChild(s);
  }
  function attach(input) {
    if (!input || input._bistAC) return; input._bistAC = true;
    injectCss(); load();
    var wrap = document.createElement('span');
    wrap.style.position = 'relative'; wrap.style.display = 'block';
    input.parentNode.insertBefore(wrap, input); wrap.appendChild(input);
    var dd = document.createElement('div');
    dd.className = 'bist-ac'; dd.setAttribute('role', 'listbox'); dd.hidden = true;
    wrap.appendChild(dd);
    var items = [], active = -1;
    function close() { dd.hidden = true; dd.innerHTML = ''; items = []; active = -1; }
    function choose(it) {
      input.value = it.c; close();
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
    function paint() { Array.prototype.forEach.call(dd.children, function (c, i) { c.classList.toggle('active', i === active); }); }
    function render() {
      load().then(function (list) {
        items = match(list, input.value);
        if (!items.length) { close(); return; }
        dd.innerHTML = items.map(function (it, i) {
          return '<div class="bist-ac-item" role="option" data-i="' + i + '"><b>' + it.c + '</b> · ' + it.n + '</div>';
        }).join('');
        active = -1; dd.hidden = false;
      });
    }
    input.addEventListener('input', render);
    input.addEventListener('focus', function () { if (input.value.trim()) render(); });
    input.addEventListener('blur', function () { setTimeout(close, 150); });
    input.addEventListener('keydown', function (e) {
      if (dd.hidden) return;
      if (e.key === 'ArrowDown') { e.preventDefault(); active = Math.min(active + 1, items.length - 1); paint(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); active = Math.max(active - 1, 0); paint(); }
      else if (e.key === 'Enter') { if (active >= 0) { e.preventDefault(); choose(items[active]); } }
      else if (e.key === 'Escape') { close(); }
    });
    dd.addEventListener('mousedown', function (e) {
      var el = e.target.closest ? e.target.closest('.bist-ac-item') : null;
      if (el) { e.preventDefault(); choose(items[+el.getAttribute('data-i')]); }
    });
  }
  window.BistAutocomplete = { attach: attach, load: load, match: match, norm: norm, resolve: resolve };
})();
