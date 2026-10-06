import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import vm from 'node:vm';

const root=new URL('../',import.meta.url);
/** Evaluate the shared engine with isolated caches and the selected cut's settings. */
function engine(cut){
  const context=vm.createContext({document:{getElementById:()=>({insertAdjacentHTML(){}})}});
  context.window=context;
  vm.runInContext(readFileSync(new URL('engine.js',root),'utf8')+'\n'+readFileSync(new URL('export_tail.js',root),'utf8'),context);
  const values={base:cut.weight,xh:cut.xHeight,ws:cut.letterWidth,caprx:cut.capitalRoundness,
    round:cut.lowercaseRoundness,straight:cut.uprightStraightness,asc:cut.ascender,
    ufoot:+cut.uFoot,os:+cut.overshoot,ital:0,corner:cut.corners,cap:cut.ends,join:cut.joins,
    penAngle:cut.penAngle,trk:cut.spaceBetweenAllLetters,alternates:cut.alternates};
  vm.runInContext(`Object.assign(P,${JSON.stringify(values)});P.contrast=displayContrast(${cut.weight},${cut.contrast},${cut.xHeight},${JSON.stringify(cut.ends)})`,context);
  return expression=>vm.runInContext(expression,context);
}

test('every cut exports distinct, cached alternatives including accents and small figures',()=>{
  for(const slug of ['soft','edge','ink','wide']){
    const cut=JSON.parse(readFileSync(new URL(`display/cuts/${slug}.json`,root),'utf8'));
    const evaluate=engine(cut);
    const manifest=JSON.parse(evaluate('JSON.stringify(displayManifest())'));
    assert.deepEqual([...new Set(Object.values(manifest).map(spec=>spec.tag))].sort(),
      ['ss01','ss02','ss03','ss04','ss05','ss06','ss07','ss08']);
    for(const [source,spec] of Object.entries(manifest)){
      const alternate=Object.entries(spec.choices).find(([choice])=>choice!==spec.default)[1];
      assert.match(alternate,/^[A-Za-z][A-Za-z0-9_.]*$/,'PostScript glyph name');
      assert.ok(alternate.length<=63,'PostScript glyph name length');
      const current=evaluate(`glyph(${JSON.stringify(source)},${cut.weight}).body`);
      const other=evaluate(`glyph(${JSON.stringify(alternate)},${cut.weight}).body`);
      assert.notEqual(current,other,slug+' '+source);
      assert.ok(!/NaN|Infinity|undefined/.test(other),alternate);
      assert.equal(evaluate(`glyph(${JSON.stringify(source)},${cut.weight}).body`),current,'forced alternate restores settings');
    }
    for(const source of ['ấ','ą','ģ','Ќ','four.tf','⁶','₉','¼']) assert.ok(manifest[source],source);
  }
});

test('choices invalidate cached forms and legacy drafts resolve to the original upright designs',()=>{
  const cut=JSON.parse(readFileSync(new URL('display/cuts/soft.json',root),'utf8'));
  const evaluate=engine(cut), original=evaluate('glyph("a",150).body');
  evaluate('P.alternates.a="double"');
  assert.notEqual(evaluate('glyph("a",150).body'),original);
  evaluate('P.alternates.a="single"');
  assert.equal(evaluate('glyph("a",150).body'),original);
  assert.equal(evaluate('displayChoices({}).a'),'double');
  assert.equal(evaluate('displayChoices({}).g'),'single');
  assert.throws(()=>evaluate('displayChoices({a:"broken"})'),/Invalid alternate/);
  for(const key of evaluate('DISPLAY_SETS.map(set=>set.key)')){
    assert.throws(()=>evaluate(`displayChoices({${JSON.stringify(key)}:null})`),/Invalid alternate/);
  }
  assert.throws(()=>evaluate('displayChoices({a:undefined})'),/Invalid alternate/);
  assert.throws(()=>evaluate('displayChoices({unknown:"single"})'),/Unknown alternate/);
});
