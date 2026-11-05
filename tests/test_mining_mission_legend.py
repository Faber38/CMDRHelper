"""Display-only regression for the shared cargo legend in mining."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PySide6.QtCore import QEvent, QSettings, QSize
from PySide6.QtWidgets import QApplication
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.ui.mining_view import MiningView
from cmdrhelper.ui.mission_cargo import (
    CargoMissionLegend, mission_cargo_icon, possible_mission_cargo_icon,
)
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class MiningMissionLegendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.addCleanup(set_language, get_language())
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.settings = QSettings(str(Path(self.tmp.name) / 'settings.ini'), QSettings.IniFormat)

    def test_shared_symbols_translations_themes_and_unchanged_stock_legend(self):
        for language, translations in _TRANSLATIONS.items():
            set_language(language)
            view = MiningView(self.settings)
            try:
                legend = view.cargo_mission_legend
                self.assertIsInstance(legend, CargoMissionLegend)
                self.assertEqual(legend.layout().rowCount(), 2)
                self.assertEqual(legend.layout().contentsMargins().top(), 0)
                self.assertEqual(legend.layout().verticalSpacing(), 2)
                stock = [(label.text(), label.toolTip()) for label in view.stock_legend_labels]
                self.assertEqual([text for text, _ in stock],
                    [tr('mining.legend_' + key) for key in
                     ('confirmed', 'last_known', 'unknown', 'inconsistent')])
                self.assertEqual([tip for _, tip in stock], [tr('mining.stock_confirmed'),
                    tr('mining.stock_tracked') + '\n' + tr('mining.stock_stale'),
                    tr('mining.stock_unknown'), tr('mining.carrier_inconsistent')])
                pictures = []
                for light, style in ((False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)):
                    view.setStyleSheet(style)
                    view.set_light_mode(light)
                    view.resize(900, 650)
                    view.show()
                    self.app.processEvents()
                    legend.refresh()
                    self.assertEqual(legend.palette().window().color().lightness() > 128, light)
                    for entry, key, icon in zip(legend.entries,
                            ('trade.cargo_legend_blue', 'trade.cargo_legend_pink'),
                            (mission_cargo_icon, possible_mission_cargo_icon)):
                        actual_key, actual_icon, symbol, label = entry
                        self.assertEqual(actual_key, key)
                        self.assertIs(actual_icon, icon)
                        self.assertIn(key, translations)
                        self.assertEqual(label.text(), translations[key])
                        self.assertTrue(label.wordWrap())
                        self.assertEqual(symbol.pixmap().toImage(), icon(light).pixmap(QSize(16,14)).toImage())
                    pictures.append(legend.entries[0][2].pixmap().toImage())
                    self.assertEqual(stock, [(label.text(), label.toolTip()) for label in view.stock_legend_labels])
                    self.assertTrue(all(dot.text() == '●' for dot in view.stock_legend_dots))
                    legend.grab()  # Exercise the actual offscreen layout and painting.
                self.assertNotEqual(*pictures)
            finally:
                view.close()
                view.deleteLater()
                self.app.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_language_event_refreshes_shared_legend(self):
        set_language('de')
        view = MiningView(self.settings)
        try:
            set_language('fr')
            self.app.sendEvent(view.cargo_mission_legend, QEvent(QEvent.LanguageChange))
            self.assertEqual([label.text() for _, _, _, label in view.cargo_mission_legend.entries],
                             [tr('trade.cargo_legend_blue'), tr('trade.cargo_legend_pink')])
        finally:
            view.close()
            view.deleteLater()
            self.app.sendPostedEvents(None, QEvent.DeferredDelete)
