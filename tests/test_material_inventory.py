import json
import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from cmdrhelper.material_inventory import MaterialInventoryReader, _Reducer
from cmdrhelper.material_catalog import get_material, merge_inventory


def event(kind, second=0, **fields):
    return dict(timestamp=f"2026-09-08T10:00:{second:02d}Z", event=kind, **fields)


def snapshot(second=1, raw=10, manufactured=8, encoded=6):
    return event("Materials", second,
                 Raw=[dict(Name="sulphur", Name_Localised="Schwefel", Count=raw)],
                 Manufactured=[dict(Name="gridresistors", Count=manufactured)],
                 Encoded=[dict(Name="consumerfirmware", Count=encoded)])


class MaterialInventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.reader = MaterialInventoryReader()

    def session(self, name="one", commander=1, fid="F1", events=None, status="identified"):
        path = Path(self.tmp.name) / (name + ".log")
        records = [event("Commander", FID=fid)] + (events or [])
        path.write_text("".join(json.dumps(e) + "\n" for e in records))
        return dict(journal_file=str(path), commander_id=commander, fid_seen=fid,
                    attribution_status=status, last_read_offset=0)

    def read(self, *events):
        return self.reader.reconstruct(1, "F1", [self.session(events=list(events))])

    def test_portable_reference_original_material_events(self):
        fixture = Path(__file__).parent / "fixtures" / "materials_reference.json"
        events = json.loads(fixture.read_text())
        session = self.session(fid="FTEST0001", events=events)
        result = self.reader.reconstruct(1, "FTEST0001", [session])
        self.assertTrue(result.known, result.issues)
        self.assertEqual(result.snapshot_timestamp, "2016-09-10T10:37:28Z")
        for name, count in dict(sulphur=300, vanadium=244, tin=53,
                                molybdenum=63, niobium=53, yttrium=35).items():
            self.assertEqual(result.material(name).count, count, name)
        self.assertEqual([len(result.by_category(k)) for k in
                          ("Raw", "Manufactured", "Encoded")], [28, 56, 35])
        self.assertEqual([sum(stock.count > 0 for stock in result.by_category(k).values())
                          for k in ("Raw", "Manufactured", "Encoded")], [28, 56, 34])
        self.assertEqual(result.material("dataminedwake").count, 0)
        self.assertEqual(result, MaterialInventoryReader().reconstruct(1, "FTEST0001", [session]))

    def test_explicit_zero_and_empty_snapshot(self):
        result = self.read(snapshot(raw=0))
        self.assertTrue(result.material("sulphur").known)
        self.assertEqual(result.material("sulphur").count, 0)
        empty = self.read(event("Materials", 1, Raw=[], Manufactured=[], Encoded=[]))
        self.assertTrue(empty.known)
        self.assertFalse(empty.material("sulphur").known)

    def test_data_reward_requires_encoded_identity(self):
        result = self.read(snapshot(), event("MissionCompleted", 2, MaterialsReward=[
            dict(Name="sulphur", Category="Data", Count=7),
            dict(Name="unknown_data", Category="Data", Count=3)]))
        self.assertEqual(result.material("sulphur").count, 10)
        self.assertFalse(result.material("unknown_data").known)

    def test_complete_snapshot(self):
        result = self.read(snapshot())
        self.assertTrue(result.known)
        self.assertEqual((result.commander_id, result.fid), (1, "F1"))
        self.assertEqual(result.snapshot_timestamp, snapshot()["timestamp"])
        self.assertEqual(result.material("sulphur").count, 10)
        self.assertEqual(result.material("sulphur").display_name, "Schwefel")
        self.assertEqual([len(result.by_category(k)) for k in ("Raw", "Manufactured", "Encoded")], [1, 1, 1])

    def test_snapshot_replacement_and_known_zero(self):
        new = event("Materials", 3, Raw=[], Manufactured=[], Encoded=[])
        result = self.read(snapshot(), event("MaterialCollected", 2, Category="Raw", Name="tin", Count=3), new)
        self.assertTrue(result.material("tin").known)
        self.assertEqual(result.material("tin").count, 0)
        self.assertEqual(result.material("sulphur").count, 0)
        self.assertIsNone(result.material("never_seen").count)
        self.assertFalse(result.material("never_seen").known)

    def test_no_snapshot_is_unknown(self):
        result = self.read(event("MaterialCollected", 2, Category="Raw", Name="tin", Count=3))
        self.assertFalse(result.known)
        self.assertIsNone(result.material("tin").count)

    def test_collected_exact_quantity_and_internal_name(self):
        result = self.read(snapshot(), event("MaterialCollected", 2, Category="raw", Name="$SULPHUR_Name;", Name_Localised="Changed display", Count=3))
        self.assertEqual(result.material("sulphur").count, 13)
        self.assertEqual(result.last_change["changes"][0]["delta"], 3)
        self.assertNotIn("Changed display", result.stocks)

    def test_collected_respects_catalog_capacity_and_effective_delta(self):
        for initial, amount, expected in ((40, 12, 52), (99, 6, 100),
                                          (90, 15, 100), (100, 12, 100)):
            with self.subTest(initial=initial, amount=amount):
                collected = event("MaterialCollected", 2, Category="Encoded",
                                  Name="adaptiveencryptors", Count=amount)
                result = self.read(event("Materials", 1, Raw=[], Manufactured=[],
                    Encoded=[dict(Name="adaptiveencryptors", Count=initial)]), collected)
                self.assertTrue(result.known, result.issues)
                self.assertEqual(result.material("adaptiveencryptors").count, expected)
                self.assertEqual(collected["Count"], amount)
                if expected == initial:
                    self.assertIsNone(result.last_change)
                else:
                    self.assertEqual(result.last_change["changes"][0]["delta"], expected - initial)

    def test_collected_real_trade_sequence_replay_and_restart(self):
        records = [event("Materials", 1, Raw=[], Manufactured=[],
                         Encoded=[dict(Name="adaptiveencryptors", Count=100)])]
        for second, (paid, received, name) in enumerate([
                (6, 54, "symmetrickeys"), (4, 36, "symmetrickeys"),
                (50, 75, "scandatabanks"), (40, 60, "shielddensityreports")], 2):
            records.append(event("MaterialTrade", second,
                Paid=dict(Material="adaptiveencryptors", Category="Encoded", Quantity=paid),
                Received=dict(Material=name, Category="Encoded", Quantity=received)))
        traded = self.read(*records)
        self.assertEqual(traded.material("adaptiveencryptors").count, 0)
        self.assertEqual(traded.material("symmetrickeys").count, 90)
        self.assertEqual(traded.material("scandatabanks").count, 75)
        self.assertEqual(traded.material("shielddensityreports").count, 60)
        records.extend(event("MaterialCollected", second, Category="Encoded",
                             Name="adaptiveencryptors", Count=amount)
                       for second, amount in enumerate((12, 12, 18, 15, 18, 15, 12), 6))
        session = self.session(events=records)
        result = self.reader.reconstruct(1, "F1", [session])
        self.assertTrue(result.known, result.issues)
        self.assertEqual(result.material("adaptiveencryptors").count, 100)
        self.assertEqual(result.last_change["changes"][0]["delta"], 10)
        row = next(row for row in merge_inventory(result)
                   if row.material.symbol == "adaptiveencryptors")
        self.assertEqual((row.count, row.material.maximum, row.percent), (100, 100, 100.0))
        self.assertEqual(result, self.reader.reconstruct(1, "F1", [session, session]))
        self.assertEqual(result, MaterialInventoryReader().reconstruct(1, "F1", [session]))

    def test_collected_uses_other_catalog_maxima(self):
        result = self.read(snapshot(raw=299), event("MaterialCollected", 2,
                           Category="Raw", Name="$SULPHUR_Name;", Count=6))
        self.assertEqual(result.material("sulphur").count, 300)
        self.assertEqual(result.last_change["changes"][0]["delta"], 1)

    def test_collected_without_reliable_maximum_is_not_limited(self):
        for name in ("unknown_material", "tg_shipsystemsdata"):
            with self.subTest(name=name):
                result = self.read(event("Materials", 1, Raw=[], Manufactured=[],
                    Encoded=[dict(Name=name, Count=99)]),
                    event("MaterialCollected", 2, Category="Encoded", Name=name, Count=6))
                self.assertTrue(result.known, result.issues)
                self.assertEqual(result.material(name).count, 105)
                self.assertEqual(result.last_change["changes"][0]["delta"], 6)

    def test_snapshot_remains_authoritative_after_limited_collection(self):
        for replacement in (73, 100, 105):
            with self.subTest(replacement=replacement):
                result = self.read(event("Materials", 1, Raw=[], Manufactured=[],
                    Encoded=[dict(Name="adaptiveencryptors", Count=99)]),
                    event("MaterialCollected", 2, Category="Encoded", Name="adaptiveencryptors", Count=6),
                    event("Materials", 3, Raw=[], Manufactured=[],
                          Encoded=[dict(Name="adaptiveencryptors", Count=replacement)]))
                self.assertEqual(result.material("adaptiveencryptors").count, replacement)
                self.assertIsNone(result.last_change)

    def test_collection_does_not_reduce_over_capacity_snapshot(self):
        result = self.read(event("Materials", 1, Raw=[], Manufactured=[],
            Encoded=[dict(Name="adaptiveencryptors", Count=105)]),
            event("MaterialCollected", 2, Category="Encoded", Name="adaptiveencryptors", Count=6))
        self.assertEqual(result.material("adaptiveencryptors").count, 105)
        self.assertIsNone(result.last_change)

    def test_other_positive_events_keep_exact_quantities(self):
        initial = event("Materials", 1, Raw=[dict(Name="sulphur", Count=10)], Manufactured=[],
                        Encoded=[dict(Name="adaptiveencryptors", Count=99)])
        for change in (
                event("MissionCompleted", 2, MaterialsReward=[
                    dict(Name="adaptiveencryptors", Category="Encoded", Count=6)]),
                event("MaterialTrade", 2,
                    Paid=dict(Material="sulphur", Category="Raw", Quantity=1),
                    Received=dict(Material="adaptiveencryptors", Category="Encoded", Quantity=6))):
            with self.subTest(event=change["event"]):
                result = self.read(initial, change)
                self.assertEqual(result.material("adaptiveencryptors").count, 105)

    def test_discarded_to_zero(self):
        result = self.read(snapshot(), event("MaterialDiscarded", 2, Category="Raw", Name="sulphur", Count=10))
        self.assertEqual(result.material("sulphur").count, 0)
        self.assertTrue(result.material("sulphur").known)

    def test_trade(self):
        result = self.read(snapshot(), event("MaterialTrade", 2,
            Paid=dict(Material="sulphur", Category="Raw", Quantity=2),
            Received=dict(Material="tin", Category="Raw", Quantity=6)))
        self.assertEqual(result.material("sulphur").count, 8)
        self.assertEqual(result.material("tin").count, 6)

    def test_engineer_craft(self):
        result = self.read(snapshot(), event("EngineerCraft", 2, Level=5,
            Ingredients=[dict(Name="GridResistors", Count=2), dict(Name="consumerfirmware", Count=1)]))
        self.assertEqual(result.material("gridresistors").count, 6)
        self.assertEqual(result.material("consumerfirmware").count, 5)

    def test_synthesis(self):
        result = self.read(snapshot(), event("Synthesis", 2, Materials=[dict(Name="sulphur", Count=3)]))
        self.assertEqual(result.material("sulphur").count, 7)

    def test_engineering_rewards_and_odyssey_exclusion(self):
        result = self.read(snapshot(), event("MissionCompleted", 2, MaterialsReward=[
            dict(Name="Sulphur", Category="$MICRORESOURCE_CATEGORY_Elements;", Count=9),
            dict(Name="GridResistors", Category="$MICRORESOURCE_CATEGORY_Manufactured;", Count=12),
            dict(Name="ConsumerFirmware", Category="$MICRORESOURCE_CATEGORY_Data;", Count=2),
            dict(Name="WeaponTestData", Category="$MICRORESOURCE_CATEGORY_Data;", Count=15),
            dict(Name="TitaniumPlating", Category="$MICRORESOURCE_CATEGORY_Component;", Count=11),
            dict(Name="CompressionLiquefiedGas", Category="$MICRORESOURCE_CATEGORY_Item;", Count=7)]))
        self.assertTrue(result.known)
        self.assertEqual(result.material("sulphur").count, 19)
        self.assertEqual(result.material("gridresistors").count, 20)
        self.assertEqual(result.material("consumerfirmware").count, 8)
        self.assertEqual(len(result.stocks), 3)

    def test_engineer_contribution_quantity_not_total(self):
        result = self.read(snapshot(), event("EngineerContribution", 2, Type="Materials", Material="gridresistors", Quantity=3, TotalQuantity=50),
                           event("EngineerContribution", 3, Type="Commodity", Commodity="osmium", Quantity=10))
        self.assertEqual(result.material("gridresistors").count, 5)
        self.assertNotIn("osmium", result.stocks)

    def test_underflow_is_isolated_and_trade_receipt_processed(self):
        with self.assertLogs("cmdrhelper.material_inventory", level="WARNING"):
            result = self.read(snapshot(), event("MaterialTrade", 2,
                Paid=dict(Material="sulphur", Category="Raw", Quantity=11),
                Received=dict(Material="tin", Category="Raw", Quantity=6)))
        self.assertFalse(result.known)
        self.assertIn("underflow", result.material_issues["sulphur"][0])
        self.assertIsNone(result.material("sulphur").count)
        self.assertEqual(result.material("tin").count, 6)
        self.assertEqual(result.material("gridresistors").count, 8)
        self.assertTrue(all(stock.count is None or stock.count >= 0 for stock in result.stocks.values()))

    def test_invalid_snapshot_does_not_replace_and_later_valid_recovers(self):
        bad = event("Materials", 2, Raw=[])
        with self.assertLogs("cmdrhelper.material_inventory", level="WARNING"):
            result = self.read(snapshot(), bad)
        self.assertFalse(result.known)
        self.assertEqual(result.snapshot_timestamp, snapshot()["timestamp"])
        with self.assertLogs("cmdrhelper.material_inventory", level="WARNING"):
            result = self.read(snapshot(), bad, snapshot(3, raw=2))
        self.assertTrue(result.known)
        self.assertEqual(result.material("sulphur").count, 2)

    def test_real_20261007_craft_underflow_and_restart(self):
        # Material fields copied from the real snapshot and craft sequence;
        # no commander identity, location or other personal journal fields.
        records = json.loads((Path(__file__).parent / "fixtures" /
                              "materials_underflow_20261007.json").read_text())
        initial = {item["Name"]: item["Count"] for cat in
                   ("Raw", "Manufactured", "Encoded") for item in records[0][cat]}
        session = self.session(events=records)
        with self.assertLogs("cmdrhelper.material_inventory", level="WARNING") as logs:
            result = self.reader.reconstruct(1, "F1", [session])
        self.assertEqual(len(logs.output), 2)
        self.assertEqual(set(result.material_issues), {"configurablecomponents"})
        self.assertEqual(len(result.material_issues["configurablecomponents"]), 2)
        self.assertIn("underflow", logs.output[0])
        self.assertIn("remains unknown", logs.output[1])
        self.assertEqual(result.issues, [])
        self.assertFalse(result.material("configurablecomponents").known)
        self.assertIsNone(result.material("configurablecomponents").count)
        expected = dict(initial)
        for craft in records[1:]:
            for item in craft["Ingredients"]:
                if item["Name"] != "configurablecomponents":
                    expected[item["Name"]] -= item["Count"]
        for name, count in expected.items():
            if name != "configurablecomponents":
                self.assertTrue(result.material(name).known, name)
                self.assertEqual(result.material(name).count, count, name)
        rows = merge_inventory(result)
        self.assertEqual([r.material.symbol for r in rows if not r.known],
                         ["configurablecomponents"])
        self.assertEqual(sum(r.known for r in rows), 145)
        self.assertTrue(all(r.count is None or r.count >= 0 for r in rows))
        self.assertEqual(result.last_change["timestamp"], records[-1]["timestamp"])
        with self.assertLogs("cmdrhelper.material_inventory", level="WARNING"):
            self.assertEqual(result, MaterialInventoryReader().reconstruct(1, "F1", [session]))

    def test_unknown_material_stays_unknown_through_all_delta_types(self):
        deltas = [
            event("MaterialCollected", 3, Name="sulphur", Category="Raw", Count=20),
            event("MaterialDiscarded", 4, Name="sulphur", Category="Raw", Count=1),
            event("MaterialTrade", 5,
                  Paid=dict(Material="gridresistors", Category="Manufactured", Quantity=1),
                  Received=dict(Material="sulphur", Category="Raw", Quantity=10)),
            event("MissionCompleted", 6, MaterialsReward=[dict(Name="sulphur", Category="Raw", Count=10)]),
            event("Synthesis", 7, Materials=[dict(Name="sulphur", Count=1)]),
            event("EngineerContribution", 8, Type="Materials", Material="sulphur", Quantity=1),
            event("EngineerCraft", 9, Ingredients=[dict(Name="sulphur", Count=1),
                                                    dict(Name="consumerfirmware", Count=1)]),
        ]
        records = [snapshot(), event("MaterialDiscarded", 2, Name="sulphur", Category="Raw", Count=11)]
        for delta in deltas:
            records.append(delta)
            with self.assertLogs("cmdrhelper.material_inventory", level="WARNING"):
                result = self.read(*records)
            self.assertIsNone(result.material("sulphur").count)
            self.assertFalse(result.material("sulphur").known)
        self.assertEqual(result.material("gridresistors").count, 7)
        self.assertEqual(result.material("consumerfirmware").count, 5)
        for replacement in (snapshot(10, raw=4), event("Materials", 10, Raw=[], Manufactured=[], Encoded=[])):
            with self.assertLogs("cmdrhelper.material_inventory", level="WARNING"):
                restored = self.read(*records, replacement)
            self.assertTrue(restored.known)
            self.assertEqual(restored.material_issues, {})
            self.assertTrue(restored.material("sulphur").known)
            self.assertEqual(restored.material("sulphur").count, 4 if replacement["Raw"] else 0)

    def test_underflow_in_each_category_leaves_other_ingredients_known(self):
        for name in ("sulphur", "gridresistors", "consumerfirmware"):
            with self.subTest(name=name), self.assertLogs("cmdrhelper.material_inventory", level="WARNING"):
                result = self.read(snapshot(), event("EngineerCraft", 2, Ingredients=[
                    dict(Name=name, Count=100),
                    *[dict(Name=n, Count=1) for n in ("sulphur", "gridresistors", "consumerfirmware") if n != name]]))
            for other, count in (("sulphur", 9), ("gridresistors", 7), ("consumerfirmware", 5)):
                self.assertEqual(result.material(other).count, None if other == name else count)
            self.assertEqual(sum(r.known for r in merge_inventory(result)), 145)

    def test_invalid_quantity_and_unknown_ingredient(self):
        for change in [event("MaterialCollected", 2, Name="tin", Category="Raw", Count=-1),
                       event("MaterialCollected", 2, Name="tin", Category="Raw", Count=1.5),
                       event("Synthesis", 2, Materials=[dict(Name="unclassified", Count=1)])]:
            with self.subTest(change=change), self.assertLogs("cmdrhelper.material_inventory", level="WARNING"):
                self.assertFalse(self.read(snapshot(), change).known)

    def test_two_commanders_remain_fully_separate(self):
        one = self.session("one", 1, "F1", [snapshot(raw=10), event("MaterialCollected", 2, Category="Raw", Name="tin", Count=3),
            event("EngineerCraft", 4, Ingredients=[dict(Name="gridresistors", Count=2)])])
        two = self.session("two", 2, "F2", [snapshot(raw=90, manufactured=40, encoded=30),
            event("MaterialDiscarded", 2, Category="Raw", Name="sulphur", Count=20),
            event("MaterialCollected", 3, Category="Raw", Name="yttrium", Count=7),
            event("Synthesis", 4, Materials=[dict(Name="consumerfirmware", Count=4)])])
        sessions = [two, one]
        first = self.reader.reconstruct(1, "F1", sessions)
        second = self.reader.reconstruct(2, "F2", sessions)
        self.assertEqual([first.material(n).count for n in ("sulphur", "gridresistors", "consumerfirmware", "tin", "yttrium")], [10, 6, 6, 3, None])
        self.assertEqual([second.material(n).count for n in ("sulphur", "gridresistors", "consumerfirmware", "tin", "yttrium")], [70, 40, 26, None, 7])
        self.assertEqual(first, self.reader.reconstruct(1, "F1", sessions))
        self.assertEqual(second, MaterialInventoryReader().reconstruct(2, "F2", sessions))
        self.assertFalse(self.reader.reconstruct(1, "F2", sessions).known)

    def test_unknown_ambiguous_and_wrong_identity_ignored(self):
        good = self.session("good", events=[snapshot()])
        unknown = self.session("unknown", events=[snapshot(5, raw=99)], status="unknown")
        ambiguous = self.session("ambiguous", events=[snapshot(6, raw=88)], status="ambiguous")
        result = self.reader.reconstruct(1, "F1", [good, unknown, ambiguous])
        self.assertEqual(result.material("sulphur").count, 10)
        wrong = self.session("wrong", fid="F2", events=[snapshot()])
        wrong["fid_seen"] = "F1"
        result = self.reader.reconstruct(1, "F1", [good, wrong])
        self.assertFalse(result.known)
        self.assertIn("identity", result.issues[0])

    def test_duplicate_sessions_and_event_delivery(self):
        session = self.session(events=[snapshot(), event("MaterialCollected", 2, Name="tin", Category="Raw", Count=3)])
        first = self.reader.reconstruct(1, "F1", [session])
        self.assertEqual(first, self.reader.reconstruct(1, "F1", [session, session]))
        reducer = _Reducer(1, "F1")
        reducer.apply(snapshot(), ("file", 10))
        collected = event("MaterialCollected", 2, Name="tin", Category="Raw", Count=3)
        reducer.apply(collected, ("file", 100))
        reducer.apply(collected, ("file", 100))
        reducer.apply(collected, ("file", 200))  # Same timestamp/payload, distinct real line.
        self.assertEqual(reducer.result.material("tin").count, 6)

    def test_append_partial_tail_restart_and_cache(self):
        session = self.session(events=[snapshot()])
        first = self.reader.reconstruct(1, "F1", [session])
        path = Path(session["journal_file"])
        with path.open("a") as handle:
            handle.write(json.dumps(event("MaterialCollected", 2, Name="tin", Category="Raw", Count=3)))
        self.assertEqual(first, self.reader.reconstruct(1, "F1", [session]))
        with path.open("a") as handle:
            handle.write("\n")
        updated = self.reader.reconstruct(1, "F1", [session])
        self.assertEqual(updated.material("tin").count, 3)
        self.assertEqual(updated, MaterialInventoryReader().reconstruct(1, "F1", [session]))

    def test_missing_or_corrupt_file_is_not_known_zero(self):
        session = self.session(events=[snapshot()])
        path = Path(session["journal_file"])
        with path.open("a") as handle:
            handle.write("not json\n")
        self.assertFalse(self.reader.reconstruct(1, "F1", [session]).known)
        path.unlink()
        self.assertFalse(self.reader.reconstruct(1, "F1", [session]).known)

    def test_chronological_order_not_input_order(self):
        later = self.session("later", events=[event("MaterialCollected", 5, Name="sulphur", Category="Raw", Count=2)])
        earlier = self.session("earlier", events=[snapshot()])
        self.assertEqual(self.reader.reconstruct(1, "F1", [later, earlier]).material("sulphur").count, 12)


class RealMaterialInventoryTests(unittest.TestCase):
    def test_reference_original_journals(self):
        database_path = os.environ.get("CMDRHELPER_TEST_DATABASE")
        commander_name = os.environ.get("CMDRHELPER_TEST_COMMANDER")
        journal_until = os.environ.get("CMDRHELPER_TEST_JOURNAL_UNTIL")
        if not all((database_path, commander_name, journal_until)):
            self.skipTest("opt-in reference DB test: set CMDRHELPER_TEST_DATABASE, "
                          "CMDRHELPER_TEST_COMMANDER and CMDRHELPER_TEST_JOURNAL_UNTIL")
        database = Path(database_path).expanduser().resolve()
        self.assertTrue(database.is_file(), "configured reference database unavailable")
        with sqlite3.connect(database.as_uri() + "?mode=ro&immutable=1", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            commander = connection.execute("SELECT id,fid FROM commanders WHERE current_name=? COLLATE NOCASE", (commander_name,)).fetchone()
            self.assertIsNotNone(commander, "configured reference commander unavailable")
            sessions = [dict(row) for row in connection.execute(
                "SELECT * FROM journal_sessions WHERE commander_id=? ORDER BY journal_file",
                (commander["id"],)) if Path(row["journal_file"]).name <= journal_until]
        self.assertTrue(sessions, "no reference sessions selected")
        self.assertTrue(all(Path(s["journal_file"]).is_file() for s in sessions),
                        "configured reference journals unavailable")
        reader = MaterialInventoryReader()
        started = time.perf_counter()
        result = reader.reconstruct(commander[0], commander["fid"], sessions)
        cold = time.perf_counter() - started
        started = time.perf_counter()
        again = reader.reconstruct(commander[0], commander["fid"], sessions)
        warm = time.perf_counter() - started
        self.assertEqual(result, again)
        self.assertTrue(result.known, result.issues)
        for name, count in dict(sulphur=300, vanadium=244, tin=53, molybdenum=63, niobium=53, yttrium=35).items():
            self.assertEqual(result.material(name).count, count, name)
        self.assertEqual([len(result.by_category(k)) for k in ("Raw", "Manufactured", "Encoded")], [28, 56, 35])
        self.assertEqual(result.material("dataminedwake").count, 0)
        self.assertEqual([sum(s.count > 0 for s in result.by_category(k).values()) for k in ("Raw", "Manufactured", "Encoded")], [28, 56, 34])
        for symbol, stock in result.stocks.items():
            self.assertIsNotNone(get_material(symbol), symbol)
            self.assertEqual(get_material(symbol).category, stock.category)
        started = time.perf_counter()
        rows = {row.material.symbol: row for row in merge_inventory(result)}
        projection = time.perf_counter() - started
        self.assertEqual(len(rows), 146)
        self.assertEqual(rows["vanadium"].percent, 97.6)
        self.assertEqual(rows["vanadium"].material.maximum, 250)
        self.assertEqual(rows["dataminedwake"].count, 0)
        self.assertEqual(sum(row.count == 0 for row in rows.values()), 28)
        self.assertTrue(all(rows[s].count == 0 for s in rows if s not in result.stocks))
        self.assertEqual(tuple(rows.values()), merge_inventory(again))
        print(f"\nReference: {len(sessions)} journals; cold={cold:.3f}s warm={warm:.3f}s")
        print(f"Catalog: {len(rows)} rows; projection={projection * 1000:.3f}ms; vanadium=244/250 (97.6%)")
