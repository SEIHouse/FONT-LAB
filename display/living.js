/* Deterministic Living Title timelines and self-contained vector exports. */
const LivingTitles = (() => {
  const FPS = 30, MAX_SECONDS = 10;
  const clamp = (x,min,max) => Math.min(max,Math.max(min,x));
  const escape = value => String(value).replace(/[&<>"']/g,c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
  /** Ease both loop edges to the resting cut, including the last sampled frame. */
  function boundary(t,duration){
    const edge = Math.min(.48,duration/4), distance = Math.min(t,Math.max(0,duration-1/FPS-t));
    const q = clamp(distance/edge,0,1); return q*q*(3-2*q);
  }
  /** Sample a channel-aware RMS envelope without cancelling antiphase stereo. */
  function audioEnvelope(channels,sampleRate,duration){
    if(!channels.length || !Number.isFinite(sampleRate) || sampleRate <= 0) throw new Error('Invalid PCM audio');
    const count = Math.ceil(duration*FPS), values = [], step = 1/FPS;
    let previous = 0;
    for(let frame=0; frame<count; frame++){
      const start = Math.floor(frame*sampleRate/FPS), end = Math.floor(Math.min(duration,(frame+1)/FPS)*sampleRate);
      let sum = 0, samples = 0;
      for(const channel of channels) for(let i=start;i<Math.min(end,channel.length);i++){
        const value = channel[i]; if(!Number.isFinite(value)) throw new Error('Invalid PCM sample');
        sum += value*value; samples++;
      }
      const rms = samples ? Math.sqrt(sum/samples) : 0;
      const target = clamp(rms*3,0,1), tau = target > previous ? .12 : .48;
      previous += (target-previous)*(1-Math.exp(-step/tau));
      values.push(previous*boundary(frame/FPS,duration));
    }
    return values;
  }
  /** Use a half-cosine breath per beat; the clip seam always returns to rest. */
  function bpmEnvelope(bpm,beats){
    if(!Number.isFinite(bpm) || bpm < 24 || bpm > 240 || !Number.isInteger(beats) || beats < 1 || beats > 16)
      throw new Error('Use 24–240 BPM and 1–16 beats');
    const duration = beats*60/bpm;
    if(duration < 1 || duration > MAX_SECONDS) throw new Error('Choose a loop between 1 and 10 seconds');
    return {duration,values:Array.from({length:Math.ceil(duration*FPS)},(_,i) =>
      (.5-.5*Math.cos(2*Math.PI*i/FPS*bpm/60))*boundary(i/FPS,duration))};
  }
  /** Apply positive, versioned offsets; disabled axes keep their exact starting values. */
  function motionCut(cut,profile,energy,strength,axes){
    const amount = clamp(energy,0,1)*clamp(strength,0,1);
    return {...cut,weight:cut.weight*(1+(axes.weight ? profile.thickness*amount : 0)),
      slant:(cut.slant || 0)+(axes.slant ? profile.slant*amount : 0),
      penAngle:(cut.penAngle || 0)+(axes.penAngle ? profile.penAngle*amount : 0)};
  }
  /** Find a prepared frame by media time, including exact end/seek positions. */
  function frameAt(sequence,time){ return clamp(Math.floor(clamp(time,0,sequence.duration)*FPS),0,sequence.frames.length-1); }
  /** Prepare bounded geometry in yielding chunks; abort before publishing any sequence. */
  async function prepare({engine,cut,spacing,text,cpsp,profile,strength,axes,duration,values,signal,onProgress=()=>{},yieldTask=()=>new Promise(r=>setTimeout(r,0))}){
    if(!Number.isFinite(duration) || duration < 1 || duration > MAX_SECONDS || values.length !== Math.ceil(duration*FPS))
      throw new Error('Invalid bounded timeline');
    if(typeof text !== 'string' || text.length > 60 || !Number.isFinite(strength) ||
       values.some(value=>!Number.isFinite(value) || value<0 || value>1)) throw new Error('Invalid motion scene');
    if(!text.trim()) throw new Error('Enter a title to prepare motion');
    if(!spacing) throw new Error('Motion requires compiled spacing from a shipped cut');
    const check = () => { if(signal?.aborted) throw new DOMException('Preparation cancelled','AbortError'); };
    check();
    const layout = engine.layout(text,cut,spacing,cpsp), frames = [];
    let bounds = [Infinity,Infinity,-Infinity,-Infinity];
    for(let i=0;i<values.length;i++){
      check();
      const frame = engine.frame(motionCut(cut,profile,values[i],strength,axes),layout);
      frames.push({...frame,time:i/FPS,duration:Math.min(1/FPS,duration-i/FPS)});
      bounds = [Math.min(bounds[0],frame.bounds[0]),Math.min(bounds[1],frame.bounds[1]),Math.max(bounds[2],frame.bounds[2]),Math.max(bounds[3],frame.bounds[3])];
      if(i%4===3 || i===values.length-1){ onProgress((i+1)/values.length); await yieldTask(); }
    }
    check();
    const pad = 40;
    const viewBox = [bounds[0]-pad,bounds[1]-pad,bounds[2]-bounds[0]+2*pad,bounds[3]-bounds[1]+2*pad];
    return {frames,duration,fps:FPS,viewBox,layout,text,profile:profile.id};
  }
  /** Use even dimensions for encoders without moving/scaling frames during the loop. */
  function dimensions(sequence,longest=1080){
    if(![1080,1920].includes(longest)) throw new Error('Choose 1080 or 1920 pixels');
    const [, ,w,h] = sequence.viewBox, scale = longest/Math.max(w,h);
    return {width:Math.max(2,Math.round(w*scale/2)*2),height:Math.max(2,Math.round(h*scale/2)*2)};
  }
  /** Prefix every internal clip reference so standalone frames can coexist safely. */
  function artwork(frame,prefix){
    const rename = text => text.replace(/id="([^"]+)"/g,(_,id)=>`id="${prefix}${id}"`)
      .replace(/url\(#([^\)]+)\)/g,(_,id)=>`url(#${prefix}${id})`);
    return `<defs>${rename(frame.defs)}</defs>${rename(frame.body)}`;
  }
  /** The preview and encoder use this exact vector frame, with identical canvas bounds. */
  function frameSVG(sequence,index,ink='#eef1f6',longest=1080){
    if(!/^#[0-9a-f]{6}$/i.test(ink)) throw new Error('Invalid artwork color');
    const {width,height} = dimensions(sequence,longest);
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${sequence.viewBox.join(' ')}" width="${width}" height="${height}" color="${ink}" role="img"><title>${escape(sequence.text)}</title>${artwork(sequence.frames[index],'f-')}</svg>`;
  }
  /** Declarative discrete animation works in secure SVG image mode without scripts. */
  function animatedSVG(sequence,ink='#eef1f6',longest=1080){
    const rest = frameSVG(sequence,0,ink,longest), count = sequence.frames.length;
    const times = [...sequence.frames.map(f=>f.time/sequence.duration),1].join(';');
    const groups = sequence.frames.map((frame,index) => {
      const values = [...Array.from({length:count},(_,j)=>j===index ? 1 : 0),index===0 ? 1 : 0].join(';');
      return `<g opacity="${index===0 ? 1 : 0}">${artwork(frame,`f${index}-`)}<animate attributeName="opacity" values="${values}" keyTimes="${times}" calcMode="discrete" dur="${sequence.duration}s" repeatCount="indefinite"/></g>`;
    }).join('');
    return rest.replace(artwork(sequence.frames[0],'f-'),
      `<metadata>SEIHouse Living Titles ${escape(sequence.profile)}; ${sequence.fps} FPS; anchored spacing</metadata>`+
      '<style>.rest{display:none}@media(prefers-reduced-motion:reduce){.motion{display:none}.rest{display:inline}}</style>'+
      `<g class="rest">${artwork(sequence.frames[0],'rest-')}</g><g class="motion">${groups}</g>`);
  }
  return {FPS,MAX_SECONDS,audioEnvelope,bpmEnvelope,boundary,motionCut,frameAt,prepare,dimensions,artwork,frameSVG,animatedSVG};
})();
