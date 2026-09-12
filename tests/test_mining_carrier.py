import json
from pathlib import Path
import tempfile
import unittest

from PySide6.QtCore import QSettings
from cmdrhelper.mining_carrier import CarrierLedger, read_carrier_feed
from cmdrhelper.mining_inventory import MiningInventory


class CarrierLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.path = self.folder / "Journal.log"
        self.ini = str(self.folder / "settings.ini")
        self.events = [dict(event="Commander", FID="F1"),
                       dict(event="Docked", MarketID=123, StationType="FleetCarrier")]
        self.settings = QSettings(self.ini, QSettings.Format.IniFormat)
        self.store = CarrierLedger(self.settings)

    def feed(self):
        self.path.write_text("".join(json.dumps(e) + "\n" for e in self.events))
        return read_carrier_feed(self.path, "F1")

    def confirm(self, count=504):
        return self.store.confirm("F1", 123, "gold", count, self.feed())

    def transfer(self, amount, direction, **extra):
        self.events.append(dict(event="CargoTransfer", Transfers=[dict(Type="gold", Count=amount,
                                                                       Direction=direction)], **extra))
        return self.store.update("F1", 123, self.feed())

    def test_manual_baseline_restart_deltas_and_duplicate_suppression(self):
        # Historical transfers do not supply or modify an opening balance.
        self.transfer(200, "tocarrier")
        ledger = self.confirm()
        self.assertEqual(ledger["records"]["gold"]["count"], 504)
        self.assertEqual(ledger["records"]["gold"]["status"], "manual")
        self.store = CarrierLedger(QSettings(self.ini, QSettings.Format.IniFormat))
        ledger = self.store.update("F1", 123, self.feed())
        self.assertEqual(ledger["records"]["gold"]["count"], 504)
        ledger = self.transfer(50, "toship")
        self.assertEqual(ledger["records"]["gold"]["count"], 454)
        ledger = self.transfer(20, "tocarrier")
        self.assertEqual(ledger["records"]["gold"]["count"], 474)
        self.assertEqual(ledger["records"]["gold"]["status"], "tracked")
        again = self.store.update("F1", 123, self.feed())
        self.assertEqual(again, ledger)
        self.store = CarrierLedger(QSettings(self.ini, QSettings.Format.IniFormat))
        self.assertEqual(self.store.update("F1", 123, self.feed()), ledger)

    def test_unknown_partial_inventory_total_and_reset(self):
        ledger = self.transfer(20, "toship")
        inventory = MiningInventory(1, "F1", vehicle={"gold": 60})
        self.store.attach(inventory, ledger)
        self.assertEqual(inventory.stock("gold"), (60, None, None))
        self.store.attach(inventory, self.confirm())
        self.assertEqual(inventory.stock("gold"), (60, 504, 564))
        self.assertEqual(inventory.stock("copper"), (0, None, None))
        self.store.attach(inventory, self.confirm(None))
        self.assertEqual(inventory.stock("gold"), (60, None, None))
        self.assertNotIn("gold", self.transfer(10, "tocarrier")["records"])

    def test_negative_invalidates_and_manual_correction_is_new_baseline(self):
        first = self.confirm(10)
        ledger = self.transfer(20, "toship")
        self.assertIsNone(ledger["records"]["gold"]["count"])
        self.assertEqual(ledger["records"]["gold"]["status"], "inconsistent")
        ledger = self.transfer(100, "tocarrier")
        self.assertIsNone(ledger["records"]["gold"]["count"])
        ledger = self.confirm(504)
        self.assertNotEqual(first["records"]["gold"]["confirmed_at"], ledger["records"]["gold"]["confirmed_at"])
        self.assertEqual(self.transfer(1, "toship")["records"]["gold"]["count"], 503)

    def test_foreign_carrier_wrong_fid_and_srv_are_not_own_transfers(self):
        self.confirm()
        self.assertEqual(self.transfer(50, "toship", CarrierID=999)["records"]["gold"]["count"], 504)
        self.events.append(dict(event="Docked", MarketID=999, StationType="FleetCarrier"))
        self.assertEqual(self.transfer(20, "tocarrier")["records"]["gold"]["count"], 504)
        self.events.append(dict(event="LaunchSRV"))
        self.assertEqual(self.transfer(20, "toship")["records"]["gold"]["count"], 504)
        self.assertEqual(self.transfer(20, "tosrv")["records"]["gold"]["count"], 504)
        self.assertEqual(self.store.update("F1", 999, self.feed())["records"], {})
        self.assertEqual(self.store.update("F2", 123, None)["records"], {})
        self.assertIsNone(read_carrier_feed(self.path, "F2"))

    def test_unattributable_transfer_invalidates_only_affected_stock(self):
        self.confirm()
        self.store.confirm("F1", 123, "copper", 20, self.feed())
        self.events.append(dict(event="Undocked"))
        ledger = self.transfer(10, "toship")
        self.assertIsNone(ledger["records"]["gold"]["count"])
        self.assertEqual(ledger["records"]["copper"]["count"], 20)

    def test_gap_truncation_and_new_journal_require_confirmation(self):
        for gap in ("truncate", "replace", "new_file"):
            with self.subTest(gap=gap):
                self.confirm()
                if gap == "truncate":
                    self.events = self.events[:1]
                elif gap == "replace":
                    self.events[0]["extra"] = True
                else:
                    self.path = self.folder / "Journal-new.log"
                ledger = self.store.update("F1", 123, self.feed())
                self.assertIsNone(ledger["records"]["gold"]["count"])
                self.assertEqual(ledger["records"]["gold"]["status"], "inconsistent")

    def test_validation_and_partial_line_not_consumed(self):
        for count in (-1, 1.5, True, "2"):
            with self.assertRaises(ValueError):
                self.confirm(count)
        with self.assertRaises(ValueError):
            self.store.confirm("F1", None, "gold", 20, self.feed())
        self.confirm()
        with self.path.open("ab") as stream:
            stream.write(b'{"event":"CargoTransfer"')
        feed = read_carrier_feed(self.path, "F1")
        self.assertEqual(self.store.update("F1", 123, feed)["records"]["gold"]["count"], 504)

    def test_explicit_own_id_without_dock_context_and_invalid_amount(self):
        self.events = self.events[:1]
        self.confirm()
        self.assertEqual(self.transfer(4, "tocarrier", CarrierID=123)["records"]["gold"]["count"], 508)
        self.assertIsNone(self.transfer(-1, "toship", CarrierID=123)["records"]["gold"]["count"])

    def test_known_zero_and_conflicting_stable_ids(self):
        inventory = MiningInventory(1, "F1", vehicle={"gold": 60})
        self.store.attach(inventory, self.confirm(0))
        self.assertEqual(inventory.stock("gold"), (60, 0, 60))
        self.assertIsNone(self.transfer(1, "tocarrier", CarrierID=123, MarketID=999)["records"]["gold"]["count"])
        self.confirm(504)
        self.events.append(dict(event="Docked", MarketID=999, StationType="FleetCarrier"))
        self.assertIsNone(self.transfer(1, "tocarrier", CarrierID=123)["records"]["gold"]["count"])
