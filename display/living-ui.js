/* Display Lab authoring only; motion settings never enter CUT or draft persistence. */
const LivingTitleUI = (() => {
  const byId = id => document.getElementById('lt-'+id);
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const engine = createLivingEngine();
  let sceneKey='',scene=null,profile=null,sequence=null,audio=null,file=null,metadata=null;
  let job=null,busy=false,mediaPromise=null,playing=false,position=0,clockStart=0,raf=0;
  let context=null,source=null,configuration=null,probeVersion=0,lastFrame=-1,seekResume=false;
  let playVersion=0;
  /** Lazy-load the local bundle only for audio/video work; retries remain possible. */
  function media(){
    if(!mediaPromise) mediaPromise = new Promise((resolve,reject)=>{
      if(typeof LivingMedia !== 'undefined'){ resolve(LivingMedia); return; }
      const script=document.createElement('script');script.src=LIVING_MEDIA_URL;
      script.onload=()=>{
        if(typeof LivingMedia==='undefined'){script.remove();mediaPromise=null;reject(new Error('The local media bundle did not initialize. Rebuild the Lab media assets.'));}
        else resolve(LivingMedia);
      };
      script.onerror=()=>{script.remove();mediaPromise=null;reject(new Error('Could not load the local media bundle. Serve the complete Lab folder over HTTP/HTTPS.'));};
      document.head.append(script);
    });
    return mediaPromise;
  }
  /** Release the current source; retain only the bounded prepared clip for seeking. */
  function stopSound(){
    if(source){source.onended=null;try{source.stop();}catch{}source.disconnect();source=null;}
  }
  function time(){
    if(!playing || !sequence) return position;
    const now = audio && context ? context.currentTime : performance.now()/1000;
    return (position+Math.max(0,now-clockStart))%sequence.duration;
  }
  /** Pause synchronously so edits/seeks cannot leave stale scheduled audio playing. */
  function pause(){
    playVersion++;
    position=time();playing=false;cancelAnimationFrame(raf);stopSound();
    if(context?.state==='running') void context.suspend();
    controls();show();
  }
  /** Paint only prepared vectors; animation does not trigger the static proof renderer. */
  function show(t=position){
    if(!sequence) return;
    const index = reduce.matches ? 0 : LivingTitles.frameAt(sequence,t);
    if(index!==lastFrame){byId('stage').innerHTML=LivingTitles.frameSVG(sequence,index,byId('ink').value,+byId('size').value);lastFrame=index;}
    byId('stage').setAttribute('aria-label',`${playing ? 'Playing' : 'Paused'} title: ${scene.text}`);
    byId('scrub').value=t;byId('time').textContent=`${t.toFixed(2)} / ${sequence.duration.toFixed(2)} s`;
  }
  function tick(){if(!playing) return;show(time());raf=requestAnimationFrame(tick);}
  /** Audio and vectors share the AudioContext clock, including pause/resume offsets. */
  async function play(){
    if(!sequence || busy || reduce.matches) return;
    const prepared=sequence,version=++playVersion;
    if(audio){
      context ??= new AudioContext(); await context.resume();
      if(sequence!==prepared || busy || version!==playVersion) return;
      stopSound();
      source=context.createBufferSource();source.buffer=audio;source.loop=true;source.loopEnd=sequence.duration;
      source.connect(context.destination);source.start(0,position%sequence.duration);clockStart=context.currentTime;
    } else clockStart=performance.now()/1000;
    playing=true;controls();tick();
  }
  /** Keep exports gated by certification and the current prepared scene. */
  function controls(){
    byId('prepare').disabled=busy || !profile;
    byId('cancel').disabled=!busy;
    byId('play').disabled=busy || !sequence || reduce.matches;
    byId('play').textContent=playing ? 'Pause' : 'Play';
    byId('restart').disabled=busy || !sequence;byId('scrub').disabled=busy || !sequence;
    byId('svg').disabled=busy || !sequence || !profile?.certified;
    byId('video').disabled=busy || !sequence || !profile?.certified;
    byId('include-audio').disabled=busy || byId('mode').value!=='audio';
    byId('video').textContent=configuration ? `Download ${configuration.extension.toUpperCase()}` : 'Check video format';
  }
  function status(text){byId('status').textContent=text;}
  /** Abort preparations/encoders before dropping their buffers; preserve the authored cut. */
  function invalidate(keepFileSelection=false){
    const inspecting=job && file && !metadata;
    pause();job?.abort();job=null;busy=false;sequence=null;audio=null;configuration=null;probeVersion++;
    if(inspecting && !keepFileSelection){
      file=null;byId('file').value='';byId('file-status').textContent='Audio loading cancelled. Choose the file again.';
    }
    position=0;lastFrame=-1;seekResume=false;byId('progress').hidden=true;
    byId('scrub').value=0;byId('time').textContent='0.00 / — s';
    byId('codec').textContent='Prepare the loop, then check the video format for this size and audio choice.';
    if(context){void context.close();context=null;}
    controls();rest();
    status(profile ? 'Paused at rest. Prepare this loop to play or export.' : 'Choose a shipped Soft, Edge, Ink or Wide cut to author motion.');
  }
  /** Show the baseline immediately, even before preparation or for an ordinary draft. */
  function rest(){
    if(!scene) return;
    const layout=engine.layout(scene.text,scene.cut,scene.spacing,scene.cpsp),frame=engine.frame(scene.cut,layout);
    const [a,b,c,d]=frame.bounds;
    const restSequence={frames:[frame],text:scene.text,viewBox:[a-40,b-40,c-a+80,d-b+80]};
    byId('stage').innerHTML=LivingTitles.frameSVG(restSequence,0,byId('ink').value,+byId('size').value);
  }
  /** Static Lab renders call this after restoring CUT from the side-by-side proofs. */
  function update(cut,text,cpsp){
    const spacing=spacingForCut(cut,SPACING_EXPORTS),key=JSON.stringify([cut,text,cpsp]);
    if(key===sceneKey) return;
    sceneKey=key;scene={cut:JSON.parse(JSON.stringify(cut)),text,spacing,cpsp};
    profile=spacing ? MOTION_PROFILES.profiles.find(p=>p.cut===spacing.cut &&
      Object.entries(p.settings).every(([k,v])=>JSON.stringify(v)===JSON.stringify(spacing.settings[k]))) : null;
    // Snapshots use the cut's name field rather than a display label in older builds.
    if(spacing && !profile) profile=MOTION_PROFILES.profiles.find(p=>Object.entries(p.settings)
      .every(([k,v])=>JSON.stringify(v)===JSON.stringify(spacing.settings[k])));
    byId('profile').textContent=profile ? `${profile.cut} · ${profile.id} · up to +${profile.thickness*100}% thickness, +${profile.slant}° slant, +${profile.penAngle}° pen angle${profile.certified ? ' · certified' : ' · exports blocked: certification required'}`
      : 'Ordinary Lab draft. Motion profiles are available for the four shipped cut geometries.';
    invalidate();
  }
  /** Decode the selected clip and prepare vectors cooperatively, with a single abort owner. */
  async function prepare(){
    if(!profile || busy) return;
    pause();configuration=null;const controller=new AbortController();job=controller;busy=true;
    byId('progress').hidden=false;byId('progress').value=0;controls();
    try{
      let timeline;
      if(byId('mode').value==='audio'){
        if(!file || !metadata) throw new Error('Choose a supported local audio file first');
        status('Decoding the selected clip…');
        audio=await (await media()).decodeClip(file,+byId('start').value,+byId('duration').value,controller.signal);
        const duration=audio.duration;
        timeline={duration,values:LivingTitles.audioEnvelope(Array.from({length:audio.numberOfChannels},(_,i)=>audio.getChannelData(i)),audio.sampleRate,duration)};
      } else { audio=null;timeline=LivingTitles.bpmEnvelope(+byId('bpm').value,+byId('beats').value); }
      status('Preparing vector frames…');
      const result=await LivingTitles.prepare({engine,cut:scene.cut,spacing:scene.spacing,text:scene.text,cpsp:scene.cpsp,profile,
        strength:+byId('strength').value/100,axes:{weight:byId('weight').checked,slant:byId('slant').checked,penAngle:byId('pen').checked},
        ...timeline,signal:controller.signal,onProgress:value=>{byId('progress').value=value;}});
      if(job!==controller) return;
      sequence=result;position=0;lastFrame=-1;byId('scrub').max=result.duration;show();
      status(`Ready · ${result.frames.length} frames · ${result.duration.toFixed(2)} s · 30 FPS${reduce.matches ? ' · reduced motion: resting preview' : ' · paused'}`);
    } catch(error){if(job===controller){sequence=null;audio=null;status(error.name==='AbortError' ? 'Preparation cancelled.' : error.message);}}
    finally{if(job===controller){job=null;busy=false;byId('progress').hidden=true;controls();}}
  }
  /** Read metadata on file selection; no full-song PCM decode or network request. */
  async function chooseFile(){
    const selected=byId('file').files[0] || null;
    invalidate(true);file=selected;metadata=null;
    if(!file) return;
    const controller=new AbortController();job=controller;busy=true;controls();byId('file-status').textContent='Reading local audio metadata…';
    try{
      const info=await (await media()).inspectAudio(file,controller.signal);
      if(job!==controller) return;
      metadata=info;byId('start').value=0;byId('start').max=Math.max(0,info.duration-1);
      byId('duration').value=Math.min(2,info.duration);byId('duration').max=Math.min(10,info.duration);
      byId('file-status').textContent=`${file.name} · ${info.duration.toFixed(2)} s · ${info.channels} channels · local only`;
    } catch(error){if(job===controller){file=null;byId('file-status').textContent=error.name==='AbortError' ? 'Audio loading cancelled. Choose the file again.' : error.message;}}
    finally{if(job===controller){job=null;busy=false;controls();}}
  }
  /** Offer the actual format for the current dimensions/audio, ignoring obsolete probes. */
  async function probe(){
    if(!sequence) return null;
    const version=++probeVersion,prepared=sequence;
    byId('codec').textContent='Checking this browser’s video codecs…';
    const dimensions=LivingTitles.dimensions(sequence,+byId('size').value);
    const selected=await (await media()).selectConfiguration(dimensions.width,dimensions.height,byId('include-audio').checked && byId('mode').value==='audio' ? audio : null);
    if(version!==probeVersion || prepared!==sequence) return null;
    configuration=selected;
    byId('codec').textContent=selected ? `${selected.label} · ${dimensions.width} × ${dimensions.height} · .${selected.extension}`
      : 'No supported video configuration for this size and audio choice. Try 1080 px or turn audio off.';
    controls();return selected;
  }
  function download(blob,extension){
    const url=URL.createObjectURL(blob),link=document.createElement('a');
    link.href=url;link.download=`${slug(scene.text)}-living.${extension}`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  async function video(){
    if(!sequence || !profile?.certified || busy) return;
    if(!configuration){await probe();return;}
    pause();const controller=new AbortController();job=controller;busy=true;controls();
    byId('progress').hidden=false;byId('progress').value=0;status(`Encoding ${configuration.label}…`);
    const size=+byId('size').value;
    try{
      const result=await (await media()).encodeVideo({sequence,frameSVG:(s,i,ink)=>LivingTitles.frameSVG(s,i,ink,size),
        ...LivingTitles.dimensions(sequence,size),ink:byId('ink').value,background:byId('background').value,
        audio:byId('include-audio').checked && byId('mode').value==='audio' ? audio : null,signal:controller.signal,
        onProgress:value=>{byId('progress').value=value;}});
      if(job!==controller) return;
      configuration=result.configuration;
      const dimensions=LivingTitles.dimensions(sequence,size);
      byId('codec').textContent=`${configuration.label} · ${dimensions.width} × ${dimensions.height} · .${configuration.extension}`;
      download(result.blob,result.configuration.extension);status(`Downloaded ${result.configuration.label}.`);
    } catch(error){if(job===controller) status(error.name==='AbortError' ? 'Video export cancelled.' : error.message);}
    finally{if(job===controller){job=null;busy=false;byId('progress').hidden=true;controls();}}
  }
  for(const id of ['mode','bpm','beats','start','duration','weight','slant','pen','strength','ink','background','size'])
    byId(id).addEventListener('input',()=>{
      byId('bpm-controls').hidden=byId('mode').value!=='bpm';byId('audio-controls').hidden=byId('mode').value!=='audio';
      byId('strength-value').textContent=byId('strength').value+'%';invalidate();
    });
  byId('file').addEventListener('change',chooseFile);
  byId('include-audio').addEventListener('change',()=>{configuration=null;probeVersion++;controls();byId('codec').textContent='Check video format for this audio choice.';});
  byId('prepare').addEventListener('click',prepare);
  byId('cancel').addEventListener('click',()=>{invalidate();status('Operation cancelled.');});
  byId('play').addEventListener('click',()=>{if(playing) pause();else void play().catch(error=>status(error.message));});
  byId('restart').addEventListener('click',()=>{pause();seekResume=false;position=0;show();});
  byId('scrub').addEventListener('input',()=>{const requested=+byId('scrub').value;seekResume=seekResume || playing;pause();position=requested;show();});
  byId('scrub').addEventListener('change',()=>{if(seekResume){seekResume=false;void play().catch(error=>status(error.message));}});
  byId('svg').addEventListener('click',()=>{if(sequence && profile?.certified) download(new Blob([LivingTitles.animatedSVG(sequence,byId('ink').value,+byId('size').value)],{type:'image/svg+xml'}),'svg');});
  byId('video').addEventListener('click',()=>{void video().catch(error=>status(error.message));});
  reduce.addEventListener('change',()=>{pause();lastFrame=-1;show();status(reduce.matches ? 'Reduced motion: resting preview.' : 'Paused.');});
  window.addEventListener('pagehide',()=>{invalidate();file=null;metadata=null;});
  return {update,prepare,inspect:()=>({prepared:!!sequence,busy,playing,position:time(),frames:sequence?.frames.length || 0,hasAudio:!!audio,profile:profile?.id}),
    // Read-only gate access: the same vectors/spacing consumed by every delivery path.
    snapshot:()=>sequence};
})();
