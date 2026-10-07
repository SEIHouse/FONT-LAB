import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import vm from 'node:vm';
import {selectConfiguration} from '../display/living-media.mjs';
const root=new URL('../',import.meta.url);
const context=vm.createContext({DOMException,AbortController,setTimeout});
vm.runInContext(readFileSync(new URL('display/living.js',root),'utf8'),context);
const core=vm.runInContext('LivingTitles',context);
const profile={id:'test-v1',thickness:.03,slant:1,penAngle:2};
const cut={weight:100,slant:8,penAngle:32};
const axes={weight:true,slant:true,penAngle:true};
const engine={layout:()=>({width:100,glyphs:[{x:0}]}),frame:c=>({body:`<path d="M0 0L${c.weight} 1"/>`,defs:'',bounds:[0,0,c.weight,100]})};
const request=()=>({engine,cut,spacing:{},text:'AV',cpsp:false,profile,strength:1,axes,
  ...core.bpmEnvelope(120,4),yieldTask:async()=>{}});

test('silence rests and stereo antiphase retains channel energy',()=>{
  const silence=core.audioEnvelope([new Float32Array(96000)],48000,2);
  assert.ok(silence.every(x=>x===0));
  const a=Float32Array.from({length:96000},(_,i)=>.2*Math.sin(i*.03)),b=a.map(x=>-x);
  assert.deepEqual([...core.audioEnvelope([a,b],48000,2)],[...core.audioEnvelope([a,a],48000,2)]);
  assert.ok(core.audioEnvelope([a,b],48000,2)[30]>.35);
});
test('120 ms attack and 480 ms release handle steady energy and transients',()=>{
  const steady=core.audioEnvelope([new Float32Array(480000).fill(.2)],48000,10);
  assert.ok(Math.abs(steady[30]-.6)<.001);
  const transient=new Float32Array(480000);transient.fill(.3,48000,52800);
  const envelope=core.audioEnvelope([transient],48000,10);
  assert.ok(envelope[32]>envelope[30]);assert.ok(envelope[33]<envelope[32]);
  assert.ok(Math.abs(envelope[33]/envelope[32]-Math.exp(-1/30/.48))<1e-6);
});
test('BPM timing and both sampled loop boundaries rest, including fractional duration',()=>{
  const loop=core.bpmEnvelope(120,4);assert.equal(loop.duration,2);assert.equal(loop.values.length,60);
  assert.equal(loop.values[0],0);assert.equal(loop.values.at(-1),0);assert.ok(loop.values[23]>.98);
  const fractional=core.bpmEnvelope(137,4);assert.equal(fractional.values.length,Math.ceil(240/137*30));
  assert.throws(()=>core.bpmEnvelope(24,16),/1 and 10/);
});
test('axis switches and strength preserve starting values and never mutate the cut',()=>{
  assert.deepEqual({...core.motionCut(cut,profile,1,1,axes)},{weight:103,slant:9,penAngle:34});
  assert.deepEqual({...core.motionCut(cut,profile,1,0,axes)},cut);
  assert.deepEqual({...core.motionCut(cut,profile,1,1,{})},cut);
  assert.deepEqual(cut,{weight:100,slant:8,penAngle:32});
});
test('preparation is bounded, yielding, deterministic, anchored and cancellable',async()=>{
  let yielded=0;const first=await core.prepare({...request(),yieldTask:async()=>{yielded++;}});
  const second=await core.prepare(request());assert.deepEqual(first,second);assert.equal(yielded,15);
  assert.equal(first.layout.width,100);assert.equal(first.frames.length,60);
  assert.ok(first.viewBox[2]>182 && first.viewBox[2]<=183);assert.equal(core.frameAt(first,0),0);assert.equal(core.frameAt(first,2),59);
  const controller=new AbortController();
  await assert.rejects(core.prepare({...request(),signal:controller.signal,yieldTask:async()=>controller.abort()}),{name:'AbortError'});
  await assert.rejects(core.prepare({...request(),duration:11}),/bounded/);
});
test('SVG is script-free, namespaced, discrete and includes a static reduced-motion fallback',async()=>{
  const sequence=await core.prepare(request());sequence.text='<Title & music>';
  const svg=core.animatedSVG(sequence);assert.ok(!/<script|href=/.test(svg));
  assert.match(svg,/calcMode="discrete"/);assert.match(svg,/prefers-reduced-motion:reduce/);
  assert.match(svg,/<title>&lt;Title &amp; music&gt;<\/title>/);assert.match(svg,/class="rest"/);
  const size=core.dimensions(sequence,1080);assert.equal(Math.max(size.width,size.height),1080);
  assert.equal(size.width%2,0);assert.equal(size.height%2,0);
});
test('codec selection probes actual dimensions/audio and falls back without dropping audio',async()=>{
  const calls=[],audio={numberOfChannels:2,sampleRate:48000};
  const config=await selectConfiguration(1080,456,audio,{video:async(codec,options)=>{calls.push([codec,options]);return true;},audio:async codec=>codec==='opus'});
  assert.equal(config.extension,'webm');assert.equal(config.video,'vp9');assert.equal(config.audio,'opus');
  assert.equal(calls[0][1].width,1080);assert.equal(calls[0][1].height,456);assert.equal(calls[0][1].frameRate,30);
  assert.equal(await selectConfiguration(1920,808,null,{video:async()=>false,audio:async()=>true}),null);
});

/** Instantiate the same closure sources used by the Python page generator. */
function drawing(){
  const code=['engine.js','display/stroke_geometry.js','display/spacing.js','display/living-engine.js']
    .map(name=>readFileSync(new URL(name,root),'utf8')).join('\n');
  return vm.runInNewContext(`(function(){const livingDefs=[];const window={};const document={getElementById:()=>({insertAdjacentHTML:(_p,html)=>livingDefs.push(html)})};${code}})()`);
}
test('isolated real-engine instances retain compiled spacing, marks and identical repeated frames',()=>{
  const cut=JSON.parse(readFileSync(new URL('display/cuts/ink.json',root),'utf8'));
  const spacing=JSON.parse(readFileSync(new URL('display/spacing_ink.json',root),'utf8'));
  const a=drawing(),b=drawing(),layout=a.layout('LA AV a\u0301\u0308 Ж β',cut,spacing,true);
  const before=a.frame(cut,layout),moving=a.frame(core.motionCut(cut,profile,1,1,axes),layout);
  assert.notEqual(moving.body,before.body);assert.deepEqual(a.frame(cut,layout),before);
  assert.equal(JSON.stringify(b.frame(cut,layout)),JSON.stringify(before));assert.ok(!/NaN|Infinity/.test(moving.body));
  assert.ok(before.defs.includes('<clipPath'));
});
