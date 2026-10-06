"""Independent regressions for Display web delivery and Reader-identical legal metadata."""
from pathlib import Path
import re
import tempfile
import unittest

from fontTools.ttLib import TTFont

from display.build_subsets import display_groups, write_css
from verify_display_subsets import css_flags, license_flags, subset_flags

ROOT = Path(__file__).resolve().parents[1]
SOFT = ROOT/'display/fonts/soft/SEIHouseDisplay-Soft.otf'
READER = ROOT/'fonts/SEIReader-Regular.otf'


class DisplaySubsetTests(unittest.TestCase):
    def test_every_cut_has_exact_reader_legal_records(self):
        with TTFont(READER) as reader:
            for cut in ('soft', 'edge', 'ink', 'wide'):
                source = ROOT/f'display/fonts/{cut}/SEIHouseDisplay-{cut.title()}.otf'
                with self.subTest(cut=cut), TTFont(source) as font:
                    self.assertEqual(license_flags(font, reader), [])

    def test_missing_license_and_restricted_embedding_are_rejected(self):
        with TTFont(READER) as reader, TTFont(SOFT) as font:
            font['name'].names = [record for record in font['name'].names if record.nameID != 13]
            font['OS/2'].fsType = 2
            failures = license_flags(font, reader)
            self.assertIn(dict(kind='display-legal-name', name_id=13), failures)
            self.assertIn(dict(kind='display-legal-os2', field='fsType'), failures)

    def test_six_groups_cover_scripts_marks_fractions_and_symbols(self):
        with TTFont(SOFT) as font:
            codes = set(font.getBestCmap())
        groups = display_groups(codes)
        self.assertEqual(set(groups), {'latin-basic', 'latin-extended', 'cyrillic', 'greek', 'vietnamese', 'symbols'})
        self.assertEqual(set().union(*groups.values()), codes)
        self.assertTrue({ord(ch) for ch in 'Ww469⁄'} <= groups['latin-basic'])
        for name, text in (('latin-extended', 'Ŵŵx\u0302\u0301'), ('cyrillic', 'КМ Ќ'),
                           ('greek', 'ΚΜ Ά'), ('vietnamese', 'Tưởng tượng'), ('symbols', '¼¾Ⓢ🎧')):
            self.assertTrue(set(map(ord, text)) <= groups[name], (name, text))

    def test_missing_stylistic_set_fails_native_subset_parity(self):
        with TTFont(SOFT) as full, TTFont(SOFT.with_suffix('.latin-basic.woff2')) as subset:
            codes = display_groups(set(full.getBestCmap()))['latin-basic']
            self.assertEqual(subset_flags(full, subset, codes)[0], [])
        with TTFont(SOFT) as full, TTFont(SOFT.with_suffix('.latin-basic.woff2')) as subset:
            for record in subset['GSUB'].table.FeatureList.FeatureRecord:
                if record.FeatureTag == 'ss04': record.FeatureTag = 'ss09'
            failures, _ = subset_flags(full, subset, codes)
            self.assertTrue(any(flag['kind'] == 'display-subset-feature-shaping' for flag in failures))

    def test_css_ranges_must_match_subset_cmap(self):
        with tempfile.TemporaryDirectory() as directory:
            css = Path(directory)/'fonts.css'
            write_css([SOFT], css)
            self.assertEqual(css_flags(css, [SOFT]), [])
            text = re.sub(r'unicode-range:[^;]+;', 'unicode-range: U+FFFF;',
                          css.read_text(encoding='utf-8'), count=1)
            css.write_text(text, encoding='utf-8')
            self.assertTrue(css_flags(css, [SOFT]))


if __name__ == '__main__':
    unittest.main()
