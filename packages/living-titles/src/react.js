import { createElement, useEffect, useRef, useState } from 'react';
import { createTitleScene, createTitlePlayer, createBpmSource } from './index.js';
const silentSource=createBpmSource();

/** Optional React integration; the host owns placement, styles and audio. */
export function LivingTitle({title,cut='Soft',strength=.7,capitalSpacing=true,axes,
  source=silentSource,color='#e6cc87',playing=true,className,style,onError}) {
  const host=useRef(null),player=useRef(null),prepared=useRef(null),applied=useRef(null),current=useRef({source,color,playing,onError});
  current.current={source,color,playing,onError};
  const [status,setStatus]=useState('preparing');
  const weight=axes?.weight ?? true,slant=axes?.slant ?? true,penAngle=axes?.penAngle ?? true;
  /** Mount completed geometry with the latest options, including in-flight edits. */
  function mount(scene){const options=current.current;
    player.current=createTitlePlayer(host.current,scene,{source:options.source,color:options.color,autoplay:options.playing});
    applied.current=options;setStatus('ready');}
  useEffect(()=>{
    const controller=new AbortController();setStatus('preparing');
    createTitleScene({title,cut,strength,capitalSpacing,axes:{weight,slant,penAngle},signal:controller.signal})
      .then(scene=>{
        if(controller.signal.aborted) return;
        prepared.current=scene;mount(scene);
      }).catch(error=>{
        if(controller.signal.aborted) return;
        setStatus('error');current.current.onError?.(error);
      });
    return ()=>{controller.abort();player.current?.dispose();player.current=null;prepared.current=null;applied.current=null;};
  },[title,cut,strength,capitalSpacing,weight,slant,penAngle]);
  useEffect(()=>{
    if(!prepared.current)return;const active=player.current;
    try{if(!active){mount(prepared.current);return;}const before=applied.current;
      if(before.source!==source)active.setSource(source);if(before.color!==color)active.setColor(color);
      if(before.playing!==playing){if(playing)active.play();else active.pause();}applied.current=current.current;
    }catch(error){active?.dispose();player.current=null;applied.current=null;setStatus('error');current.current.onError?.(error);}
  },[source,color,playing]);
  // React owns the fallback sibling; the imperative player owns only its empty host.
  return createElement('span',{className,style,'data-living-title-status':status},
    createElement('span',{ref:host,style:{display:status==='ready' ? 'block' : 'none',width:'100%',height:'100%'}}),
    status!=='ready' ? createElement('span',null,title) : null);
}
