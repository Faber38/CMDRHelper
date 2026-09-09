import tempfile
import unittest
import zipfile
from pathlib import Path

from tools import local_update_test as fixture


class LocalUpdateFixtureTests(unittest.TestCase):
    def test_derives_next_version_without_changing_source_or_other_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'CMDRHelper_v3.2.zip'
            with zipfile.ZipFile(source, 'w') as archive:
                archive.writestr('CMDRHelper_v3.2/cmdrhelper/version.py', '__version__ = "3.2"')
                archive.writestr('CMDRHelper_v3.2/main.py', '# unchanged')
            before = source.read_bytes()
            fixture.prepare(source, root / 'fixtures', '3.2.1')
            self.assertEqual(source.read_bytes(), before)
            target = root / 'fixtures/CMDRHelper_v3.2.1.zip'
            self.assertEqual(fixture.archive_version(source), '3.2')
            self.assertEqual(fixture.archive_version(target), '3.2.1')
            with zipfile.ZipFile(target) as archive:
                self.assertEqual(archive.read('CMDRHelper_v3.2/main.py'), b'# unchanged')
            self.assertTrue((root / 'fixtures/local_update_test.py').exists())
            with self.assertRaises(FileExistsError):
                fixture.prepare(source, root / 'fixtures', '3.2.1')

    def test_runner_requires_explicit_test_installation_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'Testinstallationen'):
                fixture.run(Path(directory), Path('unused.zip'))


if __name__ == '__main__':
    unittest.main()
