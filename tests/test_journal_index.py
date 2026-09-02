from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.journal_reader import _LIVE_LINE_CACHE, read_latest_state


class JournalIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.database = CMDRDatabase(self.folder / "index.db")

    def tearDown(self):
        _LIVE_LINE_CACHE.clear()
        self.temp.cleanup()

    def write(self, name="Journal.2026-09-02T000000.01.log", newline=True):
        path = self.folder / name
        raw = json.dumps({
            "timestamp": "2026-09-02T00:00:00Z", "event": "Commander",
            "FID": "F-TEST", "Name": "Test",
        }).encode()
        path.write_bytes(raw + (b"\n" if newline else b""))
        return path

    def test_new_file_is_indexed_and_unchanged_file_is_not_opened(self):
        path = self.write()
        first = scan_journal_folder(self.database, self.folder)
        self.assertFalse(first[0]["unchanged"])
        self.assertEqual(len(first[0]["sha256"]), 64)

        with patch.object(Path, "open", side_effect=AssertionError("opened")):
            second = scan_journal_folder(self.database, self.folder)
        self.assertTrue(second[0]["unchanged"])
        self.assertEqual(second[0]["journal_file"], str(path))

    def test_same_size_changed_content_is_detected_by_hash(self):
        path = self.write()
        old = scan_journal_folder(self.database, self.folder)[0]["sha256"]
        stat = path.stat()
        data = path.read_bytes().replace(b"F-TEST", b"F-ELSE")
        path.write_bytes(data)
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1))
        current = scan_journal_folder(self.database, self.folder)[0]
        self.assertNotEqual(current["sha256"], old)
        self.assertFalse(current["unchanged"])

    def test_incomplete_last_line_does_not_advance_safe_offset(self):
        path = self.write(newline=False)
        indexed = scan_journal_folder(self.database, self.folder)[0]
        self.assertEqual(indexed["last_complete_line_offset"], 0)
        with path.open("ab") as handle:
            handle.write(b"\n")
        indexed = scan_journal_folder(self.database, self.folder)[0]
        self.assertEqual(indexed["last_complete_line_offset"], path.stat().st_size)

    def test_mixed_names_keep_chronological_order(self):
        self.write("Journal.220905175455.01.log")
        self.write("Journal.2026-09-02T000000.01.log")
        indexed = scan_journal_folder(self.database, self.folder)
        self.assertEqual(Path(indexed[-1]["journal_file"]).name,
                         "Journal.2026-09-02T000000.01.log")

    def test_live_reader_keeps_incomplete_line_for_next_refresh(self):
        path = self.write()
        sessions = scan_journal_folder(self.database, self.folder)
        read_latest_state(self.folder, indexed_sessions=sessions)
        partial = json.dumps({"timestamp": "2026-09-02T00:00:01Z",
                              "event": "Location", "StarSystem": "Next"})
        with path.open("ab") as handle:
            handle.write(partial.encode())
        state = read_latest_state(self.folder, indexed_sessions=sessions)
        self.assertNotEqual(state["system"], "Next")
        with path.open("ab") as handle:
            handle.write(b"\n")
        state = read_latest_state(self.folder, indexed_sessions=sessions)
        self.assertEqual(state["system"], "Next")
        self.assertEqual(sessions[-1]["last_complete_line_offset"],
                         path.stat().st_size)

    def test_new_file_switches_live_fid_without_reclassifying_old_file(self):
        self.write("Journal.2026-09-01T000000.01.log")
        sessions = scan_journal_folder(self.database, self.folder)
        second = self.folder / "Journal.2026-09-02T000000.01.log"
        second.write_text(json.dumps({
            "timestamp": "2026-09-02T00:00:00Z", "event": "LoadGame",
            "FID": "F-SECOND", "Commander": "Second",
        }) + "\n")
        sessions = scan_journal_folder(self.database, self.folder)
        state = read_latest_state(self.folder, indexed_sessions=sessions)
        self.assertEqual(state["commander_fid"], "F-SECOND")
        self.assertEqual(state["commander"], "Second")


if __name__ == "__main__":
    unittest.main()
