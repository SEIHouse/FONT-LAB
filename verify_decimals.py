"""Audit decimal visibility, tabular alignment, and unchanged figure drawings."""
from pathlib import Path

import pathops
from fontTools.ttLib import TTFont

from build_subsets import STYLES
from verify_latin import shape
from verify_lowercase import recorded

ROOT = Path(__file__).resolve().parent
SAMPLES = ('1,234.56', '8.50%', '0.01', '7.77', '1.234,56', '8,50%',
           '$12.99', '312.00 / 314.00', '-0.05', '10.000,00')


def band_bounds(font, name, low, high):
    """Measure actual ink in the separator's vertical band, including italic slant."""
    path = pathops.Path()
    font.getGlyphSet()[name].draw(path.getPen())
    rectangle = pathops.Path()
    pen = rectangle.getPen()
    pen.moveTo((-10000, low))
    pen.lineTo((10000, low))
    pen.lineTo((10000, high))
    pen.lineTo((-10000, high))
    pen.closePath()
    clipped = pathops.op(path, rectangle, pathops.PathOp.INTERSECTION)
    return clipped.bounds if clipped else None


def verify():
    """Check every digit around both separators in every real style and delivery."""
    for style, _, _ in STYLES:
        with TTFont(ROOT/'fonts'/f'SEIReader-{style}.otf') as font, TTFont(ROOT/'old/0.33'/f'SEIReader-{style}.woff2') as before:
            cmap = font.getBestCmap()
            upem = font['head'].unitsPerEm
            numeric_names = [cmap[ord(c)] for c in '0123456789.,']
            numeric_names += [name for name in font.getGlyphOrder() if name.endswith(('.tf', '.numr', '.dnom'))]
            for name in numeric_names:
                assert font['hmtx'][name] == before['hmtx'][name], (style, name, 'metric change')
                assert recorded(font, name) == recorded(before, name), (style, name, 'outline change')
            for tabular in (False, True):
                widths = []
                for separator in '.,':
                    separator_path = pathops.Path()
                    font.getGlyphSet()[cmap[ord(separator)]].draw(separator_path.getPen())
                    low, high = separator_path.bounds[1], separator_path.bounds[3]
                    for digit in '0123456789':
                        for text in (digit+separator, separator+digit):
                            shaped = shape(font, text, tnum=tabular)
                            first, second = shaped
                            a = band_bounds(font, first[0], low, high)
                            b = band_bounds(font, second[0], low, high)
                            if a and b:
                                gap = first[1]+second[2]+b[0]-first[2]-a[2]
                                assert gap >= .07*upem, (style, text, tabular, 'separator crowded', gap/upem)
                            assert all(name != '.notdef' for name, *_ in shaped)
                        widths.append(sum(row[1] for row in shape(font, digit+separator+digit, tnum=tabular)))
                if tabular:
                    assert len(set(widths[:10])) == len(set(widths[10:])) == 1, (style, 'tabular columns drift')
                assert shape(font, '0123456789', tnum=tabular) == shape(before, '0123456789', tnum=tabular), (style, 'digit rhythm changed')
                for text in SAMPLES:
                    assert sum(row[1] for row in shape(font, text, tnum=tabular)) > sum(row[1] for row in shape(before, text, tnum=tabular)), (style, text, 'separator room missing')
                    assert shape(font, text, kern=False, tnum=tabular) == shape(before, text, kern=False, tnum=tabular), (style, text, 'unspaced layout changed')
                    for subset_name in ('latin-basic', 'latin-extended'):
                        with TTFont(ROOT/'fonts'/f'SEIReader-{style}.{subset_name}.woff2') as subset:
                            assert shape(font, text, tnum=tabular) == shape(subset, text, tnum=tabular), (style, subset_name, text)
            print(f'{style}: separators clear in both figure modes; tabular columns stable; outlines/metrics and subsets pass')


if __name__ == '__main__':
    verify()
