// Veri sayfalarının "son güncellenme" zamanı — beslendikleri veri dosyasından (TEK kaynak).
// Kullananlar: astro.config.mjs (sitemap lastmod) ve BaseLayout (WebPage JSON-LD dateModified, 2026-11-09:
// GEO denetimi araç sayfalarında tarih sinyali bulamadı; rakam her ay değişse de arama motorları görmüyordu).
// Neden: lastmod yalnız veri gerçekten değişince ilerler (doğru sinyal). Build repo kökünden çalışır.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

export const dataDir = join(process.cwd(), 'data');
export const readJson = (f) => {
  try { return JSON.parse(readFileSync(join(dataDir, f), 'utf-8')); } catch { return null; }
};
export const asDate = (v) => {
  const d = new Date(String(v).length === 10 ? `${v}T12:00:00Z` : v);
  if (isNaN(d)) return null;
  // Yalnız-tarih değerler 12:00Z'ye çevriliyordu → build sabahsa lastmod gelecekte kalıyordu (denetim 2026-10-22).
  return d.getTime() > Date.now() ? new Date() : d;
};
export const updatedOf = (f) => {
  const d = readJson(f);
  if (!d) return null;
  if (d.updated) return asDate(d.updated);
  if (d.guncellenme) return asDate(d.guncellenme);
  // Elle doğrulanan dosyalar (emekli-memur, prim, promosyon, KYK…) `updated` yerine doğrulama günü tutuyor
  // (denetim 2026-11-19 seo-4: beslediği sayfalar sitemap'te lastmod, şemada dateModified alamıyordu).
  for (const k of ['dogrulama', 'dogrulandi', 'kontrol']) if (d[k]) return asDate(d[k]);
  // TCMB/Fed takvimi: açıklanmış son kararın anı (TSİ saatiyle; eskiden 20:00Z sabiti)
  const ms = [...(d.meetings ?? []), ...(d.meetings2027 ?? [])].filter((m) => m.result)
    .map((m) => `${m.decisionDate}T${m.tsiTime ?? '14:00'}:00+03:00`).sort();
  return ms.length ? asDate(ms.at(-1)) : null;
};
const YD = ['yeniden-degerleme.json'];
const TUFE = ['tufe-aylik.json'];
const FAIZ = ['faiz-oranlari.json'];
export const DATA_PAGES = {
  'engelli-maasi': ['tufe-aylik.json', 'asgari-ucret.json'],
  'dogum-yardimi': YD,
  'evde-bakim-maasi': ['asgari-ucret.json', 'tufe-aylik.json'],
  'veraset-ve-intikal-vergisi-hesaplama': YD,
  'noter-ucretleri': YD,
  'tapu-harci-hesaplama': YD,
  'arac-muayene-ucreti': YD,
  'damga-vergisi-hesaplama': YD,
  'tasit-kredisi-hesaplama': FAIZ,
  'yeniden-degerleme-orani': YD, 'mtv-hesaplama': YD, 'pasaport-ehliyet-harci': YD, 'trafik-cezalari-hesaplama': YD,
  'emlak-vergisi-hesaplama': YD, 'gelir-vergisi-hesaplama': YD, 'vergi-dilimi-hesaplama': YD,
  'emekli-zammi-hesaplama': TUFE, 'memur-zammi-hesaplama': TUFE, 'en-dusuk-emekli-maasi': TUFE,
  'enflasyon-hesaplama': TUFE, 'enflasyon-takvimi': TUFE, 'kidem-tazminati-hesaplama': TUFE,
  'kira-artis-orani-hesaplama': ['kira-artis-2026.json'],
  'mevduat-faizi-hesaplama': FAIZ, 'konut-kredisi-hesaplama': FAIZ, 'ihtiyac-kredisi-hesaplama': FAIZ, 'kredi-hesaplama': FAIZ,
  'altin-getiri': ['altin-getiri.json'], 'dolar-getiri': ['dolar-getiri.json'], 'euro-getiri': ['euro-getiri.json'],
  'bist-getiri': ['bist-getiri.json'], 'gumus-getiri': ['gumus-getiri.json'], 'bitcoin-getiri': ['bitcoin-getiri.json'],
  'altin-dolar-borsa': ['altin-getiri.json', 'dolar-getiri.json', 'bist-getiri.json', 'euro-getiri.json', 'gumus-getiri.json', 'bitcoin-getiri.json'],
  'altin-fiyatlari': ['altin-fiyat.json'], 'altin-hesaplama': ['altin-fiyat.json'], 'altin-kac-gram': ['altin-fiyat.json'],
  'dolar-endeksi': ['dxy.json'], 'abd-tahvil-faizi': ['us-tahvil.json'], 'halka-arz': ['halka-arz.json'], 'halka-arz-getiri': ['halka-arz-getiri.json'],
  'tcmb-faiz-takvimi': ['tcmb-2026.json'], 'fed-faiz-takvimi': ['fomc-2026.json'], 'ekonomik-takvim': ['economic-calendar.json'],
  // Sitemap'te lastmod'u olmayan veri beslemeli sayfalar (denetim 2026-11-19 seo-4; dosyalar sayfaların import'larından).
  // zam2027.ts → tufe-aylik.json.
  '2027-zam-hesaplama': ['tufe-aylik.json', 'asgari-ucret.json', 'kira-artis-2026.json'],
  'asgari-ucret-hesaplama': ['asgari-ucret.json'],
  'enflasyon-farki-hesaplama': ['tufe-aylik.json', 'emekli-memur.json'],
  'emekli-refah-payi-seyyanen-zam': ['tufe-aylik.json', 'emekli-memur.json'],
  'dul-ve-yetim-maasi': ['tufe-aylik.json', 'emekli-memur.json'],
  'bedelli-askerlik-ucreti': ['tufe-aylik.json', 'emekli-memur.json'],
  'zam-alarmi': TUFE,
  'bayram-ikramiyesi': ['emekli-memur.json'],
  'emekli-promosyonu': ['emekli-promosyon.json', 'emekli-memur.json'],
  'bagkur-primi-hesaplama': ['bagkur-prim-2026.json', 'asgari-ucret.json'],
  'gss-primi-hesaplama': ['gss-prim-2026.json', 'asgari-ucret.json'],
  'kredi-karti-faiz-hesaplama': ['kredi-karti-faiz.json'],
  'kyk-burs-miktari': ['kyk-burs.json'],
  'otv-hesaplama': ['otv-arac.json', 'yeniden-degerleme.json'],
  'deger-artis-kazanci-hesaplama': ['yiufe-endeks.json', 'yeniden-degerleme.json'],
};
export const lastmodByPage = {};
for (const [page, files] of Object.entries(DATA_PAGES)) {
  const ds = files.map(updatedOf).filter(Boolean);
  if (ds.length) lastmodByPage[page] = new Date(Math.max(...ds)).toISOString();
}

// Halka arz şirket sayfaları (/halka-arz/<slug>/): kaynağın (halkarz.com) şirket güncellemesi "GG.AA.YYYY SS:dd" TSİ ya da
// ilk görülme; işlem gören şirketin getirisi her gün yenilendiği için onlarda getiri dosyasının zamanı (dal 2026-11-03 a9ca5d89).
// Dosyanın 6 saatlik zaman damgası bilerek kullanılmaz: hep yeni bir lastmod arama motorlarınca yok sayılır.
const ipoReturns = readJson('halka-arz-getiri.json');
const ipoRetCodes = new Set((ipoReturns?.items ?? []).map((r) => r.code));
const trStamp = (v) => {
  const m = /^(\d{2})\.(\d{2})\.(\d{4}) (\d{2}):(\d{2})$/.exec(v ?? '');
  return m ? asDate(`${m[3]}-${m[2]}-${m[1]}T${m[4]}:${m[5]}:00+03:00`) : null;
};
export const lastmodByIpo = {};
for (const [slug, it] of Object.entries(readJson('halka-arz-sirketler.json')?.items ?? {})) {
  const ds = [
    trStamp(it.updated_src),
    it.first_seen ? asDate(it.first_seen) : null,
    it.bist_code && ipoRetCodes.has(it.bist_code) && ipoReturns?.updated ? asDate(ipoReturns.updated) : null,
  ].filter(Boolean);
  if (ds.length) lastmodByIpo[slug] = new Date(Math.max(...ds)).toISOString();
}

/** Sayfa yolundan (/altin-fiyatlari/gram-altin/ → altin-fiyatlari) veri tarihini bulur; yoksa undefined. */
export function lastmodForPath(pathname) {
  const parts = String(pathname).replace(/^\/+/, '').split('/').filter(Boolean);
  // Halka arz şirket sayfası: şirkete özgü tarih (yoksa genel halka arz dosyasının tarihi)
  if (parts[0] === 'halka-arz' && parts.length === 2 && lastmodByIpo[parts[1]]) return lastmodByIpo[parts[1]];
  return lastmodByPage[parts[0] ?? ''];
}
