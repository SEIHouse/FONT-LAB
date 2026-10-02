"""Build the self-contained reference preview. No network access is needed.

python build_comparison.py [additional-output.html]
Always writes lab/comparison.html; an optional path updates an already open preview.
"""
from pathlib import Path
import base64
import json
import sys

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.boundsPen import BoundsPen

ROOT = Path(__file__).resolve().parent
BASELINE_VERSION = '0.32'
settings = json.loads((ROOT / 'settings.json').read_text(encoding='utf-8'))
weights = {'Light': 300, 'Regular': 400, 'Medium': 500, 'SemiBold': 600, 'Bold': 700}
faces = []
for folder, family in [('fonts', 'Candidate'), (f'old/{BASELINE_VERSION}', 'Baseline')]:
    for style, weight in weights.items():
        for italic in (False, True):
            name = ('Italic' if style == 'Regular' else style + 'Italic') if italic else style
            faces.append((family, str(weight), 'italic' if italic else 'normal',
                          ROOT / folder / f'SEIReader-{name}.woff2'))
for folder, family, weight_range in [('literata', 'Literata', '200 900'), ('rubik', 'Rubik', '300 900')]:
    for italic in (False, True):
        path = ROOT / 'references' / folder / ('Italic.woff2' if italic else 'Regular.woff2')
        with TTFont(path) as reference:
            axis = next((a for a in reference['fvar'].axes if a.axisTag == 'wght'), None)
            if axis is None or (axis.minValue, axis.maxValue) != tuple(map(float, weight_range.split())):
                raise ValueError(f'{family} weight axis does not match declared range {weight_range}: {path}')
        faces.append((family, weight_range, 'italic' if italic else 'normal',
                      path))
css = []
for family, weight, style, path in faces:
    encoded = base64.b64encode(path.read_bytes()).decode('ascii')
    css.append(f"@font-face{{font-family:{family};font-weight:{weight};font-style:{style};"
               f"font-display:swap;src:url(data:font/woff2;base64,{encoded}) format('woff2')}}")

families = ['Candidate', 'Baseline', 'Literata', 'Rubik']
regular_paths = [ROOT/'fonts/SEIReader-Regular.woff2', ROOT/f'old/{BASELINE_VERSION}/SEIReader-Regular.woff2',
                 ROOT/'references/literata/Regular.woff2', ROOT/'references/rubik/Regular.woff2']
metrics = {}
for family, path in zip(families, regular_paths):
    font = TTFont(path)
    if 'fvar' in font:
        axis = {'wght': 400}
        if family == 'Literata': axis['opsz'] = 20
        font = instantiateVariableFont(font, axis, inplace=False)
    gs = font.getGlyphSet()
    pen = BoundsPen(gs)
    gs[font.getBestCmap()[ord('x')]].draw(pen)
    upm = font['head'].unitsPerEm
    metrics[family] = {'x': font['OS/2'].sxHeight/upm, 'cap': font['OS/2'].sCapHeight/upm,
                       'inkX': pen.bounds[3]/upm,
                       'space': font['hmtx'][font.getBestCmap()[32]][0]/upm}

template = (ROOT/'comparison_template.html').read_text(encoding='utf-8')
page = (template.replace('__FONTS__', '\n'.join(css)).replace('__VERSION__', settings['version'])
        .replace('__BASELINE__', BASELINE_VERSION)
        .replace('__SPACE__', str(settings['wordSpace']/1000)).replace('__METRICS__', json.dumps(metrics)))
outputs = [ROOT/'lab/comparison.html']
if len(sys.argv) > 1: outputs.append(Path(sys.argv[1]).resolve())
for output in outputs:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding='utf-8')
    print('comparison', output, 'font faces', len(faces))
