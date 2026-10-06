"""Gate built stylistic sets, preserved glyphs, Lab controls and native title widths.

python -X utf8 verify_display_alternates.py --report dist/display-alternates.json
Add --proof-dir docs/proofs/display-step4 for native default/set title proofs.
"""
import argparse
import base64
import hashlib
import io
import json
import unicodedata
from pathlib import Path

import freetype

from fontTools.ttLib import TTFont
from playwright.sync_api import sync_playwright

from display.letter_alternates import SET_NAMES
from display.counter_geometry import topology_snapshot
from verify_display_shapes import render
from verify_display_spacing import width_flags
from verify_latin import shape
from verify_lowercase import recorded

ROOT = Path(__file__).resolve().parent
CUTS = ('soft', 'edge', 'ink', 'wide')
PRESERVATION = ROOT/'tests/fixtures/display-step4-preservation.json'
ORIGINAL = dict(a='double', g='single', R='straight', K='branched', M='vertical',
                W='plain', y='curved', G='no-spur', Q='diagonal', four='closed', sixNine='closed')
SAMPLES = ('RAY WAVE GLOW', 'QUICK MORNING', 'A Dark Sky', 'a glowing railway',
           'ÁĞ ŔĶḾŴ Ý Q 469', 'ấą ģķ ŷ\u0301', 'ΚΜ КМ а ў Ќ', '4.69 ⁴⁶⁹ ₄₆₉ ¼ ¾')
CONTROL_SAMPLES = dict(a='a à ą ấ', g='g ĝ ģ', R='R Ŕ Ř', K='K k Ķ ķ', M='M Ḿ Μ',
                       W='W Ŵ', y='y ý ỹ', G='G Ĝ Ģ', Q='Q Q', four='4 ⁴ ₄ ¼', sixNine='6 9 ⁶ ₉')
COUNTERS = dict(a=dict(single=1,double=1),g=dict(single=1,double=2),
    R=dict(straight=1,curved=1),K=dict(branched=0,joined=0),
    M=dict(vertical=0,splayed=0),W=dict(plain=0,crossed=0),
    y=dict(curved=0,straight=0),G={'no-spur':0,'spur':0},
    Q=dict(diagonal=1,long=1),four=dict(open=0,closed=1),sixNine=dict(open=0,closed=1))


def outline_hash(font, name):
    """Hash decomposed final curves independently of CFF hint/program encoding."""
    return hashlib.sha256(json.dumps(recorded(font, name), separators=(',', ':')).encode()).hexdigest()


def preservation_flags(font, cut, spacing, baseline):
    """Only alternate-covered default forms may change; every other old outline is exact."""
    allowed = {spacing['glyphs'][source]['name'] for source, spec in spacing['variants'].items()
               if spec['default'] != ORIGINAL[spec['key']]}
    changed, found = [], []
    for name, before in baseline['cuts'][cut].items():
        if name not in font.getGlyphOrder():
            found.append(dict(kind='missing-original-glyph', glyph=name))
        elif outline_hash(font, name) != before:
            changed.append(name)
            if name not in allowed:
                found.append(dict(kind='unrelated-outline-change', glyph=name))
    return found, changed


def feature_flags(font, spacing):
    """Require every set/derivative, real design differences and canonical mark shaping."""
    tags = {record.FeatureTag for record in font['GSUB'].table.FeatureList.FeatureRecord}
    found = [dict(kind='missing-stylistic-set', tag=tag) for tag in SET_NAMES if tag not in tags]
    if found:
        return found
    stream=io.BytesIO(); font.save(stream)
    face=freetype.Face(io.BytesIO(stream.getvalue()))
    for source in 'agRKkMWyGQ469':
        spec=spacing['variants'][source]
        for choice,name in spec['choices'].items():
            actual=topology_snapshot(render(face,font.getGlyphID(name)))['closed_counters']
            expected=COUNTERS[spec['key']][choice]
            if actual!=expected:
                found.append(dict(kind='alternate-design-counter',source=source,choice=choice,expected=expected,actual=actual))
    for source, spec in spacing['variants'].items():
        current = spec['choices'][spec['default']]
        other = next(name for choice, name in spec['choices'].items() if choice != spec['default'])
        if current not in font.getGlyphOrder() or other not in font.getGlyphOrder():
            found.append(dict(kind='missing-alternate', source=source))
            continue
        if recorded(font, current) == recorded(font, other):
            found.append(dict(kind='identical-alternate', source=source))
        if len(source) == 1:
            features = {spec['tag']: True}
            result = shape(font, source, **features)
            if result[0][0] != other:
                found.append(dict(kind='stylistic-substitution', source=source, actual=result))
            if result != shape(font, unicodedata.normalize('NFD', source), **features):
                found.append(dict(kind='alternate-canonical-shaping', source=source))
            if source.isupper():
                spaced = shape(font, source, cpsp=True, **features)
                if sum(row[1] for row in spaced)-sum(row[1] for row in result) != spacing['capitalSpace']*2:
                    found.append(dict(kind='alternate-cpsp', source=source))
    for text in ('469', '4.69', '1/4', '16/49', '¼¾'):
        for extras in ({}, {'tnum': True}, {'sups': True}, {'subs': True}, {'frac': True}):
            if shape(font, text, ss08=True, **extras) == shape(font, text, **extras):
                found.append(dict(kind='alternate-numeric-combination', text=text, features=extras))
    for digit in '469':
        for separator in '.,':
            for text in (digit+separator, separator+digit):
                for tabular in (False, True):
                    kerned = sum(row[1] for row in shape(font,text,ss08=True,tnum=tabular))
                    plain = sum(row[1] for row in shape(font,text,ss08=True,tnum=tabular,kern=False))
                    if kerned <= plain:
                        found.append(dict(kind='alternate-decimal-spacing',text=text,tabular=tabular))
    return found


def render_proof(page, cut, font_file, directory):
    """Show the actual default and each set next to the matching Lab SVG at 80px."""
    page.evaluate("""({cut,data})=>{
      CUT=structuredClone(PRESETS.find(p=>p.name.toLowerCase()===cut)); applyToEngine();
      const defaults=structuredClone(CUT.alternates), panel=document.createElement('section'); panel.id='alternate-proof';
      panel.style.cssText='width:1740px;padding:30px;background:#faf8f1;color:#171717;box-sizing:border-box';
      let html=`<style>@font-face{font-family:Proof;src:url(data:font/woff2;base64,${data})}</style><h1 style="font:28px sans-serif">${CUT.name} · letter designs</h1>`;
      const rows=[['Default','ag R Kk MW y G Q 469'],['ss01','a g à ą ấ ĝ ģ'],['ss02','R Ŕ Ř'],['ss03','K k Ķ ķ'],
        ['ss04','M W Ḿ Ŵ'],['ss05','y ý ŷ ỹ'],['ss06','G Ĝ Ğ Ģ'],['ss07','Q Q'],['ss08','4 6 9 ⁴ ₆ ¼ ¾']];
      for(const [tag,text] of rows){
        CUT.alternates=structuredClone(defaults);
        if(tag!=='Default') for(const set of DISPLAY_SETS.filter(set=>set.tag===tag)) CUT.alternates[set.key]=set.choices.find(choice=>choice!==defaults[set.key]);
        applyToEngine(); $('cpsp').checked=false;
        html+=`<div style="border-top:1px solid #ccc;padding:8px 0;font:16px sans-serif">${tag}: ${text}</div>`;
        html+=`<div style="font:80px Proof;font-feature-settings:'${tag==='Default'?'ss01':tag}' ${tag==='Default'?0:1};white-space:nowrap">${e_(text)}</div>`;
        html+=drawText(text,80);
      }
      html+='<h2 style="font:24px sans-serif">All sets · titles</h2>';
      for(const set of DISPLAY_SETS) CUT.alternates[set.key]=set.choices.find(choice=>choice!==defaults[set.key]);
      applyToEngine();
      for(const text of ['QUICK MORNING · RAY WAVE GLOW','A dark sky, a glowing railway · 469']){
        html+=`<div style="font:64px Proof;font-feature-settings:${[...new Set(DISPLAY_SETS.map(s=>s.tag))].map(tag=>"'"+tag+"' 1").join(',')};white-space:nowrap">${e_(text)}</div>`;
        html+=drawText(text,64);
      }
      panel.innerHTML=html;document.body.append(panel);return document.fonts.ready.then(()=>true);
    }""", dict(cut=cut, data=base64.b64encode(font_file.read_bytes()).decode()))
    page.locator('#alternate-proof').screenshot(path=str(directory/f'{cut}-alternates-titles.png'))
    page.locator('#alternate-proof').evaluate('(element)=>element.remove()')


def verify(fonts, lab, proof_dir=None):
    """Audit every native set, width agreement, controls and unchanged original curves."""
    baseline = json.loads(PRESERVATION.read_text(encoding='utf-8'))
    report = dict(gate_percent=.5, source_commit=baseline['source_commit'], cuts={}, flags=[])
    with sync_playwright() as runtime:
        browser = runtime.chromium.launch()
        page = browser.new_page(viewport=dict(width=1800, height=1200))
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(lab.resolve().as_uri())
        page.wait_for_function('typeof DISPLAY_SETS!=="undefined" && document.querySelector("#alt-a")')
        for cut in CUTS:
            file = fonts/cut/f'SEIHouseDisplay-{cut.title()}.otf'
            spacing = page.evaluate('(cut)=>SPACING_EXPORTS.find(s=>s.otf_sha256 && spacingForCut(PRESETS.find(p=>p.name.toLowerCase()===cut),[s]))', cut)
            if spacing['otf_sha256'] != hashlib.sha256(file.read_bytes()).hexdigest():
                report['flags'].append(dict(cut=cut, kind='stale-alternate-export'))
            with TTFont(file) as font, TTFont(file.with_suffix('.woff2')) as web:
                failures, changed = preservation_flags(font, cut, spacing, baseline)
                failures += feature_flags(font, spacing)
                rows = page.evaluate("""({cut,samples})=>{
                  CUT=structuredClone(PRESETS.find(p=>p.name.toLowerCase()===cut)); const defaults=structuredClone(CUT.alternates);
                  const modes=['Default',...new Set(DISPLAY_SETS.map(s=>s.tag)),'All'], rows=[];
                  const panel=document.createElement('div');panel.style.cssText='position:absolute;width:max-content';document.body.append(panel);
                  for(const mode of modes){
                    CUT.alternates=structuredClone(defaults);
                    if(mode!=='Default') for(const set of DISPLAY_SETS.filter(s=>mode==='All'||s.tag===mode)) CUT.alternates[set.key]=set.choices.find(c=>c!==defaults[set.key]);
                    applyToEngine();
                    for(const cpsp of [false,true]) for(const size of [48,96,192]) for(const text of samples){
                      $('cpsp').checked=cpsp;panel.innerHTML=drawText(text,size);const run=panel.firstElementChild;run.style.width='max-content';run.style.flexWrap='nowrap';
                      rows.push({mode,text,size,cpsp,lab_px:run.getBoundingClientRect().width});
                    }
                  }
                  panel.remove();return rows;
                }""", dict(cut=cut, samples=SAMPLES))
                for row in rows:
                    features = {tag: True for tag in SET_NAMES} if row['mode']=='All' else ({row['mode']:True} if row['mode']!='Default' else {})
                    actual = shape(font, row['text'], cpsp=row['cpsp'], **features)
                    if actual != shape(web, row['text'], cpsp=row['cpsp'], **features):
                        failures.append(dict(kind='alternate-web-shaping', text=row['text'], mode=row['mode']))
                    built = sum(glyph[1] for glyph in actual)*row['size']/font['head'].unitsPerEm
                    flags, difference = width_flags(row['lab_px'], built, **{key:row[key] for key in ('text','mode','size','cpsp')})
                    failures += flags
                    row.update(font_px=built, difference_percent=difference)
                controls = []
                for key, text in CONTROL_SAMPLES.items():
                    page.locator(f'#presets button[data-p="{cut.title()}"]').click()
                    spec = next(spec for spec in spacing['variants'].values() if spec['key']==key)
                    choice = next(choice for choice in spec['choices'] if choice!=spec['default'])
                    page.locator('#alt-'+key).select_option(choice)
                    page.wait_for_function('(args)=>JSON.parse(document.querySelector("#out").textContent).alternates[args.key]===args.choice && document.querySelector("#spacing-status").textContent.startsWith("Final")', arg=dict(key=key,choice=choice))
                    width = page.evaluate('(text)=>titleLayout(text,CUT,spacingForCut(CUT,SPACING_EXPORTS),false).width', text)
                    built = sum(glyph[1] for glyph in shape(font,text,**{spec['tag']:True}))/2
                    flags, difference = width_flags(width,built,key=key,text=text)
                    failures += flags
                    saved = page.evaluate('JSON.parse(document.querySelector("#out").textContent).alternates')
                    if saved[key] != choice:
                        failures.append(dict(kind='alternate-json-persistence', key=key))
                    controls.append(dict(key=key,choice=choice,difference_percent=difference))
                # Save/download/reload the real UI's choices in this isolated browser context.
                page.locator(f'#presets button[data-p="{cut.title()}"]').click()
                selected={}
                for key in CONTROL_SAMPLES:
                    spec=next(spec for spec in spacing['variants'].values() if spec['key']==key)
                    selected[key]=next(choice for choice in spec['choices'] if choice!=spec['default'])
                    page.locator('#alt-'+key).select_option(selected[key])
                page.wait_for_function('(selected)=>JSON.stringify(JSON.parse(document.querySelector("#out").textContent).alternates)===JSON.stringify(selected)', arg=selected)
                name='Alternate proof '+cut.title()
                page.locator('#cutname').fill(name)
                page.locator('#save').click()
                page.locator(f'#saved button[data-s="{name}"]').wait_for()
                with page.expect_download() as download:
                    page.locator('#download').click()
                downloaded=json.loads(Path(download.value.path()).read_text(encoding='utf-8'))
                page.reload()
                page.locator(f'#saved button[data-s="{name}"]').click()
                restored=page.evaluate('CUT.alternates')
                if downloaded['alternates']!=selected or restored!=selected:
                    failures.append(dict(kind='alternate-save-download-reload',name=name))
                report['flags'].extend(dict(cut=cut,**flag) for flag in failures)
            report['cuts'][cut] = dict(glyphs=len(font.getGlyphOrder()), alternatives=len(spacing['variants']),
                changed_default_outlines=changed, measurements=len(rows),
                max_difference_percent=max(row['difference_percent'] for row in rows), controls=controls,
                save_download_reload=restored==selected and downloaded['alternates']==selected, widths=rows)
            print(f"{cut.title()}: {len(rows)} widths, {len(controls)} controls, {len(failures)} flags", flush=True)
            if proof_dir:
                proof_dir.mkdir(parents=True, exist_ok=True)
                render_proof(page,cut,file.with_suffix('.woff2'),proof_dir)
        report['page_errors'] = errors
        report['flags'].extend(dict(kind='alternate-lab-page-error',error=error) for error in errors)
        browser.close()
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fonts',type=Path,default=ROOT/'display/fonts')
    parser.add_argument('--lab',type=Path,default=ROOT/'display/lab/index.html')
    parser.add_argument('--proof-dir',type=Path)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    result=verify(args.fonts,args.lab,args.proof_dir)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(bool(result['flags']))
