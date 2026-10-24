"""Actual sales: synthetic journals/database only, no network or production writes."""
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from threading import Event
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject, QSettings, Signal, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from cmdrhelper.mining_market import read_mining_prices
from cmdrhelper.mining_inventory import MiningInventory
from cmdrhelper.ui.mining_view import MiningView


def sale(price, stamp='2026-10-24T14:54:19Z', symbol='grandidierite'):
    return dict(event='MarketSell', timestamp=stamp, Type=symbol, Count=115, SellPrice=price)


class State(QObject):
    inventoryChanged = Signal()
    miningSalesChanged = Signal()
    viewedCommanderChanged = Signal(object)
    commanderIdentityChanged = Signal(object, str, str)
    journalIndexReady = Signal()
    databaseImportFinished = Signal()


class Inventory(QObject):
    loading = Signal()
    ready = Signal(object)
    refreshFinished = Signal(str)
    def refresh_now(self): pass


class MiningMarketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        temp = TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name); self.path = self.root/'db.sqlite'
        with sqlite3.connect(self.path) as con:
            con.executescript('CREATE TABLE commanders(id INTEGER, fid TEXT); '
                'INSERT INTO commanders VALUES(1,"F1"),(2,"F2"); '
                'CREATE TABLE journal_sessions(journal_file TEXT, commander_id INTEGER, fid_seen TEXT, attribution_status TEXT);')
        self.cache = {}
        self.events = [dict(event='Commander', FID='F1'),
                       dict(event='Docked', StationName='Mate City', StarSystem='Musca Dark Region HM-V c2-37'),
                       sale(551650, '2026-10-23T12:00:00Z'), sale(49595)]
        self.journal = self.add_journal(self.events)

    def add_journal(self, events, cid=1, name='Journal.2026-10-24T100000.01.log'):
        path = self.root/name
        path.write_text(''.join(json.dumps(e)+'\n' for e in events))
        with sqlite3.connect(self.path) as con:
            con.execute('INSERT INTO journal_sessions VALUES(?,?,?,?)', (str(path), cid, 'F'+str(cid), 'identified'))
        return path

    def append(self, *events):
        with self.journal.open('a') as stream:
            for event in events: stream.write(json.dumps(event)+'\n')

    def read(self, cid=1, **kw):
        return read_mining_prices(self.path, cid, cache=self.cache, **kw)

    def test_lower_higher_multiple_commodities_event_time_and_restart(self):
        self.assertEqual(self.read().quotes[0].price, 49595)
        self.append(sale(600000, '2026-10-25T00:00:00Z'), sale(9, symbol='gold'), sale(999999, '2020-01-01T00:00:00Z'))
        values = {q.symbol:q.price for q in self.read().quotes}
        self.assertEqual(values, dict(grandidierite=600000, gold=9))
        self.assertEqual(read_mining_prices(self.path, 1), self.read())

    def test_ties_use_file_chronology_and_offset_stably(self):
        self.append(sale(12))
        self.add_journal([dict(event='Commander', FID='F1'), sale(13), sale(14)], name='Journal.2026-10-24T110000.01.log')
        self.assertEqual(self.read().quotes[0].price, 14)
        self.cache.clear()
        self.assertEqual(self.read().quotes[0].price, 14)

    def test_identity_filters_and_mixed_file_rejected(self):
        self.add_journal([dict(event='Commander', FID='F2'), sale(77)], 2, 'other.log')
        self.assertEqual(self.read(2).quotes[0].price, 77)
        self.assertEqual(self.read().quotes[0].price, 49595)
        self.append(dict(event='LoadGame', FID='F2'), sale(999))
        self.assertEqual(self.read().quotes, ())
        with sqlite3.connect(self.path) as con:
            con.execute("UPDATE journal_sessions SET attribution_status='ambiguous'")
        self.assertEqual(self.read(2).quotes, ())

    def test_system_change_missing_station_and_no_offers_or_buy(self):
        self.append(dict(event='FSDJump', StarSystem='Next'), sale(50),
                    dict(event='MarketBuy', Type='gold', BuyPrice=99, Count=1),
                    dict(event='Market', Items=[dict(Name='gold', SellPrice=900)]))
        q = self.read().quotes[0]
        self.assertEqual((q.price, q.system, q.station), (50, 'Next', ''))
        self.assertEqual(self.read(2).quotes, ())

    def test_partial_lines_invalid_prices_and_missing_database(self):
        self.append(sale(-1), {**sale(999), 'timestamp':'invalid'}, {**sale(999), 'Count':0})
        with self.journal.open('a') as stream: stream.write(json.dumps(sale(999)))
        self.assertEqual(self.read().quotes[0].price, 49595)
        missing = self.root/'missing'
        self.assertEqual(read_mining_prices(missing, 1).status, 'missing')
        self.assertFalse(missing.exists())
        cancelled = Event(); cancelled.set()
        self.assertEqual(self.read(cancel=cancelled).status, 'cancelled')

    def wait(self, predicate):
        deadline = time.monotonic()+5
        while not predicate() and time.monotonic()<deadline: QTest.qWait(5)
        self.assertTrue(predicate())

    def view(self):
        state = State(); state.database = SimpleNamespace(path=self.path)
        state.settings = QSettings(str(self.root/'settings.ini'), QSettings.IniFormat)
        state.commander_id = state.viewed_commander_id = 1
        view = MiningView(state.settings, state=state, controller=Inventory())
        self.addCleanup(view.deleteLater); self.addCleanup(view.close)
        self.addCleanup(view.market_controller.pool.waitForDone)
        return state, view

    def test_live_update_commander_switch_tooltip_theme_and_other_columns(self):
        state, view = self.view(); view.show()
        self.wait(lambda:bool(view.own_market_prices))
        view.set_inventory(MiningInventory(1, 'F1', srv={'grandidierite':2}, ship={'grandidierite':3}, carrier={'grandidierite':4}))
        item = view.items['grandidierite']
        before = [item.data(i, Qt.UserRole) for i in range(1,7)]
        for light in (True, False):
            view.set_light_mode(light)
            self.assertEqual(item.data(7, Qt.UserRole), 49595)
            for value in ('Mate City', 'Musca Dark Region HM-V c2-37', '115', '24.10.26', '49.595'):
                self.assertIn(value, item.toolTip(7))
        self.append(sale(40, '2026-10-25T00:00:00Z'))
        state.miningSalesChanged.emit()
        self.assertEqual(item.data(7, Qt.UserRole), 49595)
        self.wait(lambda:item.data(7, Qt.UserRole)==40)
        self.assertEqual(before, [item.data(i, Qt.UserRole) for i in range(1,7)])
        state.viewed_commander_id = 2; state.viewedCommanderChanged.emit(2)
        self.assertEqual(view.own_market_prices, {})
        self.wait(lambda:not view.market_controller._running and not view.market_controller.timer.isActive())
        self.assertIsNone(item.data(7, Qt.UserRole))
        state.viewed_commander_id = 1; state.viewedCommanderChanged.emit(1)
        self.wait(lambda:item.data(7, Qt.UserRole)==40)
        view.hide(); view.show()
        self.assertEqual(item.data(7, Qt.UserRole), 40)

    def test_read_error_preserves_reference(self):
        _, view = self.view()
        with patch('cmdrhelper.mining_market_controller.read_mining_prices', side_effect=OSError('synthetic')):
            with self.assertLogs('cmdrhelper.mining_market_controller', level='ERROR'):
                view.show(); self.wait(lambda:view._market_status=='error')
        self.assertEqual(view.items['gold'].data(5, Qt.UserRole), 48005)
        self.assertIsNone(view.items['gold'].data(7, Qt.UserRole))

    def test_late_worker_result_discarded_after_commander_switch(self):
        from cmdrhelper.mining_market import MiningPrices
        _, view = self.view(); controller = view.market_controller
        controller.set_active(True)
        old_generation = controller._generation
        controller.request()
        controller._finished(old_generation, self.read())
        self.assertFalse(view.own_market_prices)
        controller.set_active(False)

    def test_tooltip_all_languages_missing_station_and_old_sale_has_no_age_limit(self):
        from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
        self.addCleanup(set_language, get_language())
        self.append(dict(event='FSDJump', StarSystem='Next'), sale(5, '2026-10-25T00:00:00Z'))
        _, view = self.view()
        for language in _TRANSLATIONS:
            set_language(language)
            view.settings.setValue('trade/max_age_hours', 1)
            view.set_market_prices(self.read())
            item = view.items['grandidierite']
            self.assertEqual(item.data(7, Qt.UserRole), 5)
            self.assertIn('—', item.toolTip(7))
            self.assertIn('Next', item.toolTip(7))
            self.assertNotIn('mining.', item.toolTip(7))

    def test_missing_journal_fails_instead_of_showing_unverified_older_price(self):
        self.journal.unlink()
        with self.assertRaises(OSError): self.read()

    def test_slow_worker_keeps_gui_live_and_reloads_after_identity_change(self):
        state, view = self.view()
        entered, release = Event(), Event()
        original = read_mining_prices
        calls = []
        def slow(*args, **kwargs):
            result = original(*args, **kwargs)
            calls.append(args[1])
            if len(calls) == 1:
                entered.set(); release.wait(5)
            return result
        try:
            with patch('cmdrhelper.mining_market_controller.read_mining_prices', slow):
                view.show(); self.wait(entered.is_set)
                state.viewed_commander_id = 2; state.viewedCommanderChanged.emit(2)
                QTest.qWait(20)
                self.assertFalse(view.own_market_prices)
                release.set()
                self.wait(lambda:len(calls)==2 and not view.market_controller._running)
                self.assertEqual(calls, [1,2])
                self.assertFalse(view.own_market_prices)
        finally: release.set()

    def test_previous_column_layout_preserved(self):
        _, view = self.view()
        settings = view.settings
        previous = list(MiningView.COLUMNS[:-1]); widths = [350,70,71,72,73,170,160]
        settings.setValue('materials/mining/columns', dict(version=1, columns=previous,
            widths=widths, order=[6,0,1,2,3,4,5]))
        restored = MiningView(settings); self.addCleanup(restored.deleteLater)
        self.assertEqual([restored.tree.header().logicalIndex(i) for i in range(7)], [6,0,1,2,3,4,5])
        self.assertEqual(restored.tree.header().logicalIndex(7), 7)

    def test_inventory_events_do_not_read_or_write_prices(self):
        from cmdrhelper.state import AppState
        from cmdrhelper.ui.mining_view import _MiningItem
        state, view = self.view(); view.show()
        self.wait(lambda: bool(view.own_market_prices))
        state._journal_index_sessions = [dict(journal_file=str(self.journal), commander_id=1,
                                             fid_seen='F1', attribution_status='identified')]
        AppState._notify_mining_sales(state, [])
        self.wait(lambda: not view.market_controller._running and not view.market_controller.timer.isActive())
        price = view.items['grandidierite'].text(7)
        writes = []
        original = _MiningItem.setText
        def text(item, column, value):
            if column == 7: writes.append(value)
            return original(item, column, value)
        with patch('cmdrhelper.mining_market_controller.read_mining_prices', side_effect=AssertionError('No price read')), \
                patch.object(_MiningItem, 'setText', text):
            for event in ['MiningRefined']*10 + ['Cargo', 'CollectCargo', 'CargoTransfer',
                                               'MaterialCollected', 'Docked', 'FSDJump']:
                self.append(dict(event=event))
                state.inventoryChanged.emit()
                AppState._notify_mining_sales(state, [dict(event=event)])
            QTest.qWait(250)
            self.assertFalse(view.market_controller.timer.isActive())
            self.assertFalse(view.market_controller._running)
            self.assertEqual(view.items['grandidierite'].text(7), price)
            self.assertEqual(writes, [])

    def test_event_forwarding_ignores_file_growth_but_detects_sales_and_attribution(self):
        from cmdrhelper.state import AppState
        state = State(); calls = []; state.miningSalesChanged.connect(lambda: calls.append(1))
        row = dict(journal_file=str(self.journal), commander_id=1, fid_seen='F1', attribution_status='identified')
        state._journal_index_sessions = [row]
        AppState._notify_mining_sales(state, [])
        self.assertEqual(len(calls), 1)
        row.update(file_size=9000, modified_ns=123, last_read_offset=9000)
        AppState._notify_mining_sales(state, [dict(event='MiningRefined')])
        self.assertEqual(len(calls), 1)
        AppState._notify_mining_sales(state, [sale(8)])
        self.assertEqual(len(calls), 2)
        row['attribution_status'] = 'ambiguous'
        AppState._notify_mining_sales(state, [])
        self.assertEqual(len(calls), 3)

    def test_unchanged_result_and_reopening_do_not_render_or_read(self):
        state, view = self.view(); view.show()
        self.wait(lambda: bool(view.own_market_prices))
        with patch.object(view, '_render_market_prices', wraps=view._render_market_prices) as render:
            state.miningSalesChanged.emit()
            self.wait(lambda: not view.market_controller._running and not view.market_controller.timer.isActive())
            render.assert_not_called()
        with patch('cmdrhelper.mining_market_controller.read_mining_prices', side_effect=AssertionError('No reopening read')):
            view.hide(); view.show(); QTest.qWait(200)
            self.assertEqual(view.items['grandidierite'].data(7, Qt.UserRole), 49595)

    def test_import_zero_skipped_unknown_or_changed_import_refreshes(self):
        state, view = self.view(); view.show()
        self.wait(lambda: bool(view.own_market_prices))
        with patch('cmdrhelper.mining_market_controller.read_mining_prices', wraps=read_mining_prices) as read:
            view.market_controller._import_finished({'imported_journals':0}, '')
            QTest.qWait(150); read.assert_not_called()
            self.append(sale(7, '2026-10-25T00:00:00Z'))
            view.market_controller._import_finished({'imported_journals':1}, '')
            self.assertEqual(view.items['grandidierite'].data(7, Qt.UserRole), 49595)
            self.wait(lambda:view.items['grandidierite'].data(7, Qt.UserRole)==7)
            self.assertEqual(read.call_count, 1)
            state.databaseImportFinished.emit()
            self.wait(lambda:read.call_count==2 and not view.market_controller._running)

    def test_only_changed_price_cell_is_written(self):
        from cmdrhelper.ui.mining_view import _MiningItem
        state, view = self.view(); view.show()
        self.wait(lambda: bool(view.own_market_prices))
        writes = []; original = _MiningItem.setText
        def text(item, column, value):
            if column == 7: writes.append((item.data(0, Qt.UserRole), value))
            return original(item, column, value)
        with patch.object(_MiningItem, 'setText', text):
            self.append(sale(12, '2026-10-25T00:00:00Z'))
            state.miningSalesChanged.emit()
            self.wait(lambda:view.items['grandidierite'].data(7, Qt.UserRole)==12)
        self.assertEqual(writes, [('grandidierite', '12')])

    def test_refresh_error_keeps_accepted_prices_and_tooltip(self):
        state, view = self.view(); view.show()
        self.wait(lambda: bool(view.own_market_prices))
        tooltip = view.items['grandidierite'].toolTip(7)
        with patch('cmdrhelper.mining_market_controller.read_mining_prices', side_effect=OSError('synthetic')):
            with self.assertLogs('cmdrhelper.mining_market_controller', level='ERROR'):
                state.miningSalesChanged.emit(); self.wait(lambda:view._market_status=='error')
        self.assertEqual(view.items['grandidierite'].data(7, Qt.UserRole), 49595)
        self.assertEqual(view.items['grandidierite'].toolTip(7), tooltip)

    def test_source_change_removes_disqualified_sale_on_success(self):
        from cmdrhelper.state import AppState
        state, view = self.view(); view.show()
        self.wait(lambda: bool(view.own_market_prices))
        with sqlite3.connect(self.path) as con:
            con.execute("UPDATE journal_sessions SET attribution_status='ambiguous'")
        state._journal_index_sessions = [dict(journal_file=str(self.journal), commander_id=1,
                                              fid_seen='F1', attribution_status='ambiguous')]
        AppState._notify_mining_sales(state, [])
        self.wait(lambda: not view.own_market_prices)

    def test_slow_sale_refresh_keeps_price_and_tooltip_until_replacement(self):
        state, view = self.view(); view.show()
        self.wait(lambda: bool(view.own_market_prices))
        item = view.items['grandidierite']; tooltip = item.toolTip(7)
        entered, release = Event(), Event()
        def slow(*args, **kwargs):
            entered.set(); release.wait(5)
            return read_mining_prices(*args, **kwargs)
        try:
            with patch('cmdrhelper.mining_market_controller.read_mining_prices', slow):
                self.append(sale(11, '2026-10-25T00:00:00Z'))
                state.miningSalesChanged.emit(); self.wait(entered.is_set)
                self.assertEqual(item.data(7, Qt.UserRole), 49595)
                self.assertEqual(item.toolTip(7), tooltip)
                release.set(); self.wait(lambda:item.data(7, Qt.UserRole)==11)
        finally: release.set()

    def test_sale_while_hidden_is_loaded_when_reopened(self):
        state, view = self.view(); view.show()
        self.wait(lambda: bool(view.own_market_prices))
        view.hide()
        self.append(sale(13, '2026-10-25T00:00:00Z'))
        state.miningSalesChanged.emit()
        self.assertFalse(view.market_controller.timer.isActive())
        view.show()
        self.wait(lambda:view.items['grandidierite'].data(7, Qt.UserRole)==13)
