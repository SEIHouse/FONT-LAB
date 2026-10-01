"""Verify the scope of the 0.29 lowercase consistency pass against preserved 0.28.

Run after make_fonts.py. Checks the finished fonts, including every unchanged
outline and every advance, across all ten weights/styles.
"""
from pathlib import Path
import hashlib
import json

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / 'old/0.28'
BASES = 'hnmubdpq'
DERIVATIVES = 'ñùúûü'


def recorded(font, name):
    glyphs = font.getGlyphSet()
    pen = DecomposingRecordingPen(glyphs)
    glyphs[name].draw(pen)
    return pen.value


def bounds(font, name):
    glyphs = font.getGlyphSet()
    pen = BoundsPen(glyphs)
    glyphs[name].draw(pen)
    return pen.bounds


def verify():
    before_settings = json.loads((BASELINE/'settings.json').read_text(encoding='utf-8'))
    after_settings = json.loads((ROOT/'settings.json').read_text(encoding='utf-8'))
    before_settings.pop('version')
    after_settings.pop('version')
    assert before_settings == after_settings, 'A setting changed outside the version number'
    hashes = json.loads((BASELINE/'SHA256.json').read_text(encoding='utf-8'))
    assert len(hashes) == 10, 'Expected all ten preserved baseline styles'
    for filename, digest in hashes.items():
        path = BASELINE/filename
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, f'Baseline changed: {filename}'
        with TTFont(path) as before, TTFont(ROOT/'fonts'/filename.replace('.woff2', '.otf')) as after:
            assert before.getBestCmap() == after.getBestCmap(), f'Character mapping changed: {filename}'
            assert before.getGlyphOrder() == after.getGlyphOrder(), f'Glyph set changed: {filename}'
            for table, fields in {
                'head': ['unitsPerEm'],
                'OS/2': ['sxHeight', 'sCapHeight', 'usWeightClass', 'usWidthClass',
                         'sTypoAscender', 'sTypoDescender', 'sTypoLineGap', 'usWinAscent', 'usWinDescent'],
                'hhea': ['ascent', 'descent', 'lineGap'],
                'post': ['italicAngle'],
            }.items():
                for field in fields:
                    assert getattr(before[table], field) == getattr(after[table], field), f'{filename}: {table}.{field}'
            cmap = after.getBestCmap()
            allowed = {cmap[ord(ch)] for ch in BASES + DERIVATIVES}
            unchanged = 0
            for name in after.getGlyphOrder():
                assert before['hmtx'][name][0] == after['hmtx'][name][0], f'Advance changed: {filename} {name}'
                if name not in allowed:
                    assert recorded(before, name) == recorded(after, name), f'Unexpected outline change: {filename} {name}'
                    assert before['hmtx'][name] == after['hmtx'][name], f'Unexpected bearing change: {filename} {name}'
                    unchanged += 1
            for ch in BASES + DERIVATIVES:
                name = cmap[ord(ch)]
                assert recorded(before, name) != recorded(after, name), f'Refinement missing: {filename} {ch}'
            for ch in BASES:
                name = cmap[ord(ch)]
                commands = recorded(after, name)
                expected = 2 if ch in 'bdpq' else 1
                assert sum(op == 'closePath' for op, _ in commands) == expected, f'Unexpected contour count: {filename} {ch}'
                top = after['OS/2'].sCapHeight if ch in 'hbd' else after['OS/2'].sxHeight
                bottom = -400 if ch in 'pq' else 0
                ink = bounds(after, name)
                assert abs(ink[3] - top) <= 1, f'Top alignment changed: {filename} {ch}: {ink[3]}'
                assert abs(ink[1] - bottom) <= 1, f'Bottom alignment changed: {filename} {ch}: {ink[1]}'
            for ch, base in [('ñ','n'), ('ù','u'), ('ú','u'), ('û','u'), ('ü','u')]:
                assert after['hmtx'][cmap[ord(ch)]][0] == after['hmtx'][cmap[ord(base)]][0], f'Accent advance mismatch: {filename} {ch}'
            print(f'{filename}: all advances unchanged; {unchanged} outlines unchanged; 13 intended outlines refined; counters/alignment pass')
    print('All ten styles pass the 0.29 scope and preservation checks.')


if __name__ == '__main__':
    verify()
