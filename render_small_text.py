"""Render a before/after small-text proof with Windows WPF at native pixel sizes.

python render_small_text.py <output-directory> [dpi]
HarfBuzz shapes the real fonts; WPF rasterizes their actual glyph indices. This is
supplemental Windows rasterization evidence, not a Chrome, Safari, or device test.
"""
from pathlib import Path
import io
import json
import subprocess
import sys

import uharfbuzz as hb
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent
BASELINE = '0.29'


def render(output, dpi=96):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    fonts = {}
    for family, folder in [('candidate', ROOT/'fonts'), ('baseline', ROOT/f'old/{BASELINE}')]:
        for weight in ('Light', 'Regular', 'Medium'):
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
    for weight in ('Light', 'Regular', 'Medium'):
        for size in (13, 15, 17):
            row = {'weight': weight, 'size': size, 'faces': []}
            for family in ('candidate', 'baseline'):
                lines = []
                for text, italic, liga in [
                    ('Lian · Iñés · blade · Entry · Mei’s · acquittal', False, True),
                    ('ri rn cl li · office affinity · flame reflection', False, True),
                    ('Lian · Iñés · blade · Entry · Mei’s · acquittal', True, True),
                    ('a e c s · Á É à ñ ü ç · 1⁄2 · ☯ ⚡ ▲ ♥', False, True),
                    ('fi fl · office · reflection (joins off)', False, False),
                ]:
                    style = ('Italic' if weight == 'Regular' else weight+'Italic') if italic else weight
                    path, shaper = fonts[family, style]
                    buffer = hb.Buffer()
                    buffer.add_str(text)
                    buffer.guess_segment_properties()
                    hb.shape(shaper, buffer, {'kern': True, 'liga': liga})
                    scale = size/shaper.face.upem
                    lines.append({'path': str(path), 'text': text,
                                  'glyphs': [info.codepoint for info in buffer.glyph_infos],
                                  'advances': [p.x_advance*scale for p in buffer.glyph_positions],
                                  'offsets': [[p.x_offset*scale, -p.y_offset*scale] for p in buffer.glyph_positions]})
                row['faces'].append({'family': family, 'lines': lines})
            rows.append(row)
    settings = json.loads((ROOT/'settings.json').read_text(encoding='utf-8'))
    spec = {'candidate': settings['version'], 'baseline': BASELINE, 'dpi': dpi, 'rows': rows}
    layout = output/f'windows-{dpi}.json'
    layout.write_text(json.dumps(spec, ensure_ascii=False), encoding='utf-8')
    subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(ROOT/'render_windows.ps1'),
                    '-Layout', str(layout), '-OutputDirectory', str(output)], check=True)


if __name__ == '__main__':
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    render(sys.argv[1], int(sys.argv[2]) if len(sys.argv) == 3 else 96)
