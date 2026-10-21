// Hesaplama/veri araçlarının TEK listesi — /hesaplama-araclari/ (araç merkezi) ve blog yazılarının
// "Bu konuda hesapla" kutusu (src/components/RelatedTools.astro) buradan beslenir.
// Yeni araç sayfası açınca: buraya ekle (+ Footer TOOL_LINKS + scripts/og-images.py CARDS).
// `k` = blog yazısının başlık/etiketlerinde aranacak anahtar kelimeler (küçük harf, Türkçe).
// Sayfa dosyası henüz yoksa (paralel geliştirme) araç listede görünmez — bkz. tools() aşağıda.
import { existsSync } from 'node:fs';
import { join } from 'node:path';

export type Tool = { href: string; ad: string; aciklama: string; k: string[] };
export type Grup = { baslik: string; araclar: Tool[] };

const GRUPLAR_HAM: Grup[] = [
  { baslik: 'Faiz, kredi ve birikim', araclar: [
    { href: '/faiz-hesaplama/', ad: 'Faiz hesaplama', aciklama: 'Basit/bileşik faiz, gün-ay-yıl, net getiri', k: ['faiz hesap', 'basit faiz'] },
    { href: '/mevduat-faizi-hesaplama/', ad: 'Mevduat faizi hesaplama', aciklama: 'Güncel stopajla net vadeli mevduat getirisi', k: ['mevduat', 'vadeli', 'stopaj', 'faiz getirisi', 'para piyasası', 'eurobond fonu'] },
    { href: '/kredi-hesaplama/', ad: 'Kredi hesaplama', aciklama: 'Taksit, toplam faiz ve ödeme planı', k: ['kredi', 'taksit', 'borç', 'yapılandırma', 'kredi kartı'] },
    { href: '/konut-kredisi-hesaplama/', ad: 'Konut kredisi hesaplama', aciklama: 'Peşinat, kredi/değer oranı, taksit tablosu', k: ['konut kredisi', 'ev kredisi', 'konut', 'gayrimenkul'] },
    { href: '/ihtiyac-kredisi-hesaplama/', ad: 'İhtiyaç kredisi hesaplama', aciklama: 'KKDF ve BSMV dahil taksit, BDDK vade sınırı', k: ['ihtiyaç kredisi', 'tüketici kredisi'] },
    { href: '/tasit-kredisi-hesaplama/', ad: 'Taşıt kredisi hesaplama', aciklama: 'Araç kredisi taksiti, BDDK sınırları', k: ['taşıt kredisi', 'araç kredisi', 'otomobil'] },
    { href: '/bilesik-faiz-hesaplama/', ad: 'Bileşik faiz hesaplama', aciklama: 'Düzenli katkıyla uzun vadeli birikim', k: ['bileşik', 'birikim', 'tasarruf', 'pasif gelir', 'emeklilik', 'bes', 'dca', 'uzun vade'] },
    { href: '/bono-hesaplama/', ad: 'Bono hesaplama', aciklama: 'Hazine bonosu getiri hesabı', k: ['bono', 'tahvil', 'sabit getiri', 'hazine'] },
    { href: '/yuzde-hesaplama/', ad: 'Yüzde hesaplama', aciklama: 'Yüzdesi, yüzde kaç, artış ve indirim', k: ['yüzde'] },
  ] },
  { baslik: 'Maaş, zam ve tazminat', araclar: [
    { href: '/net-maas-hesaplama/', ad: 'Net maaş hesaplama', aciklama: 'Brütten nete, vergi ve SGK kesintileri', k: ['maaş', 'net maaş', 'brüt', 'bordro', 'ücret'] },
    { href: '/asgari-ucret-hesaplama/', ad: 'Asgari ücret', aciklama: 'Net-brüt asgari ücret ve işveren maliyeti', k: ['asgari ücret'] },
    { href: '/emekli-zammi-hesaplama/', ad: 'Emekli zammı hesaplama', aciklama: 'SSK, Bağ-Kur ve memur emeklisi zammı', k: ['emekli', 'emeklilik', 'ssk', 'bağ-kur'] },
    { href: '/memur-zammi-hesaplama/', ad: 'Memur zammı hesaplama', aciklama: 'Ocak 2027 memur zammı tahmini ve katsayılar', k: ['memur'] },
    { href: '/en-dusuk-emekli-maasi/', ad: 'En düşük emekli maaşı', aciklama: 'Taban aylık, Ocak 2027 senaryosu, ödeme günleri', k: ['emekli maaşı', 'en düşük emekli'] },
    { href: '/engelli-maasi/', ad: 'Engelli maaşı ve 65 yaş aylığı', aciklama: 'Ocak 2027 tahmini ve 2026 tutarları', k: ['engelli', '65 yaş', 'yaşlılık aylığı'] },
    { href: '/evde-bakim-maasi/', ad: 'Evde bakım maaşı', aciklama: '2027 tutarı ve hane geliri şartı', k: ['evde bakım'] },
    { href: '/dogum-yardimi/', ad: 'Doğum yardımı', aciklama: '2026 tutarları, şartlar ve başvuru', k: ['doğum yardımı', 'doğum', 'çocuk'] },
    { href: '/bayram-ikramiyesi/', ad: 'Bayram ikramiyesi', aciklama: 'Emekli ikramiyesi tutarı ve 2027 bayram tarihleri', k: ['bayram ikramiye'] },
    { href: '/kidem-tazminati-hesaplama/', ad: 'Kıdem tazminatı hesaplama', aciklama: 'Tavan dahil kıdem tazminatı ve 2027 tavan tahmini', k: ['kıdem', 'tazminat', 'işten çıkar'] },
    { href: '/ihbar-tazminati-hesaplama/', ad: 'İhbar tazminatı hesaplama', aciklama: '2-8 haftalık ihbar süresi, brüt ve net tutar', k: ['ihbar'] },
    { href: '/yillik-izin-hesaplama/', ad: 'Yıllık izin hesaplama', aciklama: '14/20/26 gün hak ve kullanılmayan izin ücreti', k: ['yıllık izin', 'izin'] },
    { href: '/issizlik-maasi-hesaplama/', ad: 'İşsizlik maaşı hesaplama', aciklama: 'Süre ve aylık ödenek', k: ['işsizlik maaşı', 'işsizlik ödeneği'] },
    { href: '/bagkur-primi-hesaplama/', ad: 'Bağ-Kur primi hesaplama', aciklama: '2026 en düşük/en yüksek prim, 5 puan indirimi', k: ['bağ-kur primi', 'bağkur', 'esnaf', 'prim borcu', 'sgk prim'] },
  ] },
  { baslik: 'Vergi, harç ve zamlar', araclar: [
    { href: '/vergi-dilimi-hesaplama/', ad: 'Vergi dilimi hesaplama', aciklama: 'Gelir vergisi dilimleri ve kümülatif matrah', k: ['vergi dilim', 'gelir vergisi'] },
    { href: '/gelir-vergisi-hesaplama/', ad: 'Gelir vergisi hesaplama', aciklama: 'Kira, serbest meslek ve ticari kazanç beyannamesi', k: ['gelir vergisi', 'kira geliri', 'beyanname', 'vergi'] },
    { href: '/deger-artis-kazanci-hesaplama/', ad: 'Değer artış kazancı hesaplama', aciklama: 'Ev satışında 5 yıl kuralı, Yİ-ÜFE endeksi, 150.000 ₺ istisna', k: ['değer artış', 'ev satışı', 'konut satışı', 'gayrimenkul satış'] },
    { href: '/kurumlar-vergisi-hesaplama/', ad: 'Kurumlar vergisi hesaplama', aciklama: 'Oran %25, asgari vergi %10, 2027 üretimde %12,5', k: ['kurumlar vergisi', 'şirket', 'asgari kurumlar'] },
    { href: '/vergi-borcu-sorgulama/', ad: 'Vergi borcu sorgulama', aciklama: 'Adım adım sorgulama, gecikme zammı hesabı', k: ['vergi borcu', 'gecikme zammı', 'borç sorgula'] },
    { href: '/kdv-hesaplama/', ad: 'KDV hesaplama', aciklama: 'KDV ekle, KDV dahil fiyattan ayır', k: ['kdv'] },
    { href: '/damga-vergisi-hesaplama/', ad: 'Damga vergisi hesaplama', aciklama: 'Oranlar, maktu tutarlar, 2027 tahmini', k: ['damga vergisi'] },
    { href: '/emlak-vergisi-hesaplama/', ad: 'Emlak vergisi hesaplama', aciklama: 'Oranlar, taksitler, 2027 tahmini', k: ['emlak vergisi', 'emlak', 'gayrimenkul', 'konut'] },
    { href: '/tapu-harci-hesaplama/', ad: 'Tapu harcı hesaplama', aciklama: 'Alıcı-satıcı harcı ve döner sermaye', k: ['tapu', 'ev al', 'konut al', 'gayrimenkul'] },
    { href: '/veraset-ve-intikal-vergisi-hesaplama/', ad: 'Veraset ve intikal vergisi', aciklama: 'Miras ve bağışta istisna, dilim, vergi', k: ['veraset', 'miras', 'intikal', 'bağış'] },
    { href: '/mtv-hesaplama/', ad: 'MTV hesaplama', aciklama: 'Motorlu taşıtlar vergisi 2027', k: ['mtv', 'motorlu taşıt', 'araç vergisi', 'otomobil'] },
    { href: '/arac-muayene-ucreti/', ad: 'Araç muayene ücreti', aciklama: 'TÜVTÜRK ücretleri ve gecikme hesabı', k: ['muayene', 'tüvtürk'] },
    { href: '/noter-ucretleri/', ad: 'Noter ücretleri', aciklama: 'Araç satış, vekaletname ve onay ücretleri', k: ['noter', 'vekaletname'] },
    { href: '/yeniden-degerleme-orani/', ad: 'Yeniden değerleme oranı', aciklama: '2027 harç, ceza ve vergi zammı oranı', k: ['yeniden değerleme', '2027 zam', 'harç', 'zamlar'] },
    { href: '/kira-artis-orani-hesaplama/', ad: 'Kira artış oranı', aciklama: 'Güncel TÜFE 12 aylık ortalamasıyla', k: ['kira'] },
    { href: '/enflasyon-hesaplama/', ad: 'Enflasyon hesaplama', aciklama: 'İki tarih arası TÜFE ve paranın bugünkü değeri', k: ['enflasyon', 'tüfe', 'alım gücü', 'reel', 'dezenflasyon'] },
    { href: '/trafik-cezalari-hesaplama/', ad: 'Trafik cezaları', aciklama: 'Ceza tutarları, 1 ay içinde %25 indirim', k: ['trafik ceza'] },
    { href: '/pasaport-ehliyet-harci/', ad: 'Pasaport ve ehliyet harcı', aciklama: 'Güncel harç tutarları', k: ['pasaport', 'ehliyet', 'imei'] },
  ] },
  { baslik: 'Altın', araclar: [
    { href: '/altin-fiyatlari/', ad: 'Altın fiyatları bugün', aciklama: 'Tüm türlerin alış-satış fiyatı', k: ['altın fiyat', 'çeyrek', 'cumhuriyet altını', 'bilezik'] },
    { href: '/altin-hesaplama/', ad: 'Altın hesaplama', aciklama: 'Elindeki altının toplam değeri', k: ['gram altın', 'altın hesap', 'altın'] },
    { href: '/altin-kac-gram/', ad: 'Altın kaç gram?', aciklama: 'Resmî sikke/ziynet ağırlık tablosu', k: ['kaç gram', 'ayar', 'ziynet'] },
    { href: '/altin-getiri/', ad: 'Altın getirisi', aciklama: '1-10 yıllık TL getirisi', k: ['altın', 'altın yatırımı', 'güvenli liman'] },
  ] },
  { baslik: 'Getiri ve piyasa verisi', araclar: [
    { href: '/altin-dolar-borsa/', ad: 'Altın mı, dolar mı, borsa mı?', aciklama: 'Varlıkların karşılaştırmalı getirisi', k: ['yatırım', 'portföy', 'karşılaştır'] },
    { href: '/dolar-getiri/', ad: 'Dolar getirisi', aciklama: 'Dolar/TL tarihsel getiri', k: ['dolar', 'döviz', 'dolar kuru', 'usd'] },
    { href: '/euro-getiri/', ad: 'Euro getirisi', aciklama: 'Euro/TL tarihsel getiri', k: ['euro', 'ecb', 'avrupa'] },
    { href: '/bist-getiri/', ad: 'BIST 100 getirisi', aciklama: 'Borsa İstanbul tarihsel getiri', k: ['borsa', 'bist', 'hisse', 'endeks', 'temettü'] },
    { href: '/bitcoin-getiri/', ad: 'Bitcoin getirisi', aciklama: 'TL bazında bitcoin getirisi', k: ['bitcoin', 'kripto'] },
    { href: '/gumus-getiri/', ad: 'Gümüş getirisi', aciklama: 'TL bazında gümüş getirisi', k: ['gümüş'] },
    { href: '/halka-arz/', ad: 'Halka arz takvimi', aciklama: 'Güncel ve yaklaşan halka arzlar', k: ['halka arz', 'ipo'] },
    { href: '/halka-arz-getiri/', ad: 'Halka arz getirileri', aciklama: 'Halka arzların ilk gün ve sonrası getirisi', k: ['halka arz'] },
  ] },
  { baslik: 'Takvimler', araclar: [
    { href: '/ekonomik-takvim/', ad: 'Ekonomik takvim', aciklama: 'Haftanın önemli veri ve kararları', k: ['veri', 'istihdam', 'nfp', 'cpi', 'pce', 'gdp', 'büyüme', 'ekonomik takvim'] },
    { href: '/tcmb-faiz-takvimi/', ad: 'TCMB faiz takvimi', aciklama: 'PPK tarihleri ve kararlar', k: ['tcmb', 'merkez bankası', 'ppk', 'politika faizi'] },
    { href: '/fed-faiz-takvimi/', ad: 'Fed faiz takvimi', aciklama: 'FOMC tarihleri ve kararlar', k: ['fed', 'fomc', 'abd faiz', 'powell', 'warsh'] },
    { href: '/enflasyon-takvimi/', ad: 'Enflasyon takvimi', aciklama: 'TÜİK enflasyon açıklama tarihleri', k: ['tüik', 'enflasyon verisi', 'tüfe'] },
  ] },
];

const exists = (href: string) => existsSync(join(process.cwd(), 'src', 'pages', `${href.replace(/^\/|\/$/g, '')}.astro`))
  || existsSync(join(process.cwd(), 'src', 'pages', href.replace(/^\/|\/$/g, ''), 'index.astro'));

// Sayfa dosyası olan araçlar (yeni araç paralel geliştirilirken bağlantı kırılmasın)
export const GRUPLAR: Grup[] = GRUPLAR_HAM.map((g) => ({ ...g, araclar: g.araclar.filter((t) => exists(t.href)) }));
export const TOOLS: Tool[] = GRUPLAR.flatMap((g) => g.araclar);

// Kategori yedekleri (anahtar kelime eşleşmezse)
const KATEGORI: Record<string, string[]> = {
  'Borsa': ['/bist-getiri/', '/altin-dolar-borsa/', '/halka-arz/'],
  'Yatırım': ['/altin-dolar-borsa/', '/bilesik-faiz-hesaplama/', '/altin-getiri/'],
  'Kişisel Finans': ['/bilesik-faiz-hesaplama/', '/net-maas-hesaplama/', '/kredi-hesaplama/'],
  'Ekonomi': ['/enflasyon-hesaplama/', '/tcmb-faiz-takvimi/', '/ekonomik-takvim/'],
  'Kripto': ['/bitcoin-getiri/', '/altin-dolar-borsa/', '/dolar-getiri/'],
  'Emeklilik': ['/emekli-zammi-hesaplama/', '/bilesik-faiz-hesaplama/', '/en-dusuk-emekli-maasi/'],
};

const lower = (s: string) => s.replace(/I/g, 'ı').replace(/İ/g, 'i').toLowerCase();

/** Blog yazısı için en alakalı ≤n araç: etiket eşleşmesi 3, başlık 2 puan; gövdede zaten linkli araçlar atlanır. */
export function relatedTools(o: { title: string; tags?: string[]; category?: string; body?: string }, n = 3): Tool[] {
  const title = lower(o.title);
  const tags = (o.tags ?? []).map(lower);
  const body = o.body ?? '';
  const skor = new Map<string, number>();
  for (const t of TOOLS) {
    if (body.includes(t.href.replace(/\/$/, ''))) continue; // yazı zaten link veriyor
    let s = 0;
    for (const kw of t.k) {
      if (tags.some((tg) => tg.includes(kw))) s += 3;
      if (title.includes(kw)) s += 2;
    }
    if (s > 0) skor.set(t.href, s);
  }
  const sec = [...skor.entries()].sort((a, b) => b[1] - a[1]).map(([h]) => h);
  for (const h of KATEGORI[o.category ?? ''] ?? []) if (!sec.includes(h) && !body.includes(h.replace(/\/$/, ''))) sec.push(h);
  return sec.slice(0, n).map((h) => TOOLS.find((t) => t.href === h)).filter((t): t is Tool => !!t);
}
