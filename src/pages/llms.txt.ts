// llms.txt — yapay zekâ botlarına (ChatGPT, Claude, Perplexity…) sitenin haritası. Her build'de ÜRETİLİR (2026-11-09):
// eskiden public/llms.txt elle yazılmıştı ve araçların çoğu eksikti. Kaynaklar: araç listesi src/data/tools.ts,
// güncel rakamlar data/*.json, rehberler blog koleksiyonu. Bir rakam okunamazsa satırı atlanır (dosya asla kırılmaz).
import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { GRUPLAR } from '../data/tools';
import altin from '../../data/altin-fiyat.json';
import kira from '../../data/kira-artis-2026.json';
import yd from '../../data/yeniden-degerleme.json';
import tufe from '../../data/tufe-aylik.json';
import tcmb from '../../data/tcmb-2026.json';
import kart from '../../data/kredi-karti-faiz.json';

const U = 'https://parafomo.com';
const pct = (n: number) => '%' + n.toLocaleString('tr-TR', { maximumFractionDigits: 2 });
const tl = (n: number) => Math.round(n).toLocaleString('tr-TR') + ' TL';
const gun = (s: string) => new Date(s).toLocaleDateString('tr-TR', { timeZone: 'Europe/Istanbul', day: 'numeric', month: 'long', year: 'numeric' });

function rakamlar(): string[] {
  const out: string[] = [];
  const tryAdd = (fn: () => string | null) => { try { const s = fn(); if (s) out.push(s); } catch { /* atla */ } };
  tryAdd(() => {
    const m = (tufe as any).months?.[0];
    return m ? `- Yıllık TÜFE enflasyonu (TÜİK, ${m.ay}): ${pct(m.yillik)}; aylık ${pct(m.aylik)} — ${U}/enflasyon-hesaplama/` : null;
  });
  tryAdd(() => `- Kira artış tavanı (${(kira as any).guncelAy}, 12 aylık TÜFE ortalaması, TBK md. 344): ${pct((kira as any).guncelOran)} — ${U}/kira-artis-orani-hesaplama/`);
  tryAdd(() => {
    const y = yd as any;
    if (!y.ekimVerisiGeldi) return null;
    const resmi = y.tebligOrani ? `VUK tebliğiyle ${pct(y.tebligOrani)}` : `Ekim Yİ-ÜFE ile hesaplanan ${pct(y.onikiAyOrt)} (VUK tebliği Kasım sonunda)`;
    return `- ${y.hedefYil} yeniden değerleme oranı: ${resmi}; harç, idari para cezası ve vergi tutarlarının artış oranı — ${U}/yeniden-degerleme-orani/`;
  });
  tryAdd(() => {
    const done = (tcmb as any).meetings.filter((m: any) => m.result?.rate != null);
    const last = done[done.length - 1];
    return last ? `- TCMB politika faizi (${gun(last.decisionDate)} PPK kararı): ${pct(last.result.rate)} — ${U}/tcmb-faiz-takvimi/` : null;
  });
  tryAdd(() => {
    const t = (kart as any).tl?.[0];
    return t ? `- Kredi kartı azami aylık akdi faizi (TCMB, en düşük dilim; geçerlilik: ${gun((kart as any).gecerli)}): ${pct(t.akdi)}; gecikme faizi ${pct(t.gecikme)} — ${U}/kredi-karti-faiz-hesaplama/` : null;
  });
  tryAdd(() => {
    const g = (altin as any).kalemler.find((k: any) => k.key === 'gram-altin');
    const c = (altin as any).kalemler.find((k: any) => k.key === 'ceyrek-altin');
    return g && c ? `- Altın (gösterge, ${gun((altin as any).guncellenme)}): gram satış ${tl(g.satis)}, çeyrek satış ${tl(c.satis)} — ${U}/altin-fiyatlari/` : null;
  });
  return out;
}

export const GET: APIRoute = async () => {
  const posts = (await getCollection('blog', ({ data }) => !data.draft))
    .sort((a, b) => +new Date(b.data.pubDate) - +new Date(a.data.pubDate))
    .slice(0, 40);

  const lines: string[] = [
    '# ParaFOMO',
    '',
    '> ParaFOMO (parafomo.com), Türk tasarruf sahiplerinin enflasyon karşısında birikimini veriyle korumasına yardım eden Türkçe kişisel finans sitesidir. Maaş, emekli ve memur zammı, sosyal yardımlar, vergi-harç zamları, kredi ve mevduat için güncel resmî oranlarla hesaplayıcılar; altın, gümüş, dolar, euro, BIST 100 ve bitcoin için TL bazında tarihsel getiri tabloları; TCMB, TÜİK ve Fed takvimleri; halka arz takvimi sunar. Yatırım tavsiyesi vermez; rakamı kaynağı ve tarihiyle gösterir.',
    '',
    `Veri sayfaları otomatik güncellenir (kaynaklar: TÜİK, TCMB/EVDS, Resmî Gazete, Gelir İdaresi, SGK, Yahoo Finance, halkarz.com). Her sayfada "son güncelleme" tarihi ve yöntem notu vardır: ${U}/metodoloji/`,
    '',
    '## Güncel rakamlar (bu dosya her yayında yeniden üretilir)',
    ...rakamlar(),
    '',
  ];
  for (const g of GRUPLAR) {
    lines.push(`## ${g.baslik}`);
    for (const t of g.araclar) lines.push(`- [${t.ad}](${U}${t.href}): ${t.aciklama}`);
    lines.push('');
  }
  lines.push('## Son rehberler');
  for (const p of posts) {
    const d = (p.data as any).description as string | undefined;
    lines.push(`- [${p.data.title}](${U}/blog/${p.id}/)${d ? `: ${d}` : ''}`);
  }
  lines.push(`- Tüm yazılar: ${U}/blog/`, '');
  lines.push('## Diğer');
  lines.push(`- [Portföy takip](https://app.parafomo.com/portfoy/): BIST, altın ve gümüş için ücretsiz portföy takibi`);
  lines.push(`- [Araçları sitene ekle](${U}/sitene-ekle/): altın fiyat tablosu ve kira artış hesaplayıcısı için gömme kodu`);
  lines.push(`- [Haftalık bülten](${U}/bulten/)`);
  lines.push('');
  lines.push('## Hakkında');
  lines.push(`- [Hakkımızda](${U}/hakkimizda/)`, `- [Editoryal politika](${U}/editoryal-politika/)`, `- [Metodoloji](${U}/metodoloji/)`, `- [İletişim](${U}/iletisim/)`, '');

  return new Response(lines.join('\n'), { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
