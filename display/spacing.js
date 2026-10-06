/** Resolve the compiled cut's GPOS classes and rounded hmtx advances for SVG titles. */
function spacingForCut(cut, exports){
  if(typeof displayChoices==='function'){
    try { displayChoices(cut.alternates === undefined ? {} : cut.alternates); } catch { return null; }
  }
  const stable = value => value && typeof value === 'object'
    ? (Array.isArray(value) ? value.map(stable)
      : Object.fromEntries(Object.keys(value).sort().map(key => [key, stable(value[key])]))) : value;
  return exports.find(record => Object.entries(record.settings).every(([key, value]) =>
    JSON.stringify(stable(cut[key])) === JSON.stringify(stable(value)))) || null;
}

/** A zero pair blocks subsequent subtables in that lookup; separate lookups add. */
function titleKerning(spacing, first, second){
  let advance = 0;
  for(const lookup of spacing.kern){
    for(const table of lookup){
      if(table.format === 1){
        const value = table.pairs[first]?.[second];
        if(value === undefined) continue;
        advance += value; break;
      }
      if(table.coverage.includes(first)){
        advance += table.values[table.left[first] || 0][table.right[second] || 0];
        break;
      }
    }
  }
  return advance;
}

/** Compose marks before standard fi/fl ligatures, matching the font's feature order. */
function titleClusters(text){
  const source = languageClusters(text), result = [];
  for(let i=0; i<source.length; i++){
    const current = source[i], next = source[i+1];
    if(current.base === 'f' && !current.marks.length && next && ['i','l'].includes(next.base)){
      result.push({base:next.base === 'i' ? 'ﬁ' : 'ﬂ', marks:next.marks, component:1}); i++;
    } else result.push(current);
  }
  return result;
}

/** Position title clusters with compiled spacing, or the labeled live draft fallback. */
function titleLayout(text, cut, spacing, capitalSpacing=false){
  let width = 0, previous = '', glyphs = [];
  for(const cluster of titleClusters(text)){
    const ch = cluster.base, g = clusterGlyph(cluster, cut.weight);
    const variant = spacing?.variants?.[ch];
    const name = variant?.choices[cut.alternates?.[variant.key] ?? variant.default];
    const metric = variant && name && name!==spacing.glyphs[ch]?.name
      ? spacing.glyphs[name] : spacing?.glyphs[ch];
    const capital = capitalSpacing && metric && spacing.capitals.includes(metric.name)
      ? spacing.capitalSpace : 0;
    if(metric){
      width += titleKerning(spacing, previous, metric.name);
      if(g) glyphs.push({cluster, g, x:width+metric.origin+capital/2});
      width += metric.advance+capital; previous = metric.name;
    } else {
      // Edited/unbuilt drafts retain a live drawing; the Lab labels this approximation.
      if(!g){ width += ch === ' ' ? cut.wordSpace : 300; previous=''; continue; }
      if(ch === '\u2009' || ch === '\u202f'){ width += 120; previous=''; continue; }
      width += KERN[latinBase(previous)+latinBase(ch)] || 0;
      glyphs.push({cluster, g, x:width+cut.spaceBetweenAllLetters+g.sb0});
      width += 2*cut.spaceBetweenAllLetters+g.sb0+g.w+cut.weight+g.sb1;
      previous = ch;
    }
  }
  return {width, glyphs};
}
