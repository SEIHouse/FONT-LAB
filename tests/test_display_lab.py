"""The phone layout gate must reject wide pages and individual leaking elements."""
import unittest

from display.verify_lab import layout_flags


class DisplayMobileTests(unittest.TestCase):
    def test_viewport_sized_layout_passes(self):
        self.assertEqual(layout_flags(dict(viewport=390, document=390, body=390, outside=[])), [])

    def test_reported_580px_phone_overflow_fails(self):
        failures = layout_flags(dict(viewport=390, document=580, body=580, outside=[]))
        self.assertEqual(failures[0]['kind'], 'mobile-document-overflow')

    def test_clipped_or_negative_element_overflow_still_fails(self):
        failures = layout_flags(dict(viewport=390, document=390, body=390,
                                    outside=[dict(tag='svg', left=-20, right=380, width=400)]))
        self.assertEqual(failures[0]['kind'], 'mobile-element-overflow')


if __name__ == '__main__':
    unittest.main()
