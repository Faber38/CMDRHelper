"""Synthetic, offline regressions for vehicle evidence and bounded checkpoints."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from cmdrhelper.mining_inventory import MiningInventoryReader, MiningReducer


def cargo(vessel="Ship", **stock):
    return dict(event="Cargo", Vessel=vessel, Count=sum(stock.values()),
                Inventory=[dict(Name=k, Count=v) for k, v in stock.items()])


class VehicleEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.reducer = MiningReducer(1, "F1")
        self.offset = 0
        self.apply(dict(event="LoadGame", FID="F1", Ship="lakonminer", ShipID=51))

    def apply(self, *events, journal="/source/Journal.2026-10-26T120000.01.log"):
        for event in events:
            self.offset += 1
            self.reducer.apply(event, (journal, self.offset))
        return self.reducer.result

    def test_count_before_refinement_reconciles_exactly_once(self):
        self.apply(cargo(gold=28), dict(event="LaunchSRV", ID=52), cargo("SRV", monazite=46))
        trigger = dict(event="Cargo", Vessel="SRV", Count=47, timestamp="2026-10-26T11:24:24Z")
        result = self.apply(trigger)
        self.assertIsNone(result.srv)
        result = self.apply(dict(event="MiningRefined", Type="$monazite_name;", timestamp=trigger["timestamp"]))
        self.assertEqual(result.srv, {"monazite": 47})
        self.assertEqual(result.vehicle_records["SRV"]["quality"], "tracked")
        self.reducer.apply(dict(event="MiningRefined", Type="monazite"),
                           ("/source/Journal.2026-10-26T120000.01.log", self.offset))
        self.assertEqual(result.srv, {"monazite": 47})
        self.assertEqual(result.ship, {"gold": 28})

    def test_full_snapshot_before_refinement_not_double_counted(self):
        self.apply(cargo(gold=46))
        self.apply(dict(cargo(gold=47), timestamp="2026-10-26T11:24:24Z"))
        result = self.apply(dict(event="MiningRefined", Type="gold", timestamp="2026-10-26T11:24:24Z"))
        self.assertEqual(result.ship, {"gold": 47})

    def test_mismatched_composition_and_unexplained_count_are_not_accepted(self):
        self.apply(cargo(gold=46), dict(cargo(silver=47), timestamp="2026-10-26T11:24:24Z"))
        result = self.apply(dict(event="MiningRefined", Type="gold", timestamp="2026-10-26T11:24:24Z"))
        self.assertIsNone(result.ship)
        self.apply(cargo(gold=45), dict(cargo(gold=47), timestamp="2026-10-26T11:24:24Z"))
        result = self.apply(dict(event="MiningRefined", Type="gold", timestamp="2026-10-26T11:24:24Z"))
        self.assertIsNone(result.ship)  # A multi-tonne leading snapshot is ambiguous.
        for count, stamp in ((48, "2026-10-26T11:24:24Z"), (47, "2026-10-26T11:24:25Z")):
            self.apply(cargo(gold=46), dict(event="Cargo", Vessel="Ship", Count=count,
                                          timestamp="2026-10-26T11:24:24Z"))
            self.assertIsNone(self.apply(dict(event="MiningRefined", Type="gold", timestamp=stamp)).ship)

    def test_no_baseline_or_intervening_mutation_cannot_reconcile(self):
        trigger = dict(event="Cargo", Vessel="Ship", Count=47, timestamp="2026-10-26T11:24:24Z")
        refined = dict(event="MiningRefined", Type="gold", timestamp=trigger["timestamp"])
        self.assertIsNone(self.apply(trigger, refined).ship)
        self.apply(cargo(gold=46), trigger, dict(event="EjectCargo", Type="gold", Count=1))
        self.assertIsNone(self.apply(refined).ship)
        self.apply(cargo(gold=46), dict(trigger, Inventory=[dict(Name="gold", Count=-1)]))
        self.assertIsNone(self.apply(refined).ship)

    def test_empty_srv_dock_preserves_ship_then_relaunch(self):
        self.apply(cargo(gold=28), dict(event="LaunchSRV", ID=52), cargo("SRV"))
        result = self.apply(dict(event="DockSRV", ID=52), dict(event="LaunchSRV", ID=52))
        self.assertEqual(result.ship, {"gold": 28})
        self.assertIsNone(result.srv)

    def test_loaded_srv_dock_requires_corroborating_ship_count(self):
        self.apply(cargo(gold=28), dict(event="LaunchSRV", ID=52), cargo("SRV", gold=4))
        result = self.apply(dict(event="DockSRV", ID=52))
        self.assertIsNone(result.ship)
        self.assertEqual(result.displayed_stock("Ship", "gold"), (28, "stale"))
        result = self.apply(dict(event="Loadout", Ship="lakonminer", ShipID=51),
                            dict(event="Cargo", Vessel="Ship", Count=32))
        self.assertEqual(result.ship, {"gold": 32})
        self.assertEqual(result.vehicle_records["Ship"]["quality"], "tracked")

    def test_dock_with_unknown_srv_does_not_guess_unloading(self):
        self.apply(cargo(gold=28), dict(event="LaunchSRV", ID=52), dict(event="DockSRV", ID=52))
        result = self.apply(dict(event="Cargo", Vessel="Ship", Count=32))
        self.assertIsNone(result.ship)
        result.carrier = {"gold": 100}
        self.assertEqual(result.displayed_stock("Ship", "gold"), (28, "stale"))
        self.assertIsNone(result.stock("gold").ship_amount)
        self.assertIsNone(result.stock("gold").total_amount)

    def test_restart_in_same_srv_preserves_proven_mothership(self):
        self.apply(cargo(gold=28), dict(event="LaunchSRV", ID=52, SRVType="mev_rhino"), cargo("SRV", gold=4))
        result = self.apply(dict(event="LoadGame", FID="F1", Ship="mev_rhino", ShipID=52),
                            journal="/source/Journal.2026-10-27T120000.01.log")
        self.assertEqual(result.stock("gold")[:2], (4, 28))
        self.assertEqual(result.ship_id, 51)

    def test_unproven_srv_restart_keeps_only_stale_ship_display(self):
        self.apply(cargo(gold=28), dict(event="LaunchSRV", ID=52), cargo("SRV", gold=4))
        result = self.apply(dict(event="LoadGame", FID="F1", Ship="mev_rhino", ShipID=99))
        self.assertIsNone(result.ship)
        self.assertEqual(result.displayed_stock("Ship", "gold"), (28, "stale"))

    def test_ship_and_source_switch_never_display_other_vehicle_history(self):
        self.apply(cargo(gold=28), dict(event="CargoDepot"))
        result = self.apply(dict(event="Loadout", Ship="anaconda", ShipID=100))
        self.assertEqual(result.displayed_stock("Ship", "gold"), (None, "unknown"))
        self.apply(cargo(gold=70))
        result = self.apply(dict(event="LoadGame", FID="F1", Ship="anaconda", ShipID=100),
                            journal="/other/Journal.2026-10-27T120000.01.log")
        self.assertIsNone(result.ship)
        self.assertEqual(result.displayed_stock("Ship", "gold"), (None, "unknown"))

    def test_foot_operation_preserves_ship_and_deltas_remain_separate(self):
        self.apply(cargo(gold=28), dict(event="LaunchSRV", ID=52), cargo("SRV", gold=4))
        result = self.apply(dict(event="Disembark", SRV=True, ID=52),
                            dict(event="Embark", SRV=True, ID=52),
                            dict(event="CollectCargo", Type="gold"),
                            dict(event="EjectCargo", Type="gold", Count=1),
                            dict(event="CargoTransfer", Transfers=[dict(Type="gold", Count=4, Direction="toship")]))
        self.assertEqual(result.stock("gold")[:2], (0, 32))
        self.apply(dict(event="DockSRV", ID=52), dict(event="Disembark", SRV=False, ID=51))
        self.assertEqual(result.ship, {"gold": 32})
        self.assertEqual(result.vehicle_records["Ship"]["quality"], "tracked")


class SnapshotHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.path = self.folder / "Journal.2026-10-26T120000.01.log"
        self.events = [dict(event="Commander", FID="F1"),
                       dict(event="LoadGame", FID="F1", Ship="lakonminer", ShipID=51)]
        self.sessions = [dict(journal_file=str(self.path), commander_id=1, fid_seen="F1", attribution_status="identified")]

    def write(self):
        self.path.write_text("".join(json.dumps(e) + "\n" for e in self.events))

    def snapshot(self, count, vessel="Ship", checkpoints=None):
        full = dict(cargo(vessel, gold=count), timestamp=f"2026-10-26T12:{len(self.events)//60:02}:{len(self.events)%60:02}Z")
        self.events.append({k:v for k,v in full.items() if k != "Inventory"})
        self.write()
        (self.folder / "Cargo.json").write_text(json.dumps(full))
        return MiningInventoryReader().reconstruct(1, "F1", self.sessions,
                                                  checkpoints=checkpoints, live_path=self.path)

    def test_ten_versions_per_vehicle_and_restart_uses_older_ship_checkpoint(self):
        result = self.snapshot(28)
        self.events.append(dict(event="LaunchSRV", ID=52))
        for n in range(1, 15):
            result = self.snapshot(n, "SRV", result.checkpoints)
        histories = result.checkpoints["snapshots"]
        self.assertEqual(sorted(len(v) for v in histories.values()), [1, 10])
        for entries in histories.values():
            for entry in entries:
                self.assertEqual(entry["context"][0:3], [str(self.folder), "F1", 51])
                self.assertIn("timestamp", entry)
                self.assertEqual(len(entry["source"]), 2)
        (self.folder / "Cargo.json").unlink()
        restored = MiningInventoryReader().reconstruct(1, "F1", self.sessions,
            checkpoints=result.checkpoints, live_path=self.path)
        self.assertEqual(restored.ship, {"gold": 28})
        self.assertEqual(restored.srv, {"gold": 14})
        again = MiningInventoryReader().reconstruct(1, "F1", self.sessions,
            checkpoints=restored.checkpoints, live_path=self.path)
        self.assertEqual(again.checkpoints, restored.checkpoints)

    def test_same_fid_other_source_and_foreign_unknown_session_do_not_mix(self):
        first = self.snapshot(28)
        other = self.folder / "other"
        other.mkdir()
        p = other / "Journal.2026-10-27T120000.01.log"
        p.write_text(json.dumps(dict(event="Commander", FID="F1")) + "\n")
        rows = self.sessions + [dict(self.sessions[0], journal_file=str(p))]
        result = MiningInventoryReader().reconstruct(1, "F1", rows,
            checkpoints=first.checkpoints, live_path=p)
        self.assertIsNone(result.ship)
        self.assertEqual(result.displayed_stock("Ship", "gold"), (None, "unknown"))
        self.assertIsNone(MiningInventoryReader().reconstruct(1, "F1", rows).ship)
        rows[-1].update(commander_id=None, attribution_status="unknown", fid_seen=None)
        result = MiningInventoryReader().reconstruct(1, "F1", rows,
            checkpoints=result.checkpoints, live_path=self.path)
        self.assertEqual(result.ship, {"gold": 28})

    def test_checkpoint_identity_and_trigger_must_match(self):
        result = self.snapshot(28)
        (self.folder / "Cargo.json").unlink()
        self.events[1]["ShipID"] = 100
        self.write()
        saved = deepcopy(result.checkpoints)
        # New checkpoints may not bypass context validation through legacy aliases.
        restored = MiningInventoryReader().reconstruct(1, "F1", self.sessions,
            checkpoints=saved, live_path=self.path)
        self.assertIsNone(restored.ship)
        self.assertEqual(restored.displayed_stock("Ship", "gold"), (None, "unknown"))
        foreign = MiningInventoryReader().reconstruct(2, "F2", self.sessions,
            checkpoints=saved, live_path=self.path)
        self.assertIsNone(foreign.ship)

    def test_old_snapshot_from_unknown_ship_context_cannot_relabel_new_ship(self):
        self.events[1].pop("ShipID")
        result = self.snapshot(28)
        self.events += [dict(event="Loadout", Ship="anaconda", ShipID=100)]
        self.write()
        restored = MiningInventoryReader().reconstruct(1, "F1", self.sessions,
            checkpoints=result.checkpoints, live_path=self.path)
        self.assertIsNone(restored.ship)

    def test_docking_count_is_usable_without_sidecar(self):
        self.events += [cargo(gold=28), dict(event="LaunchSRV", ID=52), cargo("SRV", gold=4),
                        dict(event="DockSRV", ID=52), dict(event="Loadout", Ship="lakonminer", ShipID=51),
                        dict(event="Cargo", Vessel="Ship", Count=32, timestamp="2026-10-26T12:00:10Z")]
        self.write()
        result = MiningInventoryReader().reconstruct(1, "F1", self.sessions, live_path=self.path)
        self.assertEqual(result.ship, {"gold": 32})
        self.assertFalse(result.cargo_pending)

    def test_contexts_are_bounded_and_ship_change_has_separate_versions(self):
        saved = None
        for ship_id in range(35):
            self.events.append(dict(event="Loadout", Ship="lakonminer", ShipID=ship_id))
            result = self.snapshot(ship_id + 1, checkpoints=saved)
            saved = result.checkpoints
        self.assertEqual(len(saved["snapshots"]), 32)
        self.assertTrue(all(len(v) <= 10 for v in saved["snapshots"].values()))
        self.assertEqual(result.ship, {"gold": 35})

    def test_legacy_alias_cannot_keep_an_eleventh_snapshot(self):
        result = self.snapshot(1)
        self.events += [dict(cargo(gold=n), timestamp=f"2026-10-26T12:01:{n:02}Z") for n in range(2, 12)]
        self.write()
        result = MiningInventoryReader().reconstruct(1, "F1", self.sessions,
            checkpoints=result.checkpoints, live_path=self.path)
        self.assertEqual([len(v) for v in result.checkpoints["snapshots"].values()], [10])
        self.assertNotIn("Ship", result.checkpoints)

    def test_helper_and_game_restart_in_srv_replay_both_archived_snapshots(self):
        result = self.snapshot(28)
        self.events.append(dict(event="LaunchSRV", ID=52, SRVType="mev_rhino"))
        result = self.snapshot(4, "SRV", result.checkpoints)
        (self.folder / "Cargo.json").unlink()
        next_path = self.folder / "Journal.2026-10-27T120000.01.log"
        next_path.write_text("".join(json.dumps(e) + "\n" for e in [
            dict(event="Commander", FID="F1"),
            dict(event="LoadGame", FID="F1", Ship="mev_rhino", ShipID=52)]))
        self.sessions.append(dict(self.sessions[0], journal_file=str(next_path)))
        for _ in range(2):
            result = MiningInventoryReader().reconstruct(1, "F1", self.sessions,
                checkpoints=result.checkpoints, live_path=next_path)
            self.assertEqual(result.stock("gold")[:2], (4, 28))
            self.assertEqual(result.ship_id, 51)

    def test_reader_reconciles_current_sidecar_before_refinement_without_double_count(self):
        self.events += [cargo(gold=46)]
        result = self.snapshot(47)
        self.events.append(dict(event="MiningRefined", Type="gold", timestamp=self.events[-1]["timestamp"]))
        self.write()
        result = MiningInventoryReader().reconstruct(1, "F1", self.sessions,
            checkpoints=result.checkpoints, live_path=self.path)
        self.assertEqual(result.ship, {"gold": 47})
        self.assertEqual(result.vehicle_records["Ship"]["quality"], "confirmed")

