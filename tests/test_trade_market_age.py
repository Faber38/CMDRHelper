"""Shared market age: boundaries, retained snapshots and isolated QSettings."""
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from cmdrhelper.i18n import _TRANSLATIONS
from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, TradeSide
from cmdrhelper.observed_market_cache import ObservedMarketCache
from cmdrhelper.trade_search import search_trade
from cmdrhelper.trade_recommendations import search_recommendations
from cmdrhelper.ui.market_age import MarketAgeCombo, HOURS, SETTING
from cmdrhelper.ui.trade_view import TradeView
from test_trade_recommendations import market, offer, NOW, BEER, FID
import test_market_data_provider as provider_tests
import test_recommendations_view as view_tests


class MarketAgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_all_boundaries_local_community_both_directions_and_recommendations(self):
        for hours in (24, 48, 72, 168, 336, 720, 0):
            maximum = timedelta(hours=hours) if hours else None
            for seconds in (-1, 0, 1):
                age = timedelta(hours=hours or 24000, seconds=seconds)
                stamp = NOW-age
                expected = not hours or seconds <= 0
                quote = offer(stamp=stamp, commander_buy_price=10000, supply=1000)
                provider = Mock()
                provider.search_sell.return_value = provider.search_buy.return_value = MarketSearchResult(
                    MarketStatus.OK, (quote,))
                query = MarketSearch(BEER.frontier_id, 'Fixture System', max_age=maximum)
                for source in ('local', 'community'):
                    local = [market(mid=2, stamp=stamp)] if source == 'local' else []
                    provider.search_sell.return_value = provider.search_buy.return_value = MarketSearchResult(
                        MarketStatus.OK, () if local else (quote,))
                    for side in TradeSide:
                        with self.subTest(hours=hours, seconds=seconds, source=source, side=side):
                            result = search_trade(provider, query, side, local, {2: 1}, FID, clock=lambda: NOW)
                            self.assertEqual(bool(result.offers), expected)
                    result = search_recommendations(market(), local, {2: 1}, 100, 10, query,
                                                    provider, clock=lambda: NOW, local_only=source == 'local')
                    self.assertEqual(bool(result.rows), expected)
                result = search_recommendations(market(stamp=stamp), [market(mid=2)], {2:1},
                                                100, 10, query, provider, clock=lambda: NOW, local_only=True)
                self.assertEqual(bool(result.rows), expected)

    def test_provider_payload_and_client_age_filter(self):
        for hours in (24, 48, 72, 168, 336, 720, 0):
            for side in TradeSide:
                age = (hours or 24000)*3600
                rows = [provider_tests.station(market_id=i+1, age=age+delta)
                        for i, delta in enumerate((-1, 0, 1))]
                for row in rows:
                    row['market'][0].update(buy_price=100, supply=100)
                harness = provider_tests.Harness(provider_tests.response(*rows))
                harness.provider.utcnow = lambda: provider_tests.NOW
                query = provider_tests.query(max_age=timedelta(hours=hours) if hours else None)
                result = getattr(harness.provider, 'search_'+side.value)(query)
                self.assertEqual(len(result.offers), 2 if hours else 3)
                filters = harness.payloads[0]['filters']
                self.assertEqual('market_updated_at' in filters, bool(hours))
                if hours:
                    self.assertEqual(filters['market_updated_at']['value'][0],
                                     (provider_tests.NOW-timedelta(hours=hours)).isoformat())

    def test_cache_filter_never_deletes_and_restart_can_expand_age(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'cache.json'
            cache = ObservedMarketCache(path, clock=lambda: NOW)
            for days in (1, 2, 3, 7, 14, 30, 300):
                self.assertTrue(cache.put(market(mid=days, stamp=NOW-timedelta(days=days))))
            before = path.read_bytes()
            for hours, count in ((24,1),(48,2),(72,3),(168,4),(336,5),(720,6),(0,7)):
                fresh = ObservedMarketCache(path, clock=lambda: NOW)
                self.assertEqual(len(fresh.all(FID, timedelta(hours=hours) if hours else None)), count)
                self.assertTrue(fresh.cleanup())
                self.assertEqual(path.read_bytes(), before)

    def test_persisted_selection_and_invalid_fallback_all_languages(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory)/'settings.ini')
            settings = QSettings(path, QSettings.IniFormat)
            state = SimpleNamespace(settings=settings)
            combo = MarketAgeCombo(state)
            self.assertEqual(combo.currentData(), 24)
            for hours in HOURS:
                combo.setCurrentIndex(combo.findData(hours))
                restored = MarketAgeCombo(SimpleNamespace(settings=QSettings(path, QSettings.IniFormat)))
                self.assertEqual(restored.currentData(), hours)
            for value in ('bad', -1, 49, True, 24.5, '', None):
                settings.setValue(SETTING, value)
                settings.sync()
                self.assertEqual(MarketAgeCombo(state).currentData(), 24)
            for language, translations in _TRANSLATIONS.items():
                for hours in HOURS:
                    self.assertIn('trade.age_option_'+str(hours), translations, language)


class AgeViewTests(unittest.TestCase):
    setUpClass = classmethod(view_tests.RecommendationViewTests.setUpClass.__func__)
    setUp = view_tests.RecommendationViewTests.setUp
    tearDown = view_tests.RecommendationViewTests.tearDown

    def test_synced_tabs_restored_without_provider_calls_and_no_snapshot_loss(self):
        settings = QSettings(str(Path(self.tmp.name)/'settings.ini'), QSettings.IniFormat)
        self.state.settings = settings
        settings.setValue(SETTING, 336)
        other = TradeView(self.state, provider=self.provider, pool=self.pool)
        try:
            before = self.cache.path.read_bytes()
            for hours in HOURS:
                other.recommendations.max_age.setCurrentIndex(other.recommendations.max_age.findData(hours))
                for tab in (0, 1, 2):
                    other.tabs.setCurrentIndex(tab)
                    self.assertEqual(other.max_age.currentData(), hours)
                    self.assertEqual(other.recommendations.max_age.currentData(), hours)
            self.assertFalse(self.provider.calls)
            self.assertEqual(self.cache.path.read_bytes(), before)
            restarted = TradeView(self.state, provider=self.provider, pool=self.pool)
            self.assertEqual(restarted.max_age.currentData(), 0)
            self.assertEqual(restarted.recommendations.max_age.currentData(), 0)
            restarted.close(); restarted.deleteLater()
        finally:
            other.close(); other.deleteLater()

    def test_old_origin_and_destination_unlimited_search_preserves_bookmarks(self):
        from PySide6.QtCore import Qt
        self.cache.put(market(mid=2))
        before = self.cache.path.read_bytes()
        self.now = NOW + timedelta(days=40)
        self.view.local_only.setChecked(True)
        self.assertIsNone(self.view.origin)
        self.view.max_age.setCurrentIndex(self.view.max_age.findData(720))
        self.assertIsNone(self.view.origin)
        self.view.max_age.setCurrentIndex(self.view.max_age.findData(0))
        self.assertIsNotNone(self.view.origin)
        self.assertFalse(self.provider.calls)
        self.view.start_search()
        view_tests.RecommendationViewTests.wait(self)
        self.assertTrue(self.view.rows)
        self.assertEqual(self.view.rows[0].destination.market_updated_at, NOW)
        self.assertTrue(self.view.table.item(0, 14).text())
        self.view.table.item(0, 0).setCheckState(Qt.Checked)
        remembered = dict(self.view.remembered_flights)
        self.view.max_age.setCurrentIndex(self.view.max_age.findData(24))
        self.assertFalse(self.view.rows)
        self.assertEqual(self.view.remembered_flights, remembered)
        self.assertEqual(self.cache.path.read_bytes(), before)
        self.assertFalse(self.provider.calls)
