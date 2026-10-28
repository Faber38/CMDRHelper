"""Real AppState captures cargo without constructing a Materials/Mining view."""
import json
from pathlib import Path
import time
import unittest

import test_source_manager as source_tests


class MiningCaptureLifecycleTests(unittest.TestCase):
    setUpClass = classmethod(source_tests.ManagerTests.setUpClass.__func__)
    setUp = source_tests.ManagerTests.setUp
    shutdown = source_tests.ManagerTests.shutdown
    drain = source_tests.ManagerTests.drain

    def test_app_state_saves_ship_and_srv_before_any_view_exists(self):
        runtime = next(r for r in self.state.sources.runtimes.values() if r.source.name == "Steam")
        cid = runtime.processor.sessions[-1]["commander_id"]
        self.state.select_viewed_commander(cid)
        journal = Path(runtime.processor.sessions[-1]["journal_file"])
        full = dict(event="Cargo", timestamp="2026-09-14T12:01:00Z", Vessel="Ship", Count=28,
                    Inventory=[dict(Name="gold", Count=28)])
        source_tests.append(journal,
            dict(event="LoadGame", FID="TEST-Steam", Ship="lakonminer", ShipID=51,
                 timestamp="2026-09-14T12:00:58Z"),
            dict(event="Loadout", Ship="lakonminer", ShipID=51, Modules=[],
                 timestamp="2026-09-14T12:00:59Z"),
            {k:v for k,v in full.items() if k != "Inventory"})
        (journal.parent / "Cargo.json").write_text(json.dumps(full))
        runtime.watcher.check_now()
        self.drain()
        self.wait_for_stock(cid, "Ship", 28)
        source_tests.append(journal,
            dict(event="LaunchSRV", ID=52, SRVType="mev_rhino", timestamp="2026-09-14T12:01:01Z"),
            dict(event="Cargo", Vessel="SRV", Count=4, timestamp="2026-09-14T12:01:02Z"))
        full.update(Vessel="SRV", Count=4, timestamp="2026-09-14T12:01:02Z",
                    Inventory=[dict(Name="gold", Count=4)])
        (journal.parent / "Cargo.json").write_text(json.dumps(full))
        runtime.watcher.check_now()
        self.drain()
        self.wait_for_stock(cid, "SRV", 4)
        inventory = self.state.mining_inventory_controller._last_inventory
        self.assertEqual(inventory.ship, {"gold": 28})
        self.assertEqual(len(inventory.checkpoints["snapshots"]), 2)

    def wait_for_stock(self, cid, vessel, count):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            self.app.processEvents()
            saved = self.settings.value(f"materials/mining/cargo_checkpoints/{cid}", {})
            entry = saved.get(vessel, {})
            if entry.get("payload", {}).get("Count") == count:
                return
            time.sleep(.01)
        self.fail("AppState did not checkpoint cargo without a view")
