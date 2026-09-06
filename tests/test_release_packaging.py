"""Exercise packaging in tiny isolated projects, never the working release tree."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ['main.py', 'requirements.txt', 'LICENSE', 'README.md'] + [
    f'README_{lang}.md' for lang in 'DE FR IT NO SV FI PL NL ES TR EL'.split()
] + ['install.sh', 'start.sh', 'install.bat', 'install-windows.ps1', 'start.bat']
EXCLUDED = [
    'cmdrhelper/ui/backup_main_window.py', 'cmdrhelper/ui/_main_window.py',
    'cmdrhelper/assets/readme/text/de.py',
    'cmdrhelper/assets/readme/cmdrhelper_readme_master.png',
    'docs/planet-navigation-i18n-audit.md',
]


@unittest.skipUnless(all(shutil.which(t) for t in ('bash', 'zip', 'unzip')), 'requires bash/zip/unzip')
class ReleasePackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copyfile(ROOT / 'create_release.sh', self.root / 'create_release.sh')
        for name in REQUIRED:
            self.write(name, 'fixture\n')
        self.write('cmdrhelper/version.py', '__version__ = "3.0"\n')
        self.write('cmdrhelper/__init__.py', '')
        self.write('release/CMDRHelper_v2.5/keep.txt', 'older directory')
        self.write('release/CMDRHelper_v2.5.zip', 'older archive')
        self.write('release/CMDRHelper_v3.0/keep.txt', 'current directory')
        self.write('release/CMDRHelper_v3.0.zip', 'current archive')
        self.before = self.release_snapshot()

    def write(self, name, content='fixture'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def release_snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in (self.root / 'release').rglob('*') if p.is_file()}

    def run_script(self, env=None):
        return subprocess.run(['bash', 'create_release.sh'], cwd=self.root,
                              env=env, capture_output=True, text=True, timeout=20)

    def assert_preserved(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.release_snapshot(), self.before)
        self.assertFalse(list((self.root / 'release').glob('.cmdrhelper-stage.*')))

    def test_every_missing_root_file_preserves_all_existing_releases(self):
        for name in REQUIRED:
            with self.subTest(name=name):
                path = self.root / name
                saved = path.read_bytes()
                path.unlink()
                result = self.run_script()
                self.assert_preserved(result)
                self.assertIn(name, result.stderr)
                path.write_bytes(saved)

    def test_recursive_payload_exclusions_and_originals(self):
        included = ['cmdrhelper/new_future_module.py', 'cmdrhelper/favorites.py',
                    'cmdrhelper/ui/favorites_view.py', 'cmdrhelper/ui/navigation_hud_windows.py',
                    'cmdrhelper/screenshot_paths.py', 'cmdrhelper/ui/screenshot_view.py',
                    'cmdrhelper/assets/bodies/planet.png', 'cmdrhelper/assets/bodies/star.webm']
        for name in included + EXCLUDED + ['cmdrhelper/__pycache__/dummy.pyc']:
            self.write(name)
        for name in ['data/cmdrhelper.db', 'data/favorites/images/private.png',
                     'screenshots/private.bmp', 'tests/private.py', '.codex/private.txt']:
            self.write(name, 'personal source unchanged')
        self.write('data/.gitkeep', 'do not distribute even this content')
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.root / 'release/CMDRHelper_v3.0'
        expected = set(REQUIRED + included + ['cmdrhelper/version.py', 'cmdrhelper/__init__.py', 'data/.gitkeep'])
        actual = {str(p.relative_to(target)) for p in target.rglob('*') if p.is_file()}
        self.assertEqual(actual, expected)
        with zipfile.ZipFile(self.root / 'release/CMDRHelper_v3.0.zip') as archive:
            self.assertIsNone(archive.testzip())
            names = {n.removeprefix('CMDRHelper_v3.0/') for n in archive.namelist() if not n.endswith('/')}
            self.assertEqual(names, expected)
            for name in names:
                self.assertEqual(archive.read('CMDRHelper_v3.0/' + name), (target / name).read_bytes())
        for name, data in self.before.items():
            if 'v2.5' in name:
                self.assertEqual((self.root / name).read_bytes(), data)
        for name in EXCLUDED:
            self.assertTrue((self.root / name).exists())
        self.assertEqual((self.root / 'data/favorites/images/private.png').read_text(), 'personal source unchanged')
        self.assertEqual((target / 'data/.gitkeep').read_bytes(), b'')

    def test_unexpected_data_reports_path_and_preserves_releases(self):
        for name in ['cmdrhelper/private.db', 'docs/private.sqlite', 'docs/private.sqlite3-wal',
                     'cmdrhelper/logs/session.log', 'cmdrhelper/tests/test_private.py',
                     'cmdrhelper/.codex/session.txt', 'cmdrhelper/.agents/notes.txt',
                     'cmdrhelper/.git/config', 'cmdrhelper/.venv/marker',
                     'cmdrhelper/venv/marker', 'cmdrhelper/favorites/images/private.png',
                     'docs/Screenshot123.png', 'docs/2026-09-06_12-30-00_Commander.png',
                     'cmdrhelper/settings.ini', 'cmdrhelper/config.json',
                     'cmdrhelper/.config/private-settings', 'cmdrhelper/user.config', 'docs/edit.tmp']:
            with self.subTest(name=name):
                path = self.write(name)
                result = self.run_script()
                self.assert_preserved(result)
                self.assertIn(name, result.stderr)
                path.unlink()
                parent = path.parent
                while parent != self.root and parent not in (self.root / 'cmdrhelper',):
                    if any(parent.iterdir()):
                        break
                    parent.rmdir()
                    parent = parent.parent

    def test_symlink_cannot_import_private_files(self):
        source = self.write('private.txt', 'secret')
        (self.root / 'cmdrhelper/linked.txt').symlink_to(source)
        result = self.run_script()
        self.assert_preserved(result)
        self.assertIn('cmdrhelper/linked.txt', result.stderr)

    def fake_tool(self, name, script):
        tool = self.write('bin/' + name, '#!/bin/bash\n' + script)
        tool.chmod(0o755)
        return dict(os.environ, PATH=str(tool.parent) + os.pathsep + os.environ['PATH'])

    def test_cleanup_failure_is_not_ignored(self):
        real_rm = shutil.which('rm')
        env = self.fake_tool('rm', f'for arg in "$@"; do\n case "$arg" in */backup_main_window.py) exit 42 ;; esac\ndone\nexec "{real_rm}" "$@"\n')
        result = self.run_script(env)
        self.assert_preserved(result)
        self.assertIn('backup_main_window.py', result.stderr)

    def test_zip_failure_preserves_existing_releases(self):
        result = self.run_script(self.fake_tool('zip', 'exit 42\n'))
        self.assert_preserved(result)

    def test_failed_final_install_rolls_back_both_current_artifacts(self):
        real_mv = shutil.which('mv')
        env = self.fake_tool('mv', f'case "$2" in */.cmdrhelper-stage.*/CMDRHelper_v3.0.zip) exit 42 ;; esac\nexec "{real_mv}" "$@"\n')
        result = self.run_script(env)
        self.assert_preserved(result)


if __name__ == '__main__':
    unittest.main()
