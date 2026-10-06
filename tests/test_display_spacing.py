"""Independent title-spacing gates: feature behavior, class export and preservation."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from fontTools.ttLib import TTFont

from display.title_spacing import DisplaySpacing, compiled_kerning, policy_for
from font_builder import FontBuilderCore
from verify_display_spacing import feature_flags, width_flags
from verify_latin import shape

ROOT = Path(__file__).resolve().parents[1]


def exported_pair(lookups, first, second):
    """Resolve the exported lookup plan for comparison with independent native shaping."""
    value = 0
    for lookup in lookups:
        for table in lookup:
            if table['format'] == 1:
                pair = table['pairs'].get(first, {}).get(second)
                if pair is None:
                    continue
                value += pair
                break
            if first in table['coverage']:
                value += table['values'][table['left'].get(first, 0)][table['right'].get(second, 0)]
                break
    return value


class DisplayTitleSpacingTests(unittest.TestCase):
    def test_width_gate_rejects_half_percent_and_larger_errors(self):
        """Enforce the strict title-width limit in both widening and tightening cases."""
        self.assertEqual(width_flags(100.49,100)[0],[])
        self.assertTrue(width_flags(100.5,100)[0])
        self.assertTrue(width_flags(99,100)[0])

    def test_cut_policy_comes_from_geometry_and_survives_renaming(self):
        """Keep a renamed project cut on the optical policy selected by its geometry."""
        for cut in ('soft','edge','ink','wide'):
            settings=json.loads((ROOT/'display/cuts'/f'{cut}.json').read_text())
            settings['name']='Another project'
            self.assertEqual(policy_for(settings),cut)

    def test_compiled_pair_export_matches_independent_native_shaping(self):
        """Check requested pairs, accents and scripts against HarfBuzz's GPOS execution."""
        for cut in ('soft','edge','ink','wide'):
            with self.subTest(cut=cut), TTFont(ROOT/'display/fonts'/cut/f'SEIHouseDisplay-{cut.title()}.otf') as font:
                data=compiled_kerning(font)
                for pair in ('LA','LY','LT','TA','AV','AW','AY','PA','FA','VA','RT','ÁV','ÁÝ','ГД','ΑΥ','0.'):
                    glyphs=shape(font,pair,cpsp=False)
                    plain=shape(font,pair,kern=False,cpsp=False)
                    expected=(sum(row[1] for row in glyphs)-sum(row[1] for row in plain))/2
                    self.assertEqual(exported_pair(data,plain[0][0],plain[1][0]),expected,pair)

    def test_title_pass_uses_cap_height_and_keeps_real_ink_clearance(self):
        """Reject body-only title spacing, reference-rhythm drift and colliding cap pairs."""
        for cut in ('soft','edge','ink','wide'):
            settings=json.loads((ROOT/'display/cuts'/f'{cut}.json').read_text())
            builder=FontBuilderCore(settings,display=True)
            with self.subTest(cut=cut), TTFont(ROOT/'display/fonts'/cut/f'SEIHouseDisplay-{cut.title()}.otf') as font:
                policy=DisplaySpacing(builder,dict(font.getGlyphSet()),
                    {name:metric[0] for name,metric in font['hmtx'].metrics.items()},
                    font.getBestCmap(),'HnLYTAWVPRF')
                self.assertLess(policy.adjustment('L','T','cap'),policy.adjustment('L','T','body')-80)
                for pair in ('HH','nn'):
                    shaped=shape(font,pair,cpsp=False)
                    plain=shape(font,pair,kern=False,cpsp=False)
                    self.assertEqual(sum(row[1] for row in shaped),sum(row[1] for row in plain))
                for pair in ('LA','LY','LT','TA','AV','AW','AY','PA','FA','VA','RT'):
                    shaped=shape(font,pair,cpsp=False)
                    plain=shape(font,pair,kern=False,cpsp=False)
                    adjustment=sum(row[1] for row in shaped)-sum(row[1] for row in plain)
                    self.assertAlmostEqual(adjustment/2,policy.adjustment(*pair,'cap'),delta=1)
                    # Two independently rounded CFF edges can move by two font units.
                    self.assertGreaterEqual(policy.gap(*pair,'cap')[1]+adjustment,policy.clearance-2)

    def test_candidate_lab_loads_matching_exports_and_rejects_stale_fonts(self):
        """Exercise candidate asset paths, project names and the stale-font build failure."""
        with tempfile.TemporaryDirectory() as directory:
            candidate=Path(directory)
            for cut in ('soft','edge','ink','wide'):
                destination=candidate/cut
                destination.mkdir()
                shutil.copy(ROOT/'display'/f'spacing_{cut}.json',destination)
                shutil.copy(ROOT/'display/fonts'/cut/f'SEIHouseDisplay-{cut.title()}.otf',destination)
            env=dict(os.environ,SPACING_DIR=str(candidate),LAB_OUT=str(candidate/'lab.html'))
            command=[sys.executable,'-X','utf8',str(ROOT/'display/build_display_page.py')]
            result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('const SPACING_EXPORTS =',(candidate/'lab.html').read_text(encoding='utf-8'))
            # Follow make_display.py's public filename convention for a named project cut.
            named=candidate/'my-cut'
            named.mkdir()
            shutil.copy(candidate/'soft/spacing_soft.json',named/'spacing_my-cut.json')
            shutil.copy(candidate/'soft/SEIHouseDisplay-Soft.otf',named/'SEIHouseDisplay-MyCut.otf')
            settings=json.loads((ROOT/'display/cuts/soft.json').read_text())
            settings['name']='My Cut'
            probe=[sys.executable,'-X','utf8','-c',
                "import json, runpy, sys; page=runpy.run_path(sys.argv[1]); "
                "assert page['load_spacing'](json.loads(sys.argv[2]))['policy']=='soft'",
                str(ROOT/'display/build_display_page.py'),json.dumps(settings)]
            result=subprocess.run(probe,cwd=ROOT,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            stale=candidate/'soft/spacing_soft.json'
            data=json.loads(stale.read_text(encoding='utf-8'))
            data['built_alternates']['a']='double'
            stale.write_text(json.dumps(data),encoding='utf-8')
            result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Stale spacing export for Soft',result.stderr)
            data['built_alternates']['a']='single'
            data['otf_sha256']='stale'
            stale.write_text(json.dumps(data),encoding='utf-8')
            result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Stale spacing export for Soft',result.stderr)

    def test_cpsp_is_additive_and_only_changes_capitals(self):
        """Verify native capital feature behavior and fail when the feature is absent."""
        for cut in ('soft','edge','ink','wide'):
            spacing=json.loads((ROOT/'display'/f'spacing_{cut}.json').read_text(encoding='utf-8'))
            with self.subTest(cut=cut), TTFont(ROOT/'display/fonts'/cut/f'SEIHouseDisplay-{cut.title()}.otf') as font:
                self.assertEqual(feature_flags(font,spacing),[])
                features=font['GPOS'].table.FeatureList
                features.FeatureRecord=[row for row in features.FeatureRecord if row.FeatureTag!='cpsp']
                self.assertEqual(feature_flags(font,spacing),[dict(kind='missing-cpsp')])


if __name__=='__main__':
    unittest.main()
