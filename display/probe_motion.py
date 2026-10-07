"""Read-only motion construction/raster probe; writes candidates only under dist/.

Candidates are never consumed by the release gate until explicitly reviewed and
copied to tests/fixtures/display-motion-topology. This tool cannot enable exports.
"""
import argparse
import base64
import json
import math
from pathlib import Path
import sys
import zlib
import unicodedata

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from playwright.sync_api import sync_playwright
from types import SimpleNamespace
from font_builder import FontBuilderCore
import pathops
from display.living_build import engine_factory, motion_digest
from display.counter_geometry import counter_flags, topology_flags, topology_snapshot
from verify_display_shapes import flags

STATES = [dict(id='rest', weight=0, slant=0, penAngle=0)] + [
    dict(id=f'extreme-{mask}', weight=int(bool(mask & 1)), slant=int(bool(mask & 2)), penAngle=int(bool(mask & 4)))
    for mask in range(1, 8)] + [
    dict(id=f'breath-{percent}', weight=percent/100, slant=percent/100, penAngle=percent/100)
    for percent in (25, 50, 75)]


def letter_apertures(source):
    """Retain Step 1's letter/number and unencoded-alternate aperture policy."""
    return len(source)!=1 or unicodedata.category(source)[0] in 'LN'


def snapshot(raster, source):
    """Keep closed-counter witnesses everywhere and open-letter witnesses in the same policy."""
    result=topology_snapshot(raster)
    if not letter_apertures(source):
        result['white_spaces']=[point for point in result['white_spaces'] if not point[2]]
    return result

RASTER = r"""async items => {
  const results=[];
  for(const item of items){
    const f=item.frame,scale=.4,[x0,y0,x1,y1]=f.bounds;
    const x=Math.floor(x0*scale)-4,y=Math.floor(y0*scale)-4;
    const width=Math.ceil(x1*scale)-x+4,height=Math.ceil(y1*scale)-y+4;
    const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="${x/scale} ${y/scale} ${width/scale} ${height/scale}" color="#000000"><defs>${f.defs}</defs>${f.body}</svg>`;
    const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'})),image=new Image(),canvas=document.createElement('canvas');
    canvas.width=width;canvas.height=height;
    try{image.src=url;let timer;try{await Promise.race([image.decode(),new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('SVG decode timeout: '+item.name)),10000);})]);}finally{clearTimeout(timer);}
      const ctx=canvas.getContext('2d');ctx.drawImage(image,0,0);
      const rgba=ctx.getImageData(0,0,width,height).data;
      let left=width,top=height,right=-1,bottom=-1;
      for(let yy=0;yy<height;yy++) for(let xx=0;xx<width;xx++) if(rgba[(yy*width+xx)*4+3]){
        left=Math.min(left,xx);right=Math.max(right,xx);top=Math.min(top,yy);bottom=Math.max(bottom,yy);
      }
      const w=right<0 ? 0 : right-left+1,h=bottom<0 ? 0 : bottom-top+1,alpha=new Uint8Array(w*h);
      for(let yy=0;yy<h;yy++) for(let xx=0;xx<w;xx++) alpha[yy*w+xx]=rgba[((yy+top)*width+xx+left)*4+3];
      const compressed=new Uint8Array(await new Response(new Blob([alpha]).stream().pipeThrough(new CompressionStream('deflate'))).arrayBuffer());
      let binary='';for(let i=0;i<compressed.length;i+=8192) binary+=String.fromCharCode(...compressed.subarray(i,i+8192));
      results.push({name:item.name,width:w,height:h,left:right<0 ? 0 : x+left,top:bottom<0 ? 0 : -y-top,coverage:btoa(binary)});
    }finally{URL.revokeObjectURL(url);image.src='';canvas.width=canvas.height=0;}
  }
  return results;
}"""


def bitmap(record):
    """Recover actual SVG coverage with its glyph-space origin, without resampling."""
    return {key:record[key] for key in ('width','height','left','top')} | {
        'pixels':zlib.decompress(base64.b64decode(record['coverage']))}


def run(out, reviewed=None, *, slugs=('soft','edge','ink','wide'), states=STATES):
    """Check native construction and live SVG counters across all motion parameter corners."""
    out=Path(out)
    if not out.resolve().is_relative_to((HERE.parent/'dist').resolve()):
        raise ValueError('Motion candidates and gate reports must stay under dist; reviewed fixtures are read-only')
    out.mkdir(parents=True,exist_ok=True)
    profiles=json.loads((HERE/'motion_profiles.json').read_text(encoding='utf-8'))['profiles']
    report={'source_sha256':motion_digest(),'profiles':[], 'states':states,'cuts':{},'flags':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page();page.set_content('<!doctype html><html lang="en"><body></body></html>')
        page.add_script_tag(content=engine_factory(audit=True)+'\nconst auditEngine=createLivingEngine();')
        for slug in slugs:
            cut=json.loads((HERE/f'cuts/{slug}.json').read_text(encoding='utf-8'))
            profile=next(row for row in profiles if row['cut']==cut['name'])
            cut_report={'glyphs':0,'states':{},'flags':[]};baseline=None
            for state in states:
                moved=cut | {'weight':cut['weight']*(1+profile['thickness']*state['weight']),
                             'slant':cut['slant']+profile['slant']*state['slant'],
                             'penAngle':cut['penAngle']+profile['penAngle']*state['penAngle']}
                page.evaluate('(cut)=>auditEngine.apply(cut)',moved)
                records=page.evaluate('auditEngine.records()')
                builder=FontBuilderCore(moved,display=True);builder.F=page.evaluate('auditEngine.contrast()')
                source_names=sorted(records)
                candidate={'profile':profile['id'],'state':state,'settings':moved,'size_px':400,'glyphs':{}}
                expected=None
                if reviewed:
                    file=Path(reviewed)/f'{slug}-{state["id"]}.json'
                    expected=json.loads(file.read_text(encoding='utf-8'))
                    if any(candidate[key]!=expected.get(key) for key in ('profile','state','settings','size_px')) or set(expected['glyphs'])!=set(source_names):
                        raise ValueError(f'{slug}/{state["id"]}: reviewed motion fixture mismatch')
                    if state['id']=='rest':baseline=expected['glyphs']
                failures=[]
                for start in range(0,len(source_names),32):
                    names=source_names[start:start+32]
                    frames=page.evaluate('''({cut,names})=>names.map(name=>({name,frame:auditEngine.frame(cut,
                      {width:1000,glyphs:[{x:0,cluster:{base:name,marks:[]}}]})}))''',dict(cut=moved,names=names))
                    rendered=page.evaluate(RASTER,frames)
                    for row in rendered:
                        name=row['name'];raster=bitmap(row);g=records[name]
                        construction=[]
                        try:
                            path=builder.outline(g,0)
                        except pathops.PathOpsError as error:
                            path=None
                            construction.append({'kind':'construction-error','message':str(error)})
                        if path:
                            # Match Step 1: audit the actual CFF-quantized outline,
                            # after the shared fitter/cleanup and final pen rounding.
                            charstring=builder.charstring(path,1000)
                            charstring.private=SimpleNamespace(nominalWidthX=0,defaultWidthX=0,Subrs=[])
                            charstring.globalSubrs=[]
                            final=pathops.Path();charstring.draw(final.getPen())
                            construction=flags(final)
                        if bool(path) != bool(any(raster['pixels'])):
                            construction.append({'kind':'missing-raster'})
                        candidate['glyphs'][name]=snapshot(raster,name)
                        found=construction+counter_flags(raster,apertures=letter_apertures(name))
                        if expected:
                            found+=topology_flags(raster,expected['glyphs'][name])
                        if baseline is not None:
                            # Preserve every reviewed resting white-space witness even
                            # if a hole crosses the span-based "substantial" threshold.
                            shear=math.tan(math.radians(moved['slant']))-math.tan(math.radians(cut['slant']))
                            witnesses=[[round(x+shear*(y-132)),y,exterior]
                                       for x,y,exterior in baseline[name]['white_spaces']]
                            found+=topology_flags(raster,{'closed_counters':candidate['glyphs'][name]['closed_counters'],
                                                          'white_spaces':witnesses})
                        failures.extend(dict(glyph=name,**flag) for flag in found)
                    if start%128==0:print(f'  {slug}/{state["id"]}: {min(start+32,len(source_names))}/{len(source_names)}',flush=True)
                if baseline is None:baseline=candidate['glyphs']
                # A new small raster detail can cross the substantial-counter threshold;
                # retain each state witness independently and report changes for review.
                changed=[name for name in source_names if baseline[name]['closed_counters']!=candidate['glyphs'][name]['closed_counters']]
                cut_report['glyphs']=len(source_names)
                cut_report['states'][state['id']]={'glyphs':len(source_names),'counter_count_changes':changed,'flags':failures}
                cut_report['flags'].extend(dict(state=state['id'],**flag) for flag in failures)
                (out/f'{slug}-{state["id"]}.json').write_text(json.dumps(candidate,separators=(',',':'),ensure_ascii=False)+'\n',encoding='utf-8')
                print(f'{slug} {state["id"]}: {len(source_names)} engine glyphs, {len(failures)} flags, {len(changed)} counter-count changes',flush=True)
                if failures:print('  '+json.dumps(failures[:6],ensure_ascii=False),flush=True)
            report['cuts'][slug]=cut_report
            # Ordinal counters exposed the difference between safe endpoint poses
            # and unsafe intervening raster phases. Stress every enabled-axis subset.
            critical=[]
            cases=[] if states==STATES[:1] else [(mask,step/100) for mask in range(1,8) for step in range(101)]
            for start in range(0,len(cases),32):
                poses=[]
                for index,(mask,amount) in enumerate(cases[start:start+32]):
                    moved=cut | {'weight':cut['weight']*(1+profile['thickness']*amount*bool(mask&1)),
                                 'slant':cut['slant']+profile['slant']*amount*bool(mask&2),
                                 'penAngle':cut['penAngle']+profile['penAngle']*amount*bool(mask&4)}
                    poses.append({'name':str(start+index),'cut':moved})
                frames=page.evaluate('''poses=>poses.map(pose=>({name:pose.name,frame:auditEngine.frame(pose.cut,
                  {width:1000,glyphs:[{x:0,cluster:{base:'ª',marks:[]}}]})}))''',poses)
                for row in page.evaluate(RASTER,frames):
                    raster=bitmap(row)
                    failures=counter_flags(raster)
                    mask,amount=cases[int(row['name'])]
                    shear=math.tan(math.radians(cut['slant']+profile['slant']*amount*bool(mask&2)))-math.tan(math.radians(cut['slant']))
                    witnesses=[[round(x+shear*(y-132)),y,exterior] for x,y,exterior in baseline['ª']['white_spaces']]
                    failures+=topology_flags(raster,{'closed_counters':topology_snapshot(raster)['closed_counters'],'white_spaces':witnesses})
                    critical.extend(dict(glyph='ª',mask=mask,energy=amount,**flag) for flag in failures)
            cut_report['critical_samples']={'poses':len(cases),'flags':critical}
            cut_report['flags'].extend(critical)
            print(f'{slug} dense ordinals: {len(cases)} poses, {len(critical)} flags',flush=True)
            report['flags'].extend(dict(cut=slug,**flag) for flag in cut_report['flags'])
            if not cut_report['flags']:report['profiles'].append(profile['id'])
        browser.close()
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=HERE.parent/'dist/motion-candidates')
    parser.add_argument('--cut',choices=('soft','edge','ink','wide'))
    parser.add_argument('--rest-only',action='store_true')
    parser.add_argument('--reviewed',type=Path,help='Read-only fixed topology directory for certification')
    args=parser.parse_args()
    report=run(args.output_dir,args.reviewed,slugs=(args.cut,) if args.cut else ('soft','edge','ink','wide'),states=STATES[:1] if args.rest_only else STATES)
    raise SystemExit(bool(report['flags']))
