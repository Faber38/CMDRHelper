"""Version-label interaction, modal information and localized theme rendering."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import unittest
from unittest.mock import patch

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QVBoxLayout, QWidget

from cmdrhelper import version
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.ui.about_dialog import ACKNOWLEDGED_COMMANDERS, AboutDialog, VersionLabel
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tools.check_i18n import load_translation_file, placeholders


class AboutDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        set_language('de')
        self.parent = QWidget()
        self.parent.resize(800, 650)
        layout = QVBoxLayout(self.parent)
        self.label = VersionLabel()
        layout.addWidget(self.label)
        self.parent.show()
        self.addCleanup(self.parent.deleteLater)
        self.addCleanup(self.parent.close)

    def test_existing_label_text_style_and_hand(self):
        self.assertEqual(self.label.text(), f'CMDRHelper {version.__version__}')
        self.assertEqual(self.label.objectName(), 'appSubTitle')
        QTest.mouseMove(self.label, self.label.rect().center())
        self.assertEqual(self.label.cursor().shape(), Qt.PointingHandCursor)

    def test_click_opens_modal_dialog_and_close_button_works(self):
        observed = []
        def close_dialog():
            dialog = self.app.activeModalWidget()
            if isinstance(dialog, AboutDialog):
                observed.append((dialog.windowTitle(), dialog.isModal(), dialog.version_label.text()))
                QTest.mouseClick(dialog.buttons.button(QDialogButtonBox.Close), Qt.LeftButton)
            else:
                # Ensure a failed assertion cannot strand the test inside exec().
                for widget in self.app.topLevelWidgets():
                    if isinstance(widget, QDialog):
                        widget.reject()
        QTimer.singleShot(100, close_dialog)
        QTest.mouseClick(self.label, Qt.LeftButton)
        self.assertEqual(observed, [('CMDRHelper', True, f'Version {version.__version__}')])
        self.assertIsNone(self.app.activeModalWidget())

    def test_keyboard_activation_and_right_click(self):
        with patch.object(self.label, 'open_info') as opened:
            QTest.mouseClick(self.label, Qt.RightButton)
            opened.assert_not_called()
            for key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
                QTest.keyClick(self.label, key)
            self.assertEqual(opened.call_count, 3)

    def test_both_widgets_use_central_version_dynamically(self):
        with patch.object(version, '__version__', '9.9.9-test'):
            label = VersionLabel(self.parent)
            dialog = AboutDialog(self.parent)
            self.assertIn('9.9.9-test', label.text())
            self.assertEqual(dialog.version_label.text(), 'Version 9.9.9-test')
            dialog.deleteLater()

    def test_acknowledgements_follow_existing_information_with_exact_names(self):
        expected = ('Mr.Homn', 'Nanjan', 'Homunk', 'Pit', 'Mikee & Michael',
                    'PanzerPet', 'janjalan')
        self.assertEqual(ACKNOWLEDGED_COMMANDERS, expected)
        dialog = AboutDialog(self.parent)
        self.addCleanup(dialog.deleteLater)
        dialog.show()
        self.app.processEvents()
        self.assertEqual(dialog.acknowledgements_heading.text(), 'Danksagung')
        self.assertEqual(dialog.acknowledgements_intro.text(), tr('about.acknowledgements_intro'))
        self.assertEqual(dialog.acknowledged_commanders.text().replace('\n', ' · ').split(' · '),
                         ['CMDR ' + name for name in expected])
        self.assertLess(dialog.description.geometry().bottom(), dialog.acknowledgements_heading.y())
        self.assertTrue(dialog.acknowledgements_heading.font().bold())
        self.assertEqual(dialog.acknowledged_group.text(), 'sowie der gesamten EOT-Spielergruppe')
        self.assertLess(dialog.acknowledged_commanders.geometry().bottom(), dialog.acknowledged_group.y())
        self.assertEqual(dialog.description.text(), '\n\n'.join(tr('about.' + key) for key in (
            'intro', 'purpose', 'origin', 'development', 'support', 'independent', 'trademark')))

    def test_another_commander_only_needs_a_central_list_entry(self):
        with patch('cmdrhelper.ui.about_dialog.ACKNOWLEDGED_COMMANDERS',
                   ACKNOWLEDGED_COMMANDERS + ('New Commander',)):
            dialog = AboutDialog(self.parent)
            self.addCleanup(dialog.deleteLater)
            self.assertEqual(dialog.acknowledged_commanders.text().splitlines()[-1],
                             'CMDR janjalan · CMDR New Commander')
            self.assertEqual(dialog.acknowledged_commanders.text().count('CMDR '), 8)

    def test_twelve_languages_themes_and_bounded_dialog(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(len(_TRANSLATIONS), 12)
        reference = {k:v for k,v in _TRANSLATIONS['en'].items() if k.startswith('about.')}
        self.assertEqual(len(reference), 11)
        for language in _TRANSLATIONS:
            table, duplicates = load_translation_file(root / f'cmdrhelper/i18n/{language}.py')
            self.assertFalse(duplicates)
            self.assertEqual({k for k in table if k.startswith('about.')}, set(reference))
            set_language(language)
            for key, value in reference.items():
                self.assertTrue(table[key].strip())
                self.assertEqual(placeholders(table[key]), placeholders(value))
                self.assertEqual(tr(key, version=version.__version__), table[key].format(version=version.__version__))
            for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                with self.subTest(language=language, theme='dark' if theme == DARK_STYLESHEET else 'light'):
                    self.app.setStyleSheet(theme)
                    dialog = AboutDialog(self.parent)
                    dialog.show()
                    self.app.processEvents()
                    self.assertEqual(dialog.buttons.button(QDialogButtonBox.Close).text(), tr('common.close'))
                    self.assertIn('CMDR Faber38', dialog.description.text())
                    self.assertNotIn('Holger', dialog.description.text())
                    self.assertNotIn('Mangold', dialog.description.text())
                    self.assertIn('Frontier Developments plc', dialog.description.text())
                    self.assertIn(version.__version__, dialog.version_label.text())
                    self.assertEqual(dialog.acknowledgements_heading.text(), table['about.acknowledgements'])
                    self.assertEqual(dialog.acknowledgements_intro.text(), table['about.acknowledgements_intro'])
                    self.assertEqual(dialog.acknowledged_commanders.text().replace('\n', ' · ').split(' · '),
                                     ['CMDR ' + name for name in ACKNOWLEDGED_COMMANDERS])
                    self.assertNotIn('CMDR ', table['about.acknowledgements_intro'])
                    self.assertIn('EOT', dialog.acknowledgements_intro.text())
                    self.assertEqual(dialog.acknowledged_group.text(), table['about.acknowledgements_group'])
                    self.assertIn('EOT', dialog.acknowledged_group.text())
                    self.assertIn('CMDR Mikee & Michael', dialog.acknowledged_commanders.text())
                    self.assertNotIn('CMDR Mikee · CMDR Michael', dialog.acknowledged_commanders.text())
                    self.assertEqual([len(line.split(' · ')) for line in
                                      dialog.acknowledged_commanders.text().splitlines()], [2, 2, 2, 1])
                    self.assertLessEqual(dialog.width(), 490)
                    self.assertLessEqual(dialog.height(), 530)
                    self.assertTrue(dialog.screen().availableGeometry().contains(dialog.frameGeometry()))
                    QTest.keyClick(dialog, Qt.Key_Escape)
                    self.assertFalse(dialog.isVisible())
                    dialog.deleteLater()

    def test_small_dialog_scrolls_to_all_names_and_keeps_close_accessible(self):
        for language in _TRANSLATIONS:
            set_language(language)
            for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                with self.subTest(language=language, theme='dark' if theme == DARK_STYLESHEET else 'light'):
                    self.app.setStyleSheet(theme)
                    dialog = AboutDialog(self.parent)
                    try:
                        dialog.resize(360, 300)
                        dialog.show()
                        self.app.processEvents()
                        self.assertLessEqual(dialog.height(), 300)
                        scroll = dialog.scroll_area
                        bar = scroll.verticalScrollBar()
                        self.assertGreater(bar.maximum(), 0)
                        self.assertEqual(scroll.horizontalScrollBar().maximum(), 0)
                        bar.setFocus()
                        QTest.keyClick(bar, Qt.Key_End)
                        self.app.processEvents()
                        self.assertEqual(bar.value(), bar.maximum())
                        names = dialog.acknowledged_commanders
                        bottom = names.mapTo(scroll.viewport(), QPoint(0, names.height() - 1))
                        self.assertTrue(scroll.viewport().rect().contains(bottom))
                        group = dialog.acknowledged_group
                        group_bottom = group.mapTo(scroll.viewport(), QPoint(0, group.height() - 1))
                        self.assertTrue(scroll.viewport().rect().contains(group_bottom))
                        close = dialog.buttons.button(QDialogButtonBox.Close)
                        self.assertTrue(close.isVisible())
                        self.assertTrue(dialog.rect().contains(close.mapTo(dialog, close.rect().center())))
                        self.assertFalse(dialog.grab().isNull())
                        QTest.mouseClick(close, Qt.LeftButton)
                        self.assertFalse(dialog.isVisible())
                    finally:
                        dialog.close()
                        dialog.deleteLater()

    def test_sidebar_reuses_existing_version_slot(self):
        source = (Path(__file__).resolve().parents[1] / 'cmdrhelper/ui/main_window.py').read_text()
        self.assertEqual(source.count('side.addWidget(self.version_label)'), 1)
        self.assertIn('self.version_label = VersionLabel()', source)
        self.assertNotIn('nav.about', source)
