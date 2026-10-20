"""Real mission page sorting with isolated settings and no journal/database IO."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import unittest
from PySide6.QtCore import QSettings, Qt, QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget
from cmdrhelper.models import Mission
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.i18n import set_language


class Host(SimpleNamespace):
    pass


class MissionTableSortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name)/'settings.ini')
        set_language('de')
        self.host = self.make_host()

    def make_host(self):
        host = Host(state=SimpleNamespace(settings=QSettings(self.path,QSettings.IniFormat),
            missions=[], commander_id=1, refresh=lambda:None, bounties=None, combat_bonds=None))
        for name in ('_missions','_card','_save_missions_header_state','_mission_selection_changed','_refresh_missions_table'):
            setattr(host,name,getattr(MainWindow,name).__get__(host))
        for name in ('_format_reward','_format_expiry','_place_text','_translate_mission_text'):
            setattr(host,name,getattr(MainWindow,name))
        with patch('cmdrhelper.ui.bounty_view.BountyView',side_effect=lambda *a:QWidget()), patch('cmdrhelper.ui.combat_bond_view.CombatBondView',side_effect=lambda *a:QWidget()):
            host.page=host._missions()
        self.addCleanup(host.page.close)
        host.page.resize(1200,800)
        host.page.show()
        return host

    def ids(self,host=None):
        table=(host or self.host).missions_table
        return [table.item(r,0).mission.mission_id for r in range(table.rowCount())]

    def click(self,column,host=None):
        (host or self.host).missions_table.horizontalHeader().sectionClicked.emit(column)

    def test_every_column_both_directions_themes_no_mutation(self):
        # Text, credit magnitude and calendar order intentionally agree by ID.
        rows=[Mission(mission_id=2,name='Beta',destination_system='Beta',destination_body='Beta',
                      status='Beta',next_step='Beta',reward=1000,expiry='2026-02-01T00:00:00Z'),
              Mission(mission_id=1,name='alpha',destination_system='alpha',destination_body='alpha',
                      status='alpha',next_step='alpha',reward=20,expiry='2026-01-31T23:00:00Z'),
              Mission(mission_id=3,name='zulu',destination_system='zulu',destination_body='zulu',
                      status='zulu',next_step='zulu',reward=10000,expiry='2027-01-01T00:00:00Z')]
        original=deepcopy(rows)
        self.host.state.missions=rows
        for theme in (DARK_STYLESHEET,LIGHT_STYLESHEET):
            self.host.page.setStyleSheet(theme)
            self.host._refresh_missions_table()
            for column in range(7):
                self.click(column)
                self.assertEqual(self.ids(),[1,2,3])
                self.assertTrue(self.host.missions_table.horizontalHeader().isSortIndicatorShown())
                self.click(column)
                self.assertEqual(self.ids(),[3,2,1])
        self.assertEqual(rows,original)

    def test_missing_values_timezone_and_pending_offers(self):
        self.host.state.missions=[Mission(mission_id=1,name='',destination_system='',status='',next_step='',reward=None),
                                  Mission(mission_id=2,name='A',destination_system='A',destination_body='A',status='A',next_step='A',reward=0,expiry='2026-01-01T02:00:00+02:00'),
                                  Mission(mission_id=3,name='B',destination_system='B',destination_body='B',status='B',next_step='B',reward=1,expiry='2026-01-01T00:30:00Z')]
        self.host._refresh_missions_table()
        for col in range(7):
            self.click(col);self.assertEqual(self.ids(),[1,2,3])
            self.click(col);self.assertEqual(self.ids(),[3,2,1])
        self.host.state.missions=[Mission(mission_id=4,expiry='bad'),Mission(mission_id=5,expiry='2027-01-01T00:00:00Z',extra={'pending_offer':True})]
        self.host._refresh_missions_table()
        for row in range(2):self.assertEqual(self.host.missions_table.item(row,6).sort_key,(False,0))

    def test_refresh_completion_commander_and_detail_selection(self):
        a=Mission(mission_id=1,name='Zulu',summary='Detail A',reward=10)
        b=Mission(mission_id=2,name='alpha',summary='Detail B',reward=20)
        self.host.state.missions=[a,b];self.host._refresh_missions_table();self.click(0)
        self.host.missions_table.selectRow(0)
        self.assertEqual(self.host.mission_detail_text.text(),'Detail B')
        c=Mission(mission_id=3,name='Before',reward=15)
        self.host.state.missions=[a,b,c];self.host._refresh_missions_table()
        self.assertEqual(self.ids(),[2,3,1])
        self.assertEqual(self.host.mission_detail_text.text(),'Detail B')
        self.host.state.missions=[a,c];self.host._refresh_missions_table()
        self.assertEqual(self.ids(),[3,1])
        self.assertEqual(self.host.missions_table.selectionModel().selectedRows(),[])
        self.host.missions_table.selectRow(0)
        self.host.state.commander_id=2
        self.host.state.missions=[Mission(mission_id=3,name='Other commander')]
        self.host._refresh_missions_table()
        self.assertEqual(self.ids(),[3])
        self.assertEqual(self.host.missions_table.item(0,0).text(),'Other commander')
        self.assertEqual(self.host.missions_table.selectionModel().selectedRows(),[])
        self.assertEqual(self.host.missions_table._value_sort,(0,Qt.AscendingOrder))

    def test_restart_header_click_and_settings(self):
        self.host.state.missions=[Mission(mission_id=1,name='Beta',reward=2),Mission(mission_id=2,name='alpha',reward=10)]
        self.host._refresh_missions_table();self.app.processEvents()
        header=self.host.missions_table.horizontalHeader()
        point=QPoint(header.sectionViewportPosition(0)+30,header.height()//2)
        QTest.mouseClick(header.viewport(),Qt.LeftButton,pos=point)
        self.assertEqual(self.ids(),[2,1])
        QTest.mouseClick(header.viewport(),Qt.LeftButton,pos=point)
        self.assertEqual(self.ids(),[1,2])
        self.click(5);self.click(5)
        restored=self.make_host()
        restored.state.missions=deepcopy(self.host.state.missions)
        restored._refresh_missions_table()
        self.assertEqual(restored.missions_table._value_sort,(5,Qt.DescendingOrder))
        self.assertEqual(self.ids(restored),[2,1])
        self.assertTrue(restored.missions_table.horizontalHeader().isSortIndicatorShown())
