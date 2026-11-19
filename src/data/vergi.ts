// Gelir vergisi tarifesi + asgari ücret brütü — yıla bağlı vergi parametrelerinin ORTAK kaynağı.
// Neden (denetim 2026-11-18, veri-3/veri-5): 2026 dilimleri (190.000/400.000/1.500.000…) 4 sayfada ve onların
// tarayıcı betiklerinde ayrı ayrı elle yazılıydı; asgari ücret brütü (33.030) 5 sayfada sabitti. Ocak'ta biri
// unutulursa "2027 vergi dilimleri / net maaş 2027" aramalarının tepe yaptığı hafta sayfalar birbirini tutmazdı.
// Artık: data/gelir-vergisi-tarife.json (yeni yıl tebliği) + data/asgari-ucret.json (asgari-ucret-watch.py).
import tarife from '../../data/gelir-vergisi-tarife.json';
import au from '../../data/asgari-ucret.json';

/** JSON'daki biçim: [üst sınır ₺ | null (son dilim), oran %] — tarayıcıya define:vars ile bu biçimde verilir. */
export type DilimJson = [number | null, number];
/** Hesaplamada kullanılan biçim: [üst sınır ₺ | Infinity, oran 0-1]. */
export type Dilim = [number, number];

const hesapBicimi = (d: DilimJson[]): Dilim[] => d.map(([ust, oran]) => [ust ?? Infinity, oran / 100]);

export const TARIFE_YIL: number = tarife.yil;
export const UCRET_JSON = tarife.ucret as DilimJson[];
export const DIGER_JSON = tarife.diger as DilimJson[];
export const UCRET_DILIM: Dilim[] = hesapBicimi(UCRET_JSON);
export const DIGER_DILIM: Dilim[] = hesapBicimi(DIGER_JSON);

const tl0 = (n: number) => new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 0 }).format(Math.round(n));

/** Tablo satırları: "190.000 ₺'ye kadar", "190.001 – 400.000 ₺", "5.300.000 ₺ üzeri" + oran (%). */
export function dilimSatirlari(d: DilimJson[], kesme = "'"): { aralik: string; oran: number; ust: number | null }[] {
  let onceki = 0;
  return d.map(([ust, oran], i) => {
    const aralik = ust == null
      ? `${tl0(onceki)} ₺ üzeri`
      : i === 0 ? `${tl0(ust)} ₺${kesme}ye kadar` : `${tl0(onceki + 1)} – ${tl0(ust)} ₺`;
    onceki = ust ?? onceki;
    return { aralik, oran, ust };
  });
}

/** Asgari ücretin AYLIK BRÜTÜ, istenen yıl için: yürürlükteki (guncel), açıklanan gelecek yıl (yeni) ya da geçmiş.
 *  Geçmiş kayıtlarda yalnız net var: 2022'den beri asgari ücret gelir+damga vergisinden istisna → net = brüt × 0,85.
 *  Yıl bilinmiyorsa build uyarır ve yürürlükteki tutarı verir (sayfa çökmesin; yanlış yıl etiketi uyarıdan görünür). */
export function asgariBrut(yil: number): number {
  const g = au.guncel as { yil: number; brut: number };
  if (g.yil === yil) return g.brut;
  const y = (au as { yeni?: { yil: number; brut?: number; net?: number } | null }).yeni;
  if (y && y.yil === yil && (y.brut ?? y.net)) return y.brut ?? Math.round(((y.net as number) / 0.85) * 100) / 100;
  const h = (au.gecmis as { yil: number; net: number }[]).find((x) => x.yil === yil);
  if (h) return Math.round((h.net / 0.85) * 100) / 100;
  console.warn(`[vergi.ts] ${yil} asgari ücreti data/asgari-ucret.json'da yok — yürürlükteki ${g.yil} tutarı kullanıldı`);
  return g.brut;
}

/** Yürürlükteki asgari ücret yılı ve brütü (asgari-ucret-watch.py 1 Ocak'ta yeni yıla taşır). */
export const ASGARI_YIL: number = (au.guncel as { yil: number }).yil;
export const ASGARI_BRUT: number = (au.guncel as { brut: number }).brut;

/** Metinleri belli bir tarife yılı için elle yazılmış sayfalar: tarife yılı değişince build uyarısı. */
export function metinYiliKontrol(sayfa: string, metinYili: number) {
  if (metinYili !== TARIFE_YIL) {
    console.warn(`[${sayfa}] metinler ${metinYili} tarifesi için yazıldı, data/gelir-vergisi-tarife.json yılı ${TARIFE_YIL}: ` +
      `sayfadaki yıl/dilim metinlerini güncelleyip METIN_YILI'nı ${TARIFE_YIL} yap.`);
  }
}
