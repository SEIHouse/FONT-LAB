"""Check the SEIHouse Noto redraw: outlines, weights, spacing, shaping and delivery."""
import importlib.util
import json
import re
import sys
import tempfile
import unicodedata
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
ITALICS = ['Light Italic', 'Italic', 'Medium Italic', 'Bold Italic']
NIGHTS = ['Light Night', 'Regular Night', 'Medium Night', 'Light Italic Night', 'Italic Night', 'Medium Italic Night']
PROSE = ['The morning light settled gently over the quiet library.',
         'Zażółć gęślą jaźń. Příliš žluťoučký kůň. Ça va, señor? Größe, Æther, Øre, Þór.',
         '“Good evening,” it began — (128 chapters) & 50% off @ £9.99!',
         '© 2026 ® §12 ¶4: 22° ± 1°, 3×4÷2, ¼ ½ ¾, m¹ m² m³, 15 µm, 1ª 2º, ¬p ¦ q, ¤9, Ĳssel ĳs, ĿL paralŀel, ĸ, ŉ, Ŋ/ŋ, ſi ¨¯´¸.']


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
        manifest = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
        for report, entry in zip(self.reports, manifest['fonts'][:len(STYLES)], strict=True):
            # Pairs right at the threshold can flip between platforms' floating-point maths.
            self.assertAlmostEqual(report['kerning_pairs'], entry['kerning_pairs'],
                                   delta=entry['kerning_pairs']*.01, msg=report['style'])
            self.assertEqual(report['glyphs'], entry['glyphs'], report['style'])

    def test_every_glyph_is_a_clean_outline_inside_the_line(self):
        required = (set(range(0x20, 0x7F)) | (set(range(0xA0, 0x100)) - {0xAD}) | set(range(0x100, 0x180)))
        for style, font in self.fonts.items():
            cmap = font.getBestCmap()
            gdef = font['GDEF'].table.GlyphClassDef.classDefs
            self.assertGreaterEqual(len(cmap), 365)
            self.assertFalse(required - set(cmap), f'{style} missing Latin-1/Extended-A codepoints')
            for name in font.getGlyphOrder():
                with self.subTest(style=style, glyph=name):
                    advance = font['hmtx'][name][0]
                    path = outline(font, name)
                    if name in ('space', 'u00A0'):
                        self.assertGreater(advance, 0)
                        self.assertEqual(len(list(path.contours)), 0)
                        continue
                    x0, y0, x1, y1 = path.bounds
                    self.assertGreater(x1-x0, 20)
                    self.assertGreater(y1-y0, 20)
                    self.assertGreaterEqual(y0, font['hhea'].descent)
                    self.assertLessEqual(y1, font['hhea'].ascent)
                    if gdef.get(name) == 3:
                        self.assertEqual(advance, 0)
                        self.assertGreater(x0, -260)
                        self.assertLess(x1, 280)
                    else:
                        self.assertGreater(advance, 0)
                        self.assertGreater(x0, -190)
                        self.assertLess(x1, advance+90)
                    for contour in path.contours:
                        self.assertGreater(abs(contour.area), 40, 'Detached outline fragment')

    def test_counters_stay_open_at_every_weight(self):
        expected = {**dict.fromkeys('abdeopqADOPQR0469@¤§¶', 2), **dict.fromkeys('gB8©ªº½', 3),
                    **dict.fromkeys('®¼¾', 4), '%': 5, 'i': 2, 'j': 2, 'Š': 2, 'Č': 2, 'ť': 2,
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
            for text in ['To', 'Tö', 'Tï', 'Vé', 'fï', 'f)', 'f”', 'AV', 'Wa', 'r.', 'LT', 'Yo', '(j', 'gj',
                         'ïï', 'îî', 'ĩĩ', 'īī', 'ĭĭ', 'ïl', 'lï', 'ťď', 'ľľ', 'řï', 'ÏÏ', 'ŤÖ', 'ÿï', 'őő',
                         'ÂÂ', 'ÃÃ', 'ŠŤ', 'ŤŠ', 'ÑÑ', 'ÎÏ', 'ŴÂ', 'ÝÃ', 'ĽŤ', 'ÅÅ', 'ĥĥ', 'ĺĺ', 'Ťĥ',
                         'Ĳs', 'ĳs', 'Tĳ', 'ĿT', 'ĿV', 'ŀl', 'ŋj', 'ſï', 'ſö', 'ſ)']:
                buffer = shape(text)
                a, b = (outline(font, order[info.codepoint]) for info in buffer.glyph_infos)
                shift = buffer.glyph_positions[0].x_advance
                moved = b.transform(1, 0, 0, 1, shift, 0)
                overlap = pathops.op(a, moved, pathops.PathOp.INTERSECTION)
                self.assertEqual(len(list(overlap.contours)), 0, f'{style}: ink collision in {text}')

    def test_page_and_manifest_describe_the_built_fonts(self):
        manifest = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['status'], 'candidate')
        self.assertEqual([f['style'] for f in manifest['fonts']], STYLES + ITALICS + NIGHTS)
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
        for style in STYLES + ITALICS + NIGHTS:
            self.assertIn(f"fonts/SEIHouseNoto-{style.replace(' ', '')}.woff2", page)

    def test_reading_size_a_e_g_s_proportions_and_loop_balance(self):
        cases = {
            'Regular': {'g_ratio_max': 1.42, 'counter_min': 32000, 's_spine_max': 90},
            'Bold': {'g_ratio_max': 1.68, 'counter_min': 28000, 's_spine_max': 100},
        }
        for style, limits in cases.items():
            font = self.fonts[style]
            cmap = font.getBestCmap()

            gp = outline(font, cmap[ord('g')])
            inner = sorted(sorted(gp.contours, key=lambda c: c.area)[:-1], key=lambda c: c.bounds[1])
            self.assertEqual(len(inner), 2, f'{style} g should have lower and upper counters')
            lower_w = inner[0].bounds[2] - inner[0].bounds[0]
            upper_w = inner[1].bounds[2] - inner[1].bounds[0]
            self.assertLessEqual(
                lower_w / upper_w,
                limits['g_ratio_max'],
                f'{style} g lower counter too wide vs upper bowl ({lower_w:.1f} vs {upper_w:.1f})',
            )
            g_adv, _ = font['hmtx'][cmap[ord('g')]]
            self.assertGreaterEqual(g_adv - gp.bounds[2], 16, f'{style} g right sidebearing too tight')

            densities = {}
            for ch in ('a', 'e'):
                p = outline(font, cmap[ord(ch)])
                counter = min(p.contours, key=lambda c: c.area)
                self.assertGreater(counter.area, limits['counter_min'], f'{style} {ch} counter too small')
                adv, _ = font['hmtx'][cmap[ord(ch)]]
                ink = pathops.Path()
                pathops.intersection([p], [_box(-200, 0, adv + 200, 520)], ink.getPen())
                densities[ch] = ink.area / (adv * 520)
            self.assertLess(abs(densities['a'] - densities['e']), 0.02, f'{style} a/e x-height density mismatch')

            sp = outline(font, cmap[ord('s')])
            sb = sp.bounds
            mid_x = (sb[0] + sb[2]) / 2
            slice_path = pathops.Path()
            pathops.intersection([sp], [_box(mid_x - 0.5, sb[1] - 10, mid_x + 0.5, sb[3] + 10)], slice_path.getPen())
            segs = sorted(slice_path.contours, key=lambda c: c.bounds[1])
            self.assertEqual(len(segs), 3, f'{style} s center slice should cross 3 strokes')
            spine_t = segs[1].bounds[3] - segs[1].bounds[1]
            self.assertLess(spine_t, limits['s_spine_max'], f'{style} s spine too heavy ({spine_t:.1f})')


def psname(style):
    return f"SEIHouseNoto-{style.replace(' ', '')}"


class ItalicTests(unittest.TestCase):
    """True italics: drawn italic forms, slanted outlines and correct style linking."""

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.output = Path(cls.temporary.name)
        cls.reports = [build.build_font(s, out_dir=cls.output) for s in build.ITALICS]
        cls.fonts, cls.uprights = {}, {}
        for style, upright in zip(ITALICS, STYLES):
            cls.fonts[style] = TTFont(ROOT/'fonts'/f'{psname(style)}.otf')
            cls.uprights[style] = TTFont(ROOT/'fonts'/f'{psname(upright)}.otf')
            cls.addClassCleanup(cls.fonts[style].close)
            cls.addClassCleanup(cls.uprights[style].close)

    def test_checked_in_italics_match_the_source_drawings(self):
        self.assertEqual([s['name'] for s in build.ITALICS], ITALICS)
        manifest = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
        entries = manifest['fonts'][len(STYLES):len(STYLES) + len(ITALICS)]
        for style, report, entry in zip(ITALICS, self.reports, entries, strict=True):
            with TTFont(self.output/f'{psname(style)}.otf') as rebuilt:
                shipped = self.fonts[style]
                self.assertEqual(rebuilt.getGlyphOrder(), shipped.getGlyphOrder())
                for name in shipped.getGlyphOrder():
                    self.assertEqual(rebuilt['hmtx'][name][0], shipped['hmtx'][name][0], name)
                    for x, y in zip(outline(rebuilt, name).bounds, outline(shipped, name).bounds):
                        self.assertAlmostEqual(x, y, delta=1.5, msg=f'{style} {name}')
            self.assertEqual(report['glyphs'], entry['glyphs'])
            self.assertAlmostEqual(report['kerning_pairs'], entry['kerning_pairs'], delta=entry['kerning_pairs']*.01)
            # Same character set as the upright, so switching style never drops a glyph.
            self.assertEqual(self.fonts[style].getBestCmap().keys(), self.uprights[style].getBestCmap().keys())

    def test_style_linking_and_slant_metadata(self):
        for style, font in self.fonts.items():
            upright = self.uprights[style]
            self.assertEqual(font['post'].italicAngle, -10)
            self.assertEqual(font['hhea'].caretSlopeRise, 1000)
            self.assertEqual(font['hhea'].caretSlopeRun, 176)
            self.assertTrue(font['OS/2'].fsSelection & 0x01, style)
            self.assertFalse(font['OS/2'].fsSelection & 0x40, style)
            self.assertTrue(font['head'].macStyle & 2, style)
            self.assertEqual(font['OS/2'].usWeightClass, upright['OS/2'].usWeightClass)
            self.assertEqual(bool(font['head'].macStyle & 1), style == 'Bold Italic')
            name = font['name']
            # Legacy apps see a four-style family, modern apps one family with eight styles.
            self.assertEqual(name.getDebugName(1), upright['name'].getDebugName(1))
            self.assertEqual(name.getDebugName(2), 'Bold Italic' if style == 'Bold Italic' else 'Italic')
            self.assertEqual(name.getDebugName(16) or name.getDebugName(1), 'SEIHouse Noto')
            self.assertEqual(name.getDebugName(17) or name.getDebugName(2), style)
            self.assertEqual(name.getDebugName(6), psname(style))

    def test_outlines_are_clean_and_lean_at_ten_degrees(self):
        for style, font in self.fonts.items():
            cmap = font.getBestCmap()
            gdef = font['GDEF'].table.GlyphClassDef.classDefs
            for name in font.getGlyphOrder():
                if name in ('space', 'u00A0'):
                    continue
                path = outline(font, name)
                x0, y0, x1, y1 = path.bounds
                self.assertGreaterEqual(y0, font['hhea'].descent, f'{style} {name}')
                self.assertLessEqual(y1, font['hhea'].ascent, f'{style} {name}')
                if gdef.get(name) == 3:
                    self.assertEqual(font['hmtx'][name][0], 0, f'{style} {name}')
                    self.assertGreater(x0, -260, f'{style} {name}')
                    self.assertLess(x1, 280, f'{style} {name}')
                else:
                    self.assertLess(x1, font['hmtx'][name][0]+190, f'{style} {name}')
                for contour in path.contours:
                    self.assertGreater(abs(contour.area), 40, f'{style} {name}: detached fragment')
            # The I stem leans: its top sits 700·tan 10° ≈ 123 units right of its foot.
            stem = outline(font, cmap[ord('l')])
            low = pathops.op(stem, _box(-400, 300, 1200, 304), pathops.PathOp.INTERSECTION).bounds
            high = pathops.op(stem, _box(-400, 600, 1200, 604), pathops.PathOp.INTERSECTION).bounds
            self.assertAlmostEqual(high[0]-low[0], 300*.1763, delta=3, msg=style)
            # Heights are unchanged by the slant.
            self.assertAlmostEqual(outline(font, cmap[ord('x')]).bounds[3], 520, delta=1)
            self.assertAlmostEqual(outline(font, cmap[ord('H')]).bounds[3], 700, delta=1)
            self.assertEqual({font['hmtx'][cmap[ord(d)]][0] for d in '0123456789'}, {572})

    def test_italic_letterforms_are_drawn_not_slanted(self):
        for style, font in self.fonts.items():
            cmap = font.getBestCmap()
            upright = self.uprights[style]
            ucmap = upright.getBestCmap()
            contours = lambda f, c, m: len(list(outline(f, m[ord(c)]).contours))
            # Single-storey a: its counter rises to near the x-height; the upright
            # two-storey a keeps its closed bowl in the lower half.
            counter_top = lambda f, m: min((c.bounds for c in outline(f, m[ord('a')]).contours),
                                           key=lambda box: box[2]-box[0])[3]
            self.assertLess(counter_top(upright, ucmap), 300, style)
            self.assertGreater(counter_top(font, cmap), 400, style)
            # f descends below the baseline; the upright f sits on it.
            self.assertLess(outline(font, cmap[ord('f')]).bounds[1], -150)
            self.assertGreater(outline(upright, ucmap[ord('f')]).bounds[1], -2)
            # Two-storey g stays, as the family signature.
            self.assertEqual(contours(font, 'g', cmap), 3)
            # Exit strokes: n, i, u, a, d reach beyond where their stems stand.
            for char in 'nimuadh':
                ink = outline(font, cmap[ord(char)]).bounds
                advance = font['hmtx'][cmap[ord(char)]][0]
                self.assertGreater(ink[2], advance-40, f'{style} {char}')
            # Italics are a little narrower than upright.
            for char in 'nHo':
                ratio = font['hmtx'][cmap[ord(char)]][0] / upright['hmtx'][ucmap[ord(char)]][0]
                self.assertTrue(.93 < ratio < .99, f'{style} {char} {ratio}')

    def test_italic_prose_shapes_with_clear_ink(self):
        for style in ITALICS:
            data = (ROOT/'fonts'/f'{psname(style)}.otf').read_bytes()
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

            for text in PROSE + ['Don’t move, he told himself — not yet.']:
                shape(text)
            width = lambda text, kern=True: sum(p.x_advance for p in shape(text, kern).glyph_positions)
            # Exit strokes reach toward the next letter without loosening the rhythm.
            for pair in ['nn', 'mn', 'un', 'an', 'dn', 'in', 'ii', 'HH', 'oo']:
                self.assertEqual(width(pair), width(pair, False), f'{style} {pair}')
            for pair in ['To', 'AV', 'Wa', 'Yo']:
                self.assertLess(width(pair), width(pair, False), f'{style} {pair}')
            for text in ['nn', 'mm', 'uu', 'ii', 'aa', 'dd', 'hh', 'in', 'an', 'nj', 'ng', 'ay', 'af', 'nf', 'gf',
                         'yf', 'jf', 'ff', 'fï', 'f)', 'f”', 'To', 'Tö', 'AV', 'ïï', 'ââ', 'ďď', 'ťď', 'ĳs', 'ŉn']:
                buffer = shape(text)
                a, b = (outline(font, order[info.codepoint]) for info in buffer.glyph_infos)
                moved = b.transform(1, 0, 0, 1, buffer.glyph_positions[0].x_advance, 0)
                overlap = pathops.op(a, moved, pathops.PathOp.INTERSECTION)
                self.assertEqual(len(list(overlap.contours)), 0, f'{style}: ink collision in {text}')


class NightGradeTests(unittest.TestCase):
    """Zero-reflow Night optical grade: thinner strokes for dark UI, identical widths & kerning."""

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.output = Path(cls.temporary.name)
        day_cache = {}
        cls.reports = [build.build_font(s, out_dir=cls.output, day_cache=day_cache) for s in build.NIGHTS]
        cls.fonts, cls.days = {}, {}
        for style in NIGHTS:
            day_style = style.removesuffix(' Night')
            cls.fonts[style] = TTFont(ROOT/'fonts'/f'{psname(style)}.otf')
            cls.days[style] = TTFont(ROOT/'fonts'/f'{psname(day_style)}.otf')
            cls.addClassCleanup(cls.fonts[style].close)
            cls.addClassCleanup(cls.days[style].close)

    def test_checked_in_night_fonts_match_the_source_drawings(self):
        self.assertEqual([s['name'] for s in build.NIGHTS], NIGHTS)
        manifest = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
        entries = manifest['fonts'][len(STYLES) + len(ITALICS):]
        for style, report, entry in zip(NIGHTS, self.reports, entries, strict=True):
            self.assertEqual(entry['style'], style)
            with TTFont(self.output/f'{psname(style)}.otf') as rebuilt:
                shipped = self.fonts[style]
                self.assertEqual(rebuilt.getGlyphOrder(), shipped.getGlyphOrder())
                for name in shipped.getGlyphOrder():
                    self.assertEqual(rebuilt['hmtx'][name][0], shipped['hmtx'][name][0], f'{style} {name}')
                    for x, y in zip(outline(rebuilt, name).bounds, outline(shipped, name).bounds):
                        self.assertAlmostEqual(x, y, delta=1.5, msg=f'{style} {name}')
            self.assertEqual(report['glyphs'], entry['glyphs'])
            self.assertAlmostEqual(report['kerning_pairs'], entry['kerning_pairs'], delta=entry['kerning_pairs']*.01)
            self.assertEqual(self.fonts[style].getBestCmap().keys(), self.days[style].getBestCmap().keys())

    def test_night_strokes_are_thinner_while_counters_and_bounds_stay_clean(self):
        band = _box(-200, 300, 1200, 304)
        for style, font in self.fonts.items():
            day = self.days[style]
            italic = 'Italic' in style
            stem_glyph = 'u006C' if italic else 'u0131'
            d_slice = pathops.op(outline(day, stem_glyph), band, pathops.PathOp.INTERSECTION)
            n_slice = pathops.op(outline(font, stem_glyph), band, pathops.PathOp.INTERSECTION)
            d_w = d_slice.bounds[2] - d_slice.bounds[0]
            n_w = n_slice.bounds[2] - n_slice.bounds[0]
            expected_thin = 4.06 if italic else 4.0
            self.assertAlmostEqual(d_w - n_w, expected_thin, delta=0.35, msg=style)
            for name in day.getGlyphOrder():
                d_path, n_path = outline(day, name), outline(font, name)
                d_cnt, n_cnt = len(list(d_path.contours)), len(list(n_path.contours))
                self.assertEqual(n_cnt, d_cnt, f'{style} {name}')
                if list(d_path.contours):
                    self.assertGreater(abs(n_path.area), 40, f'{style} {name}')
            for ch in ('a', 'e', 'g', 's', 'B', '8'):
                gname = f'u{ord(ch):04X}'
                self.assertLess(abs(outline(font, gname).area), abs(outline(day, gname).area), f'{style} {ch}')

    def test_night_metadata_and_style_linking(self):
        for style, font in self.fonts.items():
            day = self.days[style]
            italic = 'Italic' in style
            weight_name = style.removesuffix(' Night').replace(' Italic', '').replace('Italic', 'Regular')
            expected_family = 'SEIHouse Noto Night' if weight_name == 'Regular' else f'SEIHouse Noto {weight_name} Night'
            name = font['name']
            self.assertEqual(name.getDebugName(1), expected_family, style)
            self.assertEqual(name.getDebugName(2), 'Italic' if italic else 'Regular', style)
            self.assertEqual(name.getDebugName(16), 'SEIHouse Noto', style)
            self.assertEqual(name.getDebugName(17), style, style)
            self.assertEqual(font['OS/2'].usWeightClass, day['OS/2'].usWeightClass, style)
            self.assertEqual(bool(font['OS/2'].fsSelection & 0x01), italic, style)
            self.assertEqual(bool(font['OS/2'].fsSelection & 0x40), not italic, style)
            self.assertEqual(bool(font['head'].macStyle & 2), italic, style)
            self.assertEqual(font['post'].italicAngle, -10 if italic else 0, style)
            self.assertEqual(font['hhea'].caretSlopeRise, 1000 if italic else 1, style)
            self.assertEqual(font['hhea'].caretSlopeRun, 176 if italic else 0, style)
            self.assertEqual(font['hhea'].caretSlopeRise, day['hhea'].caretSlopeRise, style)
            self.assertEqual(font['hhea'].caretSlopeRun, day['hhea'].caretSlopeRun, style)

    def test_zero_reflow_metrics_and_shaping_parity(self):
        samples = (PROSE + [unicodedata.normalize('NFD', t) for t in PROSE]
                   + ['To', 'AV', 'Wa', 'Yo', 'fï', 'f”', 'nn', 'HH', 'Ångström', 'Zażółć',
                      'a\u0302\u0301', 'e\u0323\u0302\u0301', 'o\u031b\u0301', 'i\u0323\u0304', 'i\u0328\u0304', 'x\u0302\u0301\u0323'])
        pairs = ['nn', 'mm', 'uu', 'ii', 'aa', 'dd', 'hh', 'in', 'an', 'nj', 'ng', 'ay', 'af', 'nf', 'gf',
                 'yf', 'jf', 'ff', 'fï', 'f)', 'f”', 'To', 'Tö', 'AV', 'ïï', 'ââ', 'ďď', 'ťď', 'ĳs', 'ŉn']
        for style, font in self.fonts.items():
            day = self.days[style]
            day_style = style.removesuffix(' Night')
            for gname in day.getGlyphOrder():
                self.assertEqual(font['hmtx'][gname][0], day['hmtx'][gname][0], f'{style} {gname}')
            self.assertEqual(font.getTableData('GPOS'), day.getTableData('GPOS'), style)
            self.assertEqual(font.getTableData('GSUB'), day.getTableData('GSUB'), style)
            self.assertEqual(font.getTableData('GDEF'), day.getTableData('GDEF'), style)
            n_hb = hb.Font(hb.Face(hb.Blob((ROOT/'fonts'/f'{psname(style)}.otf').read_bytes())))
            d_hb = hb.Font(hb.Face(hb.Blob((ROOT/'fonts'/f'{psname(day_style)}.otf').read_bytes())))
            for text in samples:
                nb, db = hb.Buffer(), hb.Buffer()
                nb.add_str(text); nb.guess_segment_properties(); hb.shape(n_hb, nb)
                db.add_str(text); db.guess_segment_properties(); hb.shape(d_hb, db)
                self.assertEqual([(i.codepoint, p.x_advance, p.y_advance, p.x_offset, p.y_offset)
                                  for i, p in zip(nb.glyph_infos, nb.glyph_positions)],
                                 [(i.codepoint, p.x_advance, p.y_advance, p.x_offset, p.y_offset)
                                  for i, p in zip(db.glyph_infos, db.glyph_positions)],
                                 f'{style}: {text}')
            order = font.getGlyphOrder()
            for text in pairs:
                buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties(); hb.shape(n_hb, buf)
                a, b = (outline(font, order[info.codepoint]) for info in buf.glyph_infos)
                moved = b.transform(1, 0, 0, 1, buf.glyph_positions[0].x_advance, 0)
                overlap = pathops.op(a, moved, pathops.PathOp.INTERSECTION)
                self.assertEqual(len(list(overlap.contours)), 0, f'{style}: ink collision in {text}')


class OpticalSpacingTests(unittest.TestCase):
    """The eye-reviewed optical pass on top of the automatic kerning (optical.py)."""

    STYLES = STYLES + ITALICS

    @staticmethod
    def kern(style, text):
        hbfont = hb.Font(hb.Face((ROOT/'fonts'/f'{psname(style)}.otf').read_bytes()))
        widths = []
        for feature in (True, False):
            buffer = hb.Buffer()
            buffer.add_str(text)
            buffer.guess_segment_properties()
            hb.shape(hbfont, buffer, {'kern': feature})
            widths.append(sum(p.x_advance for p in buffer.glyph_positions))
        return widths[0] - widths[1]

    def test_w_follows_v_with_lowercase(self):
        for style in self.STYLES:
            for letter in 'aeo':
                w, v = self.kern(style, 'W'+letter), self.kern(style, 'V'+letter)
                self.assertLessEqual(w, round(.75*v) + 1, f'{style} W{letter} {w} vs V{letter} {v}')

    def test_f_terminal_gets_air_but_ff_keeps_its_crossbar(self):
        for style in ['Italic', 'Medium Italic', 'Bold Italic', 'Medium', 'Bold']:
            self.assertGreater(self.kern(style, 'fi'), 0, style)
            self.assertGreater(self.kern(style, 'fl'), 0, style)
        for style in self.STYLES:
            self.assertEqual(self.kern(style, 'ff'), 0, style)
            # The air is a polish, never a gap: at most 0.16 of the heaviest stem.
            self.assertLessEqual(self.kern(style, 'fi'), 22, style)

    def test_tucked_descenders_are_closer_but_clear(self):
        expected = {'Regular': 0, 'Italic': 0, 'Medium': 14, 'Bold': 24, 'Medium Italic': 20, 'Bold Italic': 27}
        for style, value in expected.items():
            self.assertAlmostEqual(self.kern(style, 'gj'), value, delta=2, msg=style)
        for style in self.STYLES:
            self.assertEqual(self.kern(style, 'jj'), 0, style)
            self.assertLess(self.kern(style, 'gj'), 45, style)
            # Ink still clears: the italic and upright collision gates check gj, nj and ng.

    def test_reviewed_pairs_are_unchanged(self):
        """T and Y read evenly before the pass, and punctuation is outside it."""
        sys.path.insert(0, str(ROOT))
        import letters
        import spacing
        source, groups, ghosts = letters.draw(1.0, italic=True)
        measured = spacing.kerning(source, groups, ghosts=ghosts, optical_pass=False)
        optical = spacing.kerning(source, groups, ghosts=ghosts)
        changed = {k for k in set(measured[0]) | set(optical[0]) if measured[0].get(k) != optical[0].get(k)}
        self.assertTrue(changed)
        for a, b in changed:
            self.assertTrue(a in 'Wfſ' or (a.isalpha() and b.isalpha()), f'{a}{b} changed')
            self.assertNotIn(a, 'TY', f'{a}{b} changed')
        self.assertLess(len(changed), 250)


class CombiningMarkTests(unittest.TestCase):
    """Combining marks, attachment anchors, mark-to-mark stacking and NFC/NFD parity across all 14 faces."""

    ALL_STYLES = STYLES + ITALICS + NIGHTS
    MARKS = (0x300, 0x301, 0x302, 0x303, 0x304, 0x306, 0x307, 0x308, 0x309, 0x30A,
             0x30B, 0x30C, 0x312, 0x31B, 0x323, 0x326, 0x327, 0x328, 0x331)

    @classmethod
    def setUpClass(cls):
        cls.fonts, cls.hbfonts, cls.orders = {}, {}, {}
        for style in cls.ALL_STYLES:
            path = ROOT/'fonts'/f'{psname(style)}.otf'
            font = TTFont(path)
            cls.addClassCleanup(font.close)
            cls.fonts[style] = font
            cls.hbfonts[style] = hb.Font(hb.Face(path.read_bytes()))
            cls.orders[style] = font.getGlyphOrder()

    def shape(self, style, text, language=None, **features):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        if language:
            buf.language = language
        hb.shape(self.hbfonts[style], buf, features)
        order = self.orders[style]
        return [(order[i.codepoint], p.x_advance, p.x_offset, p.y_offset)
                for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

    def positioned_ink(self, style, text):
        font = self.fonts[style]
        x = 0
        ink = []
        for gname, adv, dx, dy in self.shape(style, text):
            ink.append((gname, outline(font, gname).transform(1, 0, 0, 1, x+dx, dy)))
            x += adv
        return ink

    def test_mark_repertoire_zero_advance_gdef_and_stat(self):
        for style in self.ALL_STYLES:
            font = self.fonts[style]
            cmap = font.getBestCmap()
            gdef = font['GDEF'].table.GlyphClassDef.classDefs
            self.assertIn(0x25CC, cmap, f'{style} missing dotted circle')
            self.assertIn('u012F.dotless', font.getGlyphOrder(), f'{style} missing u012F.dotless')
            self.assertEqual(gdef['u012F.dotless'], 1, style)
            self.assertEqual(gdef[cmap[0x25CC]], 1, style)
            for code in self.MARKS:
                self.assertIn(code, cmap, f'{style} missing U+{code:04X}')
                gname = cmap[code]
                self.assertEqual(font['hmtx'][gname][0], 0, f'{style} U+{code:04X} nonzero advance')
                self.assertEqual(gdef[gname], 3, f'{style} U+{code:04X} GDEF class')
            for tag, required in (('GSUB', {'ccmp', 'locl'}), ('GPOS', {'mark', 'mkmk', 'kern'})):
                tags = {r.FeatureTag for r in font[tag].table.FeatureList.FeatureRecord}
                self.assertTrue(required <= tags, f'{style} {tag} missing {required - tags}')
            self.assertIn('STAT', font, style)

    def test_precomposed_and_decomposed_text_shape_identically(self):
        extra = ['Tö', 'Vé', 'Wá', 'fï', 'Zażółć gęślą jaźń.', 'Příliš žluťoučký kůň.',
                 'ģķļņŗ ĢĶĻŅŖ', 'ďťľĽ ĎŤŇŘŠČŽ', 'ÂÃÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝ',
                 'Ẁ ẁ Ẃ ẃ Ẅ ẅ Ỳ ỳ Ș ș Ț ț']
        for style in self.ALL_STYLES:
            cmap = self.fonts[style].getBestCmap()
            for code in cmap:
                ch = chr(code)
                nfd = unicodedata.normalize('NFD', ch)
                if nfd != ch:
                    self.assertEqual(self.shape(style, ch), self.shape(style, nfd), f'{style} U+{code:04X}')
            for text in PROSE + extra:
                self.assertEqual(self.shape(style, text),
                                 self.shape(style, unicodedata.normalize('NFD', text)),
                                 f'{style}: {text}')
            self.assertEqual(self.shape(style, 'g\u0312'), self.shape(style, 'ģ'), style)
            self.assertEqual(self.shape(style, '\u0131\u0301'), self.shape(style, 'í'), style)
            self.assertEqual(self.shape(style, '\u0237\u0302'), self.shape(style, 'ĵ'), style)
            for old, new in zip('ŞşŢţ', 'ȘșȚț'):
                expected = self.shape(style, new, language='ro')
                self.assertEqual(self.shape(style, old, language='ro'), expected, f'{style} {old}')
                self.assertEqual(self.shape(style, unicodedata.normalize('NFD', old), language='ro'),
                                 expected, f'{style} NFD {old}')

    def test_base_attachment_dotless_substitution_mark_stacking_and_kerning(self):
        single = ['x\u0301', 'n\u0304', 'm\u0300', 'g\u0303', 'x\u0323', 'b\u0331', 'b\u0307', 'd\u0307',
                  't\u0308', 'f\u0307', 'y\u0323', 'g\u0323', 'p\u0323', 'M\u0301', 'V\u0303',
                  'o\u031b', 'u\u031b', 'O\u031b', 'U\u031b', 'o\u0328', 'æ\u0301', 'ø\u0301']
        isolated = [f'\u25cc{chr(c)}' for c in self.MARKS]
        stacks = ['x\u0302\u0301', 'x\u0306\u0300', 'x\u0308\u0304', 'x\u0302\u0301\u0323', 'x\u0323\u0331',
                  'X\u0302\u0301', 'a\u0302\u0301', 'ấ', 'e\u0323\u0302\u0301', 'ệ', 'o\u031b\u0301', 'ớ',
                  'u\u031b\u0323', 'ự', 'u\u0308\u030c', 'ǚ', 'A\u0302\u0301', 'Ấ', '\u25cc\u0302\u0301']
        non_connecting = ['x\u0301', 'n\u0304', 'm\u0300', 'g\u0303', 'x\u0323', 'b\u0331', 'b\u0307', 'd\u0307',
                          't\u0308', 'f\u0307', 'y\u0323', 'g\u0323', 'p\u0323', 'M\u0301', 'V\u0303',
                          'i\u0309', 'j\u0301', 'i\u0323\u0309', 'j\u0323\u0301', 'į\u0304', 'i\u0328\u0304',
                          'x\u0302\u0301', 'x\u0306\u0300', 'x\u0308\u0304', 'x\u0302\u0301\u0323',
                          'x\u0323\u0331', 'X\u0302\u0301', 'a\u0302\u0301', 'e\u0323\u0302\u0301',
                          'u\u0308\u030c', 'A\u0302\u0301', '\u25cc\u0301', '\u25cc\u0309', '\u25cc\u0323',
                          '\u25cc\u0302\u0301']
        for style in self.ALL_STYLES:
            font = self.fonts[style]
            gdef = font['GDEF'].table.GlyphClassDef.classDefs
            win_ascent, win_descent = font['OS/2'].usWinAscent, font['OS/2'].usWinDescent
            for text in single + isolated + stacks:
                shaped = self.shape(style, text)
                self.assertTrue(all(g != '.notdef' for g, _, _, _ in shaped), f'{style}: {text}')
                self.assertTrue(all(adv == 0 for g, adv, _, _ in shaped if gdef.get(g) == 3), f'{style}: {text}')
                for gname, path in self.positioned_ink(style, text):
                    _, y0, _, y1 = path.bounds
                    self.assertGreaterEqual(y0, -win_descent, f'{style} {text} {gname}')
                    self.assertLessEqual(y1, win_ascent, f'{style} {text} {gname}')
            self.assertNotEqual(self.shape(style, 'x\u0301'), self.shape(style, 'x\u0301', mark=False), style)
            for cl in ('x\u0302\u0301', 'x\u0323\u0331', '\u25cc\u0302\u0301'):
                self.assertNotEqual(self.shape(style, cl), self.shape(style, cl, mkmk=False), f'{style} {cl}')
            # Dotless substitution and canonical order equivalence.
            for text, dotless_name in [('i\u0309', 'u0131'), ('i\u0307', 'u0131'), ('j\u0301', 'u0237'),
                                       ('j\u030c', 'u0237'), ('i\u0323\u0309', 'u0131'), ('j\u0323\u0301', 'u0237'),
                                       ('į\u0304', 'u012F.dotless'), ('i\u0328\u0304', 'u012F.dotless')]:
                shaped = self.shape(style, text)
                self.assertEqual(shaped[0][0], dotless_name, f'{style} {text}')
            self.assertEqual(self.shape(style, 'i\u0323\u0309'), self.shape(style, 'i\u0309\u0323'), style)
            self.assertEqual(self.shape(style, 'j\u0323\u0301'), self.shape(style, 'j\u0301\u0323'), style)
            self.assertEqual(self.shape(style, 'į\u0304'), self.shape(style, 'i\u0328\u0304'), style)
            # No contour overlap between base and marks or between stacked marks.
            for text in non_connecting:
                ink = self.positioned_ink(style, text)
                for i, (_, pa) in enumerate(ink):
                    for _, pb in ink[i+1:]:
                        ov = pathops.op(pa, pb, pathops.PathOp.INTERSECTION)
                        self.assertLess(abs(ov.area), 0.01, f'{style} overlap in {text!r}: {ov.area}')
            # Kerning remains active across combining marks.
            for marked, plain in [('Tx\u0301', 'Tx'), ('Wa\u0323', 'Wa'), ('T\u0323o', 'To'), ('nx\u0301a', 'nxa')]:
                w_marked = sum(a for _, a, _, _ in self.shape(style, marked))
                w_plain = sum(a for _, a, _, _ in self.shape(style, plain))
                self.assertEqual(w_marked, w_plain, f'{style} {marked}')
            self.assertLess(sum(a for _, a, _, _ in self.shape(style, 'Wa\u0323')),
                            sum(a for _, a, _, _ in self.shape(style, 'Wa\u0323', kern=False)), style)


def _box(x0, y0, x1, y1):
    path = pathops.Path()
    pen = path.getPen()
    pen.moveTo((x0, y0)); pen.lineTo((x1, y0)); pen.lineTo((x1, y1)); pen.lineTo((x0, y1)); pen.closePath()
    return path


if __name__ == '__main__':
    unittest.main()
