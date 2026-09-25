"""Explorer consumes the accepted HUD result without requests or discovery inference."""
import os
import tempfile
import unittest
from importlib import import_module
from pathlib import Path
from unittest.mock import Mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QColor, QTextDocument
from PySide6.QtWidgets import QApplication
from cmdrhelper.edsm_system_status import EdsmSystemStatus, STATUS_KEYS
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests.test_explorer_table_ux import ExplorerWindow


class ExplorerEdsmStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        set_language('de')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        settings = QSettings(str(Path(self.tmp.name) / 'test.ini'), QSettings.IniFormat)
        self.window = ExplorerWindow(settings)
        self.addCleanup(self.window.deleteLater)
        self.addCleanup(self.window.close)
        state = self.window.state
        state.system_body_count = 3
        state.system_signals_count = 0
        state.edsm_enabled = True
        state.edsm_body_count = 3
        state.system_all_bodies_found = True
        state.system_scan_value = 3706
        state.system_mapped_value = 9000
        state.system_address = 1
        self.pool, self.fetch = Mock(), Mock(return_value='known')
        self.source = EdsmSystemStatus(settings, pool=self.pool, fetch=self.fetch)
        self.window._edsm_system_status = self.source
        self.source.changed.connect(self.window._refresh_explorer_scan_header)
        self.notices = []
        self.source.notice.connect(self.notices.append)
        self.source.set_enabled(True)

    def arrive(self, name='Test', address=1, finish=True, result='known'):
        self.window.state.system = name
        self.window.state.system_address = address
        self.fetch.return_value = result
        self.source.observe([dict(event='FSDJump', StarSystem=name, SystemAddress=address)], 'FID')
        worker = self.pool.start.call_args.args[0]
        if finish:
            worker.run()
        return worker

    def document(self):
        doc = QTextDocument()
        doc.setHtml(self.window.system_scan_header.text())
        return doc

    def assert_status(self, text, color):
        doc = self.document()
        cursor = doc.find(text)
        self.assertFalse(cursor.isNull(), doc.toPlainText())
        self.assertEqual(cursor.charFormat().foreground().color().name(), color)

    def test_three_results_share_hud_text_and_precede_values(self):
        for index, (result, text, color) in enumerate([
                ('known', 'EDSM: BEKANNT', '#68c7ff'),
                ('unknown', 'EDSM: NICHT BEKANNT', '#ffb000'),
                ('no_response', 'EDSM: KEINE ANTWORT', '#9ba9b7')]):
            self.arrive(str(index), index, result=result)
            self.assert_status(text, color)
            self.assertEqual(self.notices[-1], (text,))
            plain = self.document().toPlainText()
            self.assertLess(plain.index('alle Körper gefunden'), plain.index(text))
            self.assertLess(plain.index(text), plain.index('Scanwert:'))
        self.assertEqual(self.fetch.call_count, 3)

    def test_switch_both_directions_clears_old_result_before_response(self):
        for index, result in enumerate(['known', 'unknown', 'known']):
            worker = self.arrive(str(index), index, finish=False)
            self.assert_status('EDSM: —', '#9ba9b7')
            self.assertNotIn('EDSM: BEKANNT', self.document().toPlainText())
            self.assertNotIn('EDSM: NICHT BEKANNT', self.document().toPlainText())
            self.fetch.return_value = result
            worker.run()
            self.assertIn(tr(STATUS_KEYS[result]), self.document().toPlainText())

    def test_late_response_and_state_first_switch_cannot_restore_old_status(self):
        old = self.arrive('A', 1, finish=False)
        self.arrive('B', 2, result='unknown')
        old.signals.finished.emit(old.generation, 'known')
        self.assert_status('EDSM: NICHT BEKANNT', '#ffb000')
        # State may refresh before the next journal position signal arrives.
        self.window.state.system_address = 3
        self.window._refresh_explorer_scan_header()
        self.assert_status('EDSM: —', '#9ba9b7')
        self.window.state.system = 'C'
        self.window._refresh_explorer_scan_header()
        self.assert_status('EDSM: —', '#9ba9b7')

    def test_disable_commander_change_and_pending_are_neutral_without_new_requests(self):
        self.arrive()
        self.source.set_enabled(False)
        self.assert_status('EDSM: —', '#9ba9b7')
        self.arrive('B', 2, finish=False)
        self.assertEqual(self.pool.start.call_count, 1)
        self.source.set_enabled(True)
        self.arrive('C', 3)
        self.source.observe([], 'OTHER-FID')
        self.assert_status('EDSM: —', '#9ba9b7')
        self.assertEqual(self.fetch.call_count, 2)

    def test_body_counts_and_missing_source_never_infer_discovery(self):
        del self.window._edsm_system_status
        for bodies, edsm_count in [([], 0), ([dict(was_discovered=False)], 1)]:
            self.window.state.system_bodies = bodies
            self.window.state.edsm_body_count = edsm_count
            self.window._refresh_explorer_scan_header()
            self.assert_status('EDSM: —', '#9ba9b7')
        self.fetch.assert_not_called()

    def test_twelve_languages_themes_large_font_and_narrow_wrapping(self):
        for theme, style, colors, background in [
                ('dark', DARK_STYLESHEET, ['#68c7ff', '#ffb000', '#9ba9b7'], '#0b1015'),
                ('light', LIGHT_STYLESHEET, ['#17679b', '#856000', '#536574'], '#eef1f4')]:
            self.app.setStyleSheet(style + '\nQLabel { font-size: 24px; }')
            self.window.ui_theme = theme
            for language in 'de en el es fi fr it nl no pl sv tr'.split():
                set_language(language)
                help_text = import_module('cmdrhelper.help_content.' + language).HELP_TOPICS['explorer'][1]
                self.assertIn('EDSM: —', help_text)
                for index, (status, key) in enumerate(STATUS_KEYS.items()):
                    self.arrive(language + status + theme, index, result=status)
                    self.assert_status(_TRANSLATIONS[language][key], colors[index])
                label = self.window.system_scan_header
                self.assertTrue(label.wordWrap())
                self.assertEqual(label.textFormat(), Qt.RichText)
                # Render the actual header alone at a constrained width so the
                # Explorer tables' minimum size cannot mask wrapping problems.
                label.setParent(None)
                self.addCleanup(label.deleteLater)
                label.setFixedWidth(320)
                label.ensurePolished()
                height = label.heightForWidth(320)
                self.assertGreater(height, label.heightForWidth(1200))
                label.resize(320, height)
                label.show()
                self.app.processEvents()
                self.assertFalse(label.grab().isNull())
            for color in colors:
                self.assertGreaterEqual(self.contrast(color, background), 4.5)
        self.assertEqual(len(_TRANSLATIONS), 12)

    def test_real_mainwindow_signal_wiring_and_live_theme_change(self):
        from tests.test_popup_ui_settings import PopupUiSettingsTests
        helper = PopupUiSettingsTests()
        helper.setUpClass()
        helper.setUp()
        self.addCleanup(helper.doCleanups)
        main = helper.main()
        helper.explorer(main)
        for key, value in vars(self.window.state).items():
            if key not in ('settings', 'database'):
                setattr(main.state, key, value)
        source = main._edsm_system_status
        source.pool = self.pool
        source.fetch = self.fetch
        # Observe the actual HUD receiver without creating an OS overlay.
        hud = Mock()
        main._navigation_hud = hud
        source.set_enabled(True)
        source.observe([dict(event='Location', StarSystem='Test', SystemAddress=1)], 'FID')
        self.pool.start.call_args.args[0].run()
        hud.show_message.assert_called_once_with(('EDSM: BEKANNT',), 4500, channel='edsm')
        for theme, color in [('light', '#17679b'), ('dark', '#68c7ff')]:
            main._set_theme(theme)
            doc = QTextDocument()
            doc.setHtml(main.system_scan_header.text())
            cursor = doc.find('EDSM: BEKANNT')
            self.assertFalse(cursor.isNull())
            self.assertEqual(cursor.charFormat().foreground().color().name(), color)
        source.observe([dict(event='FSDJump', StarSystem='Next', SystemAddress=2)], 'FID')
        self.assertIn('EDSM: —', main.system_scan_header.text())
        hud.clear_message.assert_called_with(channel='edsm')

    @staticmethod
    def contrast(a, b):
        def luminance(value):
            c = QColor(value)
            channels = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
                        for v in (c.redF(), c.greenF(), c.blueF())]
            return sum(v * weight for v, weight in zip(channels, (.2126, .7152, .0722)))
        values = sorted([luminance(a), luminance(b)])
        return (values[1] + .05) / (values[0] + .05)
