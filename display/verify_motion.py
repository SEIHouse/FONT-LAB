"""Certify motion profiles against separately reviewed topology; never refresh witnesses.

Each cut is certified on its own. `--cut ink` checks (and with --write-certificate,
re-certifies) only Ink; the other cuts keep their entries while still current.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
from display.living_build import (CERTIFICATE, REVIEWED, certificate, fixture_digest, motion_digest,
                                  motion_profiles, profile_for, slug_of)


def all_cuts():
    """Every cut that has a motion profile, in profile order."""
    return [slug_of(row['cut']) for row in motion_profiles()['profiles']]


def fixture_flags(slugs):
    """Require each cut's exact reviewed live-SVG state inventory and bounded profile settings."""
    profiles=motion_profiles()
    if profiles.get('schema')!=1 or not profiles.get('profiles'):
        return [{'kind':'motion-profile-inventory'}]
    found=[]
    for slug in slugs:
        profile=profile_for(slug,profiles)
        if not profile or not (0<profile['thickness']<=.03 and 0<profile['slant']<=1 and 0<profile['penAngle']<=2):
            found.append({'kind':'motion-limit','cut':slug});continue
        if not REVIEWED.is_dir() or fixture_digest(slug) is None:
            found.append({'kind':'reviewed-motion-inventory','cut':slug});continue
        spacing=json.loads((HERE/f'spacing_{slug}.json').read_text(encoding='utf-8'))
        if profile['settings']!=spacing['settings']:found.append({'kind':'motion-profile-settings','cut':slug})
    return found


def verify(out, *, write_certificate=False, workers=4, slugs=None):
    """Recompute constructions/rasters independently per cut, then bind each cut's certificate."""
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    slugs=list(slugs or all_cuts())
    found=fixture_flags(slugs)
    report={'cuts':{},'profiles':[],'flags':found}
    records={}
    if not found:
        def cut_gate(slug):
            """Run a cut in its own process/browser/cache and return its exact report."""
            directory=out/slug
            with (out/f'{slug}.log').open('w',encoding='utf-8') as log:
                result=subprocess.run([sys.executable,'-X','utf8',str(HERE/'probe_motion.py'),
                    '--cut',slug,'--reviewed',str(REVIEWED),'--output-dir',str(directory)],stdout=log,stderr=subprocess.STDOUT,check=False)
            file=directory/'report.json'
            record=json.loads(file.read_text(encoding='utf-8')) if file.exists() else {'flags':[{'kind':'missing-motion-report'}]}
            if result.returncode and not record['flags']:record['flags'].append({'kind':'motion-process','exit_code':result.returncode})
            if record.get('cuts',{}).get(slug,{}).get('source_sha256')!=motion_digest(slug):
                record['flags'].append({'kind':'motion-source-changed'})
            return slug,record
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for slug,record in pool.map(cut_gate,slugs):
                records[slug]=record
                report['cuts'][slug]=record.get('cuts',{}).get(slug,{})
                report['profiles']+=record.get('profiles',[])
                report['flags']+=record['flags']
                print(f'Motion {slug}: {len(record["flags"])} flags',flush=True)
    current=certificate()
    for slug in slugs:
        profile=profile_for(slug)
        flags=records.get(slug,{}).get('flags',[{'kind':'not-run'}]) if not found else found
        entry={'profile':profile['id'] if profile else None,'source_sha256':motion_digest(slug),
               'fixture_sha256':fixture_digest(slug),'flags':flags}
        if flags or not profile or profile['id'] not in report['profiles']:
            report['flags'].append({'kind':'uncertified-motion-profile','cut':slug})
        elif write_certificate:
            current['cuts'][slug]=entry
        elif current['cuts'].get(slug)!=entry:
            report['flags'].append({'kind':'stale-motion-certificate','cut':slug})
    if write_certificate:
        current['cuts']={slug:current['cuts'][slug] for slug in sorted(current['cuts'])}
        CERTIFICATE.write_text(json.dumps(current,indent=2)+'\n',encoding='utf-8')
    (out/'motion.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'Motion: {len(report["profiles"])}/{len(slugs)} profiles, {len(report["flags"])} flags',flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'dist/motion-gates')
    parser.add_argument('--write-certificate',action='store_true',help='Certify passing sources after fixtures have been reviewed; never changes fixtures')
    parser.add_argument('--workers',type=int,choices=range(1,5),default=4)
    parser.add_argument('--cut',action='append',dest='cuts',metavar='SLUG',help='Only this cut (repeatable)')
    args=parser.parse_args()
    raise SystemExit(bool(verify(args.output_dir,write_certificate=args.write_certificate,workers=args.workers,slugs=args.cuts)['flags']))
