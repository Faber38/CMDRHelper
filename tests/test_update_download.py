from __future__ import annotations

import io
import shutil
import tempfile
import threading
import unittest
import urllib.error
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtCore import QRunnable
from PySide6.QtWidgets import QApplication, QLabel, QProgressBar, QPushButton

from cmdrhelper import update
from cmdrhelper.ui.main_window import MainWindow


def zip_bytes() -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("CMDRHelper/main.py", "# release\n")
    return stream.getvalue()


class ResponseStub:
    def __init__(self, content: bytes, content_length=None):
        self.stream = io.BytesIO(content)
        self.headers = {}
        if content_length is not None:
            self.headers["Content-Length"] = str(content_length)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size=-1):
        return self.stream.read(size)


class UpdateDownloadTests(unittest.TestCase):
    def _download(self, content, *, content_length=None, asset_size=0,
                  callback=None, cancel_event=None, verifying_callback=None):
        root = Path(tempfile.mkdtemp())
        download_dir = root / "download"
        download_dir.mkdir()
        with patch.object(update.tempfile, "mkdtemp", return_value=str(download_dir)), \
                patch.object(
                    update.urllib.request, "urlopen",
                    return_value=ResponseStub(content, content_length),
                ):
            try:
                result = update.download_release(
                    {
                        "asset_url": "https://example.invalid/release.zip",
                        "asset_name": "CMDRHelper_v2.1.2.zip",
                        "asset_size": asset_size,
                        "version": "2.1.2",
                    },
                    progress_callback=callback,
                    cancel_event=cancel_event,
                    verifying_callback=verifying_callback,
                )
            except BaseException:
                self.assertFalse(download_dir.exists())
                shutil.rmtree(root, ignore_errors=True)
                raise
        return root, result

    def test_content_length_and_real_received_bytes_are_reported(self):
        content = zip_bytes()
        progress = []
        verified = []
        root, result = self._download(
            content, content_length=len(content), asset_size=len(content) + 99,
            callback=lambda received, total, rate: progress.append(
                (received, total, rate)
            ),
            verifying_callback=lambda: verified.append(True),
        )
        try:
            self.assertEqual(progress[0], (0, len(content), 0.0))
            self.assertEqual(progress[-1][0], len(content))
            self.assertEqual(progress[-1][1], len(content))
            self.assertGreater(progress[-1][2], 0)
            self.assertEqual(verified, [True])
            self.assertTrue(zipfile.is_zipfile(result))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_api_asset_size_is_fallback_when_content_length_is_unknown(self):
        content = zip_bytes()
        progress = []
        root, _result = self._download(
            content, asset_size=len(content), callback=lambda *args: progress.append(args)
        )
        try:
            self.assertEqual(progress[-1][1], len(content))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_unknown_total_reports_zero_without_inventing_percentage(self):
        progress = []
        root, _result = self._download(
            zip_bytes(), callback=lambda *args: progress.append(args)
        )
        try:
            self.assertEqual(progress[-1][1], 0)
            self.assertGreater(progress[-1][0], 0)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_cancel_removes_partial_download(self):
        cancel = threading.Event()

        def progress(received, _total, _rate):
            if received:
                cancel.set()

        with self.assertRaises(update.DownloadCancelled):
            self._download(
                zip_bytes() + b"x" * (2 * 1024 * 1024),
                callback=progress, cancel_event=cancel,
            )

    def test_network_error_removes_download_directory(self):
        root = Path(tempfile.mkdtemp())
        download_dir = root / "download"
        download_dir.mkdir()
        with patch.object(update.tempfile, "mkdtemp", return_value=str(download_dir)), \
                patch.object(
                    update.urllib.request, "urlopen",
                    side_effect=urllib.error.URLError("offline"),
                ):
            with self.assertRaises(urllib.error.URLError):
                update.download_release({
                    "asset_url": "https://example.invalid/release.zip",
                    "version": "2.1.2",
                })
        self.assertFalse(download_dir.exists())
        shutil.rmtree(root, ignore_errors=True)

    def test_invalid_zip_is_rejected_and_removed(self):
        with self.assertRaisesRegex(RuntimeError, "kein gültiges ZIP"):
            self._download(b"incomplete zip", content_length=14)

    def test_short_response_is_rejected_even_if_received_part_is_a_zip(self):
        content = zip_bytes()
        with self.assertRaisesRegex(RuntimeError, "unvollständig"):
            self._download(content, content_length=len(content) + 100)

    def test_download_worker_uses_qrunnable_and_thread_safe_cancel_flag(self):
        worker = update.UpdateDownloadWorker({})
        self.assertIsInstance(worker, QRunnable)
        self.assertFalse(worker._cancel_event.is_set())
        worker.cancel()
        self.assertTrue(worker._cancel_event.is_set())


class UpdateDownloadPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow.__new__(MainWindow)
        self.window.update_download_progress = QProgressBar()
        self.window.update_download_detail = QLabel()

    def test_known_total_calculates_percent_rate_and_eta(self):
        self.window._update_download_progress_changed(
            84 * 1024 * 1024, 160 * 1024 * 1024, 8 * 1024 * 1024,
        )
        self.assertEqual(self.window.update_download_progress.maximum(), 100)
        self.assertEqual(self.window.update_download_progress.value(), 52)
        detail = self.window.update_download_detail.text()
        self.assertIn("84.0 MiB / 160.0 MiB", detail)
        self.assertIn("52 %", detail)
        self.assertIn("8.0 MiB/s", detail)
        self.assertIn("10 s", detail)

    def test_unknown_total_uses_busy_mode_and_real_byte_count(self):
        self.window._update_download_progress_changed(
            7 * 1024 * 1024, 0, 2 * 1024 * 1024,
        )
        self.assertEqual(self.window.update_download_progress.minimum(), 0)
        self.assertEqual(self.window.update_download_progress.maximum(), 0)
        detail = self.window.update_download_detail.text()
        self.assertIn("7.0 MiB", detail)
        self.assertNotIn("%", detail)
        self.assertNotIn("remaining", detail)

    def test_install_update_only_schedules_worker_and_does_not_run_inline(self):
        callbacks = []

        class SignalStub:
            def connect(self, callback):
                callbacks.append(callback)

        class WorkerStub:
            def __init__(self, info):
                self.info = info
                self.run_called = False
                self.signals = SimpleNamespace(
                    progress=SignalStub(), verifying=SignalStub(),
                    finished=SignalStub(), failed=SignalStub(), cancelled=SignalStub(),
                )

            def run(self):
                self.run_called = True

        class PoolStub:
            def __init__(self):
                self.worker = None

            def start(self, worker):
                self.worker = worker

        window = self.window
        window.update_status_label = QLabel()
        window.update_check_button = QPushButton()
        window.update_download_file = QLabel()
        window.update_download_detail = QLabel()
        window.update_cancel_button = QPushButton()
        window.update_thread_pool = PoolStub()
        with patch("cmdrhelper.ui.main_window.UpdateDownloadWorker", WorkerStub):
            window._install_update({
                "version": "2.1.2", "asset_name": "CMDRHelper_v2.1.2.zip",
                "asset_url": "https://example.invalid/release.zip",
            })
        self.assertIs(window.update_thread_pool.worker, window._update_download_worker)
        self.assertFalse(window._update_download_worker.run_called)


if __name__ == "__main__":
    unittest.main()
