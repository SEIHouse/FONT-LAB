"""One cut/style inventory for production builds, gates and specimens."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re

from font_builder import WCLASS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load_cuts(directory=HERE/'cuts'):
    """Discover every JSON cut, rejecting collisions before any fonts are written."""
    cuts, slugs, postscript_stems = [], set(), set()
    for file in sorted(Path(directory).glob('*.json')):
        settings = json.loads(file.read_text(encoding='utf-8'))
        name = settings.get('name', '')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9]*(?:[ -][A-Za-z0-9]+)*', name):
            raise ValueError(f'{file}: name must use letters, digits, single spaces or hyphens')
        slug = name.lower().replace(' ', '-')
        if slug in slugs:
            raise ValueError(f'{file}: duplicate cut slug {slug}')
        stem = name.replace(' ', '').lower()
        if stem in postscript_stems:
            raise ValueError(f'{file}: duplicate PostScript family identity {name}')
        slugs.add(slug)
        postscript_stems.add(stem)
        # Validate opt-in delivery settings up front, without changing the drawing JSON.
        plan = style_plan(settings)
        if slug in {'con','prn','aux','nul',*[f'com{i}' for i in range(1,10)],*[f'lpt{i}' for i in range(1,10)]}:
            raise ValueError(f'{file}: cut name is a reserved Windows filename')
        if any(len('SEIHouseDisplay'+name.replace(' ','')+'-'+face['label'])>63 for face in plan):
            raise ValueError(f'{file}: PostScript names must fit in 63 characters, including style')
        cuts.append(dict(file=file, name=name, slug=slug, settings=settings))
    if not cuts:
        raise ValueError('No cut JSON files found in '+str(directory))
    return cuts


def number(value, label, lower, upper):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not lower <= value <= upper:
        raise ValueError(f'{label} must be a finite number from {lower} to {upper}')
    return value


def style_plan(settings):
    """Preserve Regular and derive optional thickness/slant from that same cut."""
    config = settings.get('production', {})
    if not isinstance(config, dict) or set(config)-{'weights', 'oblique'}:
        raise ValueError('production supports only weights and oblique')
    weights = config.get('weights', {})
    if not isinstance(weights, dict):
        raise ValueError('production.weights must map style names to thickness multipliers')
    drawing = deepcopy(settings)
    drawing.pop('production', None)
    number(drawing['weight'], 'weight', 1, 250)
    plan = [dict(label='Regular', style='Regular', oblique=False, settings=drawing)]
    for style, factor in sorted(weights.items(), key=lambda row: WCLASS.get(row[0], 0)):
        if style not in WCLASS or style == 'Regular':
            raise ValueError('Unknown extra weight style: '+str(style))
        number(factor, f'production.weights.{style}', .5, 1.5)
        if (WCLASS[style] < 400) != (factor < 1) or factor == 1:
            raise ValueError(f'{style} must be lighter/heavier than Regular as its name indicates')
        variant = deepcopy(drawing)
        variant['weight'] = drawing['weight'] * factor
        number(variant['weight'], style+' thickness', 1, 250)
        plan.append(dict(label=style, style=style, oblique=False, settings=variant))
    if 'oblique' in config:
        angle = number(config['oblique'], 'production.oblique added degrees', 1, 20)
        variant = deepcopy(drawing)
        variant['slant'] = drawing.get('slant', 0) + angle
        number(variant['slant'], 'total oblique angle', 1, 25)
        plan.append(dict(label='Oblique', style='Regular', oblique=True, settings=variant))
    return plan


def font_path(fonts, cut, label):
    folder = Path(fonts)/cut['slug']
    if label != 'Regular':
        folder /= label
    suffix = '' if label == 'Regular' else '-'+label
    return folder/f'SEIHouseDisplay-{cut["name"].replace(" ", "")}{suffix}.otf'


def asset_record(path, root):
    path, root = Path(path), Path(root)
    return dict(path=path.relative_to(root).as_posix(), bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def read_manifest(file):
    """Manifest paths are relative to a bundle root, never arbitrary filesystem paths."""
    file = Path(file).resolve()
    manifest = json.loads(file.read_text(encoding='utf-8'))
    root = file.parent.parent  # <bundle>/display/production-manifest.json
    if manifest.get('version') != 1 or not manifest.get('cuts'):
        raise ValueError('Unsupported or empty Display production manifest')
    for cut in manifest['cuts']:
        for face in cut['styles']:
            for asset in face['assets']:
                path = (root/asset['path']).resolve()
                if not path.is_relative_to(root):
                    raise ValueError('Manifest asset escapes its bundle: '+asset['path'])
    return manifest, root
