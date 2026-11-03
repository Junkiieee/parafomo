// Yıla gelen Türkçe ekler: "2026'da" ama "2027'de", "2023'te"; "2026'ya" ama "2027'ye".
// Uygulama ek.ts'te (yüzde, kur ve ayın günü de aynı kuralla). Neden (yıl geçişi denetimi 2026-11-03): kodla
// yazılan yıllara sabit "'da"/"'ya" ekleniyordu; 2027'de yanlış olur.
export { ekDa as yilDa, ekYa as yilYa } from './ek';

// Build gününün yılı (İstanbul saatiyle; 1 Ocak 00:00-03:00 arası UTC hâlâ eski yıldadır).
// YALNIZ yıla bağlı tutarı olmayan sayfaların başlığında (faiz, kredi, bono, enflasyon, ekonomik takvim):
// 1 Ocak'taki ilk build'de kendiliğinden yeni yıla geçer. Vergi dilimi, asgari ücret, harç gibi yıllık
// tutar gösteren sayfalarda KULLANMA — onların yılı verinin yılıdır (veri güncellenmeden başlık değişmesin).
export const BU_YIL = Number(
  new Intl.DateTimeFormat('en-US', { year: 'numeric', timeZone: 'Europe/Istanbul' }).format(new Date()),
);
