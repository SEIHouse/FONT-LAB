"""Motion review and approval for rebuilt cuts, run by the local Lab server.

python -X utf8 display/motion_jobs.py review --input request.json --result result.json

review   brings a rebuilt cut's motion profile up to its built spacing, re-runs the
         full motion probe (every glyph, every reviewed pose) into dist/motion-review/,
         and lists each glyph whose reviewed witness would change.
approve  takes a clean review that is still current, copies its witnesses into the
         reviewed fixtures, certifies only those cuts and rebuilds the Lab page.

Approval is the human step: the review shows exactly what changed before anyone
approves it, and a review with any construction or counter problem cannot be approved.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from display.living_build import (CERTIFICATE, REVIEWED, STATES, certificate, certified, fixture_digest,
                                  motion_digest, motion_profiles, profile_for, slug_of)

REVIEWS = ROOT/'dist/motion-review'


def requested(payload):
    """The cuts to work on: those named, else every cut whose motion is not certified."""
    known = [slug_of(row['cut']) for row in motion_profiles()['profiles']]
    slugs = payload.get('cuts') or [slug for slug in known if not certified(slug, profile_for(slug))]
    if not isinstance(slugs, list) or not slugs or not set(slugs) <= set(known):
        raise ValueError('Choose shipped cuts with motion profiles: '+', '.join(known))
    return slugs


def sync_profile(slug):
    """Point a rebuilt cut's motion profile at its new built spacing; limits stay unchanged."""
    profiles = motion_profiles()
    profile = profile_for(slug, profiles)
    spacing = json.loads((HERE/f'spacing_{slug}.json').read_text(encoding='utf-8'))['settings']
    if profile['settings'] == spacing:
        return []
    changed = sorted(key for key in set(profile['settings']) | set(spacing)
                     if profile['settings'].get(key) != spacing.get(key))
    profile['settings'] = spacing
    (HERE/'motion_profiles.json').write_text(json.dumps(profiles, indent=2, ensure_ascii=False)+'\n',
                                             encoding='utf-8', newline='\n')
    return changed


def review(payload):
    """Probe each cut from scratch and compare its candidate witnesses with the reviewed ones."""
    from display.probe_motion import run
    results = {}
    for slug in requested(payload):
        synced = sync_profile(slug)
        if synced:
            print(f'{slug}: motion profile now follows the built settings ({", ".join(synced)})', flush=True)
        out = REVIEWS/slug
        shutil.rmtree(out, ignore_errors=True)
        print(f'Reviewing {slug}: every glyph in {len(STATES)} poses plus dense ordinal checks…', flush=True)
        report = run(out, None, slugs=(slug,))
        cut = report['cuts'][slug]
        states, glyphs, settings = {}, set(), set()
        for state in STATES:
            name = f'{slug}-{state["id"]}.json'
            candidate = json.loads((out/name).read_text(encoding='utf-8'))
            old = json.loads((REVIEWED/name).read_text(encoding='utf-8')) if (REVIEWED/name).is_file() else None
            if old is None:
                states[state['id']] = dict(new=True)
                continue
            moved = sorted(key for key in set(candidate['glyphs']) | set(old['glyphs'])
                           if candidate['glyphs'].get(key) != old['glyphs'].get(key))
            keys = sorted(key for key in set(candidate['settings']) | set(old['settings'])
                          if candidate['settings'].get(key) != old['settings'].get(key))
            if moved or keys:
                states[state['id']] = dict(glyphs=moved, settings=keys)
                glyphs.update(moved); settings.update(keys)
        summary = dict(cut=slug, source_sha256=motion_digest(slug), flags=cut['flags'], profile_synced=synced,
                       states=states, glyphs=sorted(glyphs), settings=sorted(settings))
        (out/'review.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(f'{slug}: {len(cut["flags"])} problems; {len(glyphs)} glyphs change in {len(states)} of {len(STATES)} poses', flush=True)
        results[slug] = dict(problems=len(cut['flags']), problem_examples=cut['flags'][:5], glyphs=sorted(glyphs),
                             settings=sorted(settings), states=len(states))
    return dict(cuts=results)


def approve(payload):
    """Adopt clean, current reviews as the reviewed witnesses and certify only those cuts."""
    from display.verify_motion import fixture_flags
    slugs = payload.get('cuts')
    if not isinstance(slugs, list) or not slugs:
        raise ValueError('Name the reviewed cuts to approve')
    requested(dict(cuts=slugs))
    for slug in slugs:
        file = REVIEWS/slug/'review.json'
        if not file.is_file():
            raise ValueError(f'Review {slug} first')
        summary = json.loads(file.read_text(encoding='utf-8'))
        if summary['source_sha256'] != motion_digest(slug):
            raise ValueError(f'{slug} or the engine changed after its review; review it again')
        if summary['flags']:
            raise ValueError(f'The {slug} review found problems; they must be fixed before approval')
    record = certificate()
    for slug in slugs:
        for state in STATES:
            name = f'{slug}-{state["id"]}.json'
            shutil.copyfile(REVIEWS/slug/name, REVIEWED/name)
        found = fixture_flags([slug])
        if found:
            raise ValueError(f'{slug} witnesses are inconsistent after copying: {found}')
        # The review ran the same probe the gate runs; with these witnesses in place the
        # gate's comparison is identical, so its clean result certifies the cut.
        record['cuts'][slug] = dict(profile=profile_for(slug)['id'], source_sha256=motion_digest(slug),
                                    fixture_sha256=fixture_digest(slug), flags=[])
        print(f'Approved {slug} motion', flush=True)
    record['cuts'] = {slug: record['cuts'][slug] for slug in sorted(record['cuts'])}
    CERTIFICATE.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    print('Rebuilding the Lab page…', flush=True)
    subprocess.run([sys.executable, '-X', 'utf8', str(HERE/'build_display_page.py')], check=True, cwd=ROOT)
    return dict(approved=slugs)


JOBS = dict(review=review, approve=approve)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('job', choices=sorted(JOBS))
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--result', type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding='utf-8'))
    try:
        result = dict(ok=True, **JOBS[args.job](payload))
    except Exception as error:  # reported to the Lab; the traceback stays in the job log
        import traceback
        traceback.print_exc()
        result = dict(ok=False, error=str(error))
    args.result.write_text(json.dumps(result, ensure_ascii=False)+'\n', encoding='utf-8')
    raise SystemExit(0 if result['ok'] else 1)


if __name__ == '__main__':
    main()
