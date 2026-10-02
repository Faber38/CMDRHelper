"""Station recovery after on-foot startup, using only temporary game/cache files."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from cmdrhelper.journal_reader import read_latest_state
from cmdrhelper.observed_market_cache import ObservedMarketCache, normalize_observation
from cmdrhelper.observed_market_observer import ObservedMarketObserver
from cmdrhelper.station_context import embark_station_context
from cmdrhelper.ui.recommendations_view import current_market, current_market_context

FID = 'F12520967'
NOW = datetime(2026, 9, 28, 5, 4, 26, tzinfo=timezone.utc)
STATION = dict(StarSystem='Arietis Sector HS-R a5-0', SystemAddress=5358508329680,
               StationName='Dreyer Platform', MarketID=4236567811, StationType='Outpost')
EMBARK = dict(event='Embark', timestamp='2026-09-28T05:02:42Z', ID=12,
              OnStation=True, OnPlanet=False, SRV=False, Taxi=False, Multicrew=False, **STATION)


class EmbarkStationTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        self.path = self.folder / 'Journal.2026-09-28T064911.01.log'
        self.cache = ObservedMarketCache(self.folder / 'cache.json', clock=lambda: NOW)

    def replay(self, tail, fid=FID):
        rows = [dict(event='Fileheader', timestamp='2026-09-28T04:49:06Z'),
                dict(event='Commander', timestamp='2026-09-28T04:49:42Z', FID=fid, Name='Fixture'),
                dict(event='LoadGame', timestamp='2026-09-28T04:49:42Z', FID=fid,
                     Ship='UtilitySuit_Class5', ShipID=4293000001),
                dict(event='Location', timestamp='2026-09-28T04:50:17Z', OnFoot=True,
                     Docked=False, Body='Dreyer Platform', BodyType='Station',
                     StarSystem=STATION['StarSystem'], SystemAddress=STATION['SystemAddress'])] + tail
        self.path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        d = read_latest_state(self.folder)
        observer = ObservedMarketObserver(cache=self.cache, clock=lambda: NOW)
        for row in rows:
            observer._event(row, False)
        state = SimpleNamespace(observed_markets=observer, commander_fid=d['commander_fid'],
                                station=d['station'], system=d['system'])
        return state, d

    def test_dreyer_start_on_foot_embark_without_docked_finds_388_saved_items(self):
        market = dict(event='Market', timestamp=NOW.isoformat(), **STATION)
        # Unique synthetic commodities; never copy live player market data into fixtures.
        sidecar = dict(market, Items=[dict(Name=f'fixture_commodity_{i}', BuyPrice=100,
                                         SellPrice=90, Stock=200, Demand=300) for i in range(388)])
        s, d = self.replay([EMBARK, market])
        context = current_market_context(s)
        self.assertIsNotNone(context)
        for key, value in STATION.items():
            self.assertEqual(context[key], value)
        self.assertEqual(d['market_id'], STATION['MarketID'])
        self.assertEqual(d['system_address'], STATION['SystemAddress'])
        self.assertEqual(d['last_position']['station_name'], STATION['StationName'])
        snapshot = normalize_observation(market, sidecar, fid=FID, context=context,
                                         mtime=NOW.timestamp(), now=NOW)
        self.assertTrue(self.cache.put(snapshot))
        self.assertEqual(current_market(s)['market_id'], STATION['MarketID'])
        self.assertEqual(len(self.cache.get(FID, current_market(s)['market_id'])['commodities']), 388)
        # Production uses committed SQLite headers for current_market(), not JSON prices.
        self.cache.install_headers({snapshot['market_id']: {
            k: v for k, v in snapshot.items() if k != 'commodities'}})
        self.assertEqual(current_market(s)['station_name'], 'Dreyer Platform')

    def test_invalid_embark_does_not_create_station_in_either_reader(self):
        mutations = [dict(OnStation=False, OnPlanet=True), dict(OnStation=1),
                     dict(Taxi=True), dict(Multicrew=True), dict(SRV=True), dict(Fighter=True),
                     dict(FID='F_OTHER'), dict(MarketID=0), dict(MarketID=True),
                     dict(MarketID='4236567811'), dict(StationName=''), dict(ID=True),
                     dict(SystemAddress=123), dict(StarSystem='Other system')]
        for key in ('MarketID', 'StationName', 'StarSystem', 'OnStation', 'SRV', 'Taxi', 'Multicrew', 'ID'):
            row = deepcopy(EMBARK)
            del row[key]
            mutations.append(row)
        for fields in mutations:
            row = fields if 'event' in fields else dict(EMBARK, **fields)
            with self.subTest(row=row):
                s, d = self.replay([row])
                self.assertEqual(d['station'], '')
                self.assertNotIn('MarketID', s.observed_markets.context)
                self.assertIsNone(current_market_context(s))

    def test_station_conflict_preserves_existing_context(self):
        docked = dict(EMBARK, event='Docked')
        for fields in (dict(MarketID=42), dict(StationName='Other station')):
            with self.subTest(fields=fields):
                s, d = self.replay([docked, dict(EMBARK, **fields)])
                self.assertEqual(d['station'], STATION['StationName'])
                self.assertEqual(d['market_id'], STATION['MarketID'])
                self.assertEqual(current_market_context(s)['MarketID'], STATION['MarketID'])

    def test_normal_docked_and_undocked_still_work(self):
        docked = dict(EMBARK, event='Docked')
        s, d = self.replay([docked])
        self.assertEqual(current_market_context(s)['MarketID'], STATION['MarketID'])
        s, d = self.replay([docked, dict(event='Undocked', timestamp=NOW.isoformat())])
        self.assertEqual(d['station'], '')
        self.assertIsNone(current_market_context(s))

    def test_untrusted_commander_never_establishes_embark_context(self):
        for context in ({}, {'FID': ''}, {'FID': 'bad fid'}, {'FID': 'F_OTHER'}):
            with self.subTest(context=context):
                self.assertIsNone(embark_station_context(dict(EMBARK, FID=FID), context))

    def test_optional_system_address_is_inherited_only_from_matching_system(self):
        row = dict(EMBARK)
        del row['SystemAddress']
        s, d = self.replay([row])
        self.assertEqual(d['system_address'], STATION['SystemAddress'])
        self.assertEqual(current_market_context(s)['SystemAddress'], STATION['SystemAddress'])
