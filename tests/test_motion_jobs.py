"""Lab motion review/approval: show every change, certify one cut, refuse unsafe approvals."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from display import living_build, motion_jobs
from display.living_build import STATES


class MotionJobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = self.root = Path(self.temp.name)
        (root/'display/cuts').mkdir(parents=True)
        self.reviewed = root/'tests/fixtures/display-motion-topology'
        self.reviewed.mkdir(parents=True)
        self.reviews = root/'dist/motion-review'
        self.certificate = root/'display/motion-certification.json'
        old = dict(weight=135, uFoot=False)
        self.new = dict(weight=135, uFoot=True)
        profiles = dict(schema=1, version='living-v1', profiles=[
            dict(id='soft-living-v1', cut='Soft', settings=dict(weight=150), thickness=.03, slant=1, penAngle=2),
            dict(id='ink-living-v1', cut='Ink', settings=old, thickness=.01, slant=1, penAngle=.25)])
        (root/'display/motion_profiles.json').write_text(json.dumps(profiles), encoding='utf-8')
        (root/'display/spacing_ink.json').write_text(json.dumps(dict(settings=self.new)), encoding='utf-8')
        (root/'display/spacing_soft.json').write_text(json.dumps(dict(settings=dict(weight=150))), encoding='utf-8')
        for slug, settings in (('ink', old), ('soft', dict(weight=150))):
            for state in STATES:
                glyphs = dict(u=dict(closed_counters=0, white_spaces=[[1, 2, False]]), o=dict(closed_counters=1, white_spaces=[]))
                (self.reviewed/f'{slug}-{state["id"]}.json').write_text(
                    json.dumps(dict(profile=f'{slug}-living-v1', state=state, settings=settings, size_px=400, glyphs=glyphs)),
                    encoding='utf-8')
        self.digest = 'sources-v1'
        self.flags = []
        self.patches = [patch.object(living_build, name, value) for name, value in (
            ('ROOT', root), ('REVIEWED', self.reviewed), ('CERTIFICATE', self.certificate))]
        self.patches += [patch.object(motion_jobs, name, value) for name, value in (
            ('HERE', root/'display'), ('REVIEWS', self.reviews), ('REVIEWED', self.reviewed),
            ('CERTIFICATE', self.certificate))]
        digest = lambda slug: f'{self.digest}-{slug}'
        self.patches += [patch.object(living_build, 'motion_digest', side_effect=digest),
                         patch.object(motion_jobs, 'motion_digest', side_effect=digest),
                         patch('display.probe_motion.run', side_effect=self.fake_probe),
                         patch.object(motion_jobs.subprocess, 'run'),
                         patch('display.verify_motion.fixture_flags', return_value=[])]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def fake_probe(self, out, reviewed, *, slugs):
        """Candidates as the real probe writes them: the u gains a foot in every pose."""
        out = Path(out); out.mkdir(parents=True, exist_ok=True)
        for state in STATES:
            glyphs = dict(u=dict(closed_counters=0, white_spaces=[[3, 2, False]]), o=dict(closed_counters=1, white_spaces=[]))
            (out/f'{slugs[0]}-{state["id"]}.json').write_text(json.dumps(dict(
                profile='ink-living-v1', state=state, settings=self.new, size_px=400, glyphs=glyphs)), encoding='utf-8')
        return dict(cuts={slugs[0]: dict(flags=self.flags)})

    def test_review_lists_the_changed_glyphs_and_approval_certifies_only_that_cut(self):
        result = motion_jobs.review(dict(cuts=['ink']))['cuts']['ink']
        self.assertEqual((result['problems'], result['glyphs'], result['settings'], result['states']),
                         (0, ['u'], ['uFoot'], len(STATES)))
        profiles = json.loads((self.root/'display/motion_profiles.json').read_text(encoding='utf-8'))
        self.assertEqual(profiles['profiles'][1]['settings'], self.new)
        self.assertEqual(motion_jobs.approve(dict(cuts=['ink'])), dict(approved=['ink']))
        self.assertEqual(json.loads((self.reviewed/'ink-rest.json').read_text(encoding='utf-8'))['settings'], self.new)
        record = json.loads(self.certificate.read_text(encoding='utf-8'))
        self.assertEqual(list(record['cuts']), ['ink'])
        self.assertTrue(living_build.certified('ink', living_build.profile_for('ink')))
        self.assertFalse(living_build.certified('soft', living_build.profile_for('soft')))

    def test_a_review_with_problems_cannot_be_approved(self):
        self.flags = [dict(glyph='u', kind='filled-counter')]
        self.assertEqual(motion_jobs.review(dict(cuts=['ink']))['cuts']['ink']['problems'], 1)
        with self.assertRaisesRegex(ValueError, 'found problems'):
            motion_jobs.approve(dict(cuts=['ink']))
        self.assertFalse(self.certificate.exists())

    def test_changes_after_the_review_need_a_new_review(self):
        motion_jobs.review(dict(cuts=['ink']))
        self.digest = 'sources-v2'
        with self.assertRaisesRegex(ValueError, 'review it again'):
            motion_jobs.approve(dict(cuts=['ink']))
        self.assertEqual(json.loads((self.reviewed/'ink-rest.json').read_text(encoding='utf-8'))['settings']['uFoot'], False)

    def test_unknown_cuts_are_refused(self):
        with self.assertRaisesRegex(ValueError, 'shipped cuts'):
            motion_jobs.review(dict(cuts=['../soft']))


if __name__ == '__main__':
    unittest.main()
