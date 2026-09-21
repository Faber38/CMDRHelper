"""Offline status UI with real cache/observer and synthetic journals only."""
from datetime import timedelta
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject, Signal, QEvent
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from cmdrhelper.i18n import set_language, get_language, tr, _TRANSLATIONS
from cmdrhelper.observed_market_cache import ObservedMarketCache
from cmdrhelper.observed_market_observer import ObservedMarketObserver
from cmdrhelper.ui.trade_view import TradeView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from test_observed_market_cache import NOW, FID, snapshot, event, sidecar


class State(QObject):
    changed = Signal()
    observedMarketsChanged = Signal()
    commanderIdentityChanged = Signal(object, str, str)
    system = 'Fixture System'
    commander_fid = FID


class ObservedStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.now = NOW
        self.language = get_language()
        set_language('de')
        self.state = State()
        self.cache = ObservedMarketCache(self.root/'cache.json', clock=lambda: self.now)
        self.observer = ObservedMarketObserver(self.cache, clock=lambda: self.now,
                                              on_changed=self.state.observedMarketsChanged.emit)
        self.state.observed_markets = self.observer
        self.view = TradeView(self.state)

    def tearDown(self):
        self.view.close()
        self.view.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        set_language(self.language)
        self.tmp.cleanup()

    def text(self):
        return self.view.observed_status.text()

    def test_zero_one_two_and_same_market_replacement(self):
        self.assertEqual(self.text(), 'Eigene Marktdaten: 0 Stationen')
        self.cache.put(snapshot(NOW-timedelta(minutes=3)))
        self.assertEqual(self.text(), 'Eigene Marktdaten: 1 Station · zuletzt vor 3 Min.')
        self.cache.put(snapshot(NOW-timedelta(hours=2), mid=456))
        self.assertEqual(self.text(), 'Eigene Marktdaten: 2 Stationen · zuletzt vor 3 Min.')
        self.cache.put(snapshot(mid=456))
        self.assertEqual(self.text(), 'Eigene Marktdaten: 2 Stationen · zuletzt gerade eben')

    def test_other_fid_source_and_commander_change(self):
        self.cache.put(snapshot())
        self.cache.put(snapshot(fid='F_OTHER', mid=456))
        self.assertFalse(self.cache.put(dict(snapshot(mid=789), source='spansh')))
        self.assertIn('1 Station ·', self.text())
        self.state.commander_fid = 'F_EMPTY'
        self.state.commanderIdentityChanged.emit(2, 'F_EMPTY', 'Synthetic')
        self.assertEqual(self.text(), 'Eigene Marktdaten: 0 Stationen')
        self.state.commander_fid = 'F_OTHER'
        self.state.changed.emit()
        self.assertIn('1 Station ·', self.text())

    def test_ttl_cleanup_notifies_and_exact_boundary(self):
        self.cache.put(snapshot())
        self.cache.put(snapshot(NOW-timedelta(hours=1), mid=456))
        self.now += timedelta(hours=23, seconds=-1)
        self.view.refresh_observed_markets()
        self.assertIn('2 Stationen', self.text())
        self.now += timedelta(seconds=1)
        self.cache.all(FID)  # Normal access elsewhere must update the visible label.
        self.assertEqual(self.text(), 'Eigene Marktdaten: 1 Station · zuletzt vor 23 Std.')
        self.now += timedelta(hours=1)
        self.cache.all(FID)
        self.assertEqual(self.text(), 'Eigene Marktdaten: 0 Stationen')
        self.assertEqual(json.loads(self.cache.path.read_text())['markets'], [])

    def test_observer_capture_and_replacement_without_polling(self):
        journal = self.root/'Journal.2026-01-02T110000.01.log'
        journal.write_text(json.dumps(dict(event='LoadGame', FID=FID))+'\n')
        self.observer.set_folder(self.root)
        for minute in (0, 3):
            self.now = NOW + timedelta(minutes=minute)
            with journal.open('a') as stream:
                stream.write(json.dumps(event(self.now))+'\n')
            market = self.root/'Market.json'
            market.write_text(json.dumps(sidecar(self.now)))
            os.utime(market, (self.now.timestamp(), self.now.timestamp()))
            self.assertTrue(self.observer.consume([journal]))
            self.assertEqual(self.text(), 'Eigene Marktdaten: 1 Station · zuletzt gerade eben')
            self.assertEqual(self.cache.get(FID, 123)['observed_at'], self.now.isoformat())
            self.now += timedelta(minutes=2)
            self.view.refresh_reference()
            self.assertIn('zuletzt vor 2 Min.', self.text())

    def test_show_refreshes_and_does_not_change_observation(self):
        self.cache.put(snapshot())
        self.now += timedelta(minutes=3)
        before = self.cache.path.read_bytes()
        self.view.show()
        self.app.processEvents()
        self.assertIn('zuletzt vor 3 Min.', self.text())
        self.assertEqual(before, self.cache.path.read_bytes())

    def test_defensive_source_and_duplicate_filter(self):
        rows = [snapshot(), snapshot(), dict(snapshot(mid=456), source='spansh'), snapshot(fid='F_OTHER')]
        with patch.object(self.cache, 'all', return_value=rows):
            self.view.refresh_observed_markets()
        self.assertIn('1 Station ·', self.text())

    def test_twelve_languages_themes_fonts_widths(self):
        self.cache.put(snapshot(NOW-timedelta(minutes=3)))
        self.cache.put(snapshot(mid=456))
        style = self.app.styleSheet()
        try:
            for lang in ('de','en','el','es','fi','fr','it','nl','no','pl','sv','tr'):
                set_language(lang)
                for key in ('observed_one','observed_many','observed_now','observed_last','observed_tooltip'):
                    self.assertIn('trade.'+key, _TRANSLATIONS[lang])
                for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                    self.app.setStyleSheet(theme)
                    for size in (10, 18):
                        self.app.setStyleSheet(theme + f'\nQWidget {{ font-size: {size}pt; }}')
                        self.view.setFont(QFont('Sans Serif', size))
                        for width in (480, 1200):
                            self.view.resize(width, 900)
                            self.view.refresh_observed_markets()
                            self.view.show()
                            self.app.processEvents()
                            label = self.view.observed_status
                            self.assertTrue(label.wordWrap())
                            self.assertIn('2', label.text())
                            self.assertNotIn('trade.', label.text())
                            self.assertGreaterEqual(label.height(), label.heightForWidth(label.width()))
                            self.assertLessEqual(label.width(), self.view._scroll.viewport().width())
                            self.assertLessEqual(label.geometry().bottom(), self.view.filters.geometry().top())
        finally:
            self.app.setStyleSheet(style)
