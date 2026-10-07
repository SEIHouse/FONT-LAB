"""Certify every motion profile against separately reviewed topology; never refresh witnesses."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
from display.living_build import motion_digest,fixture_digest
from display.probe_motion import STATES

CUTS=('soft','edge','ink','wide')
REVIEWED=ROOT/'tests/fixtures/display-motion-topology'


def fixture_flags():
    """Require the exact reviewed live-SVG state inventory and bounded profile settings."""
    found=[]
    profiles=json.loads((HERE/'motion_profiles.json').read_text(encoding='utf-8'))
    if profiles.get('schema')!=1 or len(profiles.get('profiles',[]))!=4:
        return [{'kind':'motion-profile-inventory'}]
    expected_files={f'{slug}-{state["id"]}.json' for slug in CUTS for state in STATES}
    if not REVIEWED.is_dir() or {file.name for file in REVIEWED.glob('*.json')}!=expected_files:
        return [{'kind':'reviewed-motion-inventory'}]
    for slug in CUTS:
        cut=json.loads((HERE/f'cuts/{slug}.json').read_text(encoding='utf-8'))
        profile=next((row for row in profiles['profiles'] if row['cut']==cut['name']),None)
        if not profile or not (0<profile['thickness']<=.03 and 0<profile['slant']<=1 and 0<profile['penAngle']<=2):
            found.append({'kind':'motion-limit','cut':slug});continue
        spacing=json.loads((HERE/f'spacing_{slug}.json').read_text(encoding='utf-8'))
        if profile['settings']!=spacing['settings']:found.append({'kind':'motion-profile-settings','cut':slug})
    return found


def verify(out, *, write_certificate=False, workers=4):
    """Recompute all constructions/rasters independently per cut, then bind the certificate."""
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    found=fixture_flags()
    report={'source_sha256':motion_digest(),'fixture_sha256':fixture_digest(),'profiles':[], 'cuts':{},'flags':found}
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
            if record.get('source_sha256')!=report['source_sha256']:record['flags'].append({'kind':'motion-source-changed'})
            return slug,record
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for slug,record in pool.map(cut_gate,CUTS):
                report['cuts'][slug]=record.get('cuts',{}).get(slug,{})
                report['profiles']+=record.get('profiles',[])
                report['flags']+=record['flags']
                print(f'Motion {slug}: {len(record["flags"])} flags',flush=True)
    certificate=HERE/'motion-certification.json'
    fields=('source_sha256','fixture_sha256','profiles','flags')
    current={key:report[key] for key in fields}
    if not report['flags'] and len(report['profiles'])==4:
        if write_certificate:
            certificate.write_text(json.dumps({'schema':1,**current},indent=2)+'\n',encoding='utf-8')
        elif not certificate.exists() or {key:json.loads(certificate.read_text(encoding='utf-8')).get(key) for key in fields}!=current:
            report['flags'].append({'kind':'stale-motion-certificate'})
    else:
        report['flags'].append({'kind':'uncertified-motion-profiles'})
    (out/'motion.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'Motion: {len(report["profiles"])}/4 profiles, {len(report["flags"])} flags',flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'dist/motion-gates')
    parser.add_argument('--write-certificate',action='store_true',help='Certify passing sources after fixtures have been reviewed; never changes fixtures')
    parser.add_argument('--workers',type=int,choices=range(1,5),default=4)
    args=parser.parse_args();raise SystemExit(bool(verify(args.output_dir,write_certificate=args.write_certificate,workers=args.workers)['flags']))
