"""Check the local Display Lab with the same Chromium runtime used by the builder.

Run `python -X utf8 display/verify_lab.py` for the built local page, or pass
`--url` to check a served Lab. No saved drafts are changed.
"""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
MOBILE_WIDTHS = (360, 375, 390, 414, 430)


def layout_snapshot(page):
    """Measure the document and visible control/specimen boxes without hiding overflow."""
    return page.evaluate("""() => ({
      viewport:innerWidth, document:document.documentElement.scrollWidth,
      body:document.body.scrollWidth,
      outside:[...document.querySelectorAll('body *')].filter(el=>
        el.namespaceURI==='http://www.w3.org/1999/xhtml' || el.matches('.run > svg'))
        .filter(el=>el.getClientRects().length && getComputedStyle(el).visibility!=='hidden')
        .map(el=>{const box=el.getBoundingClientRect(); return {
          tag:el.tagName,id:el.id,left:box.left,right:box.right,width:box.width};})
        .filter(box=>box.width && (box.left < -1 || box.right > innerWidth+1))
    })""")


def layout_flags(snapshot):
    """Fail both a wide page and elements leaking outside the viewport."""
    flags = []
    if max(snapshot['document'], snapshot['body']) > snapshot['viewport']:
        flags.append(dict(kind='mobile-document-overflow', **snapshot))
    elif snapshot['outside']:
        flags.append(dict(kind='mobile-element-overflow', **snapshot))
    return flags


def verify_mobile(page, output):
    """Gate every preset at 360–430px, default and long titles, cpsp and crossed W."""
    rows, flags = [], []
    for width in MOBILE_WIDTHS:
        page.set_viewport_size(dict(width=width, height=844))
        page.reload()
        page.locator('#save:not([disabled])').wait_for()
        for cut in ('Soft', 'Edge', 'Ink', 'Wide'):
            page.get_by_role('button', name=cut, exact=True).click()
            if page.locator('#alt-W').input_value() != 'plain':
                flags.append(dict(kind='lab-w-default', cut=cut, width=width))
            for mode in ('default', 'long-title', 'crossed-cpsp'):
                if mode == 'long-title':
                    page.locator('#t-title').fill('W'*60)
                    page.locator('#t-artist').fill('W'*40)
                    page.locator('#t-tracks').fill('W'*80+'\nThe Wide World')
                elif mode == 'crossed-cpsp':
                    page.locator('#alt-W').select_option('crossed')
                    page.locator('#cpsp').check()
                # Resize/input renders are scheduled by requestAnimationFrame.
                page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                snapshot = layout_snapshot(page)
                row = dict(width=width, cut=cut, mode=mode, **snapshot)
                rows.append(row)
                flags.extend(dict(cut=cut, mode=mode, **flag) for flag in layout_flags(snapshot))
                if width == 390 and mode == 'default':
                    page.screenshot(path=str(output/f'lab-{cut.lower()}-390.png'), full_page=True)
            page.locator('#t-title').fill('The Last Lotus')
            page.locator('#t-artist').fill('SENSEI')
            page.locator('#t-tracks').fill('Pavilion\nRoots Through Ruin\nSkybound\nOath (Interlude)\nBloom')
            page.locator('#cpsp').uncheck()
    return dict(widths=list(MOBILE_WIDTHS), measurements=len(rows), rows=rows, flags=flags)


def verify(url, output):
    """Exercise all presets, generate all live glyphs, and save 400px specimens."""
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as runtime:
        browser = runtime.chromium.launch()
        page = browser.new_page(viewport=dict(width=1440, height=1080))
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url)
        snapshot = page.locator('body').aria_snapshot()
        report = {}
        for cut in ('Soft', 'Edge', 'Ink', 'Wide'):
            if f'button "{cut}"' not in snapshot:
                raise ValueError('Missing Display preset: '+cut)
            button = page.get_by_role('button', name=cut, exact=True)
            button.click()
            if button.get_attribute('aria-pressed') != 'true':
                raise ValueError('Display preset was not selected: '+cut)
            if page.locator('#cutname').input_value() != cut:
                raise ValueError('Display cut name did not update: '+cut)
            report[cut] = page.evaluate("""() => {
              const result = {glyphs:Object.keys(G).length, instances:0, sizes:[300,400,800]};
              for(const ch of Object.keys(G)) for(const size of result.sizes){
                const svg = drawWord(ch, size);
                if(/NaN|Infinity|undefined|stroke-linecap="square"/.test(svg)) throw new Error(ch+': invalid stroke');
                if(!['\u2009','\u202f'].includes(ch) && !svg.includes('<path') && !svg.includes('<circle')) throw new Error(ch+': missing outline');
                result.instances++;
              }
              const panel = document.createElement('div'); panel.id = 'shape-proof';
              panel.style.cssText = 'width:3200px;background:white;color:black;padding:30px';
              panel.innerHTML = '<p style="font:24px sans-serif">'+CUT.name+' live SVG at 400px</p>'+drawText('K R a y W k e s',400);
              document.querySelector('#shape-proof')?.remove(); document.body.append(panel);
              return result;
            }""")
            page.locator('#shape-proof').screenshot(path=str(output/f'lab-{cut.lower()}-400.png'))
        report['mobile'] = verify_mobile(page, output)
        report['page_errors'] = errors
        report['flags'] = report['mobile']['flags'] + [dict(kind='lab-page-error', error=error) for error in errors]
        (output/'lab.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        browser.close()
        print(f"Lab: {sum(report[cut]['instances'] for cut in ('Soft','Edge','Ink','Wide'))} glyph instances, "
              f"{report['mobile']['measurements']} mobile layouts, {len(report['flags'])} flags")
        return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    location = parser.add_mutually_exclusive_group()
    location.add_argument('--url')
    location.add_argument('--lab', type=Path, default=ROOT/'display/lab/index.html')
    parser.add_argument('--proof-dir', type=Path, default=ROOT/'dist/display-lab-proofs')
    args = parser.parse_args()
    raise SystemExit(bool(verify(args.url or args.lab.resolve().as_uri(), args.proof_dir)['flags']))
