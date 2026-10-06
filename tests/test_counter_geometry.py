"""Counter/aperture failures must be measured independently of spike cleanup."""
import unittest
from pathlib import Path

import freetype

from display.counter_geometry import counter_flags, topology_flags, topology_snapshot
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

    def test_filled_counter_cannot_disappear_from_gate(self):
        filled = bitmap(['#'*50]*40)
        self.assertEqual(counter_flags(filled), [])
        expected = dict(closed_counters=1, white_spaces=[[25, 20, False]])
        failures = topology_flags(filled, expected)
        self.assertEqual({flag['kind'] for flag in failures}, {'counter-topology', 'filled-counter'})

    def test_sealed_roomy_aperture_cannot_pass_as_a_counter(self):
        sealed = bitmap(['#'*50]*10 + ['#'*5+'.'*40+'#'*5]*20 + ['#'*50]*10)
        self.assertEqual(counter_flags(sealed), [])
        expected = dict(closed_counters=0, white_spaces=[[25, 20, True]])
        failures = topology_flags(sealed, expected)
        self.assertEqual({flag['kind'] for flag in failures}, {'counter-topology', 'sealed-aperture'})

    def test_filled_aperture_cannot_disappear_from_gate(self):
        expected = dict(closed_counters=0, white_spaces=[[25, 20, True]])
        self.assertEqual(topology_flags(bitmap(['#'*50]*40), expected)[0]['kind'], 'filled-aperture')

    def test_reviewed_snapshot_records_closed_and_open_interiors(self):
        rows = ['#'*50]*10 + ['#'*5+'.'*40+'#'*5]*20 + ['#'*50]*10
        closed = topology_snapshot(bitmap(rows))
        self.assertEqual(closed['closed_counters'], 1)
        self.assertEqual(len(closed['white_spaces']), 1)
        self.assertFalse(closed['white_spaces'][0][2])
        rows[:10] = ['#'*20+'.'*10+'#'*20]*10
        opened = topology_snapshot(bitmap(rows))
        self.assertEqual(opened['closed_counters'], 0)
        self.assertEqual(len(opened['white_spaces']), 1)
        self.assertTrue(opened['white_spaces'][0][2])

    def test_white_witnesses_use_glyph_coordinates_not_raster_bounds(self):
        rows = ['#'*20+'.'*10+'#'*20]*10 + ['#'*5+'.'*40+'#'*5]*20 + ['#'*50]*10
        expected = dict(closed_counters=0, white_spaces=[[25, 20, True]])
        self.assertEqual(topology_flags(bitmap(rows), expected), [])
        padded = bitmap(['.'*60]*3 + ['.'*5+row+'.'*5 for row in rows] + ['.'*60]*2)
        padded.update(left=-5, top=43)
        self.assertEqual(topology_flags(padded, expected), [])


if __name__ == '__main__':
    unittest.main()
