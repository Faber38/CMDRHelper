"""Actual trade worker/UI with temporary commander-partitioned observed cache."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from threading import Event
import unittest

from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtWidgets import QApplication

from cmdrhelper.i18n import get_language, set_language, tr, _TRANSLATIONS
from cmdrhelper.market_data import MarketSearchResult, MarketStatus
from cmdrhelper.observed_market_cache import ObservedMarketCache
from cmdrhelper.trade_result_text import community_failure_text, market_notice_text
from cmdrhelper.ui.trade_view import TradeView
from test_recommendations_view import State, AsyncProvider
from test_trade_recommendations import market, item, NOW, BEER, FID
import test_trade_view as existing_ui


class CombinedTradeViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        previous = get_language(); self.addCleanup(set_language, previous); set_language('de')
        self.state = State()
        self.state.commander_fid = FID
        self.state.system = 'Fixture System'
        self.state.system_address = 100
        self.cache = ObservedMarketCache(Path(self.tmp.name)/'observed.json', clock=lambda: NOW)
        self.cache.put(market())
        self.cache.put(market(mid=2, fid='OTHER', rows=[item(buy=1, sell=999999)]))
        self.state.observed_markets = SimpleNamespace(cache=self.cache, context={})
        self.provider = AsyncProvider()
        original = self.provider.search_sell
        def failed(q, *, cancel):
            original(q, cancel=cancel)
            return MarketSearchResult(MarketStatus.TIMEOUT, query=q)
        self.provider.search_sell = self.provider.search_buy = failed
        self.pool = QThreadPool()
        self.view = TradeView(self.state, provider=self.provider, pool=self.pool)
        self.addCleanup(self.cleanup_view)
        self.before = self.cache.path.read_bytes()

    cleanup_view = existing_ui.TradeViewTests.cleanup_view
    wait = existing_ui.TradeViewTests.wait

    def search(self):
        self.view.commodity.set_commodity(BEER.frontier_id)
        self.view.start_search()
        self.wait()

    def test_both_tabs_show_partial_locals_and_source_without_extra_column(self):
        for tab in (0,1):
            self.view.tabs.setCurrentIndex(tab)
            self.search()
            self.assertEqual(self.view.table.rowCount(), 1)
            self.assertEqual(self.view.table.columnCount(), 10)
            self.assertEqual(self.view.table.item(0,0).data(Qt.ItemDataRole.UserRole).provider, 'local_elite')
            self.assertIn(community_failure_text('de'), self.view.status.text())
            self.assertEqual(self.view.market_notice.text(), market_notice_text('de'))
            self.assertIn(tr('recommend.local'), self.view.table.item(0, 0).toolTip())
            self.assertNotIn(tr('trade.truncated'), self.view.status.text())
            self.assertEqual(self.cache.path.read_bytes(), self.before)

    def test_no_local_is_real_error(self):
        self.state.commander_fid = 'EMPTY'
        self.state.commanderIdentityChanged.emit(None, '', '')
        self.search()
        self.assertEqual(self.view.table.rowCount(), 0)
        self.assertEqual(self.view.status.text(), tr('trade.timeout'))

    def test_commander_switch_uses_only_current_partition(self):
        self.search()
        self.assertEqual(self.view.offers[0].market_id, 1)
        self.state.commander_fid = 'OTHER'
        self.state.commanderIdentityChanged.emit(None, '', '')
        self.assertFalse(self.view.offers)
        self.search()
        self.assertEqual([o.market_id for o in self.view.offers], [2])

    def test_switch_during_search_discards_old_results(self):
        self.provider.gate.clear()
        self.view.commodity.set_commodity(BEER.frontier_id)
        self.view.start_search()
        self.state.commander_fid = 'OTHER'
        self.state.commanderIdentityChanged.emit(None, '', '')
        self.wait()
        self.assertFalse(self.view.offers)
        self.assertEqual(self.view.table.rowCount(), 0)
        self.provider.gate.set()
        self.search()
        self.assertEqual([o.market_id for o in self.view.offers], [2])

    def test_notice_all_languages(self):
        for lang in _TRANSLATIONS:
            self.assertTrue(community_failure_text(lang))
