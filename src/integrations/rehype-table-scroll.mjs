// Markdown tablolarını <div class="table-scroll"> içine sarar.
// Neden: geniş tablolar mobilde (375px) bütün sayfayı yana kaydırıyordu;
// sarmalayıcı sayesinde yalnızca tablo kendi içinde kayar. Kutu klavyeyle odaklanabilir
// (tabindex) ve adlı bir bölgedir; ad, tablodan önceki son başlıktan gelir ve sayfada
// benzersizdir ("Tablo 2: Senaryolar") — iki tablolu yazılarda hepsi "Tablo" idi (axe landmark-unique).
const textOf = (node) =>
  node.type === 'text' ? node.value : (node.children ?? []).map(textOf).join('');

export default function rehypeTableScroll() {
  return (tree) => {
    let count = 0;
    let heading = '';
    const walk = (node) => {
      if (!node.children) return;
      node.children = node.children.map((child) => {
        if (child.type === 'element' && /^h[2-4]$/.test(child.tagName)) heading = textOf(child).trim();
        if (child.type === 'element' && child.tagName === 'table') {
          count += 1;
          return {
            type: 'element',
            tagName: 'div',
            properties: {
              className: ['table-scroll'],
              tabIndex: 0,
              role: 'region',
              ariaLabel: heading ? `Tablo ${count}: ${heading}` : `Tablo ${count}`,
            },
            children: [child],
          };
        }
        walk(child);
        return child;
      });
    };
    walk(tree);
  };
}
