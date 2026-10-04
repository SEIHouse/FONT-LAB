"""Quadratic pen protocol regressions, including implied closed-loop points."""
from types import SimpleNamespace
import unittest

import pathops
from fontTools.pens.recordingPen import RecordingPen

from display.outline_cleanup import cleanup, split
from display.shape_geometry import contours, from_contours, sample


def grouped_fixture(*commands):
    """Keep the grouped pen commands visible without depending on pathops grouping."""
    return SimpleNamespace(contours=[SimpleNamespace(segments=commands)])


def rounded_square():
    """Four explicit independent quadratics bound a smooth closed 800-unit loop."""
    path = pathops.Path()
    path.moveTo(0, 400)
    path.quadTo(0, 0, 400, 0)
    path.quadTo(800, 0, 800, 400)
    path.quadTo(800, 800, 400, 800)
    path.quadTo(0, 800, 0, 400)
    path.close()
    return path


class QuadraticGeometryTests(unittest.TestCase):
    def test_grouped_controls_sample_as_two_quadratics(self):
        path = grouped_fixture(('moveTo', ((0, 0),)),
            ('qCurveTo', ((200, 200), (400, 200), (600, 0))), ('endPath', ()))
        segments = contours(path)[0]
        self.assertEqual(len(segments), 2)
        self.assertEqual(sample(segments[0], .5), (175, 150))
        self.assertEqual(sample(segments[1], .5), (425, 150))
        self.assertEqual(segments[0][-1], (300, 200))
        self.assertEqual(segments[1][0], (300, 200))
        self.assertEqual(segments[1][-1], (600, 0))
        # Cleanup's split must remain a quadratic, with exact subdivision samples.
        left, right = split(segments[0], .5)
        self.assertEqual(sample(left, .5), sample(segments[0], .25))
        self.assertEqual(sample(right, .5), sample(segments[0], .75))
        self.assertEqual(len(left), 4)
        self.assertEqual(len(right), 4)

    def test_single_quadratic_keeps_control_and_endpoint(self):
        path = grouped_fixture(('moveTo', ((10, 20),)),
            ('qCurveTo', ((110, 220), (210, 20))), ('endPath', ()))
        segments = contours(path)[0]
        self.assertEqual(segments, [[(10, 20), 'qCurveTo', (110, 220), (210, 20)]])
        self.assertEqual(sample(segments[0], .5), (110, 120))

    def test_quadratic_without_control_is_a_line(self):
        path = grouped_fixture(('moveTo', ((0, 0),)),
            ('qCurveTo', ((200, 100),)), ('endPath', ()))
        segment = contours(path)[0][0]
        self.assertEqual(segment[1], 'lineTo')
        self.assertEqual(sample(segment, .5), (100, 50))

    def test_none_endpoint_starts_at_implied_loop_midpoint(self):
        path = grouped_fixture(('qCurveTo', ((0, 0), (800, 0), (800, 800), (0, 800), None)),
                               ('closePath', ()))
        segments = contours(path)[0]
        self.assertEqual(len(segments), 4)
        self.assertEqual(segments[0][0], (0, 400))
        self.assertEqual(segments[-1][-1], (0, 400))
        self.assertEqual([sample(segment, .5) for segment in segments],
                         [(100, 100), (700, 100), (700, 700), (100, 700)])
        rebuilt = from_contours([segments])
        expected = rounded_square()
        self.assertEqual(rebuilt.bounds, expected.bounds)
        self.assertAlmostEqual(rebuilt.area, expected.area, delta=.01)
        self.assertLess(abs(pathops.op(rebuilt, expected, pathops.PathOp.XOR).area), .01)

    def test_actual_pathops_grouped_contour_preserves_ink_through_cleanup(self):
        native = pathops.Path()
        native.getPen().qCurveTo((0, 0), (800, 0), (800, 800), (0, 800), None)
        native.getPen().closePath()
        recording = RecordingPen()
        native.draw(recording)
        self.assertTrue(any(verb == 'qCurveTo' and len(points) > 2
                            for verb, points in recording.value),
                        'Fixture must exercise the real grouped quadratic pen protocol')
        clean = cleanup(native)
        expected = rounded_square()
        self.assertEqual(clean.bounds, (0, 0, 800, 800))
        self.assertAlmostEqual(clean.area, expected.area, delta=.01)
        self.assertLess(abs(pathops.op(clean, expected, pathops.PathOp.XOR).area), .01)
        self.assertTrue(clean.contains((400, 400)))
        self.assertFalse(clean.contains((10, 10)))


if __name__ == '__main__':
    unittest.main()
