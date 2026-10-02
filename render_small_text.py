"""Render a before/after small-text proof with Windows WPF at native pixel sizes.

python render_small_text.py <output-directory> [dpi] [--full-family] [--texture] [--latin] [--languages]
HarfBuzz shapes the real fonts; WPF rasterizes their actual glyph indices. This is
supplemental Windows rasterization evidence, not a Chrome, Safari, or device test.
"""
from pathlib import Path
import io
import json
import subprocess
import argparse

import uharfbuzz as hb
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent
BASELINE = '0.33'


def render(output, dpi=96, full_family=False, texture=False, latin=False, languages=False):
    """Render small sizes or all five weights at 20px, including each real italic."""
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    fonts = {}
    weights = ('Light', 'Regular', 'Medium', 'SemiBold', 'Bold') if full_family else ('Light', 'Regular', 'Medium')
    sizes = (20,) if full_family else (13, 15, 17)
    for family, folder in [('candidate', ROOT/'fonts'), ('baseline', ROOT/f'old/{BASELINE}')]:
        for weight in weights:
            for italic in (False, True):
                style = ('Italic' if weight == 'Regular' else weight+'Italic') if italic else weight
                source = folder/f'SEIReader-{style}.{"woff2" if family == "baseline" else "otf"}'
                with TTFont(source) as font:
                    font.flavor = None
                    buffer = io.BytesIO()
                    font.save(buffer)
                data = buffer.getvalue()
                font_path = output/f'{family}-{style}.otf'
                font_path.write_bytes(data)
                face = hb.Face(data)
                shaper = hb.Font(face)
                shaper.scale = (face.upem, face.upem)
                fonts[family, style] = font_path, shaper
    rows = []
    for weight in weights:
        for size in sizes:
            row = {'weight': weight, 'size': size, 'faces': []}
            for family in ('candidate', 'baseline'):
                lines = []
                samples = [
                    ('minimum · murmur · river', False, {'liga': True}),
                    ('climate · parallel · everywhere', False, {'liga': True}),
                    ('minimum · murmur · river', True, {'liga': True}),
                    ('climate · parallel · everywhere', True, {'liga': True}),
                    ('ri rn cl li · iv vi ll yw ur · fi fl', False, {'liga': False}),
                ] if not texture else [
                    ('“Mei’s,” Iñés said: “Wait… don’t!”', False, {}),
                    ('“Entry 12?” — 312, 314; 8.50%', True, {}),
                    ('0123456789 · 1,234.56 · 6089', False, {}),
                    ('0123456789 · 1,234.56 · 6089', False, {'tnum': True}),
                    ('½ ¼ ¾ · ² ₃ · fi fl · Á ñ ü ç', True, {}),
                ]
                if latin:
                    samples = [
                        ('Café · Cafe\u0301 · Iñés · In\u0303e\u0301s', False, {}),
                        ('n\u0304 m\u0300 x\u0323 g\u0303 i\u0304 j\u0301 A\u0302\u0301', False, {}),
                        ('n\u0304 m\u0300 x\u0323 g\u0303 i\u0304 j\u0301 A\u0302\u0301', True, {}),
                        ('„Lian: ‚Warte!‘“ «\u202fIñés entre.\u202f»', False, {}),
                        ('Meiʼs · Hawaiʻi · fl\u0301 · i\u0323\u0304', True, {}),
                    ]
                if languages:
                    samples=[
                        ('Łódź · gęś · Ą,Ę,ą, · żółć',False,{},'pl'),
                        ('Děvče · kůň · ďť · Příliš žluťoučký',False,{},'cs'),
                        ('Őrző · tűz · TY TTY · gyűrű',True,{},'hu'),
                        ('ĀĒĪŌŪ āēīōū · Māori · whānau',True,{},'mi'),
                        ('ȘșȚț · ŞşŢţ · Ștefan · țară',False,{},'ro'),
                        ('İpek · Işık · fikir · fi · fı',True,{},'tr'),
                        ('ƁƊƘƳ · ɓɗƙƴ · ƙarfi · ƴaƴa',False,{},'ha'),
                        ('ƁƊƘƳ · ɓɗƙƴ · ƙarfi · ƴaƴa',True,{},'ha'),
                        ('ị́ ọ̀ ụ́ · Ị́ Ọ̀ Ụ́ · Ṅṅ · ń m̀',False,{},'ig'),
                        ('ị́ ọ̀ ụ́ · Ị́ Ọ̀ Ụ́ · Ṅṅ · ń m̀',True,{},'ig'),
                        ('Ç Ê Î Ş Û · ç ê î ş û · çîrok · şev',False,{},'ku'),
                        ('oʻqish · gʻoya · oʻzbek · yoʻl',False,{},'uz'),
                    ]
                for text, italic, features, *locales in samples:
                    style = ('Italic' if weight == 'Regular' else weight+'Italic') if italic else weight
                    path, shaper = fonts[family, style]
                    buffer = hb.Buffer()
                    buffer.add_str(text)
                    buffer.guess_segment_properties()
                    if locales: buffer.language=locales[0]
                    hb.shape(shaper, buffer, {'kern': True, **features})
                    scale = size/shaper.face.upem
                    lines.append({'path': str(path), 'uri': path.as_uri(), 'text': text,
                                  'style': style, 'features': features,'language':locales[0] if locales else None,
                                  'glyphs': [info.codepoint for info in buffer.glyph_infos],
                                  'advances': [p.x_advance*scale for p in buffer.glyph_positions],
                                  # WPF GlyphOffsets use positive Y above the baseline, like HarfBuzz.
                                  'offsets': [[p.x_offset*scale, p.y_offset*scale] for p in buffer.glyph_positions]})
                row['faces'].append({'family': family, 'lines': lines})
            rows.append(row)
    settings = json.loads((ROOT/'settings.json').read_text(encoding='utf-8'))
    spec = {'candidate': settings['version'], 'baseline': BASELINE, 'dpi': dpi, 'rows': rows,
            'lineHeight': 1.5 if latin or languages else 1.4,
            'title': ('Latin alphabets (baseline lacks encoded letters)' if languages else 'Latin foundation (baseline lacks new glyphs)' if latin else 'punctuation and figures' if texture else 'broader spacing')
                     + (' / all weights' if full_family else ' / small text')}
    layout = output/f'windows-{dpi}.json'
    layout.write_text(json.dumps(spec, ensure_ascii=False), encoding='utf-8')
    subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(ROOT/'render_windows.ps1'),
                    '-Layout', str(layout), '-OutputDirectory', str(output)], check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output_directory')
    parser.add_argument('dpi', type=int, nargs='?', default=96)
    parser.add_argument('--full-family', action='store_true', help='Proof all five weights at 20px instead of the small-size matrix')
    parser.add_argument('--texture', action='store_true', help='Include dialogue punctuation and proportional/tabular figures')
    parser.add_argument('--latin', action='store_true', help='Include composed/decomposed accents, stacks, and local quotes')
    parser.add_argument('--languages', action='store_true', help='Include the new alphabets and actual Turkish/Romanian shaping')
    args = parser.parse_args()
    render(args.output_directory, args.dpi, args.full_family, args.texture, args.latin, args.languages)
