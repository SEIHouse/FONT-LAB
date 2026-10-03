"""Audit Phase 5 metadata, license delivery, and optional pre-release font preservation.

python verify_license.py
python verify_license.py --baseline dist/phase5-baseline/fonts
The baseline is a saved copy of all fifty 0.35 font files, before rebuilding.
"""
import argparse
from pathlib import Path

from fontTools.ttLib import TTFont

from build_subsets import STYLES, SUBSETS

ROOT = Path(__file__).resolve().parent
PROJECT = 'https://github.com/SEIHouse/seihouse-font-lab'
LICENSE_URL = PROJECT + '/blob/main/LICENSE'


def audit(baseline=None):
    """Check every full/subset font; a baseline additionally protects actual geometry/layout."""
    license_text = (ROOT / 'LICENSE').read_text(encoding='utf-8')
    assert 'SEIHouse Sans Ecosystem License, version 1.0' in license_text
    assert 'Installable document embedding is permitted' in license_text
    assert 'No registered-trademark' in license_text
    checked = preserved = 0
    for style, weight, slant in STYLES:
        suffixes = ['.otf', '.woff2', *[f'.{subset}.woff2' for subset in SUBSETS]]
        for suffix in suffixes:
            filename = f'SEIReader-{style}{suffix}'
            with TTFont(ROOT / 'fonts' / filename) as font:
                records = {i: [r.toUnicode() for r in font['name'].names if r.nameID == i]
                           for i in (0, 7, 8, 9, 11, 12, 13, 14)}
                assert all(records.values()), (filename, 'missing legal name ID')
                assert all('Copyright 2026 SEIHouse Productions LLC' in v for v in records[0]), filename
                assert all('No trademark registration is claimed' in v for v in records[7]), filename
                for i in (8, 9):
                    assert set(records[i]) == {'SEIHouse Productions LLC'}, (filename, i)
                for i in (11, 12):
                    assert set(records[i]) == {PROJECT}, (filename, i)
                assert set(records[14]) == {LICENSE_URL}, filename
                assert all('Ecosystem License, version 1.0' in v and LICENSE_URL in v
                           and 'require written permission' in v for v in records[13]), filename
                family = font['name'].getDebugName(16) or font['name'].getDebugName(1)
                assert family == 'SEIHouse Sans', (filename, family)
                assert font['name'].getDebugName(6) == f'SEIHouseSans-{style}', filename
                from phase4_support import release_version
                assert font['name'].getDebugName(5) == f'Version {release_version()}', filename
                assert font['OS/2'].fsType == 0 and font['OS/2'].achVendID == 'SEIH', filename
                assert font['OS/2'].usWeightClass == weight, filename
                assert bool(font['OS/2'].fsSelection & 1) == (slant == 'italic'), filename
                checked += 1
                if baseline is not None:
                    with TTFont(baseline / filename) as before:
                        assert before.getGlyphOrder() == font.getGlyphOrder(), filename
                        assert before.getBestCmap() == font.getBestCmap(), filename
                        for table in ('hmtx', 'hhea', 'GPOS', 'GSUB', 'GDEF'):
                            assert (table in before) == (table in font), (filename, table, 'presence')
                            if table in before:
                                assert before[table].compile(before) == font[table].compile(font), (filename, table)
                        old_os2, new_os2 = before['OS/2'], font['OS/2']
                        assert old_os2.compile(before) == new_os2.compile(font), (filename, 'OS/2')
                        old_top = before['CFF '].cff.topDictIndex[0]
                        new_top = font['CFF '].cff.topDictIndex[0]
                        assert old_top.Private.rawDict == new_top.Private.rawDict, (filename, 'hint parameters')
                        for old_subrs, new_subrs in (
                            (before['CFF '].cff.GlobalSubrs, font['CFF '].cff.GlobalSubrs),
                            (getattr(old_top.Private, 'Subrs', []), getattr(new_top.Private, 'Subrs', [])),
                        ):
                            assert len(old_subrs) == len(new_subrs), (filename, 'subroutine count')
                            for old_subr, new_subr in zip(old_subrs, new_subrs):
                                old_subr.decompile(); new_subr.decompile()
                                assert old_subr.program == new_subr.program, (filename, 'hint subroutine')
                        for name in font.getGlyphOrder():
                            old_char = old_top.CharStrings[name]
                            new_char = new_top.CharStrings[name]
                            old_char.decompile(); new_char.decompile()
                            assert old_char.program == new_char.program, (filename, name, 'outline/hints')
                        preserved += 1
    print(f'{checked} fonts: legal name IDs, Sans names, version, vendor, embedding, weights and italics pass')
    if baseline is not None:
        print(f'{preserved} fonts: every glyph program, hint parameter, metric, cmap and layout table matches 0.35')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path)
    audit(parser.parse_args().baseline)
