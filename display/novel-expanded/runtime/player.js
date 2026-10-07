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

  /** Validate the caller-owned sampler without opening or changing its audio. */
  function validateSource(value) {if(!value || typeof value.sample !== 'function') throw new TypeError('Motion source needs sample(seconds).');}
  /** Sample safe normalized energy, returning rest for errors or reduced motion. */
  function energy() {
    if(reduced.matches) return 0;
    try {const value=source.sample(elapsed);return Number.isFinite(value) ? Math.max(0,Math.min(1,value)) : 0;} catch {return 0;}
  }
  /** Replace only the owned artwork host and isolate every internal clip ID. */
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
  /** Advance visible playback and paint at most thirty times per second. */
  function tick(now) {
    raf=0;
    if(disposed || !playing || doc.hidden) {lastTime=null;return;}
    if(reduced.matches) {draw(true);lastTime=null;return;}
    if(lastTime !== null) elapsed+=(now-lastTime)/1000;
    lastTime=now;if(now-lastPaint >= 1000/30){draw();lastPaint=now;}raf=view.requestAnimationFrame(tick);
  }
  /** Reset the clock anchor before starting or suspending the animation request. */
  function schedule() {
    view.cancelAnimationFrame(raf);raf=0;lastTime=null;lastPaint=-Infinity;
    if(!disposed && playing && !doc.hidden && !reduced.matches) raf=view.requestAnimationFrame(tick);
  }
  /** Prevent mutation after ownership of the host has been released. */
  function check() {if(disposed) throw new Error('The title player has been disposed.');}
  /** Apply system motion changes even when the player is paused. */
  function onReduced() {draw(true);schedule();}
  /** Resume from a fresh anchor so hidden time never advances the visual clock. */
  function onVisibility() {schedule();}
  /** Stop the pending request while the page enters its history cache. */
  function onHide() {view.cancelAnimationFrame(raf);raf=0;lastTime=null;}
  doc.addEventListener('visibilitychange',onVisibility);
  reduced.addEventListener('change',onReduced);
  view.addEventListener('pagehide',onHide);view.addEventListener('pageshow',onVisibility);
  draw(true);schedule();

  return Object.freeze({
    /** Resume the visual clock without changing the source's audio transport. */
    play(){check();playing=true;schedule();},
    /** Freeze elapsed visual time while continuing to observe motion preferences. */
    pause(){check();playing=false;schedule();},
    /** Select a nonnegative visual timestamp and render its pose immediately. */
    seek(seconds){check();if(!Number.isFinite(seconds) || seconds<0) throw new RangeError('Use a nonnegative time.');elapsed=seconds;draw(true);schedule();},
    /** Replace prepared geometry after validation and reset its visual clock. */
    setScene(next){check();renderTitleSVG(next,0,{color,idPrefix:prefix});scene=next;elapsed=0;lastIndex=-1;draw(true);schedule();},
    /** Replace the caller-owned sampler and start its visual time at zero. */
    setSource(next){check();validateSource(next);source=next;elapsed=0;draw(true);schedule();},
    /** Repaint with a validated six-digit color without preparing new geometry. */
    setColor(next){check();renderTitleSVG(scene,0,{color:next,idPrefix:prefix});color=next;draw(true);},
    /** Refresh the current pose, useful for paused externally sampled input. */
    render(){check();draw(true);},
    /** Report immutable playback state without exposing mutable rendering caches. */
    getState:()=>Object.freeze({playing,disposed,elapsed,energy:disposed ? 0 : energy(),pose:lastIndex,reducedMotion:reduced.matches}),
    /** Idempotently release callbacks, artwork, source and host accessibility ownership. */
    dispose(){if(disposed) return;disposed=true;view.cancelAnimationFrame(raf);raf=0;
      doc.removeEventListener('visibilitychange',onVisibility);reduced.removeEventListener('change',onReduced);
      view.removeEventListener('pagehide',onHide);view.removeEventListener('pageshow',onVisibility);
      element.replaceChildren();for(const [name,value] of previousAttributes) {if(value===null) element.removeAttribute(name);else element.setAttribute(name,value);}
      source=null;scene=null;
    },
  });
}
