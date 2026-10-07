"""Browser gates for the silent NovelExpanded title study and future signal seam."""
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PROOFS = ROOT/'docs/proofs/novel-expanded-mock'


def verify():
    """Exercise all cut/phone states and authoring edge cases through Chromium."""
    PROOFS.mkdir(parents=True, exist_ok=True)
    errors, cases = [], []
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1200, 'height': 1100})
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}/display/novel-expanded/')
        page.wait_for_function('window.NovelExpandedMock?.inspect().ready && !NovelExpandedMock.inspect().busy', timeout=120000)
        for cut in ('Soft', 'Edge', 'Ink', 'Wide'):
            page.locator(f'#cuts [data-cut="{cut}"]').click()
            page.wait_for_function('NovelExpandedMock.inspect().ready && !NovelExpandedMock.inspect().busy', timeout=120000)
            page.evaluate('NovelExpandedMock.setMotionSource({sample:()=>0})')
            zero = page.locator('#header-art').inner_html()
            bounds = page.evaluate('NovelExpandedMock.inspect().viewBoxes')
            page.evaluate('NovelExpandedMock.setMotionSource({sample:()=>1})')
            peak = page.locator('#header-art').inner_html()
            assert zero != peak, f'{cut}: no changing letter geometry'
            assert bounds == page.evaluate('NovelExpandedMock.inspect().viewBoxes'), 'Moving canvas'
            page.evaluate('NovelExpandedMock.setMotionSource({sample:()=>NaN})')
            assert zero == page.locator('#header-art').inner_html(), 'Invalid signal must rest'
            page.evaluate('NovelExpandedMock.setMotionSource({sample:()=>{throw Error("invalid")}})')
            assert zero == page.locator('#header-art').inner_html(), 'Failed signal must rest'
            page.evaluate('NovelExpandedMock.setMotionSource({sample:()=>1})')
            for width in (360,375,390,414,430):
                page.set_viewport_size({'width':width,'height':1000})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'{cut}: overflow {width}'
                assert page.locator('#header-art').bounding_box()['width'] > 0
                cases.append({'cut':cut,'width':width,'overflow':False})
            page.set_viewport_size({'width':390,'height':1000})
            page.locator('.phone').screenshot(path=str(PROOFS/f'{cut.lower()}-390.png'))
        # Superseded preparation may never publish a stale cut.
        page.locator('#cuts [data-cut="Soft"]').click()
        page.locator('#cuts [data-cut="Edge"]').click()
        page.wait_for_function('NovelExpandedMock.inspect().cut === "Edge" && !NovelExpandedMock.inspect().busy', timeout=120000)
        assert 'Edge:' in page.locator('#profile').inner_text()
        page.evaluate('NovelExpandedMock.setMotionSource(null)')
        page.locator('#comparison').check()
        assert page.locator('#header-serif').is_visible() and not page.locator('#header-art').is_visible()
        page.locator('#comparison').uncheck()
        page.locator('#placement').select_option('both')
        page.wait_for_function('NovelExpandedMock.inspect().ready && !NovelExpandedMock.inspect().busy', timeout=120000)
        assert page.locator('#hero-art').is_visible()
        page.locator('#play').click()
        elapsed = page.evaluate('NovelExpandedMock.inspect().elapsed')
        page.wait_for_timeout(150)
        assert elapsed == page.evaluate('NovelExpandedMock.inspect().elapsed'), 'Pause clock drift'
        with page.expect_download() as event:
            page.locator('#svg').click()
        svg = Path(event.value.path()).read_text(encoding='utf-8')
        assert '<animate ' in svg and '<script' not in svg and '<title>NOVELEXPANDED</title>' in svg
        with page.expect_download() as event:
            page.locator('#save').click()
        study = json.loads(Path(event.value.path()).read_text(encoding='utf-8'))
        assert study['kind'] == 'novel-expanded-title-study' and study['cut'] == 'Edge'
        page.emulate_media(reduced_motion='reduce')
        page.wait_for_function('document.getElementById("play").disabled && NovelExpandedMock.inspect().pose === 0')
        assert page.evaluate('NovelExpandedMock.inspect().pose') == 0
        assert page.locator('#play').is_disabled()
        page.evaluate('NovelExpandedMock.setMotionSource({sample:()=>1})')
        assert page.evaluate('NovelExpandedMock.inspect().pose') == 0
        page.emulate_media(reduced_motion='no-preference')
        page.wait_for_function('!document.getElementById("play").disabled')
        # Colors edited during yielding preparation must be used at mount time.
        page.evaluate('''()=>{
          const title=document.getElementById('wordmark');title.value='NOVELEXPANDED';
          title.dispatchEvent(new Event('input',{bubbles:true}));
          for(const [id,color] of [['ink','#abcdef'],['hero-ink','#fedcba']]){
            const input=document.getElementById(id);input.value=color;
            input.dispatchEvent(new Event('input',{bubbles:true}));
          }
        }''')
        page.wait_for_function('NovelExpandedMock.inspect().ready && !NovelExpandedMock.inspect().busy', timeout=120000)
        assert page.locator('#header-art svg').get_attribute('color')=='#abcdef'
        assert page.locator('#hero-art svg').get_attribute('color')=='#fedcba'
        page.locator('#ink').fill('#e6cc87');page.locator('#hero-ink').fill('#f4efe6')
        # An unused title may be empty; selecting it must validate and then recover.
        page.locator('#placement').select_option('header')
        page.wait_for_function('!NovelExpandedMock.inspect().busy')
        page.locator('#featured').fill('')
        page.wait_for_function('!NovelExpandedMock.inspect().busy')
        assert page.evaluate('NovelExpandedMock.inspect().ready')
        page.locator('#placement').select_option('both')
        page.wait_for_function('!NovelExpandedMock.inspect().busy')
        assert not page.evaluate('NovelExpandedMock.inspect().ready')
        page.locator('#featured').fill('Defying the Heavens')
        page.wait_for_function('NovelExpandedMock.inspect().ready && !NovelExpandedMock.inspect().busy', timeout=120000)
        page.locator('#placement').select_option('featured')
        page.wait_for_function('!NovelExpandedMock.inspect().busy')
        page.locator('#wordmark').fill('')
        page.wait_for_function('!NovelExpandedMock.inspect().busy')
        assert page.evaluate('NovelExpandedMock.inspect().ready')
        assert page.locator('#hero-art').is_visible()
        assert page.locator('#svg').is_disabled()
        page.locator('#placement').select_option('header')
        page.wait_for_function('!NovelExpandedMock.inspect().busy')
        assert not page.evaluate('NovelExpandedMock.inspect().ready')
        page.locator('#wordmark').fill('NOVELEXPANDED')
        page.wait_for_function('NovelExpandedMock.inspect().ready && !NovelExpandedMock.inspect().busy', timeout=120000)
        page.evaluate('NovelExpandedMock.setMotionSource(null)')
        page.set_viewport_size({'width':1200,'height':1100})
        page.screenshot(path=str(PROOFS/'desktop.png'), full_page=True)
        page.evaluate('NovelExpandedMock.dispose()')
        assert not page.evaluate('NovelExpandedMock.inspect().ready')
        # All media remains local artwork. There is no playback owner in this page.
        assert page.locator('audio,video').count() == 0
        assert not errors, errors
        browser.close()
    server.shutdown();server.server_close()
    report={'phone_states':cases,'flags':errors,'checks':['four changing cuts','fixed canvas','signal validation',
        'superseded preparation','serif/placement','pause','SVG/JSON download','reduced motion','empty title/recovery',
        'unused title/placement recovery','color edits during preparation','dispose','no audio']}
    (PROOFS/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'NovelExpanded mock: {len(cases)} phone/cut states, signal/control/export gates, 0 flags')


if __name__ == '__main__':
    verify()
