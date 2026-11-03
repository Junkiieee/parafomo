// Yıla gelen Türkçe ekler: "2026'da" ama "2027'de", "2023'te"; "2026'ya" ama "2027'ye".
// Ek, yılın OKUNUŞUNUN son hecesine uyar (2026 = …altı → -da; 2027 = …yedi → -de; 2030 = …otuz → -da).
// Neden (yıl geçişi denetimi 2026-11-03): kodla yazılan yıllara sabit "'da"/"'ya" ekleniyordu; 2027'de yanlış olur.

// Son okunan kelimenin ünlüsü kalın mı (a, ı, o, u) ve sert ünsüzle mi bitiyor (ç, f, h, k, p, s, ş, t)?
const BIRLER: Record<number, [kalin: boolean, sert: boolean]> = {
  1: [false, false], // bir
  2: [false, false], // iki
  3: [false, true], // üç
  4: [false, true], // dört
  5: [false, true], // beş
  6: [true, false], // altı
  7: [false, false], // yedi
  8: [false, false], // sekiz
  9: [true, false], // dokuz
};
const ONLAR: Record<number, [boolean, boolean]> = {
  1: [true, false], // on
  2: [false, false], // yirmi
  3: [true, false], // otuz
  4: [true, true], // kırk
  5: [false, false], // elli
  6: [true, true], // altmış
  7: [false, true], // yetmiş
  8: [false, false], // seksen
  9: [true, false], // doksan
};

function sesUyumu(yil: number): [boolean, boolean] {
  const birler = yil % 10;
  if (birler) return BIRLER[birler];
  const onlar = Math.floor(yil / 10) % 10;
  if (onlar) return ONLAR[onlar];
  return Math.floor(yil / 100) % 10 ? [false, false] /* yüz */ : [false, false] /* bin */;
}

/** Bulunma eki: 2026 → "'da", 2027 → "'de", 2023 → "'te", 2030 → "'da". */
export function yilDa(yil: number | string): string {
  const [kalin, sert] = sesUyumu(+yil);
  return `'${sert ? 't' : 'd'}${kalin ? 'a' : 'e'}`;
}

/** Yönelme eki: 2026 → "'ya", 2027 → "'ye", 2023 → "'e" (ünsüzle bitince ünlü). */
export function yilYa(yil: number | string): string {
  const y = +yil;
  const [kalin] = sesUyumu(y);
  // Ünlüyle biten okunuşlar (iki, altı, yedi, yirmi, elli) → kaynaştırma "y"
  const birler = y % 10;
  const onlar = Math.floor(y / 10) % 10;
  const unluyleBiter = birler ? [2, 6, 7].includes(birler) : [2, 5].includes(onlar);
  return `'${unluyleBiter ? 'y' : ''}${kalin ? 'a' : 'e'}`;
}
