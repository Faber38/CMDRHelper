import json
import tempfile
import unittest
from pathlib import Path

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.ui.system_view import SystemMapWidget


ADDRESS = 27092519302129
SYSTEM = "Prua Hypai HI-G b58-12"
BODY = f"{SYSTEM} 1"


class BodySnapshotPreservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = CMDRDatabase(self.root / "test.db")
        self.commander_id = self.db.upsert_commander("F12520967", "FABER38")

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def scan(**changes):
        body = {
            "body_id": 1, "name": BODY, "short_name": "1",
            "body_type": "Planet", "star_type": "",
            "planet_class": "Rocky ice body", "radius_m": 1269296.375,
            "landable": True, "terraformable": False,
            "biological_signals": 0, "geological_signals": 0,
            "planetary_mining_signals": None,
        }
        body.update(changes)
        return {"system_address": ADDRESS, "system": SYSTEM,
                "last_timestamp": "2026-09-02T18:05:46Z",
                "system_bodies": [body]}

    def row(self):
        with self.db._connect() as con:
            return con.execute(
                """SELECT short_name,body_type,planet_class,radius_m,landable,
                          biological_signals,geological_signals,
                          planetary_mining_signals
                   FROM bodies WHERE system_address=? AND body_id=1""",
                (ADDRESS,),
            ).fetchone()

    def test_fss_placeholder_updates_signals_without_losing_scan(self):
        self.db.store_snapshot(self.scan(), self.commander_id)
        placeholder = self.scan(
            name=BODY, short_name=BODY, body_type="", planet_class="",
            radius_m=None, landable=False, biological_signals=3,
            geological_signals=4, planetary_mining_signals=17,
            _placeholder=True,
        )
        self.db.store_snapshot(placeholder, self.commander_id)
        self.assertEqual(
            self.row(),
            ("1", "Planet", "Rocky ice body", 1269296.375, 1, 3, 4, 17),
        )

    def test_saa_placeholder_updates_mining_count_without_losing_scan(self):
        self.db.store_snapshot(self.scan(), self.commander_id)
        self.db.store_snapshot(self.scan(
            short_name=BODY, body_type="", planet_class="", radius_m=None,
            landable=False, planetary_mining_signals=17, _placeholder=True,
        ), self.commander_id)
        self.assertEqual(self.row()[0:5],
                         ("1", "Planet", "Rocky ice body", 1269296.375, 1))
        self.assertEqual(self.row()[7], 17)

    def test_general_upsert_rejects_empty_values_and_full_name_short_name(self):
        self.db.store_snapshot(self.scan(), self.commander_id)
        self.db.store_snapshot(self.scan(
            short_name=BODY, body_type="", planet_class="", landable=False,
        ), self.commander_id)
        self.assertEqual(self.row()[0:5],
                         ("1", "Planet", "Rocky ice body", 1269296.375, 1))

    def test_later_complete_scan_can_improve_values(self):
        self.db.store_snapshot(self.scan(
            planet_class="Rocky body", radius_m=1000, landable=False,
        ), self.commander_id)
        self.db.store_snapshot(self.scan(), self.commander_id)
        self.assertEqual(self.row()[0:5],
                         ("1", "Planet", "Rocky ice body", 1269296.375, 1))

    def test_real_body_reconstruction_is_idempotent_and_preserves_mining(self):
        self.db.store_snapshot(self.scan(
            short_name=BODY, body_type="", planet_class="", radius_m=None,
            landable=False, planetary_mining_signals=17,
        ), self.commander_id)
        journal = self.root / "Journal.real.log"
        events = [
            {"timestamp": "2026-09-02T18:00:00Z", "event": "FSDJump",
             "StarSystem": SYSTEM, "SystemAddress": ADDRESS},
            {"timestamp": "2026-09-02T18:05:46Z", "event": "Scan",
             "BodyName": BODY, "BodyID": 1, "SystemAddress": ADDRESS,
             "PlanetClass": "Rocky ice body", "Landable": True,
             "Radius": 1269296.375},
        ]
        journal.write_text("".join(json.dumps(item) + "\n" for item in events),
                           encoding="utf-8")
        size = journal.stat().st_size
        session = {
            "journal_file": str(journal), "attribution_status": "identified",
            "fid_seen": "F12520967", "commander_name_seen": "FABER38",
            "file_size": size, "modified_ns": journal.stat().st_mtime_ns,
            "last_read_offset": size, "last_complete_line_offset": size,
            "last_indexed_at": "2026-09-02T18:06:00Z",
        }
        self.db.store_journal_session(session)
        session["commander_id"] = self.commander_id

        result = self.db.backfill_body_scan_attributes(
            self.commander_id, [session])
        self.assertEqual(result["events"], 1)
        self.assertEqual(self.row(),
                         ("1", "Planet", "Rocky ice body", 1269296.375,
                          1, 0, 0, 17))
        self.assertEqual(SystemMapWidget._body_image_name({
            "body_type": "Planet", "planet_class": self.row()[2],
        }), "planet_rocky_ice.png")
        self.assertTrue((Path("cmdrhelper/assets/bodies")
                         / "planet_rocky_ice.png").is_file())
        self.assertTrue(self.db.backfill_body_scan_attributes(
            self.commander_id, [session])["skipped"])


if __name__ == "__main__":
    unittest.main()
