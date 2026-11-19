// Sayılara gelen Türkçe ekler (yıl, yüzde, kur, ayın günü). Ek, sayının OKUNUŞUNUN son kelimesine uyar:
//   2026'da · 2027'de · 2023'te   |   Ayın 17'si · 18'i · 19'u   |   %23'ü · %40'ı   |   3,11'den · 49,98'e
// Neden (denetim 2026-11-03): ekler elle yazılmıştı → "Ayın 17'i", "%23'i kârda", "49,98'ye"; yıl dönünce de
// "Ocak 2027'dan", "2027'da" çıkacaktı. Girdi: sayı (2027, 49.98) ya da Türkçe biçimli metin ("49,98",
// "1.234,5", "%23", "Ocak 2027"); metinde SON sayı esas alınır. Kesir ("8/35") okunuşu farklıdır: payı ver.

const BIRLER = ['', 'bir', 'iki', 'üç', 'dört', 'beş', 'altı', 'yedi', 'sekiz', 'dokuz'];
const ONLAR = ['', 'on', 'yirmi', 'otuz', 'kırk', 'elli', 'altmış', 'yetmiş', 'seksen', 'doksan'];
const UNLU = 'aıoueiöü';

function tamSonKelime(n: number): string {
  if (n === 0) return 'sıfır';
  if (n % 10) return BIRLER[n % 10];
  if (n % 100) return ONLAR[(n % 100) / 10];
  if (n % 1000) return 'yüz';
  if (n % 1e6) return 'bin';
  if (n % 1e9) return 'milyon';
  return 'milyar';
}

/** Okunuştaki son kelime: 2027 → "yedi"; "49,98" → "sekiz" (kırk dokuz virgül doksan sekiz); 1500 → "yüz". */
export function sonKelime(sayi: number | string): string {
  let tam: string;
  let ondalik = '';
  if (typeof sayi === 'number') {
    [tam, ondalik = ''] = String(Math.abs(Number(sayi.toFixed(10)))).split('.');
  } else {
    const m = sayi.match(/\d[\d.]*(?:,\d+)?(?!.*\d)/s);
    if (!m) return '';
    [tam, ondalik = ''] = m[0].split(',');
    tam = tam.replace(/\./g, '');
  }
  return tamSonKelime(parseInt(/[1-9]/.test(ondalik) ? ondalik : tam, 10) || 0);
}

function uyum(sayi: number | string) {
  const k = sonKelime(sayi) || 'bir';
  const son = [...k].filter((c) => UNLU.includes(c)).pop() ?? 'i';
  return {
    kalin: 'aıou'.includes(son),
    dar: 'aı'.includes(son) ? 'ı' : 'ei'.includes(son) ? 'i' : 'ou'.includes(son) ? 'u' : 'ü',
    unluyle: UNLU.includes(k[k.length - 1]),
    sert: 'çfhkpsşt'.includes(k[k.length - 1]),
  };
}

/** Bulunma: 2026'da, 2027'de, 2023'te, %39,5'te */
export function ekDa(sayi: number | string): string {
  const u = uyum(sayi);
  return `'${u.sert ? 't' : 'd'}${u.kalin ? 'a' : 'e'}`;
}

/** Ayrılma: Ocak 2026'dan, Ocak 2027'den, 3,11'den, 2023'ten */
export function ekDan(sayi: number | string): string {
  return ekDa(sayi) + 'n';
}

/** Yönelme: 2026'ya, 2027'ye, 49,98'e, 2023'e */
export function ekYa(sayi: number | string): string {
  const u = uyum(sayi);
  return `'${u.unluyle ? 'y' : ''}${u.kalin ? 'a' : 'e'}`;
}

/** İyelik (3. tekil): Ayın 17'si, 18'i, 19'u; şirketlerin %23'ü, %40'ı */
export function ekI(sayi: number | string): string {
  const u = uyum(sayi);
  return `'${u.unluyle ? 's' : ''}${u.dar}`;
}

/** Tamlayan: %34,88'in, %50'nin, %40'ın */
export function ekIn(sayi: number | string): string {
  const u = uyum(sayi);
  return `'${u.unluyle ? 'n' : ''}${u.dar}n`;
}
