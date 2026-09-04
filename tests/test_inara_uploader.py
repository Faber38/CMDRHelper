import io
import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.inara_uploader import (
    header_presentation as inara_header_presentation,
    map_journal_event,
    upload_batch,
)


class Reply:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return json.dumps(self.payload).encode()


class InaraMappingTests(unittest.TestCase):
    def setUp(self):
        self.context = {"system": "Sol", "station": "Galileo",
                        "ship_type": "CobraMkIII", "ship_id": 7}

    def mapped(self, event, **values):
        return map_journal_event({"timestamp": "2026-09-04T10:00:00Z",
                                  "event": event, **values}, self.context)

    def test_travel_mappings(self):
        name, data = self.mapped("FSDJump", StarSystem="Achenar",
                                 StarPos=[1, 2, 3], JumpDist=12.5)
        self.assertEqual(name, "addCommanderTravelFSDJump")
        self.assertEqual(data["starsystemName"], "Achenar")
        self.assertEqual(data["jumpDistance"], 12.5)
        self.assertEqual(self.mapped("Docked", StarSystem="Sol",
                                     StationName="Galileo")[0], "addCommanderTravelDock")
        self.assertEqual(self.mapped("Touchdown", Body="Sol A 1",
                                     Latitude=1.2, Longitude=3.4)[0],
                         "addCommanderTravelLand")
        self.assertEqual(self.mapped("Location", StarSystem="Sol")[0],
                         "setCommanderTravelLocation")

    def test_mission_mappings(self):
        name, data = self.mapped("MissionAccepted", MissionID=42,
                                 Name="Mission_Delivery", DestinationSystem="Lave")
        self.assertEqual((name, data["missionGameID"]), ("addCommanderMission", 42))
        expected = {"MissionCompleted": "setCommanderMissionCompleted",
                    "MissionFailed": "setCommanderMissionFailed",
                    "MissionAbandoned": "setCommanderMissionAbandoned"}
        for journal, inara in expected.items():
            self.assertEqual(self.mapped(journal, MissionID=42)[0], inara)

    def test_ship_mappings(self):
        self.assertEqual(self.mapped("ShipyardNew", ShipType="adder", ShipID=8)[0],
                         "addCommanderShip")
        self.assertEqual(self.mapped("ShipyardSell", ShipType="adder", SellShipID=8)[0],
                         "delCommanderShip")


class InaraOutboxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = CMDRDatabase(Path(self.temp.name) / "test.db")
        with self.db._connect() as con:
            con.execute("INSERT INTO commanders(id,fid,current_name) VALUES(1,'F-A','Alpha')")
            con.execute("INSERT INTO commanders(id,fid,current_name) VALUES(2,'F-B','Beta')")
            con.execute("""INSERT INTO journal_sessions(journal_file,commander_id,
                attribution_status,last_read_offset) VALUES('a.log',1,'identified',0)""")
    def tearDown(self):
        self.temp.cleanup()

    def event(self):
        return {"timestamp": "2026-09-04T10:00:00Z", "event": "FSDJump",
                "StarSystem": "Lave", "JumpDist": 5.0}

    def test_enabled_disabled_and_deduplicated_atomic_enqueue(self):
        self.db.apply_commander_journal_delta(1, "a.log", [self.event()], 100,
                                               enqueue_inara=False)
        self.assertEqual(self.db.inara_pending(1), [])
        with self.db._connect() as con:
            con.execute("UPDATE journal_sessions SET last_read_offset=0 WHERE journal_file='a.log'")
        self.db.apply_commander_journal_delta(1, "a.log", [self.event()], 100,
                                               enqueue_inara=True)
        with self.db._connect() as con:
            con.execute("UPDATE journal_sessions SET last_read_offset=0 WHERE journal_file='a.log'")
        self.db.apply_commander_journal_delta(1, "a.log", [self.event()], 100,
                                               enqueue_inara=True)
        self.assertEqual(len(self.db.inara_pending(1)), 1)
        self.assertEqual(self.db.inara_pending(2), [])

    def test_failure_does_not_change_journal_offset_and_retry_can_succeed(self):
        self.db.apply_commander_journal_delta(1, "a.log", [self.event()], 100,
                                               enqueue_inara=True)
        row = self.db.inara_pending(1)[0]
        self.db.update_inara_outbox(errors={row["id"]: "timeout"})
        with self.db._connect() as con:
            offset = con.execute("SELECT last_read_offset FROM journal_sessions").fetchone()[0]
            status = con.execute("SELECT status,retry_count FROM inara_outbox").fetchone()
        self.assertEqual(offset, 100)
        self.assertEqual(status, ("error", 1))
        self.db.update_inara_outbox(sent_ids=[row["id"]])
        with self.db._connect() as con:
            self.assertEqual(con.execute("SELECT status FROM inara_outbox").fetchone()[0], "sent")


class InaraTransportTests(unittest.TestCase):
    rows = [{"id": 1, "event_name": "addCommanderTravelFSDJump",
             "event_timestamp": "2026-09-04T10:00:00Z",
             "event_data": {"starsystemName": "Lave"}},
            {"id": 2, "event_name": "setCommanderMissionFailed",
             "event_timestamp": "2026-09-04T10:01:00Z",
             "event_data": {"missionGameID": 42}}]

    def test_batch_partial_failure_and_real_identity_header(self):
        captured = {}
        def opener(request, timeout):
            captured.update(json.loads(request.data))
            self.assertEqual(timeout, 30)
            return Reply({"header": {"eventStatus": 200}, "events": [
                {"eventCustomID": 1, "eventStatus": 200},
                {"eventCustomID": 2, "eventStatus": 400,
                 "eventStatusText": "bad event"}]})
        sent, failed = upload_batch("TOPSECRET", "Alpha", "F-A", self.rows,
                                    opener=opener)
        self.assertEqual(sent, [1])
        self.assertIn(2, failed)
        self.assertEqual(captured["header"]["commanderName"], "Alpha")
        self.assertEqual(captured["header"]["commanderFrontierID"], "F-A")

    def test_api_key_never_logged_on_timeout(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = logging.getLogger("cmdrhelper.inara_uploader")
        logger.addHandler(handler)
        try:
            with self.assertRaises(RuntimeError):
                upload_batch("TOPSECRET", "Alpha", "F-A", self.rows,
                             opener=lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError()))
        finally:
            logger.removeHandler(handler)
        self.assertNotIn("TOPSECRET", stream.getvalue())

    def test_header_statuses(self):
        self.assertEqual(inara_header_presentation("disabled")[0], "topbar.inara_off")
        for status in ("waiting", "uploading", "ok", "error"):
            self.assertIn(status, inara_header_presentation(status)[0])


if __name__ == "__main__":
    unittest.main()
