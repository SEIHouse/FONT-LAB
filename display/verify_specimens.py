"""Check native specimen/font widths, every built style, and 360–430px layouts."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from threading import Thread

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from playwright.sync_api import sync_playwright
from display.letter_alternates import SET_NAMES
from display.production import ROOT, read_manifest

SAMPLES = ('LA LY LT TA AV AW AY PA FA VA RT', 'AFTER HOURS / HARD LIGHT', 'TURN IT UP.',
           'First light. A little further', 'Velvet radio / Way out west', 'ag RKk MW y G Q 469',
           'ÁV Ŵ Ý Ķ ģ ấ', 'ΑΥ ΚΜ / КМ Ќ ў')


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def verify(manifest_file, report_dir, *, proof_dir=None):
    manifest, root = read_manifest(manifest_file)
    directory = Path(report_dir)
    directory.mkdir(parents=True, exist_ok=True)
    if proof_dir:
        Path(proof_dir).mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(root)))
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    report = dict(flags=[], widths=0, layouts=0, device_scale_factor=2, max_width_difference_percent=0, cuts={})
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport=dict(width=1200, height=900), device_scale_factor=2)
            page.on('pageerror', lambda error: report['flags'].append(dict(kind='specimen-script', reason=str(error))))
            page.on('response', lambda response: report['flags'].append(dict(kind='specimen-http', url=response.url, status=response.status))
                    if response.status >= 400 else None)
            for cut in manifest['cuts']:
                page.goto(f'http://127.0.0.1:{server.server_port}/{cut["specimen"]}', wait_until='networkidle')
                summary = dict(styles=[], widths=0, layouts=0)
                for face in cut['styles']:
                    page.select_option('#style', face['label'])
                    page.locator('details').evaluate('(element) => element.open=true')
                    page.evaluate('document.fonts.ready')
                    summary['styles'].append(face['label'])
                    # Load the built OTF as an independent reference face. Comparing
                    # native deliveries in one browser keeps platform grid fitting
                    # identical; verify_production separately checks raw GPOS/hmtx.
                    reference_url = f'http://127.0.0.1:{server.server_port}/{face["otf"]}'
                    page.evaluate('''async face => {
                      for (const old of document.fonts) if (old.family==='SpecimenReference') document.fonts.delete(old);
                      const reference = new FontFace('SpecimenReference', `url("${face.url}")`,
                        {weight:String(face.weight),style:face.slope});
                      await reference.load(); document.fonts.add(reference);
                    }''', dict(url=reference_url, weight=face['weight'], slope=face['slope']))
                    for mode in ({'cpsp':True}, {'cpsp':False}, {'cpsp':True, **dict.fromkeys(SET_NAMES, True)}):
                        page.evaluate('''mode => {
                          document.querySelectorAll('[data-feature]').forEach(input => {
                            input.checked = Boolean(mode[input.dataset.feature]);
                            input.dispatchEvent(new Event('change'));
                          });
                        }''', mode)
                        widths = page.evaluate('''async args => {
                          const anchor = document.querySelector('.cover-title');
                          const computed = getComputedStyle(anchor);
                          await document.fonts.load(`${computed.fontStyle} ${computed.fontWeight} 80px ${computed.fontFamily}`, args.samples.join(''));
                          const expectedFeatures = ['cpsp','ss01','ss02','ss03','ss04','ss05','ss06','ss07','ss08']
                            .map(tag => `"${tag}" ${Number(Boolean(args.mode[tag]))}`).join(', ');
                          function measure(text, reference) {
                            const span = document.createElement('span'); span.className = 'cut'; span.textContent = text;
                            span.style.cssText = 'position:absolute;left:0;top:0;font-size:80px;white-space:pre;';
                            if (reference) {
                              span.style.fontFamily = 'SpecimenReference'; span.style.fontWeight = args.face.weight;
                              span.style.fontStyle = args.face.slope; span.style.fontFeatureSettings = expectedFeatures;
                            }
                            document.body.append(span); const range = document.createRange(); range.selectNodeContents(span);
                            const width = range.getBoundingClientRect().width; span.remove(); return width;
                          }
                          return args.samples.map(text => {
                            return {browser:measure(text,false),font:measure(text,true)};
                          });
                        }''', dict(samples=SAMPLES, mode=mode, face=face))
                        for text, row in zip(SAMPLES, widths):
                            width, expected = row['browser'], row['font']
                            difference = abs(width-expected)/expected*100
                            report['widths'] += 1
                            summary['widths'] += 1
                            report['max_width_difference_percent'] = max(report['max_width_difference_percent'], difference)
                            if difference >= .5:
                                report['flags'].append(dict(cut=cut['slug'], style=face['label'], kind='specimen-width', text=text,
                                                           features=mode, browser=width, font=expected, difference_percent=difference))
                        for viewport in (360, 375, 390, 414, 430):
                            page.set_viewport_size(dict(width=viewport, height=900))
                            page.evaluate('document.fonts.ready')
                            overflow = page.evaluate('''() => {
                              const width = innerWidth;
                              const elements = [...document.querySelectorAll('header, main, .intro, .style-control, .controls, .feature-grid, .specimen-grid, .cut, li, .downloads, footer')]
                                .filter(element => element.getClientRects().length)
                                .filter(element => {const r=element.getBoundingClientRect(); return r.left < -.5 || r.right > width+.5;})
                                .map(element => element.className || element.tagName);
                              return {width:Math.max(document.documentElement.scrollWidth, document.body.scrollWidth), elements};
                            }''')
                            report['layouts'] += 1
                            summary['layouts'] += 1
                            if overflow['width'] > viewport or overflow['elements']:
                                report['flags'].append(dict(cut=cut['slug'], style=face['label'], kind='specimen-overflow',
                                                           viewport=viewport, features=mode, **overflow))
                        page.set_viewport_size(dict(width=1200, height=900))
                page.select_option('#style', 'Regular')
                page.evaluate('''() => {document.querySelectorAll('[data-feature]').forEach(input => {
                  input.checked=input.dataset.feature==='cpsp';input.dispatchEvent(new Event('change'));
                });}''')
                page.evaluate('document.fonts.ready')
                if proof_dir:
                    page.screenshot(path=str(Path(proof_dir)/(cut['slug']+'.png')), full_page=True)
                report['cuts'][cut['slug']] = summary
                print(f'Specimen {cut["name"]}: {summary["widths"]} widths, {summary["layouts"]} phone layouts', flush=True)
            page.goto(f'http://127.0.0.1:{server.server_port}/site/display/index.html', wait_until='networkidle')
            for viewport in (360, 390, 430):
                page.set_viewport_size(dict(width=viewport, height=900))
                width = page.evaluate('Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)')
                if width > viewport:
                    report['flags'].append(dict(kind='collection-overflow', viewport=viewport, width=width))
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
    target = directory/'specimens.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Specimen gate: {len(report["flags"])} flags, max width difference {report["max_width_difference_percent"]:.4f}% -> {target}', flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=HERE/'production-manifest.json')
    parser.add_argument('--report-dir', type=Path, default=ROOT/'dist/display-specimen-gates')
    parser.add_argument('--proof-dir', type=Path)
    args = parser.parse_args()
    report = verify(args.manifest, args.report_dir, proof_dir=args.proof_dir)
    raise SystemExit(bool(report['flags']))
