"""Gate actual Lab title widths against independent HarfBuzz OTF/WOFF2 shaping.

python -X utf8 verify_display_spacing.py --report dist/display-spacing.json
Add --proof-dir docs/proofs/display-step3 --baseline dist/display-step3-baseline/fonts
to render before/after all-caps and mixed-case title sheets for every cut.
"""
import argparse
import base64
import hashlib
import json
import unicodedata
from pathlib import Path

from fontTools.ttLib import TTFont
from playwright.sync_api import sync_playwright

from verify_latin import shape
from verify_shared_engine import cff_programs, table_hashes

ROOT = Path(__file__).resolve().parent
CUTS = ('soft', 'edge', 'ink', 'wide')
TITLE_PAIRS = tuple('LA LY LT TA AV AW AY PA FA VA RT'.split())
ALL_CAPS = ('THE LAST LOTUS', 'LAY THE LIGHT', 'A WAVE AWAY', 'PAST THE FALL',
            'ART AT DAWN', 'LAVA / VALLEY')
MIXED_CASE = ('The Last Lotus', 'Office Reflection', 'A Tale of Two Cities',
              'Skybound: Vol. 12', 'Roots Through Ruin', 'The Artist’s Arrival')
SAMPLES = TITLE_PAIRS + ALL_CAPS + MIXED_CASE + (
    'À LA VALLÉE', unicodedata.normalize('NFD', 'À LA VALLÉE'),
    'ĐẠI LỘ ÁNH SÁNG', 'ΤΑ ΑΣΤΡΑ', 'СЛАВА И ВОЛЯ',
    'Affinity & Flame', 'fi\u0301 fl\u030B', 'a\u0301\u0308 i\u0302\u0323',
    'Live 1,234.56 · ½', 'TY LY TTY',
    'ART  AT DAWN', 'LA\u2009VA', 'A\u202fV', 'A\u00a0VA',
)


def width_flags(lab, built, **context):
    difference = abs(lab-built)/built*100
    return ([dict(kind='lab-font-width', difference_percent=difference, **context)]
            if difference >= .5 else []), difference


def feature_flags(font, spacing):
    found = []
    if 'cpsp' not in {record.FeatureTag for record in font['GPOS'].table.FeatureList.FeatureRecord}:
        return [dict(kind='missing-cpsp')]
    for text in ('AV', 'ÀÉ', 'ΑΒ', 'АВ'):
        plain, spaced = shape(font, text, cpsp=False), shape(font, text, cpsp=True)
        increment = sum(row[1] for row in spaced)-sum(row[1] for row in plain)
        if increment != len(text)*spacing['capitalSpace']*2:
            found.append(dict(kind='cpsp-capital-advance', text=text))
    for text in ('av', '0123', 'x\u0301', 'n\u0302\u0301'):
        if shape(font, text, cpsp=False) != shape(font, text, cpsp=True):
            found.append(dict(kind='cpsp-noncapital-change', text=text))
    return found


def render_proofs(page, cut, directory, fonts, baseline):
    """Use actual pre/post WOFF2 fonts, plus the exact Lab SVG, at title sizes."""
    current = fonts/cut/f'SEIHouseDisplay-{cut.title()}.woff2'
    previous = baseline/cut/current.name if baseline else current
    faces = {name:base64.b64encode(file.read_bytes()).decode()
             for name, file in (('Before', previous), ('After', current))}
    for kind, samples in (('all-caps', ALL_CAPS), ('mixed-case', MIXED_CASE)):
        page.evaluate("""({cut, samples, faces, kind}) => {
          CUT=JSON.parse(JSON.stringify(PRESETS.find(p=>p.name.toLowerCase()===cut))); applyToEngine();
          let panel=document.querySelector('#title-proof'); panel?.remove();
          panel=document.createElement('section'); panel.id='title-proof';
          panel.style.cssText='width:1580px;padding:36px;background:#faf8f1;color:#171717;box-sizing:border-box';
          const style=Object.entries(faces).map(([name,data])=>`@font-face{font-family:${name};src:url(data:font/woff2;base64,${data})}`).join('');
          const spec=(label,body)=>`<div style="font:15px sans-serif;color:#555;margin:12px 0 3px">${label}</div>${body}`;
          const native=(text,family,cpsp)=>`<div style="font:64px '${family}';font-kerning:normal;font-feature-settings:'cpsp' ${+cpsp};white-space:nowrap">${e_(text)}</div>`;
          let html=`<style>${style}</style><h1 style="font:30px sans-serif">${e_(CUT.name)} · ${kind} title spacing</h1>`;
          html+='<p style="font:16px sans-serif">Actual fonts at 64px; original glyphs and advances retained.</p>';
          for(const text of samples){
            html+=`<div style="border-top:1px solid #ccc;padding:12px 0">`;
            html+=spec('Before · built font',native(text,'Before',false));
            html+=spec('After · built font, kern',native(text,'After',false));
            html+=spec('After · built font, kern + cpsp',native(text,'After',true));
            $('cpsp').checked=true;
            html+=spec('Lab SVG · same kern + cpsp',drawText(text,64)); html+='</div>';
          }
          if(kind==='all-caps') html+=`<div style="font:48px After;font-feature-settings:'cpsp' 1">LA LY LT TA AV AW AY PA FA VA RT</div>`;
          panel.innerHTML=html; document.body.append(panel);
          return document.fonts.ready.then(()=>true);
        }""", dict(cut=cut, samples=samples, faces=faces, kind=kind))
        page.locator('#title-proof').screenshot(path=str(directory/f'{cut}-{kind}.png'))


def verify(fonts, lab, report_path=None, proof_dir=None, baseline=None):
    report = dict(gate_percent=.5, sizes_px=[48, 96, 192], samples=list(SAMPLES), cuts={}, flags=[])
    with sync_playwright() as runtime:
        browser = runtime.chromium.launch()
        page = browser.new_page(viewport=dict(width=1760, height=1100))
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(lab.resolve().as_uri())
        page.wait_for_function('typeof SPACING_EXPORTS !== "undefined" && document.querySelector("#presets button")')
        for cut in CUTS:
            font_file = fonts/cut/f'SEIHouseDisplay-{cut.title()}.otf'
            spacing = page.evaluate('(cut)=>spacingForCut(PRESETS.find(p=>p.name.toLowerCase()===cut),SPACING_EXPORTS)', cut)
            if spacing['otf_sha256'] != hashlib.sha256(font_file.read_bytes()).hexdigest():
                report['flags'].append(dict(kind='stale-spacing-export', cut=cut))
            rows = page.evaluate("""({cut,samples,sizes}) => {
              CUT=JSON.parse(JSON.stringify(PRESETS.find(p=>p.name.toLowerCase()===cut))); renderAll();
              const panel=document.createElement('div'); panel.style.cssText='position:absolute;left:0;width:max-content';
              document.body.append(panel); const rows=[];
              for(const cpsp of [false,true]) for(const size of sizes) for(const text of samples){
                $('cpsp').checked=cpsp; panel.innerHTML=drawText(text,size);
                const run=panel.firstElementChild; run.style.width='max-content';run.style.flexWrap='nowrap';
                rows.push({text,size,cpsp,lab_px:run.getBoundingClientRect().width});
              }
              panel.remove(); return rows;
            }""", dict(cut=cut, samples=SAMPLES, sizes=report['sizes_px']))
            with TTFont(font_file) as font, TTFont(font_file.with_suffix('.woff2')) as web:
                if baseline:
                    # Audit file tables before the shaping helper serializes a decompressed face.
                    with TTFont(baseline/cut/font_file.name) as original:
                        old, new = table_hashes(original), table_hashes(font)
                        changed = sorted(tag for tag in set(old)|set(new) if old.get(tag)!=new.get(tag))
                        if changed != ['GPOS'] or cff_programs(original)!=cff_programs(font):
                            report['flags'].append(dict(kind='display-outline-metric-preservation', cut=cut, changed_tables=changed))
                report['flags'].extend(dict(cut=cut, **flag) for flag in feature_flags(font, spacing))
                for row in rows:
                    actual = shape(font, row['text'], cpsp=row['cpsp'])
                    delivered = shape(web, row['text'], cpsp=row['cpsp'])
                    if actual != delivered:
                        report['flags'].append(dict(kind='web-title-shaping', cut=cut, text=row['text']))
                    built = sum(glyph[1] for glyph in actual)*row['size']/font['head'].unitsPerEm
                    flags, difference = width_flags(row['lab_px'], built, cut=cut,
                                                     text=row['text'], cpsp=row['cpsp'], size=row['size'])
                    report['flags'].extend(flags)
                    row.update(font_px=built, difference_percent=difference)
                pairs = {pair: (sum(row[1] for row in shape(font, pair, cpsp=False))-
                         sum(row[1] for row in shape(font, pair, kern=False, cpsp=False)))/2
                         for pair in TITLE_PAIRS}
            report['cuts'][cut] = dict(policy=spacing['policy'], capital_space_per_1000=spacing['capitalSpace'],
                measurements=len(rows), max_difference_percent=max(row['difference_percent'] for row in rows),
                title_pairs_per_1000=pairs, widths=rows)
            print(f"{cut.title()}: {len(rows)} title widths, max error {report['cuts'][cut]['max_difference_percent']:.4f}%")
            if proof_dir:
                proof_dir.mkdir(parents=True, exist_ok=True)
                render_proofs(page, cut, proof_dir, fonts, baseline)
        # A geometry edit invalidates compiled spacing; naming alone does not.
        draft = page.evaluate("""() => {
          CUT=JSON.parse(JSON.stringify(PRESETS[0])); CUT.name='Renamed'; renderAll();
          const renamed=!!spacingForCut(CUT,SPACING_EXPORTS);
          CUT.weight++; renderAll();
          return {renamed,edited:!!spacingForCut(CUT,SPACING_EXPORTS),disabled:$('cpsp').disabled};
        }""")
        if draft != dict(renamed=True, edited=False, disabled=True):
            report['flags'].append(dict(kind='draft-spacing-invalidation', actual=draft))
        report['page_errors'] = errors
        report['flags'].extend(dict(kind='lab-page-error', error=error) for error in errors)
        browser.close()
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f"Title-spacing gate: {len(report['flags'])} flags")
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fonts', type=Path, default=ROOT/'display/fonts')
    parser.add_argument('--lab', type=Path, default=ROOT/'display/lab/index.html')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--proof-dir', type=Path)
    parser.add_argument('--baseline', type=Path)
    args = parser.parse_args()
    raise SystemExit(bool(verify(args.fonts, args.lab, args.report, args.proof_dir, args.baseline)['flags']))
