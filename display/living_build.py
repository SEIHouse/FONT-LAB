"""Generate isolated drawing closures directly from the one shared engine source."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ('engine.js', 'display/stroke_geometry.js', 'display/spacing.js',
           'display/living-engine.js', 'display/living.js', 'display/motion_profiles.json',
           'display/cuts/soft.json', 'display/cuts/edge.json', 'display/cuts/ink.json', 'display/cuts/wide.json',
           'font_builder.py', 'display/outline_cleanup.py', 'display/counter_geometry.py',
           'verify_display_shapes.py', 'display/probe_motion.py', 'display/living_build.py')


def motion_digest():
    """Bind certification to every source/settings file that can change frame geometry."""
    digest = hashlib.sha256()
    for name in SOURCES:
        digest.update(name.encode())
        digest.update((ROOT/name).read_bytes().replace(b'\r\n', b'\n'))
    return digest.hexdigest()


def fixture_digest():
    """Bind a certificate to the separately reviewed, immutable motion witnesses."""
    digest=hashlib.sha256()
    directory=ROOT/'tests/fixtures/display-motion-topology'
    files=sorted(directory.glob('*.json'))
    if len(files)!=44:
        return None
    for file in files:
        digest.update(file.name.encode())
        digest.update(file.read_bytes().replace(b'\r\n',b'\n'))
    return digest.hexdigest()


def engine_factory(*, audit=False):
    """Give each closure its own parameters, glyph caches, window and clip collector."""
    sources = list(SOURCES[:4])
    if audit:
        sources.insert(3, 'export_tail.js')
    source = '\n'.join((ROOT/name).read_text(encoding='utf-8') for name in sources)
    if audit:
        source = source.replace('return {layout:livingLayout, frame:livingFrame};',
                                'return {layout:livingLayout,frame:livingFrame,apply:livingApply,'
                                'records:()=>({...window.exportGlyphs(P.base),...window.exportAlternates(P.base)}),'
                                'contrast:()=>P.contrast};')
    return ('function createLivingEngine(){\nconst livingDefs=[];const window={};\n'
            'const document={getElementById:()=>({insertAdjacentHTML:(_where,html)=>livingDefs.push(html)})};\n'
            + source + '\n}\n')


def profiles_for_lab():
    """Fail closed on stale/failed certification; drafts and unreviewed profiles cannot export."""
    profiles = json.loads((ROOT/'display/motion_profiles.json').read_text(encoding='utf-8'))
    certificate = ROOT/'display/motion-certification.json'
    if certificate.exists():
        record = json.loads(certificate.read_text(encoding='utf-8'))
        if (record.get('source_sha256') == motion_digest() and record.get('fixture_sha256') == fixture_digest()
                and record.get('fixture_sha256') is not None and record.get('flags') == []):
            for profile in profiles['profiles']:
                profile['certified'] = profile['id'] in record.get('profiles', [])
    return profiles
