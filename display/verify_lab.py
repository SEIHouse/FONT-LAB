"""Check the local Display Lab with the same Chromium runtime used by the builder.

Serve the repo with `python -m http.server 8766 --bind 127.0.0.1`, then run
`python -X utf8 display/verify_lab.py`. No saved drafts are changed.
"""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent


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
            assert f'button "{cut}"' in snapshot
            button = page.get_by_role('button', name=cut, exact=True)
            button.click()
            assert button.get_attribute('aria-pressed') == 'true'
            assert page.locator('#cutname').input_value() == cut
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
        page.set_viewport_size(dict(width=390, height=844))
        page.reload()
        report['mobile'] = dict(width=390, cut=page.locator('#cutname').input_value())
        assert page.get_by_role('button', name='Soft', exact=True).is_visible()
        assert not errors, errors
        report['page_errors'] = errors
        (output/'lab.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        browser.close()
        print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8766/display/lab/index.html')
    parser.add_argument('--proof-dir', type=Path, default=ROOT/'dist/display-lab-proofs')
    args = parser.parse_args()
    verify(args.url, args.proof_dir)
