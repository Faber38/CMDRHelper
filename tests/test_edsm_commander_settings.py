from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QEvent, QObject, QSettings, QThread
from PySide6.QtWidgets import QApplication
from shiboken6 import isValid

from cmdrhelper.exit_tasks import task_gate
from cmdrhelper.state import AppState


class EDSMCommanderSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.threads = []
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.settings = QSettings(
            str(Path(self.temp.name) / "settings.ini"), QSettings.IniFormat
        )
        self.state = AppState.__new__(AppState)
        QObject.__init__(self.state)
        self.state.settings = self.settings
        self.state.commander_id = 1
        self.state.commander_fid = "F-A"
        self.state.commander = "Alpha"
        self.state.journal_folder = Path(self.temp.name)
        self.state.viewed_commander_id = 1
        self.state._edsm_upload_running = False
        self.state._edsm_upload_token = None
        self.state._edsm_runtime_by_fid = {}
        self.state.edsm_upload_status = "disabled"
        self.state.edsm_upload_message = "EDSM deaktiviert"
        self.state.edsm_enabled = False
        self.state.edsm_api_key = ""
        self.state.edsm_commander = ""
        self.addCleanup(self.cleanup_state)

    def cleanup_state(self):
        self.assertEqual(QThread.currentThread(), self.app.thread())
        self.assertTrue(all(not thread.is_alive() for thread in self.threads))
        gate = task_gate()
        self.assertFalse(gate.draining)
        # Remove only this fixture's completed workers, never reset the gate.
        gate.threads[:] = [thread for thread in gate.threads if thread not in self.threads]
        self.settings.sync()
        self.state.deleteLater()
        self.settings.deleteLater()
        self.app.sendPostedEvents(None, QEvent.DeferredDelete)
        self.assertFalse(isValid(self.state))
        self.assertFalse(isValid(self.settings))

    def test_distinct_configuration_and_view_selection_is_irrelevant(self):
        self.state.set_edsm_settings("Alpha", "KEY-A", True, fid="F-A")
        self.state.set_edsm_settings("Bravo", "KEY-B", True, fid="F-B")
        self.assertEqual(self.state.edsm_settings_for_fid("F-A")["api_key"], "KEY-A")
        self.assertEqual(self.state.edsm_settings_for_fid("F-B")["api_key"], "KEY-B")
        self.state.viewed_commander_id = 2
        self.assertEqual(self.state.edsm_api_key, "KEY-A")

    def test_legacy_migration_requires_matching_unambiguous_live_identity(self):
        self.settings.setValue("edsm/commander_fid", "F-A")
        for key, value in (("edsm/commander", "Alpha"),
                           ("edsm/api_key", "OLD-A"), ("edsm/enabled", True)):
            self.settings.setValue(key, value)
        self.state._journal_index_sessions = [{
            "attribution_status": "ambiguous", "fid_seen": ""
        }]
        self.assertFalse(self.state._migrate_legacy_edsm_settings())
        self.assertTrue(self.settings.contains("edsm/api_key"))
        self.state._journal_index_sessions = [{
            "attribution_status": "identified", "fid_seen": "F-A"
        }]
        self.assertTrue(self.state._migrate_legacy_edsm_settings())
        self.assertEqual(self.state.edsm_settings_for_fid("F-A")["api_key"], "OLD-A")
        self.assertFalse(self.settings.contains("edsm/api_key"))

    def test_legacy_name_mismatch_is_not_migrated_or_removed(self):
        self.settings.setValue("edsm/commander", "Bravo")
        self.settings.setValue("edsm/api_key", "OLD-B")
        self.state._journal_index_sessions = [{
            "attribution_status": "identified", "fid_seen": "F-A"
        }]
        self.assertFalse(self.state._migrate_legacy_edsm_settings())
        self.assertEqual(self.state.edsm_settings_for_fid("F-A")["api_key"], "")
        self.assertTrue(self.settings.contains("edsm/api_key"))

    def test_legacy_upload_progress_moves_to_the_matched_fid(self):
        self.settings.setValue("edsm/commander_fid", "F-A")
        self.state._journal_index_sessions = [{"attribution_status": "identified", "fid_seen": "F-A"}]
        self.settings.setValue("edsm/commander", "Alpha")
        self.settings.setValue("edsm/api_key", "OLD-A")
        self.settings.setValue("edsm/enabled", True)
        self.settings.setValue("edsm_upload/initialized", True)
        self.settings.setValue("edsm_upload/positions/Journal.A.log", 123)
        self.assertTrue(self.state._migrate_legacy_edsm_settings())
        self.assertEqual(
            self.settings.value(
                "edsm_upload/commanders/F-A/positions/Journal.A.log"
            ),
            123,
        )
        self.assertFalse(self.settings.contains("edsm_upload/initialized"))

    def test_stale_a_worker_cannot_block_or_send_after_switch_to_b(self):
        self.state.set_edsm_settings("Alpha", "KEY-A", True, fid="F-A")
        self.state.set_edsm_settings("Bravo", "KEY-B", True, fid="F-B")
        workers = []
        uploads = []
        threads = self.threads

        class ThreadStub:
            def __init__(self, target, **_kwargs):
                self.target = target
                self.started = False
                self.alive = False
                threads.append(self)

            def start(self):
                if self.started:
                    raise RuntimeError("threads can only be started once")
                self.started = self.alive = True
                workers.append(self.run)

            def is_alive(self):
                return self.alive

            def run(self):
                try:
                    self.target()
                finally:
                    self.alive = False
                    self.target = None

        def process(uploader, _folder):
            if not uploader._still_current():
                return {"cancelled": True}
            uploads.append((uploader.fid, uploader.commander, uploader.api_key))
            return {"events_sent": 1, "events_confirmed": 1, "confirmation_complete": True,
                    "upload_attempted": True}

        with patch("cmdrhelper.state.threading.Thread", ThreadStub), patch(
            "cmdrhelper.state.EDSMJournalUploader.process_folder", process
        ):
            try:
                self.state._upload_journal_to_edsm()
                self.state._invalidate_edsm_worker()
                self.state.commander_id = 2
                self.state.commander_fid = "F-B"
                self.state.commander = "Bravo"
                self.state._load_live_edsm_settings()
                self.state.viewed_commander_id = 1
                self.state._upload_journal_to_edsm()
                self.assertEqual(len(workers), 2)
                self.assertTrue(all(thread.is_alive() for thread in threads))
                self.assertTrue(all(thread in task_gate().threads for thread in threads))
                workers[1]()
                self.assertTrue(threads[0].is_alive())
                self.assertFalse(threads[1].is_alive())
                workers[0]()
                self.assertTrue(all(not thread.is_alive() for thread in threads))
            finally:
                # Finish while the synthetic uploader is still patched, even on failure.
                for thread in threads:
                    if thread.is_alive():
                        thread.run()

        self.assertEqual(uploads, [("F-B", "Bravo", "KEY-B")])
        self.assertEqual(self.state.edsm_upload_status, 'ok')
        self.assertEqual(self.state.edsm_upload_details['confirmed'], 1)
        self.state.commander_fid = 'F-A'
        self.state._load_live_edsm_settings()
        self.assertEqual(self.state.edsm_upload_status, 'unknown')
        self.assertEqual(self.state.edsm_upload_details['confirmed'], 0)
        self.state.commander_fid = 'F-B'
        self.state._load_live_edsm_settings()
        self.assertEqual(self.state.edsm_upload_status, 'ok')

    def test_missing_b_key_does_not_start_uploader(self):
        self.state.commander_fid = "F-B"
        self.state.set_edsm_settings("Bravo", "", True, fid="F-B")
        with patch("cmdrhelper.state.threading.Thread") as thread:
            self.state._upload_journal_to_edsm()
        thread.assert_not_called()
        self.assertTrue(self.state.edsm_enabled)


if __name__ == "__main__":
    unittest.main()
