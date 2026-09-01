from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from cmdrhelper.journal_reader import read_latest_state
from cmdrhelper.route_planner.models import ShipLoadoutData


def write_journal(folder: Path, stamp: str, events: list[dict]) -> Path:
    path = folder / f"Journal.{stamp}.01.log"
    path.write_text(
        "".join(json.dumps(event) + "\n" for event in events),
        encoding="utf-8",
    )
    return path


def event(event_type: str, second: int = 0, **values):
    return {
        "timestamp": f"2026-01-01T00:00:{second:02d}Z",
        "event": event_type,
        **values,
    }


def commander(fid: str, name: str, second: int = 0):
    return event("Commander", second, FID=fid, Name=name)


def commander_a_runtime():
    return [
        commander("F-A", "Alpha"),
        event(
            "Location", 1, StarSystem="Alpha System", SystemAddress=100,
            Body="Alpha System A 1", StationName="Alpha Station",
        ),
        event(
            "LoadGame", 2, FID="F-A", Commander="Alpha", ShipID=7,
            Ship="CobraMkIII", ShipName="Alpha Ship",
        ),
        event(
            "Loadout", 3, ShipID=7, Ship="CobraMkIII", ShipName="Alpha Ship",
            Modules=[],
        ),
        event(
            "MissionAccepted", 4, MissionID=77, Name="Mission_Delivery",
            LocalisedName="Alpha Mission", DestinationSystem="Alpha Target",
        ),
        event("FSSDiscoveryScan", 5, SystemAddress=100, BodyCount=1),
        event("FSSAllBodiesFound", 6, SystemAddress=100, Count=1),
        event(
            "Disembark", 7, SystemAddress=100, BodyID=1,
            Body="Alpha System A 1", OnPlanet=True,
        ),
        event(
            "Scan", 8, SystemAddress=100, BodyID=1,
            BodyName="Alpha System A 1", PlanetClass="Rocky body",
            WasDiscovered=False, WasMapped=False, WasFootfalled=False,
        ),
        event(
            "SAASignalsFound", 9, SystemAddress=100, BodyID=1,
            BodyName="Alpha System A 1",
            Signals=[{"Type": "$SAA_SignalType_Geological;", "Count": 2}],
        ),
        event(
            "SAAScanComplete", 10, SystemAddress=100, BodyID=1,
            ProbesUsed=2, EfficiencyTarget=4,
        ),
        event(
            "ScanOrganic", 11, SystemAddress=100, BodyID=1,
            ScanType="Analyse", Genus="Alpha genus", Species="Alpha species",
            Variant="Alpha variant",
        ),
    ]


class CommanderRuntimeReaderTests(unittest.TestCase):
    def test_switch_to_b_excludes_all_personal_a_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            write_journal(folder, "2026-01-01T000000", commander_a_runtime())
            write_journal(folder, "2026-01-01T000100", [
                commander("F-B", "Bravo"),
                event(
                    "LoadGame", 1, FID="F-B", Commander="Bravo", ShipID=7,
                    Ship="SideWinder", ShipName="Bravo Ship",
                ),
            ])
            state = read_latest_state(folder)

        self.assertEqual(state["commander_fid"], "F-B")
        self.assertEqual(state["missions"], [])
        self.assertEqual(state["system"], "")
        self.assertIsNone(state["system_address"])
        self.assertEqual(state["station"], "")
        self.assertEqual(state["body"], "")
        self.assertEqual(state["ship"], "Bravo Ship")
        self.assertEqual(state["ship_loadout"].ship_id, 7)
        self.assertEqual(state["ship_loadout"].ship_type, "SideWinder")
        self.assertNotEqual(state["ship_loadout"].ship_name, "Alpha Ship")
        self.assertEqual(state["system_bodies"], [])
        self.assertEqual(state["unsold_cartography_count"], 0)
        self.assertEqual(state["unsold_biology"], [])
        self.assertFalse(state["system_all_bodies_found"])

    def test_switch_a_to_b_to_a_restores_only_a_context(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            write_journal(folder, "2026-01-01T000000", commander_a_runtime())
            write_journal(folder, "2026-01-01T000100", [
                commander("F-B", "Bravo"),
                event(
                    "Location", 1, StarSystem="Bravo System", SystemAddress=200,
                ),
                event("MissionAccepted", 2, MissionID=77, Name="Bravo Mission"),
            ])
            write_journal(folder, "2026-01-01T000200", [
                commander("F-A", "Alpha Renamed"),
            ])
            state = read_latest_state(folder)

        self.assertEqual(state["commander_fid"], "F-A")
        self.assertEqual(state["commander"], "Alpha Renamed")
        self.assertEqual(state["system"], "Alpha System")
        self.assertEqual([mission["mission_id"] for mission in state["missions"]], [77])
        self.assertEqual(state["missions"][0]["name"], "Alpha Mission")
        self.assertEqual(state["ship_loadout"].ship_name, "Alpha Ship")
        self.assertEqual(state["unsold_cartography_count"], 1)
        self.assertEqual(len(state["unsold_biology"]), 1)
        self.assertTrue(state["system_bodies"][0]["self_mapped"])
        self.assertTrue(state["system_bodies"][0]["efficient_mapping"])
        self.assertTrue(state["system_bodies"][0]["first_footfall"])
        self.assertEqual(state["system_bodies"][0]["geological_signals"], 2)
        self.assertTrue(state["system_all_bodies_found"])

    def test_same_fid_name_change_does_not_reset_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            write_journal(folder, "2026-01-01T000000", commander_a_runtime())
            write_journal(folder, "2026-01-01T000100", [
                commander("F-A", "Alpha Renamed"),
            ])
            state = read_latest_state(folder)

        self.assertEqual(state["commander"], "Alpha Renamed")
        self.assertEqual(state["system"], "Alpha System")
        self.assertEqual(len(state["missions"]), 1)
        self.assertEqual(state["ship_loadout"].ship_name, "Alpha Ship")

    def test_unknown_and_ambiguous_sessions_add_no_personal_runtime(self):
        for suffix, identity in (
            ("unknown", []),
            ("ambiguous", [commander("F-B", "Bravo"), commander("F-C", "Charlie", 1)]),
        ):
            with self.subTest(status=suffix), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                write_journal(folder, "2026-01-01T000000", commander_a_runtime())
                write_journal(folder, "2026-01-01T000100", identity + [
                    event(
                        "Location", 2, StarSystem="Foreign System", SystemAddress=999,
                    ),
                    event("MissionAccepted", 3, MissionID=999, Name="Foreign Mission"),
                    event(
                        "Loadout", 4, ShipID=99, Ship="Anaconda",
                        ShipName="Foreign Ship", Modules=[],
                    ),
                    event(
                        "Scan", 5, SystemAddress=999, BodyID=1,
                        BodyName="Foreign System 1", PlanetClass="Icy body",
                    ),
                    event(
                        "ScanOrganic", 6, SystemAddress=999, BodyID=1,
                        ScanType="Analyse", Genus="Foreign", Species="Foreign",
                    ),
                ])
                state = read_latest_state(folder)

            self.assertEqual(state["commander_fid"], "F-A")
            self.assertEqual(state["system"], "Alpha System")
            self.assertEqual([m["mission_id"] for m in state["missions"]], [77])
            self.assertEqual(state["ship_loadout"].ship_name, "Alpha Ship")
            self.assertNotEqual(state["system_address"], 999)
            self.assertTrue(all(body["name"] != "Foreign System 1" for body in state["system_bodies"]))

    def test_single_commander_runtime_still_builds_normally(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            write_journal(folder, "2026-01-01T000000", commander_a_runtime())
            state = read_latest_state(folder)

        self.assertEqual(state["commander_fid"], "F-A")
        self.assertEqual(state["system"], "Alpha System")
        self.assertEqual(len(state["missions"]), 1)
        self.assertEqual(state["ship_loadout"].ship_id, 7)
        self.assertEqual(state["unsold_cartography_count"], 1)
        self.assertEqual(len(state["unsold_biology"]), 1)


class AppStateRuntimeResetTests(unittest.TestCase):
    def test_central_reset_invalidates_personal_runtime_only(self):
        from cmdrhelper.state import AppState

        global_database = object()
        state = SimpleNamespace(
            database=global_database,
            commander="Alpha",
            system="Alpha System",
            system_address=100,
            body="A 1",
            station="Station",
            ship="Alpha Ship",
            ship_loadout=ShipLoadoutData(ship_id=7, ship_name="Alpha Ship"),
            last_timestamp="timestamp",
            missions=[object()],
            system_bodies=[{"self_mapped": True}],
            system_body_count=1,
            system_signals_count=2,
            system_all_bodies_found=True,
            system_scan_value=1,
            system_mapped_value=2,
            system_current_value=3,
            system_high_value_count=1,
            system_bio_completed_count=1,
            system_bio_value=2,
            system_bio_first_logged_value=3,
            system_bio_unknown=["x"],
            unsold_cartography_value=4,
            unsold_cartography_count=1,
            unsold_bio_value=5,
            unsold_bio_first_logged_value=6,
            unsold_bio_count=1,
            unsold_bio_unknown=["y"],
            edsm_body_count=3,
            edsm_added_count=2,
            edsm_source_status="cached",
            _edsm_request_system="Alpha System",
        )

        AppState.reset_commander_runtime_state(state)

        self.assertIs(state.database, global_database)
        self.assertEqual(state.missions, [])
        self.assertEqual(state.system, "")
        self.assertIsNone(state.system_address)
        self.assertEqual(state.ship, "")
        self.assertIsNone(state.ship_loadout.ship_id)
        self.assertEqual(state.system_bodies, [])
        self.assertEqual(state.unsold_cartography_count, 0)
        self.assertEqual(state.unsold_bio_count, 0)


if __name__ == "__main__":
    unittest.main()
