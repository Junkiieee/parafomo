// Zam sezonu e-posta yerleşimi (denetim 2026-11-19, gelir-huni-5).
// Haftalık bültenin hiç gerçek abonesi yok; zam sayfalarında, anasayfada ve zam konulu yazılarda bülten kutusu
// zam alarmıyla yarışıyordu. Sezon boyunca bu yerlerde tek e-posta sorusu zam alarmı; bülten diğer sayfalarda kalır.
// Sezon build anına göre kendiliğinden biter (site her gün yeniden build edilir): 16 Ocak 2027'den itibaren eski
// yerleşim (bülten kutusu) geri gelir — elle geri alma gerekmez. Yeni sezon için yalnız BITIS tarihini ilerlet.
export const ZAM_SEZONU_BITIS = new Date('2027-01-16T00:00:00+03:00');
export const ZAM_SEZONU = Date.now() < ZAM_SEZONU_BITIS.getTime();

const lower = (s: string) => s.replace(/I/g, 'ı').replace(/İ/g, 'i').toLowerCase();

/** Yazı zam alarmının konusuyla (asgari ücret, emekli ve memur zammı/maaşı) ilgili mi? Slug ya da etiketlerde bir kelime
 *  zam (zaman hariç), maaş, emekli (emeklilik/BES hariç), memur ile başlıyorsa ya da "asgari ücret" geçiyorsa
 *  ("asgari ödeme" değil). Bu yazıların sonunda sezon boyunca bülten yerine zam alarmı gösterilir. */
export function zamKonulu(slug: string, tags: string[] = []): boolean {
  const metin = ' ' + [slug.replace(/-/g, ' '), ...tags.map(lower)].join(' | ') + ' ';
  return /[\s|](zam(?!an)|maa[sş]|emekli(?!lik)|memur|asgari [üu]cret)/.test(metin);
}
