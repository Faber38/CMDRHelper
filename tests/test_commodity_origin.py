"""Pinned origin metadata, local-only resolution and informational purchase UI."""
from dataclasses import replace
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from cmdrhelper._commodity_master_data import COMMODITIES
from cmdrhelper.commodity_master import all_commodities, lookup_by_symbol, _build_indexes
from cmdrhelper.commodity_origin import OriginResolver, CommodityOrigin
from tools.generate_commodity_master import build_rows

EXPECTED = {'BlueMilk':128639992, 'LavianBrandy':128106744, 'SoontillRelics':3225348096,
            'JaquesQuinentianStill':128667761, 'CrystallineSpheres':128059402}
MID = EXPECTED['BlueMilk']


class CatalogOriginTests(unittest.TestCase):
    def test_exact_sources_regenerate_catalog_and_examples(self):
        self.assertEqual(build_rows(), COMMODITIES)
        self.assertEqual(sum(c.origin_market_id is not None for c in all_commodities()), 142)
        for symbol, mid in EXPECTED.items():
            self.assertEqual(lookup_by_symbol(symbol).origin_market_id, mid)
        self.assertTrue(lookup_by_symbol('GalacticTravelGuide').rare)

    def test_optional_origin_and_normal_commodity(self):
        gold = lookup_by_symbol('gold')
        self.assertIsNone(gold.origin_market_id)
        rare = replace(lookup_by_symbol('BlueMilk'), origin_market_id=None)
        self.assertIsNone(rare.origin_market_id)
        _build_indexes([gold, rare])
        for item in (replace(gold, origin_market_id=MID), replace(rare, origin_market_id=True),
                     replace(rare, origin_market_id=-1)):
            with self.assertRaises(ValueError):
                _build_indexes([item])


class LocalOriginTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name); self.db = self.root/'fixture.db'
        with sqlite3.connect(self.db) as con:
            con.executescript('''CREATE TABLE systems(system_address INTEGER,name TEXT,x REAL,y REAL,z REAL);
                CREATE TABLE station_observations(market_id INTEGER,station_name TEXT,system_address INTEGER);
                INSERT INTO systems VALUES(1,'Origin',0,0,0),(2,'Destination',3,4,0);''')
            con.execute('INSERT INTO station_observations VALUES(?,?,?)', (MID,'Fixture Port',2))
        self.resolver = OriginResolver(self.db, spansh_folder=self.root/'cache')

    def cache(self, station='Fixture Port', address=2):
        folder = self.root/'cache';folder.mkdir(exist_ok=True)
        (folder/f'{address}.json').write_text(json.dumps(dict(schema_version=1,source='spansh',
            system_address=address,system_name='Destination',fetched_at='2026-01-01T00:00:00Z',
            stations=[dict(market_id=MID,station_name=station)])))

    def test_station_identity_and_trustworthy_distance(self):
        o = self.resolver.resolve(MID, 'Origin', 1)
        self.assertEqual((o.station_name,o.system_name,o.system_address),('Fixture Port','Destination',2))
        self.assertEqual(o.distance_ly, 5)
        self.assertEqual(o.coordinates, (3,4,0))
        self.assertIsNone(self.resolver.resolve(MID, 'Missing').distance_ly)
        with sqlite3.connect(self.db) as con:
            con.execute("INSERT INTO systems VALUES(3,'Origin',99,99,99)")
        self.assertIsNone(self.resolver.resolve(MID,'Origin').distance_ly)
        self.assertEqual(self.resolver.resolve(MID,'Origin',1).distance_ly,5)

    def test_missing_unknown_corrupt_and_conflicting_sources(self):
        self.assertIsNone(self.resolver.resolve(EXPECTED['LavianBrandy']).station_name)
        self.cache()
        self.assertEqual(self.resolver.resolve(MID).station_name,'Fixture Port')
        self.cache('Contradictory Port')
        result=self.resolver.resolve(MID)
        self.assertTrue(result.conflict)
        self.assertIsNone(result.station_name)
        self.assertEqual(result.market_id,MID)
        (self.root/'cache/2.json').write_text('{')
        self.assertEqual(self.resolver.resolve(MID).station_name,'Fixture Port')
        self.assertIsNone(OriginResolver(self.root/'missing.db').resolve(MID).station_name)
        self.assertFalse((self.root/'missing.db').exists())

    def test_spansh_only_without_fetch_or_coordinates(self):
        self.cache()
        with patch('cmdrhelper.spansh_cache.fetch_system',side_effect=AssertionError('network')):
            r=OriginResolver(spansh_folder=self.root/'cache')
            o=r.resolve(MID,'Origin')
            self.assertEqual(o.station_name,'Fixture Port')
            self.assertIsNone(o.distance_ly)
            first=r._files.copy()
            self.assertEqual(r.resolve(MID),o)
            self.assertEqual(r._files,first)

    def test_market_observations_resolve_identity_without_offers(self):
        path=self.root/'markets.db'
        with sqlite3.connect(path) as con:
            con.executescript('''CREATE TABLE current_markets(market_id BLOB,observation_id INTEGER);
                CREATE TABLE market_observations(observation_id INTEGER,market_id BLOB,
                station_name TEXT,system_name TEXT,system_address BLOB);''')
            con.execute('INSERT INTO current_markets VALUES(?,1)',(MID.to_bytes(8,'big'),))
            con.execute('INSERT INTO market_observations VALUES(1,?,?,?,?)',
                        (MID.to_bytes(8,'big'),'Market Port','Market System',(10).to_bytes(8,'big')))
        o=OriginResolver(market_path=path).resolve(MID)
        self.assertEqual(o.station_name,'Market Port')
        self.assertEqual(o.system_address,10)
        self.assertFalse(hasattr(o,'supply'))
        self.assertFalse(hasattr(o,'price'))


from PySide6.QtWidgets import QApplication
from cmdrhelper.ui.trade_view import TradeView
from cmdrhelper.i18n import set_language, get_language, tr, _TRANSLATIONS
from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus
from tests.test_trade_view import State, offer


class OriginTradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        old=get_language();self.addCleanup(set_language,old);set_language('de')
        self.pool=Mock();self.state=State()
        self.view=TradeView(self.state,provider=Mock(),pool=self.pool)
        self.view.show();self.addCleanup(self.view.close)
        self.view.tabs.setCurrentIndex(1)
        self.master=lookup_by_symbol('BlueMilk')
        self.view.commodity.set_commodity(self.master.frontier_id)
        self.query=MarketSearch(self.master.frontier_id,'Test Origin',minimum_quantity=1)
        self.view._origin=CommodityOrigin(MID,'Fixture Port','Destination',2,distance_ly=5)
        self.view.render_origin()

    def test_no_offer_keeps_origin_without_invented_stock(self):
        self.view.local_only.setChecked(True)
        self.view.show_result(MarketSearchResult(MarketStatus.NO_RESULTS,query=self.query),self.query)
        text=self.view.origin_info.text()
        self.assertIn('Fixture Port · Destination',text)
        self.assertIn('5,0 ly',text)
        self.assertIn('nicht bestätigt',text)
        self.assertIn('Keine aktuellen Angebote',self.view.origin_notice.text())
        self.assertTrue(self.view.origin_notice.isVisible())
        self.assertEqual(self.view.table.rowCount(),0)
        self.assertEqual(self.view.offers,())
        self.pool.start.assert_not_called()

    def test_real_offer_remains_normal_purchase_result(self):
        o=offer(commodity_id=self.master.frontier_id,commodity_symbol=self.master.symbol,
                market_id=MID,commander_buy_price=4708,supply=42)
        self.view.show_result(MarketSearchResult(MarketStatus.OK,(o,),self.query),self.query)
        self.assertEqual(self.view.table.rowCount(),1)
        self.assertEqual(self.view.table.item(0,3).value,4708)
        self.assertEqual(self.view.table.item(0,4).value,42)
        self.assertNotIn('nicht bestätigt',self.view.origin_info.text())
        self.assertFalse(self.view.origin_notice.isVisible())

    def test_origin_theme_colors_and_unchanged_plain_text(self):
        from PySide6.QtGui import QColor, QPalette
        from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        self.view.show_result(MarketSearchResult(MarketStatus.NO_RESULTS,query=self.query),self.query)
        expected = 'Ursprungsstation: Fixture Port · Destination\nEntfernung: 5,0 ly\n' + tr('trade.origin_unconfirmed')
        for theme, highlight, normal in ((DARK_STYLESHEET, '#f0ad4e', '#d8dde3'),
                                          (LIGHT_STYLESHEET, '#b36a00', '#20262c')):
            with self.subTest(theme=highlight):
                self.app.setStyleSheet(theme)
                self.app.processEvents()
                self.assertEqual(self.view.origin_info.palette().color(QPalette.WindowText), QColor(highlight))
                self.assertEqual(self.view.origin_notice.palette().color(QPalette.WindowText), QColor(normal))
                self.assertEqual(self.view.origin_info.text(), expected)
                self.assertEqual(self.view.origin_notice.text(), tr('trade.origin_no_offers'))
                self.assertTrue(self.view.origin_notice.isVisible())
                # The same highlight applies when a confirmed offer is displayed.
                self.view._origin_no_offer = False
                self.view.render_origin()
                self.assertFalse(self.view.origin_notice.isVisible())
                self.assertEqual(self.view.origin_info.palette().color(QPalette.WindowText), QColor(highlight))
                self.view._origin_no_offer = True
                self.view.render_origin()
        self.pool.start.assert_not_called()
        self.view.provider.search.assert_not_called()

    def test_id_only_and_unknown_origin_no_names_invented(self):
        self.view._origin=CommodityOrigin(MID)
        self.view.show_result(MarketSearchResult(MarketStatus.NO_RESULTS,query=self.query),self.query)
        self.assertIn(str(MID),self.view.origin_info.text())
        self.assertNotIn('Fixture Port',self.view.origin_info.text())
        self.assertNotIn('Entfernung',self.view.origin_info.text())
        with patch('cmdrhelper.ui.trade_view.lookup_by_id',return_value=replace(self.master,origin_market_id=None)):
            self.view.refresh_origin()
        self.assertFalse(self.view.origin_info.isVisible())
        self.assertTrue(self.view.status.text())

    def test_worker_stale_results_and_sell_hidden(self):
        resolver=Mock(database_path='fixture',market_path=None,spansh_folder=None)
        resolver.resolve.return_value=CommodityOrigin(MID,'Fixture','Destination')
        self.view._origin_resolver=resolver
        self.view.invalidate_origin()
        worker=self.view._origin_worker
        self.view.commodity.set_commodity(lookup_by_symbol('gold').frontier_id)
        worker.run()
        self.assertIsNone(self.view._origin)
        self.assertFalse(self.view.origin_info.isVisible())
        self.view.tabs.setCurrentIndex(0)
        self.assertFalse(self.view.origin_info.isVisible())

    def test_translations_all_languages(self):
        for language,texts in _TRANSLATIONS.items():
            for key in ('station','market_id','unconfirmed','no_offers','distance'):
                self.assertIn('trade.origin_'+key,texts,language)
