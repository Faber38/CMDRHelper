"""Compact status uses only the loaded, tri-state exploration observations."""
import itertools
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication
from cmdrhelper.exploration_status import exploration_status
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
from cmdrhelper.ui.explorer_status import mapping_status_presentation
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests.test_explorer_table_ux import ExplorerWindow


class MappingStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.addCleanup(set_language, get_language())
        set_language('de')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def window(self, light=False):
        settings = QSettings(str(Path(self.tmp.name) / ('light.ini' if light else 'dark.ini')), QSettings.IniFormat)
        widths = [180, 210, 105, 125, 145, 235, 150, 190]
        settings.setValue('explorer/value_column_widths', widths)
        w = ExplorerWindow(settings, theme='light' if light else 'dark')
        self.addCleanup(w.deleteLater)
        self.addCleanup(w.close)
        self.assertEqual([w.explorer_value_table.columnWidth(i) for i in range(8)], widths)
        return w

    def test_all_nine_combinations_colors_tooltips_and_priority(self):
        expected = [0, 0, 0, 1, 2, 3, 1, 3, 3]
        texts = ['SELBST KARTIERT', 'BEREITS KARTIERT', 'NICHT KARTIERT', '?']
        tips = ['Dieser Körper wurde von dir kartographiert.',
                'Dieser Körper war bei deinem gespeicherten Scan bereits kartographiert.',
                'Dieser Körper war bei deinem gespeicherten Scan noch nicht kartographiert.',
                'Der Kartographie-Status ist mit den vorhandenen Daten nicht sicher bestimmbar.']
        for light, colors in [(False, ['#68c7ff', '#65d067', '#ffb000', '#9ba9b7']),
                              (True, ['#17679b', '#28752c', '#856000', '#536574'])]:
            for (own, previous), rank in zip(itertools.product((True, False, None), repeat=2), expected):
                with self.subTest(light=light, own=own, previous=previous):
                    status = exploration_status(dict(self_mapped=own, was_mapped=previous, journal_scanned=True))
                    self.assertEqual(mapping_status_presentation(status, light=light),
                                     (texts[rank], tips[rank], colors[rank], rank))

    def test_missing_invalid_and_external_information_is_unknown(self):
        for body in [{}, {'was_mapped': False}, {'self_mapped': False},
                     {'self_mapped': 0, 'was_mapped': 0},
                     {'self_mapped': False, 'was_mapped': False, 'source': 'EDSM'},
                     {'self_mapped': False, 'was_mapped': False, 'journal_scanned': False}]:
            with self.subTest(body=body):
                self.assertEqual(mapping_status_presentation(exploration_status(body))[0], '?')

    def test_reported_ten_body_fixture_in_both_themes_without_database_calls(self):
        # Recorded flags from Plio Aihm PF-Q c5-32; no production DB needed.
        names = ['C 1', 'ABC 1', 'ABC 2', 'DE 1', 'DE 2', 'DE 3', 'DE 4', 'ABCDE 1', 'ABCDE 2', 'ABCDE 3']
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        for light, style in [(False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)]:
            self.app.setStyleSheet(style)
            w = self.window(light)
            w.state.system_bodies = [dict(name=name, body_type='Planet', journal_scanned=True,
                was_mapped=name in ('ABC 2', 'DE 3', 'DE 4'), self_mapped=name == 'ABC 2') for name in names]
            db = Mock(); w.state.database = db
            w.resize(1800, 700); w.show(); w.explorer_tabs.setCurrentIndex(1)
            self.app.processEvents()
            w._refresh_explorer_tables(tab=1)
            self.assertEqual(db.mock_calls, [])
            t = w.explorer_value_table
            self.assertEqual(t.columnCount(), 8)
            self.assertEqual(t.horizontalHeaderItem(7).text(), 'Status')
            self.assertEqual([t.horizontalHeader().visualIndex(i) for i in range(8)], list(range(8)))
            counts = [0, 0, 0, 0]
            for row in range(t.rowCount()):
                item = t.item(row, 7); body = item.data(Qt.UserRole)
                text, tip, color, rank = mapping_status_presentation(exploration_status(body), light=light)
                self.assertEqual((item.text(), item.toolTip(), item.foreground().color().name()), (text, tip, color))
                counts[rank] += 1
            self.assertEqual(counts, [1, 2, 7, 0])
            self.assertIsNone(t._value_sort)
            t.horizontalHeader().sectionClicked.emit(7)
            self.assertEqual([t.item(r, 7).sort_key for r in range(10)], [0, 1, 1] + [2]*7)
            t.horizontalHeader().sectionClicked.emit(7)
            self.assertEqual([t.item(r, 7).sort_key for r in range(10)], [2]*7 + [1, 1, 0])

    def test_seven_translation_keys_in_twelve_languages(self):
        for language in 'de en el es fi fr it nl no pl sv tr'.split():
            for suffix in ['self', 'already', 'not', 'self_tip', 'already_tip', 'not_tip', 'unknown_tip']:
                self.assertTrue(_TRANSLATIONS[language]['explorer.mapping_status_' + suffix])
