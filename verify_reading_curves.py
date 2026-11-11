"""Audit the g/S/question refinement against an untouched Reader font directory.

python -X utf8 verify_reading_curves.py BASELINE [--fonts fonts] [--report report.json]
Only the three drawings and their inherited forms may change; every advance,
layout table, line metric and unrelated outline must remain identical.
"""
import argparse
import json
from pathlib import Path

from fontTools.ttLib import TTFont

from build_subsets import ALL_STYLES as STYLES
from verify_latin import shape
from verify_lowercase import recorded
from verify_shared_engine import legacy_identity, table_hashes
from phase4_support import release_version

ROOT = Path(__file__).resolve().parent
CURVE_CHARACTERS = 'gS?ĝğġģŚŜŞŠȘЅд'
SAMPLES = (
    'bridge ledger signed ginger bright digging',
    'She crossed the bridge. Was the ledger signed?',
    'S s SS g d b p q ?! minimum river climate parallel',
    'ŚŜŞŠȘ ĝğġģ Ѕ д', 'S\u0301 S\u030c g\u0306 g\u0307',
)


def audit(baseline, fonts):
    """Compare decomposed real outlines, all advances and HarfBuzz-positioned text."""
    report = {'reference': str(baseline), 'characters': CURVE_CHARACTERS, 'styles': {}, 'flags': []}
    for style, *_ in STYLES:
        filename = f'SEIReader-{style}.otf'
        with TTFont(baseline/filename, recalcTimestamp=False) as before, TTFont(fonts/filename, recalcTimestamp=False) as after:
            flags, changed, bearings = [], [], {}
            allowed = {before.getBestCmap()[ord(ch)] for ch in CURVE_CHARACTERS}
            if before.getGlyphOrder() != after.getGlyphOrder() or before.getBestCmap() != after.getBestCmap():
                flags.append({'kind': 'glyph-inventory'})
            for name in before.getGlyphOrder():
                if name not in after.getGlyphOrder():
                    continue
                old_width, old_bearing = before['hmtx'][name]
                width, bearing = after['hmtx'][name]
                if width != old_width:
                    flags.append({'kind': 'advance', 'glyph': name})
                if recorded(before, name) != recorded(after, name):
                    changed.append(name)
                    if name not in allowed:
                        flags.append({'kind': 'unrelated-outline', 'glyph': name})
                if bearing != old_bearing:
                    bearings[name] = [old_bearing, bearing]
                    if name not in allowed:
                        flags.append({'kind': 'unrelated-bearing', 'glyph': name})
            # A release may change only the version fields, not other metadata.
            version = release_version()
            old_version = before['name'].getDebugName(5).removeprefix('Version ')
            for name in before['name'].names:
                if name.nameID in (3, 5):
                    name.string = (name.toUnicode().removesuffix(old_version)+version).encode(name.getEncoding())
            before['head'].fontRevision = float(version)
            old_tables, tables = table_hashes(before), table_hashes(after)
            for tag in old_tables.keys() | tables.keys():
                if tag not in ('CFF ', 'hmtx') and old_tables.get(tag) != tables.get(tag):
                    flags.append({'kind': 'unrelated-table', 'table': tag})
            if legacy_identity(before)['metrics'] != legacy_identity(after)['metrics']:
                flags.append({'kind': 'line-metrics'})
            for sample in SAMPLES:
                if shape(before, sample) != shape(after, sample):
                    flags.append({'kind': 'positioned-text', 'text': sample})
            required = {before.getBestCmap()[ord(ch)] for ch in 'gS?'}
            if not required <= set(changed):
                flags.append({'kind': 'missing-refinement'})
            report['styles'][style] = {'glyphs': len(before.getGlyphOrder()),
                'changed_outlines': changed, 'unchanged_outlines': len(before.getGlyphOrder())-len(changed),
                'bearing_changes': bearings, 'advances_preserved': not any(f['kind']=='advance' for f in flags),
                'flags': flags}
            report['flags'].extend(dict(style=style, **flag) for flag in flags)
            print(f'{style}: {len(changed)} refined outlines, {len(flags)} flags', flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('--fonts', type=Path, default=ROOT/'fonts')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = audit(args.baseline, args.fonts)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    raise SystemExit(bool(result['flags']))
