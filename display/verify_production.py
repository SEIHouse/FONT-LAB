"""Gate every manifest face with shape, topology, delivery, license and FontBakery checks."""
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unicodedata

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import freetype
from fontTools.ttLib import TTFont
from display.build_subsets import BASIC_LIMIT, display_groups, font_style
from display.counter_geometry import counter_flags, topology_flags
from display.production import ROOT, read_manifest, style_plan
from display.title_spacing import compiled_kerning, spacing_settings
from verify_display_alternates import feature_flags
from verify_display_shapes import (ALTERNATE_TOPOLOGY, COUNTER_TOPOLOGY, CUTS, blank_flags,
                                   flags, outline, render, verify as verify_canonical, web_flags)
from verify_display_subsets import css_flags, license_flags, subset_flags
from verify_shared_engine import audit_features


def reviewed_topology(slug, spacing, style='Regular'):
    """Read immutable reviewed cut/style topology; never capture it during a gate."""
    if slug in CUTS and style=='Regular':
        base = json.loads(COUNTER_TOPOLOGY.read_text(encoding='utf-8'))
        alternates = json.loads(ALTERNATE_TOPOLOGY.read_text(encoding='utf-8'))
        if spacing['variants'] != alternates['variants'][slug]:
            raise ValueError(f'{slug}: alternate manifest differs from reviewed topology')
        return base['cuts'][slug]['glyphs'] | alternates['cuts'][slug]['glyphs']
    suffix = '' if style=='Regular' else '-'+style.lower()
    file = ROOT/f'tests/fixtures/display-production-topology/{slug}{suffix}.json'
    if not file.is_file():
        raise ValueError(f'{slug}/{style}: add reviewed 400px topology to {file.relative_to(ROOT)} before shipping')
    reference = json.loads(file.read_text(encoding='utf-8'))
    if (reference['size_px'] != 400 or reference['variants'] != spacing['variants'] or
            reference['settings'] != spacing['settings']):
        raise ValueError(f'{slug}/{style}: reviewed topology size/design/settings do not match')
    return reference['glyphs']


def shape_face(source, font, woff, spacing, expected):
    names = font.getGlyphOrder()
    found = web_flags(font, woff)
    face = freetype.Face(str(source))
    stream = io.BytesIO()
    woff.flavor = None
    woff.save(stream)
    web_face = freetype.Face(io.BytesIO(stream.getvalue()))
    aperture_names = {name for code, name in font.getBestCmap().items() if unicodedata.category(chr(code))[0] in 'LN'}
    aperture_names.update(name for name in names if name.endswith(('.tf', '.numr', '.dnom')))
    aperture_names.update(name for spec in spacing['variants'].values() for name in spec['choices'].values())
    if set(expected) != aperture_names:
        found.append(dict(kind='counter-topology-inventory'))
    for index, name in enumerate(names):
        path = outline(font, name)
        failures = blank_flags(name, path) + flags(path, font['head'].unitsPerEm)
        bitmap = render(face, index)
        failures += counter_flags(bitmap, apertures=name in aperture_names)
        if name in aperture_names:
            if name not in expected:
                failures.append(dict(kind='missing-counter-topology'))
            else:
                failures += topology_flags(bitmap, expected[name])
        if render(web_face, index) != bitmap:
            failures.append(dict(kind='web-render'))
        if bool(path) != bool(any(bitmap['pixels'])):
            failures.append(dict(kind='missing-raster'))
        found.extend(dict(glyph=name, **flag) for flag in failures)
    return found, dict(glyphs=len(names), rendered=2*len(names), topology_glyphs=len(aperture_names))


def fontbakery(sources, directory):
    """Inspect process status and JSON totals; neither WARN nor an empty report passes."""
    directory.mkdir(parents=True, exist_ok=True)
    reports, found = {}, []
    with tempfile.TemporaryDirectory(prefix='seihouse-display-fontbakery-') as temporary:
        family = Path(temporary)
        copies = []
        for source in sources:
            target = family/source.name
            if target.exists():
                raise ValueError('Duplicate font filename in cut family: '+source.name)
            shutil.copyfile(source, target)
            copies.append(target)
        for profile in ('opentype', 'universal'):
            target = directory/(profile+'.json')
            command = [sys.executable, '-m', 'fontbakery', 'check-'+profile, '-n', '-C', '-e', 'WARN', '--json', str(target)]
            if profile == 'universal':
                command.append('--skip-network')
            command.extend(str(source) for source in copies)
            with (directory/(profile+'.txt')).open('w', encoding='utf-8') as log:
                completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False)
            counts = json.loads(target.read_text(encoding='utf-8')).get('result', {}) if target.exists() else {}
            reports[profile] = counts
            if (completed.returncode or not counts.get('PASS') or
                    any(counts.get(status, 0) for status in ('WARN', 'FAIL', 'ERROR', 'FATAL', '(not finished)'))):
                found.append(dict(kind='fontbakery', profile=profile, exit_code=completed.returncode, counts=counts))
            print(f'FontBakery {directory.name} ({len(sources)} faces) {profile}: {counts}', flush=True)
    return found, reports


def verify(manifest_file, report_dir, *, run_fontbakery=True):
    manifest, root = read_manifest(manifest_file)
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    report = dict(cuts={}, flags=[])
    sources = []
    slugs = {row['slug'] for row in manifest['cuts']}
    if set(CUTS) <= slugs:
        canonical = verify_canonical(root/'display/fonts')
        (report_dir/'canonical-shapes.json').write_text(json.dumps(canonical, indent=2)+'\n', encoding='utf-8')
        report['flags'].extend(canonical['flags'])
    with TTFont(ROOT/'fonts/SEIReader-Regular.otf') as reader:
        for cut in manifest['cuts']:
            plan = {face['label']: face for face in style_plan(cut['settings'])}
            if set(plan) != {face['label'] for face in cut['styles']}:
                report['flags'].append(dict(cut=cut['slug'], kind='production-style-inventory'))
            summary = {}
            cut_sources = []
            for face in cut['styles']:
                failures = []
                assets = {asset['path']: asset for asset in face['assets']}
                if not {face['otf'], face['woff2'], face['spacing']} <= set(assets):
                    raise ValueError('Style entry references an unlisted asset')
                for asset in face['assets']:
                    path = root/asset['path']
                    if path.stat().st_size != asset['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != asset['sha256']:
                        failures.append(dict(kind='production-asset-identity', file=asset['path']))
                source = root/face['otf']
                sources.append(source)
                cut_sources.append(source)
                spacing = json.loads((root/face['spacing']).read_text(encoding='utf-8'))
                if (face['settings'] != plan.get(face['label'], {}).get('settings') or
                        spacing['settings'] != spacing_settings(face['settings']) or
                        spacing['otf_sha256'] != hashlib.sha256(source.read_bytes()).hexdigest()):
                    failures.append(dict(kind='production-spacing-identity'))
                with TTFont(source) as font, TTFont(root/face['woff2']) as woff:
                    failures += license_flags(font, reader) + license_flags(woff, reader)
                    failures += feature_flags(font, spacing)
                    inherited, inherited_summary = audit_features(font)
                    failures += inherited
                    if (face['weight'] != font['OS/2'].usWeightClass or face['slope'] != font_style(font) or
                            face['family'] != (font['name'].getDebugName(16) or font['name'].getDebugName(1))):
                        failures.append(dict(kind='production-font-metadata'))
                    if spacing['kern'] != compiled_kerning(font):
                        failures.append(dict(kind='production-compiled-kerning'))
                    for ch, row in spacing['glyphs'].items():
                        if row['advance']*2 != font['hmtx'][row['name']][0]:
                            failures.append(dict(kind='production-advance', glyph=ch))
                    geometry = dict(glyphs=len(font.getGlyphOrder()), rendered=0)
                    if face['label'] != 'Regular' or cut['slug'] not in CUTS or not set(CUTS) <= slugs:
                        try:
                            reference = reviewed_topology(cut['slug'], spacing, face['label'])
                            shapes, geometry = shape_face(source, font, woff, spacing, reference)
                            failures += shapes
                        except ValueError as exc:
                            failures.append(dict(kind='production-reviewed-topology', reason=str(exc)))
                    basic_bytes, measurements = 0, 0
                    for subset, codes in display_groups(set(font.getBestCmap())).items():
                        file = source.with_suffix('.'+subset+'.woff2')
                        if file.relative_to(root).as_posix() not in assets:
                            failures.append(dict(kind='production-subset-inventory', subset=subset))
                        with TTFont(file) as web:
                            failures += license_flags(web, reader)
                            subset_failures, count = subset_flags(font, web, codes)
                            failures += [dict(subset=subset, **flag) for flag in subset_failures]
                            measurements += count
                        if subset == 'latin-basic':
                            basic_bytes = file.stat().st_size
                            if basic_bytes >= BASIC_LIMIT:
                                failures.append(dict(kind='display-basic-size', bytes=basic_bytes))
                report['flags'].extend(dict(cut=cut['slug'], style=face['label'], **flag) for flag in failures)
                summary[face['label']] = dict(**geometry, flags=len(failures), latin_basic_bytes=basic_bytes,
                                              subset_measurements=measurements, inherited=inherited_summary)
                print(f'{cut["name"]} {face["label"]}: {len(failures)} flags', flush=True)
            bakery = {}
            if run_fontbakery:
                # Related faces must share the same check collection: FontBakery
                # validates Oblique's binary style link against its Roman sibling.
                bakery_failures, bakery = fontbakery(cut_sources, report_dir/'fontbakery'/cut['slug'])
                report['flags'].extend(dict(cut=cut['slug'], **flag) for flag in bakery_failures)
            report['cuts'][cut['slug']] = dict(styles=summary, fontbakery=bakery)
    css_path = (root/manifest['css']).resolve()
    if not css_path.is_relative_to(root):
        raise ValueError('Production CSS escapes bundle root')
    report['flags'].extend(css_flags(css_path, sources))
    report['flag_counts'] = dict(Counter(flag['kind'] for flag in report['flags']))
    target = report_dir/'production.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Production gate: {len(report["flags"])} flags -> {target}', flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=HERE/'production-manifest.json')
    parser.add_argument('--report-dir', type=Path, default=ROOT/'dist/display-production-gates')
    parser.add_argument('--skip-fontbakery', action='store_true', help='Development-only; release CI always runs both profiles')
    args = parser.parse_args()
    report = verify(args.manifest, args.report_dir, run_fontbakery=not args.skip_fontbakery)
    raise SystemExit(bool(report['flags']))
