"""Mission badges use real cargo normalization, validation and both trade views."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QStyleOptionViewItem

from cmdrhelper.cargo import cargo_snapshot, normalize_inventory, read_cargo_snapshot
from cmdrhelper.commodity_master import lookup_by_symbol
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.ship_cargo import current_ship_cargo, current_ship_inventory
from cmdrhelper.ui.commodity_picker import RARE_ROLE
from cmdrhelper.ui.mission_cargo import MISSION_CARGO_ROLE
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.ui.trade_view import TradeView
import test_saved_market_cargo_filter as existing


MID = 1070302284
NAME = 'advancedmedicines'


def item(count, mission=None, name=NAME):
    row = dict(Name=name, Count=count, Stolen=0)
    if mission is not None:
        row['MissionID'] = mission
    return row


class MissionCargoSnapshotTests(unittest.TestCase):
    def test_merge_preserves_totals_stolen_and_each_mission(self):
        rows = [item(20), item(100, MID), item(90, MID, NAME.upper()),
                dict(item(6, MID + 1), Stolen=2)]
        row = normalize_inventory(rows)[0]
        self.assertEqual(row['count'], 216)
        self.assertEqual(row['stolen'], 2)
        self.assertEqual(row['mission_counts'], {MID: 190, MID + 1: 6})
        self.assertNotIn('mission_counts', normalize_inventory([item(196)])[0])

    def test_invalid_ids_never_mark_cargo_and_large_ids_remain_exact(self):
        for mid in (None, False, True, 0, -1, '1070302284', 1.5, {}, []):
            with self.subTest(mid=mid):
                row = normalize_inventory([item(196, mid)])[0]
                self.assertEqual(row['count'], 196)
                self.assertNotIn('mission_counts', row)
        self.assertEqual(normalize_inventory([item(1, 2**64-1)])[0]['mission_counts'],
                         {2**64-1: 1})
        self.assertNotIn('mission_counts', normalize_inventory([item(0, MID), item(1)])[0])

    def test_inline_and_matching_sidecar_preserve_same_metadata(self):
        payload = dict(event='Cargo', Vessel='Ship', timestamp='2026-11-03T13:39:08Z',
                       Count=216, Inventory=[item(196, MID), item(20)])
        inline = cargo_snapshot(payload, fid='SYNTHETIC', ship_id=7, cargo_capacity=500)
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'Cargo.json'
            path.write_text(json.dumps(payload))
            trigger = {k: v for k, v in payload.items() if k != 'Inventory'}
            self.assertEqual(read_cargo_snapshot(path, trigger, fid='SYNTHETIC', ship_id=7,
                                                cargo_capacity=500), inline)
            trigger['timestamp'] = '2026-11-03T13:39:09Z'
            self.assertIsNone(read_cargo_snapshot(path, trigger, fid='SYNTHETIC', attempts=1))


class MissionCargoViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        existing.CargoFilterTests.setUpClass()
        cls.app = existing.CargoFilterTests.app

    def setUp(self):
        previous = get_language()
        self.addCleanup(set_language, previous)
        set_language('de')
        self.fixture = existing.CargoFilterTests()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.market = self.fixture.view
        self.state = self.fixture.state
        self.state.ship_loadout.cargo_capacity = 500
        self.state.observed_markets.cache = Mock()
        self.state.observed_markets.cache.storage_stats.return_value = (0, 0)
        self.trade = TradeView(self.state, provider=Mock(), pool=Mock())
        self.addCleanup(self.close_trade)
        self.market._snapshot['commodities'] = [dict(
            commodity_id=lookup_by_symbol(name).frontier_id, symbol=name,
            commander_buy_price=10, commander_sell_price=9, supply=20, demand=30)
            for name in (NAME, 'gold', 'jaquesquinentianstill')]
        self.market._render_goods()

    def close_trade(self):
        self.trade.close()
        self.trade.deleteLater()
        self.app.processEvents()

    def cargo(self, rows):
        event = self.fixture.feed('Cargo', Vessel='Ship', Count=sum(r['Count'] for r in rows),
                                  Inventory=rows)
        snapshot = cargo_snapshot(event, fid=self.state.commander_fid, ship_id=7, cargo_capacity=500)
        snapshot['context'] = dict(self.fixture.tracker.last_cargo_context)
        self.state.cargo_snapshot = snapshot
        self.state.ship_inventory = current_ship_inventory(self.state)
        self.state.ship_cargo_total = current_ship_cargo(self.state)
        self.state.cargoSnapshotChanged.emit(snapshot)

    def indices(self):
        return (self.trade.cargo_list.model().index(0, 0), self.market.goods_model.index(0, 0))

    def assert_details(self, expected):
        for index in self.indices():
            details = index.data(MISSION_CARGO_ROLE)
            self.assertEqual(tuple(details) if details else None, expected)

    def test_normal_pure_mixed_multiple_and_same_total_updates(self):
        for rows, details, tooltip in (
            ([item(196)], None, None),
            ([item(196, MID)], (196, 196, 1), 'Missionsfracht: 196 t'),
            ([item(20), item(196, MID)], (196, 216, 1), 'Missionsfracht: 196 t von insgesamt 216 t'),
            ([item(20), item(100, MID), item(96, MID+1)], (196, 216, 2), 'Für 2 Missionen'),
            ([item(116), item(100, MID+1)], (100, 216, 1), 'Missionsfracht: 100 t von insgesamt 216 t'),
            ([item(216)], None, None),
        ):
            with self.subTest(details=details):
                self.cargo(rows)
                self.assert_details(details)
                self.assertEqual(self.market.goods_proxy.rowCount(), 1)
                self.assertEqual(self.trade.cargo_list.item(0).data(Qt.UserRole)[1], sum(r['Count'] for r in rows))
                if tooltip:
                    for index in self.indices():
                        self.assertIn(tooltip, index.data(Qt.ToolTipRole))
                    self.assertIn('Eigene Schiffs-Fracht', self.indices()[1].data(Qt.ToolTipRole))

    def test_markets_all_modes_reload_and_filter_sort_prices_unchanged(self):
        self.cargo([item(196, MID)])
        self.market.goods_table.sortByColumn(2, Qt.DescendingOrder)
        before = [dict(row) for row in self.market.goods_model.rows]
        self.market.all_goods.click()
        self.assert_details((196, 196, 1))
        self.assertEqual(self.market.goods_proxy.rowCount(), 3)
        self.market._render_goods()
        self.assert_details((196, 196, 1))
        self.market.cargo_only.click()
        with patch.object(self.market.goods_proxy, 'invalidateFilter') as invalidate:
            self.cargo([item(196)])
            self.assert_details(None)
            self.cargo([item(196, MID+1)])
            self.assert_details((196, 196, 1))
            invalidate.assert_not_called()
        self.assertEqual(self.market.goods_table.horizontalHeader().sortIndicatorSection(), 2)
        for old, new in zip(before, self.market.goods_model.rows):
            self.assertEqual({k:v for k,v in old.items() if k != 'mission_cargo'},
                             {k:v for k,v in new.items() if k != 'mission_cargo'})

    def test_delivery_abandonment_and_new_snapshot(self):
        self.cargo([item(196, MID)])
        for event in ('CargoDepot', 'MissionCompleted', 'MissionAbandoned', 'MissionFailed', 'MissionAccepted'):
            self.fixture.feed(event, MissionID=MID)
            self.state.changed.emit()
            # Deliberately retain the old cached inventory to test signal order.
            self.assert_details(None)
            self.cargo([item(100, MID)])
            self.assert_details((100, 100, 1))
        self.cargo([])
        self.assertEqual(self.trade.cargo_list.count(), 0)
        self.assertEqual(self.market.goods_proxy.rowCount(), 0)
        self.assertIsNone(self.market.goods_model.index(0, 0).data(MISSION_CARGO_ROLE))

    def test_snapshot_signal_before_cached_inventory_never_mixes_quantities(self):
        self.cargo([item(196, MID)])
        old = self.state.ship_inventory
        self.cargo([item(100, MID)])
        new = self.state.ship_inventory
        self.state.ship_inventory = old
        self.state.cargoSnapshotChanged.emit(self.state.cargo_snapshot)
        self.assertIsNone(self.indices()[0].data(MISSION_CARGO_ROLE))
        self.assertEqual(tuple(self.indices()[1].data(MISSION_CARGO_ROLE)), (100, 100, 1))
        self.state.ship_inventory = new
        self.state.cargoSnapshotChanged.emit(self.state.cargo_snapshot)
        self.assert_details((100, 100, 1))

    def test_commander_ship_and_unavailable_context_clear_cached_badges(self):
        self.cargo([item(196, MID)])
        for obj, field, value, signal in (
            (self.state, 'commander_fid', 'OTHER', self.state.changed),
            (self.state, 'viewed_commander_id', 2, self.state.viewedCommanderChanged),
            (self.state.ship_loadout, 'ship_id', 8, self.state.shipLoadoutChanged),
            (self.state.ship_loadout, 'loadout_stale', True, self.state.shipLoadoutChanged),
            (self.state, '_cargo_blocked', True, self.state.changed),
            (self.state, 'cargo_snapshot', None, self.state.cargoSnapshotChanged),
        ):
            with self.subTest(field=field):
                old = getattr(obj, field, None)
                setattr(obj, field, value)
                signal.emit() if signal is self.state.changed else signal.emit(None)
                self.assert_details(None)
                setattr(obj, field, old)
                self.state.changed.emit()
                self.assert_details((196, 196, 1))
        self.fixture.feed('ShipyardSwap', ShipID=8, Ship='python')
        self.state.changed.emit()
        self.assert_details(None)

    def test_badges_render_both_themes_and_tooltips_all_languages(self):
        self.cargo([item(20), item(100, MID), item(96, MID+1)])
        for language, translations in _TRANSLATIONS.items():
            set_language(language)
            for suffix in ('', '_mixed', '_missions', '_own'):
                self.assertIn('trade.mission_cargo'+suffix, translations)
            # Rebuild selling text just as the existing UI does on recreation.
            self.trade._cargo_key = None
            self.trade.refresh_cargo()
            for index in self.indices():
                self.assertIn(tr('trade.mission_cargo_mixed', count='196', total='216'),
                              index.data(Qt.ToolTipRole))
                self.assertIn(tr('trade.mission_cargo_missions', count='2'), index.data(Qt.ToolTipRole))
            for stylesheet in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                for view, index in ((self.trade.cargo_list, self.indices()[0]),
                                    (self.market.goods_table, self.indices()[1])):
                    view.setStyleSheet(stylesheet)
                    view.ensurePolished()
                    delegate = view.itemDelegateForColumn(0) or view.itemDelegate()
                    option = QStyleOptionViewItem()
                    option.initFrom(view)
                    option.rect = QRect(0, 0, 500, 30)
                    delegate.initStyleOption(option, index)
                    self.assertFalse(option.icon.isNull())
                    image = QImage(500, 30, QImage.Format_ARGB32)
                    image.fill(Qt.transparent)
                    painter = QPainter(image)
                    delegate.paint(painter, option, index)
                    painter.end()
                    self.assertTrue(any(image.pixelColor(x, y).blue() > image.pixelColor(x, y).red()+30
                                        for x in range(40) for y in range(30)))

    def test_rare_marker_and_tooltip_remain(self):
        self.cargo([item(8, MID, 'jaquesquinentianstill')])
        row = self.trade.cargo_list.item(0)
        self.assertTrue(row.data(RARE_ROLE))
        self.assertEqual(tuple(row.data(MISSION_CARGO_ROLE)), (8, 8, 1))
        self.assertIn(tr('trade.rare_sell_excluded'), row.toolTip())
        self.assertIn('Missionsfracht: 8 t', row.toolTip())
        self.assertFalse(row.flags() & Qt.ItemIsUserCheckable)
