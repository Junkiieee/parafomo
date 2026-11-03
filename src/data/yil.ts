// Yıla gelen Türkçe ekler: "2026'da" ama "2027'de", "2023'te"; "2026'ya" ama "2027'ye".
// Uygulama ek.ts'te (yüzde, kur ve ayın günü de aynı kuralla). Neden (yıl geçişi denetimi 2026-11-03): kodla
// yazılan yıllara sabit "'da"/"'ya" ekleniyordu; 2027'de yanlış olur.
export { ekDa as yilDa, ekYa as yilYa } from './ek';
