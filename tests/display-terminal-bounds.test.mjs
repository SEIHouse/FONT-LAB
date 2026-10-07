import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import vm from 'node:vm';
const root=new URL('../',import.meta.url);
const source=readFileSync(new URL('display/stroke_geometry.js',root),'utf8');
const before=source.replace(/            \/\/ A Bezier[\s\S]+?continue;\r?\n/,'');
assert.notEqual(source,before,'The reference must remove the entire bounds guard');
/** Compare against the original contact algorithm, with the same actual engine glyphs. */
test('terminal bounds rejection is string-identical for every encoded glyph and alternate at rest/max motion',()=>{
  const context=vm.createContext({window:{},document:{getElementById:()=>({insertAdjacentHTML(){}})}});
  vm.runInContext(readFileSync(new URL('engine.js',root),'utf8')+'\n'+readFileSync(new URL('export_tail.js',root),'utf8')+
    '\n'+source+'\nconst originalPenBody=(()=>{'+before+';return displayPenBody;})();',context);
  for(const slug of ['soft','edge','ink','wide']){
    const cut=JSON.parse(readFileSync(new URL(`display/cuts/${slug}.json`,root),'utf8'));
    for(const amount of [0,1]){
      const settings={...cut,weight:cut.weight*(1+.03*amount),slant:cut.slant+amount,penAngle:cut.penAngle+2*amount};
      context.cut=settings;
      const result=vm.runInContext(`(()=>{
        Object.assign(P,{base:cut.weight,ws:cut.letterWidth,xh:cut.xHeight,caprx:cut.capitalRoundness,round:cut.lowercaseRoundness,
          straight:cut.uprightStraightness,asc:cut.ascender,os:+cut.overshoot,ufoot:+cut.uFoot,ital:0,corner:cut.corners,cap:cut.ends,join:cut.joins,
          penAngle:cut.penAngle,obliqueAngle:cut.slant,trk:cut.spaceBetweenAllLetters,alternates:cut.alternates});
        P.contrast=displayContrast(cut.weight,cut.contrast,cut.xHeight,cut.ends);
        const names=[...new Set([...Object.keys(G),...Object.keys(window.exportAlternates(cut.weight))])];
        for(const name of names){
          const g=glyph(name,cut.weight),options={...cut,contrast:P.contrast};
          if(displayPenBody(g,options)!==originalPenBody(g,options)) return {mismatch:name};
        }
        return {glyphs:names.length};
      })()`,context);
      assert.equal(result.mismatch,undefined,`${slug} ${amount}: ${result.mismatch}`);
      assert.ok(result.glyphs>800,'Cover composed letters, combining marks and all numeric/stylistic alternates');
    }
  }
});
