"""Independent regressions for immutable output and inherited feature gates."""
import json
import copy
from pathlib import Path
import shutil
import tempfile
import unittest

from fontTools.ttLib import TTFont

from verify_shared_engine import FIXTURE, ROOT, audit_features, reader_flags
from verify_display_shapes import (DESIGN, SHARED_DESIGN, design_flags,
                                   validate_design_reference)


class ReaderIdentityTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(FIXTURE.read_text(encoding='utf-8'))
        self.filename = 'SEIReader-Regular.otf'
        self.fixture['files'] = {self.filename: self.fixture['files'][self.filename]}
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)/self.filename
        shutil.copyfile(ROOT/'fonts'/self.filename, self.path)

    def failures(self):
        return reader_flags(self.path.parent, self.fixture)[0]

    def save(self, font):
        font.save(self.path)
        font.close()

    def test_complete_current_reader_matches_frozen_reference(self):
        self.assertEqual(self.failures(), [])

    def test_build_timestamps_are_the_only_ignored_fields(self):
        font = TTFont(self.path, recalcTimestamp=False)
        font['head'].created += 60
        font['head'].modified += 60
        self.save(font)
        self.assertEqual(self.failures(), [])

    def test_advance_change_fails(self):
        font = TTFont(self.path)
        advance, bearing = font['hmtx']['R']
        font['hmtx']['R'] = advance+1, bearing
        self.save(font)
        failures = self.failures()
        self.assertTrue(any('hmtx' in flag.get('tables', []) for flag in failures))

    def test_outline_or_hint_change_fails(self):
        font = TTFont(self.path)
        char = font['CFF '].cff.topDictIndex[0].CharStrings['R']
        char.decompile()
        first_number = next(i for i, value in enumerate(char.program) if isinstance(value, (int, float)))
        char.program[first_number] += 1
        self.save(font)
        failures = self.failures()
        self.assertTrue(any(flag['kind']=='reader-outline-or-hint-identity' for flag in failures))
        self.assertTrue(any('CFF ' in flag.get('tables', []) for flag in failures))

    def test_name_and_layout_are_also_protected(self):
        font = TTFont(self.path)
        font['name'].setName('Changed family', 1, 3, 1, 0x409)
        self.save(font)
        self.assertTrue(any('name' in flag.get('tables', []) for flag in self.failures()))


class DisplayInheritanceTests(unittest.TestCase):
    def test_full_shared_reader_features_work_before_reuse(self):
        with TTFont(ROOT/'fonts/SEIReader-Regular.otf') as font:
            failures, report = audit_features(font)
        self.assertEqual(failures, [])
        self.assertEqual(report['pinned_cldr_locales'], 10)
        self.assertEqual(report['languages'], 23)
        self.assertGreater(report['language_strings'], 1800)

    def test_missing_mark_feature_fails_the_behavior_gate(self):
        with TTFont(ROOT/'fonts/SEIReader-Regular.otf') as font:
            features = font['GPOS'].table.FeatureList
            features.FeatureRecord = [record for record in features.FeatureRecord if record.FeatureTag!='mark']
            features.FeatureCount = len(features.FeatureRecord)
            failures, _ = audit_features(font)
        self.assertTrue(any(flag['kind']=='display-features' and 'mark' in flag['missing'] for flag in failures))


class DisplayDesignTests(unittest.TestCase):
    def setUp(self):
        self.original = json.loads(DESIGN.read_text(encoding='utf-8'))
        self.shared = json.loads(SHARED_DESIGN.read_text(encoding='utf-8'))
        self.reader = json.loads(FIXTURE.read_text(encoding='utf-8'))
        self.font = TTFont(ROOT/'display/fonts/soft/SEIHouseDisplay-Soft.otf')
        self.addCleanup(self.font.close)

    def failures(self):
        return design_flags(self.font, 'soft', self.original, self.shared)

    def test_reviewed_inheritance_preserves_all_controls_and_final_metrics(self):
        validate_design_reference(self.original, self.shared, self.reader)
        self.assertEqual(self.failures(), [])
        self.assertEqual(len(self.shared['fonts']['soft']['previous_advance_changes']), 20)

    def test_approved_changed_old_glyph_is_still_gated_exactly(self):
        advance, bearing = self.font['hmtx']['a']
        self.font['hmtx']['a'] = advance+1, bearing
        self.assertTrue(any(flag['kind']=='advance-width' and flag['glyph']=='a' for flag in self.failures()))

    def test_new_combining_mark_advance_is_gated(self):
        name = self.font.getBestCmap()[0x301]
        advance, bearing = self.font['hmtx'][name]
        self.font['hmtx'][name] = advance+1, bearing
        self.assertTrue(any(flag['kind']=='advance-width' and flag['glyph']==name for flag in self.failures()))

    def test_original_vertical_metrics_are_gated(self):
        self.font['OS/2'].usWinAscent += 1
        self.assertTrue(any(flag['kind']=='line-metric' for flag in self.failures()))

    def test_unlisted_old_metric_change_cannot_be_blessed_by_fixture(self):
        changed = copy.deepcopy(self.shared)
        changed['fonts']['soft']['advances']['R'] += 1
        with self.assertRaisesRegex(ValueError, 'listed explicitly'):
            validate_design_reference(self.original, changed, self.reader)


if __name__ == '__main__':
    unittest.main()
