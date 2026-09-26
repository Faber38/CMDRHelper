"""Synthetic local market observations only; never use player files/settings."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cmdrhelper.commodity_master import lookup_by_symbol
from cmdrhelper import observed_market_cache as module
from cmdrhelper.observed_market_cache import ObservedMarketCache, normalize_observation, read_market
from cmdrhelper.observed_market_observer import ObservedMarketObserver

NOW = datetime(2026, 1, 2, 12, tzinfo=timezone.utc)
FID = 'F_SYNTHETIC_TEST'


def event(stamp=NOW, mid=123, station='Fixture Port', system='Fixture System'):
    return dict(timestamp=stamp.isoformat(), event='Market', MarketID=mid,
                StationName=station, StarSystem=system, StationType='Coriolis')


def sidecar(stamp=NOW, mid=123):
    beer, platinum = lookup_by_symbol('Beer'), lookup_by_symbol('Platinum')
    return dict(event(stamp, mid), Items=[
        dict(id=beer.frontier_id, Name='$beer_name;', Name_Localised='Bier',
             Category='$MARKET_category_legaldrugs;', BuyPrice=524, SellPrice=411, Stock=1500, Demand=0),
        dict(id=platinum.frontier_id, Name='$platinum_name;', BuyPrice=0, SellPrice=203385,
             Stock=0, Demand=11235),
    ])


def snapshot(stamp=NOW, mid=123, fid=FID):
    return normalize_observation(event(stamp, mid), sidecar(stamp, mid), fid=fid,
                                 mtime=stamp.timestamp(), now=stamp)


class CacheTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.path = self.root / 'market_cache' / 'observed_markets.json'
        self.now = NOW
        self.cache = ObservedMarketCache(self.path, clock=lambda: self.now)

    def test_new_market_persisted_immediately_and_restart(self):
        self.assertFalse(self.path.exists())
        self.assertTrue(self.cache.put(snapshot()))
        self.assertEqual(ObservedMarketCache(self.path, clock=lambda: NOW).get(FID, 123), snapshot())

    def test_replaces_entire_snapshot_no_history(self):
        self.cache.put(snapshot(NOW - timedelta(hours=3)))
        newer = snapshot()
        newer['commodities'] = newer['commodities'][:1]
        self.assertTrue(self.cache.put(newer))
        rows = json.loads(self.path.read_text())['markets']
        self.assertEqual(rows, [newer])
        size = self.path.stat().st_size
        self.cache.put(newer)
        self.assertEqual(self.path.stat().st_size, size)

    def test_second_market_added(self):
        self.cache.put(snapshot())
        self.cache.put(snapshot(mid=456))
        self.assertEqual(len(self.cache.all(FID)), 2)

    def test_older_snapshot_cannot_replace_newer(self):
        self.cache.put(snapshot())
        self.cache.put(snapshot(NOW - timedelta(seconds=1)))
        self.assertEqual(self.cache.get(FID, 123), snapshot())

    def test_conflicting_same_timestamp_rejected(self):
        self.cache.put(snapshot())
        conflict = snapshot()
        conflict['commodities'][0]['supply'] += 1
        self.assertFalse(self.cache.put(conflict))
        self.assertEqual(self.cache.get(FID, 123), snapshot())

    def test_235959_remains(self):
        self.cache.put(snapshot())
        self.now += timedelta(hours=24, seconds=-1)
        self.assertIsNotNone(self.cache.get(FID, 123))

    def test_exact_24h_retained_and_included(self):
        self.cache.put(snapshot())
        self.now += timedelta(hours=24)
        self.assertEqual(len(self.cache.all(FID)), 1)
        self.assertEqual(len(json.loads(self.path.read_text())['markets']), 1)

    def test_over_24h_retained_on_load(self):
        self.cache.put(snapshot())
        before = self.path.read_bytes()
        fresh = ObservedMarketCache(self.path, clock=lambda: NOW + timedelta(days=2))
        self.assertEqual(fresh.all(FID), [])
        self.assertEqual(len(fresh.all(FID, max_age=None)), 1)
        self.assertEqual(self.path.read_bytes(), before)

    def test_old_snapshots_retained_on_write(self):
        self.cache.put(snapshot())
        self.now += timedelta(days=2)
        self.cache.put(snapshot(self.now, mid=456))
        self.assertEqual([x['market_id'] for x in json.loads(self.path.read_text())['markets']], [123, 456])

    def test_old_write_retained_but_future_rejected(self):
        self.assertFalse(self.cache.put(snapshot(NOW + timedelta(seconds=1))))
        self.assertFalse(self.path.exists())
        self.assertTrue(self.cache.put(snapshot(NOW - timedelta(days=30))))
        self.assertEqual(len(self.cache.all(FID, max_age=None)), 1)

    def test_atomic_same_directory_fsync_replace(self):
        replace = os.replace
        with patch.object(module.os, 'replace', wraps=replace) as move, patch.object(module.os, 'fsync', wraps=os.fsync) as sync:
            self.assertTrue(self.cache.put(snapshot()))
        self.assertEqual(Path(move.call_args.args[0]).parent, self.path.parent)
        self.assertEqual(move.call_args.args[1], self.path)
        sync.assert_called_once()
        self.assertEqual(list(self.path.parent.glob('*.tmp')), [])

    def test_failed_replace_preserves_old_file_and_memory(self):
        self.cache.put(snapshot())
        before = self.path.read_bytes()
        with patch.object(module.os, 'replace', side_effect=OSError('synthetic failure')):
            self.assertFalse(self.cache.put(snapshot(mid=456)))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertIsNone(self.cache.get(FID, 456))
        self.assertEqual(list(self.path.parent.glob('*.tmp')), [])

    def test_failed_fsync_preserves_old_file(self):
        self.cache.put(snapshot())
        before = self.path.read_bytes()
        with patch.object(module.os, 'fsync', side_effect=OSError('synthetic failure')):
            self.assertFalse(self.cache.put(snapshot(mid=456)))
        self.assertEqual(self.path.read_bytes(), before)

    def test_age_filter_and_cleanup_do_not_write(self):
        self.cache.put(snapshot())
        before = self.path.read_bytes()
        self.now += timedelta(days=2)
        with patch.object(module.os, 'replace', side_effect=AssertionError('No write')):
            self.assertEqual(self.cache.all(FID), [])
            self.assertTrue(self.cache.cleanup())
        self.assertEqual(self.path.read_bytes(), before)

    def test_corrupt_json_duplicate_keys_version_types_recover(self):
        self.path.parent.mkdir()
        for raw in ('{', '{"version":1,"version":1,"markets":[]}',
                    '{"version":2,"markets":[]}', '{"version":true,"markets":[]}',
                    '{"version":1,"markets":{}}', '{"version":1,"markets":[null]}',
                    '{"version":1,"markets":[{"bad":true}]}'):
            with self.subTest(raw=raw):
                self.path.write_text(raw)
                cache = ObservedMarketCache(self.path, clock=lambda: NOW)
                self.assertEqual(cache.all(FID), [])
                self.assertIsNotNone(cache.last_error)
                self.assertTrue(cache.put(snapshot()))
                self.assertEqual(cache.get(FID, 123), snapshot())

    def test_partial_commodity_corruption_rejects_whole_cache(self):
        self.cache.put(snapshot())
        data = json.loads(self.path.read_text())
        data['markets'][0]['commodities'][1]['commander_sell_price'] = '203385'
        self.path.write_text(json.dumps(data))
        self.assertEqual(ObservedMarketCache(self.path, clock=lambda: NOW).all(FID), [])

    def test_required_fields_and_types(self):
        for key in ('market_id', 'station_name', 'system_name', 'observed_at', 'fid', 'source', 'commodities'):
            row = snapshot()
            del row[key]
            self.assertFalse(self.cache.put(row), key)
        for value in (-1, True, 0.5, None, '524'):
            row = snapshot()
            row['commodities'][0]['commander_buy_price'] = value
            self.assertFalse(self.cache.put(row))

    def test_read_and_write_size_limits(self):
        self.cache.put(snapshot())
        before = self.path.read_bytes()
        with patch.object(module, 'MAX_FILE_BYTES', 10):
            self.assertEqual(ObservedMarketCache(self.path, clock=lambda: NOW).all(FID), [])
            self.assertFalse(self.cache.put(snapshot(mid=456)))
        self.assertEqual(self.path.read_bytes(), before)

    def test_market_and_commodity_limits(self):
        row = snapshot()
        self.cache.put(row)
        with patch.object(module, 'MAX_MARKETS', 1):
            self.assertFalse(self.cache.put(snapshot(mid=456)))
        with patch.object(module, 'MAX_COMMODITIES', 1):
            self.assertFalse(self.cache.put(row))
        self.assertEqual(self.cache.all(FID), [snapshot()])

    def test_fid_partition_same_market_id_and_invalid_fid(self):
        self.cache.put(snapshot())
        other = snapshot(fid='F_OTHER_SYNTHETIC')
        other['commodities'][0]['supply'] = 12
        self.cache.put(other)
        self.assertEqual(self.cache.get(FID, 123), snapshot())
        self.assertEqual(self.cache.get('F_OTHER_SYNTHETIC', 123), other)
        self.assertEqual(self.cache.all('../bad'), [])
        self.assertFalse(self.cache.put(dict(snapshot(), fid='../bad')))

    def test_api_copies_find_age_validity(self):
        self.cache.put(snapshot())
        row = self.cache.find(FID, 'fixture system', 'FIXTURE PORT')[0]
        row['commodities'].clear()
        self.assertEqual(self.cache.get(FID, 123), snapshot())
        self.assertEqual(self.cache.age(snapshot(), NOW + timedelta(minutes=5)), timedelta(minutes=5))
        self.assertTrue(self.cache.is_valid(snapshot(), NOW))
        self.assertTrue(self.cache.is_valid(snapshot(), NOW + timedelta(hours=24)))

    def test_spansh_source_rejected_no_persistence(self):
        self.assertFalse(self.cache.put(dict(snapshot(), source='spansh')))
        self.assertFalse(self.path.exists())


class NormalizationTests(unittest.TestCase):
    def normalize(self, data=None, trigger=None, **kwargs):
        return normalize_observation(trigger or event(), sidecar() if data is None else data,
                                     fid=FID, now=NOW, mtime=kwargs.pop('mtime', NOW.timestamp()), **kwargs)

    def test_price_direction_supply_demand_and_master(self):
        rows = self.normalize()['commodities']
        self.assertEqual((rows[0]['commander_buy_price'], rows[0]['commander_sell_price']), (524, 411))
        self.assertEqual((rows[0]['supply'], rows[0]['demand']), (1500, 0))
        self.assertEqual((rows[1]['supply'], rows[1]['demand']), (0, 11235))
        beer = lookup_by_symbol('Beer')
        self.assertEqual((rows[0]['commodity_id'], rows[0]['symbol']), (beer.frontier_id, beer.symbol))
        self.assertEqual(rows[0]['localized_name'], 'Bier')
        self.assertEqual(self.normalize()['source'], 'local_elite')

    def test_wrong_market_id(self):
        with self.assertRaises(ValueError): self.normalize(dict(sidecar(), MarketID=456))

    def test_wrong_station(self):
        with self.assertRaises(ValueError): self.normalize(dict(sidecar(), StationName='Other Port'))

    def test_wrong_system(self):
        with self.assertRaises(ValueError): self.normalize(dict(sidecar(), StarSystem='Other System'))

    def test_old_sidecar_timestamp(self):
        with self.assertRaises(ValueError): self.normalize(sidecar(NOW - timedelta(minutes=1)))

    def test_file_time_is_guard_not_observation_time(self):
        self.assertEqual(self.normalize(mtime=NOW.timestamp() + 1)['observed_at'], NOW.isoformat())
        for mtime in (NOW.timestamp() - 3, NOW.timestamp() + 3):
            with self.assertRaises(ValueError): self.normalize(mtime=mtime)

    def test_missing_identity_and_wrong_fid(self):
        for key in ('MarketID', 'StationName', 'StarSystem', 'timestamp', 'Items'):
            data = sidecar(); del data[key]
            with self.assertRaises(ValueError): self.normalize(data)
        with self.assertRaises(ValueError): self.normalize(dict(sidecar(), FID='F_OTHER_SYNTHETIC'))

    def test_context_mismatch(self):
        for context in ({'MarketID':456}, {'StationName':'Other'}, {'StarSystem':'Other'}, {'FID':'F_OTHER'}):
            with self.assertRaises(ValueError): self.normalize(context=context)
        self.assertEqual(self.normalize(context={'SystemAddress':555})['system_address'], 555)
        with self.assertRaises(ValueError): self.normalize(dict(sidecar(), SystemAddress=111), context={'SystemAddress':555})

    def test_unknown_commodity_retained(self):
        data = sidecar()
        data['Items'][0].update(id=199999999, Name='$future_fixture_name;', Name_Localised='Future Fixture')
        row = self.normalize(data)['commodities'][0]
        self.assertEqual((row['commodity_id'],row['symbol']), (199999999, '$future_fixture_name;'))

    def test_symbol_only_known_and_unknown_supported(self):
        data = sidecar()
        del data['Items'][0]['id']
        self.assertEqual(self.normalize(data)['commodities'][0]['commodity_id'], lookup_by_symbol('Beer').frontier_id)
        data['Items'][0]['Name'] = '$future_fixture_name;'
        self.assertIsNone(self.normalize(data)['commodities'][0]['commodity_id'])

    def test_identity_conflicts_and_duplicates_rejected(self):
        data = sidecar()
        data['Items'][0]['id'] = lookup_by_symbol('Gold').frontier_id
        with self.assertRaises(ValueError): self.normalize(data)
        data = sidecar(); data['Items'].append(deepcopy(data['Items'][0]))
        with self.assertRaises(ValueError): self.normalize(data)

    def test_naive_timestamp_and_invalid_prices_rejected(self):
        with self.assertRaises(ValueError): self.normalize(dict(sidecar(), timestamp='2026-01-02T12:00:00'))
        for price in (float('nan'), -1, True, '524'):
            data = sidecar(); data['Items'][0]['BuyPrice'] = price
            with self.assertRaises(ValueError): self.normalize(data)

    def test_offset_timestamp_normalized_utc(self):
        data = sidecar(); data['timestamp'] = '2026-01-02T13:00:00+01:00'
        self.assertEqual(self.normalize(data)['observed_at'], NOW.isoformat())


class ObserverTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.path = self.root / 'Journal.2026-01-02T110000.01.log'
        self.path.write_text(json.dumps(dict(event='LoadGame', FID=FID))+'\n')
        self.now = NOW
        self.tick = 100
        self.cache = ObservedMarketCache(self.root/'cache'/'observed_markets.json', clock=lambda:self.now)
        self.observer = ObservedMarketObserver(self.cache, clock=lambda:self.now, monotonic=lambda:self.tick)
        self.observer.set_folder(self.root)
        self.write_sidecar()

    def append(self, row, path=None):
        with (path or self.path).open('a') as stream:
            stream.write(json.dumps(row)+'\n')

    def write_sidecar(self, data=None):
        path = self.root/'Market.json'
        path.write_text(json.dumps(sidecar(self.now) if data is None else data))
        os.utime(path, (self.now.timestamp(), self.now.timestamp()))

    def consume(self):
        return self.observer.consume([self.path])

    def test_valid_live_event_saved(self):
        self.append(event())
        self.assertTrue(self.consume())
        self.assertEqual(self.cache.get(FID,123), snapshot())

    def test_startup_and_restart_never_backfill_existing_market(self):
        self.append(event())
        self.observer.set_folder(self.root)
        self.assertTrue(self.consume())
        self.assertFalse(self.cache.path.exists())
        self.append(event(NOW + timedelta(seconds=1)))
        self.now += timedelta(seconds=1); self.write_sidecar()
        self.assertTrue(self.consume())
        self.assertEqual(len(self.cache.all(FID)),1)
        restarted = ObservedMarketObserver(self.cache, clock=lambda:self.now)
        restarted.set_folder(self.root); restarted.consume([self.path])
        self.assertEqual(len(self.cache.all(FID)),1)

    def test_delayed_partial_sidecar_retried_without_journal_growth(self):
        self.append(event())
        (self.root/'Market.json').write_text('{')
        self.assertFalse(self.consume())
        self.assertFalse(self.cache.path.exists())
        self.write_sidecar()
        self.assertTrue(self.consume())
        self.assertIsNotNone(self.cache.get(FID,123))

    def test_mismatch_retains_previous_and_bounded_retry(self):
        self.cache.put(snapshot(NOW - timedelta(minutes=1)))
        self.append(event())
        self.write_sidecar(dict(sidecar(), MarketID=999))
        self.assertFalse(self.consume())
        self.tick += 16
        self.assertTrue(self.consume())
        self.assertIsNotNone(self.observer.last_error)
        self.assertEqual(self.cache.get(FID,123), snapshot(NOW-timedelta(minutes=1)))

    def test_write_failure_retries_without_duplicate_event(self):
        self.append(event())
        with patch.object(module.os,'replace',side_effect=OSError('synthetic failure')):
            self.assertFalse(self.consume())
        self.assertTrue(self.consume())
        self.assertIsNotNone(self.cache.get(FID,123))

    def test_no_fid_no_capture(self):
        self.path.write_text('{}\n'); self.observer.set_folder(self.root)
        self.append(event())
        self.assertTrue(self.consume())
        self.assertFalse(self.cache.path.exists())

    def test_fid_change_cancels_pending(self):
        self.append(event())
        self.write_sidecar(dict(sidecar(), MarketID=999))
        self.assertFalse(self.consume())
        self.append(dict(event='LoadGame',FID='F_OTHER_SYNTHETIC'))
        self.write_sidecar()
        self.assertTrue(self.consume())
        self.assertFalse(self.cache.path.exists())

    def test_station_change_cancels_pending(self):
        self.append(event())
        self.write_sidecar(dict(sidecar(), MarketID=999))
        self.assertFalse(self.consume())
        self.append(dict(event='Docked',MarketID=456,StationName='Other',StarSystem='Other'))
        self.write_sidecar()
        self.assertTrue(self.consume())
        self.assertFalse(self.cache.path.exists())

    def test_new_session_rotation_requires_own_fid(self):
        self.consume()
        new = self.root/'Journal.2026-01-02T120000.01.log'
        new.write_text(json.dumps(event())+'\n')
        self.assertTrue(self.observer.consume([self.path,new]))
        self.assertFalse(self.cache.path.exists())
        self.append(dict(event='LoadGame', FID='F_OTHER_SYNTHETIC'),new)
        self.now += timedelta(seconds=1)
        self.append(event(self.now),new); self.write_sidecar()
        self.assertTrue(self.observer.consume([new]))
        self.assertIsNone(self.cache.get(FID,123))
        self.assertIsNotNone(self.cache.get('F_OTHER_SYNTHETIC',123))

    def test_consecutive_part_rotation_inherits_same_session_fid(self):
        self.consume()
        new = self.root/'Journal.2026-01-02T110000.02.log'
        new.write_text(json.dumps(dict(event='Fileheader',part=2))+'\n'+json.dumps(event())+'\n')
        self.assertTrue(self.observer.consume([new]))
        self.assertIsNotNone(self.cache.get(FID,123))

    def test_truncation_does_not_replay(self):
        self.consume()
        self.path.write_text('{}\n')
        self.consume()
        self.append(dict(event='LoadGame',FID=FID)); self.append(event())
        self.consume()
        self.assertFalse(self.cache.path.exists())

    def test_old_appended_event_not_replayed(self):
        old=NOW-timedelta(minutes=1)
        self.append(event(old)); self.write_sidecar(sidecar(old))
        self.consume()
        self.assertFalse(self.cache.path.exists())

    def test_partial_journal_line_waits(self):
        raw=json.dumps(event())
        with self.path.open('a') as stream: stream.write(raw[:40])
        self.consume()
        self.assertFalse(self.cache.path.exists())
        with self.path.open('a') as stream: stream.write(raw[40:]+'\n')
        self.consume()
        self.assertIsNotNone(self.cache.get(FID,123))

    def test_sidecar_read_bound_and_unstable_signature(self):
        with patch.object(module,'MAX_SIDECAR_BYTES',1):
            with self.assertRaises(ValueError): read_market(self.root/'Market.json')
        sig=module.signature(self.root/'Market.json')
        with patch.object(module,'signature',side_effect=[sig,(*sig[:2],sig[2]+1,*sig[3:])]):
            with self.assertRaises(OSError): read_market(self.root/'Market.json')

    def test_duplicate_market_timestamp_ambiguous(self):
        self.append(event()); self.append(event())
        self.consume()
        self.assertFalse(self.cache.path.exists())

    def test_existing_watcher_retries_sidecar_without_new_timer(self):
        from PySide6.QtWidgets import QApplication
        from cmdrhelper.journal_watcher import JournalWatcher
        app=QApplication.instance() or QApplication([])
        watcher=JournalWatcher()
        watcher.live_observers=[self.observer]
        watcher.set_folder(self.root)
        watcher.journalChanged.connect(lambda:watcher.refresh_finished(True))
        self.append(event()); (self.root/'Market.json').write_text('{')
        watcher.check_now()
        self.assertTrue(watcher._live_pending)
        self.write_sidecar(); watcher.check_now()
        self.assertFalse(watcher._live_pending)
        self.assertIsNotNone(self.cache.get(FID,123))
        watcher.timer.stop()
        self.assertIsNotNone(app)
