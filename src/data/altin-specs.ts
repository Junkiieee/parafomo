// Altın türlerinin RESMÎ ağırlık/ayar bilgisi — tek kaynak.
// Kaynak: T.C. Hazine ve Maliye Bakanlığı, "Sorularla Cumhuriyet Altını" (Darphane), Soru 3 tablosu:
// sikke çeyrek/yarım/birlik/2,5/5'lik = 1,804 / 3,608 / 7,216 / 18,040 / 36,080 g;
// ziynet = 1,754 / 3,508 / 7,016 / 17,540 / 35,080 g; Cumhuriyet ve Reşad altınlarının tümü 22 ayar.
// "Ata Lira" = 7,216 g birlik SİKKE altın (aynı belge). Fiyatlar data/altin-fiyat.json'dan (key alanı).

export const HMB_KAYNAK =
  'https://ms.hmb.gov.tr/uploads/sites/7/2026/08/Sorularla_Cumhuriyet_Altini-c412193a82fc0317.pdf';

export type AltinSpec = {
  key: string;        // data/altin-fiyat.json kalem anahtarı
  slug: string;       // /altin-fiyatlari/<slug>/
  ad: string;         // görünen ad
  kisa: string;       // cümle içi kısa ad
  gram: number;       // brüt ağırlık (g)
  milyem: number;     // saflık /1000
  ayar: string;
  grup: 'kulce' | 'ziynet' | 'sikke' | 'ayar' | 'ons';
  birim: 'adet' | 'gram' | 'ons';
  not: string;        // türü tanıtan tek cümle
};

const AYAR22 = 916; // 22/24 = 0,9166… → piyasada 916 milyem

export const ALTIN_SPECS: AltinSpec[] = [
  { key: 'gram-altin', slug: 'gram-altin', ad: 'Gram Altın', kisa: 'gram altın', gram: 1, milyem: 995,
    ayar: '24 ayar (995)', grup: 'kulce', birim: 'gram',
    not: 'Bankalarda ve kuyumcuda en çok işlem gören, 24 ayar (995 milyem) 1 gramlık külçe altın.' },
  { key: 'gram-has-altin', slug: 'has-altin', ad: 'Has Altın', kisa: 'has altın', gram: 1, milyem: 999,
    ayar: '24 ayar (999,9)', grup: 'kulce', birim: 'gram',
    not: 'En saf (999,9 milyem) altın; kuyumcular arası toptan fiyatlamada referans alınır.' },
  { key: 'ceyrek-altin', slug: 'ceyrek-altin', ad: 'Çeyrek Altın', kisa: 'çeyrek altın', gram: 1.754, milyem: AYAR22,
    ayar: '22 ayar', grup: 'ziynet', birim: 'adet',
    not: 'Piyasada "çeyrek" denince kastedilen Cumhuriyet ziynet çeyreğidir: 1,754 gram, 22 ayar. Sikke çeyrek 1,804 gramdır.' },
  { key: 'yarim-altin', slug: 'yarim-altin', ad: 'Yarım Altın', kisa: 'yarım altın', gram: 3.508, milyem: AYAR22,
    ayar: '22 ayar', grup: 'ziynet', birim: 'adet',
    not: 'Cumhuriyet ziynet yarım altını 3,508 gram ve 22 ayardır; iki çeyreğe denk ağırlıktadır.' },
  { key: 'tam-altin', slug: 'tam-altin', ad: 'Tam Altın', kisa: 'tam altın', gram: 7.016, milyem: AYAR22,
    ayar: '22 ayar', grup: 'ziynet', birim: 'adet',
    not: 'Tam (ziynet birlik) altın 7,016 gram ve 22 ayardır; düğün ve hediyede en çok kullanılan tür.' },
  { key: 'cumhuriyet-altini', slug: 'cumhuriyet-altini', ad: 'Cumhuriyet Altını', kisa: 'Cumhuriyet altını', gram: 7.216, milyem: AYAR22,
    ayar: '22 ayar', grup: 'sikke', birim: 'adet',
    not: 'Cumhuriyet altın sikkesinin birliği 7,216 gram ve 22 ayardır; ziynet tama göre daha küçük çaplı ama daha kalın ve ağırdır.' },
  { key: 'ata-altin', slug: 'ata-altin', ad: 'Ata Altın', kisa: 'Ata altın', gram: 7.216, milyem: AYAR22,
    ayar: '22 ayar', grup: 'sikke', birim: 'adet',
    not: 'Halk arasında "Ata Lira" denen altın, Hazine ve Maliye Bakanlığı tanımıyla 7,216 gramlık birlik Cumhuriyet sikke altınıdır.' },
  { key: '22-ayar-bilezik', slug: '22-ayar-bilezik', ad: '22 Ayar Bilezik', kisa: '22 ayar bilezik', gram: 1, milyem: AYAR22,
    ayar: '22 ayar', grup: 'ayar', birim: 'gram',
    not: '22 ayar (916 milyem) altının gram fiyatı; bilezik alırken buna ayrıca işçilik eklenir, bozdururken işçilik geri alınmaz.' },
  { key: '18-ayar-altin', slug: '18-ayar-altin', ad: '18 Ayar Altın', kisa: '18 ayar altın', gram: 1, milyem: 750,
    ayar: '18 ayar (750)', grup: 'ayar', birim: 'gram',
    not: '18 ayar altın %75 saf altın içerir (750 milyem); takı ve pırlanta montürlerinde yaygındır.' },
  { key: '14-ayar-altin', slug: '14-ayar-altin', ad: '14 Ayar Altın', kisa: '14 ayar altın', gram: 1, milyem: 585,
    ayar: '14 ayar (585)', grup: 'ayar', birim: 'gram',
    not: '14 ayar altın yaklaşık %58,5 saf altın içerir (585 milyem); günlük takılarda dayanıklılığı için tercih edilir.' },
  { key: 'ons', slug: 'ons-altin', ad: 'Ons Altın', kisa: 'ons altın', gram: 31.1035, milyem: 999,
    ayar: '24 ayar', grup: 'ons', birim: 'ons',
    not: 'Ons (troy ons) = 31,1035 gram; uluslararası altın fiyatı ons başına ABD doları ile verilir.' },
];

// Resmî Darphane tablosu (gram/adet) — /altin-kac-gram ve tablolar için
export const DARPHANE_TABLO = [
  { cesit: 'Çeyrek', sikke: 1.804, ziynet: 1.754 },
  { cesit: 'Yarım', sikke: 3.608, ziynet: 3.508 },
  { cesit: 'Birlik (Tam / Ata)', sikke: 7.216, ziynet: 7.016 },
  { cesit: 'İki buçukluk (Gremse)', sikke: 18.04, ziynet: 17.54 },
  { cesit: 'Beşlik', sikke: 36.08, ziynet: 35.08 },
];

export const hasGram = (s: { gram: number; milyem: number }) => (s.gram * s.milyem) / 1000;
