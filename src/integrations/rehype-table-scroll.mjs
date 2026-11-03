// Markdown tablolarını <div class="table-scroll"> içine sarar.
// Neden: geniş tablolar mobilde (375px) bütün sayfayı yana kaydırıyordu;
// sarmalayıcı sayesinde yalnızca tablo kendi içinde kayar.
export default function rehypeTableScroll() {
  const walk = (node) => {
    if (!node.children) return;
    node.children = node.children.map((child) => {
      if (child.type === 'element' && child.tagName === 'table') {
        return {
          type: 'element',
          tagName: 'div',
          properties: { className: ['table-scroll'], tabIndex: 0, role: 'region', ariaLabel: 'Tablo' },
          children: [child],
        };
      }
      walk(child);
      return child;
    });
  };
  return (tree) => walk(tree);
}
