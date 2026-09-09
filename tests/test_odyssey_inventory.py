import json
from pathlib import Path
import tempfile
import unittest

from cmdrhelper.odyssey_inventory import (
    CATEGORIES, OdysseyInventoryReader, OdysseyReducer, canonical_name,
)


def event(kind, second=0, **fields):
    return dict(timestamp=f"2026-09-08T14:58:{second:02d}Z", event=kind, **fields)


def item(name="graphene", count=5, **fields):
    return dict(Name=name, Count=count, OwnerID=0, **fields)


def snapshot(container, second=0, **categories):
    return event(container, second, **{c: categories.get(c, []) for c in CATEGORIES})


class OdysseyInventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.reader = OdysseyInventoryReader()

    def session(self, records, name="a", commander=1, fid="F1", status="identified"):
        path = Path(self.tmp.name) / (name + ".log")
        path.write_text("".join(json.dumps(e) + "\n" for e in
                                [event("Commander", FID=fid)] + records))
        return dict(journal_file=str(path), commander_id=commander, fid_seen=fid,
                    attribution_status=status)

    def read(self, *events):
        return self.reader.reconstruct(1, "F1", [self.session(list(events))])

    def pair(self, locker=10, backpack=2):
        return [snapshot("ShipLocker", Components=[item(count=locker)]),
                snapshot("Backpack", Components=[item(count=backpack)])]

    def test_full_locker_without_backpack_has_no_total(self):
        r = self.read(self.pair()[0])
        self.assertEqual(r.count("graphene", "ShipLocker"), 10)
        self.assertIsNone(r.count("graphene"))

    def test_full_backpack_and_synchronous_pair(self):
        r = self.read(*self.pair())
        self.assertEqual(r.count("graphene"), 12)
        self.assertEqual(r.count("graphene", "Backpack"), 2)

    def test_snapshot_replaces_and_missing_means_zero(self):
        r = self.read(*self.pair(), snapshot("Backpack", 1), snapshot("ShipLocker", 1))
        self.assertTrue(r.known)
        self.assertEqual(r.count("graphene"), 0)

    def test_notification_is_not_empty_snapshot(self):
        r = self.read(*self.pair(), event("ShipLocker", 1))
        self.assertIsNone(r.count("graphene", "ShipLocker"))
        self.assertEqual(sum(s.count for s in r.containers['ShipLocker'].stacks.values()), 10)

    def test_mismatched_snapshot_times_are_not_added(self):
        r = self.read(*self.pair(), snapshot("ShipLocker", 2, Components=[item(count=12)]))
        self.assertIsNone(r.total_count)

    def test_embark_empties_backpack_and_waits_for_locker(self):
        r = self.read(*self.pair(), event("Embark", 1))
        self.assertEqual(r.count("graphene", "Backpack"), 0)
        self.assertIsNone(r.total_count)
        r = self.read(*self.pair(), event("Embark", 1),
                      snapshot("ShipLocker", 2, Components=[item(count=12)]))
        self.assertEqual(r.total_count, 12)

    def test_disembark_invalidates_old_states(self):
        r = self.read(*self.pair(), event("Disembark", 1))
        self.assertIsNone(r.count("graphene", "Backpack"))
        self.assertIsNone(r.total_count)

    def test_backpack_added(self):
        r = self.read(*self.pair(), event("BackpackChange", 1,
                      Added=[item(count=3, Type="Component")]))
        self.assertEqual(r.count("graphene"), 15)
        self.assertEqual(r.last_change['changes'][0]['delta'], 3)

    def test_backpack_removed(self):
        r = self.read(*self.pair(), event("BackpackChange", 1,
                      Removed=[item(count=2, Type="Component")]))
        self.assertEqual(r.count("graphene", "Backpack"), 0)

    def test_collect_and_change_once_in_both_orders(self):
        action = event("CollectItems", 1, **item(count=3, Type="Component"))
        delta = event("BackpackChange", 1, Added=[item(count=3, Type="Component")])
        for sequence in ([action, delta], [delta, action]):
            with self.subTest(sequence=sequence):
                r = self.read(*self.pair(), *sequence)
                self.assertEqual(r.count("graphene"), 15)

    def test_use_and_change_once(self):
        r = self.read(snapshot("ShipLocker"),
                      snapshot("Backpack", Consumables=[item("healthpack", 2)]),
                      event("UseConsumable", 1, Name="healthpack", Type="Consumable"),
                      event("BackpackChange", 1,
                            Removed=[item("healthpack", 1, Type="Consumable")]))
        self.assertEqual(r.count("healthpack"), 1)

    def test_unconfirmed_action_masks_old_count(self):
        r = self.read(*self.pair(), event("CollectItems", 1, **item(count=1, Type="Component")))
        self.assertIsNone(r.count("graphene", "Backpack"))
        r = self.read(*self.pair(), event("CollectItems", 1, **item(count=1, Type="Component")),
                      snapshot("ShipLocker", 2, Components=[item(count=10)]),
                      snapshot("Backpack", 2, Components=[item(count=3)]))
        self.assertEqual(r.total_count, 13)

    def test_buy_old_and_new_sell(self):
        r = self.read(*self.pair(),
                      event("BuyMicroResources", 1, **item(count=3, Category="Component")),
                      event("BuyMicroResources", 2, MicroResources=[item(count=2, Category="Component")]),
                      event("SellMicroResources", 3, MicroResources=[item(count=4, Category="Component")]))
        self.assertEqual(r.count("graphene", "ShipLocker"), 11)

    def test_trade(self):
        r = self.read(*self.pair(), event("TradeMicroResources", 1,
                      Offered=[item(count=4, Category="Component")],
                      Received="microelectrode", Category="Component", Count=2))
        self.assertEqual(r.count("graphene", "ShipLocker"), 6)
        self.assertEqual(r.count("microelectrode"), 2)

    def test_upgrade_suit_and_weapon(self):
        for kind in ("UpgradeSuit", "UpgradeWeapon"):
            with self.subTest(kind=kind):
                r = self.read(*self.pair(), event(kind, 1, Resources=[dict(Name="graphene", Count=3)]))
                self.assertEqual(r.count("graphene"), 9)

    def test_odyssey_reward_excludes_ambiguous_data_and_horizons(self):
        r = self.read(*self.pair(), event("MissionCompleted", 1, MissionID=3, MaterialsReward=[
            dict(Name="newodysseydata", Category="$MICRORESOURCE_CATEGORY_Data;", Count=4),
            dict(Name="consumerfirmware", Category="Data", Count=9),
            dict(Name="sulphur", Category="Elements", Count=9)]))
        self.assertEqual(r.count("newodysseydata"), 4)
        self.assertFalse(any(s.key.name in ('consumerfirmware', 'sulphur') for s in r.rows))

    def test_mission_stacks_and_completion_preserved(self):
        records = [snapshot("ShipLocker", Items=[item("vehicleschematic", 2),
                   item("vehicleschematic", 1, MissionID=42)]), snapshot("Backpack"),
                   event("MissionCompleted", 1, MissionID=42)]
        r = self.read(*records)
        self.assertEqual(len(r.rows), 2)
        mission = next(row for row in r.rows if row.key.mission_id)
        self.assertEqual((mission.total, mission.mission_status), (1, 'completed'))
        r = self.read(*records, event("BuyMicroResources", 2,
                      Name="vehicleschematic", Count=3, Category="Item"))
        self.assertEqual(next(row.total for row in r.rows if row.key.mission_id), 1)
        self.assertEqual(r.count("vehicleschematic"), 6)

    def test_mission_status_never_deletes(self):
        for kind, status in (("MissionAccepted", "active"), ("MissionAbandoned", "abandoned"),
                             ("MissionFailed", "failed"), ("MissionRedirected", "unknown")):
            with self.subTest(kind=kind):
                r = self.read(snapshot("ShipLocker", Items=[item("thing", 1, MissionID=42)]),
                              snapshot("Backpack"), event(kind, 1, MissionID=42))
                self.assertEqual((r.rows[0].total, r.rows[0].mission_status), (1, status))

    def test_owner_stolen_are_distinct_from_mission(self):
        r = self.read(snapshot("ShipLocker", Items=[
            dict(Name="thing", Count=1, OwnerID=17, Stolen=True),
            dict(Name="thing", Count=2, OwnerID=0, Stolen=False),
            dict(Name="thing", Count=3, OwnerID=17, MissionID=12)]), snapshot("Backpack"))
        self.assertEqual(len(r.rows), 3)
        self.assertEqual(sum(row.key.mission_id is not None for row in r.rows), 1)

    def test_underflow_marks_unknown_and_snapshot_recovers(self):
        r = self.read(*self.pair(), event("BackpackChange", 1,
                      Removed=[item(count=20, Type="Component")]))
        self.assertIsNone(r.total_count)
        self.assertIn('underflow', r.containers['Backpack'].issues[-1])

    def test_unknown_and_ambiguous_sessions_ignored(self):
        for status in ('unknown', 'ambiguous'):
            r = self.reader.reconstruct(1, 'F1', [self.session(self.pair(), status=status)])
            self.assertFalse(r.known)

    def test_two_commanders_repeated_and_restart(self):
        a = self.session(self.pair() + [event('BackpackChange', 1,
                         Added=[item('missionthing', 1, Type='Item', MissionID=123)])])
        b = self.session([snapshot('ShipLocker', Data=[item('other', 90)]),
                          snapshot('Backpack', Items=[item('private', 7, MissionID=456)])],
                         name='b', commander=2, fid='F2')
        first = self.reader.reconstruct(1, 'F1', [a, b])
        other = self.reader.reconstruct(2, 'F2', [a, b])
        again = self.reader.reconstruct(1, 'F1', [a, b])
        self.assertEqual(first, again)
        self.assertEqual(first, OdysseyInventoryReader().reconstruct(1, 'F1', [a, b]))
        self.assertEqual((first.total_count, other.total_count), (13, 97))
        self.assertEqual(first.count('other'), 0)
        self.assertEqual(other.count('missionthing'), 0)

    def test_duplicate_rows_and_identical_archive_do_not_double_apply(self):
        records = self.pair() + [event('BackpackChange', 1, Added=[item(count=3, Type='Component')])]
        a = self.session(records)
        b = self.session(records, name='copy')
        self.assertEqual(self.reader.reconstruct(1, 'F1', [a, a, b]).total_count, 15)

    def test_same_source_reducer_once(self):
        reducer = OdysseyReducer(1, 'F1')
        for i, e in enumerate(self.pair()): reducer.apply(e, ('a', i))
        e = event('BackpackChange', 1, Added=[item(count=1, Type='Component')])
        reducer.apply(e, ('a', 2))
        reducer.apply(e, ('a', 2))
        self.assertEqual(reducer.result.total_count, 13)

    def test_sidecars_are_never_read(self):
        a = self.session(self.pair() + [event('Embark', 1),
                         snapshot('ShipLocker', 2, Components=[item(count=12)])])
        (Path(self.tmp.name) / 'Backpack.json').write_text(json.dumps(self.pair()[1]))
        self.assertEqual(self.reader.reconstruct(1, 'F1', [a]).total_count, 12)

    def test_real_faber38_synchronous_and_after_embark(self):
        records = json.loads((Path(__file__).parent / 'fixtures/odyssey_faber38.json').read_text())
        session = self.session(records, fid='FTEST0001')
        pair = self.reader.reconstruct(1, 'FTEST0001', [session], until='2026-09-08T14:58:01Z')
        after = self.reader.reconstruct(1, 'FTEST0001', [session])
        self.assertEqual(pair.total_count, 3139)
        self.assertEqual(after.total_count, 3139)
        self.assertEqual(pair.count('energycell', 'ShipLocker'), 97)
        self.assertEqual(pair.count('energycell', 'Backpack'), 3)
        self.assertEqual(after.count('energycell', 'Backpack'), 0)
        for name, count in dict(vehicleschematic=1, weaponschematic=31, suitschematic=11,
                                graphene=3, microelectrode=113, manufacturinginstructions=68,
                                weapontestdata=34, healthpack=100, energycell=100).items():
            self.assertEqual(pair.count(name), count, name)
            self.assertEqual(after.count(name), count, name)
        mission = next(row for row in after.rows if row.key.name == 'vehicleschematic')
        self.assertEqual((mission.key.mission_id, mission.mission_status, mission.total),
                         (1064707191, 'completed', 1))

    def test_canonical_names_and_unknown_symbol_retained(self):
        self.assertEqual(canonical_name('$FutureThing_Name;'), 'futurething')
        r = self.read(snapshot('ShipLocker', Items=[item('FutureThing')]), snapshot('Backpack'))
        self.assertEqual(r.rows[0].key.name, 'futurething')

    def test_bad_snapshot_does_not_create_zero(self):
        r = self.read(*self.pair(), event('Backpack', 1, Items=[]))
        self.assertIsNone(r.count('graphene', 'Backpack'))

    def test_identity_disagreement(self):
        a = self.session(self.pair(), fid='F2')
        a['fid_seen'] = 'F1'
        r = self.reader.reconstruct(1, 'F1', [a])
        self.assertFalse(r.known)
        self.assertTrue(r.issues)

    def test_cache_append_is_read(self):
        a = self.session(self.pair())
        first = self.reader.reconstruct(1, 'F1', [a])
        with Path(a['journal_file']).open('a') as handle:
            handle.write(json.dumps(event('BackpackChange', 1,
                         Added=[item(count=1, Type='Component')])) + '\n')
        self.assertEqual(first.total_count, 12)
        self.assertEqual(self.reader.reconstruct(1, 'F1', [a]).total_count, 13)

    def test_returned_state_cannot_poison_cached_result(self):
        a = self.session(self.pair())
        r = self.reader.reconstruct(1, 'F1', [a])
        r.containers['ShipLocker'].stacks.clear()
        self.assertEqual(self.reader.reconstruct(1, 'F1', [a]).total_count, 12)

    def test_attribution_change_invalidates_result_cache(self):
        a = self.session(self.pair())
        self.assertTrue(self.reader.reconstruct(1, 'F1', [a]).known)
        a['attribution_status'] = 'ambiguous'
        self.assertFalse(self.reader.reconstruct(1, 'F1', [a]).known)

    def test_ambiguous_owner_consumption_is_not_guessed(self):
        r = self.read(snapshot('ShipLocker', Components=[
            dict(Name='graphene', Count=4, OwnerID=1),
            dict(Name='graphene', Count=4, OwnerID=2)]), snapshot('Backpack'),
            event('UpgradeSuit', 1, Resources=[dict(Name='graphene', Count=1)]))
        self.assertIsNone(r.total_count)
        self.assertIn('ambiguous', r.containers['ShipLocker'].issues[-1])

    def test_consumption_cannot_take_mission_stack(self):
        r = self.read(snapshot('ShipLocker', Components=[item(count=4, MissionID=1)]),
                      snapshot('Backpack'), event('UpgradeSuit', 1,
                      Resources=[dict(Name='graphene', Count=1)]))
        self.assertIsNone(r.total_count)
        self.assertEqual(next(iter(r.containers['ShipLocker'].stacks.values())).count, 4)

    def test_delta_is_atomic(self):
        r = self.read(*self.pair(), event('BackpackChange', 1, Added=[
            item(count=1, Type='Component'), item('bad', -1, Type='Component')]))
        self.assertIsNone(r.total_count)
        self.assertEqual(sum(s.count for s in r.containers['Backpack'].stacks.values()), 2)

    def test_different_timestamp_action_not_silently_confirmed(self):
        r = self.read(*self.pair(), event('CollectItems', 1, **item(count=1, Type='Component')),
                      event('BackpackChange', 2, Added=[item(count=1, Type='Component')]))
        self.assertIsNone(r.total_count)

    def test_two_identical_actions_require_two_confirmations(self):
        e = event('CollectItems', 1, **item(count=1, Type='Component'))
        d = event('BackpackChange', 1, Added=[item(count=1, Type='Component')])
        self.assertIsNone(self.read(*self.pair(), e, e, d).total_count)
        self.assertEqual(self.read(*self.pair(), e, e, d, d).total_count, 14)

    def test_transfer_and_death_wait_for_snapshots(self):
        for kind in ('TransferMicroResources', 'Died', 'Resurrect'):
            with self.subTest(kind=kind):
                r = self.read(*self.pair(), event(kind, 1))
                self.assertIsNone(r.total_count)
                self.assertFalse(any(c.known for c in r.containers.values()))

    def test_drop_is_observation_not_second_delta(self):
        r = self.read(*self.pair(), event('DropItems', 1, **item(count=1, Type='Component')),
                      event('BackpackChange', 1, Removed=[item(count=1, Type='Component')]))
        self.assertEqual(r.total_count, 11)

    def test_mission_sentinel_is_not_a_mission(self):
        r = self.read(snapshot('ShipLocker', Items=[item('thing', 1,
                       MissionID=18446744073709551615)]), snapshot('Backpack'))
        self.assertIsNone(r.rows[0].key.mission_id)

    def test_missing_file_masks_inventory(self):
        a = self.session(self.pair())
        b = self.session([], name='missing')
        Path(b['journal_file']).unlink()
        r = self.reader.reconstruct(1, 'F1', [a, b])
        self.assertIsNone(r.total_count)
        self.assertIsNone(r.rows[0].locker)

    def test_conflicting_duplicate_session_row_excludes_file(self):
        a = self.session(self.pair())
        b = dict(a, attribution_status='ambiguous')
        self.assertFalse(self.reader.reconstruct(1, 'F1', [a, b]).known)

    def test_display_names_are_not_identity(self):
        r = self.read(snapshot('ShipLocker', Components=[
            item(Name_Localised='Graphen')]), snapshot('Backpack'))
        self.assertEqual((r.rows[0].key.name, r.rows[0].display_name), ('graphene', 'Graphen'))
