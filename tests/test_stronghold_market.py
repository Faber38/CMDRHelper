"""Synthetic Stronghold markets; all journals, caches and databases are temporary."""
from copy import deepcopy
from datetime import timedelta
from types import SimpleNamespace
import unittest

import test_observed_market_cache as fixtures
from cmdrhelper.observed_market_cache import normalize_observation
from cmdrhelper.market_store import MarketStore
from cmdrhelper.ui.recommendations_view import current_market, current_market_context


class StrongholdMarketTests(unittest.TestCase):
    setUp = fixtures.ObserverTests.setUp
    append = fixtures.ObserverTests.append
    write_sidecar = fixtures.ObserverTests.write_sidecar
    consume = fixtures.ObserverTests.consume

    def trigger(self):
        return dict(fixtures.event(self.now), StationType='')

    def dock(self, station_type='SurfaceStation'):
        self.append(dict(self.trigger(), event='Docked', StationType=station_type,
                         SystemAddress=555))

    def market(self, **changes):
        data = dict(fixtures.sidecar(self.now), StationType='')
        data.update(changes)
        self.write_sidecar(data)
        self.append(self.trigger())

    def state(self):
        return SimpleNamespace(observed_markets=self.observer, commander_fid=fixtures.FID,
                               station='Fixture Port', system='Fixture System')

    def test_stronghold_sqlite_to_current_market_and_refresh(self):
        self.observer.use_market_store = True
        self.addCleanup(self.observer.close)
        self.dock()
        for price in (524, 700):
            self.market()
            data = dict(fixtures.sidecar(self.now), StationType='')
            data['Items'][0]['BuyPrice'] = price
            self.write_sidecar(data)
            self.assertFalse(self.consume())
            self.assertEqual(len(self.observer._writes), 1)
            self.observer._writes[0][1].result(timeout=10)
            self.assertTrue(self.consume())
            with MarketStore(self.cache.path.parent / 'markets.db', read_only=True,
                             clock=lambda: self.now) as store:
                row = store.get_current(123)
            self.assertEqual(row['station_type'], 'SurfaceStation')
            self.assertEqual(row['system_address'], 555)
            self.assertEqual(row['commodities'][0]['commander_buy_price'], price)
            self.assertEqual(current_market(self.state())['observed_at'], self.now.isoformat())
            self.now += timedelta(seconds=1)

    def test_docked_without_market_does_not_import_existing_sidecar(self):
        self.dock()
        self.assertTrue(self.consume())
        self.assertIsNotNone(current_market_context(self.state()))
        self.assertIsNone(current_market(self.state()))
        self.assertFalse(self.cache.path.exists())

    def test_empty_items_is_a_read_market_without_offers(self):
        self.dock()
        self.market(Items=[])
        self.assertTrue(self.consume())
        self.assertEqual(self.cache.get(fixtures.FID, 123)['commodities'], [])
        self.assertIsNotNone(current_market(self.state()))

    def test_missing_or_stale_sidecar_never_imported(self):
        self.dock()
        self.market()
        (self.root / 'Market.json').unlink()
        self.assertFalse(self.consume())
        self.write_sidecar(dict(fixtures.sidecar(self.now - timedelta(seconds=10)), StationType=''))
        self.assertFalse(self.consume())
        self.assertIsNone(current_market(self.state()))
        self.tick += 16
        self.assertTrue(self.consume())
        self.assertIsNone(self.observer.pending)
        self.assertFalse(self.cache.path.exists())

    def test_identity_and_type_conflicts_remain_rejected(self):
        trigger = self.trigger()
        context = dict(trigger, FID=fixtures.FID, StationType='SurfaceStation', SystemAddress=555)
        for field, wrong in (('MarketID', 456), ('StationName', 'Other'),
                             ('StarSystem', 'Elsewhere'), ('SystemAddress', 556),
                             ('FID', 'F_OTHER'), ('StationType', 'FleetCarrier')):
            for source in ('event', 'sidecar', 'context'):
                with self.subTest(field=field, source=source):
                    inputs = dict(event=dict(trigger, SystemAddress=555, FID=fixtures.FID),
                                  sidecar=dict(fixtures.sidecar(), StationType='',
                                               SystemAddress=555, FID=fixtures.FID),
                                  context=deepcopy(context))
                    if field == 'StationType':
                        inputs['event']['StationType'] = 'SurfaceStation'
                        inputs['sidecar']['StationType'] = 'SurfaceStation'
                    inputs[source][field] = wrong
                    with self.assertRaises(ValueError):
                        normalize_observation(**inputs, fid=fixtures.FID, now=self.now,
                                              mtime=self.now.timestamp())

    def test_departure_station_system_and_commander_changes_cancel_pending(self):
        for change in (dict(event='Undocked'), dict(event='FSDJump', StarSystem='Elsewhere'),
                       dict(event='Docked', MarketID=456, StationName='Other', StarSystem='Fixture System'),
                       dict(event='LoadGame', FID='F_OTHER')):
            with self.subTest(change=change):
                self.append(dict(event='LoadGame', FID=fixtures.FID))
                self.dock()
                self.market(MarketID=999)
                self.assertFalse(self.consume())
                self.append(change)
                self.write_sidecar(dict(fixtures.sidecar(self.now), StationType=''))
                self.assertTrue(self.consume())
                self.assertIsNone(self.observer.pending)
                self.assertIsNone(current_market(self.state()))
                self.assertFalse(self.cache.path.exists())
                self.now += timedelta(seconds=1)

    def test_undocked_and_commander_switch_hide_previously_read_market(self):
        self.dock()
        self.market()
        self.assertTrue(self.consume())
        state = self.state()
        self.assertIsNotNone(current_market(state))
        state.commander_fid = 'F_OTHER'
        self.assertIsNone(current_market(state))
        self.append(dict(event='Undocked'))
        self.consume()
        self.assertIsNone(current_market(self.state()))
        self.assertIsNotNone(self.cache.get(fixtures.FID, 123))

    def test_normal_station_and_fleet_carrier(self):
        for station_type in ('Coriolis', 'FleetCarrier'):
            with self.subTest(station_type=station_type):
                self.dock(station_type)
                self.append(dict(fixtures.event(self.now), StationType=station_type))
                self.write_sidecar(dict(fixtures.sidecar(self.now), StationType=station_type))
                self.assertTrue(self.consume())
                self.assertEqual(self.cache.get(fixtures.FID, 123)['station_type'], station_type)
                self.assertIsNotNone(current_market(self.state()))
                self.now += timedelta(seconds=1)

    def test_only_exact_empty_optional_type_is_ignored(self):
        for station_type in ('', None, 0, False, ' '):
            with self.subTest(station_type=station_type):
                args = dict(event=dict(self.trigger(), StationType=station_type),
                            sidecar=dict(fixtures.sidecar(), StationType=station_type),
                            fid=fixtures.FID, now=self.now, mtime=self.now.timestamp())
                if station_type == '':
                    self.assertNotIn('station_type', normalize_observation(**args))
                else:
                    with self.assertRaises(ValueError):
                        normalize_observation(**args)


class StrongholdMarketStatusTests(unittest.TestCase):
    def test_badge_only_acknowledges_supplied_market(self):
        import test_observed_market_status as ui_fixtures
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance() or QApplication([])
        harness = ui_fixtures.ObservedStatusTests()
        harness.app = app
        harness.setUp()
        self.addCleanup(harness.tearDown)
        harness.state.station = 'Fixture Port'
        journal = harness.root / 'Journal.2026-01-02T110000.01.log'
        journal.write_text('{"event":"LoadGame","FID":"F_SYNTHETIC_TEST"}\n')
        harness.observer.set_folder(harness.root)
        import json
        import os
        dock = dict(fixtures.event(), event='Docked', StationType='SurfaceStation')
        with journal.open('a') as stream:
            stream.write(json.dumps(dock) + '\n')
        harness.observer.consume([journal])
        harness.view.recommendations.refresh()
        self.assertEqual(harness.view.market_read_status.status, 'open')
        self.assertIsNone(harness.view.recommendations.origin)
        trigger = dict(fixtures.event(), StationType='')
        with journal.open('a') as stream:
            stream.write(json.dumps(trigger) + '\n')
        # A missing Market.json must not mark the market as read.
        self.assertFalse(harness.observer.consume([journal]))
        harness.view.recommendations.refresh()
        self.assertEqual(harness.view.market_read_status.status, 'open')
        market = harness.root / 'Market.json'
        market.write_text(json.dumps(dict(fixtures.sidecar(), StationType='')))
        os.utime(market, (fixtures.NOW.timestamp(), fixtures.NOW.timestamp()))
        self.assertTrue(harness.observer.consume([journal]))
        self.assertEqual(harness.view.market_read_status.status, 'read')
        self.assertEqual(harness.view.recommendations.origin['market_id'], 123)
