from __future__ import annotations

import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

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

    def test_windows_spawn_is_detached_and_does_not_inherit_console_handles(self):
        process = object()
        with (
            patch.object(update.os, "name", "nt"),
            patch.object(update.subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200,
                         create=True),
            patch.object(update.subprocess, "DETACHED_PROCESS", 0x8, create=True),
            patch.object(update.subprocess, "Popen", return_value=process) as popen,
        ):
            result = update._spawn(["python.exe", "worker.py"], cwd=Path("C:/app"))

        self.assertIs(result, process)
        _args, kwargs = popen.call_args
        self.assertEqual(kwargs["creationflags"], 0x208)
        self.assertIs(kwargs["stdin"], update.subprocess.DEVNULL)
        self.assertIs(kwargs["stdout"], update.subprocess.DEVNULL)
        self.assertIs(kwargs["stderr"], update.subprocess.DEVNULL)
        self.assertTrue(kwargs["close_fds"])
        self.assertNotIn("start_new_session", kwargs)

    def test_linux_spawn_behavior_is_unchanged(self):
        process = object()
        with patch.object(update.subprocess, "Popen", return_value=process) as popen:
            result = update._spawn(["python", "worker.py"], cwd=Path("/app"))

        self.assertIs(result, process)
        _args, kwargs = popen.call_args
        self.assertTrue(kwargs["start_new_session"])
        self.assertNotIn("creationflags", kwargs)
        self.assertNotIn("stdin", kwargs)
        self.assertNotIn("stdout", kwargs)
        self.assertNotIn("stderr", kwargs)

    def test_worker_and_restart_both_use_detached_spawn(self):
        worker = Mock()
        restarted = Mock()
        with tempfile.TemporaryDirectory() as directory:
            install = Path(directory)
            (install / "main.py").touch()
            with (
                patch.object(update, "_require_local_venv_interpreter"),
                patch.object(update, "_spawn", side_effect=[worker, restarted]) as spawn,
            ):
                update.launch_installer(
                    zip_path=Path("release.zip"), install_dir=install,
                    current_version="2.1", latest_version="2.1.1", parent_pid=42,
                )
                result = update._restart_cmdrhelper(install)

        self.assertIs(result, restarted)
        self.assertEqual(spawn.call_count, 2)

    def test_keyboard_interrupt_before_installation_changes_aborts_without_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install = self._installation(root)
            archive = self._release_zip(root)
            with (
                patch.object(update, "_require_local_venv_interpreter"),
                patch.object(update, "_wait_for_parent_exit"),
                patch.object(update, "_extract_release_root", side_effect=KeyboardInterrupt),
                patch.object(update, "_restore_backup") as restore,
                patch.object(update, "_restart_cmdrhelper"),
            ):
                result = update.apply_update(
                    zip_path=archive, install_dir=install,
                    current_version="2.0.9", latest_version="2.1.0", parent_pid=1,
                )

            self.assertEqual(result, 2)
            restore.assert_not_called()
            self.assertEqual((install / "main.py").read_text(), "# old\n")

    def test_keyboard_interrupt_while_waiting_aborts_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install = self._installation(root)
            archive = self._release_zip(root)
            with (
                patch.object(update, "_require_local_venv_interpreter"),
                patch.object(update, "_wait_for_parent_exit", side_effect=KeyboardInterrupt),
                patch.object(update, "_backup_managed_files") as backup,
            ):
                result = update.apply_update(
                    zip_path=archive, install_dir=install,
                    current_version="2.0.9", latest_version="2.1.0", parent_pid=1,
                )

            self.assertEqual(result, 130)
            backup.assert_not_called()

    def test_keyboard_interrupt_during_copy_rolls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install = self._installation(root)
            archive = self._release_zip(root)

            def interrupted_copy(source, destination):
                (destination / "main.py").write_text("# partial\n")
                (destination / "cmdrhelper" / "new_only.py").write_text("partial\n")
                raise KeyboardInterrupt

            with (
                patch.object(update, "_require_local_venv_interpreter"),
                patch.object(update, "_wait_for_parent_exit"),
                patch.object(update, "_copy_release", side_effect=interrupted_copy),
                patch.object(update, "_restart_cmdrhelper"),
            ):
                result = update.apply_update(
                    zip_path=archive, install_dir=install,
                    current_version="2.0.9", latest_version="2.1.0", parent_pid=1,
                )

            self.assertEqual(result, 2)
            self.assertEqual((install / "main.py").read_text(), "# old\n")
            self.assertFalse((install / "cmdrhelper" / "new_only.py").exists())
            log = (install / update.UPDATE_LOG_RELATIVE).read_text(encoding="utf-8")
            self.assertIn("KeyboardInterrupt", log)
            self.assertIn("Rollback erfolgreich", log)

    def test_keyboard_interrupt_during_dependencies_marks_repair(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install = self._installation(root)
            archive = self._release_zip(root)
            with (
                patch.object(update, "_require_local_venv_interpreter"),
                patch.object(update, "_wait_for_parent_exit"),
                patch.object(update, "_install_requirements", side_effect=KeyboardInterrupt),
            ):
                result = update.apply_update(
                    zip_path=archive, install_dir=install,
                    current_version="2.0.9", latest_version="2.1.0", parent_pid=1,
                )

            self.assertEqual(result, 2)
            marker = json.loads(
                (install / update.UPDATE_REPAIR_RELATIVE).read_text(encoding="utf-8")
            )
            self.assertEqual(marker["phase"], "Python-Abhängigkeiten installieren")

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
