"""Audit the 0.35 outline repair against preserved 0.34 web fonts.

Reject ambiguous overlap winding in every shipped glyph, including numeric
alternates and symbols. Preserve design settings, metrics, shaping and the
intended stroke silhouette; test full-font/subset delivery independently.
"""
import argparse
import hashlib
import json
from pathlib import Path
import unicodedata

import pathops
from fontTools.ttLib import TTFont

from build_subsets import STYLES, subset_groups
from language_coverage import inventory, test_strings
from verify_latin import shape

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / 'old/0.34'


def outline(font, name):
    """Read the actual exported CFF contours, rather than engine centerlines."""
    result = pathops.Path()
    font.getGlyphSet()[name].draw(result.getPen())
    return result


def filled(path, rule=pathops.FillType.WINDING):
    """Resolve a copy using a renderer's fill rule without altering the source."""
    copy = path.transform()
    copy.fillType = rule
    return pathops.op(copy, copy, pathops.PathOp.UNION, fix_winding=True)


def missing_ink(path):
    """Measure ink that disappears when overlaps are interpreted as even/odd."""
    return abs(pathops.op(filled(path), filled(path, pathops.FillType.EVEN_ODD),
                         pathops.PathOp.XOR).area)


def verify(fonts=ROOT / 'fonts'):
    """Check all ten styles, every glyph, and all thirty independently built subsets."""
    before_settings = json.loads((BASELINE / 'settings.json').read_text(encoding='utf-8'))
    settings = json.loads((ROOT / 'settings.json').read_text(encoding='utf-8'))
    assert before_settings.pop('version') == '0.34'
    assert settings.pop('version') == '0.35'
    assert settings == before_settings, 'Design settings changed'
    for name in ('kern_styles.json', 'kern_languages.json'):
        assert json.loads((ROOT / name).read_text(encoding='utf-8')) == json.loads(
            (BASELINE / name).read_text(encoding='utf-8')), name
    for name, digest in json.loads((BASELINE / 'SHA256.json').read_text()).items():
        assert hashlib.sha256((BASELINE / name).read_bytes()).hexdigest() == digest, name

    strings = [(text, code) for code, locale in inventory()['locales'].items()
               for text in [*test_strings(locale), locale['sample']]]
    repaired = 0
    for style, _, _ in STYLES:
        with TTFont(BASELINE / f'SEIReader-{style}.woff2') as before, TTFont(
                fonts / f'SEIReader-{style}.otf') as font:
            assert before.getBestCmap() == font.getBestCmap(), (style, 'cmap')
            assert before.getGlyphOrder() == font.getGlyphOrder(), (style, 'glyph inventory')
            for table in ('hmtx', 'GPOS', 'GSUB', 'GDEF'):
                assert before[table].compile(before) == font[table].compile(font), (style, table)
            for table, fields in {
                'head': ('unitsPerEm',), 'hhea': ('ascent', 'descent', 'lineGap'),
                'post': ('italicAngle',), 'OS/2': ('sxHeight', 'sCapHeight', 'usWeightClass',
                    'sTypoAscender', 'sTypoDescender', 'sTypoLineGap', 'usWinAscent', 'usWinDescent')
            }.items():
                for field in fields:
                    assert getattr(before[table], field) == getattr(font[table], field), (style, table, field)
            for name in font.getGlyphOrder():
                old, current = outline(before, name), outline(font, name)
                loss = missing_ink(current)
                assert loss < 1, (style, name, 'ambiguous stroke winding', loss)
                old, current = filled(old), filled(current)
                if not old:
                    assert not current, (style, name, 'empty glyph changed')
                    continue
                assert current, (style, name, 'lost glyph')
                # Cleanup changes curve segmentation before whole-unit CFF rounding.
                # Allow only that subpixel fitting error around the same silhouette.
                # Skia XOR can misclassify coincident curve edges (e.g. italic
                # arrows). Measure symmetric difference through intersection
                # area instead and require the intersection to fit both inputs.
                common = abs(pathops.op(old, current, pathops.PathOp.INTERSECTION).area)
                assert common <= min(old.area, current.area) + 1, (style, name, 'intersection area')
                delta = abs(old.area + current.area - 2 * common)
                assert delta < max(8, old.area * .005), (style, name, 'silhouette changed', delta)
                assert max(abs(a-b) for a, b in zip(old.bounds, current.bounds)) < 2, (style, name, 'bounds')
            for ch in 'vVwW2345':
                name = font.getBestCmap()[ord(ch)]
                assert missing_ink(outline(before, name)) > 1000, (style, ch, 'baseline must reproduce defect')
                repaired += 1
            for text, language in strings:
                actual = shape(font, text, language=language)
                assert all(name != '.notdef' for name, _, _, _ in actual), (style, language, text, 'fallback')
                assert shape(before, text, language=language) == actual, (style, language, text)
                for form in ('NFC', 'NFD'):
                    assert actual == shape(font, unicodedata.normalize(form, text), language=language), (style, language, text, form)
            for feature, text in [('tnum', '0123456789'), ('sups', '1234567890'),
                                  ('subs', '1234567890'), ('frac', '12/34')]:
                assert shape(before, text, **{feature: 1}) == shape(font, text, **{feature: 1}), (style, feature)

            with TTFont(fonts / f'SEIReader-{style}.woff2') as web:
                for table in ('hmtx', 'GPOS', 'GSUB', 'GDEF', 'CFF '):
                    assert font[table].compile(font) == web[table].compile(web), (style, 'full web', table)
            for subset, codes in subset_groups(set(font.getBestCmap())).items():
                with TTFont(fonts / f'SEIReader-{style}.{subset}.woff2') as web:
                    assert set(web.getBestCmap()) == codes, (style, subset, 'coverage')
                    for name in web.getGlyphOrder():
                        assert missing_ink(outline(web, name)) < 1, (style, subset, name, 'winding')
                        assert font['hmtx'][name] == web['hmtx'][name], (style, subset, name, 'metrics')
                    for text in ('vVwW0123456789', '1,234.56', '8.50%', 'Iñés', 'ị́'):
                        if all(ord(ch) in codes for ch in text):
                            assert shape(font, text) == shape(web, text), (style, subset, text)
                    if subset == 'latin-extended':
                        for text, language in strings:
                            assert shape(font, text, language=language) == shape(web, text, language=language), (style, subset, language, text)
        print(f'{style}: solid stroke winding, silhouettes, metrics, layout, languages and delivery pass')
    print(f'{repaired} reported letter/digit cases repaired; {len(strings)*len(STYLES):,} language strings preserved')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fonts', type=Path, default=ROOT / 'fonts')
    verify(parser.parse_args().fonts)
