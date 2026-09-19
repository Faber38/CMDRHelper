"""Isolated live encounters; no user DB or original journal is opened."""
import json
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.journal_reader import (
    _receive_text_offer, _matching_pending_offer, _pending_offer_matches,
    read_journal_delta, _live_complete_events,
)
from cmdrhelper.mission_manager import pending_missions, normalize_missions, confirmed_mission_reward
from cmdrhelper.i18n import set_language, tr, _TRANSLATIONS
from cmdrhelper.commodities import commodity_name


def event(kind, **values):
    return {'timestamp': '2026-09-18T14:41:00Z', 'event': kind, **values}


def offer_event(**values):
    # Technical fixture of the actual 2026-09-18 14:40:36 UTC offer.
    return event('ReceiveText', timestamp='2026-09-18T14:40:36Z', Channel='npc',
                 Message='$Mission_Collect_Industrial_MessengerChat1:'
                 '#CommodityName=$DiagnosticSensor_Name;:#CommodityQuantity=18:'
                 '#destinationStationName=Pordenone Vista:'
                 '#destinationStationSystemName=Preae Aihm EH-D d12-64:'
                 '#reward=927436.000000;', **values)


def mission(**values):
    return dict({'MissionID': 123456, 'Name': 'Mission_Collect_Industrial',
                 'Commodity': 'DiagnosticSensor', 'Count': 18,
                 'DestinationStation': 'Pordenone Vista',
                 'DestinationSystem': 'Preae Aihm EH-D d12-64'}, **values)


class EncounterTests(unittest.TestCase):
    def setUp(self):
        clock = patch('cmdrhelper.database.datetime', wraps=datetime)
        self.clock = clock.start()
        self.addCleanup(clock.stop)
        self.clock.now.return_value = datetime(2026, 9, 18, 14, 41, tzinfo=timezone.utc)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.db = CMDRDatabase(self.folder / 'state.db')
        self.a = self.db.upsert_commander('FID-A', 'Same name')
        self.b = self.db.upsert_commander('FID-B', 'Same name')
        self.path = self.folder / 'Journal.2026-09-18T140000.01.log'
        self.path.write_text(json.dumps(event('LoadGame', FID='FID-A', Commander='Same name'))+'\n')
        self.apply()
        set_language('de')
        self.addCleanup(set_language, 'de')

    def append(self, *events, live=True):
        with self.path.open('a') as f:
            for e in events:
                f.write(json.dumps(e, ensure_ascii=False)+'\n')
        return self.apply(live=live)

    def apply(self, live=True):
        session = scan_journal_folder(self.db, self.folder)[0]
        events, offset = read_journal_delta(self.path, session['last_read_offset'], include_positions=True)
        self.db.apply_commander_journal_delta(self.a, self.path, events, offset, live_current=live)
        return events, offset

    def visible(self, commander=None):
        from cmdrhelper.state import AppState
        return AppState._visible_commander_missions(SimpleNamespace(
            database=self.db, commander_id=commander or self.a))

    def test_real_offer_visible_without_invented_fields(self):
        self.append(offer_event())
        rows = self.visible()
        self.assertEqual(len(rows), 1)
        m = rows[0]
        self.assertIsNone(m.mission_id)
        self.assertEqual(m.name, '18 × Hardware-Diagnostiksensor beschaffen')
        self.assertEqual(m.destination_station, 'Pordenone Vista')
        self.assertEqual(m.destination_system, 'Preae Aihm EH-D d12-64')
        self.assertEqual(m.reward, 927436)
        self.assertEqual(m.status, 'Encounter-Auftrag')
        self.assertEqual((m.expiry, m.progress_text, m.accepted_at), ('', '', ''))
        self.assertEqual(confirmed_mission_reward(rows), 0)
        self.assertEqual(self.db.commander_missions(self.a), [])

    def test_restart_and_fid_switch_without_journal_reads(self):
        self.append(offer_event())
        self.db = CMDRDatabase(self.folder / 'state.db')
        with patch.object(Path, 'open', side_effect=AssertionError('No journals')):
            self.assertEqual(len(self.visible()), 1)
            self.assertEqual(self.visible(self.b), [])
            self.assertEqual(len(self.visible(self.a)), 1)
        with self.db._connect() as con:
            payload = json.loads(con.execute("SELECT value FROM app_meta WHERE key='pending_mission_offers/FID-A'").fetchone()[0])
        self.assertEqual((payload['schema'], payload['fid']), (1, 'FID-A'))

    def test_exact_position_and_duplicate_refresh(self):
        start = self.path.stat().st_size
        self.append(offer_event())
        source = self.db.pending_mission_offers(self.a)[0]['source']
        self.assertEqual(source['offset'], start)
        self.assertEqual(source['journal_file'], str(self.path))
        self.apply()
        self.apply()
        self.assertEqual(len(self.visible()), 1)

    def test_cached_positions_match_uncached_unicode(self):
        self.append(offer_event(From_Localised='Händler'))
        uncached, offset = read_journal_delta(self.path, 0, include_positions=True)
        _live_complete_events(self.path)
        cached, cached_offset = read_journal_delta(self.path, 0, include_positions=True)
        self.assertEqual((cached, cached_offset), (uncached, offset))

    def test_no_historical_offer_import(self):
        self.append(offer_event(), live=False)
        self.assertEqual(self.visible(), [])

    def test_snapshot_promotes_once_and_preserves_authoritative_fields(self):
        self.append(offer_event())
        self.append(event('Missions', Active=[mission(LocalisedName='Authoritative title',
                         Expiry='2026-09-19T14:00:00Z', Reward=927436)]))
        self.assertEqual(self.db.pending_mission_offers(self.a), [])
        rows = self.visible()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].mission_id, 123456)
        self.assertEqual(rows[0].name, 'Authoritative title')
        self.assertEqual(rows[0].reward, 927436)
        self.assertEqual(confirmed_mission_reward(rows), 927436)
        self.apply()
        self.assertEqual(len(self.visible()), 1)

    def test_cargo_depot_promotes_and_progresses(self):
        self.append(offer_event())
        for delivered in (0, 5, 18):
            self.append(event('CargoDepot', MissionID=123456, CargoType='diagnosticsensor',
                              TotalItemsToDeliver=18, ItemsDelivered=delivered, UpdateType='Deliver'))
            self.assertEqual(self.db.pending_mission_offers(self.a), [])
            rows = self.visible()
            self.assertEqual(len(rows), 1)
            self.assertIn(f'{delivered}/18', rows[0].progress_text)
            self.assertEqual(rows[0].reward, 927436)

    def test_accepted_can_also_confirm_offer(self):
        self.append(offer_event(), event('MissionAccepted', **mission()))
        self.assertEqual(len(self.visible()), 1)
        self.assertEqual(self.db.pending_mission_offers(self.a), [])

    def test_atomic_promotion_failure_rolls_back_mission_pending_and_cursor(self):
        self.append(offer_event())
        before = self.db.pending_mission_offers(self.a)
        old_offset = scan_journal_folder(self.db, self.folder)[0]['last_read_offset']
        with self.db._connect() as con:
            con.execute("CREATE TRIGGER fail_offer_write BEFORE UPDATE ON app_meta BEGIN SELECT RAISE(ABORT, 'test failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.append(event('Missions', Active=[mission()]))
        self.assertEqual(self.db.commander_missions(self.a), [])
        self.assertEqual(self.db.pending_mission_offers(self.a), before)
        self.assertEqual(scan_journal_folder(self.db, self.folder)[0]['last_read_offset'], old_offset)
        with self.db._connect() as con:
            con.execute('DROP TRIGGER fail_offer_write')
        self.apply()
        self.assertEqual(len(self.visible()), 1)
        self.assertEqual(self.db.pending_mission_offers(self.a), [])

    def test_match_fields_and_ambiguities(self):
        a = _receive_text_offer(offer_event())
        ts = '2026-09-18T15:00:00Z'
        cases = [
            ([a], mission(), a),
            ([a, dict(a, commodity='Gold')], mission(), a),
            ([a, dict(a, count=19)], mission(), a),
            ([a, dict(a, destination_station='Elsewhere')], mission(), a),
            ([a, dict(a)], mission(), None),
            ([a], mission(Commodity='Gold'), None),
            ([a], {'Name': 'Mission_Collect_Industrial'}, None),
            ([a], mission(Reward=1), None),
            ([a], mission(DestinationSystem='Other'), None),
            ([a], mission(Name='Mission_Delivery'), None),
        ]
        for offers, item, expected in cases:
            with self.subTest(item=item, offers=offers):
                self.assertIs(_matching_pending_offer(offers, item, ts), expected)
        self.assertEqual(_pending_offer_matches([a], [mission(), mission(MissionID=2)], ts), [None, None])

    def test_two_distinct_offers_promote_correct_one(self):
        a = offer_event()
        b = dict(a, Message=a['Message'].replace('DiagnosticSensor', 'Gold'))
        self.append(a, b)
        self.assertEqual(len(self.visible()), 2)
        self.append(event('Missions', Active=[mission()]))
        self.assertEqual(len(self.visible()), 2)
        self.assertEqual(self.db.pending_mission_offers(self.a)[0]['commodity'], 'Gold')

    def test_snapshot_timestamp_does_not_replace_wall_clock_or_delete_pending(self):
        self.append(offer_event())
        self.append(event('Missions', timestamp='2026-09-21T14:00:00Z', Active=[]))
        self.assertEqual(len(self.visible()), 1)
        self.assertIsNone(_matching_pending_offer(self.db.pending_mission_offers(self.a),
                          mission(), '2026-09-21T14:00:00Z'))

    def test_confirmed_encounter_terminal_removes_mission_not_other_pending(self):
        for terminal in ('MissionCompleted', 'MissionFailed', 'MissionAbandoned'):
            with self.subTest(terminal=terminal):
                self.append(offer_event(), event('MissionAccepted', **mission()))
                self.assertEqual(self.db.pending_mission_offers(self.a), [])
                self.assertTrue(self.db.commander_missions(self.a)[0]['is_open'])
                self.append(event(terminal, MissionID=123456))
                self.assertEqual(self.db.commander_missions(self.a), [])
                self.assertEqual(self.db.pending_mission_offers(self.a), [])
                self.assertEqual(self.visible(), [])

    def test_normal_lifecycle_and_schema_unchanged(self):
        with self.db._connect() as con:
            schema = con.execute("SELECT name,sql FROM sqlite_master WHERE type='table'").fetchall()
            version = con.execute('PRAGMA user_version').fetchone()
        self.append(offer_event())
        for index, terminal in enumerate(('MissionCompleted', 'MissionFailed', 'MissionAbandoned')):
            mid = 100 + index
            self.append(event('MissionAccepted', MissionID=mid, Name='Mission_Delivery', Reward=50))
            self.append(event('MissionRedirected', MissionID=mid, NewDestinationSystem='Next'))
            self.append(event(terminal, MissionID=mid))
            self.assertNotIn(mid, [m['mission_id'] for m in self.db.commander_missions(self.a)])
        self.assertEqual(len(self.visible()), 1)
        with self.db._connect() as con:
            self.assertEqual(con.execute("SELECT name,sql FROM sqlite_master WHERE type='table'").fetchall(), schema)
            self.assertEqual(con.execute('PRAGMA user_version').fetchone(), version)

    def test_sparse_snapshot_preserves_confirmed_offer_details(self):
        self.append(offer_event(), event('Missions', Active=[mission()]))
        before = self.visible()[0]
        self.append(event('Missions', Active=[{'MissionID': 123456, 'Name': 'Mission_Collect_Industrial'}]))
        after = self.visible()[0]
        self.assertEqual((after.name, after.summary, after.reward, after.destination_station),
                         (before.name, before.summary, before.reward, before.destination_station))

    def test_snapshot_one_offer_two_ids_never_guesses(self):
        self.append(offer_event(), event('Missions', Active=[mission(), mission(MissionID=2)]))
        self.assertEqual(len(self.db.pending_mission_offers(self.a)), 1)
        self.assertTrue(all(m['reward'] == 0 for m in self.db.commander_missions(self.a)))

    def test_existing_older_mission_cannot_consume_new_offer(self):
        self.append(event('MissionAccepted', timestamp='2026-09-18T14:00:00Z', **mission()))
        self.append(offer_event(), event('Missions', Active=[mission()]))
        self.assertEqual(len(self.db.pending_mission_offers(self.a)), 1)

    def test_ambiguous_snapshot_edges_and_missing_fields(self):
        a = _receive_text_offer(offer_event())
        b = dict(a, count=19)
        broad = mission()
        del broad['Count']
        self.assertEqual(_pending_offer_matches([a, b], [mission(), broad],
                                                '2026-09-18T15:00:00Z'), [None, None])
        for item in (mission(Count=0), mission(Reward=0),
                     mission(Name='Mission_Collect_Other')):
            self.assertIsNone(_matching_pending_offer([a], item, '2026-09-18T15:00:00Z'))

    def test_sparse_then_detailed_snapshot_can_confirm(self):
        self.append(offer_event(), event('Missions', Active=[{
            'MissionID': 123456, 'Name': 'Mission_Collect_Industrial'}]))
        self.assertEqual(len(self.db.pending_mission_offers(self.a)), 1)
        self.append(event('Missions', Active=[mission()]))
        self.assertEqual(self.db.pending_mission_offers(self.a), [])
        self.assertEqual(len(self.visible()), 1)
        self.assertEqual(self.visible()[0].reward, 927436)

    def test_two_commanders_keep_independent_persisted_offers(self):
        self.append(offer_event())
        offers = self.db.pending_mission_offers(self.a)
        other = dict(offers[0], commodity='Gold', count=7)
        with self.db._connect() as con:
            self.db._store_pending_mission_offers(con, self.b, [other])
        self.assertEqual(self.visible(self.b)[0].count, 7)
        self.assertEqual(self.visible(self.a)[0].count, 18)
        self.append(event('Missions', Active=[mission()]))
        self.assertEqual(len(self.visible(self.a)), 1)
        self.assertEqual(self.visible(self.b)[0].count, 7)
        self.assertIsNone(self.visible(self.b)[0].mission_id)

    def seed_pending(self, offers, commander=None):
        with self.db._connect() as con:
            self.db._store_pending_mission_offers(con, commander or self.a, offers)

    def stored_pending(self, fid='FID-A'):
        with self.db._connect() as con:
            row = con.execute("SELECT value FROM app_meta WHERE key=?",
                              ('pending_mission_offers/' + fid,)).fetchone()
        return json.loads(row[0])['offers'] if row else []

    def test_ttl_boundaries(self):
        created = datetime(2026, 9, 18, 14, 40, 36, tzinfo=timezone.utc)
        for age, expected in ((timedelta(hours=23, minutes=59), 1),
                              (timedelta(hours=24), 0),
                              (timedelta(hours=24, minutes=1), 0)):
            with self.subTest(age=age):
                self.seed_pending([_receive_text_offer(offer_event())])
                self.clock.now.return_value = created + age
                self.assertEqual(len(self.db.pending_mission_offers(self.a)), expected)
                self.assertEqual(len(self.stored_pending()), expected)

    def test_ttl_each_offer_has_its_own_timestamp(self):
        a = dict(_receive_text_offer(offer_event()), timestamp='2026-09-18T10:00:00Z')
        b = dict(a, timestamp='2026-09-18T15:00:00Z', commodity='Gold')
        self.seed_pending([a, b])
        self.clock.now.return_value = datetime(2026, 9, 19, 11, tzinfo=timezone.utc)
        self.assertEqual(self.db.pending_mission_offers(self.a), [b])
        self.assertEqual(self.stored_pending(), [b])

    def test_ttl_invalid_timestamps_are_retained_and_logged(self):
        for value in (None, '', 'invalid', 42, '2026-09-17',
                      '2026-09-17T12:00:00', '0001-01-01T00:00:00+01:00'):
            with self.subTest(timestamp=value):
                offer = dict(_receive_text_offer(offer_event()), timestamp=value)
                self.seed_pending([offer])
                with self.assertLogs('cmdrhelper.database', level='WARNING'):
                    self.assertEqual(self.db.pending_mission_offers(self.a), [offer])
                self.assertEqual(self.stored_pending(), [offer])
        offer.pop('timestamp')
        self.seed_pending([offer])
        with self.assertLogs('cmdrhelper.database', level='WARNING'):
            self.assertEqual(self.db.pending_mission_offers(self.a), [offer])

    def test_ttl_uses_utc_duration_and_keeps_future_timestamp(self):
        # Offsets straddle a summer/winter time change; only elapsed UTC counts.
        offer = dict(_receive_text_offer(offer_event()), timestamp='2026-10-24T12:00:00+02:00')
        self.seed_pending([offer])
        self.clock.now.return_value = datetime(2026, 10, 25, 9, 59, tzinfo=timezone.utc)
        self.assertEqual(len(self.db.pending_mission_offers(self.a)), 1)
        self.clock.now.return_value += timedelta(minutes=1)
        self.assertEqual(self.db.pending_mission_offers(self.a), [])
        future = dict(offer, timestamp='2026-10-26T12:00:00Z')
        self.seed_pending([future])
        self.assertEqual(self.db.pending_mission_offers(self.a), [future])

    def test_ttl_does_not_touch_confirmed_mission_in_any_promotion_path(self):
        confirmations = (event('MissionAccepted', **mission()),
                         event('Missions', Active=[mission()]),
                         event('CargoDepot', MissionID=123456, CargoType='DiagnosticSensor',
                               TotalItemsToDeliver=18, ItemsDelivered=0, UpdateType='Deliver'))
        for confirmation in confirmations:
            with self.subTest(event=confirmation['event']):
                self.clock.now.return_value = datetime(2026, 9, 18, 14, 41, tzinfo=timezone.utc)
                self.append(offer_event(), confirmation)
                self.assertEqual(self.db.pending_mission_offers(self.a), [])
                before = self.db.commander_missions(self.a)
                self.clock.now.return_value += timedelta(hours=30)
                self.assertEqual(len(self.visible()), 1)
                self.assertEqual(self.db.commander_missions(self.a), before)
                self.assertEqual(confirmed_mission_reward(self.visible()), 927436)

    def test_ttl_cleanup_only_writes_requested_fid(self):
        offer = _receive_text_offer(offer_event())
        self.seed_pending([offer], self.a)
        self.seed_pending([offer], self.b)
        self.clock.now.return_value += timedelta(hours=30)
        self.assertEqual(self.visible(self.a), [])
        self.assertEqual(self.stored_pending('FID-B'), [offer])
        self.assertEqual(self.visible(self.b), [])
        self.assertEqual(self.stored_pending('FID-B'), [])

    def test_ttl_restart_prunes_before_display_without_reading_journals(self):
        self.append(offer_event())
        self.clock.now.return_value += timedelta(hours=30)
        self.db = CMDRDatabase(self.folder / 'state.db')
        with patch.object(Path, 'open', side_effect=AssertionError('No journals')):
            self.assertEqual(self.visible(), [])
        self.assertEqual(self.stored_pending(), [])

    def test_ttl_new_receive_text_prunes_old_offer(self):
        self.append(offer_event())
        self.clock.now.return_value += timedelta(hours=30)
        new = dict(offer_event(), timestamp=self.clock.now.return_value.isoformat())
        self.append(new)
        self.assertEqual(len(self.stored_pending()), 1)
        self.assertEqual(self.stored_pending()[0]['timestamp'], new['timestamp'])

    def test_ttl_already_old_receive_text_is_not_stored_as_pending(self):
        self.clock.now.return_value += timedelta(hours=30)
        self.append(offer_event())
        self.assertEqual(self.stored_pending(), [])
        self.assertEqual(self.visible(), [])

    def test_ttl_confirmation_events_prune_before_matching(self):
        for confirmation in (event('Missions', Active=[mission()]),
                             event('CargoDepot', MissionID=123456, CargoType='DiagnosticSensor',
                                   TotalItemsToDeliver=18, ItemsDelivered=0, UpdateType='Deliver')):
            with self.subTest(event=confirmation['event']):
                self.clock.now.return_value = datetime(2026, 9, 19, 20, tzinfo=timezone.utc)
                self.seed_pending([_receive_text_offer(offer_event())])
                self.append(confirmation)
                self.assertEqual(self.stored_pending(), [])
                self.assertEqual(self.visible()[0].reward, 0)

    def test_ttl_cleanup_write_failure_preserves_pending(self):
        self.append(offer_event())
        before = self.stored_pending()
        self.clock.now.return_value += timedelta(hours=30)
        with patch.object(self.db, '_store_pending_mission_offers', side_effect=sqlite3.OperationalError('TTL failure')):
            with self.assertRaises(sqlite3.OperationalError):
                self.db.pending_mission_offers(self.a)
        self.assertEqual(self.stored_pending(), before)

    def test_translations_and_commodity_fallback(self):
        keys = ('missions.encounter', 'missions.reward_offer', 'missions.encounter_hint',
                'missions.encounter_collect', 'commodity.diagnosticsensor')
        for lang, catalog in _TRANSLATIONS.items():
            for key in keys:
                self.assertIn(key, catalog, (lang, key))
        self.assertEqual(commodity_name('$DiagnosticSensor_Name;'), 'Hardware-Diagnostiksensor')
        self.assertEqual(commodity_name('diagnosticsensor', 'Journal name'), 'Journal name')
        self.assertEqual(commodity_name('$UnknownGoods_Name;'), 'UnknownGoods')

    def test_dark_light_table_and_details(self):
        from PySide6.QtWidgets import QApplication, QTableWidget, QLabel
        from cmdrhelper.ui.main_window import MainWindow
        from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
        app = QApplication.instance() or QApplication([])
        self.append(offer_event())
        table = QTableWidget(0, 7)
        view = SimpleNamespace(state=SimpleNamespace(missions=self.visible()), missions_table=table,
                mission_detail_title=QLabel(), mission_detail_text=QLabel(), mission_progress_text=QLabel(),
                _translate_mission_text=MainWindow._translate_mission_text,
                _place_text=MainWindow._place_text, _format_reward=MainWindow._format_reward,
                _format_expiry=MainWindow._format_expiry)
        view._mission_selection_changed = lambda: MainWindow._mission_selection_changed(view)
        for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            table.setStyleSheet(style)
            MainWindow._refresh_missions_table(view)
            self.assertEqual(table.rowCount(), 1)
            self.assertIn('Belohnungsangebot', table.item(0, 5).text())
            self.assertEqual(table.item(0, 6).text(), tr('common.unknown'))
            self.assertIn('MissionID', table.item(0, 3).toolTip())
            table.selectRow(0)
            view._mission_selection_changed()
            self.assertIn('Hardware-Diagnostiksensor', view.mission_detail_title.text())
            self.assertNotIn('0/18', view.mission_progress_text.text())
        from PySide6.QtCore import QTimer
        self.clock.now.return_value += timedelta(hours=30)
        with patch.object(QTimer, 'start', side_effect=AssertionError('No new timer')):
            view.state.missions = self.visible()
            MainWindow._refresh_missions_table(view)
        self.assertEqual(len(view.state.missions), 0)  # Existing missions counter source.
        self.assertEqual(table.rowCount(), 0)
        self.assertEqual(view.mission_detail_title.text(), tr('missions.none_selected'))
        table.close()
