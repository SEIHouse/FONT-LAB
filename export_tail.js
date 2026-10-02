function exportRecord(ch, S){
  const g = glyph(ch, S);
  const paths = [...g.body.matchAll(/<path d="([^"]+)" fill="none" stroke="currentColor" stroke-width="([^"]+)"/g)].map(m => ({ d:m[1], w:+m[2] }));
  const circles = [...g.body.matchAll(/<circle cx="([^"]+)" cy="([^"]+)" r="([^"]+)"/g)].map(m => [+m[1], +m[2], +m[3]]);
  const fills = [...g.body.matchAll(/<path data-fill="1" d="([^"]+)"[^>]*stroke-width="([^"]+)"/g)].map(m => ({ d:m[1], sw:+m[2] }));
  const latin=READING_LETTERS.has(ch) || ACC[ch] || DOTLESS[ch] || ch==='◌';
  return { paths, circles, fills, sb0:g.sb0, sb1:g.sb1, w:g.w,
           ...(COMBINING[ch] ? {mark:g.mark,attach:g.attach,anchors:g.anchors}
             : latin ? {anchors:latinAnchors(ch,S)} : {}) };
}
window.exportGlyphs = S => Object.fromEntries(Object.keys(G).map(ch => [ch, exportRecord(ch, S)]));
window.exportAlternates = S => Object.fromEntries(Object.keys(NUMERIC_VARIANTS)
  .filter(name => name.endsWith('.tf') || name.endsWith('.numr') || name.endsWith('.dnom'))
  .concat(Object.keys(DOTLESS)).map(name => [name, exportRecord(name, S)]));
window.getKern = () => KERN;
window.getP = () => P;

