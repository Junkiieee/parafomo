// Olay önizleme yazılarının otomatik "sonuç kutusu" (TCMB / Fed kararı, TÜİK TÜFE).
//
// Yazının frontmatter'ına `sonuc: "tcmb:2026-10-22"` | `"fed:2026-10-28"` | `"tufe:2026-10"` yazılır.
// Karar/veri açıklanınca ilgili cron veriyi yazıp deploy eder (policy-decisions.sh 11:25/13:25/19:25/21:25 UTC,
// kira-artis-update.sh TÜİK günü) → yazı o build'de kendiliğinden "açıklandı" kutusunu gösterir.
// Ajanın ertesi sabah elle sonuç kutusu eklemesine gerek kalmaz (eskiden ~16 saat gecikiyordu).
// İsteğe bağlı `sonucBaslik`: karar açıklanınca sayfa başlığı olur; yer tutucular aşağıdaki `vars` anahtarları.
import tufe from '../../data/tufe-aylik.json';
import { releaseOf } from './tuik';
import { PERIOD, byMonth, cumKnown, remaining, sskProj, memurProj } from './zam2027';
import kira from '../../data/kira-artis-2026.json';

type TcmbResult = { decision: 'hold' | 'cut' | 'hike'; bp: number; rate: number; prev?: number; lending?: number; borrowing?: number; source: string };
type TcmbMeeting = { decisionDate: string; tsiTime: string; result?: TcmbResult };
type FedResult = { decision: 'hold' | 'cut' | 'hike'; bp: number; lower: number; upper: number; vote?: string; source: string };
type FedMeeting = { decisionDate: string; tsiTime: string; result?: FedResult };

const tcmbFiles = import.meta.glob('../../data/tcmb-*.json', { eager: true, import: 'default' }) as Record<string, { meetings: TcmbMeeting[]; previous?: { rate: number } }>;
const fomcFiles = import.meta.glob('../../data/fomc-*.json', { eager: true, import: 'default' }) as Record<string, { meetings: FedMeeting[]; meetings2027?: FedMeeting[] }>;

const AYLAR = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
const nf = (n: number) => n.toLocaleString('tr-TR', { maximumFractionDigits: 2 });
const nf2 = (n: number) => n.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const gun = (iso: string) => {
  const [y, m, d] = iso.split('-').map(Number);
  return `${d} ${AYLAR[m - 1]} ${y}`;
};
const band = (lo: number, up: number) => `%${nf2(lo)}–${nf2(up)}`;

export type EventResult = {
  tur: 'tcmb' | 'fed' | 'tufe';
  done: boolean;
  date: string;          // karar/açıklama günü (YYYY-MM-DD)
  at: string;            // açıklanma anı, ISO (TSİ +03:00) — dateModified/lastmod bununla, gelecekteyse build anına çekilir
  kicker: string;        // "Karar açıklandı · 22 Ekim 2026, 14:00"
  headline: string;      // ana cümle
  details: string[];
  links: { href: string; label: string; external?: boolean }[];
  vars: Record<string, string>;
};

function tcmb(key: string): EventResult | null {
  const all = Object.values(tcmbFiles).flatMap((f) => f.meetings ?? []).sort((a, b) => a.decisionDate.localeCompare(b.decisionDate));
  const i = all.findIndex((m) => m.decisionDate === key);
  if (i < 0) return null;
  const m = all[i];
  const when = `${gun(m.decisionDate)}, ${m.tsiTime}`;
  const links = [{ href: '/tcmb-faiz-takvimi/', label: 'TCMB faiz takvimi' }, { href: '/mevduat-faizi-hesaplama/', label: 'Mevduat faizi hesaplama' }];
  const r = m.result;
  if (!r) {
    return {
      tur: 'tcmb', done: false, date: m.decisionDate, at: `${m.decisionDate}T${m.tsiTime}:00+03:00`, kicker: `PPK kararı · ${when} TSİ`,
      headline: 'Karar henüz açıklanmadı. Bu kutu, TCMB kararı açıkladığında otomatik güncellenir.',
      details: [], links, vars: {},
    };
  }
  const prevRate = r.prev ?? [...all.slice(0, i)].reverse().find((x) => x.result)?.result?.rate
    ?? Object.values(tcmbFiles).find((f) => f.previous)?.previous?.rate;
  const karar = r.decision === 'hold' ? 'sabit' : r.decision === 'cut' ? 'indirim' : 'artış';
  const headline = r.decision === 'hold'
    ? `TCMB politika faizini %${nf(r.rate)} seviyesinde sabit tuttu.`
    : `TCMB politika faizini ${Math.abs(r.bp)} baz puan ${r.decision === 'cut' ? 'indirdi' : 'artırdı'}: ${prevRate != null ? `%${nf(prevRate)} → ` : ''}%${nf(r.rate)}.`;
  const details = r.lending != null && r.borrowing != null
    ? [`Gecelik borç verme faizi %${nf(r.lending)}, gecelik borçlanma faizi %${nf(r.borrowing)}.`] : [];
  return {
    tur: 'tcmb', done: true, date: m.decisionDate, at: `${m.decisionDate}T${m.tsiTime}:00+03:00`, kicker: `Karar açıklandı · ${when}`, headline, details,
    links: [{ href: r.source, label: 'TCMB karar metni', external: true }, ...links],
    vars: { oran: nf(r.rate), onceki: prevRate != null ? nf(prevRate) : '', bp: String(Math.abs(r.bp)), karar },
  };
}

function fed(key: string): EventResult | null {
  const all = Object.values(fomcFiles).flatMap((f) => [...(f.meetings ?? []), ...(f.meetings2027 ?? [])]);
  const m = all.find((x) => x.decisionDate === key);
  if (!m) return null;
  const when = `${gun(m.decisionDate)}, ${m.tsiTime} TSİ`;
  const links = [{ href: '/fed-faiz-takvimi/', label: 'Fed faiz takvimi' }];
  const r = m.result;
  if (!r) {
    return {
      tur: 'fed', done: false, date: m.decisionDate, at: `${m.decisionDate}T${m.tsiTime}:00+03:00`, kicker: `FOMC kararı · ${when}`,
      headline: 'Karar henüz açıklanmadı. Bu kutu, Fed kararı açıkladığında otomatik güncellenir.',
      details: [], links, vars: {},
    };
  }
  const d = r.bp / 100;
  const karar = r.decision === 'hold' ? 'sabit' : r.decision === 'cut' ? 'indirim' : 'artış';
  const headline = r.decision === 'hold'
    ? `Fed politika faizini ${band(r.lower, r.upper)} bandında sabit tuttu.`
    : `Fed politika faizini ${Math.abs(r.bp)} baz puan ${r.decision === 'cut' ? 'indirdi' : 'artırdı'}: ${band(r.lower - d, r.upper - d)} → ${band(r.lower, r.upper)}.`;
  return {
    tur: 'fed', done: true, date: m.decisionDate, at: `${m.decisionDate}T${m.tsiTime}:00+03:00`, kicker: `Karar açıklandı · ${when}`, headline,
    details: r.vote ? [`Oylama: ${r.vote}.`] : [],
    links: [{ href: r.source, label: 'Fed açıklaması', external: true }, ...links],
    vars: { bant: band(r.lower, r.upper), bp: String(Math.abs(r.bp)), karar },
  };
}

function tufeEv(key: string): EventResult | null {
  if (!/^\d{4}-\d{2}$/.test(key)) return null;
  const y = +key.slice(0, 4), mo = +key.slice(5);
  const ay = `${AYLAR[mo - 1]} ${y}`;
  const sonrakiAy = mo === 12 ? `Ocak ${y + 1}` : `${AYLAR[mo]} ${y}`;
  // Takvimde yoksa: TÜİK'in olağan günü (izleyen ayın 3'ü, hafta sonuysa ilk iş günü) — src/data/tuik.ts; o zaman
  // "(tahmini)" yazılır. Eskiden düz "ayın 3'ü"ydü: Aralık 2026 verisi Pazar 3 Ocak 2027 görünüyordu.
  const { date: rel, tahmini } = releaseOf(key);
  const links = [
    { href: '/enflasyon-takvimi/', label: 'Enflasyon takvimi' },
    { href: '/kira-artis-orani-hesaplama/', label: 'Kira artış oranı' },
    { href: '/emekli-zammi-hesaplama/', label: 'Emekli zammı hesaplama' },
  ];
  const row = (tufe.months as { ay: string; yillik: number; aylik: number }[]).find((x) => x.ay === key);
  if (!row) {
    return {
      tur: 'tufe', done: false, date: rel, at: `${rel}T10:00:00+03:00`, kicker: `TÜİK · ${gun(rel)}, 10:00${tahmini ? ' (tahmini)' : ''}`,
      headline: `${ay} enflasyonu henüz açıklanmadı. Bu kutu, TÜİK veriyi açıkladığı gün otomatik güncellenir.`,
      details: [], links, vars: {},
    };
  }
  const details = (kira as { guncelAy: string; guncelOran: number }).guncelAy === sonrakiAy
    ? [`${sonrakiAy} kira artış tavanı (12 aylık TÜFE ortalaması): %${nf2((kira as { guncelOran: number }).guncelOran)}.`] : [];
  const vars: Record<string, string> = { ay, aylik: nf2(row.aylik), yillik: nf2(row.yillik) };
  // Zam dönemi ayıysa (src/data/zam2027.ts PERIOD) emekli/memur zammı satırı — araç sayfalarıyla AYNI modül ve rakam.
  // Neden (denetim 2026-11-18): Ekim yazısının gövdesi "memur zammı ~%8,1" derken araçlar %10,75 gösteriyordu; kutu
  // yalnız TÜFE + kira tavanını yazıyordu. Birikim yazının ayına kadar; tahmin build günündeki güncel tahmin.
  const idx = PERIOD.indexOf(key);
  if (idx >= 0 && PERIOD.slice(0, idx + 1).every((k) => byMonth.has(k))) {
    const pct = (x: number) => `%${nf2(x * 100)}`;
    const ilk = PERIOD[0];
    const son = PERIOD[PERIOD.length - 1];
    const ad = (k: string) => AYLAR[+k.slice(5) - 1];
    const hedefAy = +son.slice(5) === 12 ? `Ocak ${+son.slice(0, 4) + 1}` : `${AYLAR[+son.slice(5)]} ${son.slice(0, 4)}`;
    const cumKey = PERIOD.slice(0, idx + 1).reduce((c, k) => c * (1 + byMonth.get(k)!.aylik / 100), 1) - 1;
    const aralik = idx === 0 ? ay : `${ad(ilk)}–${ay}`;
    const ssk = remaining === 0 ? cumKnown : sskProj;
    details.push(remaining === 0
      ? `${hedefAy} zammı kesinleşti: SSK ve Bağ-Kur emeklisine ${pct(cumKnown)} (${ad(ilk)}–${ad(son)} ${son.slice(0, 4)} enflasyonu), memur ve memur emeklisine ${pct(memurProj.zam)}.`
      : `${aralik} birikimli enflasyon ${pct(cumKey)} (${hedefAy} emekli zammının kesinleşen kısmı). Güncel tahmin: SSK ve Bağ-Kur ${pct(ssk)}, memur ${pct(memurProj.zam)}.`);
    links.splice(3, 0, { href: '/memur-zammi-hesaplama/', label: 'Memur zammı' });
    Object.assign(vars, { birikim: nf2(cumKey * 100), ssk: nf2(ssk * 100), memur: nf2(memurProj.zam * 100) });
  }
  return {
    tur: 'tufe', done: true, date: rel, at: `${rel}T10:00:00+03:00`, kicker: `Veri açıklandı · ${gun(rel)}, 10:00`,
    headline: `${ay} enflasyonu: aylık %${nf2(row.aylik)}, yıllık %${nf2(row.yillik)}.`,
    details,
    links: [{ href: 'https://data.tuik.gov.tr/Kategori/GetKategori?p=enflasyon-ve-fiyat-106', label: 'TÜİK', external: true }, ...links],
    vars,
  };
}

export function eventResult(sonuc?: string): EventResult | null {
  if (!sonuc) return null;
  const [tur, key] = sonuc.split(':');
  if (tur === 'tcmb') return tcmb(key);
  if (tur === 'fed') return fed(key);
  if (tur === 'tufe') return tufeEv(key);
  return null;
}

// "TCMB Ekim 2026 Faiz Kararı Açıklandı: Politika Faizi %{oran}" → yer tutucular doldurulur;
// doldurulamayan yer tutucu kalırsa null (yarım başlık yayınlanmaz).
export function fillTitle(tpl: string | undefined, vars: Record<string, string>): string | null {
  if (!tpl) return null;
  const out = tpl.replace(/\{(\w+)\}/g, (all, k) => (vars[k] ? vars[k] : all));
  return /\{\w+\}/.test(out) ? null : out;
}

/** Olay sonucunun yazıya girdiği an: açıklanma saati; build daha erkense build anı (gelecek tarih yazılmaz).
 *  Eski `date + 'T12:00:00Z'` sabiti TÜFE günü (10:00 TSİ) sabah build'inde dateModified'ı ~5 saat ileri yazıyordu. */
export function eventModified(ev: EventResult): Date {
  return new Date(Math.min(Date.parse(ev.at), Date.now()));
}
