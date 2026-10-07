"""Generate reviewed per-cut title proofs through the Lab's prepared frame renderer."""
import html
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
from playwright.sync_api import sync_playwright
from display.living_build import profiles_for_lab


def build():
    """Write transparent SVGs and an accessible responsive gallery for all certified cuts."""
    profiles=profiles_for_lab()['profiles']
    if len(profiles)!=4 or not all(profile.get('certified') for profile in profiles):
        raise ValueError('All four profiles must be certified before publishing animated proofs')
    destination=ROOT/'docs/proofs/display-step6';destination.mkdir(parents=True,exist_ok=True)
    cards=[]
    with sync_playwright() as p:
        browser=p.chromium.launch();page=browser.new_page()
        page.goto((HERE/'lab/index.html').as_uri());page.wait_for_function('LivingTitleUI.inspect().prepared')
        for profile in profiles:
            cut=profile['cut'];slug=cut.lower()
            page.locator(f'#presets [data-p="{cut}"]').click()
            for kind,text,cpsp in (('caps','LA AV THE LAST LOTUS',True),('mixed','A Quiet Bloom',False)):
                page.locator('#t-title').fill(text);page.locator('#cpsp').set_checked(cpsp)
                page.locator('#lt-prepare').click();page.wait_for_function('LivingTitleUI.inspect().prepared && !LivingTitleUI.inspect().busy')
                svg=page.evaluate('LivingTitles.animatedSVG(LivingTitleUI.snapshot(),"#eef1f6",1080)')
                file=f'{slug}-{kind}.svg';(destination/file).write_text(svg+'\n',encoding='utf-8',newline='\n')
                cards.append(f'<article><h2>{html.escape(cut)} · {kind}</h2><p>{html.escape(profile["id"])} · '
                             f'+{profile["thickness"]*100}% thickness / +{profile["slant"]}° slant / +{profile["penAngle"]}° pen · '
                             f'{"cpsp on" if cpsp else "cpsp off"}</p><img src="{file}" loading="lazy" alt="{html.escape(text)} in {cut}">'
                             f'<a href="{file}" download>Download transparent animated SVG</a></article>')
        browser.close()
    (destination/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Living Title proofs · SEIHouse</title>
<style>*{box-sizing:border-box}body{margin:0;background:#0f1115;color:#eef1f6;font:16px/1.5 system-ui}
main{max-width:1200px;margin:auto;padding:20px}a{color:#a6b5ff}article{border:1px solid #3c4457;border-radius:12px;padding:16px;margin:18px 0}
h2{font-size:20px}p{overflow-wrap:anywhere}img{display:block;width:100%;height:auto;max-height:360px;margin:20px 0}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto}}</style>
<main><a href="../../../display/lab/index.html">Open the Display Lab</a><h1>Living Titles · reviewed cuts</h1>
<p>120 BPM · four beats · two seconds · 30 FPS · anchored compiled spacing · 1080 px.
These self-contained SVG images animate declaratively and show a resting title with reduced motion.</p>
'''+''.join(cards)+'</main></html>\n',encoding='utf-8',newline='\n')
    print(f'Living proofs: {len(cards)} SVGs -> {destination.relative_to(ROOT)}')


if __name__=='__main__':build()
