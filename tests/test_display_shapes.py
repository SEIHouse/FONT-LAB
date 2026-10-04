"""Construction regressions: adversarial debris, attached caps and acute joins."""
import math
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import pathops

from font_builder import FontBuilderCore, SC
from display.outline_cleanup import cleanup
from display.shape_geometry import contours, length
from verify_display_shapes import flags

builder = FontBuilderCore(json.loads((Path(__file__).resolve().parents[1] /
    'display/cuts/soft.json').read_text(encoding='utf-8')), display=True)


def polygon(points):
    """Create an independent filled fixture in native font units."""
    path = pathops.Path(); pen = path.getPen()
    pen.moveTo(points[0])
    for point in points[1:]: pen.lineTo(point)
    pen.closePath()
    return path


class OutlineCleanupTests(unittest.TestCase):
    def test_spur_and_notch_are_removed_at_their_roots(self):
        for y in (470, 530):
            with self.subTest(y=y):
                dirty = polygon([(0,0),(500,0),(500,500),(300,500),
                                 (290,y),(280,500),(0,500)])
                self.assertTrue(flags(dirty), 'Verifier must reject the original defect')
                clean = cleanup(dirty)
                self.assertEqual(flags(clean), [])
                self.assertAlmostEqual(abs(clean.area), 250000, delta=1)
                self.assertEqual(clean.bounds, (0,0,500,500))

    def test_needle_is_removed_without_rounding_the_letter_corners(self):
        dirty = polygon([(0,0),(500,0),(500,500),(301,500),
                         (300,525),(299,500),(0,500)])
        self.assertTrue(any('spike' in flag['kind'] for flag in flags(dirty)))
        clean = cleanup(dirty)
        self.assertEqual(flags(clean), [])
        self.assertEqual(clean.bounds, (0,0,500,500))

    def test_micro_contour_removed_but_visible_dot_and_counter_survive(self):
        dirty = polygon([(0,0),(500,0),(500,500),(0,500)])
        hole = polygon([(100,100),(100,400),(400,400),(400,100)])
        dot = builder.circle(300, 50, 4, 0)
        micro = polygon([(700,700),(701,700),(701,701),(700,701)])
        dirty.addPath(hole); dirty.addPath(dot); dirty.addPath(micro)
        clean = cleanup(dirty)
        self.assertEqual(flags(clean), [])
        self.assertEqual(len(list(clean.contours)), 3)
        self.assertFalse(clean.contains((250,250)))
        self.assertTrue(clean.contains((600,-100)))
        self.assertFalse(clean.contains((700.5,700.5)))

    def test_near_duplicate_points_collapsed(self):
        dirty = polygon([(0,0),(1,0),(500,0),(500,500),(0,500)])
        self.assertTrue(any(flag['kind'] == 'tiny-segment' for flag in flags(dirty)))
        clean = cleanup(dirty)
        self.assertEqual(flags(clean), [])
        self.assertEqual(len(contours(clean)[0]), 4)
        self.assertTrue(all(length(segment) > 400 for segment in contours(clean)[0]))

    def test_duplicate_winding_and_self_overlap_resolved(self):
        dirty = polygon([(0,0),(500,0),(500,500),(0,500)])
        dirty.addPath(polygon([(0,0),(500,0),(500,500),(0,500)]))
        self.assertTrue(any(flag['kind'] == 'self-overlap' for flag in flags(dirty)))
        clean = cleanup(dirty)
        self.assertEqual(flags(clean), [])
        self.assertAlmostEqual(abs(clean.area), 250000)

    def test_full_size_symbol_tip_survives(self):
        triangle = polygon([(0,0),(600,0),(300,900)])
        clean = cleanup(triangle)
        self.assertEqual(clean.bounds, triangle.bounds)
        self.assertAlmostEqual(abs(clean.area), abs(triangle.area))
        self.assertEqual(flags(clean), [])


class StrokeConstructionTests(unittest.TestCase):
    def test_neutral_options_preserve_reader_construction_and_italic_angle(self):
        settings = json.loads((Path(__file__).resolve().parents[1]/'settings.json').read_text(encoding='utf-8'))
        settings.update(corners='soft', ends='round', joins='round', penAngle=0, slant=0)
        core = FontBuilderCore(settings)
        self.assertFalse(core.configured_shapes)
        self.assertEqual(core.SLANT, settings['italicAngle'])

    def test_reader_display_options_keep_upright_strokes_unsheared(self):
        settings = json.loads((Path(__file__).resolve().parents[1]/'settings.json').read_text(encoding='utf-8'))
        settings['ends'] = 'flat'
        core = FontBuilderCore(settings)
        self.assertFalse(core.PRESERVE_RHYTHM, 'changed outlines must remeasure pairs')
        shape = core.outline(dict(paths=[dict(d='M0 0L0 700',w=85)], circles=[]), 0)
        self.assertAlmostEqual(shape.bounds[0], -85, delta=.01)
        self.assertAlmostEqual(shape.bounds[2], 85, delta=.01)

    def test_angled_pen_caps_perpendicular_after_oblique_shear(self):
        shear = math.tan(math.radians(8))
        with patch.multiple(builder, F=2.6, PEN=32, TAN=shear, CAP_FLAT=True):
            for degrees in (0, 30, 75, 90, 145):
                angle = math.radians(degrees)
                end = (500*math.cos(angle), 500*math.sin(angle))
                path = builder.configured_stroke([('M',(0,0)),('L',end)], 0, 135)
                final = path.transform(skewX=shear)
                tx,ty = end[0]-shear*end[1], -end[1]
                norm = math.hypot(tx,ty); tx,ty = tx/norm,ty/norm
                faces = []
                for segments in contours(final):
                    for segment in segments:
                        if segment[1] != 'lineTo': continue
                        a,b = segment[0],segment[-1]
                        vx,vy = b[0]-a[0],b[1]-a[1]
                        if math.hypot(vx,vy) > 20 and abs(vx*tx+vy*ty) < .002:
                            faces.append(segment)
                self.assertEqual(len(faces), 2, (degrees, 'two flat perpendicular faces required'))

    def test_attached_branch_does_not_extend_left_of_parent_stem(self):
        with patch.multiple(builder, F=1, PEN=0, TAN=0, SLANT=0, CAP_FLAT=True, JOIN_SHARP=True):
            shape = builder.outline(dict(paths=[dict(d='M0 0L0 700',w=115),
                dict(d='M470 700L0 215',w=115)], circles=[]), 0)
            region = polygon([(-300,-650),(-115,-650),(-115,-200),(-300,-200)])
            extra = pathops.op(shape, region, pathops.PathOp.INTERSECTION)
            self.assertLess(abs(extra.area), .01, 'K attachment must not grow a square-cap beak')

    def test_coincident_terminals_fill_outer_join_without_notch(self):
        with patch.multiple(builder, F=1, PEN=0, TAN=0, SLANT=0, CAP_FLAT=True, JOIN_SHARP=True):
            shape = builder.outline(dict(paths=[dict(d='M0 700L0 0',w=115),
                dict(d='M0 0L400 0',w=115)], circles=[]), 0)
            self.assertTrue(shape.contains((-100,100)), 'outside corner of joined L must be filled')
            self.assertEqual(flags(shape), [])

    def test_acute_miter_falls_back_to_bounded_bevel(self):
        with patch.multiple(builder, F=1, PEN=0, TAN=0, CAP_FLAT=False, JOIN_SHARP=True):
            path = builder.configured_stroke([('M',(-100,700)),('L',(0,0)),('L',(100,700))], 0, 115)
            self.assertLessEqual(path.bounds[3], 115*SC, 'no long miter needle')
            self.assertEqual(flags(cleanup(path)), [])


if __name__ == '__main__':
    unittest.main()
