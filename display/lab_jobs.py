"""Display Lab jobs run by the local Lab server, one process per job.

python -X utf8 display/lab_jobs.py build --input cut.json --result result.json

build    turns the Lab's current settings into a real draft font under dist/lab-builds/
promote  replaces a shipped cut's settings and rebuilds only that cut, its CSS, manifest,
         specimens and the Lab page
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from display.production import number, style_plan

BUILDS = ROOT/'dist/lab-builds'
NAME = re.compile(r'[A-Za-z][A-Za-z0-9]*(?:[ -][A-Za-z0-9]+)*')
# The Lab's slider ranges; a draft outside them came from a hand-edited file.
RANGES = dict(weight=(30, 220), letterWidth=(.7, 1.7), xHeight=(400, 620), capitalRoundness=(0, 320),
              lowercaseRoundness=(0, 1), uprightStraightness=(.4, 1), ascender=(620, 800), contrast=(1, 6),
              penAngle=(-60, 60), slant=(-6, 16), spaceBetweenAllLetters=(-30, 120), wordSpace=(120, 480))
CHOICES = dict(corners=('soft', 'cut'), ends=('round', 'flat'), joins=('round', 'sharp'), pen=('oval', 'nib'))
FLAGS = ('uFoot', 'overshoot', 'italicForms')
# Browser-only bookkeeping never reaches a cut file.
DRAFT_ONLY = ('savedAt',)


def validate(cut):
    """Reject anything the Lab could not have produced before a builder sees it."""
    if not isinstance(cut, dict):
        raise ValueError('A cut must be a JSON object')
    name = cut.get('name')
    if not isinstance(name, str) or len(name) > 40 or not NAME.fullmatch(name):
        raise ValueError('Cut names use letters, digits, single spaces or hyphens (up to 40 characters)')
    for key, (lower, upper) in RANGES.items():
        if key in cut or key in ('weight', 'contrast', 'lowercaseRoundness', 'spaceBetweenAllLetters'):
            number(cut.get(key), key, lower, upper)
    for key, allowed in CHOICES.items():
        if key in cut and cut[key] not in allowed:
            raise ValueError(f'{key} must be one of: '+', '.join(allowed))
    for key in FLAGS:
        if key in cut and not isinstance(cut[key], bool):
            raise ValueError(f'{key} must be true or false')
    for key in ('letterSpace', 'pairSpace', 'alternates'):
        if key in cut and not isinstance(cut[key], dict):
            raise ValueError(f'{key} must be an object')
    clean = {key: value for key, value in cut.items() if key not in DRAFT_ONLY}
    style_plan(clean)
    return clean


def slug_of(name):
    """Match the builder's own slug rule."""
    return name.lower().replace(' ', '-')


def build(cut):
    """Build Regular for a draft into its own stamped folder; keep only the newest build."""
    from display.make_display import build_style
    cut = validate(cut)
    cut.pop('production', None)
    slug = slug_of(cut['name'])
    folder = BUILDS/slug
    stamp = time.strftime('%Y%m%d-%H%M%S')
    out = folder/stamp
    out.mkdir(parents=True, exist_ok=False)
    print(f'Building {cut["name"]} from the Lab settings…', flush=True)
    otf = build_style(cut, out, metadata_dir=out)
    for old in folder.iterdir():
        if old != out and old.is_dir():
            shutil.rmtree(old, ignore_errors=True)
    rel = lambda path: '/'+path.relative_to(ROOT).as_posix()
    return dict(slug=slug, name=cut['name'], stamp=stamp, otf=rel(otf), woff2=rel(otf.with_suffix('.woff2')),
                spacing=rel(out/f'spacing_{slug}.json'))


def promote(cut):
    """Replace an existing shipped cut's settings, then rebuild just that cut and the Lab."""
    from display.build_all_cuts import build_all
    cut = validate(cut)
    slug = slug_of(cut['name'])
    target = HERE/'cuts'/f'{slug}.json'
    if not target.is_file():
        raise ValueError(f'There is no shipped cut named {cut["name"]}. New cuts still need the full release steps.')
    existing = json.loads(target.read_text(encoding='utf-8'))
    if existing['name'] != cut['name']:
        raise ValueError(f'Use the exact shipped name, {existing["name"]}')
    # Keep the file's existing key order so the change reads as a small diff.
    # JavaScript sends 1.0 as 1; keep the file's float spelling for unchanged values.
    for key, value in cut.items():
        if isinstance(existing.get(key), float) and type(value) is int and existing[key] == value:
            cut[key] = existing[key]
    merged = {**existing, **cut}
    target.write_text(json.dumps(merged, indent=2, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')
    print(f'Saved display/cuts/{slug}.json; rebuilding {cut["name"]}…', flush=True)
    build_all(only=[slug])
    print('Rebuilding the Lab page…', flush=True)
    subprocess.run([sys.executable, '-X', 'utf8', str(HERE/'build_display_page.py')], check=True, cwd=ROOT)
    return dict(slug=slug, name=cut['name'], changed=sorted(key for key in merged if existing.get(key) != merged[key]))


JOBS = dict(build=build, promote=promote)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('job', choices=sorted(JOBS))
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--result', type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding='utf-8'))
    try:
        result = dict(ok=True, **JOBS[args.job](payload.get('cut')))
    except Exception as error:  # reported to the Lab; the traceback stays in the job log
        import traceback
        traceback.print_exc()
        result = dict(ok=False, error=str(error))
    args.result.write_text(json.dumps(result, ensure_ascii=False)+'\n', encoding='utf-8')
    raise SystemExit(0 if result['ok'] else 1)


if __name__ == '__main__':
    main()
