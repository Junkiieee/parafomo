import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const blog = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    category: z.enum([
      'Yatırım',
      'Borsa',
      'Kripto',
      'Kişisel Finans',
      'Ekonomi',
      'Emeklilik',
    ]),
    tags: z.array(z.string()).default([]),
    author: z.string().default('ParaFOMO Editörlüğü'),
    readingTime: z.number().optional(),
    draft: z.boolean().default(false),
    featured: z.boolean().default(false),
    cover: z.string().optional(),
    // Sıkça Sorulan Sorular — verilirse sayfada görünür SSS bölümü + FAQPage schema üretilir.
    faq: z.array(z.object({ q: z.string(), a: z.string() })).optional(),
    // Olay önizlemesi: "tcmb:YYYY-MM-DD" | "fed:YYYY-MM-DD" | "tufe:YYYY-MM" → veri açıklanınca otomatik sonuç kutusu
    // (src/data/event-result.ts). sonucBaslik: açıklanınca kullanılacak başlık; yer tutucular {oran} {onceki} {bp}
    // {karar} (tcmb) · {bant} {bp} {karar} (fed) · {ay} {aylik} {yillik} (tufe).
    sonuc: z.string().regex(/^(tcmb|fed):\d{4}-\d{2}-\d{2}$|^tufe:\d{4}-\d{2}$/).optional(),
    sonucBaslik: z.string().optional(),
    // YouTube Shorts senaryosu (kalıcı kayıt): [0]=kanca, ortadakiler=vuruşlar, [-1]=CTA.
    // scripts/shorts-script.py üretir; scripts/shorts-build.py kullanır. Sayfada gösterilmez.
    shorts: z.array(z.string()).optional(),
    shorts_broll: z.array(z.string()).optional(),
  }),
});

export const collections = { blog };
