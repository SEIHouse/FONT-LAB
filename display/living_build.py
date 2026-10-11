"""Generate isolated drawing closures directly from the one shared engine source.

Motion certification is per cut: each cut's certificate binds the shared drawing
sources, that cut's settings and motion profile, and that cut's reviewed witnesses.
Changing one cut therefore needs only that cut re-reviewed; an engine change still
needs every cut.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEWED = ROOT/'tests/fixtures/display-motion-topology'
CERTIFICATE = ROOT/'display/motion-certification.json'
# The drawing closure, in load order.
FACTORY_SOURCES = ('engine.js', 'display/stroke_geometry.js', 'display/spacing.js', 'display/living-engine.js')
# Every shared file that can change frame geometry or its checks.
SHARED_SOURCES = FACTORY_SOURCES + ('display/living.js', 'font_builder.py', 'display/outline_cleanup.py',
                                    'display/counter_geometry.py', 'verify_display_shapes.py',
                                    'display/probe_motion.py', 'display/living_build.py')
# Reviewed poses: rest, the seven nonzero axis corners and three intermediate breaths.
STATES = [dict(id='rest', weight=0, slant=0, penAngle=0)] + [
    dict(id=f'extreme-{mask}', weight=int(bool(mask & 1)), slant=int(bool(mask & 2)), penAngle=int(bool(mask & 4)))
    for mask in range(1, 8)] + [
    dict(id=f'breath-{percent}', weight=percent/100, slant=percent/100, penAngle=percent/100)
    for percent in (25, 50, 75)]


def slug_of(name):
    """The cut builder's slug rule."""
    return name.lower().replace(' ', '-')


def motion_profiles():
    """The versioned motion limits for every cut that has them."""
    return json.loads((ROOT/'display/motion_profiles.json').read_text(encoding='utf-8'))


def profile_for(slug, profiles=None):
    """The motion profile whose cut has this slug, or None."""
    profiles = profiles or motion_profiles()
    return next((row for row in profiles['profiles'] if slug_of(row['cut']) == slug), None)


def motion_digest(slug):
    """Bind one cut's certificate to the shared sources, its settings and its motion profile."""
    digest = hashlib.sha256()
    for name in SHARED_SOURCES + (f'display/cuts/{slug}.json',):
        digest.update(name.encode())
        digest.update((ROOT/name).read_bytes().replace(b'\r\n', b'\n'))
    profiles = motion_profiles()
    digest.update(json.dumps(dict(schema=profiles.get('schema'), version=profiles.get('version'),
                                  profile=profile_for(slug, profiles)), sort_keys=True).encode())
    return digest.hexdigest()


def witness_files(slug):
    """One cut's reviewed witnesses, one file per motion state."""
    return [REVIEWED/f'{slug}-{state["id"]}.json' for state in STATES]


def fixture_digest(slug):
    """Bind a cut's certificate to its separately reviewed, immutable motion witnesses."""
    files = witness_files(slug)
    if not all(file.is_file() for file in files):
        return None
    digest = hashlib.sha256()
    for file in files:
        digest.update(file.name.encode())
        digest.update(file.read_bytes().replace(b'\r\n', b'\n'))
    return digest.hexdigest()


def certificate():
    """The per-cut certificate record; an older or missing file certifies nothing."""
    if not CERTIFICATE.exists():
        return dict(schema=2, cuts={})
    record = json.loads(CERTIFICATE.read_text(encoding='utf-8'))
    return record if record.get('schema') == 2 and isinstance(record.get('cuts'), dict) else dict(schema=2, cuts={})


def certified(slug, profile, record=None):
    """A cut is certified only while its sources, profile and witnesses are unchanged."""
    entry = (record or certificate())['cuts'].get(slug)
    witnesses = fixture_digest(slug)
    return bool(entry and profile and entry.get('profile') == profile['id'] and entry.get('flags') == []
                and witnesses is not None and entry.get('fixture_sha256') == witnesses
                and entry.get('source_sha256') == motion_digest(slug))


def engine_factory(*, audit=False):
    """Give each closure its own parameters, glyph caches, window and clip collector."""
    sources = list(FACTORY_SOURCES)
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
    profiles = motion_profiles()
    record = certificate()
    for profile in profiles['profiles']:
        profile['certified'] = certified(slug_of(profile['cut']), profile, record)
    return profiles
