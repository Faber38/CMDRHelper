"""Installation-wide local knowledge; synthetic JSON/SQLite only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
from pathlib import Path
import sqlite3
import tempfile
from threading import Event
import unittest
from unittest.mock import Mock, patch

from cmdrhelper.market_store import MarketStore, _SCHEMA, SCHEMA_VERSION, StoreFormatError
from cmdrhelper.market_migration import migrate_market_cache
from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, TradeSide
from cmdrhelper.trade_market_source import TradeMarketSource
from cmdrhelper.trade_search import search_trade
from cmdrhelper.recommendation_market_source import RecommendationStoreSession
from cmdrhelper.trade_recommendations import search_recommendations
from cmdrhelper.mining_market import read_mining_prices
from cmdrhelper.mining_catalog import MINING_COMMODITIES
from test_market_store import observation, commodity, NOW, FID, GOLD


def downgrade_fixture(path):
    """Recreate genuine schema-1 per-observer pointers from synthetic observations."""
    with sqlite3.connect(path) as con:
        for name in ('current_age', 'current_system', 'current_system_name', 'current_station'):
            con.execute('DROP INDEX '+name)
        con.execute('ALTER TABLE current_markets RENAME TO fixture_current_v2')
        schema = _SCHEMA[_SCHEMA.index('CREATE TABLE current_markets'): _SCHEMA.index('CREATE TABLE store_meta')]
        schema = schema.replace('PRIMARY KEY(market_id)', 'PRIMARY KEY(fid, market_id)')
        for fragment in schema.split(';'):
            if fragment.strip(): con.execute(fragment)
        con.execute('''INSERT INTO current_markets SELECT fid,market_id,observation_id,observed_at,
            system_address,lower(system_name) FROM (SELECT o.*, ROW_NUMBER() OVER
            (PARTITION BY fid,market_id ORDER BY observed_at DESC) rank FROM market_observations o) WHERE rank=1''')
        con.execute('DROP TABLE fixture_current_v2')
        con.execute('PRAGMA user_version=1')


class SharedMarketTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.path, self.source = self.root/'markets.db', self.root/'observed_markets.json'
        migrate_market_cache(self.source, self.path, clock=lambda: NOW)
        self.store = MarketStore(self.path, clock=lambda: NOW)
        self.addCleanup(self.store.close)

    def test_newest_shared_not_arrival_order_and_provenance_history(self):
        first = observation(fid='CMDR1', stamp=NOW-timedelta(hours=2), rows=[commodity(GOLD, sell=100)])
        second = observation(fid='CMDR2', stamp=NOW, rows=[commodity(GOLD, sell=300)])
        late = observation(fid='CMDR1', stamp=NOW-timedelta(hours=1), rows=[commodity(GOLD, sell=999)])
        self.store.record_observation(first)
        self.assertEqual(self.store.get_current(1), first)
        self.store.record_observation(second)
        result = self.store.record_observation(late)
        self.assertFalse(result.current_changed)
        self.assertEqual(self.store.get_current(1), second)
        self.assertEqual([h.fid for h in self.store.get_history('CMDR1',1).items], ['CMDR1','CMDR1'])
        self.assertEqual(self.store.get_history('CMDR2',1).items[0].fid, 'CMDR2')
        self.assertEqual(self.store.storage_stats()[0], 1)
        for active in ('CMDR1','CMDR2','CMDR3',''):
            provider = Mock()
            provider.search_buy.return_value = provider.search_sell.return_value = MarketSearchResult(MarketStatus.NO_RESULTS)
            source = TradeMarketSource(self.path, active, 'Synthetic System', 42)
            for side in TradeSide:
                result = search_trade(provider, MarketSearch(GOLD.frontier_id,'Synthetic System'),side,
                                      fid=active, local_source=source, clock=lambda:NOW)
                self.assertEqual(len(result.offers),1)
                self.assertEqual(result.offers[0].commander_sell_price,300)
        self.assertEqual(read_mining_prices(self.path,timedelta(days=1),clock=lambda:NOW).quotes[0].header.fid,'CMDR2')

    def test_recommendations_origin_and_target_can_be_observed_by_other_commanders(self):
        origin=observation(fid='CMDR1',rows=[commodity(GOLD,buy=10,sell=12)])
        target=observation(mid=2,fid='CMDR2',rows=[commodity(GOLD,buy=11,sell=100)])
        self.store.record_observation(origin);self.store.record_observation(target)
        provider=Mock()
        query=MarketSearch('', 'Synthetic System')
        for active in ('CMDR1','CMDR2','CMDR3'):
            source=TradeMarketSource(self.path,active,'Synthetic System',42)
            with RecommendationStoreSession(source,{k:v for k,v in origin.items() if k!='commodities'},query,
                                            clock=lambda:NOW,cancel=Event()) as session:
                result=search_recommendations(session.origin,(),{},10,0,query,provider,
                    clock=lambda:NOW,local_only=True,local_evaluator=session)
            self.assertEqual(result.rows[0].destination.market_id,2)
        provider.search_sell.assert_not_called()

    def test_tie_is_deterministic_and_latest_empty_suppresses_old_price(self):
        for fid in ('ZZ','AA'):
            self.store.record_observation(observation(fid=fid,rows=[commodity(GOLD,sell=10 if fid=='AA' else 90)]))
        self.assertEqual(self.store.get_current(1)['fid'],'AA')
        self.store.record_observation(observation(mid=2,fid='AA',rows=[commodity(GOLD,sell=10)]))
        self.store.record_observation(observation(mid=2,fid='ZZ',rows=[commodity(GOLD,sell=90)]))
        self.assertEqual(self.store.get_current(2)['fid'],'AA')
        self.store.record_observation(observation(mid=3,fid='CMDR1',stamp=NOW-timedelta(hours=1),rows=[commodity(GOLD,sell=999)]))
        self.store.record_observation(observation(mid=3,fid='CMDR2',rows=[]))
        self.assertEqual(read_mining_prices(self.path,timedelta(days=1),clock=lambda:NOW).quotes[0].commodity.commander_sell_price,10)

    def test_schema1_upgrade_preserves_all_observations_and_is_idempotent(self):
        rows=[observation(fid='CMDR1',stamp=NOW-timedelta(hours=2)),observation(fid='CMDR2')]
        for row in rows:self.store.record_observation(row)
        self.store.close();downgrade_fixture(self.path)
        with self.assertRaises(StoreFormatError):MarketStore(self.path,read_only=True)
        before=self.source.exists()
        result=migrate_market_cache(self.source,self.path,clock=lambda:NOW)
        self.assertFalse(result.imported)
        with MarketStore(self.path,read_only=True,clock=lambda:NOW) as store:
            self.assertEqual(store._con.execute('PRAGMA user_version').fetchone()[0],2)
            self.assertEqual(store.get_stats().observations,2)
            self.assertEqual(store.get_current(1),rows[1])
            self.assertEqual(store._con.execute('PRAGMA foreign_key_check').fetchall(),[])
            revision=store.get_stats().revision
        with MarketStore(self.path,clock=lambda:NOW) as store:self.assertEqual(store.get_stats().revision,revision)
        self.assertEqual(self.source.exists(),before)

    def test_upgrade_failure_rolls_back_schema_and_data(self):
        self.store.record_observation(observation())
        self.store.close();downgrade_fixture(self.path)
        original=MarketStore._verify_format
        def fail(store, *, version=SCHEMA_VERSION):
            original(store,version=version)
            if version==2:raise RuntimeError('synthetic upgrade failure')
        with patch.object(MarketStore,'_verify_format',fail),self.assertRaisesRegex(RuntimeError,'synthetic'):
            MarketStore(self.path,clock=lambda:NOW)
        with sqlite3.connect(self.path) as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0],1)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM market_observations').fetchone()[0],1)
            self.assertEqual(con.execute('PRAGMA table_info(current_markets)').fetchall()[0][-1],1)

    def test_json_all_fids_same_market_migrates_without_loss(self):
        path=self.root/'second.db';source=self.root/'source.json'
        rows=[observation(fid='CMDR2'),observation(fid='CMDR1',stamp=NOW-timedelta(hours=1))]
        raw=json.dumps(dict(version=1,markets=rows));source.write_text(raw)
        migrate_market_cache(source,path,clock=lambda:NOW)
        with MarketStore(path,read_only=True,clock=lambda:NOW) as store:
            self.assertEqual(store.get_stats().current_markets,1)
            self.assertEqual(store.get_stats().observations,2)
            self.assertEqual(store.get_current(1),rows[0])
            for fid in ('CMDR1','CMDR2'):self.assertEqual(len(store.get_history(fid,1).items),1)
        self.assertEqual(source.read_text(),raw)

    def test_cleanup_preserves_only_shared_current_forever(self):
        self.store.record_observation(observation(fid='CMDR1',stamp=NOW-timedelta(days=732)))
        self.store.record_observation(observation(fid='CMDR2',stamp=NOW-timedelta(days=731)))
        self.store.record_observation(observation(mid=2,fid='CMDR1',stamp=NOW-timedelta(days=2)))
        self.store.record_observation(observation(mid=2,fid='CMDR2',stamp=NOW-timedelta(days=1)))
        def cleanup():
            with MarketStore(self.path,clock=lambda:NOW) as store:return store.cleanup()
        with ThreadPoolExecutor(1) as pool:result=pool.submit(cleanup).result()
        self.assertEqual(result.observations_removed,1)
        self.assertEqual(self.store.get_current(1,None)['fid'],'CMDR2')
        self.assertEqual(self.store.get_history('CMDR1',2).items[0].fid,'CMDR1')

    def test_future_import_is_preserved_but_never_masks_valid_shared_quote(self):
        self.store.record_observation(observation(fid='CMDR1'))
        future=self.store.record_observation(observation(fid='CMDR2',stamp=NOW+timedelta(days=1)),allow_future=True)
        self.assertFalse(future.current_changed)
        self.assertEqual(self.store.get_current(1)['fid'],'CMDR1')
        self.assertEqual(self.store.get_observation('CMDR2',future.observation_id)['fid'],'CMDR2')
