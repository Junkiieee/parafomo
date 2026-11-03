// TÜİK TÜFE açıklama takvimi — bütün data/tuik-enflasyon-YYYY.json dosyaları tek listede.
// Neden (yıl geçişi denetimi 2026-11-03): 3 sayfa yalnız tuik-enflasyon-2026.json'u içe aktarıyordu; 2026 dosyası
// Kasım verisiyle (3 Aralık) bitiyor → 4 Aralık'tan Ocak'a "enflasyon ne zaman açıklanacak" cevapsız kalıyordu.
// 2027 dosyası eklenince sayfalar kendiliğinden okur. Takvimde olmayan ay için tek yedek kural: aşağıda.
type Release = { covers: string; date: string };
type TuikFile = { releaseTime?: string; releases?: Release[] };

const files = import.meta.glob('../../data/tuik-enflasyon-*.json', { eager: true, import: 'default' }) as Record<string, TuikFile>;

export const AYLAR = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
export const RELEASE_TIME = Object.values(files).find((f) => f.releaseTime)?.releaseTime ?? '10:00';

const seen = new Set<string>();
/** Bütün yılların açıklamaları, tarihe göre sıralı (aynı ay iki dosyada varsa ilki). */
export const RELEASES: Release[] = Object.values(files)
  .flatMap((f) => f.releases ?? [])
  .sort((a, b) => a.date.localeCompare(b.date))
  .filter((r) => (seen.has(r.covers) ? false : (seen.add(r.covers), true)));

const pad = (n: number) => String(n).padStart(2, '0');

/** TÜİK'in olağan kuralı: izleyen ayın 3'ü; hafta sonuna denk gelirse sonraki ilk iş günü
 *  (ör. Aralık 2025 verisi: 3 Ocak 2026 Cumartesi → 5 Ocak). Resmî tatiller bilinmez — kesin gün takvimden gelir. */
export function usualReleaseDate(key: string): string {
  const y = +key.slice(0, 4);
  const m = +key.slice(5, 7);
  const d = new Date(Date.UTC(m === 12 ? y + 1 : y, m === 12 ? 0 : m, 3));
  while (d.getUTCDay() === 0 || d.getUTCDay() === 6) d.setUTCDate(d.getUTCDate() + 1);
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`;
}

/** 'YYYY-MM' verisinin açıklama günü: takvimde varsa o, yoksa olağan kural (tahmini: true). */
export function releaseOf(key: string): { date: string; tahmini: boolean } {
  const covers = `${AYLAR[+key.slice(5, 7) - 1]} ${key.slice(0, 4)}`;
  const r = RELEASES.find((x) => x.covers === covers);
  return r ? { date: r.date, tahmini: false } : { date: usualReleaseDate(key), tahmini: true };
}

/** "Kasım 2026" → "2026-11" */
export const coversKey = (covers: string) => {
  const [ad, yil] = covers.split(' ');
  return `${yil}-${pad(AYLAR.indexOf(ad) + 1)}`;
};
