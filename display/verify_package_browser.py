"""Exercise the actual packed consumer's DOM/React players, not source aliases."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from threading import Thread
from playwright.sync_api import sync_playwright


def verify(directory):
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=directory))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch();page=browser.new_page();errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{server.server_port}/')
            page.wait_for_function('document.querySelector("[data-living-title-status=ready]")',timeout=60000)
            assert page.locator('#react [role=img]').get_attribute('aria-label')=='SEN'
            # Prop changes cancel superseded work; errors recover and leave a readable label.
            page.evaluate('setTitle("SEA")')
            page.wait_for_function('document.querySelector("[data-living-title-status=preparing]")')
            page.evaluate('setTitle("NOVELEXPANDED")')
            page.wait_for_function('document.querySelector("#react [role=img]")?.getAttribute("aria-label")==="NOVELEXPANDED"',timeout=60000)
            page.evaluate('setTitle("NOVELEXPANDED","invalid")')
            page.wait_for_function('document.querySelector("[data-living-title-status=error]")')
            assert page.locator('#react').inner_text()=='NOVELEXPANDED'
            page.evaluate('setTitle("NOVELEXPANDED","#ffffff")')
            page.wait_for_function('document.querySelector("[data-living-title-status=ready]")')
            page.evaluate('''async()=>{
              const a=await api.createTitleScene({title:'SEA',cut:'Soft'});
              const b=await api.createTitleScene({title:'SEN',cut:'Ink'});
              window.source={sample:()=>1};window.one=api.createTitlePlayer(document.getElementById('one'),a,{source});
              window.two=api.createTitlePlayer(document.getElementById('two'),b,{source});
            }''')
            ids=page.locator('svg [id]').evaluate_all('(nodes)=>nodes.map(n=>n.id)')
            assert len(ids)==len(set(ids)), 'Duplicate clip IDs across players'
            page.evaluate('one.pause()');before=page.evaluate('one.getState().elapsed');page.wait_for_timeout(120)
            assert before==page.evaluate('one.getState().elapsed')
            page.evaluate('one.seek(12);one.setSource({sample:()=>NaN})')
            assert page.evaluate('one.getState().pose')==0
            page.evaluate('one.setSource({sample:()=>{throw Error("invalid signal")}})')
            assert page.evaluate('one.getState().pose')==0
            page.evaluate('one.setSource(source)')
            assert page.evaluate('one.getState().pose')==59
            page.emulate_media(reduced_motion='reduce')
            # Let preference-change events dispatch before polling MediaQueryList getters.
            page.wait_for_timeout(150)
            state=page.evaluate('[one.getState(),two.getState()]')
            assert all(s['pose']==0 for s in state),state
            assert page.evaluate('one.getState().reducedMotion')
            page.emulate_media(reduced_motion='no-preference')
            page.wait_for_timeout(150)
            assert page.evaluate('one.getState().pose')==59
            page.evaluate('one.dispose();one.dispose();two.dispose();unmount()')
            assert page.locator('#one svg,#two svg,#react svg').count()==0
            assert not errors,errors
            assert page.evaluate('window.errors.length')==1
            browser.close()
        print('Packed browser: StrictMode, prop cancellation, errors/recovery, unique clips, pause/seek, signals, reduced motion, disposal passed')
    finally:
        server.shutdown();server.server_close()


if __name__=='__main__':verify(str(Path(sys.argv[1]).resolve()))
