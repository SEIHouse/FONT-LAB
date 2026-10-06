"""Gate Display licensing, six web subsets, CSS coverage and native layout parity."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import unicodedata

from fontTools.ttLib import TTFont

from build_subsets import unicode_range
from display.build_subsets import BASIC_LIMIT, FACE_ORDER, display_groups
from display.letter_alternates import SET_NAMES
from language_coverage import inventory, test_strings
from verify_latin import shape
from verify_lowercase import recorded

ROOT = Path(__file__).resolve().parent
CUTS = ('soft', 'edge', 'ink', 'wide')
LEGAL_IDS = (0, 7, 8, 9, 11, 12, 13, 14)


def legal_records(font):
    """Include every platform/language record, so a missing EULA cannot hide in one name."""
    return {name_id: sorted((record.platformID, record.platEncID, record.langID, record.toUnicode())
                           for record in font['name'].names if record.nameID == name_id)
            for name_id in LEGAL_IDS}


def license_flags(font, reader):
    """Require exactly the Reader's legal identity, URLs, vendor and embedding permissions."""
    expected, actual = legal_records(reader), legal_records(font)
    found = [dict(kind='display-legal-name', name_id=name_id) for name_id in LEGAL_IDS
             if not actual[name_id] or actual[name_id] != expected[name_id]]
    for field in ('fsType', 'achVendID'):
        if getattr(font['OS/2'], field) != getattr(reader['OS/2'], field):
            found.append(dict(kind='display-legal-os2', field=field))
    return found


def shaping_samples(codes):
    """Cover every supported language plus feature combinations and stacked marks."""
    samples = set()
    for language, locale in inventory()['locales'].items():
        for text in [*test_strings(locale), locale['sample']]:
            if all(ord(ch) in codes for ch in text + unicodedata.normalize('NFC', text)):
                samples.add((text, language))
    for text in ('Ww WAVE WORLD', 'LA LY LT TA AV AW AY PA FA VA RT', 'ÁV Ŵ Ý Ķ ģ ấ',
                 'fi fl', 'x\u0302\u0301 i\u030b j\u0301', 'ŞşŢţ', 'ȘșȚț',
                 'ΚΜ ΆΥ', 'КМ Ќ ў', 'Tưởng tượng', '469 4.69 16/49', '⁴⁶⁹ ₄₆₉ ¼¾',
                 'Ⓢ 🎧 💻 ♫ → ♥'):
        for form in (text, unicodedata.normalize('NFD', text)):
            if all(ord(ch) in codes for ch in form + unicodedata.normalize('NFC', form)):
                samples.add((form, None))
    return sorted(samples, key=lambda row: (row[0], row[1] or ''))


def subset_flags(full, subset, codes):
    """Protect every retained outline/metric and its real HarfBuzz shaping behavior."""
    found, measurements = [], 0
    expected = {code: name for code, name in full.getBestCmap().items() if code in codes}
    if subset.getBestCmap() != expected:
        found.append(dict(kind='display-subset-coverage'))
    for name in subset.getGlyphOrder():
        if name not in full.getGlyphOrder():
            found.append(dict(kind='display-subset-extra-glyph', glyph=name))
        elif subset['hmtx'][name] != full['hmtx'][name] or recorded(subset, name) != recorded(full, name):
            found.append(dict(kind='display-subset-outline-metric', glyph=name))
    for field in ('sTypoAscender', 'sTypoDescender', 'sTypoLineGap', 'usWinAscent', 'usWinDescent'):
        if getattr(subset['OS/2'], field) != getattr(full['OS/2'], field):
            found.append(dict(kind='display-subset-line-metric', field=field))
    for text, language in shaping_samples(codes):
        if shape(subset, text, language=language) != shape(full, text, language=language):
            found.append(dict(kind='display-subset-language-shaping', text=text, language=language))
        measurements += 1
    modes = [{}, {'cpsp': True}, *[{tag: True} for tag in SET_NAMES],
             {tag: True for tag in SET_NAMES}, {'tnum': True}, {'sups': True},
             {'subs': True}, {'frac': True}, {'ss08': True, 'tnum': True},
             {'ss08': True, 'frac': True}, {'ss04': True, 'cpsp': True}]
    for text in ('Ww WAVE WORLD', 'ag RKk MW y G Q 469', 'ÁV Ŵ Ķ ģ ấ', 'ΚΜ КМ Ќ',
                 '469 4.69 16/49', '⁴⁶⁹ ₄₆₉ ¼¾', 'x\u0302\u0301'):
        if not all(ord(ch) in codes for ch in text):
            continue
        for features in modes:
            if shape(subset, text, **features) != shape(full, text, **features):
                found.append(dict(kind='display-subset-feature-shaping', text=text, features=features))
            measurements += 1
    for language in ('tr', 'ro'):
        for text in ('fi', 'ŞşŢţ'):
            if all(ord(ch) in codes for ch in text):
                if shape(subset, text, language=language) != shape(full, text, language=language):
                    found.append(dict(kind='display-subset-locl', language=language, text=text))
                measurements += 1
    return found, measurements


def css_flags(css, sources):
    """Check URLs, families, ordering and ranges against the actual subset cmap."""
    text = css.read_text(encoding='utf-8')
    blocks = re.findall(r'@font-face\s*\{([^}]+)\}', text)
    expected = []
    for source in sources:
        with TTFont(source) as font:
            family = font['name'].getDebugName(16) or font['name'].getDebugName(1)
            weight = str(font['OS/2'].usWeightClass)
        for name in FACE_ORDER:
            file = source.with_suffix('.'+name+'.woff2')
            with TTFont(file) as subset:
                ranges = unicode_range(set(subset.getBestCmap()))
            url = './'+Path(os.path.relpath(file, css.parent)).as_posix()
            expected.append((family, url, weight, ranges))
    found = []
    if len(blocks) != len(expected):
        return [dict(kind='display-css-face-count', expected=len(expected), actual=len(blocks))]
    for index, (block, (family, url, weight, ranges)) in enumerate(zip(blocks, expected)):
        values = dict(re.findall(r'([a-z-]+)\s*:\s*([^;]+);', block))
        if (values.get('font-family') != '"'+family+'"' or
                values.get('src') != 'url("'+url+'") format("woff2")' or
                values.get('font-weight') != weight or values.get('font-style') != 'normal' or
                values.get('font-display') != 'swap' or values.get('unicode-range') != ranges):
            found.append(dict(kind='display-css-face', face=index, file=url))
    return found


def verify(fonts, css=None):
    """Audit all 32 Display deliveries and the shipped or candidate stylesheets."""
    report = dict(basic_limit_bytes=BASIC_LIMIT, cuts={}, flags=[])
    sources = [fonts/cut/f'SEIHouseDisplay-{cut.title()}.otf' for cut in CUTS]
    with TTFont(ROOT/'fonts/SEIReader-Regular.otf') as reader:
        for cut, source in zip(CUTS, sources):
            summary = dict(subsets={}, license_files=0, measurements=0)
            with TTFont(source) as full:
                groups = display_groups(set(full.getBestCmap()))
                for file in [source, source.with_suffix('.woff2'),
                             *[source.with_suffix('.'+name+'.woff2') for name in FACE_ORDER]]:
                    with TTFont(file) as font:
                        found = license_flags(font, reader)
                        summary['license_files'] += 1
                        name = next((name for name in FACE_ORDER if file.name.endswith('.'+name+'.woff2')), None)
                        if name:
                            failures, checks = subset_flags(full, font, groups[name])
                            found += failures
                            summary['measurements'] += checks
                            size = file.stat().st_size
                            if name == 'latin-basic' and size >= BASIC_LIMIT:
                                found.append(dict(kind='display-basic-size', bytes=size))
                            summary['subsets'][name] = dict(bytes=size, glyphs=len(font.getGlyphOrder()),
                                characters=len(font.getBestCmap()), sha256=hashlib.sha256(file.read_bytes()).hexdigest())
                        report['flags'].extend(dict(cut=cut, file=file.name, **flag) for flag in found)
            report['cuts'][cut] = summary
            print(f"{cut.title()}: {summary['license_files']} licensed files, Latin basic "
                  f"{summary['subsets']['latin-basic']['bytes']} bytes, {summary['measurements']} shaping checks", flush=True)
    if css is None and fonts.resolve() == (ROOT/'display/fonts').resolve():
        css = ROOT/'display/fonts.css'
    if css:
        report['flags'] += css_flags(css, sorted(sources))
    else:
        for source in sources:
            report['flags'] += css_flags(source.parent/'fonts.css', [source])
    print(f"Display subset/license gate: {len(report['flags'])} flags")
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fonts', type=Path, default=ROOT/'display/fonts')
    parser.add_argument('--css', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = verify(args.fonts, args.css)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    raise SystemExit(bool(report['flags']))
