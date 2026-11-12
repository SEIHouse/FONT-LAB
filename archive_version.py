"""Archive font versions and maintain the canonical website version registry (site/versions.json).

Uses only the Python standard library.

Usage:
  python archive_version.py --sync
      Verify all archived and current font hashes and refresh site/versions.json.

  python archive_version.py --recover-history --sync
      Extract any missing historical Sans (0.25..0.41) and Display (0.1 milestones)
      WOFF2 sets from Git commits into old/ with SHA256.json, then refresh site/versions.json.

  python archive_version.py --snapshot-sans --title "Short release title" --summary "Plain-language summary"
      Snapshot the current fonts/ directory into old/<current-version>/ before bumping phase4.json.

  python archive_version.py --snapshot-display <id> --title "Short title" --summary "Plain-language summary"
      Snapshot the current display/fonts/ cuts into old/display/<id>/ before rebuilding Display cuts.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
VERSIONS_JSON = ROOT / 'site' / 'versions.json'

STANDARD_STYLES = [
    ('Light', 300, 'normal', False),
    ('LightItalic', 300, 'italic', False),
    ('Regular', 400, 'normal', False),
    ('Italic', 400, 'italic', False),
    ('Medium', 500, 'normal', False),
    ('MediumItalic', 500, 'italic', False),
    ('SemiBold', 600, 'normal', False),
    ('SemiBoldItalic', 600, 'italic', False),
    ('Bold', 700, 'normal', False),
    ('BoldItalic', 700, 'italic', False),
]

NIGHT_STYLES = [
    ('LightNight', 300, 'normal', True),
    ('LightItalicNight', 300, 'italic', True),
    ('RegularNight', 400, 'normal', True),
    ('ItalicNight', 400, 'italic', True),
    ('MediumNight', 500, 'normal', True),
    ('MediumItalicNight', 500, 'italic', True),
]

DISPLAY_CUTS = [
    ('soft', 'Soft'),
    ('edge', 'Edge'),
    ('ink', 'Ink'),
    ('wide', 'Wide'),
]

# Historical Git commits for recovering previously unarchived Sans releases into old/<version>/
HISTORICAL_SANS_GIT = [
    ('0.25', '8e6ff15', False),
    ('0.26', 'bd77e3b', False),
    ('0.35', 'f18c6e8', False),
    ('0.36', 'bc61d90', False),
    ('0.39', 'd4d0802', True),
    ('0.40', '3c05afe', True),
    ('0.41', '5a77228', True),
]

# Historical Git commits for recovering Display 0.1 milestones into old/display/<id>/
HISTORICAL_DISPLAY_GIT = [
    ('0.1-initial', '341ed29', 'Initial Display 0.1 prototype cuts'),
    ('0.1-step2-shapes', '1689770', 'Clean flat caps, bounded miters, and shared engine unification'),
    ('0.1-counter-repair', '69b6494', 'Heavy-pen counter opening in Soft and Edge'),
    ('0.1-step3-spacing', '554ffad', 'Capital-height title kerning and all-caps spacing'),
    ('0.1-step4-alternates', 'ac1a9da', 'Individual letter alternates and stylistic sets ss01-ss08'),
    ('0.1-pre-step5', 'f135ed1', 'Plain W/w default, ecosystem license metadata, and production polish'),
]

# Canonical plain-language release notes for SEIHouse Sans (newest first except current, which is read/merged dynamically)
SANS_METADATA = {
    '0.42': {
        'shortTitle': 'Light & Medium Night-mode grades',
        'date': '2026-11-12',
        'summary': 'Added Night-mode optical grades for Light and Medium alongside Regular so all three reading weights soften glare on dark screens without changing letter widths or shifting line breaks.',
        'highlights': [
            '6 Night-mode faces across Light, Regular, and Medium (upright and real italic)',
            'Exact Day-mode character widths and kerning so toggling Day/Night never reflows a page',
            '16 full web faces covering 148 verified languages across Latin, Cyrillic, Greek, and Vietnamese',
        ],
    },
    '0.41': {
        'shortTitle': 'Rare Latin, African & Celtic languages (148 locales)',
        'date': '2026-11-11',
        'summary': 'Added 54 characters and accents for Welsh, Irish, Scottish Gaelic, Asturian, Yoruba, Lingala, Ewe, Akan, Bambara, and more, plus Lithuanian dotless-į and Makhuwa capital TT spacing.',
        'highlights': [
            '54 new Latin, African, Celtic, and European letters and precomposed accents',
            '148 pinned Unicode CLDR locales (161 verified languages total)',
            '100% of existing 0.40 letter shapes and spacing preserved unchanged',
        ],
    },
    '0.40': {
        'shortTitle': 'Smoother g, S, and question-mark curves',
        'date': '2026-11-11',
        'summary': 'Gave lowercase g the same smooth shared bowl as b/d/p/q and softened capital S and ? into continuous reading curves while preserving all letter widths and spacing.',
        'highlights': [
            'Unified lowercase g bowl matching b, d, p, and q',
            'Continuous, calmer curves on capital S and ?',
            'Identical spacing and line breaks across all weights and Night grades',
        ],
    },
    '0.39': {
        'shortTitle': 'Cyrillic, Greek, Vietnamese & first Night grade',
        'date': '2026-10-25',
        'summary': 'Completed Latin Extended-A, common Slavic Cyrillic (with cursive italics), modern Greek, and full Vietnamese tone stacks, followed by the first Regular & Italic Night-mode optical grade.',
        'highlights': [
            'Added Cyrillic, modern Greek, and 88 Vietnamese vowel-and-tone letters',
            'Introduced RegularNight & ItalicNight (-4 stroke units on dark backgrounds)',
            'Verified even size density across 15px-22px app reading steps',
        ],
    },
    '0.36': {
        'shortTitle': 'Renamed to SEIHouse Sans & Ecosystem License',
        'date': '2026-10-03',
        'summary': 'Officially named the family SEIHouse Sans and embedded the SEIHouse Sans Ecosystem License 1.0 in every font file while keeping legacy SEIReader stylesheets working.',
        'highlights': [
            'Adopted the SEIHouse Sans family name alongside SEIReader compatibility',
            'Embedded SEIHouse Productions LLC ownership and Ecosystem License 1.0',
            'Preserved every 0.35 letter drawing and spacing value unchanged',
        ],
    },
    '0.35': {
        'shortTitle': 'Sharp stroke-join ink repair & paragraph audit',
        'date': '2026-10-02',
        'summary': 'Fixed tiny missing-ink gaps where diagonal strokes met in v, V, w, W, and digits, and audited full-paragraph sentence and apostrophe spacing across all ten styles.',
        'highlights': [
            'Clean, solid ink joins in v/V/w/W, numeric alternates, and symbols',
            'Full-paragraph spacing inspection across upright and italic weights',
            'Zero changes to letter widths, weights, or kerning pairs',
        ],
    },
    '0.34': {
        'shortTitle': 'First 10 multilingual alphabets & decimal spacing',
        'date': '2026-10-02',
        'summary': 'Added 94 letters for Polish, Czech, Hungarian, Romanian, Turkish, Hausa, Kurdish, Māori, Igbo, and Uzbek, plus clearer breathing room around decimal points and commas in numbers.',
        'highlights': [
            '94 new letters including hooked Hausa capitals, Turkish dotted-i, and Romanian commas',
            'Roomier decimal periods and commas in prices and percentages (1,234.56 / 8.50%)',
            'Created the lean app font bundle format',
        ],
    },
    '0.33': {
        'shortTitle': 'Latin accent foundation & international quotes',
        'date': '2026-10-01',
        'summary': 'Built automatic mark attachment and accent stacking for 19 combining marks, dotless i/j under accents, and local European quotation marks and apostrophes.',
        'highlights': [
            '19 combining accents with automatic stacking and italic placement',
            'Identical rendering whether text is precomposed (NFC) or decomposed (NFD)',
            'Added German/Polish/French quotes and lexical apostrophes',
        ],
    },
    '0.32': {
        'shortTitle': 'Quieter punctuation, smoother digits & balanced weights',
        'date': '2026-10-01',
        'summary': 'Softened dots, commas, quotes, and dashes; redrew 2, 3, 5, 6, 8, and 9 with continuous curves; and tuned Light (slightly firmer) and Medium (slightly lighter) for small screens.',
        'highlights': [
            'Curved comma/quote tails and gentler punctuation weight in prose',
            'Smoother figure curves across default, tabular, and fraction numerals',
            'Firmer Light (74) and calmer Medium (97) strokes for phone reading',
        ],
    },
    '0.31': {
        'shortTitle': 'Broader paragraph rhythm pass',
        'date': '2026-10-01',
        'summary': 'Tuned word-level rhythm across dense repeating stems and diagonals in words like minimum, murmur, river, climate, parallel, and everywhere across all ten styles.',
        'highlights': [
            'Balanced double-l (ll) and protected yw/tw separation',
            'Opened crowded italic ur and um combinations',
            'Preserved all character widths and earlier optical pairs',
        ],
    },
    '0.30': {
        'shortTitle': 'Optical pair spacing for snag words',
        'date': '2026-10-01',
        'summary': 'Measured and refined spacing around narrow letters and ligatures in snag words like Lian, Iñés, blade, Entry, Mei’s, acquittal, and ri/rn/cl/li.',
        'highlights': [
            'Joined fi and fl ligatures now space cleanly beside neighboring letters',
            'Extra small-size breathing room for tt and ry pairs',
            'Separate upright and italic optical pair tuning at every weight',
        ],
    },
    '0.29': {
        'shortTitle': 'Cohesive lowercase arches & bowls',
        'date': '2026-09-30',
        'summary': 'Refined h, n, and m shoulders, the lower curve of u, and shared b/d/p/q bowls so every lowercase letter sits naturally beside the 0.28 a/e/c/s curves.',
        'highlights': [
            'Continuous arches on h, n, and m with smooth stem joins',
            'Harmonized b, d, p, and q bowls with softly squared sides',
            'Handwriting-style italics kept their distinct lower branches and exits',
        ],
    },
    '0.28': {
        'shortTitle': 'Reading curves for a, e, c, s & roomier word space',
        'date': '2026-09-30',
        'summary': 'Introduced dedicated continuous reading curves for upright a, e, c, and s, gave i a touch more side room, and opened the word space from 0.205 em to 0.220 em.',
        'highlights': [
            'Individual reading curves for upright a, e, c, and s',
            'Word space opened to 0.220 em for calmer chapter lines',
            'Added the 4-column Literata & Rubik reference comparison',
        ],
    },
    '0.27': {
        'shortTitle': 'Rounder upright forms & raised quotation marks',
        'date': '2026-09-30',
        'summary': 'Applied long-form reading feedback: rounder and slightly wider upright letters, raised curly and straight quotes, and gentler lowercase pair spacing.',
        'highlights': [
            'Softer, slightly wider upright letter proportions',
            'Raised quotation marks with apostrophes tucked naturally near letters',
            'Added the 3-chapter reading test and device checklist',
        ],
    },
    '0.26': {
        'shortTitle': 'Tabular numbers, fractions & web subsets',
        'date': '2026-09-30',
        'summary': 'Added stat-screen tabular figures (tnum), stacked fractions (frac), superscripts and subscripts, and split web deliveries for faster browser loading.',
        'highlights': [
            'Equal-width tabular digits (tnum) so stat columns stay aligned',
            'Automatic fractions (1/2, ½, ¼, ¾) and superscript/subscript digits',
            'First multi-subset WOFF2 web stylesheet',
        ],
    },
    '0.25': {
        'shortTitle': 'First full Font Lab family & screen hinting',
        'date': '2026-09-30',
        'summary': 'First complete 10-style Font Lab build: 5 weights with real handwriting-inspired italics, ~1,800 automatic kerning pairs per style, joined fi/fl, and crisp screen hinting.',
        'highlights': [
            '5 weights (Light to Bold), each with upright and real italic forms',
            'Automatic optical pair spacing and joined fi / fl ligatures',
            'Alignment zones and autohinting for sharp small text',
        ],
    },
    '0.6': {
        'shortTitle': 'Original SEIHouse Soft prototype',
        'date': '2026-09-15',
        'summary': 'The earliest preserved prototype (SEIHouse Soft): heavier stroke weight, taller lowercase height, and the original squared-curve silhouette before long-form reading refinements.',
        'highlights': [
            'Original Regular upright prototype preserved for historical comparison',
            'Taller lowercase x-height (550) and heavier Regular stroke (108)',
            'Shows how far SEIHouse Sans has evolved for chapter reading',
        ],
    },
}

DISPLAY_METADATA = {
    '0.1': {
        'label': 'Display 0.1 · Current (Living Titles 0.1.3)',
        'shortTitle': 'Refined curves, 148 locales & certified Living Titles',
        'date': '2026-11-11',
        'summary': 'All four cuts (Soft, Edge, Ink, Wide) share the latest smooth reading curves, 148-language character set, stylistic alternates, compiled title kerning, and certified Living Title motion.',
        'highlights': [
            'Inherits Sans 0.40 smooth g/S/? curves and 0.41 rare Latin/African/Celtic characters',
            'Per-cut motion certification and flat-nib / true-italic Lab authoring',
            'Ships static OTF/WOFF2 cuts plus the @seihouse/living-titles 0.1.3 runtime',
        ],
    },
    '0.1-pre-step5': {
        'label': 'Display 0.1 · Milestone 6 (Production Ready)',
        'shortTitle': 'Plain W/w default, licensing & web subsets',
        'date': '2026-10-06',
        'summary': 'Made plain W/w the default across all four cuts (moving crossed W to optional ss04), embedded ecosystem licensing, and added 6 fast web subsets per cut.',
        'highlights': [
            'Plain W/w default in Soft, Edge, Ink, and Wide (crossed W in ss04)',
            'Matched SEIHouse ecosystem license metadata and sub-25 KB Latin-basic subsets',
            'Added finished-cut cover, poster, and tracklist specimen pages',
        ],
    },
    '0.1-step4-alternates': {
        'label': 'Display 0.1 · Milestone 5 (Letter Alternates)',
        'shortTitle': 'Custom letter designs & stylistic sets ss01-ss08',
        'date': '2026-10-06',
        'summary': 'Added selectable alternate designs for a/g, R, K/k, M/W, y, G, Q, and open/closed 4/6/9 so each cut has its own distinct signature letters.',
        'highlights': [
            '8 OpenType stylistic sets (ss01-ss08) baked into every Display font',
            'Each cut preset chooses defaults suited to its weight and mood',
            'Full kerning support across every alternate letterform',
        ],
    },
    '0.1-step3-spacing': {
        'label': 'Display 0.1 · Milestone 4 (Title Kerning)',
        'date': '2026-10-06',
        'summary': 'Introduced dedicated capital-height title kerning and optional all-caps spacing (cpsp) tuned to each cut’s geometry.',
        'highlights': [
            'Separate optical spacing policies for Soft, Edge, Ink, and Wide titles',
            'Additive cpsp capital spacing for all-caps covers and headers',
            'Exact width parity between the live Display Lab and built font files',
        ],
    },
    '0.1-counter-repair': {
        'label': 'Display 0.1 · Milestone 3 (Counter Repair)',
        'shortTitle': 'Opened crowded interiors in heavy cuts',
        'date': '2026-10-06',
        'summary': 'Added heavy-pen counter compensation so bold cuts like Soft and Edge keep clear, open spaces inside letters like a and e without losing stem weight.',
        'highlights': [
            'Repaired nearly closed lowercase a and e counters in Soft and Edge',
            'Horizontal strokes automatically reserve interior room at heavy weights',
            'Ink and Wide remained crisp and untouched',
        ],
    },
    '0.1-step2-shapes': {
        'label': 'Display 0.1 · Milestone 2 (Clean Shapes & Shared Engine)',
        'shortTitle': 'Repaired stroke caps/miters & unified engine',
        'date': '2026-10-04',
        'summary': 'Unified Display with the main Sans drawing engine, repaired angled flat terminals and sharp miters, and unlocked multilingual Cyrillic, Greek, and Vietnamese titles.',
        'highlights': [
            'Clean flat-cap and miter geometry with zero outline debris',
            'Shared core engine bringing 732 multilingual glyphs to every cut',
            'Passed FontBakery quality checks with 0 failures and 0 warnings',
        ],
    },
    '0.1-initial': {
        'label': 'Display 0.1 · Milestone 1 (Original Import)',
        'shortTitle': 'First Soft, Edge, Ink & Wide prototype cuts',
        'date': '2026-10-02',
        'summary': 'The initial imported SEIHouse Display 0.1 workshop introducing the four signature cut personalities before outline cleanup, counter repair, and title kerning.',
        'highlights': [
            'Established the four core Display voices: Soft, Edge, Ink, and Wide',
            'Basic Latin character set prior to shared-engine unification',
            'Preserved baseline showing how far title shapes and spacing progressed',
        ],
    },
}

NOTO_VERSIONS = [
    {
        'version': 'Refinement 01',
        'label': 'Balanced · Refinement 01',
        'shortTitle': 'Smoother bowls, clearer openings & steadier spacing',
        'date': '2026-11-11',
        'current': True,
        'summary': 'Refined pass on the chosen Balanced foundation: smoother curves in a, c, e, g, and s, coordinated arches in n, m, h, and r, lighter crossbars on e/f/t, and steadier word spacing.',
        'highlights': [
            'Builds directly on your selected Balanced (Study B) warmth direction',
            'Smoother lowercase bowls and cleaner interior openings',
            'Prototype Latin character set for side-by-side reading evaluation',
        ],
        'path': 'noto/studies/warmth/fonts/SEIHouseNotoBalanced-Regular.woff2',
    },
    {
        'version': 'Study B',
        'label': 'Original Balanced (Study B)',
        'shortTitle': 'Approved warmth foundation (unchanged baseline)',
        'date': '2026-10-28',
        'current': False,
        'summary': 'The original middle-ground study you selected as the SEIHouse Noto foundation (14-unit terminal rounding, 0.585 curve fullness, 1.025 width), kept unchanged as a fixed reference.',
        'highlights': [
            'Chosen foundation balancing crispness with gentle SEIHouse warmth',
            '14-unit rounded terminals and moderate curve fullness',
            'Preserved byte-for-byte to anchor future refinements',
        ],
        'path': 'noto/studies/warmth/fonts/SEIHouseNotoStudyB-Regular.woff2',
    },
    {
        'version': 'Study A',
        'label': 'Study A · Subtle Warmth',
        'shortTitle': 'Crisper corners & closer to neutral',
        'date': '2026-10-28',
        'current': False,
        'summary': 'Exploratory study with minimal corner rounding (3 source units) and narrower proportions (1.000 width) to test the crisp end of the warmth spectrum.',
        'highlights': [
            '3-unit subtle terminal rounding and tighter 0.545 curve fullness',
            'Standard 1.000 width factor',
            'Part of the initial three-way warmth study',
        ],
        'path': 'noto/studies/warmth/fonts/SEIHouseNotoStudyA-Regular.woff2',
    },
    {
        'version': 'Study C',
        'label': 'Study C · Pronounced Warmth',
        'shortTitle': 'Rounder terminals & wider, softer bowls',
        'date': '2026-10-28',
        'current': False,
        'summary': 'Exploratory study pushing softness further (29-unit terminal rounding, 0.625 curve fullness, 1.050 width) to test the warm boundary of the design space.',
        'highlights': [
            '29-unit pronounced terminal rounding and fuller 0.625 curves',
            'Wider 1.050 letter proportions',
            'Helped confirm Study B (Balanced) as the sweet spot',
        ],
        'path': 'noto/studies/warmth/fonts/SEIHouseNotoStudyC-Regular.woff2',
    },
]


def sha256_bytes(data: bytes) -> str:
    """Return lowercase hex SHA-256 digest."""
    return hashlib.sha256(data).hexdigest()


def write_lf(path: Path, text: str) -> None:
    """Write UTF-8 text with deterministic LF line endings across OSes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as handle:
        handle.write(text)


def git_blob(commit: str, rel_path: str) -> bytes | None:
    """Read exact file bytes from a Git commit, returning None if absent."""
    result = subprocess.run(
        ['git', 'show', f'{commit}:{rel_path}'],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def verify_woff2(data: bytes, label: str) -> None:
    """Ensure bytes form a valid WOFF2 header and declared byte length."""
    if len(data) < 12 or data[:4] != b'wOF2' or int.from_bytes(data[8:12], 'big') != len(data):
        raise ValueError(f'Invalid WOFF2 binary for {label}')


def recover_historical_archives() -> None:
    """Extract unarchived historical Sans and Display WOFF2 sets from Git into old/."""
    for version, commit, include_night in HISTORICAL_SANS_GIT:
        target_dir = ROOT / 'old' / version
        styles = list(STANDARD_STYLES) + (NIGHT_STYLES if include_night else [])
        hashes = {}
        target_dir.mkdir(parents=True, exist_ok=True)
        for style_name, _, _, _ in styles:
            filename = f'SEIReader-{style_name}.woff2'
            data = git_blob(commit, f'fonts/{filename}')
            if data is None:
                continue
            verify_woff2(data, f'{commit}:fonts/{filename}')
            dest = target_dir / filename
            if not dest.exists():
                dest.write_bytes(data)
            elif dest.read_bytes() != data:
                raise ValueError(f'Existing file {dest} differs from Git commit {commit}')
            hashes[filename] = sha256_bytes(data)
        if not hashes:
            raise RuntimeError(f'No WOFF2 files recovered for Sans {version} at {commit}')
        for meta_name in ('settings.json', 'phase4.json'):
            meta_bytes = git_blob(commit, meta_name)
            meta_dest = target_dir / meta_name
            if meta_bytes is not None and not meta_dest.exists():
                meta_dest.write_bytes(meta_bytes)
        write_lf(target_dir / 'SHA256.json', json.dumps(dict(sorted(hashes.items())), indent=2) + '\n')
        family_title = 'SEIHouse Sans' if float(version) >= 0.36 else 'SEIReader'
        write_lf(
            target_dir / 'README.md',
            f'# Preserved {family_title} {version}\n\n'
            f'Archived full WOFF2 family ({len(hashes)} faces) from release commit `{commit}`.\n'
            f'`SHA256.json` records the original font bytes for version history and comparison.\n'
            f'Do not rebuild or overwrite these preserved baseline files.\n',
        )
        print(f'Archived Sans {version} ({len(hashes)} WOFF2 faces) -> old/{version}/')

    for milestone_id, commit, description in HISTORICAL_DISPLAY_GIT:
        target_dir = ROOT / 'old' / 'display' / milestone_id
        target_dir.mkdir(parents=True, exist_ok=True)
        hashes = {}
        for slug, cut_name in DISPLAY_CUTS:
            filename = f'SEIHouseDisplay-{cut_name}.woff2'
            rel = f'display/fonts/{slug}/{filename}'
            data = git_blob(commit, rel)
            if data is None:
                raise RuntimeError(f'Missing {rel} in commit {commit}')
            verify_woff2(data, f'{commit}:{rel}')
            dest = target_dir / filename
            if not dest.exists():
                dest.write_bytes(data)
            elif dest.read_bytes() != data:
                raise ValueError(f'Existing file {dest} differs from Git commit {commit}')
            hashes[filename] = sha256_bytes(data)
        write_lf(target_dir / 'SHA256.json', json.dumps(dict(sorted(hashes.items())), indent=2) + '\n')
        write_lf(
            target_dir / 'README.md',
            f'# Preserved SEIHouse Display ({milestone_id})\n\n'
            f'{description} (commit `{commit}`).\n'
            f'`SHA256.json` records all four full WOFF2 cuts for historical comparison.\n',
        )
        print(f'Archived Display {milestone_id} (4 WOFF2 cuts) -> old/display/{milestone_id}/')


def collect_sans_faces(folder: Path, rel_prefix: str) -> tuple[list[dict], dict]:
    """Inspect a directory of SEIReader-*.woff2 files and build hashed face descriptors."""
    faces = []
    weights_found = set()
    night_weights = set()
    has_italic = False
    for style_name, weight, slant, is_night in STANDARD_STYLES + NIGHT_STYLES:
        filename = f'SEIReader-{style_name}.woff2'
        path = folder / filename
        if not path.exists():
            continue
        data = path.read_bytes()
        verify_woff2(data, str(path))
        faces.append({
            'path': f'{rel_prefix}/{filename}',
            'styleName': style_name,
            'weight': weight,
            'style': slant,
            'night': is_night,
            'bytes': len(data),
            'sha256': sha256_bytes(data),
        })
        if is_night:
            night_weights.add(weight)
        else:
            weights_found.add(weight)
            if slant == 'italic':
                has_italic = True
    if not faces:
        raise ValueError(f'No SEIReader WOFF2 files found in {folder}')
    capabilities = {
        'weights': sorted(weights_found),
        'italic': has_italic,
        'nightWeights': sorted(night_weights),
    }
    return faces, capabilities


def version_sort_key(ver: str) -> tuple[int, ...]:
    """Sort version strings like '0.6', '0.25', '0.42' numerically descending."""
    # Note: historically 0.6 -> 0.12 -> 0.25 -> 0.42 (minor integer after '0.').
    parts = [int(p) for p in ver.split('.')]
    return tuple(parts)


def build_versions_manifest(extra_sans_meta: dict | None = None, extra_display_meta: dict | None = None) -> dict:
    """Assemble and hash-check the complete site/versions.json structure."""
    existing = {}
    if VERSIONS_JSON.exists():
        existing = json.loads(VERSIONS_JSON.read_text(encoding='utf-8'))

    existing_sans = {
        item['version']: item
        for item in existing.get('tracks', {}).get('sans', {}).get('versions', [])
    }
    existing_display = {
        item['version']: item
        for item in existing.get('tracks', {}).get('display', {}).get('versions', [])
    }

    phase4 = json.loads((ROOT / 'phase4.json').read_text(encoding='utf-8'))
    current_sans_ver = phase4['version']
    living_pkg = json.loads((ROOT / 'packages' / 'living-titles' / 'package.json').read_text(encoding='utf-8'))
    living_ver = living_pkg['version']

    # 1. SEIHouse Sans versions: current in fonts/ + archived in old/<ver>/ + 0.6 in old/previous.woff2
    sans_entries = []

    current_faces, current_caps = collect_sans_faces(ROOT / 'fonts', 'fonts')
    cur_meta = {
        **existing_sans.get(current_sans_ver, {}),
        **SANS_METADATA.get(current_sans_ver, {}),
        **((extra_sans_meta or {}).get(current_sans_ver, {})),
    }
    sans_entries.append({
        'version': current_sans_ver,
        'label': f'SEIHouse Sans {current_sans_ver}',
        'shortTitle': cur_meta.get('shortTitle', f'Release {current_sans_ver}'),
        'date': cur_meta.get('date', datetime.date.today().isoformat()),
        'current': True,
        'summary': cur_meta.get('summary', phase4.get('scope', '')),
        'highlights': cur_meta.get('highlights', []),
        'capabilities': current_caps,
        'faces': current_faces,
    })

    old_root = ROOT / 'old'
    archived_dirs = []
    for child in old_root.iterdir():
        if child.is_dir() and re.fullmatch(r'\d+\.\d+(?:\.\d+)?', child.name) and child.name != current_sans_ver:
            archived_dirs.append(child)
    archived_dirs.sort(key=lambda d: version_sort_key(d.name), reverse=True)

    for folder in archived_dirs:
        ver = folder.name
        faces, caps = collect_sans_faces(folder, f'old/{ver}')
        # Verify against folder SHA256.json if present
        sha_file = folder / 'SHA256.json'
        if sha_file.exists():
            recorded = json.loads(sha_file.read_text(encoding='utf-8'))
            for face in faces:
                fname = Path(face['path']).name
                if fname in recorded and recorded[fname] != face['sha256']:
                    raise ValueError(f'SHA-256 mismatch for {face["path"]} against {sha_file}')
        meta = {
            **existing_sans.get(ver, {}),
            **SANS_METADATA.get(ver, {}),
            **((extra_sans_meta or {}).get(ver, {})),
        }
        family_name = 'SEIHouse Sans' if version_sort_key(ver) >= (0, 36) else 'SEIReader'
        sans_entries.append({
            'version': ver,
            'label': f'{family_name} {ver}',
            'shortTitle': meta.get('shortTitle', f'Archived {ver}'),
            'date': meta.get('date', ''),
            'current': False,
            'summary': meta.get('summary', f'Preserved {family_name} {ver} release.'),
            'highlights': meta.get('highlights', []),
            'capabilities': caps,
            'faces': faces,
        })

    # Include 0.6 prototype (old/previous.woff2)
    proto_path = old_root / 'previous.woff2'
    if proto_path.exists():
        proto_bytes = proto_path.read_bytes()
        verify_woff2(proto_bytes, str(proto_path))
        meta_06 = {**existing_sans.get('0.6', {}), **SANS_METADATA['0.6']}
        sans_entries.append({
            'version': '0.6',
            'label': 'SEIHouse Soft 0.6 (Prototype)',
            'shortTitle': meta_06['shortTitle'],
            'date': meta_06['date'],
            'current': False,
            'summary': meta_06['summary'],
            'highlights': meta_06['highlights'],
            'capabilities': {'weights': [400], 'italic': False, 'nightWeights': []},
            'faces': [{
                'path': 'old/previous.woff2',
                'styleName': 'Regular',
                'weight': 400,
                'style': 'normal',
                'night': False,
                'bytes': len(proto_bytes),
                'sha256': sha256_bytes(proto_bytes),
            }],
        })

    # 2. Title Engine / Display milestones
    display_entries = []
    cur_display_faces = []
    for slug, cut_name in DISPLAY_CUTS:
        rel_path = f'display/fonts/{slug}/SEIHouseDisplay-{cut_name}.woff2'
        data = (ROOT / rel_path).read_bytes()
        verify_woff2(data, rel_path)
        cur_display_faces.append({
            'cut': slug,
            'cutLabel': cut_name,
            'path': rel_path,
            'weight': 400,
            'style': 'normal',
            'bytes': len(data),
            'sha256': sha256_bytes(data),
        })
    disp_cur_meta = {
        **existing_display.get('0.1', {}),
        **DISPLAY_METADATA['0.1'],
        **((extra_display_meta or {}).get('0.1', {})),
    }
    display_entries.append({
        'version': '0.1',
        'label': f'Display 0.1 · Current (Living Titles {living_ver})',
        'shortTitle': disp_cur_meta['shortTitle'],
        'date': disp_cur_meta['date'],
        'current': True,
        'summary': disp_cur_meta['summary'],
        'highlights': disp_cur_meta['highlights'],
        'faces': cur_display_faces,
    })

    display_old_root = old_root / 'display'
    if display_old_root.exists():
        known_order = [
            '0.1-pre-step5',
            '0.1-step4-alternates',
            '0.1-step3-spacing',
            '0.1-counter-repair',
            '0.1-step2-shapes',
            '0.1-initial',
        ]
        found_dirs = {d.name: d for d in display_old_root.iterdir() if d.is_dir()}
        extra_ids = sorted([k for k in found_dirs if k not in known_order], reverse=True)
        ordered_ids = extra_ids + [k for k in known_order if k in found_dirs]
        for mid in ordered_ids:
            m_dir = found_dirs[mid]
            m_faces = []
            sha_file = m_dir / 'SHA256.json'
            recorded = json.loads(sha_file.read_text(encoding='utf-8')) if sha_file.exists() else {}
            for slug, cut_name in DISPLAY_CUTS:
                fname = f'SEIHouseDisplay-{cut_name}.woff2'
                fpath = m_dir / fname
                if not fpath.exists():
                    continue
                data = fpath.read_bytes()
                verify_woff2(data, str(fpath))
                digest = sha256_bytes(data)
                if fname in recorded and recorded[fname] != digest:
                    raise ValueError(f'SHA-256 mismatch for {fpath} against {sha_file}')
                m_faces.append({
                    'cut': slug,
                    'cutLabel': cut_name,
                    'path': f'old/display/{mid}/{fname}',
                    'weight': 400,
                    'style': 'normal',
                    'bytes': len(data),
                    'sha256': digest,
                })
            d_meta = {
                **existing_display.get(mid, {}),
                **DISPLAY_METADATA.get(mid, {}),
                **((extra_display_meta or {}).get(mid, {})),
            }
            display_entries.append({
                'version': mid,
                'label': d_meta.get('label', f'Display {mid}'),
                'shortTitle': d_meta.get('shortTitle', mid),
                'date': d_meta.get('date', ''),
                'current': False,
                'summary': d_meta.get('summary', f'Preserved Display milestone {mid}.'),
                'highlights': d_meta.get('highlights', []),
                'faces': m_faces,
            })

    # 3. SEIHouse Noto studies
    noto_entries = []
    for item in NOTO_VERSIONS:
        rel_path = item['path']
        data = (ROOT / rel_path).read_bytes()
        verify_woff2(data, rel_path)
        noto_entries.append({
            'version': item['version'],
            'label': item['label'],
            'shortTitle': item['shortTitle'],
            'date': item['date'],
            'current': item['current'],
            'summary': item['summary'],
            'highlights': item['highlights'],
            'capabilities': {'weights': [400], 'italic': False, 'nightWeights': []},
            'faces': [{
                'path': rel_path,
                'styleName': 'Regular',
                'weight': 400,
                'style': 'normal',
                'night': False,
                'bytes': len(data),
                'sha256': sha256_bytes(data),
            }],
        })

    default_sans_compare = '0.39' if any(v['version'] == '0.39' for v in sans_entries) else sans_entries[1]['version']
    return {
        'schema': 1,
        'tracks': {
            'sans': {
                'id': 'sans',
                'name': 'SEIHouse Sans',
                'subtitle': 'Long-form chapter reading & interface typeface',
                'currentVersion': current_sans_ver,
                'defaultCompareVersion': default_sans_compare,
                'workspaceUrl': '../../lab/index.html',
                'workspaceLabel': 'Open Reader Lab',
                'versions': sans_entries,
            },
            'display': {
                'id': 'display',
                'name': 'Title Engine · Display',
                'subtitle': 'Covers, chapter headers, posters & Living Titles',
                'currentVersion': '0.1',
                'livingTitlesVersion': living_ver,
                'defaultCompareVersion': '0.1-initial',
                'cuts': [{'id': slug, 'label': label} for slug, label in DISPLAY_CUTS],
                'workspaceUrl': '../../display/lab/index.html',
                'workspaceLabel': 'Open Display Lab',
                'versions': display_entries,
            },
            'noto': {
                'id': 'noto',
                'name': 'SEIHouse Noto',
                'subtitle': 'Warm Noto-based reading foundation study',
                'currentVersion': 'Refinement 01',
                'defaultCompareVersion': 'Study B',
                'workspaceUrl': '../../noto/studies/warmth/index.html',
                'workspaceLabel': 'Open Noto Warmth Study',
                'versions': noto_entries,
            },
        },
    }


def snapshot_current_sans(title: str, summary: str) -> None:
    """Copy current fonts/ full WOFF2 faces into old/<version>/ before bumping phase4.json."""
    phase4 = json.loads((ROOT / 'phase4.json').read_text(encoding='utf-8'))
    ver = phase4['version']
    dest_dir = ROOT / 'old' / ver
    dest_dir.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for style_name, _, _, _ in STANDARD_STYLES + NIGHT_STYLES:
        fname = f'SEIReader-{style_name}.woff2'
        src = ROOT / 'fonts' / fname
        if src.exists():
            data = src.read_bytes()
            verify_woff2(data, str(src))
            (dest_dir / fname).write_bytes(data)
            hashes[fname] = sha256_bytes(data)
    for meta_name in ('settings.json', 'phase4.json'):
        if (ROOT / meta_name).exists():
            shutil.copyfile(ROOT / meta_name, dest_dir / meta_name)
    write_lf(dest_dir / 'SHA256.json', json.dumps(dict(sorted(hashes.items())), indent=2) + '\n')
    write_lf(
        dest_dir / 'README.md',
        f'# Preserved SEIHouse Sans {ver}\n\n'
        f'{summary or title or f"Archived SEIHouse Sans {ver} full WOFF2 family."}\n'
        f'`SHA256.json` records all {len(hashes)} full WOFF2 faces.\n',
    )
    print(f'Snapshotted current Sans {ver} ({len(hashes)} faces) -> old/{ver}/')


def snapshot_current_display(milestone_id: str, title: str, summary: str) -> None:
    """Copy current display/fonts/ full WOFF2 cuts into old/display/<id>/."""
    if not re.fullmatch(r'[a-z0-9.-]+', milestone_id):
        raise ValueError('Milestone id may only use lowercase letters, digits, dots, and hyphens')
    dest_dir = ROOT / 'old' / 'display' / milestone_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for slug, cut_name in DISPLAY_CUTS:
        fname = f'SEIHouseDisplay-{cut_name}.woff2'
        src = ROOT / 'display' / 'fonts' / slug / fname
        data = src.read_bytes()
        verify_woff2(data, str(src))
        (dest_dir / fname).write_bytes(data)
        hashes[fname] = sha256_bytes(data)
    write_lf(dest_dir / 'SHA256.json', json.dumps(dict(sorted(hashes.items())), indent=2) + '\n')
    write_lf(
        dest_dir / 'README.md',
        f'# Preserved SEIHouse Display ({milestone_id})\n\n'
        f'{summary or title or f"Archived Display milestone {milestone_id}."}\n',
    )
    print(f'Snapshotted current Display cuts -> old/display/{milestone_id}/')


def sync_homepage_version(sans_version: str) -> None:
    """Update data-sans-version markers in index.html if present."""
    index_path = ROOT / 'index.html'
    if not index_path.exists():
        return
    html = index_path.read_text(encoding='utf-8')
    updated = re.sub(
        r'(<[^>]+data-sans-version[^>]*>)(?:SEIHouse Sans\s+)?\d+\.\d+(?:\.\d+)?(</[^>]+>)',
        lambda m: f'{m.group(1)}SEIHouse Sans {sans_version}{m.group(2)}'
        if 'SEIHouse Sans' in m.group(0)
        else f'{m.group(1)}{sans_version}{m.group(2)}',
        html,
    )
    if updated != html:
        write_lf(index_path, updated)
        print(f'Synced index.html version badges -> {sans_version}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recover-history', action='store_true', help='Recover unarchived versions from Git into old/')
    parser.add_argument('--snapshot-sans', action='store_true', help='Archive current fonts/ into old/<version>/')
    parser.add_argument('--snapshot-display', metavar='ID', help='Archive current display/fonts/ into old/display/<ID>/')
    parser.add_argument('--title', default='', help='Short release title when snapshotting')
    parser.add_argument('--summary', default='', help='Plain-language release summary when snapshotting')
    parser.add_argument('--sync', action='store_true', help='Write/refresh site/versions.json and sync homepage badges')
    args = parser.parse_args()

    if args.recover_history:
        recover_historical_archives()

    extra_sans = {}
    extra_display = {}
    if args.snapshot_sans:
        ver = json.loads((ROOT / 'phase4.json').read_text(encoding='utf-8'))['version']
        snapshot_current_sans(args.title, args.summary)
        if args.title or args.summary:
            extra_sans[ver] = {
                k: v for k, v in [('shortTitle', args.title), ('summary', args.summary), ('date', datetime.date.today().isoformat())] if v
            }

    if args.snapshot_display:
        snapshot_current_display(args.snapshot_display, args.title, args.summary)
        if args.title or args.summary:
            extra_display[args.snapshot_display] = {
                'label': f'Display · {args.title}' if args.title else f'Display {args.snapshot_display}',
                **({k: v for k, v in [('shortTitle', args.title), ('summary', args.summary), ('date', datetime.date.today().isoformat())] if v}),
            }

    if args.sync or args.snapshot_sans or args.snapshot_display or args.recover_history:
        manifest = build_versions_manifest(extra_sans, extra_display)
        write_lf(VERSIONS_JSON, json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
        sync_homepage_version(manifest['tracks']['sans']['currentVersion'])
        counts = {k: len(v['versions']) for k, v in manifest['tracks'].items()}
        print(f'Wrote site/versions.json -> Sans: {counts["sans"]}, Display: {counts["display"]}, Noto: {counts["noto"]}')
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
