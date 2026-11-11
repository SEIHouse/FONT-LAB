"""Native feature and preservation regressions for all Display letter designs."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from fontTools.ttLib import TTFont

from display.letter_alternates import alternate_kerning
from verify_display_alternates import feature_flags, preservation_flags, outline_hash, PRESERVATION
from verify_latin import shape

ROOT=Path(__file__).resolve().parents[1]


class DisplayAlternateTests(unittest.TestCase):
    """Use independent native shaping and deliberately broken feature/outline tables."""

    def test_alternate_pairs_keep_cap_punctuation_and_descender_policy(self):
        """Alternate capitals use the cap band beside punctuation and leave j unkerned."""
        profiles = dict.fromkeys(('R', 'j', ')', '('))
        policy = SimpleNamespace(profiles=profiles, builder=SimpleNamespace(settings={}),
            add_profile=lambda name, *_: profiles.update({name: None}), adjustment=Mock(return_value=-3))
        designs = {'R': dict(default='straight', choices={'straight': 'R', 'curved': 'altR'})}
        lines, _ = alternate_kerning(policy, designs, {}, {'altR': None}, {'altR': 1000},
            lambda name: name, 2, set(), set())
        policy.adjustment.assert_any_call('altR', ')', 'cap')
        policy.adjustment.assert_any_call('(', 'altR', 'cap')
        self.assertFalse(any('j' in call.args[:2] for call in policy.adjustment.call_args_list))
        self.assertFalse(any('@R_j' in line or '@L_j' in line for line in lines))
        policy.builder.settings['pairSpace'] = {'Rj': -12}
        lines, _ = alternate_kerning(policy, designs, {}, {'altR': None}, {'altR': 1000},
            lambda name: name, 2, set(), set())
        self.assertIn(' pos @ALT_R @R_j -24;', lines)

    def test_all_sets_and_derivatives_shape_in_every_cut(self):
        """Cover real designs, small figures, capital spacing and canonical accents."""
        for cut in ('soft','edge','ink','wide'):
            spacing=json.loads((ROOT/'display'/f'spacing_{cut}.json').read_text(encoding='utf-8'))
            with self.subTest(cut=cut), TTFont(ROOT/'display/fonts'/cut/f'SEIHouseDisplay-{cut.title()}.otf') as font:
                self.assertEqual(feature_flags(font,spacing),[])

    def test_removed_set_is_rejected(self):
        """A compiled inventory with no ss07 must fail even when its glyphs remain."""
        spacing=json.loads((ROOT/'display/spacing_soft.json').read_text(encoding='utf-8'))
        with TTFont(ROOT/'display/fonts/soft/SEIHouseDisplay-Soft.otf') as font:
            for record in font['GSUB'].table.FeatureList.FeatureRecord:
                if record.FeatureTag=='ss07': record.FeatureTag='ss09'
            self.assertTrue(any(flag['kind']=='missing-stylistic-set' for flag in feature_flags(font,spacing)))

    def test_unrelated_outline_cannot_change(self):
        """Changing an untouched H is detected by the immutable Step 3 curve hashes."""
        spacing=json.loads((ROOT/'display/spacing_soft.json').read_text(encoding='utf-8'))
        baseline=json.loads(PRESERVATION.read_text(encoding='utf-8'))
        with TTFont(ROOT/'display/fonts/soft/SEIHouseDisplay-Soft.otf') as font:
            self.assertEqual(preservation_flags(font,'soft',spacing,baseline)[0],[])
            char=font['CFF '].cff.topDictIndex[0].CharStrings['H']
            char.decompile(); char.program=['endchar']
            failures, _=preservation_flags(font,'soft',spacing,baseline)
            self.assertTrue(any(flag['kind']=='unrelated-outline-change' and flag['glyph']=='H' for flag in failures))

    def test_new_bases_and_alternates_keep_mark_attachment_and_stacking(self):
        """Remaining marks attach to both variants, with zero advances and stacked anchors."""
        for cut in ('soft','edge','ink','wide'):
            with self.subTest(cut=cut), TTFont(ROOT/'display/fonts'/cut/f'SEIHouseDisplay-{cut.title()}.otf') as font:
                for enabled in (False,True):
                    text='g\u030b\u0301'
                    result=shape(font,text,ss01=enabled)
                    self.assertNotEqual(result,shape(font,text,ss01=enabled,mark=False))
                    self.assertNotEqual(result,shape(font,text,ss01=enabled,mkmk=False))
                    self.assertTrue(all(row[1]==0 for row in result[1:]))

    def test_refined_alternate_outline_is_required_in_edge_and_wide(self):
        """Reject a broken or absent ss01 curve outside the older glyph inventory."""
        baseline=json.loads(PRESERVATION.read_text(encoding='utf-8'))
        curves=json.loads((ROOT/'tests/fixtures/display-reading-curves.json').read_text(encoding='utf-8'))
        for cut in ('edge','wide'):
            spacing=json.loads((ROOT/'display'/f'spacing_{cut}.json').read_text(encoding='utf-8'))
            name=next(name for name in curves['cuts'][cut] if name not in baseline['cuts'][cut])
            for missing in (False,True):
                with self.subTest(cut=cut,missing=missing), TTFont(ROOT/'display/fonts'/cut/f'SEIHouseDisplay-{cut.title()}.otf') as font:
                    self.assertEqual(preservation_flags(font,cut,spacing,baseline)[0],[])
                    if missing:
                        font.setGlyphOrder([glyph for glyph in font.getGlyphOrder() if glyph!=name])
                    else:
                        char=font['CFF '].cff.topDictIndex[0].CharStrings[name]
                        char.decompile(); char.program=['endchar']
                    failures,_=preservation_flags(font,cut,spacing,baseline)
                    self.assertIn(dict(kind='unapproved-alternate-curve',glyph=name),failures)

    def test_refined_default_cannot_revert_to_historical_outline(self):
        """The old S hash is no longer a valid replacement for the approved S."""
        baseline=json.loads(PRESERVATION.read_text(encoding='utf-8'))
        spacing=json.loads((ROOT/'display/spacing_soft.json').read_text(encoding='utf-8'))
        with TTFont(ROOT/'display/fonts/soft/SEIHouseDisplay-Soft.otf') as font:
            with patch('verify_display_alternates.outline_hash',side_effect=lambda f,name:
                       baseline['cuts']['soft']['S'] if name=='S' else outline_hash(f,name)):
                failures,_=preservation_flags(font,'soft',spacing,baseline)
            self.assertIn(dict(kind='unapproved-reading-curve',glyph='S'),failures)


if __name__=='__main__':
    unittest.main()
