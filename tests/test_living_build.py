"""Exports must fail closed when motion sources, witnesses or certification drift."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from display.living_build import engine_factory,profiles_for_lab


class LivingBuildTests(unittest.TestCase):
    def test_private_factory_embeds_the_shared_source_and_isolates_drawing_state(self):
        factory=engine_factory()
        source=(Path(__file__).resolve().parents[1]/'engine.js').read_text(encoding='utf-8')
        self.assertIn(source,factory)
        self.assertIn('const window={}',factory)
        self.assertIn('const livingDefs=[]',factory)
        self.assertIn('return {layout:livingLayout, frame:livingFrame}',factory)

    def certify(self, root, record, sources, witnesses=None):
        """Read the Lab profiles for a certificate with patched per-cut digests."""
        certificate=root/'display/motion-certification.json'
        if record is None:
            certificate.unlink(missing_ok=True)
        else:
            certificate.write_text(json.dumps(record),encoding='utf-8')
        witnesses=witnesses or {}
        with patch('display.living_build.ROOT',root),patch('display.living_build.CERTIFICATE',certificate),\
                patch('display.living_build.motion_digest',side_effect=lambda slug:sources[slug]),\
                patch('display.living_build.fixture_digest',side_effect=lambda slug:witnesses.get(slug,'fixture-'+slug)):
            return {p['id']:p['certified'] for p in profiles_for_lab()['profiles']}

    def test_stale_or_failed_certificate_cannot_enable_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'display').mkdir()
            profiles={'schema':1,'profiles':[{'id':'soft-living-v1','cut':'Soft'}]}
            (root/'display/motion_profiles.json').write_text(json.dumps(profiles),encoding='utf-8')
            sources={'soft':'source'}
            good={'profile':'soft-living-v1','source_sha256':'source','fixture_sha256':'fixture-soft','flags':[]}
            self.assertEqual(self.certify(root,None,sources),{'soft-living-v1':False})
            # The single-file schema 1 certificate no longer certifies anything.
            legacy={'source_sha256':'source','fixture_sha256':'fixture','profiles':['soft-living-v1'],'flags':[]}
            self.assertEqual(self.certify(root,legacy,sources),{'soft-living-v1':False})
            for entry in (good|{'source_sha256':'changed'},good|{'fixture_sha256':'changed'},
                          good|{'flags':[{'kind':'filled-counter'}]},good|{'profile':'soft-living-v2'}):
                self.assertEqual(self.certify(root,{'schema':2,'cuts':{'soft':entry}},sources),{'soft-living-v1':False})
            self.assertEqual(self.certify(root,{'schema':2,'cuts':{'soft':good}},sources,{'soft':None}),{'soft-living-v1':False})
            self.assertEqual(self.certify(root,{'schema':2,'cuts':{'soft':good}},sources),{'soft-living-v1':True})

    def test_changing_one_cut_keeps_the_other_cuts_certified(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'display').mkdir()
            profiles={'schema':1,'profiles':[{'id':'soft-living-v1','cut':'Soft'},{'id':'ink-living-v1','cut':'Ink'}]}
            (root/'display/motion_profiles.json').write_text(json.dumps(profiles),encoding='utf-8')
            record={'schema':2,'cuts':{slug:{'profile':f'{slug}-living-v1','source_sha256':f'source-{slug}',
                                              'fixture_sha256':f'fixture-{slug}','flags':[]} for slug in ('soft','ink')}}
            self.assertEqual(self.certify(root,record,{'soft':'source-soft','ink':'source-ink'}),
                             {'soft-living-v1':True,'ink-living-v1':True})
            self.assertEqual(self.certify(root,record,{'soft':'source-soft','ink':'ink-was-rebuilt'}),
                             {'soft-living-v1':True,'ink-living-v1':False})


if __name__=='__main__':unittest.main()
