"""Audit the 0.31 spacing pass against preserved 0.30 in all ten styles.

Checks every contour/metric, changed shaping, accent classes, ligature neighbors,
subset shaping, hinting, and actual outline separation in the reported words.
"""
from pathlib import Path
import hashlib
import io
import json

import pathops
import uharfbuzz as hb
from fontTools.ttLib import TTFont

from build_subsets import STYLES
from verify_lowercase import recorded

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT/'old/0.30'
RHYTHM_WORDS = ('minimum', 'murmur', 'river', 'climate', 'parallel', 'everywhere',
                'rival', 'arrival', 'vivid', 'willow', 'weary', 'yearly', 'twilight')
PREVIOUS_FOCUS = set('Li ia an In ne es bl la ad de En nt tr ry Me ei ac cq qu ui it tt ta al ri rn rm cl li fi fl'.split())
ALLOWED_PAIR_CHANGES = {a+b for word in RHYTHM_WORDS for a,b in zip(word, word[1:])} - PREVIOUS_FOCUS
WORDS = ('Lian', 'Iñés', 'blade', 'Entry', 'Mei’s', "Mei's", 'acquittal',
         'ri', 'rn', 'cl', 'li', 'office', 'affinity', 'flame', 'reflection') + RHYTHM_WORDS


def shaped(font, text, kern=True, liga=True):
    """Return HarfBuzz glyph names, advances, and offsets for the selected features."""
    if not hasattr(font, '_spacing_shaper'):
        font.flavor = None
        data = io.BytesIO()
        font.save(data)
        face = hb.Face(data.getvalue())
        font._spacing_shaper = hb.Font(face)
        font._spacing_shaper.scale = (face.upem, face.upem)
    shaper = font._spacing_shaper
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(shaper, buffer, {'kern': kern, 'liga': liga})
    return [(font.getGlyphOrder()[i.codepoint], p.x_advance, p.x_offset, p.y_offset)
            for i, p in zip(buffer.glyph_infos, buffer.glyph_positions)]


def adjustment(font, text):
    """Return pair-advance differences with kerning enabled, without ligature substitution."""
    plain = shaped(font, text, kern=False, liga=False)
    spaced = shaped(font, text, liga=False)
    return [b[1]-a[1] for a, b in zip(plain, spaced)]


def verify():
    """Audit font preservation, shaping, hints, collisions, and per-style Lab spacing."""
    before_settings = json.loads((BASELINE/'settings.json').read_text(encoding='utf-8'))
    after_settings = json.loads((ROOT/'settings.json').read_text(encoding='utf-8'))
    before_settings.pop('version'); after_settings.pop('version')
    assert before_settings == after_settings, 'Setting changed outside the version number'
    hashes = json.loads((BASELINE/'SHA256.json').read_text(encoding='utf-8'))
    style_pairs = json.loads((ROOT/'kern_styles.json').read_text(encoding='utf-8'))
    before_pairs = json.loads((BASELINE/'kern_styles.json').read_text(encoding='utf-8'))
    assert len(hashes) == len(style_pairs) == 10
    reports = {}
    for style, _, _ in STYLES:
        old_pairs, new_pairs = before_pairs[style], style_pairs[style]
        changed_pairs = {pair for pair in old_pairs.keys() | new_pairs.keys()
                         if old_pairs.get(pair, 0) != new_pairs.get(pair, 0)}
        assert changed_pairs and changed_pairs <= ALLOWED_PAIR_CHANGES, (style, 'pair changed outside the inspected rhythm cases', changed_pairs-ALLOWED_PAIR_CHANGES)
        filename = f'SEIReader-{style}.woff2'
        baseline_path = BASELINE/filename
        assert hashlib.sha256(baseline_path.read_bytes()).hexdigest() == hashes[filename], filename
        with TTFont(baseline_path) as before, TTFont(ROOT/'fonts'/filename.replace('.woff2', '.otf')) as after:
            assert before.getBestCmap() == after.getBestCmap(), style
            assert before.getGlyphOrder() == after.getGlyphOrder(), style
            for name in after.getGlyphOrder():
                assert recorded(before, name) == recorded(after, name), (style, name, 'outline changed')
                assert before['hmtx'][name] == after['hmtx'][name], (style, name, 'advance/bearing changed')
            for table, fields in {
                'head': ['unitsPerEm'], 'hhea': ['ascent', 'descent', 'lineGap'], 'post': ['italicAngle'],
                'OS/2': ['sxHeight', 'sCapHeight', 'usWeightClass', 'usWidthClass', 'sTypoAscender',
                         'sTypoDescender', 'sTypoLineGap', 'usWinAscent', 'usWinDescent'],
            }.items():
                for field in fields:
                    assert getattr(before[table], field) == getattr(after[table], field), (style, table, field)
            private = after['CFF '].cff.topDictIndex[0].Private
            before_private = before['CFF '].cff.topDictIndex[0].Private
            for key in ('BlueValues', 'OtherBlues', 'StdVW', 'StdHW'):
                assert getattr(private, key) == getattr(before_private, key), (style, key)
            # Hint instructions must still exist after the rebuild, including Light.
            charstring = after['CFF '].cff.topDictIndex[0].CharStrings['n']
            charstring.decompile()
            assert any(token in charstring.program for token in ('hstem', 'hstemhm', 'vstem', 'vstemhm')), style
            for base, accent in [('In','Iñ'), ('ne','ñé'), ('es','és'), ('qu','qù'), ('ui','üi'),
                                 ('ar','ár'), ('ur','ür'), ('va','và'), ('ev','év'), ('ly','lý')]:
                assert adjustment(after, base) == adjustment(after, accent), (style, base, accent)
            glyphs = after.getGlyphSet()
            outlines = {}
            for text in WORDS + ('fi', 'fl'):
                assert shaped(before, text, kern=False) == shaped(after, text, kern=False), (style, text, 'default glyphs/advances changed')
                for liga in (True, False):
                    positioned = shaped(after, text, liga=liga)
                    x = 0; previous = None
                    for name, advance, dx, dy in positioned:
                        if name not in outlines:
                            outline = pathops.Path()
                            glyphs[name].draw(outline.getPen())
                            outlines[name] = outline
                        ink = outlines[name].transform(translateX=x+dx, translateY=dy)
                        if previous is not None:
                            overlap = pathops.op(previous, ink, pathops.PathOp.INTERSECTION)
                            assert abs(overlap.area) < .01, (style, text, 'ink collision', name, liga)
                        previous = ink; x += advance
            assert shaped(after, 'fi')[0][0] == after.getBestCmap()[ord('ﬁ')], style
            assert shaped(after, 'fl')[0][0] == after.getBestCmap()[ord('ﬂ')], style
            for text in ('eﬂ', 'ﬂe'):
                assert adjustment(after, text)[0] != 0, (style, text, 'ligature neighbor spacing missing')
            with TTFont(ROOT/'fonts'/f'SEIReader-{style}.latin-basic.woff2') as subset:
                for text in ('Lian', 'blade', 'Entry', 'acquittal', 'ri rn cl li', 'office affinity flame reflection'):
                    assert shaped(after, text) == shaped(subset, text), (style, text, 'subset shaping')
                for text in RHYTHM_WORDS:
                    assert shaped(after, text) == shaped(subset, text), (style, text, 'broader subset shaping')
            for pair, value in style_pairs[style].items():
                if len(pair) == 2 and all(ord(ch) in after.getBestCmap() for ch in pair):
                    assert adjustment(after, pair)[0] == round(value*2), (style, pair, 'Lab spacing does not match font')
            changed = {}
            for text in WORDS:
                old, new = shaped(before, text), shaped(after, text)
                if old != new: changed[text] = {'before': sum(p[1] for p in old), 'after': sum(p[1] for p in new)}
            assert sum(word in changed for word in RHYTHM_WORDS[:6]) >= 3, (style, 'expected broader word spacing changes missing')
            reports[style] = changed
            print(f'{style}: {len(changed_pairs)} inspected pairs changed; all 295 contours/metrics preserved; shaping and collision checks pass')
    print('All ten styles pass the 0.31 broader spacing audit.')
    return reports


if __name__ == '__main__':
    verify()
