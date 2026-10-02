"""Check Phase 2 glyphs, shaping, and web subsets after rebuilding all styles."""
import io
import os

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from build_subsets import HERE, STYLES, SUBSETS, subset_groups

DIGITS = '0123456789'
NAMES = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine')
SUPERS = '⁰¹²³⁴⁵⁶⁷⁸⁹'
SUBS = '₀₁₂₃₄₅₆₇₈₉'
ADDED_UNICODE = SUPERS + SUBS + '½¼¾⁄'


def shape(path, text, features=None):
    font = TTFont(path)
    if path.endswith('.woff2'):
        # HarfBuzz accepts SFNT bytes; browsers decompress WOFF2 before shaping too.
        font.flavor = None
        output = io.BytesIO()
        font.save(output)
        data = output.getvalue()
    else:
        data = open(path, 'rb').read()
    face = hb.Face(data)
    shaper = hb.Font(face)
    shaper.scale = (font['head'].unitsPerEm, font['head'].unitsPerEm)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(shaper, buffer, features or {})
    names = [font.getGlyphOrder()[info.codepoint] for info in buffer.glyph_infos]
    advances = [position.x_advance for position in buffer.glyph_positions]
    font.close()
    return names, advances


def ink_center(font, name):
    glyphs = font.getGlyphSet()
    pen = BoundsPen(glyphs)
    glyphs[name].draw(pen)
    assert pen.bounds is not None, name
    return (pen.bounds[0] + pen.bounds[2]) / 2


def verify_style(style):
    source = os.path.join(HERE, 'fonts', f'SEIReader-{style}.otf')
    font = TTFont(source)
    cmap = font.getBestCmap()
    assert all(ord(ch) in cmap for ch in ADDED_UNICODE), style
    default, default_advance = shape(source, DIGITS)
    assert default == list(NAMES), (style, default)
    assert len(set(default_advance)) > 1, style

    tabular, tabular_advance = shape(source, DIGITS, {'tnum': 1})
    assert tabular == [name + '.tf' for name in NAMES], (style, tabular)
    assert set(tabular_advance) == {max(default_advance)}, (style, tabular_advance)
    for name in tabular:
        assert abs(ink_center(font, name) - font['hmtx'][name][0] / 2) <= 1, (style, name)

    supers, _ = shape(source, DIGITS, {'sups': 1})
    subs, _ = shape(source, DIGITS, {'subs': 1})
    assert supers == [cmap[ord(ch)] for ch in SUPERS], (style, supers)
    assert subs == [cmap[ord(ch)] for ch in SUBS], (style, subs)
    assert shape(source, '2', {'tnum': 1, 'sups': 1})[0] == [cmap[ord('²')]], style
    assert shape(source, '2', {'tnum': 1, 'subs': 1})[0] == [cmap[ord('₂')]], style
    assert abs(ink_center(font, supers[0]) - font['hmtx'][supers[0]][0] / 2) <= 1, style

    for text, expected in (
        ('1/2', ['one.numr', cmap[ord('⁄')], 'two.dnom']),
        ('12/34', ['one.numr', 'two.numr', cmap[ord('⁄')], 'three.dnom', 'four.dnom']),
    ):
        actual, _ = shape(source, text, {'frac': 1})
        assert actual == expected, (style, text, actual)
        combined, _ = shape(source, text, {'frac': 1, 'tnum': 1})
        assert combined == expected, (style, text, combined)
    direct, _ = shape(source, '1⁄2')
    assert direct == ['one.numr', cmap[ord('⁄')], 'two.dnom'], (style, direct)
    assert shape(source, '1/2')[0] == ['one', cmap[ord('/')], 'two'], style
    assert shape(source, '½¼¾')[0] == [cmap[ord(ch)] for ch in '½¼¾'], style
    assert font['hmtx'][cmap[ord('½')]][0] == (
        font['hmtx']['one.numr'][0] + font['hmtx'][cmap[ord('⁄')]][0] + font['hmtx']['two.dnom'][0])

    for name in SUBSETS:
        subset_path = os.path.join(HERE, 'fonts', f'SEIReader-{style}.{name}.woff2')
        subset = TTFont(subset_path)
        expected = subset_groups(set(cmap))[name]
        assert set(subset.getBestCmap()) == expected, (style, name)
        subset.close()
    basic = os.path.join(HERE, 'fonts', f'SEIReader-{style}.latin-basic.woff2')
    assert shape(basic, '10', {'tnum': 1})[0] == ['one.tf', 'zero.tf'], style
    assert shape(basic, '1/2', {'frac': 1})[0] == ['one.numr', cmap[ord('⁄')], 'two.dnom'], style
    assert shape(basic, '1⁄2')[0] == ['one.numr', cmap[ord('⁄')], 'two.dnom'], style
    assert shape(basic, '12/34', {'frac': 1, 'tnum': 1})[0] == [
        'one.numr', 'two.numr', cmap[ord('⁄')], 'three.dnom', 'four.dnom'], style
    assert shape(basic, '2', {'sups': 1})[0] == [cmap[ord('²')]], style
    font.close()
    print('verified', style)


if __name__ == '__main__':
    for style, _, _ in STYLES:
        verify_style(style)
    css = open(os.path.join(HERE, 'fonts.css'), encoding='utf-8').read()
    assert css.count('@font-face') == len(STYLES) * len(SUBSETS)
    print('Phase 2 shaping and 30 web subsets verified')
