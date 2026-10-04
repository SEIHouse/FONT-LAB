"""Shipped glyph bounds must fit Windows clipping without changing line spacing."""
from pathlib import Path
import unittest

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]


class DisplayClippingTests(unittest.TestCase):
    def assert_ink_fits(self, font):
        """Measure every finished glyph through the glyph-set drawing interface."""
        glyphs = font.getGlyphSet()
        os2 = font['OS/2']
        for name in font.getGlyphOrder():
            pen = BoundsPen(glyphs)
            glyphs[name].draw(pen)
            if pen.bounds:
                self.assertLessEqual(pen.bounds[3], os2.usWinAscent, name)
                self.assertGreaterEqual(pen.bounds[1], -os2.usWinDescent, name)

    def test_every_display_cut_fits_windows_clipping_and_retains_line_spacing(self):
        for cut in ('soft', 'edge', 'ink', 'wide'):
            with self.subTest(cut=cut), TTFont(ROOT/f'display/fonts/{cut}/SEIHouseDisplay-{cut.title()}.otf') as font:
                self.assert_ink_fits(font)
                self.assertEqual((font['hhea'].ascent, font['hhea'].descent, font['hhea'].lineGap),
                                 (1900, -500, 0))
                self.assertEqual((font['OS/2'].sTypoAscender, font['OS/2'].sTypoDescender, font['OS/2'].sTypoLineGap),
                                 (1900, -500, 0))

    def test_original_edge_clipping_rejects_inherited_vietnamese_stacks(self):
        with TTFont(ROOT/'display/fonts/edge/SEIHouseDisplay-Edge.otf') as font:
            font['OS/2'].usWinAscent = 2200
            with self.assertRaises(AssertionError):
                self.assert_ink_fits(font)


if __name__ == '__main__':
    unittest.main()
