"""Check the SEIHouse Noto redraw: outlines, weights, spacing, shaping and delivery."""
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

import pathops
import uharfbuzz as hb
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1] / 'noto/studies/redraw'
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('redraw_build', ROOT/'build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

STYLES = ['Light', 'Regular', 'Medium', 'Bold']
PROSE = ['The morning light settled gently over the quiet library.',
         'Zażółć gęślą jaźń. Příliš žluťoučký kůň. Ça va, señor? Größe, Æther, Øre, Þór.',
         '“Good evening,” it began — (128 chapters) & 50% off @ £9.99!']


def outline(font, name):
    path = pathops.Path()
    font.getGlyphSet()[name].draw(path.getPen())
    return path


class RedrawTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.output = Path(cls.temporary.name)
        cls.reports = [build.build_font(s, out_dir=cls.output) for s in build.WEIGHTS]
        cls.fonts = {}
        for style in STYLES:
            cls.fonts[style] = TTFont(ROOT/'fonts'/f'SEIHouseNoto-{style}.otf')
            cls.addClassCleanup(cls.fonts[style].close)

    def test_checked_in_fonts_match_the_source_drawings(self):
        """Advances are exact and outlines agree to a unit, on any build platform."""
        self.assertEqual([s['name'] for s in build.WEIGHTS], STYLES)
        for style in STYLES:
            with TTFont(self.output/f'SEIHouseNoto-{style}.otf') as rebuilt:
                shipped = self.fonts[style]
                self.assertEqual(rebuilt.getGlyphOrder(), shipped.getGlyphOrder())
                self.assertEqual(rebuilt.getBestCmap(), shipped.getBestCmap())
                for name in shipped.getGlyphOrder():
                    self.assertEqual(rebuilt['hmtx'][name][0], shipped['hmtx'][name][0], name)
                    a, b = outline(rebuilt, name).bounds, outline(shipped, name).bounds
                    for x, y in zip(a, b):
                        self.assertAlmostEqual(x, y, delta=1.5, msg=f'{style} {name}')
            with TTFont(ROOT/'fonts'/f'SEIHouseNoto-{style}.woff2') as web:
                self.assertEqual(web.getGlyphOrder(), self.fonts[style].getGlyphOrder())

    def test_every_glyph_is_a_clean_outline_inside_the_line(self):
        for style, font in self.fonts.items():
            self.assertGreaterEqual(len(font.getBestCmap()), 310)
            for name in font.getGlyphOrder():
                with self.subTest(style=style, glyph=name):
                    advance = font['hmtx'][name][0]
                    self.assertGreater(advance, 0)
                    path = outline(font, name)
                    if name in ('space', 'u00A0'):
                        self.assertEqual(len(list(path.contours)), 0)
                        continue
                    x0, y0, x1, y1 = path.bounds
                    self.assertGreater(x1-x0, 20)
                    self.assertGreater(y1-y0, 20)
                    self.assertGreaterEqual(y0, font['hhea'].descent)
                    self.assertLessEqual(y1, font['hhea'].ascent)
                    self.assertGreater(x0, -190)
                    self.assertLess(x1, advance+90)
                    for contour in path.contours:
                        self.assertGreater(abs(contour.area), 40, 'Detached outline fragment')

    def test_counters_stay_open_at_every_weight(self):
        expected = {**dict.fromkeys('abdeopqADOPQR0469@', 2), **dict.fromkeys('gB8', 3), '%': 5, 'i': 2, 'j': 2,
                    'c': 1, 's': 1, 'n': 1, 'S': 1, 'C': 1, '&': 3, 'æ': 3, 'œ': 3, 'ß': 1}
        for style, font in self.fonts.items():
            cmap = font.getBestCmap()
            for char, count in expected.items():
                self.assertEqual(len(list(outline(font, cmap[ord(char)]).contours)), count, f'{style} {char}')

    def test_heights_and_overshoots_are_shared(self):
        for style, font in self.fonts.items():
            cmap = font.getBestCmap()
            box = lambda c: outline(font, cmap[ord(c)]).bounds
            for char in 'nhmrixz':
                self.assertAlmostEqual(box(char)[1], 0, delta=1, msg=f'{style} {char}')
            for char in 'xz':
                self.assertAlmostEqual(box(char)[3], 520, delta=1, msg=f'{style} {char}')
            for char in 'HEIT':
                self.assertAlmostEqual(box(char)[3], 700, delta=1, msg=f'{style} {char}')
            self.assertAlmostEqual(box('o')[1], -11, delta=1.5)
            self.assertAlmostEqual(box('o')[3], 531, delta=1.5)
            self.assertAlmostEqual(box('O')[3], 711, delta=1.5)
            self.assertAlmostEqual(box('p')[1], box('q')[1], delta=1)
            self.assertEqual(font['OS/2'].sxHeight, 520)
            self.assertEqual(font['OS/2'].sCapHeight, 700)

    def test_weights_grow_in_order_and_figures_do_not_reflow(self):
        stems = []
        for style in STYLES:
            font = self.fonts[style]
            cmap = font.getBestCmap()
            x0, _, x1, _ = outline(font, cmap[ord('ı')]).bounds
            stems.append(x1-x0)
            self.assertEqual({font['hmtx'][cmap[ord(d)]][0] for d in '0123456789'}, {572})
        self.assertEqual(stems, sorted(stems))
        self.assertTrue(70 < stems[0] < 82 < stems[1] < 94 < stems[2] < 112 < stems[3] < 140, stems)
        self.assertEqual([self.fonts[s]['OS/2'].usWeightClass for s in STYLES], [300, 400, 500, 700])
        self.assertEqual(self.fonts['Bold']['head'].macStyle & 1, 1)

    def test_modulation_and_tapered_joins(self):
        """Horizontals are lighter than verticals, and an arch thins where it leaves its stem."""
        font = self.fonts['Regular']
        cmap = font.getBestCmap()
        o = [c.bounds for c in outline(font, cmap[ord('o')]).contours]
        outer, inner = sorted(o, key=lambda b: b[0])
        side, crown = inner[0]-outer[0], outer[3]-inner[3]
        self.assertGreater(side, crown+8)
        self.assertLess(crown, 78)
        # In n the arch has thinned away from the stem well below the x-height.
        n = outline(font, cmap[ord('n')])
        left = n.bounds[0]
        band = pathops.op(n, _box(left-10, 348, left+260, 352), pathops.PathOp.INTERSECTION)
        run = min((c.bounds for c in band.contours), key=lambda b: b[0])
        self.assertAlmostEqual(run[2]-run[0], 88, delta=3)

    def test_prose_shapes_without_missing_glyphs_or_collisions(self):
        for style in STYLES:
            data = (ROOT/'fonts'/f'SEIHouseNoto-{style}.otf').read_bytes()
            hbfont = hb.Font(hb.Face(data))
            font = self.fonts[style]
            order = font.getGlyphOrder()

            def shape(text, kern=True):
                buffer = hb.Buffer()
                buffer.add_str(text)
                buffer.guess_segment_properties()
                hb.shape(hbfont, buffer, {'kern': kern})
                self.assertTrue(all(info.codepoint for info in buffer.glyph_infos), f'{style}: {text}')
                return buffer

            for text in PROSE:
                shape(text)
            width = lambda text, kern=True: sum(p.x_advance for p in shape(text, kern).glyph_positions)
            for pair in ['To', 'AV', 'Wa', 'Yo', 'LT', 'r.', 'Tö', 'Vé']:
                self.assertLess(width(pair), width(pair, False), f'{style} {pair}')
            for pair in ['nn', 'oo', 'HH', 'il']:
                self.assertEqual(width(pair), width(pair, False), f'{style} {pair}')
            # Kerned neighbours keep clear ink, also under accents and overhangs.
            for text in ['To', 'Tö', 'Tï', 'Vé', 'fï', 'f)', 'f”', 'AV', 'Wa', 'r.', 'LT', 'Yo', '(j', 'gj']:
                buffer = shape(text)
                a, b = (outline(font, order[info.codepoint]) for info in buffer.glyph_infos)
                shift = buffer.glyph_positions[0].x_advance
                moved = b.transform(1, 0, 0, 1, shift, 0)
                overlap = pathops.op(a, moved, pathops.PathOp.INTERSECTION)
                self.assertEqual(len(list(overlap.contours)), 0, f'{style}: ink collision in {text}')

    def test_page_and_manifest_describe_the_built_fonts(self):
        manifest = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['status'], 'candidate')
        self.assertEqual([f['style'] for f in manifest['fonts']], STYLES)
        cmap = self.fonts['Regular'].getBestCmap()
        import hashlib
        for entry in manifest['fonts']:
            data = (ROOT/'fonts'/f"{entry['psname']}.woff2").read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry['sha256'])
            self.assertEqual({ord(c) for c in entry['characters']}, set(cmap))
        page = (ROOT/'index.html').read_text(encoding='utf-8')
        charset = json.loads(re.search(r'/\*CHARSET\*/(".*?")/\*END\*/', page, re.S).group(1))
        self.assertEqual({ord(c) for c in charset} | {0xA0}, set(cmap))
        shown = re.search(r'<p class="glyphs-all">(.*?)</p>', page, re.S).group(1)
        import html
        shown = html.unescape(re.sub(r'<span>.*?</span>', '', shown))
        self.assertFalse({c for c in shown if not c.isspace() and ord(c) not in cmap})
        for style in STYLES:
            self.assertIn(f'fonts/SEIHouseNoto-{style}.woff2', page)


def _box(x0, y0, x1, y1):
    path = pathops.Path()
    pen = path.getPen()
    pen.moveTo((x0, y0)); pen.lineTo((x1, y0)); pen.lineTo((x1, y1)); pen.lineTo((x0, y1)); pen.closePath()
    return path


if __name__ == '__main__':
    unittest.main()
