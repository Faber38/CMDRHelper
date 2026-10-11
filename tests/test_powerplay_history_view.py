"""DB-backed day navigation and explicit manual deletion confirmations."""
from datetime import date, timedelta
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

    def test_live_totals_flow_through_database_state_signal_and_rank_view(self):
        from cmdrhelper.journal_reader import read_latest_state
        from cmdrhelper.powerplay import decode_powers_cache
        from cmdrhelper.powerplay_rank import rank_progress
        from cmdrhelper.ui.styles import DARK_STYLESHEET
        from tests.test_powerplay_ranks import rank_document, encoded
        from cmdrhelper.i18n import set_language
        set_language('de')
        self.today.return_value=date(2026,10,9)
        rows=[dict(timestamp='2026-10-09T09:42:24Z',event='SearchAndRescue',
                   Name='wreckagecomponents',Count=6)]
        rows += [dict(timestamp='2026-10-09T09:42:25Z',event='PowerplayMerits',
                      Power='Nakato Kaine',MeritsGained=gain,TotalMerits=total)
                 for gain,total in ((3140,94567),(340,94907),(2800,97707))]
        prior=self.journal(rows,name='Journal.2026-10-09T110541.01.log',fid='F12520967')
        snapshot=self.journal([dict(timestamp='2026-10-09T10:02:22Z',event='Powerplay',
                                   Power='Nakato Kaine',Rank=14,Merits=94567)],
                              name='Journal.2026-10-09T120136.01.log',fid='F12520967')
        self.sync(prior,snapshot)
        self.state.commander_id=snapshot['commander_id']
        data=read_latest_state(self.folder,powerplay_history=False)
        self.assertEqual(data['powerplay'].merits,94567)
        # Same projection assignment used by AppState.refresh(), followed by
        # its existing signal; no UI-side merit calculation or extra polling.
        self.state.powerplay=data['powerplay']
        self.state.powerplay.merits=self.db.powerplay_merits(
            self.state.commander_id,power=self.state.powerplay.power)
        self.assertEqual(self.state.powerplay.merits,94567)
        powers=decode_powers_cache(encoded(rank_document()))
        self.view.setStyleSheet(DARK_STYLESHEET)
        with patch.object(self.view.cache,'load',return_value=powers):
            self.view.show();self.state.changed.emit();self.app.processEvents()
        self.assertEqual(self.view.personal['rank'].text(),'14')
        self.assertEqual(self.view.personal['merits'].text(),'94.567')
        self.assertIn('433',self.view.rank_summary.text())
        self.assertIn('95.000',self.view.rank_summary.text())
        self.assertIn('94,6 %',self.view.rank_bar.format())
        self.assertEqual(self.view.rank_bar.property('rankStatus'),'confirmed')
        self.assertTrue(self.view.rank_bar.isVisible())
        image=self.view.rank_bar.grab().toImage()
        from PySide6.QtGui import QColor
        self.assertTrue(any(image.pixel(x,2)==QColor('#247a41').rgb() for x in range(image.width())))
        self.assertEqual(rank_progress('Nakato Kaine',14,94567,powers).needed,433)
        self.assertEqual(self.view.recent.rowCount(),1)
        self.assertEqual(self.view.recent.item(0,3).text(),'+3.140 / +340 / +2.800')
        self.assertEqual(self.view.recent.item(0,4).text(),'≈')

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
