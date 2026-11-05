import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import { SITE } from '../site.config';
import { eventResult, fillTitle } from '../data/event-result';

export async function GET(context) {
  const posts = (await getCollection('blog', ({ data }) => !data.draft)).sort(
    (a, b) => b.data.pubDate.getTime() - a.data.pubDate.getTime()
  );

  return rss({
    title: `${SITE.name} — ${SITE.tagline}`,
    description: SITE.description,
    site: context.site,
    xmlns: { atom: 'http://www.w3.org/2005/Atom' },
    items: posts.map((post) => {
      // Olay yazısında sonuç açıklandıysa sayfadaki "…Açıklandı…" başlığı (PostLayout / news-sitemap ile aynı kural).
      const ev = eventResult(post.data.sonuc);
      return {
        title: (ev?.done && fillTitle(post.data.sonucBaslik, ev.vars)) || post.data.title,
        description: post.data.description,
        pubDate: post.data.pubDate,
        categories: [post.data.category, ...post.data.tags],
        link: `/blog/${post.id}/`,
      };
    }),
    customData: `<language>tr-tr</language><atom:link href="${new URL('rss.xml', SITE.url).href}" rel="self" type="application/rss+xml" />`,
  });
}
