"""Production regressions for cut discovery, opt-in isolation and topology gates."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from display import make_display
from display.production import ROOT, font_path, load_cuts, read_manifest, style_plan
from display.title_spacing import write_spacing
from display.verify_production import reviewed_topology
from font_builder import FontBuilderCore


class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.soft = json.loads((ROOT/'display/cuts/soft.json').read_text(encoding='utf-8'))

    def test_regular_only_is_default_and_extra_plans_do_not_mutate_cut(self):
        original = deepcopy(self.soft)
        self.assertEqual([face['label'] for face in style_plan(self.soft)], ['Regular'])
        extras = style_plan(self.soft | {'production':dict(weights={'Light':.85,'Bold':1.03},oblique=9)})
        self.assertEqual([face['label'] for face in extras], ['Regular', 'Light', 'Bold', 'Oblique'])
        for face in extras:
            changed = {key for key in original if face['settings'][key] != original[key]}
            self.assertEqual(changed, {'weight'} if face['label'] in ('Light', 'Bold') else
                             {'slant'} if face['label']=='Oblique' else set())
        extras[-1]['settings']['alternates']['W'] = 'crossed'
        self.assertEqual(self.soft, original)

    def test_per_cut_weights_and_oblique_are_independent(self):
        ink = json.loads((ROOT/'display/cuts/ink.json').read_text(encoding='utf-8'))
        ink['production'] = dict(weights={'Light': .9}, oblique=7)
        faces = style_plan(ink)
        self.assertEqual([face['label'] for face in faces], ['Regular', 'Light', 'Oblique'])
        self.assertEqual(faces[-1]['settings']['slant'], 15)
        self.assertEqual(faces[1]['settings']['weight'], ink['weight']*.9)
        self.assertTrue(all('production' not in face['settings'] for face in faces))
        self.assertEqual(len(style_plan(self.soft)), 1)

    def test_bad_style_plans_are_rejected_before_building(self):
        for config in ({'weights':{'Regular':.9}}, {'weights':{'Light':1.1}}, {'weights':{'Bold':.9}},
                       {'weights':{'Light':float('nan')}}, {'oblique':True}, {'oblique':-9},
                       {'weights':[.9]}, {'unknown':1}, None):
            with self.subTest(config=config), self.assertRaises(ValueError):
                style_plan(self.soft | {'production':config})

    def test_discovers_unlisted_cuts_and_rejects_name_collisions(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder/'z-new.json').write_text(json.dumps(self.soft | {'name':'New Cut'}), encoding='utf-8')
            (folder/'a-soft.json').write_text(json.dumps(self.soft), encoding='utf-8')
            self.assertEqual([cut['slug'] for cut in load_cuts(folder)], ['soft', 'new-cut'])
            (folder/'collision.json').write_text(json.dumps(self.soft | {'name':'New-Cut'}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'duplicate cut slug'):
                load_cuts(folder)

    def test_paths_and_spacing_are_isolated_by_cut_and_style(self):
        cut = dict(slug='soft', name='Soft')
        self.assertEqual(font_path(Path('fonts'), cut, 'Regular'), Path('fonts/soft/SEIHouseDisplay-Soft.otf'))
        self.assertEqual(font_path(Path('fonts'), cut, 'Oblique'), Path('fonts/soft/Oblique/SEIHouseDisplay-Soft-Oblique.otf'))

    def test_distinct_folders_cannot_share_a_postscript_family(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for index, name in enumerate(('New Cut', 'NewCut')):
                (folder/f'{index}.json').write_text(json.dumps(self.soft | {'name':name}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'PostScript'):
                load_cuts(folder)

    def test_oblique_does_not_enable_italic_drawing_substitutions(self):
        captured = {}
        class Core:
            FAMILY, VERSION = 'fixture', '0'
            def __init__(self, settings, **kwargs):
                captured['core'] = FontBuilderCore(settings, **kwargs)
            def export(self):
                return {}
            def build(self, data, out, style, *, oblique=False):
                captured.update(oblique=oblique, style=style)
        with tempfile.TemporaryDirectory() as directory, patch.object(make_display, 'FontBuilderCore', Core):
            make_display.build_style(style_plan(self.soft | {'production':{'oblique':9}})[-1]['settings'], directory, oblique=True)
        self.assertFalse(captured['core'].ITAL)
        self.assertTrue(captured['core'].display)
        self.assertTrue(captured['oblique'])
        self.assertEqual(captured['style'], 'Regular')
        with self.assertRaises(ValueError):
            FontBuilderCore(self.soft | {'family':'SEIHouse Sans'}).build({}, 'unused.otf', oblique=True)

    def test_extra_style_requires_reviewed_topology_for_exact_settings(self):
        spacing=json.loads((ROOT/'display/spacing_wide.json').read_text(encoding='utf-8'))
        with self.assertRaisesRegex(ValueError, 'do not match'):
            reviewed_topology('wide', spacing, 'Light')
        with self.assertRaisesRegex(ValueError, 'add reviewed'):
            reviewed_topology('edge', spacing, 'Bold')

    def test_manifest_cannot_read_assets_outside_its_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory)/'display/production-manifest.json'
            manifest.parent.mkdir()
            manifest.write_text(json.dumps(dict(version=1, cuts=[dict(styles=[dict(assets=[dict(path='../../other.otf')])])])), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'escapes'):
                read_manifest(manifest)

    def test_hashed_spacing_metadata_has_portable_lf_bytes(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch('display.title_spacing.export_spacing', return_value={'glyph':'Á'}):
            write_spacing('unused.otf', self.soft, {}, None, directory)
            self.assertEqual((Path(directory)/'spacing_soft.json').read_bytes(), '{"glyph":"Á"}\n'.encode('utf-8'))


if __name__ == '__main__':
    unittest.main()
