"""Gate the shared engine against frozen Reader output and real Display shaping.

The checked-in Reader fixture was captured before this refactor from all fifty
0.36 deliveries. The 0.36 release changed 0.35 licensing metadata only. A local
0.35 font directory can additionally establish that every CFF program, hint,
metric and layout table still matches that release.
"""
import argparse
import hashlib
import json
from pathlib import Path
import unicodedata

from fontTools.ttLib import TTFont

from build_subsets import STYLES, SUBSETS
from language_coverage import inventory, test_strings
from verify_latin import CLUSTERS, MARKS, shape

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT/'tests/fixtures/reader-0.36-identity.json'
CUTS = ('soft', 'edge', 'ink', 'wide')
DIGITS = '0123456789'
DIGIT_NAMES = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine')
# Exercise every established language documented in README, alongside all ten
# CLDR inventories. These are coverage examples, not native-reader certification.
FOUNDATION = {
    'en': 'The quick brown fox jumps over the lazy dog.',
    'es': '¡Qué alegría! El niño llegó mañana.',
    'fr': '« Café, garçon : où êtes-vous ? »',
    'pt': 'João põe açúcar no café e lê notícias.',
    'de': '„Ärger über süße Grüße und größere Häuser.“',
    'it': 'Perché l\u2019abilità è già più utile?',
    'nl': 'IJsselmeer: ideeën, één café en naïeve woorden.',
    'ca': 'L\u2019al·lota dóna informació a l\u2019illa.',
    'da': 'Rødgrød, æbletræer og blåbær på øen.',
    'no': 'Blåbær, øyer og ærlige spørsmål.',
    'sv': 'Åsa läser högt om öl och gröna träd.',
    'fi': 'Hyvää päivää! Yö, äiti ja lämmin sää.',
    'is': 'Þóra sér nýja eyju, æði og gömul orð.',
}


def digest(data):
    """Hash bytes or a deterministic JSON representation, including hint masks."""
    if not isinstance(data, bytes):
        data = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                          default=lambda value: {'bytes': bytes(value).hex()}).encode()
    return hashlib.sha256(data).hexdigest()


def table_hashes(font):
    """Hash every SFNT table; normalize only build-time head bookkeeping.

    FontBuilder and the hint tool stamp head.created/head.modified. The file
    checksum consequently changes as well. No outline, hint, name, metric or
    layout field is excluded from this comparison.
    """
    head = font['head']
    saved = head.created, head.modified, head.checkSumAdjustment
    head.created = head.modified = head.checkSumAdjustment = 0
    try:
        return {tag: digest(font.getTableData(tag)) for tag in sorted(font.keys())
                if tag != 'GlyphOrder'}
    finally:
        head.created, head.modified, head.checkSumAdjustment = saved


def cff_programs(font):
    """Fingerprint all Type 2 outline/hint programs and their shared hint data."""
    cff = font['CFF '].cff
    top = cff.topDictIndex[0]
    programs = {}
    for name in font.getGlyphOrder():
        char = top.CharStrings[name]
        char.decompile()
        programs[name] = char.program
    subrs = []
    for array in (cff.GlobalSubrs, getattr(top.Private, 'Subrs', [])):
        result = []
        for subr in array:
            subr.decompile()
            result.append(subr.program)
        subrs.append(result)
    return dict(glyphs=digest(programs), subroutines=digest(subrs),
                private_dict=digest(top.Private.rawDict))


def font_identity(file):
    """Capture immutable evidence without a fixture-regeneration CLI shortcut."""
    with TTFont(file, recalcTimestamp=False) as font:
        return dict(sha256=digest(file.read_bytes()), glyphs=len(font.getGlyphOrder()),
                    tables=table_hashes(font), programs=cff_programs(font))


def reader_flags(directory, fixture, baseline=None):
    """Check all ten full styles and thirty subsets against the frozen delivery."""
    flags, files = [], {}
    for filename, expected in fixture['files'].items():
        file = directory/filename
        if not file.exists():
            flags.append(dict(kind='reader-missing-file', file=filename))
            continue
        actual = font_identity(file)
        tables = set(expected['tables']) | set(actual['tables'])
        different = [tag for tag in sorted(tables)
                     if expected['tables'].get(tag) != actual['tables'].get(tag)]
        if different:
            flags.append(dict(kind='reader-table-identity', file=filename, tables=different))
        if expected['programs'] != actual['programs']:
            flags.append(dict(kind='reader-outline-or-hint-identity', file=filename))
        row = dict(glyphs=actual['glyphs'], byte_identical=actual['sha256']==expected['sha256'],
                   normalized_tables_identical=not different,
                   outline_and_hint_programs_identical=expected['programs']==actual['programs'])
        if baseline is not None:
            old_file = baseline/filename
            if not old_file.exists():
                flags.append(dict(kind='reader-035-missing-file', file=filename))
            else:
                old = font_identity(old_file)
                # 0.35 -> 0.36 changed family/version/license strings in name/CFF
                # and fontRevision in head. All remaining tables are protected.
                relevant = (set(old['tables']) | set(actual['tables']))-{'head', 'name', 'CFF '}
                changed = [tag for tag in sorted(relevant)
                           if old['tables'].get(tag) != actual['tables'].get(tag)]
                row['matches_035_geometry_metrics_layout'] = not changed and old['programs']==actual['programs']
                if not row['matches_035_geometry_metrics_layout']:
                    flags.append(dict(kind='reader-035-identity', file=filename, tables=changed))
                with TTFont(old_file) as old_font, TTFont(file) as font:
                    for field in ('unitsPerEm', 'xMin', 'yMin', 'xMax', 'yMax', 'flags', 'macStyle'):
                        if getattr(old_font['head'], field) != getattr(font['head'], field):
                            flags.append(dict(kind='reader-035-head-geometry', file=filename, field=field))
        files[filename] = row
    return flags, files


def audit_features(font):
    """Test inherited features by their shaped behavior, including mark offsets."""
    found = []
    cmap = font.getBestCmap()

    def check(condition, kind, **detail):
        if not condition:
            found.append(dict(kind=kind, **detail))

    required = {'GSUB': {'ccmp', 'locl', 'liga', 'frac', 'tnum', 'sups', 'subs'},
                'GPOS': {'kern', 'mark', 'mkmk'}}
    for tag, features in required.items():
        actual = ({record.FeatureTag for record in font[tag].table.FeatureList.FeatureRecord}
                  if tag in font and font[tag].table.FeatureList else set())
        check(features <= actual, 'display-features', table=tag, missing=sorted(features-actual))
    if any(flag['kind']=='display-features' for flag in found):
        return found, dict(language_strings=0, languages=0)

    classes = font['GDEF'].table.GlyphClassDef.classDefs if 'GDEF' in font else {}
    for mark in MARKS:
        name = cmap.get(ord(mark))
        check(name is not None and font['hmtx'][name][0]==0 and classes.get(name)==3,
              'display-combining-mark', character=f'U+{ord(mark):04X}')
    for text in CLUSTERS:
        result = shape(font, text)
        check(all(name!='.notdef' for name, *_ in result), 'display-mark-glyph', text=text)
        check(result==shape(font, unicodedata.normalize('NFC', text))==
              shape(font, unicodedata.normalize('NFD', text)), 'display-mark-canonical', text=text)
        check(all(advance==0 for name, advance, *_ in result if classes.get(name)==3),
              'display-mark-advance', text=text)
    check(shape(font, 'x\u0301')!=shape(font, 'x\u0301', mark=False), 'display-mark-attachment')
    check(shape(font, 'x\u0302\u0301')!=shape(font, 'x\u0302\u0301', mkmk=False), 'display-mark-stack')
    # i + macron now composes to encoded ī; use an unencoded double-acute
    # combination to exercise contextual dot removal directly.
    for text, name in (('i\u030b', 'i.dotless'), ('j\u0301', 'j.dotless'), ('ị́', 'i.below.dotless')):
        check(shape(font, text)[0][0]==name, 'display-dotless', text=text)
    check([row[0] for row in shape(font, 'fi', language='tr')]==['f', 'i.loclTRK'],
          'display-turkish-local-form')
    check(shape(font, 'fi')[0][0]==cmap[0xFB01], 'display-default-ligature')
    check(shape(font, 'ŞşŢţ', language='ro')==shape(font, 'ȘșȚț', language='ro'),
          'display-romanian-local-form')
    check(shape(font, 'ŞşŢţ', language='tr')!=shape(font, 'ȘșȚț', language='tr'),
          'display-turkish-cedilla')

    checks = 0
    locales = inventory()['locales']
    for code, row in locales.items():
        for text in [*test_strings(row), row['sample']]:
            result = shape(font, text, language=code)
            check(all(ord(ch) in cmap for ch in text), 'display-language-encoding', language=code, text=text)
            check(all(name!='.notdef' for name, *_ in result), 'display-language-fallback', language=code, text=text)
            check(result==shape(font, unicodedata.normalize('NFC', text), language=code)==
                  shape(font, unicodedata.normalize('NFD', text), language=code),
                  'display-language-canonical', language=code, text=text)
            checks += 1
    for code, text in FOUNDATION.items():
        result = shape(font, text, language=code)
        check(all(ord(ch) in cmap for ch in text), 'display-foundation-encoding', language=code)
        check(all(name!='.notdef' for name, *_ in result), 'display-foundation-fallback', language=code)
        check(result==shape(font, unicodedata.normalize('NFD', text), language=code),
              'display-foundation-canonical', language=code)
        checks += 1

    tnum = shape(font, DIGITS, kern=False, tnum=True)
    check([row[0] for row in tnum]==[name+'.tf' for name in DIGIT_NAMES], 'display-tabular-substitution')
    check(len({row[1] for row in tnum})==1, 'display-tabular-advances')
    for feature, text in (('sups', '⁰¹²³⁴⁵⁶⁷⁸⁹'), ('subs', '₀₁₂₃₄₅₆₇₈₉')):
        check([row[0] for row in shape(font, DIGITS, **{feature: True})]==[cmap[ord(ch)] for ch in text],
              'display-numeric-substitution', feature=feature)
        check(shape(font, '2', **{feature: True, 'tnum': True})==shape(font, '2', **{feature: True}),
              'display-numeric-feature-order', feature=feature)
    for text, expected in (
            ('1/2', ['one.numr', cmap[0x2044], 'two.dnom']),
            ('12/34', ['one.numr', 'two.numr', cmap[0x2044], 'three.dnom', 'four.dnom'])):
        for features in ({'frac': True}, {'frac': True, 'tnum': True}):
            check([row[0] for row in shape(font, text, **features)]==expected,
                  'display-fraction', text=text, features=features)
    check([row[0] for row in shape(font, '1⁄2')]==['one.numr', cmap[0x2044], 'two.dnom'],
          'display-direct-fraction')
    for separator in '.,':
        widths = {sum(row[1] for row in shape(font, digit+separator+digit, tnum=True)) for digit in DIGITS}
        check(len(widths)==1, 'display-tabular-decimals', separator=separator)
        for digit in DIGITS:
            for pair in (digit+separator, separator+digit):
                for tabular in (False, True):
                    unkerned = sum(row[1] for row in shape(font, pair, kern=False, tnum=tabular))
                    kerned = sum(row[1] for row in shape(font, pair, tnum=tabular))
                    check(kerned>unkerned, 'display-decimal-separator-spacing', text=pair, tabular=tabular)
    return found, dict(language_strings=checks, languages=len(locales)+len(FOUNDATION),
                      pinned_cldr_locales=len(locales), foundation_language_samples=len(FOUNDATION),
                      features={tag: sorted(tags) for tag, tags in required.items()})


def verify(reader_fonts, display_fonts, reader_baseline=None, reader_only=False, full_fonts_only=False):
    """Return a machine-readable gate report without modifying build products."""
    fixture = json.loads(FIXTURE.read_text(encoding='utf-8'))
    expected_files = {f'SEIReader-{style}{suffix}' for style, *_ in STYLES
                      for suffix in ('.otf', '.woff2', *[f'.{subset}.woff2' for subset in SUBSETS])}
    if set(fixture['files']) != expected_files:
        raise ValueError('The frozen Reader identity fixture must include all fifty deliveries')
    if full_fonts_only:
        fixture['files'] = {name: record for name, record in fixture['files'].items() if name.count('.')==1}
    found, reader = reader_flags(reader_fonts, fixture, reader_baseline)
    skeleton = (ROOT/'engine.js').read_text(encoding='utf-8').split('const P =', 1)[0]
    if digest(skeleton.encode()) != fixture['reader_skeleton_sha256']:
        found.append(dict(kind='shared-reader-skeleton'))
    if (ROOT/'display/engine.js').exists():
        found.append(dict(kind='forked-display-engine'))
    display = {}
    expected_cmap = fixture['cmap']
    for cut in (() if reader_only else CUTS):
        file = display_fonts/cut/f'SEIHouseDisplay-{cut.title()}.otf'
        with TTFont(file) as font:
            actual_cmap = {str(code): name for code, name in font.getBestCmap().items()}
            if actual_cmap != expected_cmap:
                found.append(dict(cut=cut, kind='display-shared-repertoire',
                                  missing=sorted(set(expected_cmap)-set(actual_cmap), key=int),
                                  extra=sorted(set(actual_cmap)-set(expected_cmap), key=int)))
            failures, summary = audit_features(font)
            found.extend(dict(cut=cut, **failure) for failure in failures)
            summary['glyphs'] = len(font.getGlyphOrder())
            summary['flags'] = len(failures)
            display[cut] = summary
            print(f"{cut.title()}: {summary['glyphs']} glyphs, {summary['languages']} languages, "
                  f"{summary['language_strings']} shaping strings, {len(failures)} feature flags")
    identical = sum(row['byte_identical'] for row in reader.values())
    print(f'Reader: {len(reader)} deliveries, {identical} byte-identical, '
          f"{sum(row['normalized_tables_identical'] for row in reader.values())} table-identical")
    print(f'Shared-engine gate: {len(found)} flags')
    return dict(reference=fixture['reference'], normalization=fixture['normalization'],
                scope=dict(reader_deliveries=len(fixture['files']), display_cuts=len(display)),
                reader=reader, display=display, flags=found)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reader-fonts', type=Path, default=ROOT/'fonts')
    parser.add_argument('--display-fonts', type=Path, default=ROOT/'display/fonts')
    parser.add_argument('--reader-baseline', type=Path, help='Optional preserved 0.35 fifty-file directory')
    parser.add_argument('--reader-only', action='store_true', help='Audit Reader candidates before Display rebuild')
    parser.add_argument('--full-fonts-only', action='store_true', help='Audit twenty full Reader files before subset build')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = verify(args.reader_fonts, args.display_fonts, args.reader_baseline,
                    args.reader_only, args.full_fonts_only)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    raise SystemExit(bool(report['flags']))
