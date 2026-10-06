"""Counter/aperture failures must be measured independently of spike cleanup."""
import unittest
from pathlib import Path

import freetype

from display.counter_geometry import counter_flags
from verify_display_shapes import render

ROOT = Path(__file__).resolve().parents[1]


def bitmap(rows):
    return dict(width=len(rows[0]), height=len(rows),
                pixels=bytes(255 if char == '#' else 0 for row in rows for char in row))


class CounterGeometryTests(unittest.TestCase):
    def test_frozen_reported_a_reproduces_the_missing_gate(self):
        # Immutable subset of the shipped Step 2 font: no geometry regeneration.
        face = freetype.Face(str(ROOT/'tests/fixtures/display-soft-counters-before.otf'))
        failures = counter_flags(render(face, face.get_char_index(ord('a'))))
        self.assertTrue(any(flag['kind'] == 'narrow-counter' for flag in failures))

    def test_shipped_a_family_and_other_stacked_bowls_have_room(self):
        for cut in ('soft', 'edge', 'ink', 'wide'):
            face = freetype.Face(str(ROOT/f'display/fonts/{cut}/SEIHouseDisplay-{cut.title()}.otf'))
            for char in 'Aaàáâãäåāăąạảấầẩẫậắằẳẵặаæegεs8':
                index = face.get_char_index(ord(char))
                self.assertGreater(index, 0, (cut, char, 'missing glyph'))
                self.assertEqual(counter_flags(render(face, index)), [], (cut, char))

    def test_long_thin_enclosed_counter_fails(self):
        rows = ['#'*50]*10 + ['#'*5+'.'*40+'#'*5]*2 + ['#'*50]*10
        self.assertTrue(any(flag['kind'] == 'narrow-counter' for flag in counter_flags(bitmap(rows))))

    def test_open_basin_with_pinched_entrance_fails(self):
        rows = ['#'*24+'.'*2+'#'*24]*10 + ['#'*5+'.'*40+'#'*5]*20 + ['#'*50]*10
        self.assertTrue(any(flag['kind'] == 'narrow-aperture' for flag in counter_flags(bitmap(rows))))

    def test_roomy_counter_and_open_basin_pass(self):
        rows = ['#'*50]*10 + ['#'*5+'.'*40+'#'*5]*20 + ['#'*50]*10
        self.assertEqual(counter_flags(bitmap(rows)), [])
        rows[:10] = ['#'*20+'.'*10+'#'*20]*10
        self.assertEqual(counter_flags(bitmap(rows)), [])

    def test_small_detail_is_not_a_full_letter_counter(self):
        rows = ['#'*50]*10 + ['#'*20+'.'*10+'#'*20]*2 + ['#'*50]*10
        self.assertEqual(counter_flags(bitmap(rows)), [])

    def test_symbol_gap_still_checks_enclosed_counters(self):
        rows = ['#'*24+'.'*2+'#'*24]*10 + ['#'*5+'.'*40+'#'*5]*20 + ['#'*50]*10
        self.assertEqual(counter_flags(bitmap(rows), apertures=False), [])
        rows[:10] = ['#'*50]*10
        rows[10:30] = ['#'*5+'.'*40+'#'*5]*2
        self.assertTrue(any(flag['kind'] == 'narrow-counter' for flag in
                            counter_flags(bitmap(rows), apertures=False)))


if __name__ == '__main__':
    unittest.main()
