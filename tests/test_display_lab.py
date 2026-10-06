"""The phone layout gate must reject wide pages and individual leaking elements."""
import unittest
from unittest.mock import MagicMock, patch

from display.verify_lab import layout_flags, verify_mobile


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

    def test_crossed_w_preset_is_reported_even_under_python_optimization(self):
        page = MagicMock()
        page.locator.return_value.input_value.return_value = 'crossed'
        with patch('display.verify_lab.layout_snapshot', return_value=dict(
                viewport=390, document=390, body=390, outside=[])):
            result = verify_mobile(page, MagicMock())
        self.assertEqual(len(result['flags']), 20)
        self.assertEqual({flag['kind'] for flag in result['flags']}, {'lab-w-default'})


if __name__ == '__main__':
    unittest.main()
