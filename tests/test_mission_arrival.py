"""Arrival evidence from synthetic journals only; no database/application startup."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

from cmdrhelper.game_instances import GameInstance, ProcessSnapshot
from cmdrhelper.mission_arrival import ArrivalPosition, ArrivalSource
from cmdrhelper.models import Mission


def event(kind, **fields):
    return dict(event=kind, timestamp='2026-01-01T12:00:00Z', **fields)


def mission(mid=1069627151, **fields):
    return Mission(mission_id=mid, name='Bringen Sie Mona Rich ein Paket',
                   destination_system='HIP 97950',
                   **dict(dict(destination_station='Donoso Biochemical Complex'), **fields))


def dock(**fields):
    return event('Docked', **dict(dict(StarSystem='HIP 97950', SystemAddress=42,
                                     StationName='Donoso Biochemical Complex', MarketID=7), **fields))


class ArrivalPositionTests(unittest.TestCase):
    def setUp(self):
        self.p = ArrivalPosition()
        self.m = mission()

    def feed(self, *events):
        for n, e in enumerate(events):
            self.p.feed(e, n)

    def test_mona_approach_then_docked_without_mission_mutation(self):
        before = deepcopy(self.m)
        self.feed(event('Location', StarSystem='HIP 97950', SystemAddress=42),
                  event('ApproachBody', Body='HIP 97950 ABC 1 c', BodyID=16),
                  event('ApproachSettlement', Name=self.m.destination_station, SystemAddress=42,
                        BodyName='HIP 97950 ABC 1 c', BodyID=16))
        self.assertFalse(self.p.matches(self.m))
        self.feed(dock())
        self.assertTrue(self.p.matches(self.m))
        self.assertEqual(self.m, before)
        self.assertEqual(self.m.status, 'Angenommen')

    def test_location_requires_explicit_docking_and_exact_place(self):
        for fields, expected in [({'Docked': True}, True), ({'Docked': False}, False),
                                 ({}, False), ({'Docked': True, 'StationName': 'Other'}, False),
                                 ({'Docked': True, 'StarSystem': 'Other'}, False)]:
            e = dock(**fields); e['event'] = 'Location'
            self.feed(e)
            self.assertEqual(self.p.matches(self.m), expected)

    def test_missing_fields_system_only_and_wrong_place(self):
        for e in [event('Docked', StarSystem='HIP 97950'),
                  event('Docked', StationName=self.m.destination_station),
                  event('FSDJump', StarSystem='HIP 97950'), dock(StationName='Other')]:
            self.p = ArrivalPosition(); self.feed(e)
            self.assertFalse(self.p.matches(self.m))

    def test_touchdown_needs_matching_body_context_and_player(self):
        self.m.destination_station = ''; self.m.destination_body = 'Planet'
        for body, player, expected in [('Planet', True, True), ('Wrong', True, False),
                                        ('Planet', False, False), ('Planet', None, False)]:
            self.p = ArrivalPosition()
            self.feed(event('Location', StarSystem='HIP 97950'),
                      event('ApproachBody', Body='Planet', BodyID=4))
            self.assertFalse(self.p.matches(self.m))
            self.feed(event('Touchdown', Body=body, BodyID=4, PlayerControlled=player))
            self.assertEqual(self.p.matches(self.m), expected)
        self.p = ArrivalPosition()
        self.feed(event('Touchdown', StarSystem='HIP 97950', Body='Planet', PlayerControlled=True))
        self.assertFalse(self.p.matches(self.m))

    def test_station_target_never_satisfied_by_planet_landing(self):
        self.m.destination_body = 'Planet'
        self.feed(event('Location', StarSystem='HIP 97950', Body='Planet', BodyID=4),
                  event('Touchdown', Body='Planet', BodyID=4, PlayerControlled=True))
        self.assertFalse(self.p.matches(self.m))

    def test_departures_and_contradictions_clear(self):
        for e in [event('SupercruiseEntry', StarSystem='HIP 97950'),
                  event('FSDJump', StarSystem='Other'), event('LeaveBody'),
                  event('ApproachSettlement', Name='Other'), dock(MarketID=8, StationName='Other'),
                  event('Location', StarSystem='HIP 97950', Docked=False),
                  event('Shutdown'), event('Died')]:
            with self.subTest(event=e):
                self.feed(dock(), e)
                self.assertFalse(self.p.matches(self.m))

    def test_undock_liftoff_disembark_embark_do_not_invent_departure(self):
        self.feed(dock())
        for kind in ('Undocked', 'Disembark', 'Embark', 'Liftoff'):
            self.feed(event(kind, StarSystem='HIP 97950', PlayerControlled=True))
            self.assertTrue(self.p.matches(self.m), kind)

    def test_multiple_missions_redirect_and_pending(self):
        self.feed(dock())
        other = deepcopy(self.m); other.mission_id += 1
        self.assertTrue(all(self.p.matches(m) for m in (self.m, other)))
        other.destination_station = 'Hoffman Installation'
        self.assertFalse(self.p.matches(other))
        self.m.extra['pending_offer'] = True
        self.assertFalse(self.p.matches(self.m))

    def test_non_position_payload_cannot_move_player(self):
        self.feed(dock(), event('Scan', StarSystem='Other', Body='Other'),
                  event('Touchdown', PlayerControlled=False, StarSystem='Other', Body='Other'))
        self.assertTrue(self.p.matches(self.m))

    def test_conflicting_system_and_market_identifiers_reject_docking(self):
        self.feed(dock(), dock(SystemAddress=43))
        self.assertFalse(self.p.matches(self.m))
        self.p = ArrivalPosition(system='HIP 97950', address=42)
        self.feed(event('ApproachSettlement', Name=self.m.destination_station, MarketID=8), dock())
        self.assertFalse(self.p.matches(self.m))


class ArrivalSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'Journal.2026-01-01T120000.01.log'
        self.session = dict(journal_file=str(self.path), fid_seen='A', commander_id=1,
                            attribution_status='identified', first_event_at='2026-01-01T12:00:00Z')
        self.processor = NS(sessions=[self.session], projection_for=Mock(
            return_value=dict(commander_fid='A', latest_journal_session=self.session)))
        self.runtime = NS(generation=1, processor=self.processor,
                          source=NS(id='heroic', enabled=True, status='ready', path=self.tmp.name))
        self.state = NS(commander_id=1, commander_fid='A', viewed_commander_id=1,
                        sources=NS(runtimes={'heroic': self.runtime}))
        self.process = ProcessSnapshot(True, [GameInstance(12, 0, journals=(str(self.path),))])
        self.mock_process = patch('cmdrhelper.mission_arrival.inspect_instances', return_value=self.process).start()
        self.addCleanup(patch.stopall)
        self.source = ArrivalSource()
        self.events = [event('Commander', FID='A', Name='Synthetic'), event('LoadGame', FID='A'), dock()]
        self.write()
        self.status()

    def write(self):
        self.path.write_text(''.join(json.dumps(e)+'\n' for e in self.events))
        size = self.path.stat().st_size
        self.session.update(last_read_offset=size, last_complete_line_offset=size)

    def status(self, **fields):
        data = event('Status', **dict(dict(Flags=1), **fields))
        (self.path.parent / 'Status.json').write_text(json.dumps(data))

    def test_confirmed_source_and_no_database_needed(self):
        result = self.source.snapshot(self.state)
        self.assertIsNotNone(result)
        self.assertTrue(result[1].matches(mission()))

    def test_real_source_projection_from_temporary_database(self):
        from cmdrhelper.database import CMDRDatabase
        from cmdrhelper.source_processing import SourceProcessor
        db = CMDRDatabase(Path(self.tmp.name) / 'synthetic.db')
        processor = SourceProcessor(db, self.path.parent)
        processor.process()
        self.runtime.processor = processor
        cid = processor.sessions[-1]['commander_id']
        self.state.commander_id = self.state.viewed_commander_id = cid
        result = self.source.snapshot(self.state)
        self.assertIsNotNone(result)
        self.assertTrue(result[1].matches(mission()))

    def test_no_process_ambiguous_or_unavailable(self):
        for snapshot in [ProcessSnapshot(False), ProcessSnapshot(True),
                         ProcessSnapshot(True, self.process.instances * 2)]:
            self.mock_process.return_value = snapshot
            self.assertIsNone(self.source.snapshot(self.state))

    def test_historical_commander_and_foreign_fid(self):
        self.state.viewed_commander_id = 2
        self.assertIsNone(self.source.snapshot(self.state))
        self.state.viewed_commander_id = 1; self.state.commander_fid = 'B'
        self.assertIsNone(self.source.snapshot(self.state))

    def test_ambiguous_sources_and_unverified_session(self):
        self.state.sources.runtimes['steam'] = NS(
            generation=2, processor=self.processor,
            source=NS(id='steam', enabled=True, status='ready', path=self.tmp.name))
        self.assertIsNone(self.source.snapshot(self.state))
        del self.state.sources.runtimes['steam']
        self.session['attribution_status'] = 'unknown'
        self.assertIsNone(self.source.snapshot(self.state))

    def test_pending_bytes_new_session_and_stale_projection(self):
        with self.path.open('a') as f: f.write('{')
        self.assertIsNone(self.source.snapshot(self.state))
        self.write()
        self.processor.projection_for.return_value = None
        self.assertIsNone(self.source.snapshot(self.state))
        self.processor.projection_for.return_value = dict(commander_fid='A', latest_journal_session=self.session)
        (self.path.parent / 'Journal.2026-01-02T120000.01.log').write_text('')
        self.assertIsNone(self.source.snapshot(self.state))

    def test_missing_partial_stale_and_flying_status(self):
        p = self.path.parent / 'Status.json'
        for text in ['{', '{}', json.dumps(event('Status')),
                     '{"event":"Status","Flags":1,"timestamp":"2025-01-01T00:00:00Z"}']:
            p.write_text(text)
            self.assertIsNone(self.source.snapshot(self.state), text)
        p.unlink()
        self.assertIsNone(self.source.snapshot(self.state))

    def test_old_docked_without_current_confirmation_not_claimed(self):
        self.status(Flags=0)
        self.assertFalse(self.source.snapshot(self.state)[1].matches(mission()))
        self.status(Flags=1)
        self.assertIsNotNone(self.source.snapshot(self.state))
        self.events.append(event('Undocked')); self.write(); self.status(Flags=0)
        self.assertIsNotNone(self.source.snapshot(self.state))
        self.status(Flags=16)
        self.assertFalse(self.source.snapshot(self.state)[1].matches(mission()))
        self.status(Flags=0)
        self.assertFalse(self.source.snapshot(self.state)[1].matches(mission()))

    def test_planet_confirmation_and_status_body_conflict(self):
        self.events = self.events[:2] + [event('Location', StarSystem='HIP 97950', Body='Planet', BodyID=4),
            event('Touchdown', Body='Planet', BodyID=4, PlayerControlled=True)]
        self.write(); self.status(Flags=2, BodyName='Planet')
        m = mission(destination_station='', destination_body='Planet')
        self.assertTrue(self.source.snapshot(self.state)[1].matches(m))
        self.status(Flags=2, BodyName='Other')
        self.assertFalse(self.source.snapshot(self.state)[1].matches(m))

    def test_delayed_status_retains_binding_but_not_hit(self):
        self.events[-1]['timestamp'] = '2026-01-01T12:00:01Z'; self.write()
        pending = self.source.snapshot(self.state)
        self.assertIsNotNone(pending)
        self.assertFalse(pending[1].matches(mission()))
        (self.path.parent / 'Status.json').write_text(json.dumps(
            dict(event='Status', timestamp='2026-01-01T12:00:01Z', Flags=1)))
        self.assertEqual(self.source.snapshot(self.state)[0], pending[0])
        self.assertTrue(self.source.snapshot(self.state)[1].matches(mission()))

    def test_terminal_events_and_identity_conflict(self):
        for kind in ('MissionCompleted', 'MissionAbandoned', 'MissionFailed'):
            self.events.append(event(kind, MissionID=1069627151)); self.write()
            self.assertIn(1069627151, self.source.snapshot(self.state)[2])
        self.events.append(event('Commander', FID='B')); self.write()
        self.assertIsNone(self.source.snapshot(self.state))

    def test_new_login_in_same_file_has_new_binding(self):
        old = self.source.snapshot(self.state)[0]
        self.events += [event('LoadGame', FID='A'), dock()]
        self.write()
        self.assertNotEqual(self.source.snapshot(self.state)[0], old)
