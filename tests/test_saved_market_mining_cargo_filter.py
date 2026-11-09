"""Trade and Mining share the published ship stock; all data is synthetic."""
import unittest
from copy import deepcopy
from os.path import abspath
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtCore import Qt

from cmdrhelper.mining_controller import mining_publication_context
from cmdrhelper.mining_inventory import MiningReducer, MiningInventoryReader
from cmdrhelper.ship_cargo import ShipCargoTracker
from cmdrhelper.i18n import tr
from cmdrhelper.commodity_master import lookup_by_symbol
import test_saved_market_cargo_filter as existing


class MiningCargoFilterTests(existing.CargoFilterFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.controller = self.state.mining_inventory_controller

    def publish(self, goods=None):
        """Real sequence: ship 62 -> 44 -> Rhino 57 -> SRV 34 t."""
        goods = {} if goods is None else goods
        self.state._inventory_revisions = {'mining': 10}
        self.state.database = SimpleNamespace(path=str(self.database))
        journal = abspath('synthetic-journal')
        self.state._journal_index_sessions[0]['journal_file'] = journal
        fid = self.state.commander_fid
        events = [
            dict(event='LoadGame', FID=fid, Ship='explorer_nx', ShipID=62),
            dict(event='Loadout', Ship='explorer_nx', ShipID=62),
            dict(event='Cargo', Vessel='Ship', Count=sum(goods.values()),
                 Inventory=[dict(Name=k, Count=v) for k, v in goods.items()]),
            dict(event='ShipyardSwap', StoreShipID=62, ShipID=44, ShipType='panthermkii'),
            dict(event='Loadout', Ship='panthermkii', ShipID=44),
            dict(event='LaunchSRV', ID=57, SRVType='mev_rhino', PlayerControlled=True),
            dict(event='Cargo', Vessel='SRV', Count=34,
                 Inventory=[dict(Name='thortveitite', Count=34)]),
        ]
        reducer, tracker = MiningReducer(1, fid), ShipCargoTracker()
        for i, event in enumerate(events):
            event['timestamp'] = f'2026-11-05T14:00:{i:02d}Z'
            reducer.apply(event, (journal, i))
            tracker.apply(event, fid, journal)
        self.state.ship_cargo_context = tracker.context
        self.state.ship_loadout = SimpleNamespace(ship_id=44, ship_type='panthermkii',
            loadout_complete=True, loadout_stale=False, cargo_capacity=576,
            loadout_timestamp=events[4]['timestamp'])
        self.state.cargo_snapshot = None
        self.state._cargo_status = None
        inventory = reducer.result
        inventory.publication_context = mining_publication_context(self.state)
        self.controller._last_inventory = inventory
        self.controller.ready.emit(inventory)
        return inventory

    def test_real_sequence_empty_ship_is_not_srv_cargo(self):
        inventory = self.publish()
        self.assertEqual(inventory.ship_id, 44)
        self.assertEqual(inventory.ship, {})
        self.assertEqual(inventory.srv, {'thortveitite': 34})
        self.assertEqual(inventory.vehicle_records['Ship']['quality'], 'tracked')
        self.assertEqual(self.view.goods_proxy.rowCount(), 0)
        self.assertEqual(self.view.cargo_notice.text(), tr('browse.cargo_retained_empty'))
        self.assertTrue(self.view.cargo_only.isChecked())

    def test_filled_stock_and_no_io_or_mutation(self):
        inventory = self.publish({'gold': 2, 'beer': 1})
        before = deepcopy(inventory)
        selected = self.view._selected_id
        self.view.goods_table.sortByColumn(2, Qt.DescendingOrder)
        with patch.object(MiningInventoryReader, 'reconstruct', side_effect=AssertionError('no scan')), \
             patch.object(existing.MarketStore, 'get_current', side_effect=AssertionError('no DB')), \
             patch.object(existing.ui, 'read_markets', side_effect=AssertionError('no reload')), \
             patch('builtins.open', side_effect=AssertionError('no file read')):
            self.view.filter_goods()
            self.assertEqual(self.view.goods_proxy.rowCount(), 2)
            self.view.goods_search.setText('Bier')
            self.assertEqual(self.view.goods_proxy.rowCount(), 1)
            self.view.goods_search.clear()
        self.assertEqual(inventory, before)
        self.assertEqual(self.view._selected_id, selected)
        self.assertEqual(self.view.goods_table.horizontalHeader().sortIndicatorSection(), 2)
        self.assertEqual(self.view.cargo_notice.text(), tr('browse.cargo_retained'))
        self.view.mining_only.setChecked(True)
        self.assertEqual(self.view.goods_proxy.rowCount(), 2)
        self.view.all_goods.setChecked(True)
        self.assertEqual(self.view.goods_proxy.rowCount(), 3)

    def test_unknown_commodity_pauses(self):
        self.publish({'uncatalogued': 1})
        self.assertIsNone(self.view.goods_proxy.cargo_ids)
        self.assertEqual(self.view.cargo_notice.text(), tr('browse.cargo_identity_unknown'))

    def source_replay(self, events=None, *, new_session=False):
        """Use the real parser/reader across a Linux source-directory symlink."""
        import json
        from cmdrhelper.journal_reader import read_latest_state, classify_journal_file
        if not hasattr(self, 'source_alias'):
            physical = self.root / 'debian-installation'
            physical.mkdir()
            self.source_alias = self.root / 'steam'
            self.source_alias.symlink_to(physical, target_is_directory=True)
            self.replay_events, self.replay_sessions, self.checkpoints = [], [], {}
        if not self.replay_sessions or new_session:
            name = f'Journal.2026-11-{5 + len(self.replay_sessions):02}T151202.01.log'
            self.replay_path = self.source_alias / name
            self.replay_events = []
            self.replay_sessions.append({})
        self.replay_events.extend(events or [])
        for n, event in enumerate(self.replay_events):
            event.setdefault('timestamp', f'2026-11-{4 + len(self.replay_sessions):02}T15:00:{n:02}Z')
        self.replay_path.write_text(''.join(json.dumps(e) + '\n' for e in self.replay_events))
        self.replay_sessions[-1] = dict(classify_journal_file(self.replay_path), commander_id=1)
        d = read_latest_state(self.source_alias, indexed_sessions=self.replay_sessions, powerplay_history=False)
        self.state.database = SimpleNamespace(path=str(self.database))
        self.state._journal_index_sessions = deepcopy(self.replay_sessions)
        self.state._inventory_revisions = {'mining': len(self.replay_events)}
        self.state.ship_loadout = d['ship_loadout']
        self.state.ship_cargo_context = d['ship_cargo_context']
        self.state.cargo_snapshot = None
        self.state._cargo_status = None
        inventory = MiningInventoryReader().reconstruct(1, self.state.commander_fid,
            self.replay_sessions, checkpoints=self.checkpoints, live_path=self.replay_path)
        self.checkpoints = inventory.checkpoints
        inventory.publication_context = mining_publication_context(self.state)
        self.controller._last_inventory = inventory
        self.controller.ready.emit(inventory)
        return inventory

    def thortveitite_events(self):
        fid = self.state.commander_fid
        self.view._snapshot['commodities'].append(dict(
            commodity_id=lookup_by_symbol('thortveitite').frontier_id, symbol='Thortveitite',
            commander_buy_price=10, commander_sell_price=9, supply=20, demand=30))
        self.view._render_goods()
        cargo = lambda vessel, count: dict(event='Cargo', Vessel=vessel, Count=count,
            Inventory=[dict(Name='thortveitite', Count=count)] if count else [])
        self.full_cargo = cargo
        return [dict(event='Commander', FID=fid, Name='Synthetic'),
            dict(event='LoadGame', FID=fid, Ship='explorer_nx', ShipID=62),
            dict(event='Loadout', Ship='explorer_nx', ShipID=62, CargoCapacity=397, Modules=[]),
            cargo('Ship', 0),
            dict(event='ShipyardSwap', StoreShipID=62, ShipID=44, ShipType='panthermkii'),
            dict(event='Loadout', Ship='panthermkii', ShipID=44, CargoCapacity=576, Modules=[]),
            dict(event='LaunchSRV', ID=57, SRVType='mev_rhino'), cargo('SRV', 57),
            dict(event='CargoTransfer', Transfers=[dict(Type='thortveitite', Count=57, Direction='toship')]),
            cargo('SRV', 0), cargo('SRV', 15), dict(event='DockSRV', ID=57),
            dict(event='Loadout', Ship='panthermkii', ShipID=44, CargoCapacity=576, Modules=[]),
            cargo('Ship', 72), dict(event='LaunchSRV', ID=57, SRVType='mev_rhino'),
            cargo('SRV', 0), cargo('SRV', 1)]

    def test_steam_symlink_real_72_ship_1_srv_and_tab_return(self):
        from PySide6.QtCore import QSettings
        from cmdrhelper.ui.mining_view import MiningView
        inventory = self.source_replay(self.thortveitite_events())
        self.assertEqual(inventory.ship, {'thortveitite': 72})
        self.assertEqual(inventory.srv, {'thortveitite': 1})
        self.assertNotEqual(inventory.source_folder, str(self.replay_path.parent))
        expected = {lookup_by_symbol('thortveitite').frontier_id}
        self.assertEqual(self.view.goods_proxy.cargo_ids, expected)
        self.assertEqual(self.view.goods_proxy.rowCount(), 1)
        selected = self.view._selected_id
        self.view.hide()
        settings = QSettings(str(self.root / 'mining.ini'), QSettings.IniFormat)
        mining = MiningView(settings, controller=self.controller)
        self.addCleanup(mining.deleteLater)
        mining.show()
        self.assertEqual(mining.items['thortveitite'].data(2, Qt.UserRole), 72)
        self.assertEqual(mining.items['thortveitite'].data(1, Qt.UserRole), 1)
        mining.hide()
        self.view.show()
        self.app.processEvents()
        self.assertEqual(self.view.goods_proxy.cargo_ids, expected)
        self.assertEqual(self.view._selected_id, selected)
        self.view.goods_search.setText('Bier')
        self.assertEqual(self.view.goods_proxy.rowCount(), 0)
        self.view.goods_search.clear()
        self.assertEqual(self.view.goods_proxy.rowCount(), 1)
        # The market contains no matching commodity: no unrelated goods appear.
        self.view._snapshot['commodities'] = self.view._snapshot['commodities'][:-1]
        self.view._render_goods()
        self.assertEqual(self.view.goods_proxy.rowCount(), 0)

    def test_symlink_transfers_new_cargo_ship_switch_and_empty(self):
        self.source_replay(self.thortveitite_events())
        inventory = self.source_replay([dict(event='CargoTransfer', Transfers=[
            dict(Type='thortveitite', Count=1, Direction='toship')]), self.full_cargo('SRV', 0)])
        self.assertEqual(inventory.ship, {'thortveitite': 73})
        self.assertEqual(self.view.goods_proxy.rowCount(), 1)
        inventory = self.source_replay([dict(event='DockSRV', ID=57),
            dict(event='ShipyardSwap', StoreShipID=44, ShipID=62, ShipType='explorer_nx'),
            dict(event='Loadout', Ship='explorer_nx', ShipID=62, CargoCapacity=397, Modules=[])])
        self.assertEqual(inventory.ship_id, 62)
        self.assertEqual(self.view.goods_proxy.rowCount(), 1)
        self.source_replay([self.full_cargo('Ship', 0)])
        self.assertEqual(self.view.goods_proxy.rowCount(), 0)
        self.source_replay([dict(event='LaunchSRV', ID=57, SRVType='mev_rhino')])
        self.assertEqual(self.view.goods_proxy.rowCount(), 0)

    def test_symlink_helper_and_elite_restart_never_revive_stale_ship(self):
        self.source_replay(self.thortveitite_events())
        # A new reader (helper restart) rebuilds identical evidence, not a stale anchor.
        self.controller._last_inventory = None
        self.controller.loading.emit()
        self.assertIsNone(self.view.goods_proxy.cargo_ids)
        inventory = self.source_replay()
        self.assertEqual(inventory.ship, {'thortveitite': 72})
        self.assertEqual(self.view.goods_proxy.rowCount(), 1)
        fid = self.state.commander_fid
        inventory = self.source_replay([dict(event='Commander', FID=fid, Name='Synthetic'),
            dict(event='LoadGame', FID=fid, Ship='mev_rhino', ShipID=57), self.full_cargo('SRV', 1)],
            new_session=True)
        self.assertIsNone(inventory.ship)
        self.assertIsNone(self.view.goods_proxy.cargo_ids)
        self.assertEqual(self.view.cargo_notice.text(), tr('browse.cargo_unavailable'))
        self.source_replay([dict(event='Commander', FID=fid, Name='Synthetic'),
            dict(event='LoadGame', FID=fid, Ship='panthermkii', ShipID=44),
            dict(event='Loadout', Ship='panthermkii', ShipID=44, CargoCapacity=576, Modules=[]),
            self.full_cargo('Ship', 72)], new_session=True)
        self.assertEqual(self.view.goods_proxy.rowCount(), 1)


    def test_shared_quality_and_publication_signals(self):
        inventory = self.publish({'gold': 2})
        record = inventory.vehicle_records['Ship']
        for quality in ('confirmed', 'tracked', 'stale', 'unknown', 'inconsistent'):
            with self.subTest(quality=quality):
                record['quality'] = quality
                self.controller.ready.emit(inventory)
                if quality in ('confirmed', 'tracked'):
                    self.assertEqual(self.view.goods_proxy.rowCount(), 1)
                    self.assertEqual(self.view.cargo_notice.text(),
                        tr('browse.cargo_retained') if quality == 'tracked' else '')
                else:
                    self.assertIsNone(self.view.goods_proxy.cargo_ids)
        self.controller.loading.emit()
        self.assertIsNone(self.view.goods_proxy.cargo_ids)
        record['quality'] = 'confirmed'
        self.controller.ready.emit(inventory)
        self.assertEqual(self.view.goods_proxy.rowCount(), 1)

    def test_published_mining_stock_is_the_only_authority(self):
        inventory = self.publish({'gold': 2})
        # Disagreeing live snapshots/loadout/path spellings must not trigger a
        # second stock assessment in the trade filter.
        self.state.cargo_snapshot = {'inventory': [{'frontier_name': 'beer', 'count': 99}]}
        self.state.ship_loadout.loadout_stale = True
        self.state._inventory_conflict = ('synthetic',) * 6
        inventory.carrier = {'beer': 100}
        inventory.srv = {'platinum': 1}
        with patch('cmdrhelper.ship_cargo.current_ship_inventory', side_effect=AssertionError('no second assessment')), \
             patch.object(MiningInventoryReader, 'reconstruct', side_effect=AssertionError('no scan')):
            self.controller.publicationChanged.emit()
            self.assertEqual(self.view.goods_proxy.cargo_ids, {lookup_by_symbol('gold').frontier_id})
