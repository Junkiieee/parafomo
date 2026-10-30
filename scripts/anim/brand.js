// =====================================================================
//  brand.js — ParaFOMO marka katmanı: her stilin üstüne aynı kimlik (koyu zemin, marka yeşili, altın rakam,
//  Anton/Oswald, sarı-vurgulu altyazı, ABONE OL). Stil kitinin PAL'ını marka koyusuna çeker.
//  Beklenen: TL (zaman çizelgesi: satırlar t0/t1/cap), W, H, ctx, TT.
// =====================================================================
const BR = {
  bg: '#0F1316', face: '#141B1F', edge: '#6E7E84', inner: '#2A363C',
  brand: '#2BB194', light: '#63D491', gold: '#FFC94D', red: '#E3120B', white: '#F4F6F5', muted: '#9AA5A1',
};
if (typeof PAL !== 'undefined') Object.assign(PAL, { paper: BR.bg, face: BR.face, edge: BR.edge, inner: BR.inner, accent: BR.brand, text: '#D5DDDA', textD: '#7A8A86' });
const ANTON = 'Anton, "DejaVu Sans", sans-serif';
const OSW = 'Oswald, "DejaVu Sans", sans-serif';
const DMONO = '"DejaVu Sans Mono", monospace';

// satır zamanları: L('sgk') → { t0, t1 }; cue('sgk') = başlangıç
const L = (id) => TL.lines.find((l) => l.id === id) || { t0: 1e9, t1: 1e9 };
const cue = (id) => L(id).t0;
const curLine = () => { let c = null; for (const l of TL.lines) if (TT >= l.t0 - 0.05) c = l; return c; };
const trn = (x, dec = 0) => x.toLocaleString('tr-TR', { minimumFractionDigits: dec, maximumFractionDigits: dec });
const tl = (x) => '₺' + trn(Math.round(x));

function txt(str, x, y, font, color, o = {}) {
  ctx.save(); ctx.font = font; ctx.fillStyle = color; ctx.textAlign = o.align ?? 'left'; ctx.textBaseline = o.base ?? 'alphabetic';
  ctx.globalAlpha = o.al ?? 1;
  if (o.ls) ctx.letterSpacing = o.ls + 'px';
  ctx.fillText(str, x, y); const w = ctx.measureText(str).width; ctx.restore(); return w;
}

// üst bant: küçük marka etiketi + büyük başlık (yay ile gelir)
function brandHeader(title, t0, o = {}) {
  const a = clamp(spring(TT, t0, { k: 140, damp: 0.8 })) * (o.al ?? 1);
  if (a <= 0.001) return;
  txt(o.eyebrow || 'PARAFOMO · 2026 RAKAMLARIYLA', 70, 268, `500 26px ${DMONO}`, BR.brand, { al: a, ls: 2 });
  txt(title, 70, 352 + (1 - a) * 24, typeof fitFont === 'function' ? fitFont(title, 880, 76, ANTON) : `76px ${ANTON}`, BR.white, { al: a });
  if (o.sub) txt(o.sub, 72, 402, `400 34px ${OSW}`, BR.muted, { al: a });
}

// altyazı: satırın metni 3'er kelimelik parçalar, konuşulan kelime altın (sarı vurgu) — karakter oranlı zamanlama
function captions(y = 1488) {
  const l = curLine(); if (!l || TT > l.t1 + 0.25) return;
  const words = l.cap.split(/\s+/), lens = words.map((w) => w.length + 1), tot = lens.reduce((a, b) => a + b, 0);
  const u = clamp((TT - l.t0) / Math.max(0.1, l.t1 - l.t0)) * tot;
  let acc = 0, wi = 0; for (let i = 0; i < words.length; i++) { if (u >= acc) wi = i; acc += lens[i]; }
  if (l.words && l.words.length === words.length) { wi = 0; for (let i = 0; i < words.length; i++) if (TT >= l.words[i] - 0.04) wi = i; }   // gerçek kelime zamanı
  const g0 = Math.floor(wi / 3) * 3, grp = words.slice(g0, g0 + 3);
  ctx.save(); ctx.font = BR.capFont || `600 64px ${OSW}`; ctx.textBaseline = 'alphabetic';
  const sp = 18, ws = grp.map((w) => ctx.measureText(w.toLocaleUpperCase('tr-TR')).width);
  const tw = ws.reduce((a, b) => a + b, 0) + sp * (grp.length - 1), k = Math.min(1, 860 / tw);
  ctx.translate(470, y); ctx.scale(k, k); ctx.translate(-470, -y);   // geniş parça güvenli alana sığsın
  let x = 470 - tw / 2;
  grp.forEach((w, i) => {
    const up = w.toLocaleUpperCase('tr-TR'), on = g0 + i === wi;
    if (on) { ctx.fillStyle = BR.capHi || '#FFC94D'; ctx.beginPath(); ctx.roundRect(x - 10, y - 62, ws[i] + 20, 80, 10); ctx.fill(); }
    ctx.lineWidth = 8; ctx.strokeStyle = BR.capStroke || 'rgba(0,0,0,0.55)'; ctx.lineJoin = 'round';
    if (!on) ctx.strokeText(up, x, y);
    ctx.fillStyle = on ? '#111' : (BR.capText || BR.white); ctx.fillText(up, x, y);
    x += ws[i] + sp;
  });
  ctx.restore();
}

// kapanış: site + ABONE OL (kırmızı, üçgenli). o: { l1, l2, sub, al, t (yerel zaman; yoksa TT - t0) }
function ctaCard(t0, o = {}) {
  const lt = o.t ?? (TT - t0), A = o.al ?? 1;
  const a = clamp(lt <= 0 ? 0 : spring(lt, 0, { k: 120, damp: 0.75 })) * A;
  if (a <= 0.001) return;
  ctx.save(); ctx.globalAlpha = a * 0.82; ctx.fillStyle = BR.bg; ctx.fillRect(0, 0, W, H); ctx.restore();
  const y = 760 + (1 - a) * 40, l1 = (o.l1 || 'KENDİ MAAŞININ').toLocaleUpperCase('tr-TR'), l2 = (o.l2 || 'ANATOMİSİNİ GÖR').toLocaleUpperCase('tr-TR');
  txt(l1, 470, y, fitFont(l1, 860, 64, ANTON), BR.white, { align: 'center', al: a });
  txt(l2, 470, y + 84, fitFont(l2, 860, 64, ANTON), BR.white, { align: 'center', al: a });
  txt('parafomo.com', 470, y + 200, `86px ${ANTON}`, BR.gold, { align: 'center', al: a });
  txt((o.sub || 'NET MAAŞ HESAPLAMA · ÜCRETSİZ').toLocaleUpperCase('tr-TR'), 470, y + 256, fitFont((o.sub || 'NET MAAŞ HESAPLAMA · ÜCRETSİZ').toLocaleUpperCase('tr-TR'), 860, 28, DMONO, 500), BR.muted, { align: 'center', al: a, ls: 1 });
  const b = clamp(lt <= 0.6 ? 0 : spring(lt, 0.6, { k: 200, damp: 0.45 }));
  if (b > 0.001) {
    ctx.save(); ctx.globalAlpha = A; ctx.translate(470, y + 400); ctx.scale(b, b);
    ctx.fillStyle = BR.red; ctx.beginPath(); ctx.roundRect(-210, -58, 420, 116, 20); ctx.fill();
    ctx.fillStyle = BR.white; ctx.beginPath(); ctx.moveTo(-150, -24); ctx.lineTo(-150, 24); ctx.lineTo(-110, 0); ctx.closePath(); ctx.fill();
    ctx.font = `56px ${ANTON}`; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText('ABONE OL', -86, 4);
    ctx.restore();
  }
}
