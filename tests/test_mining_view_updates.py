"""Mining presentation reuse must never reuse authoritative inventory identity."""
import os
import tempfile
import unittest
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication
from cmdrhelper.mining_inventory import MiningInventory
from cmdrhelper.mining_market import MiningPrices, MiningSale
from cmdrhelper.ui.mining_view import MiningView
from test_mining_view import RefreshController


class MiningViewUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.settings = QSettings(str(Path(self.tmp.name) / 'settings.ini'), QSettings.IniFormat)
        self.inventory = MiningInventory(1, 'FA', ship={'gold': 12}, srv={}, carrier={'gold': 30}, carrier_id=7)
        self.controller = RefreshController()
        self.controller._last_inventory = self.inventory
        self.view = MiningView(self.settings, controller=self.controller)
        self.addCleanup(self.view.deleteLater)
        self.addCleanup(self.view.close)

    def test_identical_projection_adopts_new_identity_without_model_or_layout_changes(self):
        v = self.view
        new = deepcopy(self.inventory)
        new.commander_id, new.fid, new.carrier_id = 2, 'FB', 8
        new.source_folder = 'new-source'
        new.carrier_feed = {'verified': False}
        changes = []
        v.tree.model().dataChanged.connect(lambda *args: changes.append(args))
        v.tree.model().layoutChanged.connect(lambda *args: changes.append(args))
        with patch.object(v, '_apply_filters', wraps=v._apply_filters) as filters:
            v.set_inventory(new)
        self.assertIs(v._inventory, new)
        self.assertEqual(changes, [])
        filters.assert_not_called()

    def test_same_object_mutation_and_added_removed_goods_update_filter_and_sort(self):
        v = self.view
        v.only_stock.setChecked(True)
        v.tree.sortItems(2, Qt.DescendingOrder)
        self.inventory.ship['silver'] = 20
        self.inventory.ship['gold'] = 2
        v.set_inventory(self.inventory)
        self.assertEqual(v.items['silver'].data(2, Qt.UserRole), 20)
        self.assertFalse(v.items['silver'].isHidden())
        self.assertEqual(v.tree.topLevelItem(0), v.items['silver'])
        del self.inventory.ship['silver']
        v.set_inventory(self.inventory)
        self.assertTrue(v.items['silver'].isHidden())
        self.assertEqual(v.items['gold'].data(2, Qt.UserRole), 2)
        self.assertEqual(v.tree.topLevelItemCount(), len(v.items))

    def test_stale_and_unknown_never_become_confirmed_or_count_towards_total(self):
        v = self.view
        inv = deepcopy(self.inventory)
        inv.ship = None
        inv.ship_id, inv.source_folder = 3, 'source-a'
        inv.vehicle_records = {'Ship': {'ship_id': 3, 'source_folder': 'source-a', 'last_confirmed': {'gold': 12}}}
        v.set_inventory(inv)
        gold = v.items['gold']
        self.assertIsNone(gold.data(2, Qt.UserRole))
        self.assertEqual(gold.data(2, Qt.UserRole + 1), 'stale')
        self.assertEqual(gold.data(2, Qt.UserRole + 2), 12)
        self.assertIsNone(gold.data(4, Qt.UserRole))
        inv.source_folder = 'source-b'
        v.set_inventory(inv)
        self.assertEqual(gold.data(2, Qt.UserRole + 1), 'unknown')
        self.assertIsNone(gold.data(2, Qt.UserRole + 2))
        inv.ship = {'gold': 12}
        v.set_inventory(inv)
        self.assertEqual(gold.data(2, Qt.UserRole + 1), 'confirmed')
        self.assertEqual(gold.data(4, Qt.UserRole), 42)

    def test_carrier_record_changes_with_identical_amount_are_visible(self):
        inv = deepcopy(self.inventory)
        inv.carrier_records = {'gold': {'confirmed_at': '2026-10-01T12:00:00Z', 'status': 'confirmed'}}
        self.view.set_inventory(inv)
        before = self.view.items['gold'].toolTip(3)
        inv.carrier_records['gold']['status'] = 'inconsistent'
        self.view.set_inventory(inv)
        self.assertNotEqual(self.view.items['gold'].toolTip(3), before)
        self.assertEqual(self.view.items['gold'].data(3, Qt.UserRole), 30)

    def test_price_metadata_error_and_removal_are_not_suppressed(self):
        v = self.view
        quote = MiningSale('gold', 10000, datetime(2026, 10, 1, tzinfo=timezone.utc), 3, 'Port', 'System')
        prices = MiningPrices((quote,))
        v.set_market_prices(prices)
        changes = []
        v.tree.model().dataChanged.connect(lambda *args: changes.append(args))
        v.tree.model().layoutChanged.connect(lambda *args: changes.append(args))
        v.set_market_prices(deepcopy(prices))
        self.assertEqual(changes, [])
        before = v.items['gold'].toolTip(7)
        v.set_market_prices(MiningPrices((replace(quote, station='Other', count=7),)))
        self.assertNotEqual(v.items['gold'].toolTip(7), before)
        self.assertEqual(v.items['gold'].data(7, Qt.UserRole), 10000)
        v.set_market_prices(MiningPrices((replace(quote, price=20000),)))
        self.assertEqual(v.items['gold'].data(7, Qt.UserRole), 20000)
        v.set_market_prices(MiningPrices(status='error'))
        self.assertIsNone(v.items['gold'].data(7, Qt.UserRole))
        before = v.items['gold'].toolTip(7)
        v.set_market_prices(MiningPrices())
        self.assertNotEqual(v.items['gold'].toolTip(7), before)

    def test_repeated_snapshot_preserves_selection_sort_and_filter(self):
        v = self.view
        v.search.setText('gold')
        v.tree.sortItems(2, Qt.AscendingOrder)
        v.tree.setCurrentItem(v.items['gold'])
        v.set_inventory(deepcopy(self.inventory))
        self.assertEqual(v.tree.currentItem(), v.items['gold'])
        self.assertEqual(v.search.text(), 'gold')
        self.assertEqual(v.tree.header().sortIndicatorOrder(), Qt.AscendingOrder)
        self.assertTrue(v.items['silver'].isHidden())

    def test_ready_controller_initializes_inventory_once(self):
        calls = []
        original = MiningView.set_inventory
        def record(view, inventory):
            calls.append(inventory)
            original(view, inventory)
        with patch.object(MiningView, 'set_inventory', record):
            view = MiningView(self.settings, controller=self.controller)
        self.addCleanup(view.deleteLater)
        self.assertEqual(calls, [self.inventory])
        self.assertEqual(view.items['gold'].data(2, Qt.UserRole), 12)

    def test_nested_update_preserves_disabled_sorting_and_updates(self):
        v = self.view
        v.tree.setSortingEnabled(False)
        v.tree.setUpdatesEnabled(False)
        with v._table_update():
            self.inventory.ship['gold'] = 19
            v.set_inventory(self.inventory)
        self.assertFalse(v.tree.isSortingEnabled())
        self.assertFalse(v.tree.updatesEnabled())
        self.assertEqual(v.items['gold'].data(2, Qt.UserRole), 19)
