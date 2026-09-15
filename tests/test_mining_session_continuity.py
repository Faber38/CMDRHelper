"""Session boundaries must preserve evidence, never turn old values into guesses."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from PySide6.QtCore import QSettings

from cmdrhelper.mining_carrier import CarrierLedger, read_carrier_feed
from cmdrhelper.mining_inventory import MiningInventoryReader


def cargo(vessel, count):
    return dict(event="Cargo", Vessel=vessel, Count=count,
                Inventory=[dict(Name="gold", Count=count)] if count else [])


def login(ship_id=1, fid="F1", ship="CobraMkIII"):
    return [dict(event="Commander", FID=fid),
            dict(event="LoadGame", FID=fid, Ship=ship, ShipID=ship_id)]


def transfer(count, direction="toship", **extra):
    return dict(event="CargoTransfer", Transfers=[dict(Type="gold", Count=count,
                                                      Direction=direction)], **extra)


class MiningSessionContinuityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.ini = str(self.folder / "settings.ini")
        self.settings = QSettings(self.ini, QSettings.Format.IniFormat)
        self.store = CarrierLedger(self.settings)
        self.paths, self.sessions = [], []
        self.first_events = login() + [cargo("Ship", 48), dict(event="LaunchSRV"),
                                      cargo("SRV", 20),
                                      dict(event="Docked", MarketID=123, StationType="FleetCarrier")]
        self.add_session(self.first_events)
        self.initial = self.read()
        self.store.confirm("F1", 123, "gold", 504, self.feed())

    def add_session(self, events, name=None, fid="F1", status="identified"):
        name = name or f"Journal.2026-09-{12 + len(self.paths):02}T120000.01.log"
        path = self.folder / name
        path.write_text("".join(json.dumps(event) + "\n" for event in events))
        self.paths.append(path)
        self.sessions.append(dict(journal_file=str(path), commander_id=1,
                                  fid_seen=fid, attribution_status=status))
        return path

    def append(self, path, *events):
        with path.open("a") as stream:
            for event in events:
                stream.write(json.dumps(event) + "\n")

    def feed(self):
        return read_carrier_feed(self.paths[-1], "F1")

    def read(self, checkpoints=None, sessions=None):
        return MiningInventoryReader().reconstruct(1, "F1", self.sessions if sessions is None else sessions,
            checkpoints=checkpoints, live_path=self.paths[-1])

    def update(self):
        return self.store.update("F1", 123, self.feed(), sessions=self.sessions)

    def test_helper_restart_and_same_ship_session_then_zero_are_independent(self):
        self.store = CarrierLedger(QSettings(self.ini, QSettings.Format.IniFormat))
        restored = self.read(self.initial.checkpoints)
        self.store.attach(restored, self.update())
        self.assertEqual(restored.stock("gold"), (20, 48, 504, 572))
        self.add_session(login())
        restored = self.read(restored.checkpoints)
        self.store.attach(restored, self.update())
        self.assertEqual(restored.stock("gold"), (20, 48, 504, 572))
        self.append(self.paths[-1], cargo("Ship", 0))
        restored = self.read(restored.checkpoints)
        self.store.attach(restored, self.update())
        self.assertEqual(restored.stock("gold"), (20, 0, 504, 524))
        # A fresh reader and settings object have no in-memory vehicle state.
        self.store = CarrierLedger(QSettings(self.ini, QSettings.Format.IniFormat))
        again = self.read(restored.checkpoints)
        self.store.attach(again, self.update())
        self.assertEqual(again.stock("gold"), (20, 0, 504, 524))

    def test_known_ship_and_known_srv_remain_independent(self):
        for vessel in ("Ship", "SRV"):
            with self.subTest(vessel=vessel):
                self.paths[0].write_text("".join(json.dumps(e) + "\n" for e in login() + [cargo(vessel, 20)]))
                result = self.read()
                self.assertEqual(result.stock("gold")[:2], (20, None) if vessel == "SRV" else (None, 20))
                self.assertIsNone(result.stock("gold").total_amount)

    def test_ship_change_invalidates_old_vehicle_context_but_keeps_confirmation(self):
        self.add_session(login(ship_id=2) + [cargo("Ship", 0)])
        result = self.read(self.initial.checkpoints)
        self.store.attach(result, self.update())
        self.assertEqual(result.stock("gold"), (None, 0, 504, None))
        self.assertEqual(result.vehicle_records["SRV"]["last_confirmed"], {"gold": 20})
        self.assertEqual(result.vehicle_records["SRV"]["status"], "unknown")
        self.assertEqual(result.vehicle_records["Ship"]["last_confirmed"], {})

    def test_missing_ship_identity_and_srv_login_do_not_guess_mothership(self):
        for events in (login(ship_id=None), login(ship="mev_rhino", ship_id=42),
                       login(ship="lander01", ship_id=1)):
            with self.subTest(events=events):
                self.paths[0].write_text("".join(json.dumps(e) + "\n" for e in self.first_events + events))
                result = self.read(self.initial.checkpoints)
                self.assertEqual(result.stock("gold")[:2], (None, None))
                self.assertEqual(result.vehicle_records["Ship"]["last_confirmed"], {"gold": 48})

    def test_conflicting_loadout_or_invalid_ship_id_cannot_prove_continuity(self):
        for events in ([dict(event="Loadout", ShipID=1, Ship="Anaconda")],
                       login(ship_id=True), login(ship_id=-1)):
            with self.subTest(events=events):
                self.paths[0].write_text("".join(json.dumps(e) + "\n" for e in self.first_events + events))
                result = self.read(self.initial.checkpoints)
                self.assertEqual(result.stock("gold")[:2], (None, None))
                self.assertEqual(result.vehicle_records["Ship"]["last_confirmed"], {"gold": 48})

    def test_srv_launch_destruction_and_docking_require_fresh_evidence(self):
        for event in (dict(event="LaunchSRV", ID=99, SRVType="testbuggy"),
                      dict(event="SRVDestroyed"), dict(event="DockSRV")):
            with self.subTest(event=event):
                self.paths[0].write_text("".join(json.dumps(e) + "\n" for e in self.first_events + [event]))
                result = self.read(self.initial.checkpoints)
                self.assertIsNone(result.srv)
                self.assertEqual(result.vehicle_records["SRV"]["last_confirmed"], {"gold": 20})
                if event["event"] != "DockSRV":
                    self.assertEqual(result.ship, {"gold": 48})

    def test_commander_and_carrier_identity_never_share_balances(self):
        self.add_session(login(fid="F2") + [cargo("Ship", 8)], fid="F2")
        result = MiningInventoryReader().reconstruct(2, "F2", [dict(self.sessions[-1], commander_id=2)],
            checkpoints=self.initial.checkpoints, live_path=self.paths[-1])
        self.assertEqual(result.stock("gold"), (None, 8, None, None))
        self.assertNotIn("last_confirmed", result.vehicle_records["SRV"])
        self.assertEqual(self.store.update("F2", 123, read_carrier_feed(self.paths[-1], "F2"))["records"], {})
        self.assertEqual(self.store.update("F1", 999, None)["records"], {})
        self.assertEqual(self.store._load("F1", 123)["records"]["gold"]["count"], 504)

    def test_cross_session_tail_and_multiple_transfers_are_applied_exactly_once(self):
        # The old session remains active in the SRV: explicitly return to Ship.
        self.append(self.paths[0], cargo("Ship", 48), transfer(10))
        self.add_session(login() + [transfer(20, "tocarrier", CarrierID=123)])
        self.add_session(login() + [transfer(4, CarrierID=123)])
        first = self.update()
        self.assertEqual(first["records"]["gold"]["count"], 510)
        self.assertEqual(first["records"]["gold"]["last_confirmed"], 504)
        for _ in range(2):
            self.store = CarrierLedger(QSettings(self.ini, QSettings.Format.IniFormat))
            self.assertEqual(self.update(), first)

    def test_contiguous_parts_preserve_dock_context_across_refresh_and_restart(self):
        self.append(self.paths[0], cargo("Ship", 48))
        self.add_session([dict(event="Fileheader", part=2), dict(event="Commander", FID="F1"),
                          dict(event="Docked", MarketID=123, StationType="FleetCarrier")],
                         "Journal.2026-09-12T120000.02.log")
        # This part has identity but no further docking context on the next read.
        self.update()
        self.append(self.paths[-1], transfer(10))
        self.store = CarrierLedger(QSettings(self.ini, QSettings.Format.IniFormat))
        self.assertEqual(self.update()["records"]["gold"]["count"], 494)

    def test_missing_index_anchor_stays_unknown_then_can_recover(self):
        old_anchor = deepcopy(self.store._load("F1", 123)["anchor"])
        self.add_session(login() + [transfer(10, CarrierID=123)])
        ledger = self.store.update("F1", 123, self.feed(), sessions=self.sessions[1:])
        self.assertIsNone(ledger["records"]["gold"]["count"])
        self.assertEqual(ledger["records"]["gold"]["last_confirmed"], 504)
        self.assertEqual(ledger["anchor"], old_anchor)
        self.store = CarrierLedger(QSettings(self.ini, QSettings.Format.IniFormat))
        self.assertEqual(self.update()["records"]["gold"]["count"], 494)
        self.assertEqual(self.update()["records"]["gold"]["count"], 494)

    def test_invalid_prefix_and_missing_part_do_not_bridge_gaps(self):
        original = self.paths[0].read_bytes()
        self.add_session(login(), "Journal.2026-09-12T120000.03.log")
        ledger = self.update()
        self.assertIsNone(ledger["records"]["gold"]["count"])
        self.assertEqual(ledger["records"]["gold"]["last_confirmed"], 504)
        self.assertEqual(self.read(self.initial.checkpoints).stock("gold")[:2], (None, None))
        self.paths.pop()
        self.sessions.pop()
        self.paths[0].write_bytes(original.replace(b'"Count": 48', b'"Count": 49'))
        self.assertIsNone(self.update()["records"]["gold"]["count"])
        self.paths[0].write_bytes(original)
        self.assertEqual(self.update()["records"]["gold"]["count"], 504)

    def test_unreadable_or_unidentified_intermediate_session_is_a_gap(self):
        middle = self.add_session(login())
        self.add_session(login() + [cargo("Ship", 0)])
        for failure in ("missing", "ambiguous", "partial"):
            with self.subTest(failure=failure):
                middle.write_text("".join(json.dumps(e) + "\n" for e in login()))
                self.sessions[1]["attribution_status"] = "identified"
                if failure == "missing":
                    middle.unlink()
                elif failure == "ambiguous":
                    self.sessions[1]["attribution_status"] = "ambiguous"
                else:
                    with middle.open("ab") as stream:
                        stream.write(b'{"event":"CargoTransfer"')
                result = self.read(self.initial.checkpoints)
                self.assertEqual(result.stock("gold")[:2], (None, 0))
                ledger = self.update()
                self.assertIsNone(ledger["records"]["gold"]["count"])
                self.assertEqual(ledger["records"]["gold"]["last_confirmed"], 504)

    def test_later_read_failure_rolls_back_tentative_transfers_before_retry(self):
        self.append(self.paths[0], cargo("Ship", 48), transfer(10))
        middle = self.add_session(login() + [transfer(20, "tocarrier", CarrierID=123)])
        raw = middle.read_bytes()
        self.add_session(login())
        middle.unlink()
        ledger = self.update()
        self.assertIsNone(ledger["records"]["gold"]["count"])
        self.assertEqual(ledger["records"]["gold"]["resume_count"], 504)
        middle.write_bytes(raw)
        self.assertEqual(self.update()["records"]["gold"]["count"], 514)
        self.assertEqual(self.update()["records"]["gold"]["count"], 514)

    def test_missing_vehicle_source_preserves_last_value_without_displaying_it(self):
        self.add_session(login() + [cargo("Ship", 0)])
        result = self.read(self.initial.checkpoints, sessions=self.sessions[1:])
        self.assertEqual(result.stock("gold")[:2], (None, 0))
        self.assertEqual(result.vehicle_records["SRV"]["last_confirmed"], {"gold": 20})
        restarted = self.read(result.checkpoints, sessions=self.sessions[1:])
        self.assertEqual(restarted.vehicle_records["SRV"], result.vehicle_records["SRV"])

    def test_truncated_vehicle_anchor_does_not_display_an_older_balance(self):
        self.append(self.paths[0], cargo("Ship", 51))
        confirmed = self.read(self.initial.checkpoints)
        raw = self.paths[0].read_bytes()
        self.paths[0].write_bytes(raw[:raw[:-1].rfind(b"\n") + 1])
        result = self.read(confirmed.checkpoints)
        self.assertEqual(result.stock("gold")[:2], (None, None))
        self.assertEqual(result.vehicle_records["Ship"]["last_confirmed"], {"gold": 51})
        self.paths[0].write_bytes(raw)
        recovered = self.read(result.checkpoints)
        self.assertEqual(recovered.stock("gold")[:2], (20, 51))

    def test_ambiguous_transfer_cannot_be_repaired_by_unchanged_refresh(self):
        self.add_session(login() + [dict(event="Undocked"), transfer(10)])
        ledger = self.update()
        self.assertIsNone(ledger["records"]["gold"]["count"])
        self.assertEqual(ledger["records"]["gold"]["last_confirmed"], 504)
        self.append(self.paths[-1], transfer(100, "tocarrier", CarrierID=123))
        self.assertIsNone(self.update()["records"]["gold"]["count"])

    def test_new_manual_baseline_does_not_repair_other_commodities_after_gap(self):
        self.store.confirm("F1", 123, "copper", 20, self.feed())
        self.add_session(login())
        self.store.update("F1", 123, self.feed())  # No index: continuity still unresolved.
        ledger = self.store.confirm("F1", 123, "gold", 600, self.feed())
        for ledger in (ledger, self.update()):
            self.assertEqual(ledger["records"]["gold"]["count"], 600)
            self.assertIsNone(ledger["records"]["copper"]["count"])
            self.assertEqual(ledger["records"]["copper"]["last_confirmed"], 20)

    def test_legacy_carrier_settings_are_compatible_but_destroyed_values_stay_unknown(self):
        key = self.store.key("F1", 123)
        old = self.settings.value(key)
        old.pop("context", None)
        old["records"]["gold"].pop("last_confirmed")
        self.settings.setValue(key, old)
        self.add_session(login())
        ledger = self.update()
        self.assertEqual(ledger["records"]["gold"]["count"], 504)
        self.assertEqual(ledger["records"]["gold"]["last_confirmed"], 504)
        old["records"]["gold"].update(count=None, status="inconsistent")
        self.settings.setValue(key, old)
        ledger = self.update()
        self.assertIsNone(ledger["records"]["gold"]["count"])
        self.assertIsNone(ledger["records"]["gold"]["last_confirmed"])

    def test_legacy_vehicle_checkpoint_without_continuity_metadata_still_replays(self):
        full = dict(cargo("Ship", 48), timestamp="2026-09-12T12:00:02Z")
        trigger = {k: v for k, v in full.items() if k != "Inventory"}
        self.paths[0].write_text("".join(json.dumps(e) + "\n" for e in login() + [trigger]))
        sidecar = self.folder / "Cargo.json"
        sidecar.write_text(json.dumps(full))
        first = self.read()
        legacy = {k: v for k, v in first.checkpoints.items() if k != "continuity"}
        self.assertIn("Ship", legacy)
        sidecar.unlink()
        self.add_session(login())
        self.assertEqual(self.read(legacy).ship, {"gold": 48})

    def test_diagnostics_do_not_contain_journal_identity_or_content(self):
        self.add_session(login() + [transfer(4, CarrierID=123)])
        with self.assertLogs("cmdrhelper.mining_carrier", level="DEBUG") as logs:
            self.update()
        messages = "\n".join(logs.output)
        self.assertIn("continuity", messages)
        for private in ("F1", str(self.folder), "CobraMkIII", "504", "gold"):
            self.assertNotIn(private, messages)
