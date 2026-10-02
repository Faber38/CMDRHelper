"""Offline pad evidence, incremental reads and production recommendation path."""
from dataclasses import replace
from datetime import timedelta
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import unittest
from unittest.mock import patch

from cmdrhelper.pad_metadata import PadMetadata, largest_pad, matching_pad
from cmdrhelper.market_candidates import local_offer, merge_destinations, matches_location
from cmdrhelper.market_data import PadSize, MarketSearch
from cmdrhelper.market_store import MarketStore
from cmdrhelper.trade_market_source import TradeMarketSource
from cmdrhelper.recommendation_market_source import RecommendationStoreSession
from cmdrhelper.trade_recommendations import search_recommendations
from test_trade_recommendations import market, item, offer, NOW, FID, Provider

MID = 4280361219
ADDRESS = 9465973581169
NAME = 'Mackenzie Relay'
SYSTEM = 'Arietis Sector KX-T b3-4'


class PadMetadataTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.journals = self.root/'journals'
        self.spansh = self.root/'spansh'
        self.journals.mkdir()
        self.spansh.mkdir()
        self.path = self.journals/'Journal.2026-01-02T110000.01.log'
        self.resolver = PadMetadata()

    def event(self, pads=None, **changes):
        return dict(dict(event='Docked', timestamp=(NOW-timedelta(hours=1)).isoformat(),
            MarketID=MID, StationName=NAME, StarSystem=SYSTEM, SystemAddress=ADDRESS,
            LandingPads=pads or dict(Small=9, Medium=13, Large=7)), **changes)

    def write(self, events):
        self.path.write_text(''.join(json.dumps(e)+'\n' for e in events))

    def external(self, pads):
        (self.spansh/f'{ADDRESS}.json').write_text(json.dumps(dict(schema_version=1,
            source='spansh', system_address=ADDRESS, system_name=SYSTEM,
            fetched_at=NOW.isoformat(), stations=[dict(market_id=MID, station_name=NAME,
                landing_pads=pads)])))

    def lookup(self, metadata, mid=MID, name=NAME, system=SYSTEM, address=ADDRESS):
        return matching_pad(metadata, mid, name, system, address)

    def test_sizes_and_invalid_counts(self):
        for pads, expected in ((dict(small=9,medium=13,large=7),PadSize.LARGE),
                               (dict(small=3,medium=1,large=0),PadSize.MEDIUM),
                               (dict(small=1,medium=0,large=0),PadSize.SMALL),
                               (dict(small=0,medium=0,large=0),None),
                               (dict(small=1,medium=0,large=True),None),
                               (dict(small=1,medium=0,large=-1),None), ({},None), (None,None)):
            with self.subTest(pads=pads):
                self.assertEqual(largest_pad(pads),expected)

    def test_journal_priority_over_matching_spansh_and_identity_guards(self):
        self.write([self.event(dict(Small=3,Medium=1,Large=0))])
        self.external(dict(small=9,medium=13,large=7))
        data=self.resolver.read(self.journals,self.spansh)
        self.assertEqual(self.lookup(data),PadSize.MEDIUM)
        self.assertEqual(data[MID]['source'],'journal')
        for args in (dict(mid=MID+1),dict(name='Valhalla'),dict(system='Other'),dict(address=1)):
            self.assertIsNone(self.lookup(data,**args))

    def test_existing_spansh_cache_fallback(self):
        self.external(dict(small=9,medium=13,large=7))
        data=self.resolver.read(self.journals,self.spansh)
        self.assertEqual(self.lookup(data),PadSize.LARGE)
        self.assertEqual(data[MID]['source'],'spansh')

    def test_unchanged_files_not_reopened_and_only_new_tail_read(self):
        self.write([self.event()])
        self.resolver.read(self.journals)
        with patch.object(Path,'open',side_effect=AssertionError('unchanged journal reread')):
            self.assertEqual(self.lookup(self.resolver.read(self.journals)),PadSize.LARGE)
        offset=self.path.stat().st_size
        with self.path.open('a') as f:
            f.write(json.dumps(self.event(dict(Small=1,Medium=0,Large=0),timestamp=NOW.isoformat()))+'\n')
        original=Path.open
        seeks=[]
        def opened(path,*args,**kwargs):
            handle=original(path,*args,**kwargs)
            seek=handle.seek
            def tracked(value,*rest):
                seeks.append(value)
                return seek(value,*rest)
            handle.seek=tracked
            return handle
        with patch.object(Path,'open',opened):
            self.assertEqual(self.lookup(self.resolver.read(self.journals)),PadSize.SMALL)
        self.assertEqual(seeks,[offset])

    def test_docking_requested_uses_current_system_and_truncation_discards_old_data(self):
        e=self.event(event='DockingRequested')
        del e['StarSystem'];del e['SystemAddress']
        self.write([dict(event='Location',StarSystem=SYSTEM,SystemAddress=ADDRESS),e])
        self.assertEqual(self.lookup(self.resolver.read(self.journals)),PadSize.LARGE)
        self.write([])
        self.assertIsNone(self.lookup(self.resolver.read(self.journals)))

    def test_prices_and_freshness_survive_metadata_merge(self):
        local=local_offer(market(mid=MID,station_name=NAME,system_name=SYSTEM,
            system_address=ADDRESS),item(),5,NOW)
        older=offer(mid=MID,station_name=NAME,system_name=SYSTEM,system_id64=ADDRESS,
            stamp=NOW-timedelta(hours=1),commander_sell_price=99999)
        merged=merge_destinations([local],[older],NOW,timedelta(hours=24))[0]
        self.assertEqual(merged,replace(local,largest_pad=PadSize.LARGE))
        newer=replace(older,market_updated_at=NOW,largest_pad=None)
        old_local=replace(local,market_updated_at=NOW-timedelta(hours=1),largest_pad=PadSize.MEDIUM)
        self.assertEqual(merge_destinations([old_local],[newer],NOW,timedelta(hours=24))[0],
                         replace(newer,largest_pad=PadSize.MEDIUM))
        for other in (replace(older,market_id=MID+1),replace(older,system_name='Other')):
            own=next(o for o in merge_destinations([local],[other],NOW,timedelta(hours=24))
                     if o.market_id==MID)
            self.assertIsNone(own.largest_pad)

    def test_filter_semantics(self):
        for required in PadSize:
            for known in (None,PadSize.SMALL,PadSize.MEDIUM,PadSize.LARGE):
                ranks={None:0,PadSize.ANY:0,PadSize.SMALL:1,PadSize.MEDIUM:2,PadSize.LARGE:3}
                self.assertEqual(matches_location(offer(largest_pad=known),
                    MarketSearch('',SYSTEM,required_pad=required)),ranks[known]>=ranks[required])

    def test_mackenzie_sqlite_recommendation_large_filter(self):
        self.write([self.event()])
        path=self.root/'markets.db'
        origin=market(system_name=SYSTEM,system_address=ADDRESS)
        target=market(mid=MID,station_name=NAME,system_name=SYSTEM,system_address=ADDRESS)
        with MarketStore(path,clock=lambda:NOW) as store:
            store.record_observation(origin);store.record_observation(target)
        source=TradeMarketSource(path,FID,SYSTEM,ADDRESS,journal_folder=self.journals)
        for pad in (PadSize.LARGE,PadSize.MEDIUM):
            query=MarketSearch('',SYSTEM,required_pad=pad)
            with RecommendationStoreSession(source,origin,query,clock=lambda:NOW,cancel=Event()) as session:
                result=search_recommendations(session.origin,(),{},16,10,query,Provider(),
                    clock=lambda:NOW,local_only=True,local_evaluator=session)
                self.assertEqual(len(result.rows),1)
                self.assertEqual(result.rows[0].destination.market_id,MID)
                self.assertEqual(result.rows[0].destination.largest_pad,PadSize.LARGE)
                self.assertEqual(result.rows[0].destination.commander_sell_price,item()['commander_sell_price'])

    def test_unknown_valhalla_remains_unknown(self):
        local=local_offer(market(station_name='Valhalla'),item(),5,NOW)
        self.assertIsNone(local.largest_pad)
        self.assertFalse(matches_location(local,MarketSearch('',SYSTEM,required_pad=PadSize.LARGE)))
