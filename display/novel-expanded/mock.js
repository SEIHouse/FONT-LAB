import {cuts,createTitleScene,createTitlePlayer,createBpmSource,exportAnimatedSVG} from './runtime/index.js';
// The mock consumes the same core and browser player delivered to Development.
const $=id=>document.getElementById(id),reduced=matchMedia('(prefers-reduced-motion: reduce)');
const fields=['wordmark','featured','placement','cpsp','weight','slant','penAngle','strength','bpm','ink','hero-ink'];
let cutName='Soft',scenes=[],players=[],controller,busy=false,playing=!reduced.matches,externalSource=null,disposed=false;
let motionSource=createBpmSource({bpm:Number($('bpm').value)});
function sceneSettings(){return {schema:1,kind:'novel-expanded-title-study',cut:cutName,
  wordmark:$('wordmark').value,featured:$('featured').value,placement:$('placement').value,
  cpsp:$('cpsp').checked,axes:{weight:$('weight').checked,slant:$('slant').checked,penAngle:$('penAngle').checked},
  strength:Number($('strength').value)/100,bpm:Number($('bpm').value),ink:$('ink').value,heroInk:$('hero-ink').value};}
function present(){
  const s=sceneSettings(),compare=$('comparison').checked;
  const headerLiving=scenes.length>0 && !compare && s.placement!=='featured';
  const heroLiving=scenes.length>0 && !compare && s.placement!=='header';
  $('header-art').hidden=!headerLiving;$('header-serif').hidden=headerLiving;
  $('hero-art').hidden=!heroLiving;$('hero-serif').hidden=heroLiving;$('hero-label').hidden=!heroLiving;
  $('header-serif').textContent=s.wordmark;$('hero-serif').textContent=s.featured;$('hero-label').textContent=s.featured;
  $('header-serif').style.color=s.ink;$('hero-serif').style.color=s.heroInk;
  $('cut-caption').textContent=compare?'Serif comparison':`${cutName} / living`;
  $('strength-value').value=`${Math.round(s.strength*100)}%`;$('bpm-value').value=`${s.bpm} BPM`;
  $('play').textContent=reduced.matches?'Reduced motion: static':playing?'Pause motion':'Play motion';
  $('play').disabled=busy || !scenes.length || reduced.matches;
  $('restart').disabled=busy || !scenes.length || reduced.matches;
  $('svg').disabled=busy || !scenes.length || Boolean(externalSource);
  $('cuts').querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.cut===cutName)));
}
async function prepare(){
  controller?.abort();controller=new AbortController();const active=controller,s=sceneSettings();busy=true;present();
  $('status').textContent='Preparing lettering…';
  try{
    const next=[];
    for(const [i,title] of [s.wordmark,s.featured].entries()) next.push(await createTitleScene({
      title,cut:s.cut,strength:s.strength,capitalSpacing:s.cpsp,axes:s.axes,signal:active.signal,
      onProgress:value=>{if(controller===active)$('status').textContent=`Preparing lettering… ${Math.round((i+value)*50)}%`;},
    }));
    if(active.signal.aborted || disposed)return;
    players.forEach(p=>p.dispose());players=[];scenes=next;
    players=next.map((scene,i)=>createTitlePlayer($(i?'hero-art':'header-art'),scene,
      {source:motionSource,color:i?s.heroInk:s.ink,autoplay:playing}));
    const limits=s.cut==='Ink'?'1% thickness, 1° slant, 0.25° pen angle':'3% thickness, 1° slant, 2° pen angle';
    $('profile').textContent=`${s.cut}: up to +${limits}. Strength scales these reviewed limits.`;
    $('status').textContent=externalSource?'External motion signal · audio stays with its owner.':'Ready · silent breathing preview';
  }catch(error){if(error.name!=='AbortError' && controller===active){players.forEach(p=>p.dispose());players=[];scenes=[];$('status').textContent=error.message;}}
  finally{if(controller===active){busy=false;present();}}
}
function download(content,type,name){const url=URL.createObjectURL(new Blob([content],{type})),a=document.createElement('a');
  a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('cuts').innerHTML=cuts.map(c=>`<button data-cut="${c.name}" aria-pressed="${c.name===cutName}">${c.name}</button>`).join('');
$('cuts').addEventListener('click',event=>{const name=event.target.dataset.cut;if(name){cutName=name;prepare();}});
fields.forEach(id=>$(id).addEventListener('input',()=>{
  present();if(['ink','hero-ink'].includes(id))players[id==='ink'?0:1]?.setColor($(id).value);
  else if(id==='bpm'){if(!externalSource){motionSource=createBpmSource({bpm:Number($('bpm').value)});players.forEach(p=>p.setSource(motionSource));}}
  else if(id!=='placement')prepare();
}));
$('comparison').addEventListener('change',present);
$('play').addEventListener('click',()=>{playing=!playing;players.forEach(p=>playing?p.play():p.pause());present();});
$('restart').addEventListener('click',()=>players.forEach(p=>p.seek(0)));
$('save').addEventListener('click',()=>download(JSON.stringify(sceneSettings(),null,2)+'\n','application/json','novel-expanded-title-study.json'));
$('svg').addEventListener('click',()=>{if(busy || !scenes.length || externalSource)return;
  download(exportAnimatedSVG(scenes[0],{bpm:Number($('bpm').value),color:$('ink').value}),'image/svg+xml','novel-expanded-wordmark.svg');});
document.querySelectorAll('[data-demo]').forEach(b=>b.addEventListener('click',()=>{$('demo-message').textContent=b.dataset.demo;$('status').textContent=b.dataset.demo;}));
document.querySelectorAll('.genre').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('.genre').forEach(g=>{g.classList.toggle('selected',g===b);g.setAttribute('aria-pressed',String(g===b));});
}));
const onReduced=()=>present();reduced.addEventListener('change',onReduced);
window.NovelExpandedMock=Object.freeze({
  setMotionSource(value){if(disposed)throw new Error('The mock has been disposed.');
    if(value!==null && (!value || typeof value.sample!=='function'))throw new TypeError('Motion source needs sample(seconds).');
    externalSource=value;motionSource=value ?? createBpmSource({bpm:Number($('bpm').value)});
    players.forEach(p=>p.setSource(motionSource));present();
    $('status').textContent=value?'External motion signal · audio stays with its owner.':'Ready · silent breathing preview';},
  inspect:()=>({ready:scenes.length===2,busy,cut:cutName,energy:players[0]?.getState().energy ?? 0,
    pose:players[0]?.getState().pose ?? -1,elapsed:players[0]?.getState().elapsed ?? 0,playing,reduced:reduced.matches,
    source:externalSource?'external':'silent',scene:sceneSettings(),viewBoxes:scenes.map(s=>s.viewBox)}),
  dispose(){if(disposed)return;disposed=true;controller?.abort();players.forEach(p=>p.dispose());players=[];scenes=[];externalSource=null;
    reduced.removeEventListener('change',onReduced);},
});
present();prepare();
