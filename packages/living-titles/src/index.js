import { createLivingEngine, LivingTitles, DATA } from './engine.js';
export { createTitlePlayer } from './player.js';

export const cuts = Object.freeze(DATA.cuts.map(c => Object.freeze({name:c.name,note:c.note})));
const clamp = value => Number.isFinite(value) ? Math.max(0,Math.min(1,value)) : 0;
const colorPattern = /^#[0-9a-f]{6}$/i;
const scenes = new WeakSet();

/** Prepare the reviewed energy range once; an audio owner can select poses later. */
export async function createTitleScene({title,cut='Soft',strength=.7,capitalSpacing=true,
  axes={weight:true,slant:true,penAngle:true},signal,onProgress}={}) {
  if(typeof title !== 'string' || !title.trim() || title.length > 60) throw new TypeError('Use a nonempty title of at most 60 UTF-16 code units.');
  if(!Number.isFinite(strength) || strength < 0 || strength > 1) throw new RangeError('Strength must be between 0 and 1.');
  if(typeof capitalSpacing !== 'boolean' || !axes || typeof axes !== 'object' ||
    Object.keys(axes).some(k=>!['weight','slant','penAngle'].includes(k) || typeof axes[k] !== 'boolean')) throw new TypeError('Invalid spacing or motion axes.');
  const index = DATA.cuts.findIndex(c=>c.name === cut);
  if(index < 0) throw new RangeError('Choose Soft, Edge, Ink or Wide.');
  const profile = DATA.profiles.find(p=>p.cut === cut && p.certified);
  if(!profile) throw new Error('This cut does not have current motion certification.');
  const engine = createLivingEngine();
  const enabled={weight:axes.weight ?? true,slant:axes.slant ?? true,penAngle:axes.penAngle ?? true};
  const sequence = await LivingTitles.prepare({engine,cut:DATA.cuts[index],spacing:DATA.spacing[index],
    text:title,cpsp:capitalSpacing,profile,strength,axes:enabled,signal,onProgress,duration:2,
    values:Array.from({length:60},(_,i)=>i/59)});
  for(const frame of sequence.frames) {Object.freeze(frame.bounds);Object.freeze(frame);}
  Object.freeze(sequence.frames);Object.freeze(sequence.viewBox);
  // Do not expose mutable glyph clusters or the generated engine's caches.
  const scene = Object.freeze({title,cut,profile:profile.id,strength,capitalSpacing,
    axes:Object.freeze(enabled),viewBox:sequence.viewBox,advance:sequence.layout.width,
    frames:sequence.frames});
  scenes.add(scene);
  return scene;
}

function validateScene(scene) {if(!scenes.has(scene)) throw new TypeError('Use a scene created by this package instance.');}
export function poseIndex(scene,energy) {validateScene(scene);return Math.round(clamp(energy)*(scene.frames.length-1));}

/** Deterministic vectors. Provide a distinct prefix when embedding multiple inline SVGs. */
export function renderTitleSVG(scene,energy=0,{color='#e6cc87',idPrefix='living-title',longestEdge=1080}={}) {
  validateScene(scene);
  if(!colorPattern.test(color)) throw new TypeError('Use a six-digit hex color.');
  if(typeof idPrefix !== 'string' || !/^[A-Za-z][A-Za-z0-9_-]*$/.test(idPrefix)) throw new TypeError('Invalid SVG identifier prefix.');
  const sequence={viewBox:scene.viewBox,frames:scene.frames,text:scene.title};
  const svg=LivingTitles.frameSVG(sequence,poseIndex(scene,energy),color,longestEdge);
  return svg.replace(/id="f-([^"]+)"/g,(_,id)=>`id="${idPrefix}-${id}"`)
    .replace(/url\(#f-([^\)]+)\)/g,(_,id)=>`url(#${idPrefix}-${id})`);
}

/** Silent source for previews. The caller supplies the elapsed playback clock. */
export function createBpmSource({bpm=60,beats=4}={}) {
  const envelope=LivingTitles.bpmEnvelope(bpm,beats);
  return Object.freeze({duration:envelope.duration,sample(seconds){
    if(!Number.isFinite(seconds)) return 0;
    const time=((seconds%envelope.duration)+envelope.duration)%envelope.duration;
    return envelope.values[LivingTitles.frameAt({duration:envelope.duration,frames:envelope.values},time)];
  }});
}

/** Channel analysis stays with audio owners; this utility smooths normalized energy. */
export function smoothEnergy(previous,input,deltaSeconds) {
  if(!Number.isFinite(deltaSeconds) || deltaSeconds < 0) throw new RangeError('Use a nonnegative elapsed time.');
  const from=clamp(previous),to=clamp(input),tau=to > from ? .12 : .48;
  return from+(to-from)*(1-Math.exp(-deltaSeconds/tau));
}

export function exportAnimatedSVG(scene,{bpm=60,beats=4,color='#e6cc87',longestEdge=1080}={}) {
  validateScene(scene);
  const {duration,values}=LivingTitles.bpmEnvelope(bpm,beats);
  const sequence={viewBox:scene.viewBox,text:scene.title,profile:scene.profile,fps:30,duration,
    frames:values.map((energy,i)=>({...scene.frames[poseIndex(scene,energy)],time:i/30,
      duration:Math.min(1/30,duration-i/30)}))};
  return LivingTitles.animatedSVG(sequence,color,longestEdge);
}
