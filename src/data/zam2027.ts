// Ocak 2027 memur / SSK zammı tahmini — /emekli-zammi-hesaplama ve /kidem-tazminati-hesaplama ortak kaynağı.
// Ocak 2027 zammı = Temmuz–Aralık 2026 birikimli TÜFE (SSK/Bağ-Kur) ve toplu sözleşme + enflasyon
// farkı (memur / memur emeklisi). Aylık TÜFE scripts/tufe-update.py ile TCMB tablosundan gelir.
// Yöntem 2026-10-10'da Temmuz 2026 resmi oranlarıyla doğrulandı (SSK %17,75 · memur %13,51).
import tufe from '../../data/tufe-aylik.json';

export const PERIOD = ['2026-07', '2026-08', '2026-09', '2026-10', '2026-11', '2026-12'];
export const TS_H2_2026 = 7; // 8. Dönem Toplu Sözleşme (Hakem Kurulu, RG 27.08.2025): 2026 2. yarı %7
export const TS_H1_2027 = 5; // 2027 1. yarı %5

type M = { ay: string; yillik: number; aylik: number };
export const byMonth = new Map((tufe.months as M[]).map((m) => [m.ay, m]));

export const knownKeys = PERIOD.filter((k) => byMonth.has(k));
export const cumKnown = knownKeys.reduce((c, k) => c * (1 + byMonth.get(k)!.aylik / 100), 1) - 1; // ör. 0.0556
export const remaining = PERIOD.length - knownKeys.length;
const last3 = (tufe.months as M[]).slice(0, 3);
export const ASSUME = +(last3.reduce((s, m) => s + m.aylik, 0) / last3.length).toFixed(2); // kalan aylar varsayımı (%)

export const project = (assume: number) => (1 + cumKnown) * Math.pow(1 + assume / 100, remaining) - 1;
export const memurFrom = (cum6: number) => {
  const fark = Math.max(0, (1 + cum6) / (1 + TS_H2_2026 / 100) - 1);
  return { fark, zam: (1 + fark) * (1 + TS_H1_2027 / 100) - 1 };
};
export const sskProj = project(ASSUME);
export const memurProj = memurFrom(sskProj);
