from __future__ import annotations

import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from cmdrhelper.python_support import is_supported
from cmdrhelper import update


ROOT = Path(__file__).resolve().parents[1]


class PythonSupportTests(unittest.TestCase):
    def test_supported_bounds(self):
        self.assertFalse(is_supported((3, 9, 9)))
        self.assertTrue(is_supported((3, 10, 0)))
        self.assertTrue(is_supported((3, 13, 9)))
        self.assertFalse(is_supported((3, 14, 0)))


class WindowsBatchContractTests(unittest.TestCase):
    def test_install_is_root_bound_and_repairs_only_local_venv(self):
        text = (ROOT / "install.bat").read_text(encoding="utf-8")
        self.assertIn('cd /d "%INSTALL_ROOT%"', text)
        self.assertIn('if errorlevel 1 (', text)
        self.assertIn('set "VENV_DIR=%INSTALL_ROOT%venv"', text)
        self.assertIn('rmdir /s /q "%VENV_DIR%"', text)
        self.assertIn('fsutil reparsepoint query "%VENV_DIR%"', text)
        self.assertNotIn("data\\", text)
        self.assertIn('"%VENV_PYTHON%" -m pip install -r "%REQUIREMENTS%"', text)

    def test_start_uses_absolute_local_paths_and_preserves_exitcode(self):
        text = (ROOT / "start.bat").read_text(encoding="utf-8")
        self.assertIn('set "VENV_PYTHON=%INSTALL_ROOT%venv\\Scripts\\python.exe"', text)
        self.assertIn('set "MAIN_PY=%INSTALL_ROOT%main.py"', text)
        run = text.index('"%VENV_PYTHON%" "%MAIN_PY%"')
        save = text.index('set "APP_EXIT=%errorlevel%"')
        pause = text.index("pause", save)
        self.assertLess(run, save)
        self.assertLess(save, pause)
        self.assertIn("exit /b %APP_EXIT%", text)


class UpdaterSafetyTests(unittest.TestCase):
    def _release_zip(self, parent: Path, extra=True) -> Path:
        source = parent / "release source" / "CMDRHelper_v2.1.0"
        (source / "cmdrhelper").mkdir(parents=True)
        (source / "main.py").write_text("# new\n", encoding="utf-8")
        (source / "requirements.txt").write_text("example>=1\n", encoding="utf-8")
        (source / "cmdrhelper" / "version.py").write_text(
            '__version__ = "2.1.0"\n', encoding="utf-8"
        )
        if extra:
            (source / "cmdrhelper" / "new_only.py").write_text("NEW = True\n")
        download = parent / "download"
        download.mkdir()
        archive = download / "release.zip"
        with zipfile.ZipFile(archive, "w") as handle:
            for item in source.rglob("*"):
                if item.is_file():
                    handle.write(item, Path(source.name) / item.relative_to(source))
        return archive

    def _installation(self, parent: Path) -> Path:
        install = parent / "CMDR Helper Ü Test"
        (install / "cmdrhelper").mkdir(parents=True)
        (install / "data").mkdir()
        (install / "main.py").write_text("# old\n")
        (install / "requirements.txt").write_text("olddep==1\n")
        (install / "cmdrhelper" / "version.py").write_text(
            '__version__ = "2.0.9"\n'
        )
        (install / "data" / "cmdrhelper.db").write_text("personal")
        return install

    def test_foreign_interpreter_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            install = Path(directory) / "app"
            expected = update._expected_venv_python(install)
            expected.parent.mkdir(parents=True)
            expected.touch()
            with self.assertRaisesRegex(RuntimeError, "lokalen venv"):
                update._require_local_venv_interpreter(
                    install, Path(directory) / "other" / "python.exe"
                )

    def test_apply_failure_removes_new_files_and_marks_repair(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install = self._installation(root)
            archive = self._release_zip(root)
            with (
                patch.object(update, "_require_local_venv_interpreter"),
                patch.object(update, "_wait_for_parent_exit"),
                patch.object(update, "_install_requirements", side_effect=RuntimeError("pip failed")),
            ):
                result = update.apply_update(
                    zip_path=archive, install_dir=install,
                    current_version="2.0.9", latest_version="2.1.0", parent_pid=1,
                )
            self.assertEqual(result, 2)
            self.assertEqual((install / "main.py").read_text(), "# old\n")
            self.assertFalse((install / "cmdrhelper" / "new_only.py").exists())
            self.assertEqual((install / "data" / "cmdrhelper.db").read_text(), "personal")
            marker = json.loads((install / update.UPDATE_REPAIR_RELATIVE).read_text())
            self.assertEqual(marker["phase"], "Python-Abhängigkeiten installieren")
            expected_repair = "install.bat" if os.name == "nt" else "install.sh"
            self.assertEqual(marker["repair"], expected_repair)
            status = update.consume_update_status(install)
            self.assertEqual(status["kind"], "rollback")
            self.assertFalse((install / update.UPDATE_STATUS_RELATIVE).exists())

    def test_success_verifies_version_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install = self._installation(root)
            archive = self._release_zip(root)
            with (
                patch.object(update, "_require_local_venv_interpreter"),
                patch.object(update, "_wait_for_parent_exit"),
                patch.object(update, "_install_requirements"),
                patch.object(update, "_installed_version", return_value="2.1.0") as version,
                patch.object(update, "_restart_cmdrhelper", return_value=object()),
                patch.object(update, "_verify_restart") as handshake,
            ):
                result = update.apply_update(
                    zip_path=archive, install_dir=install,
                    current_version="2.0.9", latest_version="2.1.0", parent_pid=1,
                )
            self.assertEqual(result, 0)
            version.assert_called_once_with(install.resolve())
            handshake.assert_called_once()
            self.assertTrue((install / "cmdrhelper" / "new_only.py").exists())
            self.assertEqual((install / "data" / "cmdrhelper.db").read_text(), "personal")


if __name__ == "__main__":
    unittest.main()
