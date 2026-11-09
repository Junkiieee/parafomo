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
  // TCMB/Fed takvimi: açıklanmış son kararın günü
  const ms = [...(d.meetings ?? []), ...(d.meetings2027 ?? [])].filter((m) => m.result).map((m) => m.decisionDate).sort();
  return ms.length ? asDate(`${ms.at(-1)}T20:00:00Z`) : null;
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
};
export const lastmodByPage = {};
for (const [page, files] of Object.entries(DATA_PAGES)) {
  const ds = files.map(updatedOf).filter(Boolean);
  if (ds.length) lastmodByPage[page] = new Date(Math.max(...ds)).toISOString();
}

/** Sayfa yolundan (/altin-fiyatlari/gram-altin/ → altin-fiyatlari) veri tarihini bulur; yoksa undefined. */
export function lastmodForPath(pathname) {
  const seg = String(pathname).replace(/^\/+/, '').split('/')[0];
  return lastmodByPage[seg];
}
