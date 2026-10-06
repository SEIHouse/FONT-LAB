import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import vm from 'node:vm';

const root = new URL('../',import.meta.url);
const context = vm.createContext({document:{getElementById:()=>({insertAdjacentHTML(){}})}});
context.window=context;
vm.runInContext(readFileSync(new URL('engine.js',root),'utf8')+'\n'+
  readFileSync(new URL('display/spacing.js',root),'utf8'),context);
const evaluate = expression => JSON.parse(vm.runInContext(`JSON.stringify(${expression})`,context));

test('explicit zero masks later class subtables; separate kern lookups add',()=>{
  assert.equal(evaluate(`titleKerning({kern:[[
    {format:1,pairs:{A:{V:0}}},
    {format:2,coverage:['A'],left:{A:1},right:{V:1},values:[[0,0],[0,-100]]}
  ],[{format:1,pairs:{A:{V:12}}}]]},'A','V')`),12);
});

test('renaming keeps final spacing; geometry, missing fields and nested spacing edits invalidate it',()=>{
  assert.equal(evaluate(`!!spacingForCut({name:'Renamed',weight:150,letterSpace:{A:{before:3,after:4}}},
    [{settings:{weight:150,letterSpace:{A:{after:4,before:3}}}}])`),true);
  for(const cut of ["{weight:151,letterSpace:{A:{before:3,after:4}}}",
                    "{letterSpace:{A:{before:3,after:4}}}",
                    "{weight:150,letterSpace:{A:{before:9,after:4}}}",
                    `{weight:150,letterSpace:{A:'{"after":4,"before":3}'}}`]){
    assert.equal(evaluate(`spacingForCut(${cut},[{settings:{weight:150,letterSpace:{A:{before:3,after:4}}}}])`),null);
  }
});

test('Lab uses rounded compiled metrics and glyph kerning, including cpsp placements',()=>{
  const spacing = {glyphs:{A:{name:'A',advance:700,origin:12},V:{name:'V',advance:650,origin:12}},
    capitals:['A','V'],capitalSpace:20,kern:[[{format:1,pairs:{A:{V:-100}}}]]};
  const result=evaluate(`titleLayout('AV',{weight:150,spaceBetweenAllLetters:100},${JSON.stringify(spacing)},true)`);
  assert.equal(result.width,1290);
  assert.deepEqual(result.glyphs.map(g=>g.x),[22,642]);
});

test('composition precedes fi/fl joining and preserves ligature mark components',()=>{
  assert.deepEqual(evaluate(`titleClusters('fi\u0301').map(c=>c.base)`),['f','í']);
  assert.deepEqual(evaluate(`titleClusters('Office Reflection').map(c=>c.base)`),
    ['O','f','ﬁ','c','e',' ','R','e','ﬂ','e','c','t','i','o','n']);
  assert.deepEqual(evaluate(`titleClusters('fl\u030B')`),[{base:'ﬂ',marks:['\u030b'],component:1}]);
});
