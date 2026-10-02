"""Bookmarked outbound action, context cancellation and unchanged return routes."""
from dataclasses import replace
from datetime import timedelta
import time
import unittest
from unittest.mock import Mock
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from cmdrhelper.i18n import _TRANSLATIONS, set_language
from cmdrhelper.market_data import MarketTarget, PadSize, MarketSearchResult, MarketStatus
from cmdrhelper.market_candidates import local_offer
from cmdrhelper.trade_recommendations import SupplyRecommendation
from test_trade_recommendations import market, item, offer, NOW, BEER, GOLD
from test_supply_recommendations import source
from test_trade_station_body import cache_document
import test_recommendations_view as fixtures


class OutboundViewTests(unittest.TestCase):
    setUpClass = fixtures.RecommendationViewTests.__dict__['setUpClass']
    setUp = fixtures.RecommendationViewTests.setUp
    tearDown = fixtures.RecommendationViewTests.tearDown

    def wait(self):
        deadline = time.monotonic()+3
        while time.monotonic()<deadline:
            self.app.processEvents()
            QTest.qWait(5)
            if self.view.worker is None and not self.view._pending_fixed_search:
                return
        self.fail('Outbound worker did not finish')

    def bookmark(self, **changes):
        row = SupplyRecommendation(source(**changes), local_offer(market(),item(),0,NOW),20)
        supply = self.trade.supply_recommendations
        supply.render((row,))
        mark = supply.table.item(0,0)
        mark.setCheckState(Qt.Checked)
        return row, mark.data(Qt.UserRole+2)

    def action(self,key):
        self.trade.supply_recommendations.remembered_panel.route_buttons[key].click()

    def test_action_auto_search_direction_all_commodities_and_return_unchanged(self):
        self.now = NOW+timedelta(seconds=1)
        self.cache.put(market(stamp=self.now,rows=[item(),item(GOLD)]))
        row,key = self.bookmark()
        self.trade.tabs.setCurrentWidget(self.trade.supply_recommendations)
        self.action(key)
        self.wait()
        self.assertIs(self.trade.tabs.currentWidget(),self.view)
        self.assertEqual(self.view.active_target(),MarketTarget(2,200))
        self.assertTrue(self.view.fixed_target_enabled.isChecked())
        self.assertIn('Synthetic Port',self.view.fixed_target_label.text())
        self.assertIn('Fixture Port',self.view.fixed_target_label.text())
        self.assertEqual({r.destination.commodity_id for r in self.view.rows},{BEER.frontier_id,GOLD.frontier_id})
        self.assertTrue(all(q.target==MarketTarget(2,200) and q.reference_system=='Fixture System'
                            for q in self.provider.calls))
        self.assertTrue(all(r.destination.market_id==2 for r in self.view.rows))
        self.assertEqual(self.trade.supply_recommendations.remembered_flights[key],row)

    def test_toggle_off_cancels_and_restores_normal_query_without_filter_changes(self):
        _,key = self.bookmark()
        self.view.radius.setCurrentIndex(3)
        self.view.pad.setCurrentIndex(self.view.pad.findData(PadSize.LARGE))
        self.view.carriers.setChecked(True)
        self.view.arrival.setText('300')
        before = (self.view.radius.currentData(),self.view.pad.currentData(),
                  self.view.carriers.isChecked(),self.view.arrival.text(),self.view.margin.value())
        self.provider.gate.clear()
        self.action(key)
        worker = self.view.worker
        self.view.fixed_target_enabled.setChecked(False)
        self.assertTrue(worker.cancel.is_set())
        self.provider.gate.set()
        self.wait()
        self.assertFalse(self.view.rows)
        self.view.start_search(); self.wait()
        self.assertIsNone(self.provider.calls[-1].target)
        self.assertEqual(before,(self.view.radius.currentData(),self.view.pad.currentData(),
                         self.view.carriers.isChecked(),self.view.arrival.text(),self.view.margin.value()))

    def test_removal_uncheck_and_clear_invalidate_dependent_target(self):
        for method in ('remove','uncheck','clear'):
            _,key = self.bookmark()
            self.provider.gate.clear()
            self.action(key)
            worker = self.view.worker
            panel = self.trade.supply_recommendations.remembered_panel
            if method=='uncheck':
                self.trade.supply_recommendations.table.item(0,0).setCheckState(Qt.Unchecked)
            elif method=='remove':
                panel.entries[key][2].click()
            else:
                panel.clear()
            self.assertIsNone(self.view.active_target())
            self.assertIsNone(self.view.fixed_target_key)
            self.assertTrue(worker.cancel.is_set())
            self.provider.gate.set(); self.wait()
            self.assertFalse(self.view.rows)

    def test_multiple_bookmarks_switch_while_old_worker_runs(self):
        first,key1 = self.bookmark()
        second,key2 = self.bookmark(mid=3)
        self.provider.gate.clear()
        self.action(key1)
        old = self.view.worker
        self.action(key2)
        self.assertTrue(old.cancel.is_set())
        self.provider.gate.set(); self.wait()
        self.assertEqual(self.view.active_target(),MarketTarget(3,200))
        self.assertEqual(self.provider.calls[-1].target,MarketTarget(3,200))
        self.assertFalse(self.view.rows) # Fake provider returns station 2; never substitute.
        panel = self.trade.supply_recommendations.remembered_panel
        panel.remove(key1)
        self.assertEqual(self.view.active_target(),MarketTarget(3,200))
        self.assertEqual(panel.targets[key2],second)

    def test_body_and_pad_are_carried_from_bookmark_without_invention(self):
        service = Mock(spec=['cached'])
        service.cached.return_value = cache_document()
        self.state.spansh_stations = service
        for changes,expected in ((dict(station_type='CraterPort'),'4 a'),
                                 (dict(station_type='Coriolis'),None),
                                 (dict(station_type='CraterPort',station_name='Unknown'),None)):
            self.trade.supply_recommendations.remembered_panel.clear()
            _,key = self.bookmark(**changes)
            self.action(key); self.wait()
            text = self.view.fixed_target_label.text()
            self.assertEqual('Körper: 4 a' in text,expected is not None)
            self.assertIn('Groß',text)

    def test_context_change_discards_late_results_and_commander_clears_target(self):
        _,key = self.bookmark()
        self.provider.gate.clear()
        self.action(key)
        worker = self.view.worker
        self.state.station='Other station'; self.state.changed.emit()
        self.assertTrue(worker.cancel.is_set())
        self.provider.gate.set(); self.wait()
        self.assertFalse(self.view.rows)
        self.assertEqual(self.view.active_target(),MarketTarget(2,200))
        self.state.commander_fid='Other'; self.state.changed.emit()
        self.assertIsNone(self.view.active_target())

    def test_local_only_preserved_uses_store_no_community(self):
        self.cache.put(market(mid=2, system_address=200))
        _,key = self.bookmark()
        self.view.local_only.setChecked(True)
        self.action(key); self.wait()
        self.assertFalse(self.provider.calls)
        # Different-system distance is unknown in this fixture: do not invent it.
        self.assertFalse(self.view.rows)
        self.assertTrue(self.view.last_run.local_only)

    def test_no_target_data_no_fallback_and_no_automatic_retry(self):
        _,key = self.bookmark()
        self.provider.search_sell = lambda q,cancel: MarketSearchResult(MarketStatus.NO_RESULTS)
        self.action(key); self.wait()
        self.assertFalse(self.view.rows)
        self.assertEqual(self.view.active_target(),MarketTarget(2,200))
        self.assertFalse(self.view._pending_fixed_search)

    def test_i18n_keys_in_every_language(self):
        for language,values in _TRANSLATIONS.items():
            for key in ('search','search_tooltip','only_target','target','filters','return_route'):
                text = values['outbound.'+key]
                self.assertTrue(text,language)
                text.format(station='Port',system='System',commodity='Beer')

    def test_outbound_action_uses_explanatory_tooltip_in_all_languages(self):
        panel = self.trade.supply_recommendations.remembered_panel
        for language, values in _TRANSLATIONS.items():
            with self.subTest(language=language):
                set_language(language)
                panel.clear()
                _, key = self.bookmark()
                action = panel.route_buttons[key]
                self.assertEqual(action.toolTip(), values['outbound.search_tooltip'])
                self.assertNotEqual(action.toolTip(), action.text())
                self.assertGreater(len(action.toolTip()), len(action.text()))
                self.assertFalse(self.provider.calls)
                self.assertIsNone(self.view.active_target())
