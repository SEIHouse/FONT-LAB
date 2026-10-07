import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {cuts,createTitleScene,poseIndex,renderTitleSVG,createBpmSource,smoothEnergy,exportAnimatedSVG} from '../packages/living-titles/dist/index.js';

test('headless import and all four reviewed cuts produce deterministic anchored scenes',async()=>{
  assert.deepEqual(cuts.map(c=>c.name),['Soft','Edge','Ink','Wide']);
  for(const {name} of cuts){
    const first=await createTitleScene({title:'SEA & SEN',cut:name});
    const second=await createTitleScene({title:'SEA & SEN',cut:name});
    assert.equal(first.frames.length,60);assert.deepEqual(first,second);
    assert.equal(renderTitleSVG(first,0),renderTitleSVG(second,0));
    assert.notEqual(first.frames[0].body,first.frames[59].body);
    assert.ok(first.advance>0);assert.ok(first.viewBox[2]>0);
    assert.match(renderTitleSVG(first,1),/<title>SEA &amp; SEN<\/title>/);
    assert.ok(Object.isFrozen(first));assert.ok(Object.isFrozen(first.frames));
    assert.throws(()=>{first.frames[0].bounds[0]=0;},TypeError);
  }
});
test('disabled axes and zero strength preserve resting geometry',async()=>{
  for(const options of [{strength:0},{axes:{weight:false,slant:false,penAngle:false}}]){
    const scene=await createTitleScene({title:'SEN',...options});
    assert.equal(scene.frames[0].body,scene.frames[59].body);
  }
  const partial=await createTitleScene({title:'SEN',axes:{weight:false}});
  assert.deepEqual(partial.axes,{weight:false,slant:true,penAngle:true});
});
test('bounded preparation validates options and cancels without publishing a scene',async()=>{
  for(const options of [{title:''},{title:'x'.repeat(61)},{title:'SEA',cut:'Draft'},
    {title:'SEA',strength:1.1},{title:'SEA',axes:{slant:1}},{title:'SEA',capitalSpacing:1}])
    await assert.rejects(createTitleScene(options));
  const controller=new AbortController();
  await assert.rejects(createTitleScene({title:'SEA',signal:controller.signal,onProgress:()=>controller.abort()}),{name:'AbortError'});
});
test('safe SVG colors and identifiers; callers can isolate clip definitions',async()=>{
  const scene=await createTitleScene({title:'SEA'});
  const one=renderTitleSVG(scene,1,{idPrefix:'first'}),two=renderTitleSVG(scene,1,{idPrefix:'second'});
  assert.match(one,/id="first-/);assert.match(two,/url\(#second-/);
  assert.throws(()=>renderTitleSVG(scene,0,{idPrefix:'bad" onload="x'}));
  assert.throws(()=>renderTitleSVG(scene,0,{color:'red"'}));
  assert.throws(()=>renderTitleSVG({...scene},0));
  assert.equal(poseIndex(scene,NaN),0);assert.equal(poseIndex(scene,10),59);
  const svg=exportAnimatedSVG(scene,{bpm:120});assert.match(svg,/<animate /);assert.match(svg,/prefers-reduced-motion/);
  assert.ok(!svg.includes('<script'));assert.throws(()=>exportAnimatedSVG(scene,{color:'url(x)'}));
});
test('external smoothing and silent clock sources retain the existing response',()=>{
  assert.ok(Math.abs(smoothEnergy(0,1,.12)-(1-Math.exp(-1)))<1e-12);
  assert.ok(Math.abs(smoothEnergy(1,0,.48)-Math.exp(-1))<1e-12);
  assert.throws(()=>smoothEnergy(0,1,-1));
  const source=createBpmSource({bpm:120});assert.equal(source.duration,2);
  assert.equal(source.sample(0),0);assert.equal(source.sample(2),0);
  assert.equal(source.sample(NaN),0);assert.equal(source.sample(-.5),source.sample(1.5));
});
test('private runtime artifact ships only expected public runtime/font files',()=>{
  const release=JSON.parse(readFileSync(new URL('../packages/living-titles/releases/release.json',import.meta.url)));
  const bytes=readFileSync(new URL(`../packages/living-titles/releases/${release.filename}`,import.meta.url));
  assert.equal(createHash('sha256').update(bytes).digest('hex'),release.sha256);
  const mandatory=['dist/index.js','dist/index.d.ts','dist/react.js','dist/react.d.ts','dist/player.js','dist/engine.js','dist/fonts.css','NOTICE.txt','SANS-LICENSE.txt'];
  for(const name of mandatory)assert.ok(release.files.includes(name),name);
  assert.equal(release.files.filter(f=>f.endsWith('.woff2')).length,4);
  assert.ok(release.files.every(f=>!/(mock|mediabunny|living-media|src\/|tests\/)/.test(f)));
  const manifest=JSON.parse(readFileSync(new URL('../packages/living-titles/package.json',import.meta.url)));
  assert.equal(manifest.dependencies,undefined);assert.equal(manifest.private,true);
  assert.equal(manifest.peerDependenciesMeta.react.optional,true);
});
