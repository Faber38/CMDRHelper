import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import json
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from PySide6.QtCore import QObject, QSettings, Signal, QLocale
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from cmdrhelper.i18n import get_language, set_language, tr, _TRANSLATIONS
from cmdrhelper.material_traders import (Coordinates, TraderStation, TraderType, TraderSearchResult,
                                       SearchStatus, MaterialTraderSearchService, CandidatePage)
from cmdrhelper.ui.material_view import MaterialView
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.route_planner.route_planner_view import RoutePlannerView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class State(QObject):
    changed = Signal()
    positionChanged = Signal(str, object, str)


class InventoryStub(QObject):
    loading = Signal()
    ready = Signal(object, str)


def found(kind='Raw'):
    station = TraderStation(TraderType(kind), '61 Cygni', 'Broglie Terminal', 42, 123,
                            Coordinates(3, 4, 0), 'Ocellus Starport', distance_ly=11.368731,
                            arrival_distance_raw=987654321, source_updated_at='2026-09-08 22:21:28+00',
                            retrieved_at=datetime.now(timezone.utc))
    return TraderSearchResult(SearchStatus.FOUND, station)


class TraderUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        previous = get_language()
        self.addCleanup(set_language, previous)
        set_language('de')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = State()
        self.state.system = 'Sol'
        self.state.system_address = 1
        self.state.star_pos = Coordinates(0, 0, 0)
        self.state.commander_id = 1
        self.state.settings = QSettings(str(Path(self.tmp.name) / 'settings.ini'), QSettings.IniFormat)
        self.service = Mock()
        self.service.find_nearest.side_effect = lambda kind, **kw: found(kind)
        self.view = MaterialView(self.state, controller=InventoryStub(),
                                 odyssey_controller=InventoryStub(), trader_service=self.service)
        self.panel = self.view.trader_panel
        self.view.resize(1000, 780)
        self.view.show()
        self.addCleanup(self.view.close)

    def wait(self):
        end = time.monotonic() + 4
        while self.panel._running and time.monotonic() < end:
            QTest.qWait(10)
        self.assertFalse(self.panel._running)
        self.app.processEvents()

    def search(self, tab=0):
        self.view.tabs.setCurrentIndex(tab)
        self.panel.search_button.click()
        self.wait()

    def test_button_only_classic_tabs(self):
        for index in range(4):
            self.view.tabs.setCurrentIndex(index)
            self.assertEqual(self.panel.search_button.isVisible(), index < 3)
        self.assertFalse(self.panel.isVisible())
        self.service.find_nearest.assert_not_called()

    def test_raw_tab(self):
        self.search(0)
        self.assertEqual(self.service.find_nearest.call_args.args, ('Raw',))
        self.assertIn('Rohmaterialhändler', self.panel.heading.text())

    def test_manufactured_tab(self):
        self.search(1)
        self.assertEqual(self.service.find_nearest.call_args.args, ('Manufactured',))
        self.assertIn('hergestellte', self.panel.heading.text())

    def test_encoded_tab(self):
        self.search(2)
        self.assertEqual(self.service.find_nearest.call_args.args, ('Encoded',))
        self.assertIn('Daten-Materialhändler', self.panel.heading.text())

    def test_reference_coordinates_and_name_only(self):
        self.search()
        self.assertEqual(self.service.find_nearest.call_args.kwargs,
                         dict(system_name='Sol', coordinates=Coordinates(0, 0, 0)))
        self.state.star_pos = None
        self.state.changed.emit()
        self.search()
        self.assertEqual(self.service.find_nearest.call_args.kwargs, dict(system_name='Sol', coordinates=None))

    def test_existing_database_coordinates_used(self):
        path = Path(self.tmp.name) / 'test.db'
        with sqlite3.connect(path) as con:
            con.execute('CREATE TABLE systems(system_address INTEGER,name TEXT,x REAL,y REAL,z REAL)')
            con.execute("INSERT INTO systems VALUES (1,'Sol',0,0,0)")
        self.state.database = SimpleNamespace(path=path)
        self.state.star_pos = None
        self.search()
        self.assertEqual(self.service.find_nearest.call_args.kwargs['coordinates'], Coordinates(0,0,0))

    def test_unknown_reference_does_not_call_service(self):
        self.state.system = ''
        self.state.system_address = None
        self.state.star_pos = None
        self.search()
        self.service.find_nearest.assert_not_called()
        self.assertEqual(self.panel.description.text(), tr('trader.unknown_system'))

    def test_background_thread_and_duplicate_suppression(self):
        gate = threading.Event()
        threads = []
        def lookup(*args, **kwargs):
            threads.append(threading.get_ident())
            gate.wait(3)
            return found()
        self.service.find_nearest.side_effect = lookup
        self.panel.search_button.click()
        try:
            self.assertFalse(self.panel.search_button.isEnabled())
            self.assertEqual(self.panel.search_button.text(), tr('trader.searching'))
            self.panel.search()
            QTest.qWait(30)
            self.assertEqual(self.service.find_nearest.call_count, 1)
            self.assertNotEqual(threads, [threading.get_ident()])
        finally:
            gate.set()
            self.wait()

    def test_success_distance_timestamp_and_no_arrival_unit(self):
        self.search()
        self.assertTrue(self.panel.isVisible())
        self.assertIn('11,4 ly', self.panel.description.text())
        self.assertIn('61 Cygni', self.panel.description.text())
        self.assertIn('Broglie Terminal', self.panel.description.text())
        self.assertIn('Raw', self.panel.metadata.text())
        self.assertIn('2026', self.panel.metadata.text())
        self.assertIn('Datenstand', self.panel.metadata.text())
        self.assertIn(tr('trader.access_unknown'), self.panel.toolTip())
        text = self.panel.description.text() + self.panel.metadata.text()
        self.assertNotIn('987654321', text)
        self.assertNotIn(' ls', text)
        self.assertNotIn(' km', text)

    def test_error_messages(self):
        for status, key in [(SearchStatus.NETWORK_ERROR, 'unreachable'), (SearchStatus.TIMEOUT, 'unreachable'),
                            (SearchStatus.NOT_FOUND, 'not_found'), (SearchStatus.SCHEMA_ERROR, 'unavailable'),
                            (SearchStatus.INVALID_JSON, 'unavailable'), (SearchStatus.HTTP_ERROR, 'unavailable'),
                            (SearchStatus.DETAIL_VALIDATION_FAILED, 'unavailable'), (SearchStatus.SEARCH_LIMIT, 'unavailable')]:
            self.service.find_nearest.side_effect = None
            self.service.find_nearest.return_value = TraderSearchResult(status)
            self.search()
            self.assertEqual(self.panel.description.text(), tr('trader.' + key))
            self.assertFalse(self.panel.route_button.isVisible())

    def test_tab_results_separate_no_automatic_request(self):
        self.search(0)
        self.view.tabs.setCurrentIndex(1)
        self.assertFalse(self.panel.isVisible())
        self.assertEqual(self.service.find_nearest.call_count, 1)
        self.search(1)
        self.view.tabs.setCurrentIndex(0)
        self.assertIn('Rohmaterialhändler', self.panel.heading.text())
        self.assertEqual(self.service.find_nearest.call_count, 2)

    def test_system_change_clears_result_without_query(self):
        self.search()
        self.state.system = 'Different'
        self.state.system_address = 2
        self.state.changed.emit()
        self.assertFalse(self.panel.isVisible())
        self.assertEqual(self.service.find_nearest.call_count, 1)
        receiver = Mock()
        self.panel.routeRequested.connect(receiver)
        self.panel.open_route()
        receiver.assert_not_called()

    def test_late_result_for_old_system_discarded(self):
        old = self.panel.reference()
        self.state.system = 'Different'
        self.panel._finished(old, 'Raw', found())
        self.assertFalse(self.panel.isVisible())

    def test_late_result_for_other_tab_not_shown(self):
        self.view.tabs.setCurrentIndex(1)
        self.panel._finished(self.panel.reference(), 'Raw', found())
        self.assertFalse(self.panel.isVisible())
        self.view.tabs.setCurrentIndex(0)
        self.assertTrue(self.panel.isVisible())

    def test_service_cache_still_used(self):
        client = Mock()
        station = found().station
        client.search_page.return_value = CandidatePage((station,), True)
        client.station_detail.return_value = station
        self.panel.service = MaterialTraderSearchService(client)
        self.search()
        self.search()
        self.assertEqual(client.search_page.call_count, 1)
        self.assertTrue(self.panel.current_result().from_cache)

    def test_mainwindow_route_handoff_sets_only_system(self):
        planner = RoutePlannerView(self.state)
        self.addCleanup(planner.close)
        planner._calculate_ship_route = Mock()
        planner.route_tabs.setCurrentIndex(1)
        window = SimpleNamespace(PAGE_ROUTE_PLANNER=MainWindow.PAGE_ROUTE_PLANNER,
                                 pages=Mock(widget=Mock(return_value=planner)), _show_page=Mock())
        self.view.routeRequested.connect(lambda system: MainWindow._open_material_trader_route(window, system))
        self.search()
        self.panel.route_button.click()
        self.assertEqual(planner.ship_destination_system.text(), '61 Cygni')
        self.assertEqual(planner.ship_start_system.text(), self.state.system)
        self.assertEqual(planner.ship_current_system.text(), self.state.system)
        self.assertEqual(planner.route_tabs.currentIndex(), 0)
        window._show_page.assert_called_once_with(MainWindow.PAGE_ROUTE_PLANNER)
        planner._calculate_ship_route.assert_not_called()
        self.assertIsNone(planner._carrier_route)

    def test_dark_and_light(self):
        for light, style in [(False,DARK_STYLESHEET),(True,LIGHT_STYLESHEET)]:
            self.view.setStyleSheet(style)
            self.view.set_light_mode(light)
            self.search()
            self.assertTrue(self.panel.isVisible())
            self.assertFalse(self.view.grab().isNull())

    def test_all_12_languages_have_13_trader_keys(self):
        for language in ('de','en','fr','it','no','sv','fi','pl','nl','es','tr','el'):
            set_language(language)
            self.assertEqual(len([k for k in _TRANSLATIONS[language] if k.startswith('trader.')]), 13)
            self.search()
            self.assertNotIn('trader.', self.panel.heading.text())

    def test_german_help_explains_trader_semantics(self):
        from cmdrhelper.help_content.de import HELP_TOPICS
        text = HELP_TOPICS['materials'][1].split('<h3>Odyssey</h3>')[0]
        for term in ('Spansh-Community-Daten', 'Raw', 'Manufactured', 'Encoded',
                     'direkte Systementfernung', 'Zugang ist nicht garantiert', 'Zielsystem, nicht die Station'):
            self.assertIn(term, text)
