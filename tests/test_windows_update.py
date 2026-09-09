from __future__ import annotations

import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from cmdrhelper import update, windows_update, i18n


class WindowsProcessTests(unittest.TestCase):
    def kernel(self, result=0):
        kernel = Mock()
        kernel.OpenProcess.return_value = 123
        kernel.WaitForSingleObject.return_value = result
        return kernel

    def test_waits_on_process_handle_without_termination_rights(self):
        kernel = self.kernel()
        with patch.object(windows_update, "_kernel32", return_value=kernel), \
                patch.object(os, "kill", side_effect=AssertionError("must not signal")):
            windows_update.wait_for_process_exit(42, 12)
        kernel.OpenProcess.assert_called_once_with(0x00100000, False, 42)
        kernel.WaitForSingleObject.assert_called_once_with(123, 12000)
        kernel.CloseHandle.assert_called_once_with(123)

    def test_timeout_closes_handle(self):
        kernel = self.kernel(258)
        with patch.object(windows_update, "_kernel32", return_value=kernel):
            with self.assertRaisesRegex(RuntimeError, "rechtzeitig"):
                windows_update.wait_for_process_exit(42)
        kernel.CloseHandle.assert_called_once_with(123)

    def test_missing_process_is_finished_but_access_error_is_not(self):
        kernel = self.kernel()
        kernel.OpenProcess.return_value = None
        for error in (87, 5):
            with self.subTest(error=error), \
                    patch.object(windows_update, "_kernel32", return_value=kernel), \
                    patch.object(windows_update.ctypes, "get_last_error", return_value=error, create=True):
                if error == 87:
                    windows_update.wait_for_process_exit(42)
                else:
                    with self.assertRaises(OSError):
                        windows_update.wait_for_process_exit(42)
        kernel.WaitForSingleObject.assert_not_called()

    def test_wait_failure_is_not_process_exit(self):
        kernel = self.kernel(0xFFFFFFFF)
        with patch.object(windows_update, "_kernel32", return_value=kernel), \
                patch.object(windows_update.ctypes, "get_last_error", return_value=6, create=True):
            with self.assertRaises(OSError):
                windows_update.wait_for_process_exit(42)
        kernel.CloseHandle.assert_called_once()

    def test_windows_dispatch_never_uses_kill(self):
        with patch.object(update, "os", SimpleNamespace(name="nt")), \
                patch.object(windows_update, "wait_for_process_exit") as wait:
            update._wait_for_parent_exit(42, 9)
            wait.assert_called_once_with(42, 9)
            with self.assertRaises(RuntimeError):
                update._pid_exists(42)


class UpdateSequenceTests(unittest.TestCase):
    def scenario(self, platform="nt", failure=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install = root / "app with spaces"
            (install / "cmdrhelper").mkdir(parents=True)
            (install / "data").mkdir()
            (install / "data" / "user.db").write_bytes(b"personal")
            (install / "main.py").write_text("old")
            (root / "download").mkdir()
            archive = root / "download" / "release.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("release/main.py", "new")
                z.writestr("release/cmdrhelper/version.py", '__version__ = "3.2.1"')
                z.writestr("release/data/user.db", "DO NOT INSTALL")
            events = []
            lock = Mock()
            lock.unlock.side_effect = lambda: events.append("unlock")
            real_backup = update._backup_managed_files
            real_copy = update._copy_release
            def wait(*args):
                events.append("wait")
                self.assertEqual((install / "main.py").read_text(), "old")
                restart.assert_not_called()
                if failure == "wait":
                    raise RuntimeError("timeout")
                events.append("exited")
            def acquire():
                self.assertIn("exited", events)
                events.append("lock")
                if failure == "lock":
                    raise RuntimeError("lock timeout")
                return lock
            def backup(*args):
                events.append("backup")
                real_backup(*args)
            def copy(*args):
                events.append("copy")
                real_copy(*args)
                if failure == "copy":
                    raise RuntimeError("copy failed")
            def launch(*args):
                events.append("restart")
                self.assertIn("exited", events)
                if platform == "nt":
                    self.assertIn("unlock", events)
                return Mock(pid=999)
            # Replace only update's os reference; pathlib still sees the host OS.
            fake_os = Mock(wraps=os)
            fake_os.name = platform
            with patch.object(update, "os", fake_os), \
                    patch.object(update, "_require_local_venv_interpreter"), \
                    patch.object(update, "_wait_for_parent_exit", side_effect=wait), \
                    patch.object(update, "_acquire_update_instance_lock", side_effect=acquire), \
                    patch.object(update, "_backup_managed_files", side_effect=backup), \
                    patch.object(update, "_copy_release", side_effect=copy), \
                    patch.object(update, "_install_requirements", side_effect=RuntimeError("pip failed") if failure == "dependencies" else None), \
                    patch.object(update, "_installed_version", return_value="wrong" if failure == "version" else "3.2.1"), \
                    patch.object(update, "_restart_cmdrhelper", side_effect=launch) as restart, \
                    patch.object(update, "_verify_restart"):
                result = update.apply_update(zip_path=archive, install_dir=install,
                    current_version="3.2", latest_version="3.2.1", parent_pid=42)
            self.assertEqual((install / "data" / "user.db").read_bytes(), b"personal")
            self.assertEqual((install / "main.py").read_text(), "old" if failure else "new")
            if "backup" in events:
                backups = list((install / "backup").glob("CMDRHelper_v*"))
                self.assertEqual((backups[0] / "main.py").read_text(), "old")
                self.assertFalse((backups[0] / "data").exists())
            return result, events, restart.call_count

    def test_windows_order_and_exactly_one_restart(self):
        self.assertEqual(self.scenario(), (0,
            ["wait", "exited", "lock", "backup", "copy", "unlock", "restart"], 1))

    def test_windows_wait_timeout_does_not_install_or_restart(self):
        self.assertEqual(self.scenario(failure="wait"), (4, ["wait"], 0))

    def test_windows_lock_timeout_does_not_install_or_restart(self):
        self.assertEqual(self.scenario(failure="lock"), (4, ["wait", "exited", "lock"], 0))

    def test_windows_copy_failure_rolls_back_without_restart(self):
        self.assertEqual(self.scenario(failure="copy"), (2,
            ["wait", "exited", "lock", "backup", "copy", "unlock"], 0))

    def test_windows_dependency_or_version_failure_never_restarts(self):
        for failure in ("dependencies", "version"):
            with self.subTest(failure=failure):
                result, events, count = self.scenario(failure=failure)
                self.assertEqual(result, 2)
                self.assertEqual(count, 0)
                self.assertEqual(events[-1], "unlock")

    @unittest.skipIf(os.name == "nt", "Linux regression runs on Linux")
    def test_linux_success_keeps_existing_flow(self):
        self.assertEqual(self.scenario("posix"), (0,
            ["wait", "exited", "backup", "copy", "restart"], 1))

    @unittest.skipIf(os.name == "nt", "Linux regression runs on Linux")
    def test_linux_rollback_still_restarts_restored_version(self):
        self.assertEqual(self.scenario("posix", "copy"), (2,
            ["wait", "exited", "backup", "copy", "restart"], 1))

    def test_helper_starts_only_update_module_with_parent_pid(self):
        with patch.object(update, "_require_local_venv_interpreter"), \
                patch.object(update, "_spawn") as spawn, \
                patch.object(update, "_log_update"):
            update.launch_installer(zip_path=Path("release.zip"), install_dir=Path("app"),
                current_version="3.2", latest_version="3.2.1", parent_pid=42)
        args = spawn.call_args.args[0]
        self.assertEqual(args[:3], [update.sys.executable, "-m", "cmdrhelper.update"])
        self.assertNotIn("main.py", args)
        self.assertEqual(args[-2:], ["--parent-pid", "42"])
        spawn.assert_called_once()

    def test_restart_uses_running_venv_interpreter_and_absolute_main(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.py").touch()
            with patch.object(update, "_spawn") as spawn:
                update._restart_cmdrhelper(root)
            spawn.assert_called_once_with([update.sys.executable, str(root / "main.py")], cwd=root)


class DownloadHandoffTests(unittest.TestCase):
    def handoff(self, platform, fail=False):
        from cmdrhelper.ui import main_window as ui
        events = []
        window = SimpleNamespace(
            _update_download_result={"version": "3.2.1"},
            _release_requires_database_update=lambda result: False,
            _finish_update_download_ui=lambda: None,
            _set_update_status=lambda text: None,
            _update_download_failed=lambda error: events.append("failed"),
        )
        def launch(**kwargs):
            events.append("helper")
            if fail:
                raise RuntimeError("spawn failed")
        fake_os = Mock(wraps=os)
        fake_os.name = platform
        with patch.object(ui, "os", fake_os), \
                patch.object(ui, "launch_installer", side_effect=launch), \
                patch.object(ui.QMessageBox, "information", side_effect=lambda *a: events.append("dialog")), \
                patch.object(ui.QApplication, "quit", side_effect=lambda: events.append("quit")):
            ui.MainWindow._update_download_finished(window, Path("release.zip"))
        return events

    def test_windows_dialog_does_not_consume_helper_timeout(self):
        self.assertEqual(self.handoff("nt"), ["dialog", "helper", "quit"])

    def test_spawn_failure_keeps_old_application_open(self):
        self.assertEqual(self.handoff("nt", True), ["dialog", "helper", "failed"])

    def test_linux_dialog_order_unchanged(self):
        self.assertEqual(self.handoff("posix"), ["helper", "dialog", "quit"])


class SingleInstanceTests(unittest.TestCase):
    def test_all_languages_have_actual_paragraphs(self):
        for language in i18n._TRANSLATIONS:
            with self.subTest(language=language):
                text = i18n.tr_for_language(language, "app.already_running_text")
                self.assertIn("\n\n", text)
                self.assertNotIn(r"\n", text)

    def test_updater_waits_for_same_lock_and_does_not_remove_live_lock(self):
        lock = Mock()
        lock.tryLock.return_value = False
        with patch.object(update, "QLockFile", return_value=lock) as factory:
            with self.assertRaisesRegex(RuntimeError, "Sperre"):
                update._acquire_update_instance_lock(1)
        self.assertTrue(factory.call_args.args[0].endswith("cmdrhelper.lock"))
        lock.tryLock.assert_called_once_with(1000)
        lock.setStaleLockTime.assert_called_once_with(0)
        lock.removeStaleLockFile.assert_not_called()

    def test_manual_second_start_stops_before_state_and_window(self):
        from cmdrhelper import app
        lock = Mock()
        lock.tryLock.return_value = False
        with patch.object(app, "os", SimpleNamespace(name="nt", getpid=lambda: 42)), \
                patch.object(app, "QApplication"), \
                patch.object(app, "QLockFile", return_value=lock), \
                patch.object(app, "QSettings"), \
                patch.object(app, "QMessageBox") as message, \
                patch.object(app, "configure_logging"), \
                patch.object(app, "AppState") as state, \
                patch.object(app, "MainWindow") as window, \
                patch.object(app.sys, "excepthook"):
            app.run()
        message.information.assert_called_once()
        lock.setStaleLockTime.assert_called_once_with(0)
        state.assert_not_called()
        window.assert_not_called()


if __name__ == "__main__":
    unittest.main()
