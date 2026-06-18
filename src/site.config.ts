/**
 * ParaFOMO — merkezi site ayarları.
 * Marka bilgisi, navigasyon ve sosyal linkler buradan yönetilir.
 */
export const SITE = {
  name: 'ParaFOMO',
  tagline: 'Parana akıl kat.',
  description:
    'ParaFOMO; yatırım, borsa, kripto ve kişisel finans üzerine sade, güvenilir ve uygulanabilir Türkçe rehberler sunar. Paranı korumayı ve büyütmeyi öğren.',
  url: 'https://parafomo.com',
  locale: 'tr_TR',
  lang: 'tr',
  author: 'ParaFOMO',
  email: 'merhaba@parafomo.com',
  // Yayına alırken doğru kullanıcı adlarıyla güncelle.
  social: {
    x: 'https://x.com/parafomo',
    instagram: 'https://instagram.com/parafomo',
    youtube: '',
  },
};

export const NAV = [
  { label: 'Anasayfa', href: '/' },
  { label: 'Yazılar', href: '/blog' },
  { label: 'Yatırım', href: '/kategori/yatirim' },
  { label: 'Borsa', href: '/kategori/borsa' },
  { label: 'Kripto', href: '/kategori/kripto' },
  { label: 'Kişisel Finans', href: '/kategori/kisisel-finans' },
  { label: 'Hakkımızda', href: '/hakkimizda' },
];

export const CATEGORIES = [
  { name: 'Yatırım', slug: 'yatirim', desc: 'Uzun vadeli servet inşası, portföy ve varlık dağılımı.' },
  { name: 'Borsa', slug: 'borsa', desc: 'BIST ve global piyasalar, hisse analizi, temettü.' },
  { name: 'Kripto', slug: 'kripto', desc: 'Bitcoin, altcoin, blokzincir ve risk yönetimi.' },
  { name: 'Kişisel Finans', slug: 'kisisel-finans', desc: 'Bütçe, tasarruf, borç ve harcama disiplini.' },
  { name: 'Ekonomi', slug: 'ekonomi', desc: 'Enflasyon, faiz, döviz ve makroekonomi.' },
  { name: 'Emeklilik', slug: 'emeklilik', desc: 'BES, uzun vadeli planlama ve finansal özgürlük.' },
];

/** Kategori adından URL slug'ına çeviri. */
export function categorySlug(name: string): string {
  const map: Record<string, string> = {
    'Yatırım': 'yatirim',
    'Borsa': 'borsa',
    'Kripto': 'kripto',
    'Kişisel Finans': 'kisisel-finans',
    'Ekonomi': 'ekonomi',
    'Emeklilik': 'emeklilik',
  };
  return map[name] ?? name.toLowerCase();
}
