import json
from pathlib import Path
import tempfile
import unittest

from cmdrhelper.mining_inventory import MiningInventoryReader, MiningReducer, total_stock


def cargo(vessel="Ship", **items):
    return dict(event="Cargo", Vessel=vessel, Count=sum(items.values()),
                Inventory=[dict(Name=name, Count=count) for name, count in items.items()])


class MiningInventoryTests(unittest.TestCase):
    def setUp(self):
        self.reducer = MiningReducer(1, "F1")
        self.offset = 0

    def apply(self, *events):
        for event in events:
            self.offset += 1
            self.reducer.apply(event, ("journal", self.offset))
        return self.reducer.result

    def test_ship_snapshot_and_zero_for_absent_commodity(self):
        result = self.apply(cargo(thortveitite=12, uraninite=16))
        self.assertEqual(result.stock("uraninite"), (16, None, None))
        self.assertEqual(result.stock("gold"), (0, None, None))

    def test_srv_switch_never_adds_ship_and_srv_and_dock_waits_for_snapshot(self):
        self.apply(cargo(thortveitite=12), dict(event="LaunchSRV", PlayerControlled=True))
        self.assertIsNone(self.reducer.result.vehicle)
        result = self.apply(cargo("SRV", thortveitite=4))
        self.assertEqual(result.stock("thortveitite")[0], 4)
        self.assertEqual(result.vessel, "SRV")
        self.apply(dict(event="DockSRV", PlayerControlled=True))
        self.assertIsNone(self.reducer.result.vehicle)
        result = self.apply(cargo(thortveitite=16))
        self.assertEqual(result.stock("thortveitite")[0], 16)

    def test_refining_collection_ejection_trade_and_full_snapshot_wins(self):
        self.apply(cargo(copper=10))
        self.apply(dict(event="MiningRefined", Type="$copper_name;"))
        self.assertEqual(self.reducer.result.stock("copper")[0], 11)
        self.apply(dict(event="CollectCargo", Type="Copper"),
                   dict(event="EjectCargo", Type="copper", Count=2),
                   dict(event="MarketBuy", Type="copper", Count=10),
                   dict(event="MarketSell", Type="copper", Count=4))
        self.assertEqual(self.reducer.result.stock("copper")[0], 16)
        self.apply(cargo(copper=7))
        self.assertEqual(self.reducer.result.stock("copper")[0], 7)
        self.apply(dict(event="MiningRefined", Type="copper"), cargo(copper=8))
        self.assertEqual(self.reducer.result.stock("copper")[0], 8)

    def test_refinement_without_baseline_is_unknown_and_sources_are_idempotent(self):
        self.apply(dict(event="MiningRefined", Type="copper"))
        self.assertIsNone(self.reducer.result.stock("copper")[0])
        self.apply(cargo(copper=2))
        event = dict(event="MiningRefined", Type="copper")
        self.reducer.apply(event, ("file", 77))
        self.reducer.apply(event, ("file", 77))
        self.assertEqual(self.reducer.result.stock("copper")[0], 3)

    def test_count_only_conflict_and_negative_inventory_are_unknown_until_snapshot(self):
        self.apply(cargo(copper=2), dict(event="Cargo", Vessel="Ship", Count=2))
        self.assertEqual(self.reducer.result.stock("copper")[0], 2)
        self.apply(dict(event="Cargo", Vessel="Ship", Count=3))
        self.assertIsNone(self.reducer.result.vehicle)
        self.apply(cargo(copper=1), dict(event="MarketSell", Type="copper", Count=2))
        self.assertIsNone(self.reducer.result.vehicle)
        self.apply(cargo(copper=5))
        self.assertEqual(self.reducer.result.stock("copper")[0], 5)

    def test_ship_transfer_deltas_do_not_create_carrier_inventory(self):
        self.apply(cargo(gold=10), dict(event="CargoTransfer", Transfers=[
            dict(Type="gold", Count=4, Direction="tocarrier")]))
        self.assertEqual(self.reducer.result.stock("gold"), (6, None, None))
        self.apply(dict(event="CargoTransfer", Transfers=[dict(Type="gold", Count=2, Direction="toship")]))
        self.assertEqual(self.reducer.result.stock("gold"), (8, None, None))
        self.apply(dict(event="CarrierStats", SpaceUsage=dict(Cargo=200)),
                   dict(event="CarrierTradeOrder", Commodity="gold", SaleOrder=200),
                   dict(event="CarrierMarket", Items=[dict(Name="gold", Stock=200)]))
        self.assertIsNone(self.reducer.result.carrier)

    def test_transfer_between_ship_and_srv_keeps_separate_snapshots(self):
        self.apply(cargo(gold=10), dict(event="LaunchSRV"), cargo("SRV", gold=2))
        self.apply(dict(event="CargoTransfer", Transfers=[dict(Type="gold", Count=3, Direction="tosrv")]))
        self.assertEqual(self.reducer.result.stock("gold")[0], 5)
        self.assertEqual(self.reducer.stocks["Ship"]["gold"], 7)
        self.apply(dict(event="CargoTransfer", Transfers=[dict(Type="gold", Count=2, Direction="toship")]))
        self.assertEqual(self.reducer.result.stock("gold")[0], 3)
        self.assertEqual(self.reducer.stocks["Ship"]["gold"], 9)

    def test_new_ship_session_and_invalid_snapshots_do_not_keep_old_stock(self):
        self.apply(dict(event="LoadGame", ShipID=1), cargo(gold=10),
                   dict(event="Loadout", ShipID=2, Ship="CobraMkIII"))
        self.assertIsNone(self.reducer.result.vehicle)
        self.apply(cargo(gold=5), dict(event="LoadGame", ShipID=2))
        self.assertIsNone(self.reducer.result.vehicle)
        self.apply(dict(event="Cargo", Vessel="Ship", Count=1, Inventory=[dict(Name="gold", Count=-1)]))
        self.assertIsNone(self.reducer.result.vehicle)

    def test_total_requires_both_parts(self):
        for a, b, expected in ((16, 120, 136), (16, None, None), (None, 120, None),
                               (0, 0, 0), (None, None, None)):
            self.assertEqual(total_stock(a, b), expected)

    def test_non_cargo_rewards_keep_stock_but_commodity_changes_require_snapshot(self):
        self.apply(cargo(gold=4), dict(event="MissionCompleted", Reward=1000),
                   dict(event="EngineerContribution", Type="Materials", Commodity="iron", Quantity=2))
        self.assertEqual(self.reducer.result.stock("gold")[0], 4)
        self.apply(dict(event="MissionCompleted", CommodityReward=[dict(Name="gold", Count=2)]))
        self.assertIsNone(self.reducer.result.vehicle)
        self.apply(cargo(gold=6))
        self.assertEqual(self.reducer.result.stock("gold")[0], 6)


class MiningReaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "Journal.2026-09-12T120000.01.log"
        self.sidecar = self.path.parent / "Cargo.json"
        self.sessions = [dict(journal_file=str(self.path), commander_id=1, fid_seen="F1", attribution_status="identified")]

    def write(self, events):
        all_events = [dict(event="Commander", FID="F1"), dict(event="LoadGame", FID="F1", Ship="CobraMkIII", ShipID=1)] + events
        for i, event in enumerate(all_events):
            event.setdefault("timestamp", f"2026-09-12T12:00:{i:02}Z")
        self.path.write_text("".join(json.dumps(e) + "\n" for e in all_events))

    def test_ship_and_srv_sidecars_are_bound_to_latest_identified_cargo_event(self):
        for vessel in ("Ship", "SRV"):
            full = cargo(vessel, gold=16)
            full["timestamp"] = "2026-09-12T12:00:02Z"
            self.write([{k: v for k, v in full.items() if k != "Inventory"}])
            self.sidecar.write_text(json.dumps(full))
            result = MiningInventoryReader().reconstruct(1, "F1", self.sessions, live_path=self.path)
            self.assertEqual(result.vessel, vessel)
            self.assertEqual(result.stock("gold")[0], 16)
            other = MiningInventoryReader().reconstruct(2, "F2", self.sessions, live_path=self.path)
            self.assertIsNone(other.vehicle)

    def test_restart_checkpoint_then_append_is_replayed_once(self):
        full = dict(cargo(gold=16), timestamp="2026-09-12T12:00:02Z")
        trigger = {k: v for k, v in full.items() if k != "Inventory"}
        self.write([trigger])
        self.sidecar.write_text(json.dumps(full))
        first = MiningInventoryReader().reconstruct(1, "F1", self.sessions, live_path=self.path)
        self.sidecar.write_text("{")
        self.write([trigger, dict(event="MiningRefined", Type="gold")])
        reader = MiningInventoryReader()
        for _ in range(2):
            result = reader.reconstruct(1, "F1", self.sessions, checkpoints=first.checkpoints)
            self.assertEqual(result.stock("gold")[0], 17)
        self.write([trigger, cargo(gold=3), dict(event="MarketSell", Type="gold", Count=2)])
        result = reader.reconstruct(1, "F1", self.sessions, checkpoints=first.checkpoints)
        self.assertEqual(result.stock("gold")[0], 1)

    def test_embedded_snapshot_restarts_without_sidecar_or_settings(self):
        self.write([cargo("SRV", copper=8), dict(event="MiningRefined", Type="copper")])
        result = MiningInventoryReader().reconstruct(1, "F1", self.sessions)
        self.assertEqual(result.stock("copper")[0], 9)

    def test_wrong_vessel_sidecar_and_conflicting_file_identity_are_rejected(self):
        full = dict(cargo("SRV", gold=16), timestamp="2026-09-12T12:00:02Z")
        self.write([dict(event="Cargo", Vessel="Ship", Count=16)])
        self.sidecar.write_text(json.dumps(full))
        result = MiningInventoryReader().reconstruct(1, "F1", self.sessions, live_path=self.path)
        self.assertIsNone(result.vehicle)
        self.write([cargo(gold=16), dict(event="Commander", FID="F2")])
        result = MiningInventoryReader().reconstruct(1, "F1", self.sessions)
        self.assertIsNone(result.vehicle)
