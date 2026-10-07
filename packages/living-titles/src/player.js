import { createBpmSource, poseIndex, renderTitleSVG } from './index.js';
let nextId=0;

/** Browser-only mount. It observes motion and never creates an audio transport. */
export function createTitlePlayer(element,scene,{source=createBpmSource(),color='#e6cc87',autoplay=true}={}) {
  if(!element || element.nodeType !== 1) throw new TypeError('Provide a DOM element.');
  const doc=element.ownerDocument,view=doc.defaultView;
  if(!view) throw new Error('The title player requires a browser document.');
  const prefix=`seihouse-living-${++nextId}`;
  let playing=Boolean(autoplay),disposed=false,raf=0,elapsed=0,lastTime=null,lastIndex=-1,lastPaint=-Infinity;
  const previousAttributes=['role','aria-label'].map(name=>[name,element.getAttribute(name)]);
  // Render and validate before attaching lifecycle listeners or replacing the host.
  validateSource(source); renderTitleSVG(scene,0,{color,idPrefix:prefix});
  const reduced=view.matchMedia('(prefers-reduced-motion: reduce)');

  function validateSource(value) {if(!value || typeof value.sample !== 'function') throw new TypeError('Motion source needs sample(seconds).');}
  function energy() {
    if(reduced.matches) return 0;
    try {const value=source.sample(elapsed);return Number.isFinite(value) ? Math.max(0,Math.min(1,value)) : 0;} catch {return 0;}
  }
  function draw(force=false) {
    if(disposed) return;
    const value=energy(),index=poseIndex(scene,value);
    if(!force && index === lastIndex) return;
    lastIndex=index;
    element.innerHTML=renderTitleSVG(scene,value,{color,idPrefix:prefix});
    const svg=element.firstElementChild;
    svg.removeAttribute('role');svg.setAttribute('aria-hidden','true');svg.setAttribute('focusable','false');
    svg.setAttribute('width','100%');svg.setAttribute('height','100%');svg.style.display='block';
    element.setAttribute('role','img');element.setAttribute('aria-label',scene.title);
  }
  function tick(now) {
    raf=0;
    if(disposed || !playing || doc.hidden) {lastTime=null;return;}
    if(reduced.matches) {draw(true);lastTime=null;return;}
    if(lastTime !== null) elapsed+=(now-lastTime)/1000;
    lastTime=now;if(now-lastPaint >= 1000/30){draw();lastPaint=now;}raf=view.requestAnimationFrame(tick);
  }
  function schedule() {
    view.cancelAnimationFrame(raf);raf=0;lastTime=null;lastPaint=-Infinity;
    if(!disposed && playing && !doc.hidden && !reduced.matches) raf=view.requestAnimationFrame(tick);
  }
  function check() {if(disposed) throw new Error('The title player has been disposed.');}
  function onReduced() {draw(true);schedule();}
  function onVisibility() {schedule();}
  function onHide() {view.cancelAnimationFrame(raf);raf=0;lastTime=null;}
  doc.addEventListener('visibilitychange',onVisibility);
  reduced.addEventListener('change',onReduced);
  view.addEventListener('pagehide',onHide);view.addEventListener('pageshow',onVisibility);
  draw(true);schedule();

  return Object.freeze({
    play(){check();playing=true;schedule();},
    pause(){check();playing=false;schedule();},
    seek(seconds){check();if(!Number.isFinite(seconds) || seconds<0) throw new RangeError('Use a nonnegative time.');elapsed=seconds;draw(true);schedule();},
    setScene(next){check();renderTitleSVG(next,0,{color,idPrefix:prefix});scene=next;elapsed=0;lastIndex=-1;draw(true);schedule();},
    setSource(next){check();validateSource(next);source=next;elapsed=0;draw(true);schedule();},
    setColor(next){check();renderTitleSVG(scene,0,{color:next,idPrefix:prefix});color=next;draw(true);},
    render(){check();draw(true);},
    getState:()=>Object.freeze({playing,disposed,elapsed,energy:disposed ? 0 : energy(),pose:lastIndex,reducedMotion:reduced.matches}),
    dispose(){if(disposed) return;disposed=true;view.cancelAnimationFrame(raf);raf=0;
      doc.removeEventListener('visibilitychange',onVisibility);reduced.removeEventListener('change',onReduced);
      view.removeEventListener('pagehide',onHide);view.removeEventListener('pageshow',onVisibility);
      element.replaceChildren();for(const [name,value] of previousAttributes) {if(value===null) element.removeAttribute(name);else element.setAttribute(name,value);}
      source=null;scene=null;
    },
  });
}
