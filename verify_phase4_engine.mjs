// Compare real engine output with the previous committed language step.
// node verify_phase4_engine.mjs [BASELINE_COMMIT]
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {beforeReadingCurves, beforeSymbols043} from './tests/reader-curve-scope.mjs';
const root=dirname(fileURLToPath(import.meta.url));
const release=JSON.parse(fs.readFileSync(join(root,'phase4.json'),'utf8'));
const baseline=process.argv[2] || release.previous_step_commit || release.baseline_commit;
const setup=source=>{
 const ctx=vm.createContext({window:{},document:{getElementById:()=>({insertAdjacentHTML(){}})}});
 vm.runInContext(source,ctx);
 return ctx;
};
const beforeSource=execFileSync('git',['show',`${baseline}:engine.js`],{cwd:root,encoding:'utf8'});
const before=setup(beforeSource);
const afterSource=fs.readFileSync(join(root,'engine.js'),'utf8');
const after=setup(afterSource);
const preSymbols=setup(beforeSymbols043(afterSource));
const preserved=setup(beforeReadingCurves(afterSource));
const norm=s=>s.replace(/\r\n/g,'\n');
const target=norm(beforeSource)===norm(beforeReadingCurves(beforeSource))?preserved:norm(beforeSource)===norm(beforeSymbols043(beforeSource))?preSymbols:after;
const oldChars=vm.runInContext('[...Object.keys(G),...Object.keys(DOTLESS),...Object.keys(LANGUAGE_ALTERNATES),...Object.keys(NUMERIC_VARIANTS)]',before);
let count=0;
for(const weight of [70,85,100,115,140]){
 for(const italic of [0,1]) for(const contrast of [1,1.12,1.4]){
  const values={base:weight,ital:italic,contrast,round:0.55,xh:510,caprx:245,ws:0.95,os:1,ufoot:0,straight:0.82,asc:700,trk:2.8};
  for(const ctx of [before,after,preSymbols,preserved]){
   ctx.values=values;
   vm.runInContext('Object.assign(P,values)',ctx);
  }
  for(const ch of oldChars){
   for(const ctx of [before,after,preSymbols,preserved]){
    ctx.ch=ch;ctx.weight=weight;
   }
   const snapshot=ctx=>vm.runInContext('(()=>{const g=glyph(ch,weight);return JSON.stringify([g.body,g.w,g.sb0,g.sb1]);})()',ctx);
   const label=[ch,weight,italic,contrast].join(' ');
   assert.equal(snapshot(target),snapshot(before),label);
   assert.deepEqual(JSON.parse(snapshot(after)).slice(1),JSON.parse(snapshot(before)).slice(1),label+' metrics');count++;
  }
  after.weight=weight;
  vm.runInContext("for(const ch of VIETNAMESE_ADDED){ const parent=latinBase(ch),g=glyph(ch,weight),base=glyph(parent,weight); if(g.w!==base.w || g.sb0!==base.sb0 || g.sb1!==base.sb1) throw new Error('New letter advance changed: '+ch); }",after);
 }
}

vm.runInContext("Object.assign(P,{base:85,ital:0,contrast:1.12})",after);
after.testWord="Ố";
assert(vm.runInContext('word(testWord,20,false)',after).includes('overflow="visible"'));
after.testWord="O\u0302\u0301";
assert(vm.runInContext('word(testWord,20,false)',after).includes('overflow="visible"'));
after.testWord="Lian";
assert(!vm.runInContext('word(testWord,20,false)',after).includes('overflow="visible"'));
console.log(count+' historical SVG cases preserved outside the three refined drawings; all advances and tall NFC/NFD overflow pass.');
