"""Batch invalidation integration; actual readers and temporary source ingestion."""
from pathlib import Path
import time
import unittest
from unittest.mock import patch
import test_source_manager
import test_source_processing
from test_import_catchup import append, event
from cmdrhelper.inventory_invalidation import KINDS, batch_kinds, event_kinds


class RulesTests(unittest.TestCase):
    def test_reader_event_sets_and_carrier_identity(self):
        from cmdrhelper.material_inventory import EVENTS as materials
        from cmdrhelper.mining_inventory import EVENTS as mining
        from cmdrhelper.odyssey_inventory import EVENTS as odyssey
        for kind, events in [('materials', materials), ('mining', mining), ('odyssey', odyssey)]:
            for name in events:
                self.assertIn(kind, event_kinds([{'event': name}]), name)
        self.assertEqual(event_kinds([{'event': 'FSDJump'}]), set())
        self.assertEqual(event_kinds([{'event': 'CarrierStats'}]), {'mining', 'odyssey'})

    def test_corrections_continuity_and_unknown_input(self):
        row = dict(journal_file='a', commander_id=1, fid_seen='F1',
                   attribution_status='identified', first_event_at='t',
                   last_read_offset=100, file_size=100, sha256='hash', modified_ns=1)
        self.assertEqual(batch_kinds([row], [dict(row)], []), set())
        self.assertEqual(batch_kinds([row], [dict(row, modified_ns=2)], []), set())
        for key, value in [('commander_id', 2), ('fid_seen', 'F2'),
                           ('attribution_status', 'unknown'), ('first_event_at', 'other'),
                           ('sha256', 'corrected'), ('last_read_offset', 50),
                           ('file_size', 120)]:
            self.assertEqual(batch_kinds([row], [dict(row, **{key: value})], []), KINDS, key)
        self.assertEqual(batch_kinds([row], [], []), KINDS)
        self.assertEqual(batch_kinds([], [row], []), KINDS)
        self.assertEqual(batch_kinds([row], [row], [], full=True), KINDS)

    def test_appending_a_duplicate_changes_odyssey_deduplication_basis(self):
        row = dict(journal_file='a', commander_id=1, fid_seen='F1',
                   attribution_status='identified', last_read_offset=100,
                   file_size=100, sha256='same')
        latest = dict(row, journal_file='b')
        changed = dict(latest, last_read_offset=150, file_size=150, sha256='new')
        self.assertEqual(batch_kinds([row, latest], [row, changed],
            [('b', 'F1', dict(event='FSDJump', _journal_offset=100))]), KINDS)
        self.assertEqual(batch_kinds([latest], [changed],
            [('b', 'F1', dict(event='FSDJump', _journal_offset=100))],
            indexed=[row, changed]), KINDS)


class ProcessorInvalidationTests(unittest.TestCase):
    setUp = test_source_processing.ProcessingTests.setUp
    def test_noop_live_history_import_and_recovery(self):
        p = self.processors[0]
        p.process()
        self.assertEqual(p.inventory_kinds, KINDS)
        p.process()
        self.assertEqual(p.inventory_kinds, set())
        append(self.paths[0], event('FSDJump', StarSystem='Jump', SystemAddress=50))
        p.process()
        self.assertEqual(p.inventory_kinds, set())
        append(self.paths[0], event('MaterialCollected', Category='Raw', Name='iron', Count=1))
        with patch.object(p.database, 'store_snapshot', side_effect=RuntimeError('after commit')):
            with self.assertRaises(RuntimeError):
                p.process()
        self.assertEqual(p.inventory_kinds, KINDS)
        p.process()
        self.assertEqual(p.context['applied_events'], [])
        self.assertEqual(p.inventory_kinds, KINDS)
        newer = self.paths[0].with_name('Journal.2026-09-14T130000.01.log')
        append(newer, event('Commander', FID='F-a', Name='Same'))
        p.process()
        self.assertEqual(p.inventory_kinds, KINDS)
        append(self.paths[0], event('FSDJump', StarSystem='History', SystemAddress=51))
        p.process()
        self.assertEqual(p.inventory_kinds, KINDS)
        p.initialized = False
        p.process()
        self.assertEqual(p.inventory_kinds, KINDS)

    def test_index_correction_and_new_historical_file(self):
        p = self.processors[0]
        p.process()
        older = self.paths[0].with_name('Journal.2026-09-13T120000.01.log')
        append(older, event('Commander', FID='F-a', Name='Same'),
               event('MaterialCollected', Category='Raw', Name='iron', Count=2))
        p.process()
        self.assertEqual(p.inventory_kinds, KINDS)
        with self.db._connect() as con:
            con.execute("UPDATE journal_sessions SET attribution_status='unknown', commander_id=NULL WHERE journal_file=?", (str(older),))
        p.process()
        self.assertEqual(p.inventory_kinds, KINDS)
        with self.db._connect() as con:
            con.execute("UPDATE journal_sessions SET attribution_status='identified', commander_id=? WHERE journal_file=?",
                        (p.sessions[-1]['commander_id'], str(older)))
        p.process()
        self.assertEqual(p.inventory_kinds, KINDS)


class InventoryBatchTests(unittest.TestCase):
    setUpClass = classmethod(test_source_manager.ManagerTests.setUpClass.__func__)
    setUp = test_source_manager.ManagerTests.setUp
    shutdown = test_source_manager.ManagerTests.shutdown
    drain = test_source_manager.ManagerTests.drain
    def selected_runtime(self):
        runtime = next(iter(self.state.sources.runtimes.values()))
        self.state.select_viewed_commander(runtime.processor.sessions[-1]['commander_id'])
        return runtime

    def batch(self, runtime, events):
        before = dict(self.state._inventory_revisions)
        append(Path(runtime.processor.sessions[-1]['journal_file']), *events)
        runtime.watcher.check_now()
        self.drain()
        return {kind: self.state._inventory_revisions[kind] - before[kind] for kind in KINDS}

    def test_independent_and_mixed_batches_count_once(self):
        r = self.selected_runtime()
        for events, expected in [
            ([event('FSDJump', StarSystem='Jump', SystemAddress=50)], set()),
            ([event('MaterialCollected', Category='Raw', Name='iron', Count=2),
              event('MaterialDiscarded', Category='Raw', Name='iron', Count=1)], {'materials'}),
            ([event('Cargo', Vessel='Ship', Inventory=[]), event('MiningRefined', Type='gold'),
              event('CollectCargo', Type='gold'), event('CargoTransfer', Transfers=[])], {'mining'}),
            ([event('ShipLocker', Items=[], Components=[], Data=[], Consumables=[])], {'odyssey'}),
            ([event('FSDJump', StarSystem='Mixed', SystemAddress=51),
              event('MaterialTrade', Paid=dict(Material='iron', Category='Raw', Quantity=1),
                    Received=dict(Material='nickel', Category='Raw', Quantity=1)),
              event('Cargo', Vessel='Ship', Inventory=[]),
              event('Backpack', Items=[], Components=[], Data=[], Consumables=[])], KINDS),
        ]:
            self.assertEqual(self.batch(r, events), {k: int(k in expected) for k in KINDS})
        before = dict(self.state._inventory_revisions)
        self.state.sources.request(r.source.id)
        self.drain()
        self.assertEqual(self.state._inventory_revisions, before)

    def test_fsd_does_not_start_any_reader_and_material_result_updates(self):
        from cmdrhelper.material_controller import MaterialController
        from cmdrhelper.odyssey_controller import OdysseyController
        r = self.selected_runtime()
        # Establish sidecar identity before measuring a subsequent append.
        for runtime in self.state.sources.runtimes.values():
            runtime.watcher.check_now()
        self.drain()
        material = MaterialController(self.state)
        odyssey = OdysseyController(self.state)
        mining = self.state.mining_inventory_controller
        controllers = [material, mining, odyssey]
        def settle():
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                self.app.processEvents()
                if all(not c._running and not c._dirty and not c.timer.isActive() for c in controllers):
                    return
                time.sleep(.01)
            self.fail('readers did not settle')
        self.app.processEvents()
        settle()
        results = []
        material.ready.connect(lambda inventory, name: results.append(inventory))
        try:
            with patch.object(material.reader, 'reconstruct', wraps=material.reader.reconstruct) as m, \
                 patch.object(mining.reader, 'reconstruct', wraps=mining.reader.reconstruct) as c, \
                 patch.object(odyssey.reader, 'reconstruct', wraps=odyssey.reader.reconstruct) as o:
                self.batch(r, [event('FSDJump', StarSystem='No inventory', SystemAddress=99)])
                settle()
                self.assertEqual([m.call_count, c.call_count, o.call_count], [0, 0, 0])
                self.batch(r, [event('MaterialCollected', Category='Raw', Name='iron', Count=2)])
                settle()
                self.assertEqual([m.call_count, c.call_count, o.call_count], [1, 0, 0])
                self.assertTrue(results[-1].known)
                self.assertEqual(results[-1].material('iron').count, 3)
                other = next(rt for rt in self.state.sources.runtimes.values() if rt is not r)
                self.state.select_viewed_commander(other.processor.sessions[-1]['commander_id'])
                settle()
                self.assertEqual([m.call_count, c.call_count, o.call_count], [2, 1, 1])
                self.assertEqual(results[-1].fid, 'TEST-Heroic')
        finally:
            for controller in (material, odyssey):
                controller.timer.stop()
                controller.pool.waitForDone()
                controller.deleteLater()

    def test_same_fid_source_switch_and_transfers_survive_skipped_jumps(self):
        r = self.selected_runtime()
        mining = self.state.mining_inventory_controller
        def settle():
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                self.app.processEvents()
                if not mining._running and not mining._dirty and not mining.timer.isActive():
                    return mining._last_inventory
                time.sleep(.01)
            self.fail('mining did not settle')
        self.batch(r, [event('LoadGame', FID='TEST-Steam', Commander='Steam', Ship='anaconda', ShipID=1),
                       event('Cargo', Vessel='Ship', Inventory=[dict(Name='gold', Count=10, Stolen=0)]),
                       event('LaunchSRV', PlayerControlled=True),
                       event('Cargo', Vessel='SRV', Inventory=[dict(Name='gold', Count=2, Stolen=0)])])
        inventory = settle()
        self.assertEqual((inventory.ship, inventory.srv), ({'gold': 10}, {'gold': 2}))
        self.batch(r, [event('FSDJump', StarSystem='Context', SystemAddress=52)])
        self.batch(r, [event('CargoTransfer', Transfers=[dict(Type='gold', Count=3, Direction='tosrv')])])
        inventory = settle()
        self.assertEqual((inventory.ship, inventory.srv), ({'gold': 7}, {'gold': 5}))
        self.state.sources.request(r.source.id)
        self.drain()
        self.assertEqual((settle().ship, settle().srv), ({'gold': 7}, {'gold': 5}))
        other = next(rt for rt in self.state.sources.runtimes.values() if rt is not r)
        new = Path(other.source.path) / 'Journal.2026-09-15T120000.01.log'
        append(new, event('LoadGame', FID='TEST-Steam', Commander='Steam', Ship='anaconda', ShipID=2),
               event('Cargo', Vessel='Ship', Inventory=[dict(Name='gold', Count=40, Stolen=0)]))
        other.watcher.check_now()
        # check_now polls the current file; directory discovery happens only every
        # tenth poll. An empty source queue does not prove this new file was read.
        deadline = time.monotonic() + 20
        while True:
            self.app.processEvents()
            imported = any(
                row['journal_file'] == str(new) and row['fid_seen'] == 'TEST-Steam'
                for row in other.processor.sessions
            )
            if imported and not self.state.sources.running and not self.state.sources.queue:
                break
            if time.monotonic() >= deadline:
                self.fail('new Heroic journal for TEST-Steam was not processed within 20 seconds')
            time.sleep(.01)
        self.state.sources.preferred_source = other.source.id
        self.state.sources.refresh_selected()
        inventory = settle()
        self.assertEqual(inventory.ship, {'gold': 40})
        self.assertEqual(inventory.source_folder, other.source.path)
        self.state.sources.preferred_source = r.source.id
        self.state.sources.refresh_selected()
        inventory = settle()
        self.assertEqual((inventory.ship, inventory.srv), ({'gold': 7}, {'gold': 5}))
