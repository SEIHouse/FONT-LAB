"""Build a private installable Living Titles runtime from certified shared sources."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from display.living_build import engine_factory, profiles_for_lab, motion_digest, fixture_digest
from display.title_spacing import spacing_settings

PACKAGE=ROOT/'packages/living-titles'


def build():
    """Rebuild the private artifact from current certified inputs and no stale files."""
    profiles=profiles_for_lab()['profiles']
    if len(profiles)!=4 or not all(p.get('certified') for p in profiles):
        raise ValueError('Runtime delivery requires all four current motion certificates')
    cuts,spacing=[],[]
    for slug in ('soft','edge','ink','wide'):
        cut=json.loads((ROOT/f'display/cuts/{slug}.json').read_text(encoding='utf-8'))
        record=json.loads((ROOT/f'display/spacing_{slug}.json').read_text(encoding='utf-8'))
        font=ROOT/f'display/fonts/{slug}/SEIHouseDisplay-{cut["name"]}.otf'
        if (record.get('schema')!=1 or record['settings']!=spacing_settings(cut)
                or record['built_alternates']!=cut['alternates']
                or record['otf_sha256']!=hashlib.sha256(font.read_bytes()).hexdigest()):
            raise ValueError(f'Stale compiled spacing for {slug}')
        cuts.append(cut);spacing.append(record)
    out=PACKAGE/'dist'
    resolved=out.resolve()
    if resolved.parent!=PACKAGE.resolve() or resolved.name!='dist':
        raise ValueError('Package output must remain inside its own dist directory')
    # Validate the complete tree before removing or writing any package payload.
    previous=list(out.rglob('*'))
    for old in previous:
        if old.is_symlink() or old.is_junction() or not old.resolve().is_relative_to(resolved):
            raise ValueError('Package output must not contain symlinks, junctions or external paths')
    # Keep empty OneDrive-backed directories, but remove every previous payload file.
    # npm omits empty directories; a deleted/renamed source can never enter the archive.
    for old in previous:
        if old.is_file():
            if not old.resolve().is_relative_to(resolved):
                raise ValueError('Previous package files must stay inside dist')
            old.unlink()
    out.mkdir(parents=True,exist_ok=True)
    def output_path(relative):
        """Reject redirected output paths before each generated-file write."""
        path=out/relative
        if path.is_symlink() or path.is_junction() or not path.resolve().is_relative_to(resolved):
            raise ValueError('Generated package files must stay inside dist')
        return path
    source=('/* Generated from the shared Reader/Display source. Do not edit. */\n'
            +engine_factory()+(ROOT/'display/living.js').read_text(encoding='utf-8')
            +'\nconst DATA='+json.dumps({'cuts':cuts,'spacing':spacing,'profiles':profiles},ensure_ascii=True,separators=(',',':'))
            +';\nexport {createLivingEngine,LivingTitles,DATA};\n')
    output_path('engine.js').write_text(source,encoding='utf-8',newline='\n')
    for file in (PACKAGE/'src').iterdir():
        if file.suffix in ('.js','.ts'):
            output_path(file.name).write_text(file.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
    fonts=output_path('fonts');fonts.mkdir(exist_ok=True)
    manifest=json.loads((ROOT/'display/production-manifest.json').read_text(encoding='utf-8'))
    deliveries={asset['path']:asset for record in manifest['cuts'] for style in record['styles'] for asset in style['assets']}
    css=[]
    for cut in cuts:
        name=cut['name'];file=f'SEIHouseDisplay-{name}.woff2'
        path=f'display/fonts/{name.lower()}/{file}';font_bytes=(ROOT/path).read_bytes()
        if path not in deliveries or hashlib.sha256(font_bytes).hexdigest()!=deliveries[path]['sha256']:
            raise ValueError(f'Stale production WOFF2 delivery for {name}')
        output_path(f'fonts/{file}').write_bytes(font_bytes)
        css.append(f"@font-face{{font-family:'SEIHouse Display {name}';font-style:normal;font-weight:400;font-display:swap;src:url('./fonts/{file}') format('woff2');}}")
    output_path('fonts.css').write_text('\n'.join(css)+'\n',encoding='utf-8',newline='\n')
    output_path('provenance.json').write_text(json.dumps({'schema':1,'source_sha256':motion_digest(),
        'fixture_sha256':fixture_digest(),'profiles':[p['id'] for p in profiles],
        'fonts':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(fonts.iterdir())}},indent=2)+'\n',encoding='utf-8',newline='\n')
    (PACKAGE/'SANS-LICENSE.txt').write_text((ROOT/'LICENSE').read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
    print(f'Living Titles package: four reviewed cuts, shared vectors, DOM/React players -> {out.relative_to(ROOT)}')


if __name__=='__main__':build()
