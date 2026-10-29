"""Check the selected base, final outlines, spacing and generated delivery."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pathops
import uharfbuzz as hb
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1] / 'noto/studies/warmth'
spec = importlib.util.spec_from_file_location('balanced_study', ROOT/'build_samples.py')
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class BalancedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.output = Path(cls.temporary.name)
        with patch.object(study, 'ROOT', cls.output):
            study.build_font(study.STUDIES[1])
            study.build_font(study.REFINEMENT)
        cls.font = TTFont(cls.output/'fonts/SEIHouseNotoBalanced-Regular.otf')
        cls.addClassCleanup(cls.font.close)

    def test_approved_balanced_is_unchanged_and_refinement_is_reproducible(self):
        baseline = (self.output/'fonts/SEIHouseNotoStudyB-Regular.woff2').read_bytes()
        self.assertEqual(hashlib.sha256(baseline).hexdigest(),
                         'e8a81727e9fdcde265498f2bdcbe1876802e538368bdeda146ef57b0c56a35b0')
        self.assertEqual(study.SELECTED_BASE_ID, 'B')
        for extension in ['otf', 'woff2']:
            name = f'SEIHouseNotoBalanced-Regular.{extension}'
            self.assertEqual((ROOT/'fonts'/name).read_bytes(), (self.output/'fonts'/name).read_bytes())

    def test_every_glyph_has_valid_geometry_and_fits_the_line(self):
        font = self.font
        glyphs = font.getGlyphSet()
        self.assertEqual(len(font.getBestCmap()), 94)
        self.assertAlmostEqual(font['head'].fontRevision, .002, delta=.00001)
        self.assertEqual(font['OS/2'].ulCodePageRange1, 1)
        for name in font.getGlyphOrder():
            with self.subTest(glyph=name):
                advance, _ = font['hmtx'][name]
                self.assertGreater(advance, 0)
                path = pathops.Path()
                glyphs[name].draw(path.getPen())
                if name == 'space':
                    self.assertEqual(len(list(path.contours)), 0)
                    continue
                x0,y0,x1,y1 = path.bounds
                self.assertGreater(x1,x0)
                self.assertGreater(y1,y0)
                self.assertGreaterEqual(x0,-1)
                self.assertLessEqual(x1,advance+1)
                self.assertGreaterEqual(y0,font['hhea'].descent)
                self.assertLessEqual(y1,font['hhea'].ascent)
                for contour in path.contours:
                    self.assertGreater(abs(contour.area), 1, 'Detached outline fragment')

    def test_counters_remain_open_and_straight_stems_share_the_baseline(self):
        glyphs, cmap = self.font.getGlyphSet(), self.font.getBestCmap()
        for char, count in {**dict.fromkeys('abdegopqBOPQR0689',2), 'g':3,'B':3,'8':3,',':1,';':2}.items():
            path = pathops.Path()
            glyphs[cmap[ord(char)]].draw(path.getPen())
            self.assertEqual(len(list(path.contours)),count,char)
        for char in 'hnmr':
            path = pathops.Path()
            glyphs[cmap[ord(char)]].draw(path.getPen())
            self.assertAlmostEqual(path.bounds[1],0,delta=1,msg=char)

    def test_accent_kerning_and_real_prose_shape_without_missing_glyphs(self):
        data = (self.output/'fonts/SEIHouseNotoBalanced-Regular.otf').read_bytes()
        font = hb.Font(hb.Face(data))
        def shape(text, kern=True):
            buffer = hb.Buffer()
            buffer.add_str(text)
            buffer.guess_segment_properties()
            hb.shape(font,buffer,{'kern':kern})
            self.assertTrue(all(glyph.codepoint for glyph in buffer.glyph_infos),text)
            glyphs = self.font.getGlyphSet()
            order = self.font.getGlyphOrder()
            cursor, last_right = 0, None
            for info, pos in zip(buffer.glyph_infos, buffer.glyph_positions):
                path = pathops.Path()
                glyphs[order[info.codepoint]].draw(path.getPen())
                if list(path.contours):
                    left,_,right,_ = path.bounds
                    if last_right is not None:
                        self.assertGreater(cursor+pos.x_offset+left,last_right,'Ink collision in '+text)
                    last_right = cursor+pos.x_offset+right
                cursor += pos.x_advance
            return sum(pos.x_advance for pos in buffer.glyph_positions)
        for text in ['To','Tó','Tö','Wa','Wá','AV','minimum river','é á í ó ú ö ü ñ è',
                     'The morning light settled gently over the quiet library.']:
            self.assertGreater(shape(text),0)
        self.assertLess(shape('To'),shape('To',False))
        self.assertEqual(shape('To')-shape('To',False),shape('Tó')-shape('Tó',False))


if __name__ == '__main__':
    unittest.main()
