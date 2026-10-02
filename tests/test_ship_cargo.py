"""Ship totals: actual parser -> binding -> resolver -> recommendation UI input."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace, MethodType
import unittest
from unittest.mock import patch

from cmdrhelper.journal_reader import read_latest_state
from cmdrhelper.ship_cargo import CARGO_MUTATIONS, current_ship_cargo
from cmdrhelper.state import AppState
from cmdrhelper.ui.recommendations_view import ship_space

BASE = datetime(2026, 9, 27, 15, 20, tzinfo=timezone.utc)
NOW = BASE + timedelta(seconds=90)


def event(kind, second, **fields):
    return dict(event=kind, timestamp=(BASE + timedelta(seconds=second)).isoformat(), **fields)


def loadout(sid=44, capacity=576, second=5):
    return event('Loadout', second, Ship='panthermkii', ShipID=sid,
                 ShipName='[EOT] = Erft-Mammut =', CargoCapacity=capacity, Modules=[])


def cargo(count=0, second=6, vessel='Ship', inline=True):
    e = event('Cargo', second, Vessel=vessel, Count=count)
    if inline:
        e['Inventory'] = [dict(Name='gold', Count=count)] if count else []
    return e


def status(count=0, second=80, **fields):
    return dict(event('Status', second, Cargo=count, Flags=1 << 24, Flags2=0), **fields)


class Signal:
    def __init__(self):
        self.values = []
    def emit(self, value):
        self.values.append(value)


class ShipCargoTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        self.path = self.folder / 'Journal.2026-09-27T152000.01.log'
        self.clock = patch('cmdrhelper.ship_cargo.utc_now', return_value=NOW)
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def replay(self, events, sidecar=None, fid='F-A', state=None):
        rows = [event('Fileheader', 0), event('Commander', 1, FID=fid, Name='Test'),
                event('LoadGame', 2, FID=fid, Ship='panthermkii', ShipID=38)] + events
        self.path.write_text(''.join(json.dumps(e) + '\n' for e in rows))
        d = read_latest_state(self.folder)
        session = dict(attribution_status='identified', commander_id=1, fid_seen=fid,
                       journal_file=str(self.path), first_event_at=None,
                       last_complete_line_offset=self.path.stat().st_size,
                       last_read_offset=self.path.stat().st_size)
        s = state or SimpleNamespace(cargoSnapshotChanged=Signal(), cargo_snapshot=None)
        s.commander_id = 1
        s.commander_fid = fid
        s.ship = d['ship']
        s.ship_loadout = d['ship_loadout']
        s.ship_cargo_context = d['ship_cargo_context']
        s.ship_cargo_total = None
        s.active_srv_type = d['active_srv_type']
        s.journal_folder = self.folder
        s._journal_index_sessions = [session]
        s._cargo_status = sidecar
        s._cargo_refresh_data = (d, session)
        s._apply_live_cargo_snapshot = MethodType(AppState._apply_live_cargo_snapshot, s)
        AppState._apply_live_cargo_snapshot(s, d, session)
        return s, d

    def mammut_events(self):
        return [event('LaunchSRV', 3, SRVType='testbuggy'), cargo(second=4, vessel='SRV'),
                event('DockSRV', 5), loadout(38, 43, 6),
                event('ShipyardSwap', 7, ShipID=44, ShipType='panthermkii'), loadout(second=8)]

    def test_kraehe_after_on_foot_start_uses_only_fresh_ship_status(self):
        # Yesterday's cargo predates the ship switch and today's on-foot start.
        old_cargo = cargo(5, second=6, inline=False)
        (self.folder / 'Cargo.json').write_text(json.dumps(cargo(5, second=6)))
        kraehe = dict(loadout(12, 16, 30), Ship='cobramkv',
                      ShipName='[EOT] = Erft-Krähe =')
        rows = [loadout(), old_cargo, event('ShipyardSwap', 7, ShipID=12),
                dict(kraehe, timestamp=event('', 8)['timestamp']),
                event('Disembark', 9, SRV=False, Taxi=False, Multicrew=False),
                event('Shutdown', 10),
                event('LoadGame', 20, FID='F-A', Ship='UtilitySuit_Class5',
                      Ship_Localised='$UtilitySuit_Class1_Name;', ShipID=4293000001),
                event('Embark', 30, ID=12, SRV=False, Taxi=False, Multicrew=False),
                kraehe]
        s, d = self.replay(rows)
        self.assertEqual(d['active_srv_type'], '')
        self.assertIsNone(d['active_srv_capacity'])
        self.assertEqual(s.ship_cargo_context['vessel'], 'Ship')
        self.assertEqual(s.ship_cargo_context['ship_id'], 12)
        self.assertIsNone(s.cargo_snapshot)
        self.assertIsNone(current_ship_cargo(s))
        s._cargo_status = status(0)
        for age, expected in ((0, 16), (120, 16), (121, 16)):
            with self.subTest(age=age), patch(
                    'cmdrhelper.ship_cargo.utc_now',
                    return_value=BASE + timedelta(seconds=80 + age)):
                self.assertEqual(ship_space(s), ('[EOT] = Erft-Krähe =', expected))
                if expected is not None:
                    self.assertEqual(current_ship_cargo(s)['count'], 0)
                    self.assertEqual(current_ship_cargo(s)['source'], 'status')
                self.assertIsNone(s.cargo_snapshot)

    def test_suit_start_clears_previous_srv_without_enabling_ship_cargo(self):
        for suit in ('UtilitySuit_Class5', 'ExplorationSuit_Class3', 'TacticalSuit_Class1'):
            with self.subTest(suit=suit):
                s, d = self.replay([
                    loadout(), event('LaunchSRV', 6, SRVType='mev_rhino'),
                    event('LoadGame', 10, FID='F-A', Ship=suit,
                          Ship_Localised=f'${suit}_Name;')], status())
                self.assertEqual(d['active_srv_type'], '')
                self.assertIsNone(d['active_srv_capacity'])
                self.assertIsNone(current_ship_cargo(s))

    def test_real_srv_start_and_confirmed_ship_transitions(self):
        for vehicle, capacity in (('testbuggy', 4), ('mev_rhino', 72),
                                  ('combat_multicrew_srv_01', 2), ('lander01', None)):
            rows = [loadout(), event('LoadGame', 10, FID='F-A', Ship=vehicle)]
            with self.subTest(vehicle=vehicle):
                s, d = self.replay(rows, status())
                self.assertEqual(d['active_srv_type'], vehicle)
                self.assertEqual(d['active_srv_capacity'], capacity)
                self.assertEqual(s.ship_cargo_context['vessel'], 'SRV')
                self.assertIsNone(current_ship_cargo(s))
            for transition in ([event('Embark', 20, SRV=False, Taxi=False, Multicrew=False)],
                               [loadout(second=20)], [event('DockSRV', 20)]):
                with self.subTest(vehicle=vehicle, transition=transition):
                    s, d = self.replay(rows + transition, status())
                    self.assertEqual(d['active_srv_type'], '')
                    self.assertIsNone(d['active_srv_capacity'])
                    s, _ = self.replay(rows + transition + [loadout(second=21)], status())
                    self.assertEqual(ship_space(s)[1], 576)

    def test_embark_srv_taxi_or_multicrew_does_not_clear_srv_or_enable_ship(self):
        for field in ('SRV', 'Taxi', 'Multicrew'):
            with self.subTest(field=field):
                fields = dict(SRV=False, Taxi=False, Multicrew=False)
                fields[field] = True
                s, d = self.replay([loadout(), event('LaunchSRV', 6, SRVType='mev_rhino'),
                                    event('Embark', 10, **fields)], status())
                self.assertEqual(d['active_srv_type'], 'mev_rhino')
                self.assertEqual(d['active_srv_capacity'], 72)
                self.assertIsNone(current_ship_cargo(s))

    def test_fighter_blocks_ship_cargo_until_return_and_new_evidence(self):
        rows = [loadout(), cargo(5), event('LaunchFighter', 10, PlayerControlled=True)]
        s, _ = self.replay(rows, status())
        self.assertIsNone(current_ship_cargo(s))
        for transition in (event('DockFighter', 20),
                           event('Embark', 20, SRV=False, Taxi=False, Multicrew=False)):
            with self.subTest(transition=transition):
                s, d = self.replay(rows + [transition])
                self.assertEqual(d['active_srv_type'], '')
                self.assertIsNone(d['active_srv_capacity'])
                self.assertEqual(s.ship_cargo_context['vessel'], 'Ship')
                self.assertIsNone(current_ship_cargo(s))
                s._cargo_status = status(5)
                self.assertEqual(ship_space(s)[1], 571)
                s._cargo_status = status(5, Flags=1 << 25)
                self.assertIsNone(current_ship_cargo(s))

    def test_real_sequence_zero_and_loaded_status_without_relabelling_srv(self):
        for used, free in ((0, 576), (120, 456)):
            with self.subTest(used=used):
                s, _ = self.replay(self.mammut_events(), status(used))
                self.assertEqual(ship_space(s), ('[EOT] = Erft-Mammut =', free))
                self.assertEqual(s.cargo_snapshot['vessel'], 'SRV')
                self.assertIsNone(s.cargo_snapshot['ship_id'])
                self.assertEqual(current_ship_cargo(s)['source'], 'status')

    def test_old_ship_cargo_is_never_rebound_even_across_multiple_switches(self):
        for last_id in (45, 44):
            events = [loadout(), cargo(5), event('ShipyardSwap', 7, ShipID=45),
                      loadout(45, 100, 8)]
            if last_id == 44:
                # A -> B -> A within one refresh AND the same timestamp.
                events += [event('ShipyardSwap', 8, ShipID=44), loadout(44, 100, 8)]
            s, d = self.replay(events)
            self.assertEqual(d['last_cargo_context']['ship_id'], 44)
            self.assertIsNone(s.cargo_snapshot)
            self.assertIsNone(ship_space(s)[1])
            s._apply_live_cargo_snapshot(d, s._journal_index_sessions[-1])
            self.assertIsNone(s.cargo_snapshot)
            self.assertNotEqual(ship_space(s)[1], 95)

    def test_srv_zero_is_not_ship_zero_without_status(self):
        s, _ = self.replay(self.mammut_events())
        self.assertIsNone(ship_space(s)[1])

    def test_snapshot_then_count_only_then_status_priority(self):
        s, _ = self.replay([loadout(), cargo(5)], status(120))
        self.assertEqual((ship_space(s)[1], current_ship_cargo(s)['source']), (571, 'snapshot'))
        s, _ = self.replay([loadout(), cargo(10, inline=False)], status(120))
        self.assertIsNone(s.cargo_snapshot)
        self.assertEqual((ship_space(s)[1], current_ship_cargo(s)['source']), (566, 'journal'))
        s, _ = self.replay(self.mammut_events(), status(120))
        self.assertEqual(current_ship_cargo(s)['source'], 'status')
        s, _ = self.replay(self.mammut_events() + [cargo(5, 81)], status(120), state=s)
        self.assertEqual(current_ship_cargo(s)['source'], 'snapshot')
        self.assertEqual(ship_space(s)[1], 571)

    def test_status_before_or_same_second_as_switch_and_stale_status_rejected(self):
        for second in (6, 7, 8, -100, 96):
            s, _ = self.replay(self.mammut_events(), status(second=second))
            # second 8 is the Loadout; switch barrier is second 7, so this is
            # admissible when Status and Loadout agree. Test the switch second.
            if second == 8:
                self.assertEqual(ship_space(s)[1], 576)
            else:
                self.assertIsNone(ship_space(s)[1])
        s, _ = self.replay(self.mammut_events(), status())
        with patch('cmdrhelper.ship_cargo.utc_now', return_value=BASE + timedelta(seconds=201)):
            self.assertIsNone(ship_space(s)[1])

    def test_wrong_vehicle_and_invalid_status_values(self):
        invalid = [dict(Flags=1 << 26), dict(Flags=(1 << 24) | (1 << 26)),
                   dict(Flags=(1 << 24) | (1 << 25)), dict(Flags=0), dict(Flags=True)]
        invalid += [dict(Flags2=v) for v in (1, 2, 4)]
        invalid += [dict(Cargo=v) for v in (-1, 577, 0.5, True, '0', None, float('nan'), float('inf'))]
        for fields in invalid:
            with self.subTest(fields=fields):
                payload = status()
                payload.update(fields)
                s, _ = self.replay(self.mammut_events(), payload)
                self.assertIsNone(ship_space(s)[1])

    def test_loadout_session_and_commander_validation(self):
        for mutation in ('stale', 'incomplete', 'wrong_fid', 'wrong_session', 'ambiguous', 'old_loadout'):
            s, _ = self.replay(self.mammut_events(), status())
            if mutation == 'stale': s.ship_loadout.loadout_stale = True
            if mutation == 'incomplete': s.ship_loadout.loadout_complete = False
            if mutation == 'wrong_fid': s.commander_fid = 'F-B'
            if mutation == 'wrong_session': s._journal_index_sessions[-1]['journal_file'] = 'other'
            if mutation == 'ambiguous': s._journal_index_sessions[-1]['attribution_status'] = 'ambiguous'
            if mutation == 'old_loadout': s.ship_loadout.loadout_timestamp = event('', -1)['timestamp']
            with self.subTest(mutation=mutation): self.assertIsNone(ship_space(s)[1])

    def test_missing_mismatched_late_sidecar_changes_only_inventory_not_identity(self):
        s, d = self.replay([loadout(), cargo(5, inline=False)])
        self.assertEqual(ship_space(s)[1], 571)
        sidecar = self.folder / 'Cargo.json'
        sidecar.write_text(json.dumps(cargo(5, second=4)))
        s._apply_live_cargo_snapshot(d, s._journal_index_sessions[-1])
        self.assertIsNone(s.cargo_snapshot)
        sidecar.write_text(json.dumps(cargo(5)))
        AppState._poll_ship_cargo(s)
        self.assertEqual(s.cargo_snapshot['ship_id'], 44)
        self.assertEqual(current_ship_cargo(s)['source'], 'snapshot')
        # Replaying after a switch must not reattach the now matching sidecar.
        s, _ = self.replay([loadout(), cargo(5, inline=False),
                           event('ShipyardSwap', 7, ShipID=45), loadout(45, 100, 8)], state=s)
        self.assertIsNone(s.cargo_snapshot)
        self.assertIsNone(ship_space(s)[1])

    def test_mutations_invalidate_then_authoritative_count_replaces_without_double_count(self):
        for kind in sorted(CARGO_MUTATIONS):
            with self.subTest(kind=kind):
                rows = [loadout(), cargo(5), event(kind, 10, Count=2, Type='gold')]
                s, _ = self.replay(rows, status(5, second=9))
                self.assertIsNone(s.cargo_snapshot)
                self.assertIsNone(ship_space(s)[1])
                s, _ = self.replay(rows + [cargo(7, second=11)])
                self.assertEqual(ship_space(s)[1], 569)
                s, _ = self.replay(rows, status(7, second=11))
                self.assertEqual(ship_space(s)[1], 569)

    def test_ship_srv_ship_recovers_only_with_new_evidence(self):
        rows = [loadout(), cargo(5), event('LaunchSRV', 7, SRVType='testbuggy')]
        s, _ = self.replay(rows, status(5))
        self.assertIsNone(ship_space(s)[1])
        rows += [cargo(0, 8, 'SRV'), event('DockSRV', 9)]
        s, _ = self.replay(rows)
        self.assertIsNone(ship_space(s)[1])
        s, _ = self.replay(rows, status(5))
        self.assertEqual(ship_space(s)[1], 571)
        s, _ = self.replay(rows + [cargo(7, 11)])
        self.assertEqual(ship_space(s)[1], 569)

    def test_new_game_death_resurrection_new_ship_and_commander_reset(self):
        for transition in (event('LoadGame', 10, FID='F-A', Ship='panthermkii', ShipID=44),
                           event('Died', 10), event('Resurrect', 10),
                           event('ShipyardNew', 10, NewShipID=45), event('Shutdown', 10)):
            with self.subTest(transition=transition):
                s, _ = self.replay([loadout(), cargo(5), transition], status())
                self.assertIsNone(ship_space(s)[1])
        s, _ = self.replay([loadout(), cargo(5)])
        AppState.reset_commander_runtime_state(s)
        self.assertIsNone(s.cargo_snapshot)
        self.assertIsNone(s.ship_cargo_total)
        s, _ = self.replay([loadout()], state=s, fid='F-B')
        self.assertIsNone(ship_space(s)[1])

    def test_start_during_game_and_game_after_app_start(self):
        # Same parser entry point on initial refresh and on watcher refresh.
        s, _ = self.replay(self.mammut_events(), status())
        fresh, _ = self.replay(self.mammut_events(), status())
        self.assertEqual(ship_space(s), ship_space(fresh))
        empty, _ = self.replay([])
        self.assertIsNone(ship_space(empty)[1])
        empty, _ = self.replay(self.mammut_events(), status(), state=empty)
        self.assertEqual(ship_space(empty)[1], 576)

    def test_poll_retains_confirmed_status_but_blocks_pending_journal(self):
        s, _ = self.replay(self.mammut_events())
        path = self.folder / 'Status.json'
        path.write_text(json.dumps(status()))
        AppState._poll_ship_cargo(s)
        self.assertEqual(s.ship_cargo_total['count'], 0)
        before = len(s.cargoSnapshotChanged.values)
        path.write_text(json.dumps(status(120)))
        AppState._poll_ship_cargo(s)
        self.assertEqual(ship_space(s)[1], 456)
        self.assertGreater(len(s.cargoSnapshotChanged.values), before)
        with patch('cmdrhelper.ship_cargo.utc_now', return_value=BASE + timedelta(seconds=201)):
            AppState._poll_ship_cargo(s)
            self.assertEqual(s.ship_cargo_total['count'], 120)
            self.assertEqual(ship_space(s)[1], 456)
        with self.path.open('a') as f: f.write(json.dumps(event('ShipyardSwap', 85, ShipID=45)) + '\n')
        AppState._poll_ship_cargo(s)
        self.assertIsNone(ship_space(s)[1])

    def test_status_invalid_json_never_keeps_previous_value(self):
        s, _ = self.replay(self.mammut_events())
        path = self.folder / 'Status.json'
        path.write_text(json.dumps(status()))
        AppState._poll_ship_cargo(s)
        self.assertEqual(ship_space(s)[1], 576)
        for payload in ('{', json.dumps(status()).replace('"Cargo": 0', '"Cargo": 0, "Cargo": 5')):
            path.write_text(payload)
            AppState._poll_ship_cargo(s)
            self.assertIsNone(ship_space(s)[1])

    def test_confirmed_1110_t_survives_time_poll_and_journal_replay_not_restart(self):
        rows = [loadout(45, 1110)]
        s, _ = self.replay(rows, status())
        (self.folder / 'Status.json').write_text(json.dumps(status()))
        for age in (0, 120, 121, 86400):
            with self.subTest(age=age), patch(
                    'cmdrhelper.ship_cargo.utc_now',
                    return_value=BASE + timedelta(seconds=80 + age)):
                AppState._poll_ship_cargo(s)
                self.assertEqual(ship_space(s)[1], 1110)
                self.assertEqual(s.ship_cargo_total['source'], 'status')
                self.assertEqual(s.ship_cargo_total['ship_id'], 45)
        with patch('cmdrhelper.ship_cargo.utc_now', return_value=BASE + timedelta(days=1)):
            binding = dict(s._confirmed_status_cargo['binding'])
            s, _ = self.replay(rows + [event('Music', 85)], status(), state=s)
            AppState._poll_ship_cargo(s)
            self.assertEqual(ship_space(s)[1], 1110)
            self.assertEqual(s._confirmed_status_cargo['binding'], binding)
            restarted, _ = self.replay(rows, status())
            self.assertIsNone(ship_space(restarted)[1])
            self.assertIsNone(restarted._confirmed_status_cargo)

    def test_every_mutation_invalidates_status_and_requires_new_evidence(self):
        for kind in sorted(CARGO_MUTATIONS):
            with self.subTest(kind=kind):
                rows = [loadout(45, 1110)]
                s, _ = self.replay(rows, status())
                self.assertEqual(ship_space(s)[1], 1110)
                rows += [event(kind, 85, Count=2, Type='gold')]
                s, _ = self.replay(rows, status(), state=s)
                # Even still-fresh pre-mutation evidence must be rejected.
                self.assertIsNone(ship_space(s)[1])
                self.assertIsNone(s._confirmed_status_cargo)
                with patch('cmdrhelper.ship_cargo.utc_now', return_value=BASE + timedelta(seconds=300)):
                    self.assertIsNone(ship_space(s)[1])
                    s._cargo_status = status(2, second=299)
                    self.assertEqual(ship_space(s)[1], 1108)
                    self.assertEqual(current_ship_cargo(s)['source'], 'status')

    def test_confirmed_status_cannot_cross_ship_session_or_vehicle_transitions(self):
        transitions = [
            [event('ShipyardSwap', 85, ShipID=46), loadout(46, 1110, 86)],
            [event('ShipyardSwap', 85, ShipID=46), loadout(46, 1110, 85),
             event('ShipyardSwap', 85, ShipID=45), loadout(45, 1110, 85)],
            [event('LoadGame', 85, FID='F-A', Ship='panthermkii', ShipID=45),
             loadout(45, 1110, 86)],
            [event('LaunchSRV', 85, SRVType='testbuggy')],
            [event('LaunchSRV', 85, SRVType='testbuggy'), event('DockSRV', 86)],
            [event('Disembark', 85)],
            [event('Disembark', 85), event('Embark', 86, SRV=False)],
            [event('LaunchFighter', 85, PlayerControlled=True)],
            [event('Died', 85)], [event('Resurrect', 85)], [event('Shutdown', 85)],
        ]
        for tail in transitions:
            with self.subTest(tail=tail):
                rows = [loadout(45, 1110)]
                s, _ = self.replay(rows, status())
                self.assertEqual(ship_space(s)[1], 1110)
                s, _ = self.replay(rows + tail, status(), state=s)
                self.assertIsNone(ship_space(s)[1])
                self.assertIsNone(s._confirmed_status_cargo)

    def test_confirmed_status_commander_and_loadout_guards_remain_active(self):
        for mutation in ('fid', 'commander', 'journal', 'stale', 'incomplete',
                         'capacity', 'loadout_timestamp', 'flags', 'quantity'):
            with self.subTest(mutation=mutation):
                s, _ = self.replay([loadout(45, 1110)], status())
                self.assertEqual(ship_space(s)[1], 1110)
                if mutation == 'fid': s.commander_fid = 'F-B'
                if mutation == 'commander': s.commander_id = 2
                if mutation == 'journal': s._journal_index_sessions[-1]['journal_file'] = 'other'
                if mutation == 'stale': s.ship_loadout.loadout_stale = True
                if mutation == 'incomplete': s.ship_loadout.loadout_complete = False
                if mutation == 'capacity': s.ship_loadout.cargo_capacity = 1000
                if mutation == 'loadout_timestamp': s.ship_loadout.loadout_timestamp = event('', 81)['timestamp']
                if mutation == 'flags': s._cargo_status['Flags2'] = 1
                if mutation == 'quantity': s._cargo_status['Cargo'] = 1
                with patch('cmdrhelper.ship_cargo.utc_now', return_value=BASE + timedelta(seconds=201)):
                    self.assertIsNone(ship_space(s)[1])
                    self.assertIsNone(s._confirmed_status_cargo)
        s, _ = self.replay([loadout(45, 1110)], status())
        self.assertEqual(ship_space(s)[1], 1110)
        AppState.reset_commander_runtime_state(s)
        self.assertIsNone(s._confirmed_status_cargo)

    def test_authoritative_cargo_replaces_confirmed_status_without_ttl(self):
        for inline, source in ((True, 'snapshot'), (False, 'journal')):
            with self.subTest(source=source):
                rows = [loadout(45, 1110)]
                s, _ = self.replay(rows, status())
                self.assertEqual(ship_space(s)[1], 1110)
                s, _ = self.replay(rows + [cargo(7, 85, inline=inline)], status(), state=s)
                with patch('cmdrhelper.ship_cargo.utc_now', return_value=BASE + timedelta(days=1)):
                    self.assertEqual(ship_space(s)[1], 1103)
                    self.assertEqual(current_ship_cargo(s)['source'], source)
                    self.assertIsNone(s._confirmed_status_cargo)

    def test_pending_journal_temporarily_blocks_but_does_not_expire_confirmation(self):
        s, _ = self.replay([loadout(45, 1110)], status())
        (self.folder / 'Status.json').write_text(json.dumps(status()))
        AppState._poll_ship_cargo(s)
        self.assertEqual(ship_space(s)[1], 1110)
        s._journal_index_sessions[-1]['last_read_offset'] = 0
        with patch('cmdrhelper.ship_cargo.utc_now', return_value=BASE + timedelta(days=1)):
            AppState._poll_ship_cargo(s)
            self.assertIsNone(ship_space(s)[1])
            s._journal_index_sessions[-1]['last_read_offset'] = self.path.stat().st_size
            AppState._poll_ship_cargo(s)
            self.assertEqual(ship_space(s)[1], 1110)

    def test_uncommitted_journal_and_new_file_block_unlabelled_status(self):
        s, _ = self.replay(self.mammut_events())
        (self.folder / 'Status.json').write_text(json.dumps(status()))
        s._journal_index_sessions[-1]['last_read_offset'] = 0
        AppState._poll_ship_cargo(s)
        self.assertIsNone(ship_space(s)[1])
        s._journal_index_sessions[-1]['last_read_offset'] = self.path.stat().st_size
        AppState._poll_ship_cargo(s)
        self.assertEqual(ship_space(s)[1], 576)
        newer = self.folder / 'Journal.2026-09-27T152100.01.log'
        newer.write_text(json.dumps(event('Fileheader', 85)) + '\n')
        AppState._poll_ship_cargo(s)
        self.assertIsNone(ship_space(s)[1])

    def test_malformed_inline_cargo_does_not_establish_a_total(self):
        for fields in (dict(Count=True), dict(Count=-1), dict(Inventory=[])):
            broken = cargo(5)
            broken.update(fields)
            s, _ = self.replay([loadout(), broken])
            self.assertIsNone(ship_space(s)[1])

    def test_new_session_requires_its_own_loadout_and_cargo_or_status(self):
        rows = [loadout(), cargo(5),
                event('LoadGame', 10, FID='F-A', Ship='panthermkii', ShipID=44)]
        s, _ = self.replay(rows, status())
        self.assertIsNone(ship_space(s)[1])
        s, _ = self.replay(rows + [loadout(second=11)], status(120))
        self.assertIsNone(s.cargo_snapshot)
        self.assertEqual(ship_space(s)[1], 456)
        s, _ = self.replay(rows + [loadout(second=11), cargo(8, second=12)])
        self.assertEqual(ship_space(s)[1], 568)

    def test_commander_change_without_explicit_reset_cannot_reuse_snapshot(self):
        s, _ = self.replay([loadout(), cargo(5)])
        self.assertEqual(ship_space(s)[1], 571)
        s, _ = self.replay([loadout()], fid='F-B', state=s)
        self.assertIsNone(s.cargo_snapshot)
        self.assertIsNone(ship_space(s)[1])

    def test_new_ship_recovers_from_new_loadout_and_its_own_cargo(self):
        s, _ = self.replay([loadout(), cargo(5),
                           event('ShipyardNew', 10, NewShipID=45),
                           loadout(45, 100, 11), cargo(20, 12)])
        self.assertEqual(s.cargo_snapshot['ship_id'], 45)
        self.assertEqual(ship_space(s)[1], 80)

    def test_same_second_new_game_does_not_reuse_old_srv_snapshot(self):
        s, _ = self.replay([event('LaunchSRV', 5, SRVType='testbuggy'),
                           cargo(0, 5, 'SRV'), event('LoadGame', 5, FID='F-A', Ship='testbuggy')])
        self.assertIsNone(s.cargo_snapshot)
        self.assertIsNone(ship_space(s)[1])
