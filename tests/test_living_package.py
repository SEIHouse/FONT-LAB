"""Reject stale files in the private runtime's broad dist delivery scope."""
from pathlib import Path
import os
import shutil
import subprocess
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

    def test_linked_font_directory_cannot_redirect_writes(self):
        """A linked font directory must fail before any cleanup or external writes."""
        (build_living_package.ROOT/'dist').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=build_living_package.ROOT/'dist') as temporary:
            directory=Path(temporary)
            package=directory/'package'
            shutil.copytree(build_living_package.PACKAGE/'src',package/'src')
            out=package/'dist';out.mkdir()
            outside=directory/'outside';outside.mkdir()
            sentinel=outside/'SEIHouseDisplay-Soft.woff2'
            sentinel.write_bytes(b'preserve external font')
            marker=out/'obsolete.js';marker.write_text('preserve until preflight passes',encoding='utf-8')
            try:
                (out/'fonts').symlink_to(outside,target_is_directory=True)
            except OSError as error:
                if os.name!='nt':
                    raise
                # Windows junctions require no symlink privilege and have the same hazard.
                result=subprocess.run(['cmd','/c','mklink','/J',str(out/'fonts'),str(outside)],capture_output=True)
                if result.returncode:
                    self.skipTest(f'Link creation unavailable on this host: {error}')
            with patch.object(build_living_package,'PACKAGE',package):
                with self.assertRaisesRegex(ValueError,'symlinks, junctions or external paths'):
                    build_living_package.build()
            self.assertEqual(sentinel.read_bytes(),b'preserve external font')
            self.assertEqual(marker.read_text(encoding='utf-8'),'preserve until preflight passes')


if __name__=='__main__':
    unittest.main()
