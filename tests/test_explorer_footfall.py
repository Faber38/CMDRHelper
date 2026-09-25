"""First-footfall presentation and cumulative commander-scoped saved observations."""
import copy
import os
import tempfile
import unittest
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.state import AppState
from cmdrhelper.ui.explorer_status import FOOTFALL_COLOR_ROLE, mapping_status_presentation
from cmdrhelper.exploration_status import exploration_status
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests.test_explorer_table_ux import ExplorerWindow


class ExplorerFootfallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        set_language('de')

    def window(self, light=False):
        settings = QSettings(str(Path(self.tmp.name) / 'ui.ini'), QSettings.IniFormat)
        window = ExplorerWindow(settings, theme='light' if light else 'dark')
        window.resize(720, 500)
        window.show()
        window.explorer_tabs.setCurrentIndex(1)
        self.addCleanup(window.deleteLater)
        self.addCleanup(window.close)
        return window

    def refresh(self, window, bodies):
        window.state.system_bodies = bodies
        window._refresh_explorer_tables(tab=1)
        self.app.processEvents()
        return window.explorer_value_table

    def body(self, **kw):
        return dict(dict(body_id=2, name='Example 2', body_type='Planet',
                         journal_scanned=True, biological_signals=0, biology=[],
                         self_mapped=False, was_mapped=False), **kw)

    def test_true_combines_all_mapping_states_in_both_themes(self):
        for light in (False, True):
            window = self.window(light)
            for own, previous in ((True, False), (False, True), (False, False), (None, None)):
                with self.subTest(light=light, own=own, previous=previous):
                    body = self.body(first_footfall=True, self_mapped=own, was_mapped=previous)
                    table = self.refresh(window, [body])
                    item = table.item(0, 7)
                    text, tip, color, rank = mapping_status_presentation(exploration_status(body), light=light)
                    self.assertEqual(item.text(), 'ERSTBETRETUNG\n' + text)
                    self.assertEqual(item.foreground().color().name(), color)
                    self.assertEqual(item.data(FOOTFALL_COLOR_ROLE), '#856000' if light else '#ffb000')
                    self.assertEqual(item.sort_key, rank)
                    self.assertIn(tip, item.toolTip())
                    self.assertIn(tr('explorer.first_footfall_tip'), item.toolTip())
                    self.assertNotIn('first_footfall_at', item.toolTip())
                    self.assertEqual(table.columnCount(), 8)

    def test_false_missing_and_refresh_remove_badge(self):
        window = self.window()
        for value in (True, False, None):
            body = self.body(**({} if value is None else {'first_footfall': value}))
            table = self.refresh(window, [body])
            self.assertEqual('ERSTBETRETUNG' in table.item(0, 7).text(), value is True)
            self.assertEqual(bool(table.item(0, 7).data(FOOTFALL_COLOR_ROLE)), value is True)
        self.refresh(window, [])
        self.assertEqual(table.rowCount(), 0)

    def test_twelve_languages_help_and_no_english_fallback(self):
        labels = set()
        for lang in 'de en el es fi fr it nl no pl sv tr'.split():
            with self.subTest(lang=lang):
                set_language(lang)
                label = _TRANSLATIONS[lang]['explorer.first_footfall']
                tip = _TRANSLATIONS[lang]['explorer.first_footfall_tip']
                labels.add(label)
                self.assertEqual(tr('explorer.first_footfall'), label)
                self.assertTrue(tip)
                if lang != 'en':
                    self.assertNotIn('First footfall', tip)
                    self.assertNotEqual(label, 'FIRST FOOTFALL')
                help_html = import_module('cmdrhelper.help_content.' + lang).HELP_TOPICS['explorer'][1]
                self.assertIn(label, help_html)
                self.assertIn('Universal Cartographics', help_html)
                self.assertIn('Vista Genomics', help_html)
                window = self.window()
                table = self.refresh(window, [self.body(first_footfall=True)])
                self.assertIn(label, table.item(0, 7).text())
                self.assertIn(tip, table.item(0, 7).toolTip())
        self.assertEqual(len(labels), 12)

    def test_large_font_narrow_column_paints_both_accents_and_keeps_tooltip(self):
        for light, style in ((False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)):
            self.app.setStyleSheet(style)
            window = self.window(light)
            table = window.explorer_value_table
            window.explorer_value_fit_check.setChecked(False)
            font = QFont(table.font())
            font.setPointSize(22)
            table.setFont(font)
            table.horizontalHeader().setStretchLastSection(False)
            table.setColumnWidth(7, 145)
            self.refresh(window, [self.body(first_footfall=True, self_mapped=True)])
            table.scrollToItem(table.item(0, 7))
            self.app.processEvents()
            option = QStyleOptionViewItem()
            option.initFrom(table)
            option.font = table.font()
            index = table.model().index(0, 7)
            hint = table.itemDelegateForColumn(7).sizeHint(option, index)
            self.assertGreaterEqual(table.rowHeight(0), hint.height())
            self.assertGreaterEqual(table.rowHeight(0), table.fontMetrics().lineSpacing() * 2)
            self.assertEqual(table.columnWidth(7), 145)
            rect = table.visualItemRect(table.item(0, 7))
            picture = table.viewport().grab(rect).toImage()
            colors = {picture.pixelColor(x, y).name()
                      for x in range(picture.width()) for y in range(picture.height())}
            self.assertIn('#856000' if light else '#ffb000', colors)
            self.assertIn('#17679b' if light else '#68c7ff', colors)
            self.assertIn('ERSTBETRETUNG', table.item(0, 7).toolTip().upper())

    def test_saved_true_survives_restart_live_false_and_is_scoped(self):
        path = Path(self.tmp.name) / 'isolated.db'
        db = CMDRDatabase(path)
        a = db.upsert_commander('FOOT-A', 'Alpha')
        b = db.upsert_commander('FOOT-B', 'Bravo')
        db.store_snapshot(dict(system_address=60, system='Example',
            last_timestamp='2026-01-01T00:00:00Z',
            system_bodies=[self.body(first_footfall=True)]), a)
        # New database object models restart; only temporary synthetic data.
        db = CMDRDatabase(path)
        state = SimpleNamespace(database=db, commander_id=a, system_address=60)
        live = self.body(first_footfall=False)
        before = copy.deepcopy(live)
        window = self.window()
        for commander, address, expected in ((a, 60, True), (b, 60, False),
                                              (a, 61, False), (a, 60, True)):
            state.commander_id, state.system_address = commander, address
            bodies = AppState._own_explorer_bodies(state, [live])
            table = self.refresh(window, bodies)
            self.assertEqual(bodies[0]['first_footfall'], expected)
            self.assertEqual('ERSTBETRETUNG' in table.item(0, 7).text(), expected)
        self.assertEqual(live, before)
        saved = AppState._own_explorer_bodies(state, [])
        self.assertTrue(saved[0]['first_footfall'])
        self.assertIn('ERSTBETRETUNG', self.refresh(window, saved).item(0, 7).text())

    def test_status_sort_retains_mapping_priority_and_body_identity(self):
        window = self.window()
        table = self.refresh(window, [self.body(body_id=1, name='A', first_footfall=True),
                                     self.body(body_id=2, name='B', self_mapped=True)])
        table.sortItems(7, Qt.AscendingOrder)
        self.assertEqual(table.item(0, 7).text(), 'SELBST KARTIERT')
        self.assertEqual(table.item(1, 7).data(Qt.UserRole)['body_id'], 1)
        self.assertIn('ERSTBETRETUNG', table.item(1, 7).text())
