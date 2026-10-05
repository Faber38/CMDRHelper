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
from cmdrhelper.ui.observed_market_status import format_cache_size
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

    def assert_status(self, count):
        unit = 'Station' if count == 1 else 'Stationen'
        size = self.cache.path.stat().st_size if self.cache.path.exists() else 0
        self.assertEqual(self.text(), f'Lokale Marktdaten: {count} {unit} · {format_cache_size(size)}')
        self.assertEqual(self.cache.storage_stats(), (count, size))
        self.assertEqual(self.view.recommendations.observed_status.text(), self.text())

    def test_zero_one_two_and_same_market_replacement(self):
        self.assert_status(0)
        self.assertFalse(self.cache.path.exists())
        self.assertTrue(self.cache.put(snapshot(NOW-timedelta(minutes=3))))
        self.assert_status(1)
        size = self.cache.storage_stats()[1]
        self.assertTrue(self.cache.put(snapshot(NOW-timedelta(hours=2), mid=456)))
        self.assert_status(2)
        self.assertGreater(self.cache.storage_stats()[1], size)
        size = self.cache.storage_stats()[1]
        self.assertTrue(self.cache.put(dict(snapshot(mid=456), station_name='Updated station with a longer name')))
        self.assert_status(2)
        self.assertGreater(self.cache.storage_stats()[1], size)

    def test_other_fid_source_and_commander_change(self):
        self.cache.put(snapshot())
        self.cache.put(snapshot(fid='F_OTHER', mid=456))
        self.cache.put(snapshot(fid='F_OTHER'))
        self.assertFalse(self.cache.put(dict(snapshot(mid=789), source='spansh')))
        self.assert_status(2)
        for fid in ('F_EMPTY', 'F_OTHER', ''):
            self.state.commander_fid = fid
            self.state.commanderIdentityChanged.emit(2, fid, 'Synthetic')
            self.assert_status(2)

    def test_age_filter_refresh_preserves_snapshots(self):
        self.cache.put(snapshot())
        self.cache.put(snapshot(NOW-timedelta(days=400), mid=456))
        before = self.cache.path.read_bytes()
        self.now += timedelta(days=500)
        for index in range(self.view.max_age.count()):
            self.view.max_age.setCurrentIndex(index)
            self.view.refresh_observed_markets()
            self.view.recommendations.refresh()
            self.assert_status(2)
        self.assertEqual(self.cache.path.read_bytes(), before)

    def test_missing_empty_and_metadata_only(self):
        self.assert_status(0)
        self.cache.path.touch()
        self.view.refresh_observed_markets()
        self.view.recommendations.refresh()
        self.assert_status(0)
        self.cache.path.write_text('{"version":1,"markets":[]}')
        self.view.refresh_observed_markets()
        self.view.recommendations.refresh()
        self.assert_status(0)
        self.cache.put(snapshot())
        before = self.cache.path.read_bytes()
        with patch.object(Path, 'open', side_effect=AssertionError('No extra file read')), \
                patch.object(self.cache, 'all', side_effect=AssertionError('No filtered snapshots')), \
                patch.object(self.cache, '_write', side_effect=AssertionError('No writes')):
            self.view.refresh_observed_markets()
            self.view.recommendations.refresh()
            self.assert_status(1)
        self.assertEqual(self.cache.path.read_bytes(), before)
        self.cache.path.unlink()
        self.view.refresh_observed_markets()
        self.view.recommendations.refresh()
        self.assert_status(0)

    def test_file_size_units_and_actual_metadata(self):
        for size, expected in ((0, '0 B'), (1, '1 B'), (1023, '1.023 B'),
                               (1024, '1 KiB'), (732*1024, '732 KiB'),
                               (1024**2, '1 MiB'), (int(1.5*1024**2), '1,5 MiB'),
                               (2*1024**2, '2 MiB')):
            with self.subTest(size=size):
                self.assertEqual(format_cache_size(size), expected)
                with self.cache.path.open('wb') as stream:
                    stream.truncate(size)
                self.view.refresh_observed_markets()
                self.view.recommendations.refresh()
                self.assertEqual(self.text(), 'Lokale Marktdaten: 0 Stationen · '+expected)

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
            self.assert_status(1)
            self.assertEqual(self.cache.get(FID, 123)['observed_at'], self.now.isoformat())
            self.now += timedelta(minutes=2)
            self.view.refresh_reference()
            self.assert_status(1)

    def test_show_refreshes_and_does_not_change_observation(self):
        self.cache.put(snapshot())
        self.now += timedelta(minutes=3)
        before = self.cache.path.read_bytes()
        self.view.show()
        self.app.processEvents()
        self.assert_status(1)
        self.assertEqual(before, self.cache.path.read_bytes())

    def test_header_updates_after_sqlite_commit_on_sell_tab(self):
        self.state.station = 'Fixture Port'
        self.observer.use_market_store = True
        self.addCleanup(self.observer.close)
        journal = self.root/'Journal.2026-01-02T110000.01.log'
        journal.write_text(json.dumps(dict(event='LoadGame', FID=FID))+'\n')
        self.observer.set_folder(self.root)
        self.observer.writer.ready.result(timeout=10)
        self.view.show()
        self.view.tabs.setCurrentIndex(0)
        self.app.processEvents()
        badge = self.view.market_read_status
        self.assertEqual(badge.status, 'open')
        with journal.open('a') as stream:
            stream.write(json.dumps(dict(event(), event='Docked'))+'\n')
            stream.write(json.dumps(event())+'\n')
        market = self.root/'Market.json'
        market.write_text(json.dumps(sidecar()))
        os.utime(market, (NOW.timestamp(), NOW.timestamp()))
        self.assertFalse(self.observer.consume([journal]))
        self.observer._writes[0][1].result(timeout=10)
        self.app.processEvents()  # Deliver the worker's existing Qt signal, no manual refresh.
        self.assertEqual(self.view.tabs.currentIndex(), 0)
        self.assertTrue(badge.isVisible())
        self.assertEqual(badge.status, 'read')
        self.assertEqual(badge.toolTip(), tr('trade.current_market_read_tooltip', station='Fixture Port'))
        self.observer.close()

    def test_twelve_languages_themes_fonts_widths(self):
        self.cache.put(snapshot(NOW-timedelta(minutes=3)))
        self.cache.put(snapshot(mid=456))
        style = self.app.styleSheet()
        try:
            for lang in ('de','en','el','es','fi','fr','it','nl','no','pl','sv','tr'):
                set_language(lang)
                for key in ('observed_one','observed_many','observed_tooltip'):
                    self.assertIn('trade.'+key, _TRANSLATIONS[lang])
                for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                    self.app.setStyleSheet(theme)
                    for size in (10, 18):
                        self.app.setStyleSheet(theme + f'\nQWidget {{ font-size: {size}pt; }}')
                        self.view.setFont(QFont('Sans Serif', size))
                        for width in (480, 1200):
                            self.view.resize(width, 900)
                            self.view.refresh_observed_markets()
                            self.view.recommendations.refresh()
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
