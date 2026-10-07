"""PP2-only UI preferences, using isolated QSettings and real header gestures."""
from datetime import date, timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PySide6.QtCore import QSettings, QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QHeaderView
from cmdrhelper.ui.powerplay_view import PowerplayView, ChronicleTable
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests.test_powerplay import ViewState, event

KEY = ChronicleTable.WIDTHS_KEY
DAY = date(2026,10,6)


class ColumnWidthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.path=str(Path(tmp.name)/'ui.ini')
        self.settings=QSettings(self.path,QSettings.IniFormat)
        clock=patch('cmdrhelper.ui.powerplay_view.local_today',return_value=DAY)
        self.clock=clock.start();self.addCleanup(clock.stop)
        self.view=self.make_view(self.settings)

    def make_view(self,settings):
        state=ViewState();state.settings=settings
        view=PowerplayView(state);view.resize(1200,900);view.show()
        self.app.processEvents();self.addCleanup(view.close)
        return view

    def widths(self,view=None):
        return [(view or self.view).recent.columnWidth(i) for i in range(5)]

    def drag(self,column=2,amount=-70):
        header=self.view.recent.horizontalHeader()
        point=QPoint(header.sectionViewportPosition(column)+header.sectionSize(column)-1,header.height()//2)
        QTest.mousePress(header.viewport(),Qt.LeftButton,pos=point)
        QTest.mouseMove(header.viewport(),point+QPoint(amount,0),30)
        QTest.mouseRelease(header.viewport(),Qt.LeftButton,pos=point+QPoint(amount,0))
        self.app.processEvents()

    def test_interactive_defaults_and_click_does_not_save(self):
        sizes=self.widths()
        self.assertGreater(sizes[2],max(sizes[:2]+sizes[3:]))
        self.assertTrue(all(self.view.recent.horizontalHeader().sectionResizeMode(i)==QHeaderView.Interactive for i in range(5)))
        self.drag(amount=0)
        self.assertIsNone(self.settings.value(KEY))

    def test_mouse_resize_saved_and_restart_restores(self):
        before=self.widths();self.drag()
        expected=self.widths()
        self.assertLess(expected[2],before[2])
        self.assertEqual(self.settings.value(KEY),expected)
        self.view.close()
        restarted=self.make_view(QSettings(self.path,QSettings.IniFormat))
        self.assertEqual(self.widths(restarted),expected)

    def test_all_five_columns_can_be_dragged(self):
        for col in range(5):
            before=self.widths()
            self.drag(column=col,amount=20)
            self.assertGreater(self.widths()[col],before[col])
            self.assertIsNotNone(self.settings.value(KEY))

    def test_live_day_navigation_visibility_and_themes_preserve_widths(self):
        self.drag();expected=self.widths()
        self.view.state.powerplay.apply(event('PowerplayMerits',Power='Test Power',MeritsGained=3600,TotalMerits=13256))
        self.view.state.changed.emit();self.app.processEvents()
        self.assertEqual(self.widths(),expected)
        self.view.previous_day.click();self.app.processEvents()
        self.assertEqual(self.view.selected_day,DAY-timedelta(days=1))
        self.assertEqual(self.widths(),expected)
        self.view.today_button.click()
        self.clock.return_value=DAY+timedelta(days=1)
        self.view.render();self.app.processEvents()
        self.assertEqual(self.widths(),expected)
        self.view.hide();self.view.show();self.app.processEvents()
        self.assertEqual(self.widths(),expected)
        for theme in (DARK_STYLESHEET,LIGHT_STYLESHEET):
            self.view.setStyleSheet(theme);self.app.processEvents()
            self.assertEqual(self.widths(),expected)
        self.assertEqual(self.settings.value(KEY),expected)

    def test_live_scrollbar_does_not_resize_user_columns(self):
        self.drag(column=0,amount=20)
        expected=self.widths()
        for n in range(80):
            self.view.state.powerplay.apply(dict(event('PowerplayCollect',Power='Test Power',Type='item',Count=1),
                timestamp=f'2026-10-06T10:{n//60:02}:{n%60:02}Z'))
        self.view.render();self.app.processEvents()
        self.assertEqual(self.widths(),expected)

    def test_narrow_fit_does_not_overwrite_preference(self):
        self.drag();expected=self.widths()
        for width in (480,360,260):
            self.view.resize(width,900);self.app.processEvents()
            self.assertEqual(self.settings.value(KEY),expected)
            self.assertTrue(all(w>=m for w,m in zip(self.widths(),self.view.recent.column_widths.minimums)))
        self.view.resize(1200,900);self.app.processEvents()
        self.assertEqual(self.widths(),expected)
        restored=self.make_view(QSettings(self.path,QSettings.IniFormat))
        restored.resize(480,900);self.app.processEvents()
        self.assertLessEqual(sum(self.widths(restored)),restored.recent.viewport().width())
        self.assertEqual(self.settings.value(KEY),expected)

    def test_invalid_saved_widths_use_defaults(self):
        expected=self.widths()
        for value in (None,'broken',[50]*4,[True]*5,[-1]*5,[100000]*5,[75.5]*5,[60,80,0,80,80],[60,80,40,80,80]):
            self.settings.setValue(KEY,value);self.settings.sync()
            view=self.make_view(QSettings(self.path,QSettings.IniFormat))
            self.assertEqual(self.widths(view),expected)
            view.close()

    def test_reset_removes_only_pp2_preference(self):
        defaults=self.widths()
        self.settings.setValue('overview/recent_systems_column_widths',[150,350])
        self.drag();self.view.reset_columns_action.trigger();self.app.processEvents()
        self.assertIsNone(self.settings.value(KEY))
        self.assertEqual(self.widths(),defaults)
        self.assertEqual(self.settings.value('overview/recent_systems_column_widths'),[150,350])
