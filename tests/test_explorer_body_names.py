"""Short table names are presentation only; full names and identity survive."""
import copy
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QHelpEvent
from PySide6.QtWidgets import QStyle

from cmdrhelper.i18n import _TRANSLATIONS, set_language, tr
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
import test_bio_body_footfall as bio_tests


class ExplorerBodyNameTests(unittest.TestCase):
    setUpClass = classmethod(bio_tests.BioBodyFootfallTests.setUpClass.__func__)
    setUp = bio_tests.BioBodyFootfallTests.setUp
    tearDown = bio_tests.BioBodyFootfallTests.tearDown
    option = bio_tests.BioBodyFootfallTests.option

    def test_existing_helper_handles_prefixes_and_fallbacks(self):
        for system, body, expected in (
            ('Pru Aescs TU-G d10-103', {'name': 'Pru Aescs TU-G d10-103 A 8 a'}, 'A 8 a'),
            ('Sol', {'name': 'Earth', 'short_name': 'Earth'}, 'Earth'),
            ('Test', {'name': 'Test AB 2 a b', 'short_name': 'Test AB 2 a b'}, 'AB 2 a b'),
            ('Test', {'name': 'Test A', 'short_name': 'A', 'body_type': 'Star'}, 'A'),
            ('Test', {'name': 'Test B', 'body_type': 'Star'}, 'B'),
            ('Test', {'name': 'Test', 'body_type': 'Star'}, 'Test'),
            ('Test', {'name': 'Testament 1'}, 'Testament 1'),
            ('Test', {'name': 'Other system 1'}, 'Other system 1'),
            ('', {'name': 'Unknown system 3'}, 'Unknown system 3'),
            ('Test', {'short_name': 'B 2 a'}, 'B 2 a'),
            ('Test', {}, '?'),
        ):
            with self.subTest(system=system, body=body):
                before = copy.deepcopy(body)
                self.assertEqual(MainWindow._explorer_body_name(body, system), expected)
                self.assertEqual(body, before)

    def test_both_tables_names_tooltips_identity_status_and_values(self):
        w = self.window
        system = 'Pru Aescs TU-G d10-103'
        w.state.system = system
        bodies = [dict(body_id=i, system_address=123, commander_id=5,
                       name=system + ' ' + short, short_name=system + ' ' + short,
                       biological_signals=1, geological_signals=2, planetary_mining_signals=3,
                       first_footfall=(i == 0), self_mapped=True, was_mapped=False,
                       current_value=12345, possible_value=20000, planet_class='Water world')
                  for i, short in enumerate(('A 8 a', 'AB 2 a b', 'B 12'))]
        original = copy.deepcopy(bodies)
        w.state.system_bodies = bodies
        for theme, style in (('dark', DARK_STYLESHEET), ('light', LIGHT_STYLESHEET)):
            w.ui_theme = theme
            w.setStyleSheet(style)
            for language in _TRANSLATIONS:
                set_language(language)
                # Compare all remaining columns with the previous name helper.
                with patch.object(w, '_explorer_body_name', side_effect=lambda b, *args: b.get('short_name') or b.get('name') or '?'):
                    w._refresh_explorer_tables()
                expected = {}
                for table in (w.explorer_value_table, w.explorer_bio_table):
                    expected[table] = {
                        table.item(r, 0).data(Qt.UserRole)['body_id']:
                        [(table.item(r, c).text(), table.item(r, c).toolTip())
                         for c in range(1, table.columnCount())]
                        for r in range(table.rowCount())}
                w._refresh_explorer_tables()
                for table in expected:
                    for row in range(table.rowCount()):
                        item = table.item(row, 0)
                        body = item.data(Qt.UserRole)
                        self.assertEqual(item.text(), ('A 8 a', 'AB 2 a b', 'B 12')[body['body_id']])
                        self.assertIn(body['name'], item.toolTip())
                        self.assertEqual(body, original[body['body_id']])
                        self.assertEqual(expected[table][body['body_id']],
                            [(table.item(row, c).text(), table.item(row, c).toolTip())
                             for c in range(1, table.columnCount())])
                        w._show_body_details = Mock()
                        w._explorer_table_body_activated(item)
                        w._show_body_details.assert_called_once_with(body)
                self.assertEqual(bodies, original)
        self.app.processEvents()
        for row in range(w.explorer_bio_table.rowCount()):
            index, option = self.option(row)
            self.assertEqual(not option.icon.isNull(), index.data(Qt.UserRole)['body_id'] == 0)
            if option.icon.isNull():
                continue
            for element, expected_text in (
                (QStyle.SE_ItemViewItemDecoration, tr('footfall.label')),
                (QStyle.SE_ItemViewItemText, original[0]['name']),
            ):
                rect = self.table.style().subElementRect(element, option, self.table)
                event = QHelpEvent(QEvent.ToolTip, rect.center(), self.table.viewport().mapToGlobal(rect.center()))
                with patch('cmdrhelper.ui.bio_body_delegate.QToolTip.showText') as show:
                    self.delegate.helpEvent(event, self.table, option, index)
                    self.assertEqual(show.call_args.args[1], expected_text)
