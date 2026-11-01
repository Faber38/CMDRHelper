"""Stock copy optimization must preserve evidence and ownership boundaries."""
from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest

from cmdrhelper.mining_inventory import MiningReducer, MiningInventoryReader


class MiningStockCopyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'Journal.2026-09-01T120000.01.log'
        self.reducer = MiningReducer(1, 'FA')
        self.offset = 0
        self.apply('LoadGame', FID='FA', Ship='anaconda', ShipID=7)

    def apply(self, kind, **values):
        self.offset += 1
        self.reducer.apply(dict(event=kind, timestamp=values.pop('timestamp', '2026-09-01T12:00:00Z'), **values), (str(self.path), self.offset))

    def cargo(self, vessel, count):
        self.apply('Cargo', Vessel=vessel, Count=count, Inventory=[dict(Name='gold', Count=count)])

    def test_published_and_historical_stocks_are_independent_of_next_delta(self):
        self.cargo('Ship', 4)
        published = self.reducer.result.ship
        historical = self.reducer.result.vehicle_records['Ship']['last_confirmed']
        self.apply('MiningRefined', Type='gold', timestamp='2026-09-01T12:00:01Z')
        self.assertEqual(published, {'gold': 4})
        self.assertEqual(historical, {'gold': 4})
        self.assertEqual(self.reducer.result.ship, {'gold': 5})
        self.assertIsNot(self.reducer.result.ship, self.reducer.stocks['Ship'])
        self.assertIsNot(self.reducer.result.ship, self.reducer.result.vehicle_records['Ship']['last_confirmed'])

    def test_mutating_published_snapshot_cannot_change_reducer_or_evidence(self):
        self.cargo('Ship', 4)
        self.reducer.result.ship['gold'] = 999
        self.assertEqual(self.reducer.stocks['Ship'], {'gold': 4})
        self.assertEqual(self.reducer.result.vehicle_records['Ship']['last_confirmed'], {'gold': 4})
        self.reducer.result.vehicle_records['Ship']['last_confirmed']['gold'] = 888
        self.assertEqual(self.reducer.stocks['Ship'], {'gold': 4})
        self.apply('MarketBuy', Type='gold', Count=1)
        self.assertEqual(self.reducer.result.ship, {'gold': 5})

    def test_docking_candidate_does_not_mutate_previous_ship_or_srv(self):
        self.cargo('Ship', 4)
        ship = self.reducer.result.ship
        self.apply('LaunchSRV', ID=1, SRVType='testbuggy')
        self.cargo('SRV', 2)
        srv = self.reducer.result.srv
        self.apply('DockSRV', ID=1)
        self.assertIsNone(self.reducer.result.ship)
        self.assertEqual(ship, {'gold': 4})
        self.assertEqual(srv, {'gold': 2})
        self.apply('Cargo', Vessel='Ship', Count=6)
        self.assertEqual(self.reducer.result.ship, {'gold': 6})
        self.assertEqual(ship, {'gold': 4})
        self.assertEqual(srv, {'gold': 2})

    def test_leading_full_snapshot_and_delta_are_counted_once(self):
        self.cargo('Ship', 2)
        self.cargo('Ship', 3)
        self.reducer.result.ship['gold'] = 999
        self.assertEqual(self.reducer.pending_count['stock'], {'gold': 2})
        self.assertEqual(self.reducer.pending_count['snapshot'], {'gold': 3})
        self.apply('MiningRefined', Type='gold')
        self.assertEqual(self.reducer.result.ship, {'gold': 3})

    def test_invalid_transfer_never_publishes_partial_arithmetic_as_confirmed(self):
        self.cargo('Ship', 4)
        self.cargo('SRV', 2)
        ship, srv = self.reducer.result.ship, self.reducer.result.srv
        self.apply('CargoTransfer', Transfers=[dict(Type='gold', Count=1, Direction='tosrv'), dict(Type='gold', Count=-1, Direction='tosrv')])
        self.assertIsNone(self.reducer.result.ship)
        self.assertIsNone(self.reducer.result.srv)
        self.assertEqual(ship, {'gold': 4})
        self.assertEqual(srv, {'gold': 2})
        self.assertEqual(self.reducer.result.vehicle_records['Ship']['last_confirmed'], {'gold': 4})
        self.assertEqual(self.reducer.result.vehicle_records['Ship']['quality'], 'stale')

    def test_nested_invalid_quantity_is_still_rejected_without_mutating_event(self):
        self.cargo('Ship', 4)
        event = dict(event='Cargo', Vessel='Ship', Count=1, Inventory=[dict(Name='gold', Count={'bad': 1})])
        original = deepcopy(event)
        self.reducer.apply(event, (str(self.path), 99))
        self.assertEqual(event, original)
        self.assertIsNone(self.reducer.result.ship)
        self.assertEqual(self.reducer.result.vehicle_records['Ship']['last_confirmed'], {'gold': 4})

    def test_reader_cache_and_nested_checkpoints_do_not_share_returned_stocks(self):
        events = [dict(event='Commander', FID='FA'), dict(event='LoadGame', FID='FA', Ship='anaconda', ShipID=7), dict(event='Cargo', timestamp='2026-09-01T12:00:00Z', Vessel='Ship', Count=4, Inventory=[dict(Name='gold', Count=4)])]
        self.path.write_text(''.join(json.dumps(e)+'\n' for e in events))
        sessions = [dict(journal_file=str(self.path), commander_id=1, fid_seen='FA', attribution_status='identified')]
        reader = MiningInventoryReader()
        first = reader.reconstruct(1, 'FA', sessions)
        checkpoints = deepcopy(first.checkpoints)
        expected = deepcopy(checkpoints)
        first.ship['gold'] = 999
        first.vehicle_records['Ship']['last_confirmed']['gold'] = 888
        second = reader.reconstruct(1, 'FA', sessions, checkpoints=checkpoints)
        self.assertEqual(second.ship, {'gold': 4})
        second.checkpoints['continuity']['vehicles']['Ship']['last_confirmed']['gold'] = 777
        self.assertEqual(checkpoints, expected)
        unknown = reader.reconstruct(2, 'FB', sessions, checkpoints=checkpoints)
        self.assertIsNone(unknown.ship)
        self.assertEqual(unknown.fid, 'FB')
