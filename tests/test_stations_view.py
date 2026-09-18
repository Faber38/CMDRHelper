"""Local station cards and Explorer updates, without network or application DB."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import Qt, QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from cmdrhelper.i18n import tr, get_language, set_language, _TRANSLATIONS
from cmdrhelper.ui.stations_view import StationsView
from cmdrhelper.ui.station_details import StationDetailDialog
from cmdrhelper.ui.ship_widgets import ShipImageViewer
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.spansh_stations import SpanshStations, SETTING


def facilities():
    return [
        dict(identity='market:1', market_id=1, station_name='Ridorana Surface', station_type='CraterOutpost',
             parent_body_id=49, body_name='Test 9 g', source='Journal + Spansh', spansh=dict(
                 distance_ls=4583, primary_economy='Colony', controlling_faction='Brewer Corporation',
                 landing_pads=dict(large=3, medium=2, small=2), economies={'Colony': 100},
                 services=['market', 'repair', 'refuel', 'restock'],
                 source_updated_at='2026-09-13T00:00:00Z', fetched_at='2026-09-16T00:00:00Z')),
        dict(identity='market:2', market_id=2, station_name='Ridorana Forge', station_type='Dodec',
             parent_body_id=None, body_name='Ridorana Forge', source='Journal', spansh={'distance_ls': 500}),
        dict(identity='market:3', market_id=3, station_name='Choo', station_type='OnFootSettlement',
             parent_body_id=38, body_name='Test 7 e', source='Spansh'),
    ]


class StationsViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        set_language('de')
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.settings = QSettings(str(Path(directory.name) / 'ui.ini'), QSettings.IniFormat)
        self.service = SpanshStations(self.settings, cache=Mock(), pool=Mock())
        self.view = StationsView(spansh=self.service)
        self.view.resize(950, 700)
        self.view.set_system(42, 'Test', facilities())
        self.view.show()
        self.app.processEvents()

    def tearDown(self):
        for window in self.app.topLevelWidgets():
            window.close()
        self.view.deleteLater()
        self.app.processEvents()

    def visible(self):
        return [c.station['market_id'] for c in self.view.cards if not c.isHidden()]

    def choose(self, combo, value):
        combo.setCurrentIndex(combo.findData(value))

    def test_empty_and_count_are_model_based_not_filtered(self):
        self.assertEqual(self.view.tab_title, 'STATIONEN (3)')
        self.view.search.setText('missing')
        self.assertEqual(self.visible(), [])
        self.assertEqual(self.view.tab_title, 'STATIONEN (3)')
        self.assertEqual(self.view.empty.text(), tr('stations.no_matches'))
        self.view.set_system(43, 'Empty', [])
        self.assertEqual(self.view.tab_title, 'STATIONEN (0)')
        self.assertEqual(self.view.empty.text(), tr('stations.empty_local'))

    def test_disabled_notice_leaves_search_and_details_usable(self):
        self.assertTrue(self.view.local_notice.isVisible())
        self.view.search.setFocus()
        QTest.keyClicks(self.view.search, 'Ridorana')
        self.assertEqual(set(self.visible()), {1, 2})
        card = next(c for c in self.view.cards if c.station['market_id'] == 1)
        QTest.mouseClick(card.header, Qt.LeftButton)
        self.assertTrue(card.details.isVisible())
        self.service.pool.start.assert_not_called()
        self.service.cache.read.assert_not_called()

    def test_live_toggle_preserves_cards_filters_and_count(self):
        self.view.search.setText('Ridorana')
        cards = list(self.view.cards)
        for active in (True, False, True):
            self.service.set_enabled(active)
            # The existing signal updates visibility synchronously, without model refresh.
            self.assertEqual(self.view.local_notice.isHidden(), active)
            self.assertEqual(self.view.cards, cards)
            self.assertEqual(self.view.search.text(), 'Ridorana')
            self.assertEqual(self.view.tab_title, 'STATIONEN (3)')
        self.service.pool.start.assert_not_called()
        self.service.cache.read.assert_not_called()

    def test_empty_text_tracks_service_even_while_view_hidden(self):
        self.view.set_system(43, 'Empty', [])
        self.view.hide()
        for active in (True, False, True):
            self.service.set_enabled(active)
            self.assertEqual(self.view.empty.text(), tr('stations.empty' if active else 'stations.empty_local'))
            self.assertEqual(self.view.local_notice.isHidden(), active)
            self.assertEqual(self.view.tab_title, 'STATIONEN (0)')

    def test_initial_enabled_setting_hides_notice(self):
        self.settings.setValue(SETTING, True)
        service = SpanshStations(self.settings, cache=Mock(), pool=Mock())
        view = StationsView(spansh=service)
        self.addCleanup(view.deleteLater)
        self.assertTrue(view.local_notice.isHidden())
        self.assertEqual(view.empty.text(), tr('stations.empty'))
        self.assertTrue(service.active)

    def test_notice_translates_in_all_twelve_languages(self):
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language, table in _TRANSLATIONS.items():
            set_language(language)
            self.view.set_system(43, 'Empty', [])
            for key in ('stations.local_notice', 'stations.local_notice_settings', 'stations.empty_local'):
                self.assertTrue(table[key].strip(), (language, key))
            self.assertEqual(self.view.local_notice.text(), table['stations.local_notice'] + '\n' + table['stations.local_notice_settings'])
            self.assertEqual(self.view.empty.text(), table['stations.empty_local'])

    def test_case_insensitive_search_and_combined_filters(self):
        self.view.search.setText('rIDorANA')
        self.assertEqual(set(self.visible()), {1, 2})
        self.choose(self.view.type_filter, 'surface')
        self.assertEqual(self.visible(), [1])
        self.choose(self.view.body_filter, 38)
        self.assertEqual(self.visible(), [])

    def test_unknown_parent_uses_safe_parent_field(self):
        self.choose(self.view.body_filter, 'unknown')
        self.assertEqual(self.visible(), [2])
        self.assertEqual(self.view.body_filter.count(), 4)
        self.assertEqual(self.view.body_filter.findText('Ridorana Forge'), -1)

    def test_all_sort_orders_put_missing_distance_last(self):
        self.assertEqual(self.visible(), [3, 2, 1])
        self.choose(self.view.sort_order, 'distance')
        self.assertEqual(self.visible(), [2, 1, 3])
        self.choose(self.view.sort_order, 'body')
        self.assertEqual(self.visible(), [3, 1, 2])
        self.choose(self.view.sort_order, 'type')
        self.assertEqual(self.visible(), [1, 2, 3])

    def test_expand_lazy_details_match_existing_dialog(self):
        card = next(c for c in self.view.cards if c.station['market_id'] == 1)
        self.assertTrue(all(c.details is None for c in self.view.cards))
        QTest.mouseClick(card.header, Qt.LeftButton)
        self.app.processEvents()
        self.assertTrue(card.header.isChecked())
        self.assertIsNotNone(card.details)
        dialog = StationDetailDialog(card.station, 'Test')
        for name in ('info', 'external_info', 'external_dates'):
            self.assertEqual(getattr(card.details, name).text(), getattr(dialog, name).text())
        self.assertIn('L: 3', card.details.external_info.text())
        self.assertIn('M: 2', card.details.external_info.text())
        self.assertEqual(len(card.details.service_labels), 4)
        QTest.mouseClick(card.header, Qt.LeftButton)
        self.assertTrue(card.details.isHidden())

    def test_thumbnail_double_click_uses_existing_viewer(self):
        card = next(c for c in self.view.cards if c.station['market_id'] == 1)
        self.assertEqual(card.image.size().width(), 112)
        self.assertEqual(card.image._source_path.name, 'surface_station.png')
        QTest.mouseDClick(card.image, Qt.LeftButton)
        self.app.processEvents()
        viewer = self.view.findChild(ShipImageViewer)
        self.assertIsNotNone(viewer)
        self.assertEqual(viewer.windowTitle(), 'Ridorana Surface')
        self.assertFalse(card.header.isChecked())

    def test_update_preserves_filters_expansion_and_rebuilds_body_options(self):
        card = next(c for c in self.view.cards if c.station['market_id'] == 1)
        card.header.setChecked(True)
        self.view.search.setText('Ridorana')
        self.choose(self.view.type_filter, 'surface')
        self.choose(self.view.body_filter, 49)
        data = facilities()
        data[0]['spansh']['distance_ls'] = 9000
        data.append(dict(identity='market:4', market_id=4, station_name='New', parent_body_id=99, body_name='Test 10'))
        self.view.set_system(42, 'Test', data)
        self.assertEqual(self.view.search.text(), 'Ridorana')
        self.assertEqual(self.view.body_filter.currentData(), 49)
        self.assertNotEqual(self.view.body_filter.findData(99), -1)
        self.assertEqual(self.visible(), [1])
        card = next(c for c in self.view.cards if c.station['market_id'] == 1)
        self.assertTrue(card.header.isChecked())
        self.assertIn('9,000.0', card.details.external_info.text())

    def test_system_change_clears_filters_and_old_cards(self):
        self.view.search.setText('Ridorana')
        self.choose(self.view.body_filter, 49)
        self.view.set_system(43, 'New system', [dict(identity='market:8', market_id=8, station_name='New')])
        self.assertEqual(self.view.search.text(), '')
        self.assertEqual(self.view.body_filter.currentData(), 'all')
        self.assertEqual(self.visible(), [8])
        self.assertEqual(self.view.body_filter.findData(49), -1)

    def test_unchanged_model_keeps_widgets_and_inputs_untouched(self):
        data = facilities(); before = deepcopy(data)
        card_ids = [id(c) for c in self.view.cards]
        with patch('cmdrhelper.spansh_cache.fetch_system', side_effect=AssertionError('network')):
            self.view.set_system(42, 'Test', data)
            self.view.search.setText('Ridorana')
        self.assertEqual([id(c) for c in self.view.cards], card_ids)
        self.assertEqual(data, before)

    def test_dark_light_and_translation_keys(self):
        self.view.cards[0].header.setChecked(True)
        for light, style in ((False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)):
            self.app.setStyleSheet(style)
            self.view.set_light_mode(light)
            self.app.processEvents()
            self.assertFalse(self.view.grab().isNull())
            self.assertEqual(self.view.cards[0].light, light)
            self.assertTrue(self.view.local_notice.isVisible())
            self.assertEqual(self.view.local_notice.palette().window().color().name(), '#080d12')
            self.assertEqual(self.view.local_notice.palette().windowText().color().name(), '#d8dde3')
        for language, table in _TRANSLATIONS.items():
            for key in ('tab', 'search', 'all_bodies', 'empty', 'no_matches'):
                self.assertIn('stations.' + key, table, language)
        set_language('en')
        self.view.set_system(42, 'Test', facilities())
        self.assertEqual(self.view.tab_title, 'STATIONS (3)')

    def test_explorer_tab_and_targeted_refresh_use_supplied_model(self):
        from tests.test_explorer_table_ux import ExplorerWindow
        with tempfile.TemporaryDirectory() as directory:
            window = ExplorerWindow(QSettings(str(Path(directory) / 'ui.ini'), QSettings.IniFormat))
            window.state.system_address = 42
            window.state.system_stations = facilities()
            window.state.database.system_stations = Mock(side_effect=AssertionError('DB query'))
            window._refresh_stations_tab()
            self.assertEqual(window.explorer_tabs.indexOf(window.stations_view), 3)
            self.assertEqual(window.explorer_tabs.tabText(3), 'STATIONEN (3)')
            window.state.system_stations = facilities()[:1]
            window._station_model_updated(42)
            self.assertEqual(window.explorer_tabs.tabText(3), 'STATIONEN (1)')
            self.assertEqual(len(window.stations_view.cards), 3)  # Hidden: build deferred.
            self.assertIn(3, window._explorer_dirty_tabs)
            window.pages = SimpleNamespace(currentIndex=lambda: window.PAGE_EXPLORER)
            window.explorer_tabs.setCurrentIndex(3)
            self.assertEqual(len(window.stations_view.cards), 1)
            window.state.database.system_stations.assert_not_called()
            window.state.system_address = 99
            window.state.system = 'Empty system'
            window.state.system_stations = []
            window.pages = SimpleNamespace(currentIndex=lambda: window.PAGE_EXPLORER)
            window._refresh_explorer_tables = Mock()
            window._explorer_dirty = True
            window._refresh_visible_details()
            self.assertEqual(window.explorer_tabs.tabText(3), 'STATIONEN (0)')
            self.assertEqual(window.stations_view.cards, [])
            window.close(); window.deleteLater()


if __name__ == '__main__':
    unittest.main()
