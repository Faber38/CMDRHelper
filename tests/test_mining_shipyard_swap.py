"""Offline regressions for cargo carried by a successful ShipyardSwap."""
from copy import deepcopy
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication

from cmdrhelper.mining_inventory import MiningInventoryReader, MiningReducer
from cmdrhelper.mining_carrier import CarrierLedger, read_carrier_feed
from cmdrhelper.mining_persistence import save_values
from cmdrhelper.ui.mining_view import MiningView


class ShipyardSwapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / 'Journal.2026-11-02T170000.01.log'
        self.sessions = [self.session(self.path)]
        self.rows = []
        self.saved = {}
        self.serial = 0
        self.settings = QSettings(str(self.root / 'settings.ini'), QSettings.IniFormat)
        self.add('Commander', FID='F1')
        self.add('LoadGame', FID='F1', Ship='panthermkii', ShipID=44)

    @staticmethod
    def session(path, cid=1, fid='F1'):
        return dict(journal_file=str(path), commander_id=cid, fid_seen=fid,
                    attribution_status='identified')

    def add(self, event, **fields):
        self.serial += 1
        stamp = (datetime(2026, 11, 2, 17) + timedelta(seconds=self.serial)).isoformat() + 'Z'
        row = dict(event=event, timestamp=stamp)
        row.update(fields)
        offset = self.path.stat().st_size if self.path.exists() else 0
        with self.path.open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        self.rows.append((row, (str(self.path), offset)))
        return row

    def cargo(self, count, inline=True, **fields):
        inventory = [dict(Name='samarium', Count=count)] if count else []
        row = self.add('Cargo', Vessel='Ship', Count=count,
                       **({'Inventory': inventory} if inline else {}), **fields)
        (self.root / 'Cargo.json').write_text(json.dumps(dict(row, Inventory=inventory)))
        self.saved = self.read().checkpoints
        return row

    def read(self, live=True, cid=1, fid='F1'):
        return MiningInventoryReader().reconstruct(cid, fid, self.sessions,
            checkpoints=self.saved, live_path=self.path if live else None)

    def swap(self, old=44, new=51, loadout=True, **fields):
        kind = 'panthermkii' if new == 44 else 'lakonminer'
        payload = dict(StoreShipID=old, ShipID=new, ShipType=kind)
        payload.update(fields)
        row = self.add('ShipyardSwap', **payload)
        if loadout:
            self.add('Loadout', ShipID=new, Ship=kind, CargoCapacity=256)
        return row

    def assert_stock(self, count, ship_id=51, quality='tracked'):
        results = []
        for live in (True, False, True):
            result = self.read(live)
            self.assertEqual(result.ship_id, ship_id)
            self.assertEqual(result.ship.get('samarium', 0) if result.ship is not None else None, count)
            self.assertEqual(result.displayed_stock('Ship', 'samarium'), (count, quality))
            results.append((result.ship, result.vehicle_records, result.checkpoints))
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0], results[2])
        return result

    def test_real_44_to_51_sequence_128_samarium(self):
        # Relevant facts of the real 2026-11-02 sequence; no production files.
        self.cargo(128, inline=False, timestamp='2026-11-02T17:35:10Z')
        self.add('Docked', timestamp='2026-11-02T17:39:24Z',
                 StationType='FleetCarrier', MarketID=3705965312)
        swap = self.swap(loadout=False, timestamp='2026-11-02T17:39:36Z')
        self.add('Loadout', timestamp='2026-11-02T17:39:38Z',
                 ShipID=51, Ship='lakonminer', CargoCapacity=256)
        result = self.assert_stock(128)
        record = result.vehicle_records['Ship']
        self.assertEqual(record['ship_id'], 51)
        self.assertEqual(record['ship_type'], 'lakonminer')
        self.assertEqual(record['confirmed_at'], swap['timestamp'])
        self.assertEqual(record['source'], list(self.rows[-2][1]))
        self.assertEqual(record['source_folder'], str(self.root))
        self.assertEqual((result.commander_id, result.fid), (1, 'F1'))

    def test_confirmed_empty_is_carried_as_tracked_zero(self):
        self.cargo(0)
        self.swap()
        self.assert_stock(0)

    def carrier_transfer(self, direction, amount, expected_ship, expected_carrier):
        self.cargo(128)
        self.add('Docked', StationType='FleetCarrier', MarketID=123)
        store = CarrierLedger(self.settings)
        feed = lambda: read_carrier_feed(self.path, 'F1')
        store.confirm('F1', 123, 'samarium', 200, feed())
        self.add('CargoTransfer', Transfers=[dict(Type='samarium', Count=amount, Direction=direction)])
        self.assert_stock(expected_ship, ship_id=44)
        before = store.update('F1', 123, feed())
        self.swap()
        result = self.assert_stock(expected_ship)
        after = store.update('F1', 123, feed())
        self.assertEqual(after['records'], before['records'])
        self.assertEqual(after['records']['samarium']['count'], expected_carrier)
        self.assertEqual(store.update('F1', 123, feed()), after)
        store.attach(result, after)
        # Known-zero SRV fixture only for verifying the combined total.
        result.srv = {}
        self.assertEqual(result.stock('samarium').total_amount, 328)

    def test_transfer_to_carrier_before_swap(self):
        self.carrier_transfer('tocarrier', 128, 0, 328)

    def test_transfer_from_carrier_before_swap(self):
        self.carrier_transfer('toship', 50, 178, 150)

    def test_multiple_swaps(self):
        self.cargo(128)
        self.swap()
        self.swap(51, 62)
        self.assert_stock(128, ship_id=62)

    def test_return_uses_current_cargo_not_old_ships_snapshot(self):
        self.cargo(128)
        self.swap()
        self.add('MarketSell', Type='samarium', Count=28)
        self.swap(51, 44)
        self.assert_stock(100, ship_id=44)

    def test_missing_new_sidecar_does_not_lose_carried_stock(self):
        self.cargo(128, inline=False)
        self.swap()
        (self.root / 'Cargo.json').unlink()
        self.assert_stock(128)

    def test_later_complete_snapshot_replaces_projection(self):
        self.cargo(128)
        self.swap()
        self.cargo(75, inline=False)
        self.assert_stock(75, quality='confirmed')

    def test_unknown_base_stays_unknown(self):
        self.swap()
        self.assert_stock(None, quality='unknown')

    def test_stale_base_is_not_promoted(self):
        self.cargo(128)
        self.add('Cargo', Vessel='Ship', Count=128)  # No matching sidecar.
        self.assertIsNone(self.read().ship)
        self.swap()
        self.assert_stock(None, quality='unknown')

    def test_settings_and_game_restart_after_swap(self):
        self.cargo(128, inline=False)
        self.swap(loadout=False)
        save_values(self.settings, {'checkpoints': self.read().checkpoints})
        self.saved = QSettings(self.settings.fileName(), QSettings.IniFormat).value('checkpoints')
        self.add('Shutdown')
        self.path = self.root / 'Journal.2026-11-02T180000.01.log'
        self.sessions.append(self.session(self.path))
        self.add('Commander', FID='F1')
        self.add('LoadGame', FID='F1', Ship='lakonminer', ShipID=51)
        self.assert_stock(128)

    def test_live_and_replay_update_table_with_existing_status_colors(self):
        app = QApplication.instance() or QApplication([])
        self.cargo(128)
        self.swap()
        view = MiningView(self.settings)
        try:
            for live in (True, False):
                result = self.read(live)
                for light, yellow in ((False, '#f0ad4e'), (True, '#b36a00')):
                    view.set_light_mode(light)
                    view.set_inventory(result)
                    item = view.items['samarium']
                    self.assertEqual(item.text(2), '128')
                    self.assertEqual(item.data(2, Qt.UserRole + 1), 'tracked')
                    self.assertEqual(item.foreground(2).color().name(), yellow)
            self.assertIsNotNone(app)
        finally:
            view.deleteLater()

    def test_repeated_source_events_and_reconstruction_are_idempotent(self):
        self.cargo(128)
        self.swap()
        reducer = MiningReducer(1, 'F1')
        for row, source in self.rows:
            reducer.apply(row, source)
        before = deepcopy(reducer.result)
        for row, source in self.rows:
            reducer.apply(row, source)
        self.assertEqual(reducer.result, before)
        self.assert_stock(128)

    def test_ten_snapshot_rotation_no_fake_snapshot_or_relabelling(self):
        for count in range(116, 129):
            self.cargo(count, inline=False)
        before = deepcopy(self.saved['snapshots'])
        self.assertEqual([len(v) for v in before.values()], [10])
        self.swap()
        result = self.assert_stock(128)
        self.assertEqual(result.checkpoints['snapshots'], before)
        self.assertTrue(all(e['context'][2] == 44 for v in before.values() for e in v))

    def test_invalid_swap_identity_does_not_carry_stock(self):
        for fields in (dict(StoreShipID=None), dict(StoreShipID=45), dict(StoreShipID=True),
                       dict(ShipID=None), dict(ShipID=-1), dict(ShipID=True),
                       dict(ShipID=44), dict(ShipType='mev_rhino')):
            with self.subTest(fields=fields):
                reducer = MiningReducer(1, 'F1')
                events = [dict(event='LoadGame', FID='F1', Ship='panthermkii', ShipID=44),
                          dict(event='Cargo', Vessel='Ship', Count=128,
                               Inventory=[dict(Name='samarium', Count=128)]),
                          dict(event='ShipyardSwap', StoreShipID=44, ShipID=51, ShipType='lakonminer')]
                events[-1].update(fields)
                for i, event in enumerate(events):
                    reducer.apply(event, (str(self.path), i))
                self.assertIsNone(reducer.result.ship)

    def test_source_and_commander_cannot_supply_foreign_baseline(self):
        self.cargo(128, inline=False)
        self.path = self.root / 'other' / self.path.name
        self.path.parent.mkdir()
        self.sessions.append(self.session(self.path))
        self.add('Commander', FID='F1')
        self.swap()
        self.assertIsNone(self.read().ship)
        self.assertIsNone(self.read(cid=2, fid='F2').ship)

    def test_srv_context_is_cleared(self):
        self.cargo(128)
        self.add('LaunchSRV', ID=57, SRVType='mev_rhino')
        self.add('Cargo', Vessel='SRV', Count=0, Inventory=[])
        self.add('DockSRV', ID=57)
        self.swap(loadout=False)
        reducer = MiningReducer(1, 'F1')
        for row, source in self.rows:
            reducer.apply(row, source)
        self.assertEqual(reducer.result.ship, {'samarium': 128})
        self.assertIsNone(reducer.result.srv)
        self.assertIsNone(reducer.srv_id)
        self.assertIsNone(reducer.srv_type)
        self.assertIsNone(reducer.docking_stock)

    def test_buy_and_new_still_invalidate_cargo(self):
        self.cargo(128)
        for kind in ('ShipyardBuy', 'ShipyardNew'):
            reducer = MiningReducer(1, 'F1')
            for row, source in self.rows:
                reducer.apply(row, source)
            reducer.apply(dict(event=kind, ShipID=51, NewShipID=51), (str(self.path), 99999))
            self.assertIsNone(reducer.result.ship)
