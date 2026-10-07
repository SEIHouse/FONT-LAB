"""Reject stale files in the private runtime's broad dist delivery scope."""
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from display import build_living_package


class LivingPackageBuildTests(unittest.TestCase):
    def test_rebuild_removes_obsolete_runtime_and_font_files(self):
        """Deleted source and font files must disappear from output and provenance."""
        (build_living_package.ROOT/'dist').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=build_living_package.ROOT/'dist') as temporary:
            package=Path(temporary)/'package'
            shutil.copytree(build_living_package.PACKAGE/'src',package/'src')
            out=package/'dist'
            (out/'fonts').mkdir(parents=True)
            (out/'obsolete.js').write_text('obsolete',encoding='utf-8')
            (out/'fonts/obsolete.woff2').write_bytes(b'obsolete')
            with patch.object(build_living_package,'PACKAGE',package):
                build_living_package.build()
            self.assertFalse((out/'obsolete.js').exists())
            self.assertFalse((out/'fonts/obsolete.woff2').exists())
            self.assertNotIn('obsolete',(out/'provenance.json').read_text(encoding='utf-8'))
            self.assertEqual(len(list((out/'fonts').glob('*.woff2'))),4)


if __name__=='__main__':
    unittest.main()
