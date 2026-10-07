/* Local media decoding/encoding. The engine and cut state are not library inputs. */
import {Input,BlobSource,ALL_FORMATS,AudioBufferSink,Output,BufferTarget,
  Mp4OutputFormat,WebMOutputFormat,CanvasSource,AudioBufferSource,canEncodeVideo,canEncodeAudio} from 'mediabunny';

const abortCheck = signal => { if(signal?.aborted) throw new DOMException('Operation cancelled','AbortError'); };
/** Read container metadata without decoding the song into memory. */
export async function inspectAudio(file,signal){
  const input = new Input({source:new BlobSource(file),formats:ALL_FORMATS});
  const cancel = () => input.dispose(); signal?.addEventListener('abort',cancel,{once:true});
  try{
    abortCheck(signal);
    const track = await input.getPrimaryAudioTrack();
    if(!track || !await track.canDecode()) throw new Error('This browser cannot decode this audio file. Try WAV, MP3 or another supported file.');
    const first = await track.getFirstTimestamp(), end = await track.computeDuration();
    const duration = end-first, channels = await track.getNumberOfChannels(), sampleRate = await track.getSampleRate();
    if(!Number.isFinite(duration) || duration < 1 || channels < 1 || channels > 8 || sampleRate > 192000)
      throw new Error('Use an audio file of at least one second, with up to eight channels and 192 kHz.');
    abortCheck(signal); return {duration,channels,sampleRate};
  } finally { signal?.removeEventListener('abort',cancel); input.dispose(); }
}
/** Decode only packets intersecting the selected clip; trim PCM to its exact bounds. */
export async function decodeClip(file,start,duration,signal){
  if(!Number.isFinite(start) || start < 0 || !Number.isFinite(duration) || duration < 1 || duration > 10)
    throw new Error('Select a 1–10 second clip');
  const input = new Input({source:new BlobSource(file),formats:ALL_FORMATS});
  const cancel = () => input.dispose(); signal?.addEventListener('abort',cancel,{once:true});
  try{
    abortCheck(signal);
    const track = await input.getPrimaryAudioTrack();
    if(!track || !await track.canDecode()) throw new Error('Unsupported audio decoder');
    const first = await track.getFirstTimestamp(), end = await track.computeDuration();
    if(first+start+duration > end+1e-5) throw new Error('The selected clip extends beyond the audio file');
    const channels = await track.getNumberOfChannels(), sampleRate = await track.getSampleRate();
    if(channels < 1 || channels > 8 || sampleRate > 192000) throw new Error('Unsupported channel count or sample rate');
    const buffer = new AudioBuffer({numberOfChannels:channels,length:Math.round(duration*sampleRate),sampleRate});
    const sink = new AudioBufferSink(track), from = first+start, to = from+duration;
    let copied = 0;
    for await(const chunk of sink.buffers(from,to)){
      abortCheck(signal);
      if(chunk.buffer.sampleRate !== sampleRate || chunk.buffer.numberOfChannels !== channels) throw new Error('Audio format changes inside the clip');
      const offset = Math.round((chunk.timestamp-from)*sampleRate);
      const a = Math.max(0,-offset), b = Math.min(chunk.buffer.length,buffer.length-offset);
      if(b > a){
        for(let channel=0;channel<channels;channel++) buffer.getChannelData(channel)
          .set(chunk.buffer.getChannelData(channel).subarray(a,b),Math.max(0,offset));
        copied += b-a;
      }
    }
    abortCheck(signal);
    if(!copied) throw new Error('The selected clip contains no decodable audio');
    return buffer;
  } finally { signal?.removeEventListener('abort',cancel); input.dispose(); }
}
/** Probe the actual size and optional audio configuration; never silently discard music. */
export async function selectConfiguration(width,height,audio=null,probes={video:canEncodeVideo,audio:canEncodeAudio}){
  const candidates = [
    {extension:'mp4',mime:'video/mp4',video:'avc',audio:'aac',label:'MP4 · H.264'},
    {extension:'webm',mime:'video/webm',video:'vp9',audio:'opus',label:'WebM · VP9'},
    {extension:'webm',mime:'video/webm',video:'vp8',audio:'opus',label:'WebM · VP8'},
  ];
  for(const candidate of candidates){
    try{
      if(!await probes.video(candidate.video,{width,height,frameRate:30,bitrate:8_000_000})) continue;
      if(audio && !await probes.audio(candidate.audio,{numberOfChannels:audio.numberOfChannels,sampleRate:audio.sampleRate,bitrate:192_000})) continue;
      return {...candidate,label:candidate.label+(audio ? ` + ${candidate.audio==='aac' ? 'AAC' : 'Opus'}` : ' · silent')};
    } catch { /* A broken/absent codec is an unavailable configuration. */ }
  }
  return null;
}
/** Rasterize exactly the prepared SVG frame; revoke temporary URLs on every path. */
export async function paintFrame(canvas,svg,background,signal){
  abortCheck(signal);
  const url = URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'})), image = new Image();
  try{
    image.src = url; await image.decode(); abortCheck(signal);
    const ctx = canvas.getContext('2d',{alpha:false});
    ctx.fillStyle = background; ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.drawImage(image,0,0,canvas.width,canvas.height);
  } finally { image.removeAttribute('src'); URL.revokeObjectURL(url); }
}
/** Encode frames at their prepared timestamps with bounded encoder backpressure. */
export async function encodeVideo({sequence,frameSVG,width,height,ink,background,audio,signal,onProgress=()=>{}}){
  abortCheck(signal);
  const configuration = await selectConfiguration(width,height,audio);
  if(!configuration) throw new Error('No supported video configuration for this size and audio choice. Try 1080 px or turn audio off.');
  const canvas = document.createElement('canvas'); canvas.width=width; canvas.height=height;
  const output = new Output({format:configuration.extension==='mp4' ? new Mp4OutputFormat() : new WebMOutputFormat(),target:new BufferTarget()});
  const video = new CanvasSource(canvas,{codec:configuration.video,bitrate:8_000_000});
  output.addVideoTrack(video,{frameRate:30});
  const sound = audio ? new AudioBufferSource({codec:configuration.audio,bitrate:192_000}) : null;
  if(sound) output.addAudioTrack(sound);
  const cancel = () => { if(output.state!=='finalized') void output.cancel().catch(()=>{}); }; signal?.addEventListener('abort',cancel,{once:true});
  try{
    abortCheck(signal); await output.start();
    if(sound) await sound.add(audio);
    for(let i=0;i<sequence.frames.length;i++){
      abortCheck(signal);
      await paintFrame(canvas,frameSVG(sequence,i,ink),background,signal);
      const frame = sequence.frames[i]; await video.add(frame.time,frame.duration);
      onProgress((i+1)/sequence.frames.length);
      if(i%4===3) await new Promise(resolve=>setTimeout(resolve,0));
    }
    abortCheck(signal); await output.finalize(); abortCheck(signal);
    return {blob:new Blob([output.target.buffer],{type:configuration.mime}),configuration};
  } catch(error){ if(!['finalized','canceled'].includes(output.state)) await output.cancel(); throw error; }
  finally { signal?.removeEventListener('abort',cancel); canvas.width=canvas.height=0; }
}
