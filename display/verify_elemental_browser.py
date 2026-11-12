"""Exercise the packed @seihouse/elemental-title consumer in real Chromium."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from threading import Thread
from playwright.sync_api import sync_playwright


def verify(directory):
    """Serve the installed consumer and verify rendering, moments, signatures, and reduced motion."""
    server = ThreadingHTTPServer(
        ('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=directory)
    )
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': 900, 'height': 600})
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{server.server_port}/')
            page.wait_for_function(
                'document.querySelector("#lightning .elemental-title__ink[data-running=\\"true\\"] svg")',
                timeout=30000,
            )
            assert page.get_by_role('heading', name='Kept Reading', exact=True).count() == 1
            assert page.get_by_role('heading', name='Still Waters', exact=True).count() == 1
            assert page.locator('#lightning .elemental-title__text').inner_text() == 'Kept Reading'
            assert page.locator('#water .elemental-title__text').inner_text() == 'Still Waters'

            # Trigger an explicit strike and verify onMoment reports cues & beats
            page.evaluate('window.playStrike()')
            page.wait_for_function(
                'window.moments.some((m) => m.id === "strike" && m.explicit === true)',
                timeout=10000,
            )

            # Trigger Quill Stormwrit signature and verify front/back SVG scene renders & reports
            page.evaluate('window.playSignature("quill/stormwrit")')
            page.wait_for_function(
                'window.moments.some((m) => m.id === "signature" && m.signature?.id === "quill/stormwrit")',
                timeout=10000,
            )
            assert page.locator('#lightning [data-signature="quill/stormwrit"]').count() == 1

            # Reduced motion pauses live running state while keeping static element frame
            page.emulate_media(reduced_motion='reduce')
            page.wait_for_timeout(150)
            assert (
                page.locator('#lightning .elemental-title__ink').get_attribute('data-running')
                == 'false'
            )
            assert page.locator('#lightning svg .et-frame[data-slot="still"]').count() >= 1

            # Unmount cleans up all DOM/SVG nodes cleanly
            page.emulate_media(reduced_motion='no-preference')
            page.evaluate('window.unmount()')
            assert page.locator('#root svg').count() == 0
            assert not errors, errors
            browser.close()
        print(
            'Packed browser: StrictMode, Lightning/Water SVG stage, strike, Quill Stormwrit signature, reduced motion, disposal passed'
        )
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    verify(str(Path(sys.argv[1]).resolve()))
