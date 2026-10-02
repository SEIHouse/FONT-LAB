window.exportGlyphs = function(S){
  const out = {};
  for(const ch of Object.keys(G)){
    const g = glyph(ch, S);
    const paths = [...g.body.matchAll(/<path d="([^"]+)" fill="none" stroke="currentColor" stroke-width="([^"]+)"/g)].map(m => ({ d:m[1], w:+m[2] }));
    const circles = [...g.body.matchAll(/<circle cx="([^"]+)" cy="([^"]+)" r="([^"]+)"/g)].map(m => [+m[1], +m[2], +m[3]]);
    const fills = [...g.body.matchAll(/<path data-fill="1" d="([^"]+)"[^>]*stroke-width="([^"]+)"/g)].map(m => ({ d:m[1], sw:+m[2] }));
    const cm = g.clipId.match(/^c(-?\d+)_(n?)(\d+)$/);
    const clip = cm ? { top:+cm[1], bot:(cm[2] ? -1 : 1) * +cm[3] } : null;
    out[ch] = { paths, circles, fills, clip, sb0:g.sb0, sb1:g.sb1, w:g.w };
  }
  return out;
};
window.getKern = () => KERN;
window.getP = () => P;
