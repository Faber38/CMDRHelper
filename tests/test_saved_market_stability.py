"""Market browsing keeps its rows and reference across unrelated UI refreshes."""
from datetime import timedelta
import shutil
import sqlite3
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PySide6.QtCore import Qt, Signal
import test_saved_markets as saved
from test_saved_markets import Fixture, State, MarketStore, observation, NOW, MATE, ui, tr


class ImportState(State):
    databaseImportFinished = Signal(object, str)


class StabilityTests(Fixture, unittest.TestCase):
    setUpClass = saved.ViewTests.__dict__['setUpClass']
    cleanup = saved.ViewTests.cleanup
    wait = saved.ViewTests.wait
    select = saved.ViewTests.select

    def setUp(self):
        with patch('test_saved_markets.State', ImportState):
            saved.ViewTests.setUp(self)

    def test_reshow_retains_radius_rows_scroll_sort_selection_without_reads_or_resets(self):
        with MarketStore(self.market, clock=lambda: NOW) as store:
            for mid in range(4, 110):
                store.record_observation(observation(mid))
        self.view.reload(); self.wait()
        v = self.view
        v.radius.setValue(10)
        v.markets_table.sortByColumn(1, Qt.DescendingOrder)
        self.select(MATE)
        v.markets_table.verticalScrollBar().setValue(25)
        v.markets_table.horizontalScrollBar().setValue(20)
        positions = (v.markets_table.verticalScrollBar().value(),
                     v.markets_table.horizontalScrollBar().value())
        resets, visible_counts = [], []
        v.markets_model.modelReset.connect(lambda: resets.append(True))
        v.markets_proxy.layoutChanged.connect(lambda: visible_counts.append(v.markets_proxy.rowCount()))
        v.markets_proxy.rowsRemoved.connect(lambda *_: visible_counts.append(v.markets_proxy.rowCount()))
        v.clock = lambda: NOW + timedelta(minutes=2)
        with patch.object(ui, 'read_reference', side_effect=AssertionError('no reference read')), \
             patch.object(ui, 'read_markets', side_effect=AssertionError('no market read')), \
             patch.object(ui, 'read_market', side_effect=AssertionError('no detail read')):
            for _ in range(3):
                v.hide(); v.show(); self.wait()
                self.assertEqual(v.markets_proxy.rowCount(), 110)
                self.assertEqual(v._selected_id, MATE)
                self.assertTrue(v.markets_table.currentIndex().isValid())
                self.assertEqual((v.markets_table.verticalScrollBar().value(),
                                  v.markets_table.horizontalScrollBar().value()), positions)
        self.assertFalse(resets)
        self.assertTrue(all(count == 110 for count in visible_counts))
        self.assertEqual(v.markets_proxy.sortColumn(), 1)
        self.assertEqual(v.markets_proxy.sortOrder(), Qt.DescendingOrder)
        self.assertEqual(v.radius.value(), 10)
        self.assertEqual(v.markets_model.rows[0]['age'], 3720)
        with MarketStore(self.market, clock=lambda: NOW) as store:
            store.record_observation(observation(1000))
        self.state.observedMarketsChanged.emit(); self.wait()
        self.assertEqual(v.markets_proxy.rowCount(), 111)
        self.assertEqual(v._selected_id, MATE)
        self.assertEqual((v.markets_table.verticalScrollBar().value(),
                          v.markets_table.horizontalScrollBar().value()), positions)
        self.assertEqual(v.markets_proxy.sortOrder(), Qt.DescendingOrder)

    def test_pending_new_reference_has_no_old_distances_and_late_result_is_discarded(self):
        v = self.view
        self.select(MATE)
        gate, entered = Event(), Event()
        self.addCleanup(gate.set)
        original = ui.read_reference
        def delayed(source, name, cancel=None):
            if name == 'System 1':
                entered.set(); gate.wait(3)
                # Deliberately return even after cancellation: generations must protect us.
                return original(source, name)
            return original(source, name, cancel)
        with patch.object(ui, 'read_reference', delayed):
            v.reference.setText('System 1'); v.change_reference()
            self.assertTrue(entered.wait(1))
            self.assertIsNone(v._reference_coordinates)
            self.assertTrue(all(r['distance'] is None for r in v.markets_model.rows))
            self.assertEqual(v.reference_status.text(), tr('browse.reference_loading'))
            v.reference.setText('System 2'); v.change_reference()
            gate.set(); self.wait()
        self.assertEqual(v._reference_coordinates, original(v.source, 'System 2'))
        self.assertEqual(next(r for r in v.markets_model.rows if r['header'].market_id == 2)['distance'], 0)
        self.assertEqual(v._selected_id, MATE)

    def test_same_reference_refresh_keeps_rows_while_worker_pending(self):
        v = self.view
        v.radius.setValue(10)
        original = ui.read_reference
        gate, entered = Event(), Event()
        self.addCleanup(gate.set)
        def delayed(*args, **kwargs):
            entered.set(); gate.wait(3)
            return original(*args, **kwargs)
        resets = []
        v.markets_model.modelReset.connect(lambda: resets.append(True))
        with patch.object(ui, 'read_reference', delayed):
            v.reload()
            self.assertTrue(entered.wait(1))
            self.app.processEvents()
            self.assertEqual(v.markets_proxy.rowCount(), 4)
            gate.set(); self.wait()
        self.assertEqual(v.markets_proxy.rowCount(), 4)
        self.assertFalse(resets)

    def test_unknown_error_retry_and_database_import(self):
        v = self.view
        v.radius.setValue(10)
        v.reference.setText('No coords'); v.change_reference(); self.wait()
        self.assertEqual(v.markets_proxy.rowCount(), 0)
        self.assertEqual(v.reference_status.text(), tr('browse.reference_unknown'))
        with patch.object(ui, 'read_reference', side_effect=OSError('synthetic')):
            with self.assertLogs(ui.logger, level='ERROR'):
                v.change_reference(); self.wait()
        self.assertIsNone(v._reference_coordinates)
        self.assertEqual(v.markets_proxy.rowCount(), 0)
        with sqlite3.connect(self.database) as con:
            con.execute('UPDATE systems SET x=0,y=0,z=0 WHERE name="No coords"')
        self.state.databaseImportFinished.emit({}, '')
        self.wait()
        self.assertEqual(v.markets_proxy.rowCount(), 4)
        # A failed refresh of previously valid coordinates must not pretend success.
        with patch.object(ui, 'read_reference', side_effect=OSError('synthetic')):
            with self.assertLogs(ui.logger, level='ERROR'):
                v.reload(); self.wait()
        self.assertEqual(v.markets_proxy.rowCount(), 0)
        v.change_reference(); self.wait()
        self.assertEqual(v.markets_proxy.rowCount(), 4)

    def test_new_database_same_reference_does_not_reuse_old_coordinates(self):
        v = self.view
        other = self.root / 'other.db'
        shutil.copyfile(self.database, other)
        with sqlite3.connect(other) as con:
            con.execute('UPDATE systems SET x=30 WHERE name="System 0"')
        self.state.database = SimpleNamespace(path=other)
        v.hide(); v.show()
        self.assertIsNone(v._reference_coordinates)
        self.wait()
        self.assertEqual(v._reference_coordinates.x, 30)

    def test_live_reference_change_and_real_market_addition(self):
        v = self.view
        self.select(MATE)
        self.state.system = 'System 2'
        v.hide(); v.show(); self.wait()
        self.assertEqual(v._reference_name, 'System 2')
        self.assertEqual(next(r for r in v.markets_model.rows if r['header'].market_id == 2)['distance'], 0)
        with MarketStore(self.market, clock=lambda: NOW) as store:
            store.record_observation(observation(1000))
            store.record_observation(observation(MATE, age=0, count=2, name='Mate City'))
        self.state.observedMarketsChanged.emit(); self.wait()
        self.assertEqual(v.markets_model.rowCount(), 5)
        self.assertEqual(v._selected_id, MATE)
        self.assertEqual(v.goods_model.rowCount(), 2)
