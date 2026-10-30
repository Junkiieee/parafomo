// =====================================================================
//  generic.js — veriyle sürülen Short: TL.data.scenes = [{ line, type, head, data }] (sahne başına bir satır).
//  Sahne, satırı konuşulmaya başlamadan 0,15 sn önce gelir; önceki sahne 0,3 sn'de söner.
//  İlk sahne 0. karede yerleşmiş hâlde başlar (kapak/akış karesi asla boş olmaz).
// =====================================================================
const GD = TL.data, GS = GD.scenes;
const FIRST_OFF = 1.6, XF = 0.3;
const sStart = (i) => (i === 0 ? -FIRST_OFF : cue(GS[i].line) - 0.15);
function drawScene(i, al) {
  const sc = GS[i], f = SC[sc.type] || SC.icon_text, t = TT - sStart(i);
  if (sc.type !== 'cta') brandHeader((sc.head || '').toLocaleUpperCase('tr-TR'), sStart(i) + (i === 0 ? 0 : 0.05), { eyebrow: GD.eyebrow, al });
  f(sc.data || {}, t, al);
}
const curScene = () => { let i = 0; for (let k = 0; k < GS.length; k++) if (TT >= sStart(k)) i = k; return i; };
function drawPiece() {   // zemin SKIN.bg'de; burada yalnız sahne katmanı
  const i = curScene();
  const z = 1 + 0.02 * clamp((TT - Math.max(0, sStart(i))) / 4);   // sahne içinde yavaş itme
  ctx.save(); ctx.translate(470, 900); ctx.scale(z, z); ctx.translate(-470, -900);
  const fx = i > 0 ? clamp((TT - sStart(i)) / XF) : 1;
  if (fx < 1) drawScene(i - 1, 1 - fx);
  drawScene(i, fx);
  ctx.restore();
}
function drawOverlay() { if (GS[curScene()].type !== 'cta') captions(); }   // altyazı her kaplamada net, en üstte
