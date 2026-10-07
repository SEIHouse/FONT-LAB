/* Appended inside a generated closure containing the unchanged shared engine. */
/** Configure an isolated instance; never touch the ordinary Lab's drawing state. */
function livingApply(cut){
  P.alternates = displayChoices(cut.alternates ?? {});
  Object.assign(P, {base:cut.weight, ws:cut.letterWidth, xh:cut.xHeight,
    contrast:displayContrast(cut.weight,cut.contrast,cut.xHeight,cut.ends), penAngle:cut.penAngle || 0,
    caprx:cut.capitalRoundness, round:cut.lowercaseRoundness, straight:cut.uprightStraightness || 1,
    corner:cut.corners === 'cut' ? 'cut' : 'soft', cap:cut.ends, join:cut.joins,
    os:cut.overshoot === false ? 0 : 1, ufoot:cut.uFoot ? 1 : 0, asc:cut.ascender || 700,
    ital:0, obliqueAngle:cut.slant || 0, trk:cut.spaceBetweenAllLetters});
  for(const key of Object.keys(cache)) delete cache[key];
  for(const key of Object.keys(clipDone)) delete clipDone[key];
  livingDefs.length = 0;
}
/** Freeze the shipped font's origins/advances/kern before any motion is applied. */
function livingLayout(text, cut, spacing, cpsp){
  livingApply(cut);
  const layout = titleLayout(text,cut,spacing,cpsp);
  return {width:layout.width, glyphs:layout.glyphs.map(({cluster,x}) => ({cluster,x}))};
}
/** Draw one frame with local glyph/clip caches and fixed compiled glyph positions. */
function livingFrame(cut, layout){
  livingApply(cut);
  const tangent = Math.tan((cut.slant || 0)*Math.PI/180);
  let body = '', bounds = [Infinity,Infinity,-Infinity,-Infinity];
  for(const {cluster,x} of layout.glyphs){
    const g = clusterGlyph(cluster,cut.weight);
    if(!g) continue;
    const origin = x-tangent*330;
    body += `<g transform="translate(${origin} 0)${tangent ? ` skewX(${-cut.slant})` : ''}"${cut.ends === 'flat' ? '' : ` clip-path="url(#${g.clipId})"`}>${displayPenBody(g,{...cut,contrast:P.contrast})}</g>`;
    const ink = inkBounds(g);
    if(!ink) continue;
    // Conservative pen/miter allowance also covers flat-cap contact overlaps.
    const margin = cut.weight*Math.max(1,P.contrast)+8;
    for(const bx of [ink[0]-margin,ink[2]+margin]) for(const by of [ink[1]-margin,ink[3]+margin]){
      const xx = origin+bx+tangent*by, yy = -by;
      bounds = [Math.min(bounds[0],xx),Math.min(bounds[1],yy),Math.max(bounds[2],xx),Math.max(bounds[3],yy)];
    }
  }
  if(!body) bounds = [0,-700,Math.max(layout.width,100),0];
  return {body,defs:livingDefs.join(''),bounds};
}
return {layout:livingLayout, frame:livingFrame};
