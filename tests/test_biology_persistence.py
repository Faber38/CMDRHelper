import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from cmdrhelper.biology_backfill import backfill_biology
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.i18n import get_language, set_language
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.journal_reader import read_journal_delta
from cmdrhelper.state import AppState
from cmdrhelper.ui.body_detail_window import BodyDetailWindow


ADDRESS = 20154100423162
NAME = "Prua Hypai RB-D c29-73 AB 2 f"
VARIANTS = (
    "Fungoida Setisis - Orange", "Tussock Catena - Lime",
    "Frutexa Flammasis - Smaragd", "Osseus Spiralis - Grau",
    "Bacterium Alcyoneum - Smaragd", "Cactoida Peperatis - Blaugrün",
)


def organic(variant=VARIANTS[0], progress="Analyse", **extra):
    return {"event": "ScanOrganic", "timestamp": "2026-09-04T12:37:06Z",
            "SystemAddress": ADDRESS, "Body": 51, "ScanType": progress,
            "Genus_Localised": variant.split()[0],
            "Species_Localised": variant.split(" - ")[0],
            "Variant_Localised": variant, **extra}


def contents(path):
    with sqlite3.connect(path) as con:
        return {name: sorted(con.execute(f'SELECT * FROM "{name}"').fetchall(), key=repr)
                for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}


class BiologyPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.db = CMDRDatabase(self.folder / "state.db")
        self.commander = self.db.upsert_commander("F12520967", "FABER38")
        self.other = self.db.upsert_commander("OTHER", "Other")
        self.journal = self.folder / "Journal.2026-09-04T134325.01.log"

    def prepare(self, events, *, already_read=False, fid="F12520967"):
        entries = [{"event": "LoadGame", "timestamp": "2026-09-04T11:43:53Z",
                    "FID": fid, "Commander": "FABER38"}, *events]
        self.journal.write_text("".join(json.dumps(e) + "\n" for e in entries))
        scan_journal_folder(self.db, self.folder)
        if already_read:
            with self.db._connect() as con:
                con.execute("UPDATE journal_sessions SET last_read_offset=? WHERE journal_file=?",
                            (self.journal.stat().st_size, str(self.journal)))
        return read_journal_delta(self.journal, 0)

    def findings(self, body=51, commander=None, address=ADDRESS):
        return self.db.biology_for_body(address, body, commander or self.commander)

    def backfill(self, **options):
        return backfill_biology(self.db.path, self.commander,
                                journals=[self.journal], **options)

    def test_live_progress_numeric_body_and_replay_are_one_durable_finding(self):
        events, offset = self.prepare([organic(progress=p) for p in ("Log", "Sample", "Analyse")])
        self.db.apply_commander_journal_delta(self.commander, self.journal, events, offset)
        self.assertEqual(len(self.findings()), 1)
        self.assertEqual(self.findings()[0]["scan_type"], "Analyse")
        self.db.apply_commander_journal_delta(self.commander, self.journal, events, offset)
        self.assertEqual(len(self.findings()), 1)
        # Even replayed older progress at a new offset must not demote Analyse.
        self.db.apply_commander_journal_delta(self.commander, self.journal,
            [organic(progress="Log", timestamp="2026-09-04T12:33:34Z")], offset + 1)
        self.assertEqual(self.findings()[0]["scan_type"], "Analyse")
        self.assertEqual(self.findings()[0]["last_seen"], "2026-09-04T12:37:06Z")

    def test_log_and_sample_persist_before_completion(self):
        events, offset = self.prepare([organic(progress="Log"),
                                      organic(VARIANTS[1], progress="Sample")])
        self.db.apply_commander_journal_delta(self.commander, self.journal, events, offset)
        self.assertEqual({r["scan_type"] for r in self.findings()}, {"Log", "Sample"})
        self.assertEqual(self.db.commander_summary(self.commander)["unsold_biology"]["findings"], 0)

    def test_sale_leaves_all_six_durable_findings_and_body_detail(self):
        events, offset = self.prepare([*[organic(v) for v in VARIANTS],
            {"event": "SellOrganicData", "timestamp": "2026-09-04T13:16:32Z",
             "BioData": [{"Variant_Localised": v} for v in VARIANTS]}])
        self.db.apply_commander_journal_delta(self.commander, self.journal, events, offset)
        self.assertEqual(self.db.commander_summary(self.commander)["unsold_biology"]["findings"], 0)
        self.assertEqual(len(self.findings()), 6)
        self.assert_detail()

    def assert_detail(self):
        self.db.store_snapshot({"system": "Prua Hypai RB-D c29-73", "system_address": ADDRESS,
            "system_bodies": [{"body_id": 51, "name": NAME, "biological_signals": 6,
                               "planet_class": "Rocky body", "body_type": "Planet"}]}, self.commander)
        body = self.db.chronicle_system_details(ADDRESS, self.commander)["bodies"][0]
        language = get_language()
        set_language("de")
        try:
            dialog = BodyDetailWindow(body)
            labels = [label.text() for label in dialog.findChildren(QLabel)]
            self.assertTrue(any(text.startswith("6 von 6") for text in labels), labels)
            self.assertFalse(any("noch nicht identifiziert" in text for text in labels))
            dialog.close()
        finally:
            set_language(language)

    def test_body_id_takes_precedence_and_commanders_systems_bodies_are_separate(self):
        events, offset = self.prepare([organic(), organic(BodyID=52),
                                      organic(SystemAddress=99), organic(Body="51")])
        self.db.apply_commander_journal_delta(self.commander, self.journal, events, offset)
        self.db.apply_commander_journal_delta(self.other, self.folder / "other.log",
                                             [organic()], offset)
        self.assertEqual(len(self.findings()), 1)
        self.assertEqual(len(self.findings(body=52)), 1)
        self.assertEqual(len(self.findings(address=99)), 1)
        self.assertEqual(len(self.findings(commander=self.other)), 1)

    def test_backfill_preview_backup_only_missing_rows_and_repeat(self):
        self.prepare([organic(v, progress=p) for v in VARIANTS
                      for p in ("Log", "Sample", "Analyse")], already_read=True)
        self.db.store_biology(ADDRESS, 51, "Fungoida", "Fungoida Setisis", VARIANTS[0],
                             "Analyse", "2026-09-04T12:30:00Z", self.commander)
        before = contents(self.db.path)
        self.assertEqual(len(self.backfill()["missing"]), 5)
        self.assertEqual(contents(self.db.path), before)
        result = self.backfill(apply=True)
        self.assertEqual(result["inserted"], 5)
        self.assertEqual(contents(result["backup"]), before)
        after = contents(self.db.path)
        for table in before:
            if table != "biology":
                self.assertEqual(after[table], before[table], table)
        self.assertTrue(all(row in after["biology"] for row in before["biology"]))
        self.assertEqual(len(self.findings()), 6)
        again = self.backfill(apply=True)
        self.assertEqual(again["inserted"], 0)
        self.assertIsNone(again["backup"])
        self.assertEqual(contents(self.db.path), after)
        self.assert_detail()

    def test_backfill_scope_does_not_insert_other_body_system_or_commander(self):
        self.prepare([organic(), organic(BodyID=52), organic(SystemAddress=99)], already_read=True)
        result = self.backfill(apply=True, system_address=ADDRESS, body_id=51)
        self.assertEqual(result["inserted"], 1)
        self.assertEqual(self.findings(body=52), [])
        self.assertEqual(self.findings(address=99), [])
        self.assertEqual(self.findings(commander=self.other), [])

    def test_backfill_rejects_changed_identity_and_unread_or_truncated_prefix(self):
        self.prepare([organic()])
        with self.assertRaises(ValueError):
            self.backfill(apply=True)
        self.prepare([organic()], already_read=True)
        raw = self.journal.read_text()
        self.journal.write_text(raw.replace("F12520967", "F00000000"))
        with self.assertRaises(ValueError):
            self.backfill(apply=True)
        self.journal.write_text(raw[:-2])
        with self.assertRaises(ValueError):
            self.backfill(apply=True)
        self.assertEqual(self.findings(), [])

    def test_backfill_does_not_read_beyond_committed_offset(self):
        self.prepare([organic()], already_read=True)
        with self.journal.open("a") as handle:
            handle.write(json.dumps(organic(VARIANTS[1])) + "\n")
        self.assertEqual(self.backfill(apply=True)["inserted"], 1)

    def test_delta_biology_and_offset_roll_back_together(self):
        events, offset = self.prepare([organic()])
        before = contents(self.db.path)
        real_store = self.db.store_biology
        def fail_after_store(*args, **kwargs):
            real_store(*args, **kwargs)
            raise RuntimeError("interrupted delta")
        with patch.object(self.db, "store_biology", side_effect=fail_after_store):
            with self.assertRaises(RuntimeError):
                self.db.apply_commander_journal_delta(self.commander, self.journal, events, offset)
        self.assertEqual(contents(self.db.path), before)

    def test_archive_import_still_records_six_species_and_is_repeatable(self):
        self.prepare([organic(v, progress=p) for v in VARIANTS
                      for p in ("Log", "Sample", "Analyse")])
        self.db.import_journal_archive(self.folder)
        self.assertEqual(len(self.findings()), 6)
        self.assertTrue(all(r["scan_type"] == "Analyse" for r in self.findings()))
        before = self.findings()
        self.db.import_journal_archive(self.folder)
        self.assertEqual(self.findings(), before)

    def test_revisit_empty_or_partial_live_biology_keeps_six_known_species(self):
        events, offset = self.prepare([organic(v) for v in VARIANTS])
        self.db.apply_commander_journal_delta(self.commander, self.journal, events, offset)
        self.assert_detail()
        state = SimpleNamespace(database=self.db, commander_id=self.commander,
                                system_address=ADDRESS)
        for live in ([], [{**self.findings()[0], "scan_type": "Log"}]):
            current = {"body_id": 51, "biology": live}
            result = AppState._own_explorer_bodies(state, [current])[0]
            self.assertEqual(len(result["biology"]), 6)
            self.assertTrue(all(item["scan_type"] == "Analyse" for item in result["biology"]))
            self.assertEqual(current["biology"], live)


if __name__ == "__main__":
    unittest.main()
