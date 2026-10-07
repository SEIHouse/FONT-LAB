"""Browser regression gate for authoring, declarative SVG playback and real encoded video."""
import argparse
import base64
from contextlib import contextmanager
import functools
import http.server
import json
from pathlib import Path
import subprocess
import sys
import threading
import wave
import math
import struct

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
from playwright.sync_api import sync_playwright
from display.verify_lab import layout_snapshot,layout_flags,MOBILE_WIDTHS


@contextmanager
def local_site():
    """Serve local assets in a secure localhost context, never uploading creator media."""
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*_args):
            """Keep gate output limited to assertions and the final report."""
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield f'http://127.0.0.1:{server.server_port}'
    finally:server.shutdown();server.server_close();thread.join()


def audio_fixture(file):
    """Make antiphase stereo with silent outer sections to verify selected-clip trimming."""
    sample_rate=48000
    with wave.open(str(file),'wb') as out:
        out.setnchannels(2);out.setsampwidth(2);out.setframerate(sample_rate)
        pcm=bytearray()
        for i in range(sample_rate*4):
            value=round(6553*math.sin(2*math.pi*220*i/sample_rate)) if sample_rate<=i<3*sample_rate else 0
            pcm.extend(struct.pack('<hh',value,-value))
        out.writeframes(pcm)


VECTOR_PARITY = r"""() => {
  const sequence=LivingTitleUI.snapshot(),svg=LivingTitles.animatedSVG(sequence);
  const staticWord=new DOMParser().parseFromString(drawWord(sequence.text,30).replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" '),'image/svg+xml');
  const liveWord=new DOMParser().parseFromString(`<svg xmlns="http://www.w3.org/2000/svg">${sequence.frames[0].body}</svg>`,'image/svg+xml');
  const serializer=new XMLSerializer();
  if([...staticWord.documentElement.children].map(el=>serializer.serializeToString(el)).join('')!==
    [...liveWord.documentElement.children].map(el=>serializer.serializeToString(el)).join('')) throw new Error('Resting live artwork changed');
  const doc=new DOMParser().parseFromString(svg,'image/svg+xml');
  if(doc.querySelector('parsererror')) throw new Error('Invalid exported SVG XML');
  if(doc.querySelector('script') || doc.querySelector('[href]')) throw new Error('SVG must be self-contained');
  const groups=[...doc.querySelector('.motion').children];
  if(groups.length!==sequence.frames.length) throw new Error('Missing SVG frame');
  const ids=[...doc.querySelectorAll('[id]')].map(el=>el.id);
  if(new Set(ids).size!==ids.length) throw new Error('Duplicate clip IDs');
  for(let i=0;i<groups.length;i++){
    const preview=LivingTitles.artwork(sequence.frames[i],`f${i}-`);
    const parsed=new DOMParser().parseFromString(`<svg xmlns="http://www.w3.org/2000/svg">${preview}</svg>`,'image/svg+xml');
    const clone=groups[i].cloneNode(true);clone.querySelector('animate').remove();
    if([...clone.children].map(el=>serializer.serializeToString(el)).join('')!==
      [...parsed.documentElement.children].map(el=>serializer.serializeToString(el)).join('')) throw new Error('SVG/preview vector mismatch');
  }
  return {frames:groups.length,ids:ids.length,viewBox:sequence.viewBox,svg};
}"""

VIDEO_CHECK = r"""async ({withAudio=false,longest=1080}) => {
  const sequence=LivingTitleUI.snapshot(),size=LivingTitles.dimensions(sequence,longest);
  const audio=withAudio ? window.gateAudio : null;
  const result=await LivingMedia.encodeVideo({sequence,frameSVG:(s,i,ink)=>LivingTitles.frameSVG(s,i,ink,longest),...size,
    ink:'#ffffff',background:'#000000',audio});
  const url=URL.createObjectURL(result.blob),video=document.createElement('video');
  video.muted=true;video.preload='auto';video.src=url;document.body.append(video);
  const wait=type=>new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>reject(new Error('Video '+type+' timeout')),15000);
    video.addEventListener(type,()=>{clearTimeout(timer);resolve();},{once:true});
    video.addEventListener('error',()=>{clearTimeout(timer);reject(new Error('Video decode failed'));},{once:true});
  });
  const metrics=[];
  try{
    await wait('loadeddata');
    if(Math.abs(video.duration-sequence.duration)>1/30) throw new Error('Encoded duration differs by more than a frame');
    for(const index of [0,Math.floor(sequence.frames.length/4),Math.floor(sequence.frames.length/2)]){
      video.currentTime=sequence.frames[index].time+1/60;await wait('seeked');
      const reference=document.createElement('canvas'),decoded=document.createElement('canvas');
      reference.width=decoded.width=size.width;reference.height=decoded.height=size.height;
      await LivingMedia.paintFrame(reference,LivingTitles.frameSVG(sequence,index,'#ffffff',longest),'#000000');
      const ctx=decoded.getContext('2d');ctx.drawImage(video,0,0);
      const a=reference.getContext('2d').getImageData(0,0,size.width,size.height).data,b=ctx.getImageData(0,0,size.width,size.height).data;
      const box=pixels=>{
        let x0=size.width,y0=size.height,x1=-1,y1=-1;
        for(let y=0;y<size.height;y++)for(let x=0;x<size.width;x++)if(pixels[(y*size.width+x)*4]>128){
          x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);}
        return [x0,y0,x1,y1];
      };
      const bounds=box(a),encoded=box(b),error=Math.max(...bounds.map((value,i)=>Math.abs(value-encoded[i])));
      if(error>2) throw new Error('Encoded ink bounds differ by more than two pixels');
      let difference=0,ink=0;
      for(let i=0;i<a.length;i+=4){difference+=Math.abs(a[i]-b[i]);ink+=a[i];}
      if(difference/Math.max(ink,1)>.03) throw new Error('Decoded frame differs from its prepared vector');
      metrics.push({index,bounds,encoded,error,relativeCoverageError:difference/ink});
      reference.width=decoded.width=0;
    }
    const bytes=new Uint8Array(await result.blob.arrayBuffer());let binary='';
    for(let i=0;i<bytes.length;i+=8192) binary+=String.fromCharCode(...bytes.subarray(i,i+8192));
    return {configuration:result.configuration,...size,duration:video.duration,metrics,bytes:btoa(binary)};
  }finally{video.pause();video.removeAttribute('src');video.load();video.remove();URL.revokeObjectURL(url);}
}"""


def verify(out, *, video=True):
    """Exercise visible controls, lifecycle races, image-mode SVG and real browser codecs."""
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    audio_fixture(out/'phase-stereo.wav')
    report={'cuts':{},'mobile':[],'flags':[]}
    with local_site() as base,sync_playwright() as p:
        browser=p.chromium.launch(args=['--mute-audio'])
        page=browser.new_page(viewport={'width':1280,'height':900})
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.add_init_script('''window.gateContexts=[];const NativeAudioContext=window.AudioContext;
          window.AudioContext=class extends NativeAudioContext{
            constructor(...args){super(...args);window.gateContexts.push(this);this.gateConnections=0;}
            createBufferSource(){const node=super.createBufferSource(),ctx=this;
              const connect=node.connect.bind(node),disconnect=node.disconnect.bind(node),start=node.start.bind(node);
              node.connect=(...args)=>{ctx.gateConnections++;return connect(...args);};
              node.disconnect=(...args)=>{ctx.gateConnections--;return disconnect(...args);};
              node.start=(...args)=>{ctx.gateSourceStart=ctx.currentTime;ctx.gateSourceOffset=args[1] || 0;return start(...args);};return node;}
          };''')
        page.goto(base+'/display/lab/index.html');page.wait_for_function('LivingTitleUI.inspect().prepared')
        for cut in ('Soft','Edge','Ink','Wide'):
            page.locator(f'#presets [data-p="{cut}"]').click()
            page.locator('#t-title').fill('LA AV The Last Lotus Á β Ж')
            page.locator('#cpsp').check()
            page.locator('#lt-prepare').click();page.wait_for_function('LivingTitleUI.inspect().prepared')
            vectors=page.evaluate(VECTOR_PARITY)
            (out/f'{cut.lower()}.svg').write_text(vectors.pop('svg'),encoding='utf-8')
            frozen=page.evaluate('LivingTitleUI.snapshot().layout')
            compiled=page.evaluate("titleLayout($('t-title').value,CUT,spacingForCut(CUT,SPACING_EXPORTS),true).width")
            if frozen['width']!=compiled:raise ValueError('Resting compiled spacing drift')
            # Repeated preparation must produce identical frame geometry and canvas bounds.
            first=page.evaluate('JSON.stringify(LivingTitleUI.snapshot())')
            page.locator('#lt-prepare').click();page.wait_for_function('LivingTitleUI.inspect().prepared && !LivingTitleUI.inspect().busy')
            if first!=page.evaluate('JSON.stringify(LivingTitleUI.snapshot())'):raise ValueError('Non-deterministic preparation')
            page.locator('#lt-play').click();page.wait_for_function('LivingTitleUI.inspect().playing')
            page.wait_for_timeout(120);page.locator('#lt-play').click()
            if page.evaluate('LivingTitleUI.inspect().playing'):raise ValueError('Pause failed')
            page.locator('#lt-scrub').evaluate('(el)=>{el.value="1.2";el.dispatchEvent(new Event("input",{bubbles:true}));el.dispatchEvent(new Event("change",{bubbles:true}));}')
            if abs(page.evaluate('LivingTitleUI.inspect().position')-1.2)>1e-6:raise ValueError('Seek failed')
            page.locator('#lt-restart').click()
            if page.evaluate('LivingTitleUI.inspect().position')!=0:raise ValueError('Restart failed')
            report['cuts'][cut]=vectors | {'compiled_width':compiled}
            if video:
                page.add_script_tag(url=base+'/display/lab/living-media.js')
                encoded=page.evaluate(VIDEO_CHECK,dict(withAudio=False))
                (out/f'{cut.lower()}.{encoded["configuration"]["extension"]}').write_bytes(base64.b64decode(encoded.pop('bytes')))
                report['cuts'][cut]['video']=encoded
                if cut=='Soft':
                    large=page.evaluate(VIDEO_CHECK,dict(withAudio=False,longest=1920))
                    (out/f'soft-1920.{large["configuration"]["extension"]}').write_bytes(base64.b64decode(large.pop('bytes')))
                    if max(large['width'],large['height'])!=1920:raise ValueError('1920 pixel output sizing failed')
                    report['large_video']=large
        # Declarative standalone and image-mode playback must both animate.
        standalone=browser.new_page();standalone.goto(base+'/'+(out/'soft.svg').resolve().relative_to(ROOT).as_posix())
        standalone.evaluate('document.documentElement.pauseAnimations();document.documentElement.setCurrentTime(.5)')
        if standalone.locator('.motion > g').evaluate_all('els=>els.filter(el=>getComputedStyle(el).opacity==="1").length')!=1:
            raise ValueError('Standalone SVG frame selection failed')
        image=browser.new_page();image.set_content(f'<img id="proof" width="1080" src="{base}/{(out/"soft.svg").resolve().relative_to(ROOT).as_posix()}">')
        image.wait_for_function('document.querySelector("img").complete')
        before=image.locator('#proof').screenshot();image.wait_for_timeout(240);after=image.locator('#proof').screenshot()
        if before==after:raise ValueError('SVG image embedding did not animate')
        standalone.emulate_media(reduced_motion='reduce')
        if standalone.locator('.motion').evaluate('el=>getComputedStyle(el).display')!='none':raise ValueError('SVG reduced motion failed')
        page.emulate_media(reduced_motion='reduce')
        if not page.locator('#lt-play').is_disabled():raise ValueError('Reduced-motion preview must rest')
        page.emulate_media(reduced_motion='no-preference')
        # Editing stops stale playback and cancels prepared frames without writing CUT.
        saved=page.evaluate('JSON.stringify(CUT)')
        page.locator('#lt-play').click();page.wait_for_function('LivingTitleUI.inspect().playing')
        page.locator('#lt-strength').fill('40')
        if page.evaluate('LivingTitleUI.inspect().playing || LivingTitleUI.inspect().prepared'):raise ValueError('Editing failed to invalidate')
        if saved!=page.evaluate('JSON.stringify(CUT)'):raise ValueError('Motion changed saved cut')
        page.locator('#lt-bpm').fill('60');page.locator('#lt-beats').fill('10');page.locator('#lt-prepare').click();page.locator('#lt-cancel').click()
        page.wait_for_timeout(40)
        if page.evaluate('LivingTitleUI.inspect().prepared || LivingTitleUI.inspect().busy'):raise ValueError('Cancellation published obsolete frames')
        # Audio metadata, selected clip PCM, antiphase envelope and encode timestamps.
        page.locator('#lt-mode').select_option('audio');page.locator('#lt-file').set_input_files(str(out/'phase-stereo.wav'))
        page.wait_for_function('!LivingTitleUI.inspect().busy && document.querySelector("#lt-file-status").textContent.includes("channels")')
        page.locator('#lt-start').fill('1');page.locator('#lt-duration').fill('2');page.locator('#lt-prepare').click()
        page.wait_for_function('LivingTitleUI.inspect().prepared')
        audio_metrics=page.evaluate('''async url=>{
          const file=new File([await (await fetch(url)).blob()],'phase.wav');window.gateAudio=await LivingMedia.decodeClip(file,1,2);
          const buffer=window.gateAudio,a=buffer.getChannelData(0),b=buffer.getChannelData(1);
          const envelope=LivingTitles.audioEnvelope([a,b],buffer.sampleRate,buffer.duration);
          return {duration:buffer.duration,samples:buffer.length,channels:buffer.numberOfChannels,
            phaseError:Math.max(...a.slice(0,1000).map((x,i)=>Math.abs(x+b[i]))),peak:Math.max(...envelope)};
        }''',base+'/'+(out/'phase-stereo.wav').resolve().relative_to(ROOT).as_posix())
        if audio_metrics['phaseError']>1e-5 or audio_metrics['peak']<.35 or audio_metrics['samples']!=96000:raise ValueError('Selected stereo PCM failed')
        report['audio']=audio_metrics
        page.locator('#lt-play').click();page.wait_for_function('LivingTitleUI.inspect().playing')
        page.wait_for_timeout(100)
        if page.evaluate('Math.abs(LivingTitleUI.inspect().position-(gateContexts.at(-1).currentTime-gateContexts.at(-1).gateSourceStart+gateContexts.at(-1).gateSourceOffset))')>1/30:
            raise ValueError('Preview does not follow the audio clock')
        page.locator('#lt-play').click()
        if page.evaluate('gateContexts.some(context=>context.gateConnections!==0)'):raise ValueError('Pause left audio connected')
        if video:
            encoded=page.evaluate(VIDEO_CHECK,dict(withAudio=True));target=out/('audio.'+encoded['configuration']['extension'])
            target.write_bytes(base64.b64decode(encoded.pop('bytes')));report['audio_video']=encoded
            if not shutil_which('ffprobe'):raise ValueError('ffprobe is required for the audio/video timestamp gate')
            probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_packets','-of','json',str(target)],text=True,encoding='utf-8'))
            streams={row['codec_type']:row for row in probe['streams']}
            if set(streams)!={'audio','video'}:raise ValueError('Export lost a selected audio track')
            starts={kind:float(row.get('start_time',0)) for kind,row in streams.items()}
            # Container edits compensate encoder priming; playable starts must align.
            if abs(starts['audio']-starts['video'])>1/30:raise ValueError('Audio/video start timestamps drift')
            if any(abs(float(row.get('duration',encoded['duration']))-encoded['duration'])>1/30 for row in streams.values()):
                raise ValueError('Audio/video end timestamps drift')
            report['audio_video']['streams']={kind:{k:row.get(k) for k in ('codec_name','start_time','duration','sample_rate','channels')} for kind,row in streams.items()}
            cancelled=page.evaluate('''async()=>{
              const controller=new AbortController(),s=LivingTitleUI.snapshot(),size=LivingTitles.dimensions(s);
              try{await LivingMedia.encodeVideo({sequence:s,frameSVG:LivingTitles.frameSVG,...size,ink:'#ffffff',background:'#000000',
                audio:null,signal:controller.signal,onProgress:()=>controller.abort()});return false;}
              catch(error){return error.name==='AbortError';}
            }''')
            if not cancelled:raise ValueError('Video cancellation failed')
        page.locator('#lt-file').set_input_files({'name':'broken.wav','mimeType':'audio/wav','buffer':b'not audio'})
        page.wait_for_function('!LivingTitleUI.inspect().busy')
        if page.evaluate('LivingTitleUI.inspect().prepared'):raise ValueError('Invalid audio retained a prepared sequence')
        page.wait_for_function('gateContexts.every(context=>context.state==="closed" && context.gateConnections===0)')
        # Force the actual unsupported-codec UI path in a fresh page with no cached adapter.
        unsupported=browser.new_page();unsupported.goto(base+'/display/lab/index.html')
        unsupported.wait_for_function('LivingTitleUI.inspect().prepared')
        unsupported.evaluate('window.LivingMedia={selectConfiguration:async()=>null}')
        if unsupported.locator('#lt-video').is_disabled():raise ValueError('Release Lab has an uncertified profile')
        unsupported.locator('#lt-video').click()
        unsupported.wait_for_function('document.querySelector("#lt-codec").textContent.includes("No supported")')
        if video:
            fallback=browser.new_page();fallback.add_init_script('''const support=VideoEncoder.isConfigSupported.bind(VideoEncoder);
              VideoEncoder.isConfigSupported=async config=>config.codec.startsWith('avc1') ? {supported:false,config} : support(config);''')
            fallback.goto(base+'/display/lab/index.html');fallback.wait_for_function('LivingTitleUI.inspect().prepared')
            fallback.add_script_tag(url=base+'/display/lab/living-media.js')
            fallback.evaluate('''async url=>{const file=new File([await(await fetch(url)).blob()],'phase.wav');
              window.gateAudio=await LivingMedia.decodeClip(file,1,2);}''',base+'/'+(out/'phase-stereo.wav').resolve().relative_to(ROOT).as_posix())
            webm=fallback.evaluate(VIDEO_CHECK,dict(withAudio=True))
            if webm['configuration']['extension']!='webm':raise ValueError('Real WebM fallback failed')
            target=out/'fallback.webm';target.write_bytes(base64.b64decode(webm.pop('bytes')))
            streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(target)],text=True,encoding='utf-8'))
            tracks={row['codec_type']:row for row in streams['streams']}
            if set(tracks)!={'audio','video'} or tracks['audio']['codec_name']!='opus':raise ValueError('WebM fallback lost Opus audio')
            if abs(float(tracks['audio'].get('start_time',0))-float(tracks['video'].get('start_time',0)))>1/30:
                raise ValueError('WebM audio/video start timestamps drift')
            if abs(float(streams['format']['duration'])-webm['duration'])>1/30:raise ValueError('WebM audio/video end timestamps drift')
            report['webm_fallback']=webm
        # All motion panel states must remain inside every phone viewport.
        for width in MOBILE_WIDTHS:
            page.set_viewport_size({'width':width,'height':900})
            for mode in ('audio','bpm'):
                page.locator('#lt-mode').select_option(mode);page.wait_for_timeout(30)
                snapshot=layout_snapshot(page);failures=layout_flags(snapshot)
                report['mobile'].append({'width':width,'mode':mode,'flags':failures});report['flags']+=failures
        report['flags'] += [{'kind':'page-error','error':error} for error in errors]
        browser.close()
    (out/'browser.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'Living Titles: {len(report["cuts"])} cuts, {len(report["mobile"])} phone states, {len(report["flags"])} flags',flush=True)
    return report


def shutil_which(name):
    """Locate ffprobe without requiring its directory to be hard-coded on Windows."""
    import shutil
    return shutil.which(name)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'dist/living-browser')
    parser.add_argument('--skip-video',action='store_true')
    args=parser.parse_args();raise SystemExit(bool(verify(args.output_dir,video=not args.skip_video)['flags']))
