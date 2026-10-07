"""DB-backed day navigation and explicit manual deletion confirmations."""
from datetime import timedelta
from unittest.mock import patch
from PySide6.QtWidgets import QMessageBox
import unittest
from tests import test_powerplay_store as store
from tests.test_powerplay_store import DAY, delivery, credit
from tests import test_powerplay as base


class HistoryViewTests(unittest.TestCase):
    journal = store.StoreTests.journal
    sync = store.StoreTests.sync
    setUpClass = classmethod(base.PowerplayViewTests.setUpClass.__func__)

    def setUp(self):
        store.StoreTests.setUp(self)
        clock=patch('cmdrhelper.ui.powerplay_view.local_today',return_value=DAY)
        self.today=clock.start();self.addCleanup(clock.stop)
        self.state=base.ViewState()
        self.state.database=self.db
        self.session=self.journal([delivery(),credit(0,48,12831)])
        self.sync(self.session)
        self.state.commander_id=self.session['commander_id']
        self.state.commander='Test A'
        self.state.powerplay.merits=self.db.powerplay_merits(self.state.commander_id)
        self.view=base.PowerplayView(self.state)
        self.addCleanup(self.view.close)

    def test_navigation_and_running_midnight(self):
        self.assertEqual(self.view.recent.rowCount(),1)
        self.assertFalse(self.view.next_day.isEnabled())
        self.view._move_day(-1)
        self.assertEqual(self.view.selected_day,DAY-timedelta(days=1))
        self.assertEqual(self.view.recent.rowCount(),0)
        self.today.return_value=DAY+timedelta(days=1)
        self.view.render()
        self.assertEqual(self.view.selected_day,DAY-timedelta(days=1))
        self.view._today()
        self.assertIsNone(self.view.selected_day)
        self.assertEqual(self.view.recent.rowCount(),0)
        self.view._move_day(-1)
        self.assertEqual(self.view.recent.rowCount(),1)
        self.view._move_day(2)
        self.assertIsNone(self.view.selected_day)
        self.assertFalse(self.view.next_day.isEnabled())

    def test_follow_today_rollover_without_selection(self):
        self.today.return_value=DAY+timedelta(days=1)
        self.view.render()
        self.assertIsNone(self.view.selected_day)
        self.assertEqual(self.view.recent.rowCount(),0)

    def test_delete_requires_confirmation_and_preserves_total(self):
        with patch.object(QMessageBox,'question',return_value=QMessageBox.No):
            self.view._delete_history(None)
        self.assertEqual(self.view.recent.rowCount(),1)
        with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes) as ask:
            self.view._delete_history(None)
        self.assertIn('Test A',ask.call_args.args[2])
        self.assertEqual(self.view.recent.rowCount(),0)
        self.assertEqual(self.db.powerplay_merits(self.state.commander_id),12831)
        self.assertIsNone(self.view.selected_day)
