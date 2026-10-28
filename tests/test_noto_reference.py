"""Reference provenance must reject cached or downloaded bytes that were changed."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    'noto_study', Path(__file__).resolve().parents[1] / 'noto/studies/warmth/build_samples.py')
study = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(study)


class ReferenceTests(unittest.TestCase):
    def test_reference_cache_and_download_validation(self):
        expected = b'pinned reference bytes'
        digest = hashlib.sha256(expected).hexdigest()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(study, 'ROOT', root), patch.object(
                study, 'REFERENCE_FILES', [('test.ttf', 'test.ttf', digest)]
            ), patch.object(study.urllib.request, 'urlopen') as fetch:
                fetch.return_value = io.BytesIO(expected)
                study.fetch_reference()
                target = root / 'reference/test.ttf'
                self.assertEqual(target.read_bytes(), expected)
                fetch.reset_mock()
                study.fetch_reference()
                fetch.assert_not_called()
                target.write_bytes(b'tampered cache')
                fetch.return_value = io.BytesIO(expected)
                study.fetch_reference()
                self.assertEqual(target.read_bytes(), expected)
                self.assertEqual(json.loads((root / 'reference/provenance.json').read_text())[0]['sha256'], digest)
                target.write_bytes(b'tampered again')
                fetch.return_value = io.BytesIO(b'unexpected download')
                with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                    study.fetch_reference()
                self.assertEqual(target.read_bytes(), b'tampered again')


if __name__ == '__main__':
    unittest.main()
