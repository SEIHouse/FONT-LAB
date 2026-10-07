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

    def test_stale_or_failed_certificate_cannot_enable_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'display').mkdir()
            profiles={'schema':1,'profiles':[{'id':'soft-living-v1'}]}
            (root/'display/motion_profiles.json').write_text(json.dumps(profiles),encoding='utf-8')
            certificate=root/'display/motion-certification.json'
            good={'source_sha256':'source','fixture_sha256':'fixture','profiles':['soft-living-v1'],'flags':[]}
            with patch('display.living_build.ROOT',root),patch('display.living_build.motion_digest',return_value='source'),patch('display.living_build.fixture_digest',return_value='fixture'):
                self.assertFalse(profiles_for_lab()['profiles'][0].get('certified',False))
                for record in (good|{'source_sha256':'changed'},good|{'fixture_sha256':'changed'},good|{'flags':[{'kind':'filled-counter'}]}):
                    certificate.write_text(json.dumps(record),encoding='utf-8')
                    self.assertFalse(profiles_for_lab()['profiles'][0].get('certified',False))
                certificate.write_text(json.dumps(good),encoding='utf-8')
                self.assertTrue(profiles_for_lab()['profiles'][0]['certified'])


if __name__=='__main__':unittest.main()
