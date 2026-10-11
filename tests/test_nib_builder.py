"""The builder's flat nib must produce the exact swept shapes the Lab draws."""
import json
import math
from pathlib import Path
import unittest

from font_builder import SC, FontBuilderCore, nib_split

ROOT = Path(__file__).resolve().parents[1]


def builder(**changes):
    """A Display builder for Ink with only the given settings changed."""
    settings = json.loads((ROOT/'display/cuts/ink.json').read_text(encoding='utf-8')) | changes
    return FontBuilderCore(settings, display=True)


def area(path):
    return sum(abs(contour.area) for contour in path.contours)


class NibBuilderTests(unittest.TestCase):
    def test_sharp_nib_sweeps_a_stem_into_its_exact_rectangle(self):
        core = builder(pen='nib', ends='flat', contrast=4, penAngle=0)
        length, thick, round_, c, s = core.nib_shape(100)
        path = core.nib_stroke(core.parse('M0 0L0 -700'), 0, 100)
        expected = (-length/2*SC, -thick/2*SC, length/2*SC, (700+thick/2)*SC)
        for value, edge in zip(path.bounds, expected):
            self.assertAlmostEqual(value, edge, places=3)
        self.assertAlmostEqual(area(path), length*(700+thick)*SC*SC, delta=1)

    def test_a_stroke_along_the_nib_is_a_hairline_of_the_nib_thickness(self):
        core = builder(pen='nib', ends='flat', contrast=5, penAngle=45)
        length, thick, *_ = core.nib_shape(100)
        side = 300/math.sqrt(2)
        path = core.nib_stroke(core.parse(f'M0 0L{side} -{side}'), 0, 100)
        self.assertAlmostEqual(area(path), (300+length)*thick*SC*SC, delta=SC*SC)

    def test_soft_nib_grows_the_sweep_by_half_its_thickness(self):
        core = builder(pen='nib', ends='round', contrast=4, penAngle=0)
        length, thick, *_ = core.nib_shape(100)
        path = core.nib_stroke(core.parse('M0 0L0 -700'), 0, 100)
        expected = (-length/2*SC, -thick/2*SC, length/2*SC, (700+thick/2)*SC)
        for value, edge in zip(path.bounds, expected):
            self.assertAlmostEqual(value, edge, delta=.05*SC)

    def test_python_and_lab_split_curves_at_the_same_point(self):
        pieces = nib_split(((0, 0), (55, 0), (100, 45), (100, 100)), (1, 1))
        self.assertEqual(len(pieces), 2)
        joint, control = pieces[0][3], pieces[0][2]
        self.assertAlmostEqual(joint[0]-control[0], joint[1]-control[1], places=9)

    def test_oval_cuts_do_not_use_the_nib(self):
        self.assertFalse(builder().NIB)
        # The Reader never draws with the nib, even if a setting asks for it.
        reader = json.loads((ROOT/'display/cuts/ink.json').read_text(encoding='utf-8')) | {'pen': 'nib', 'family': 'SEIHouse Sans'}
        self.assertFalse(FontBuilderCore(reader).NIB)
        self.assertTrue(builder(pen='nib').NIB)


if __name__ == '__main__':
    unittest.main()
