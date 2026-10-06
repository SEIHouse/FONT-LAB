"""Candidate font builds must leave shipped spacing metadata untouched."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import make_fonts
from display import make_display


class FakeCore:
    """Avoid browser/hint work while exercising the entry points' actual writes."""
    def __init__(self, settings, *, display=False, asset_dir=None):
        self.asset_dir = Path(asset_dir)
        self.S = settings['weight']
        self.ITAL = False
        self.FAMILY = 'fixture'
        self.VERSION = '0'
        self.STYLE_KERN = {'Regular': {'AV': -10}}
        self.LANGUAGE_KERN = {'Regular': {'hu': {'TY': 10}}}

    def export(self):
        return {'kern': {'AV': -10}}

    def build(self, data, out, *args):
        (self.asset_dir/'kern_auto.json').write_text('{}', encoding='utf-8')
        Path(out).write_bytes(b'candidate')


class CandidateOutputTests(unittest.TestCase):
    def test_shared_display_stylesheet_rebuilds_missing_and_stale_subsets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stale = root/'fonts/edge/SEIHouseDisplay-Edge.otf'
            stale.parent.mkdir(parents=True)
            stale.write_bytes(b'existing cut')
            stale.with_suffix('.latin-basic.woff2').write_bytes(b'stale subset')
            cut = root/'cut.json'
            cut.write_text(json.dumps({'name':'Soft', 'weight':85}), encoding='utf-8')

            def rebuild_subsets(source):
                source.with_suffix('.latin-basic.woff2').write_bytes(source.read_bytes())

            def validate_css(sources, output):
                for source in sources:
                    self.assertEqual(source.with_suffix('.latin-basic.woff2').read_bytes(), source.read_bytes())
                output.write_text('valid stylesheet', encoding='utf-8')

            with patch.object(make_display, 'HERE', root), patch.object(make_display, 'FontBuilderCore', FakeCore), \
                 patch.object(make_display, 'build_cut_subsets', rebuild_subsets), \
                 patch.object(make_display, 'write_css', validate_css):
                make_display.build_cut(cut)
            self.assertEqual((root/'fonts.css').read_text(encoding='utf-8'), 'valid stylesheet')

    def test_reader_candidate_metadata_stays_with_candidate_fonts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('kern_base.json', 'kern_auto.json', 'kern_styles.json', 'kern_languages.json'):
                (root/name).write_text('approved', encoding='utf-8')
            candidate = root/'candidate'
            with patch.object(make_fonts, 'HERE', root), patch.object(make_fonts, 'FontBuilderCore', FakeCore):
                make_fonts.build_fonts({'weight':85, 'weights':{'Regular':85}}, candidate)
            for name in ('kern_base.json', 'kern_auto.json', 'kern_styles.json', 'kern_languages.json'):
                self.assertEqual((root/name).read_text(encoding='utf-8'), 'approved')
                self.assertTrue((candidate/name).is_file())

    def test_display_candidate_metadata_stays_with_candidate_fonts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'kern_auto_soft.json').write_text('approved', encoding='utf-8')
            cut = root/'cut.json'
            cut.write_text(json.dumps({'name':'Soft', 'weight':85}), encoding='utf-8')
            candidate = root/'candidate'
            with patch.object(make_display, 'HERE', root), patch.object(make_display, 'FontBuilderCore', FakeCore), \
                 patch.object(make_display, 'build_cut_subsets') as subsets, patch.object(make_display, 'write_css') as css:
                make_display.build_cut(cut, candidate)
            subsets.assert_called_once_with(candidate/'SEIHouseDisplay-Soft.otf')
            css.assert_called_once_with([candidate/'SEIHouseDisplay-Soft.otf'], candidate/'fonts.css')
            self.assertEqual((root/'kern_auto_soft.json').read_text(encoding='utf-8'), 'approved')
            self.assertTrue((candidate/'kern_auto.json').is_file())


if __name__ == '__main__':
    unittest.main()
