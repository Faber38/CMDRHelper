"""Safe composition binding across a same-ship on-foot round trip."""
import json
import unittest
from datetime import timedelta
from unittest.mock import patch
from cmdrhelper.ship_cargo import current_ship_inventory, CARGO_MUTATIONS
from cmdrhelper.state import AppState
from tests import test_ship_cargo as helpers
from tests.test_ship_cargo import event, loadout, cargo, status


class InventoryTests(unittest.TestCase):
    setUp = helpers.ShipCargoTests.setUp
    replay = helpers.ShipCargoTests.replay

    def snapshot(self, inline=True):
        row = cargo(8, inline=inline)
        if inline:
            row['Inventory'] = [dict(Name='jaquesquinentianstill', Count=8, Stolen=0)]
        return row

    def base(self, inline=True):
        return [loadout(20, 24), self.snapshot(inline)]

    def roundtrip(self, second=10):
        return [event('Disembark', second, ID=20, SRV=False, Taxi=False, Multicrew=False),
                event('Embark', second+1, ID=20, SRV=False, Taxi=False, Multicrew=False),
                loadout(20, 24, second+2)]

    def test_snapshot_and_twice_same_ship_return(self):
        for tail in ([], self.roundtrip(), self.roundtrip()+self.roundtrip(20)):
            with self.subTest(tail=tail):
                s, _ = self.replay(self.base()+tail, status(8))
                inv = current_ship_inventory(s)
                self.assertEqual(inv['ship_id'], 20)
                self.assertEqual(inv['count'], 8)
                self.assertEqual(inv['inventory'][0]['frontier_name'], 'jaquesquinentianstill')
                self.assertEqual(inv['inventory'][0]['count'], 8)
                self.assertEqual(s.ship_loadout.cargo_capacity, 24)

    def test_restart_matching_sidecar_after_two_roundtrips(self):
        (self.folder/'Cargo.json').write_text(json.dumps(self.snapshot()))
        rows = self.base(False)+self.roundtrip()+self.roundtrip(20)
        first, _ = self.replay(rows)
        restarted, _ = self.replay(rows)
        self.assertEqual(current_ship_inventory(first), current_ship_inventory(restarted))
        self.assertEqual(current_ship_inventory(restarted)['count'], 8)
        self.assertIn('revalidated_at', current_ship_inventory(restarted)['context'])

    def test_return_requires_explicit_same_id_and_loadout(self):
        tails = [self.roundtrip()[:1], self.roundtrip()[:2],
                 [*self.roundtrip()[:2], loadout(21, 24, 12)],
                 [event('ShipyardSwap', 10, ShipID=21), loadout(21, 24, 11)],
                 [event('Disembark', 10), *self.roundtrip()[1:]],
                 [self.roundtrip()[0], event('Embark', 11, ID=21), loadout(20, 24, 12)],
                 [self.roundtrip()[0], event('Embark', 11, ID=20, Taxi=True), loadout(20, 24, 12)]]
        for tail in tails:
            with self.subTest(tail=tail):
                s, _ = self.replay(self.base()+tail, status(8))
                self.assertIsNone(current_ship_inventory(s))

    def test_every_mutation_while_away_blocks_restoration(self):
        changes = [event(k, 10, Type='gold', Count=1) for k in CARGO_MUTATIONS]
        changes += [cargo(0, 10, 'SRV'), event('LoadGame', 10, FID='F-A', ShipID=20, Ship='cobramkv')]
        for change in changes:
            with self.subTest(change=change):
                tail = self.roundtrip()
                s, _ = self.replay(self.base()+[tail[0], change]+tail[1:], status(8))
                self.assertIsNone(current_ship_inventory(s))

    def test_status_only_cannot_invent_inventory(self):
        s, _ = self.replay([loadout(20, 24)], status(8))
        self.assertIsNone(current_ship_inventory(s))
        s, _ = self.replay(self.base(), status(8))
        self.assertEqual(current_ship_inventory(s)['count'], 8)
        s._cargo_status = status(9)
        self.assertIsNone(current_ship_inventory(s))

    def test_status_conflict_does_not_expire_or_survive_a_new_snapshot(self):
        s, _ = self.replay(self.base(), status(9))
        self.assertIsNone(current_ship_inventory(s))
        with patch("cmdrhelper.ship_cargo.utc_now", return_value=helpers.NOW + timedelta(days=1)):
            self.assertIsNone(current_ship_inventory(s))
        s, _ = self.replay(self.base()+self.roundtrip(), state=s)
        self.assertIsNone(current_ship_inventory(s))
        s, _ = self.replay(self.base()+[cargo(9, 30)], state=s)
        self.assertEqual(current_ship_inventory(s)["count"], 9)

    def test_empty_is_known_and_commander_guard_remains(self):
        s, _ = self.replay([loadout(20, 24), cargo(0)])
        self.assertEqual(current_ship_inventory(s)['inventory'], [])
        s.commander_fid = 'other'
        self.assertIsNone(current_ship_inventory(s))

    def test_live_poll_publishes_and_invalidates_inventory(self):
        s, _ = self.replay(self.base())
        AppState._poll_ship_cargo(s)
        self.assertEqual(s.ship_inventory['count'], 8)
        s, _ = self.replay(self.base()+[event('MarketSell', 10, Type='jaquesquinentianstill', Count=8)], state=s)
        AppState._poll_ship_cargo(s)
        self.assertIsNone(s.ship_inventory)
        s, _ = self.replay(self.base()+[cargo(0, 11)], state=s)
        AppState._poll_ship_cargo(s)
        self.assertEqual(s.ship_inventory['count'], 0)
