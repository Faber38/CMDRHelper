"""Evidence status must survive replay, persistence and a game restart in an SRV."""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QStyle, QStyleOptionViewItem

from cmdrhelper.mining_inventory import MiningInventory, MiningInventoryReader
from cmdrhelper.mining_persistence import save_values
from cmdrhelper.i18n import tr, get_language, set_language, _TRANSLATIONS
from cmdrhelper.ui.mining_view import MiningView


class MiningReplayStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.settings = QSettings(str(self.folder / 'settings.ini'), QSettings.IniFormat)
        self.view = MiningView(self.settings)
        self.addCleanup(self.view.deleteLater)
        self.sessions = []
        self.serial = 0
        self.session('cobramkiii', 51)

    def session(self, ship, ship_id, fid='F1', cid=1):
        self.path = self.folder / f'Journal.2026-10-30T{12 + len(self.sessions):02}0000.01.log'
        self.sessions.append(dict(journal_file=str(self.path), commander_id=cid,
                                  fid_seen=fid, attribution_status='identified'))
        self.append('Commander', FID=fid, Name='Synthetic')
        self.append('LoadGame', FID=fid, Commander='Synthetic', Ship=ship, ShipID=ship_id,
                    GameMode='Solo', Credits=1000000, Loan=0)

    def append(self, event, **fields):
        self.serial += 1
        stamp = datetime.strptime(self.path.name.split('.')[1], '%Y-%m-%dT%H%M%S')
        data = dict(timestamp=(stamp + timedelta(seconds=self.serial)).isoformat() + 'Z',
                    event=event, **fields)
        with self.path.open('a') as stream:
            stream.write(json.dumps(data) + '\n')
        return data

    def cargo(self, vessel, amount, inline=True):
        inventory = [dict(Name='monazite', Count=amount, Stolen=0)] if amount else []
        event = self.append('Cargo', Vessel=vessel, Count=amount,
                            **({'Inventory': inventory} if inline else {}))
        (self.folder / 'Cargo.json').write_text(json.dumps({**event, 'Inventory': inventory}))

    def read(self, saved=None, live=True, cid=1, fid='F1'):
        return MiningInventoryReader().reconstruct(cid, fid, self.sessions,
            checkpoints=saved, live_path=self.path if live else None)

    def assert_table(self, result, srv, ship, ship_quality, total):
        # Explicit known-zero carrier fixture, never inferred from vehicle cargo.
        result.carrier = {'monazite': 0}
        self.view.set_inventory(result)
        item = self.view.items['monazite']
        self.assertEqual(list(result.stock('monazite')), [srv, ship, 0, total])
        self.assertEqual([item.data(i, Qt.UserRole) for i in range(1, 5)], [srv, ship, 0, total])
        self.assertEqual(item.data(2, Qt.UserRole + 1), ship_quality)
        self.assertEqual(item.text(4), str(total) if total is not None else '—')
        if ship_quality == 'stale':
            self.assertEqual(result.displayed_stock('Ship', 'monazite'), (20, 'stale'))
            self.assertEqual(item.data(2, Qt.UserRole + 2), 20)
            self.assertEqual(item.text(2), tr('mining.stock_stale_value', value='20'))
            self.assertIn(tr('mining.stock_stale'), item.toolTip(2))
            self.assertIn('ShipID: 51', item.toolTip(2))
            self.assertTrue(item.font(2).italic())
            self.view.only_stock.setChecked(True)
            self.assertFalse(item.isHidden())
            for light, yellow, grey in ((False, '#f0ad4e', '#8e969e'),
                                        (True, '#b36a00', '#65717c')):
                self.view.set_light_mode(light)
                self.assertEqual(item.foreground(2).color().name(), yellow)
                self.assertEqual(item.foreground(4).color().name(), grey)
        elif ship is not None:
            self.assertEqual(item.text(2), str(ship))

    def baseline(self, inline=True):
        self.cargo('Ship', 20, inline=inline)
        first = self.read()
        self.append('LaunchSRV', ID=52, SRVType='mev_rhino', Loadout='starter')
        self.cargo('SRV', 20, inline=inline)
        result = self.read(first.checkpoints)
        self.assert_table(result, 20, 20, 'confirmed', 40)
        return result

    def test_missing_sidecar_status_and_table_match_replay(self):
        self.baseline()
        self.cargo('Ship', 20, inline=False)
        (self.folder / 'Cargo.json').unlink()
        for live in (True, False):
            self.assert_table(self.read(live=live), 20, None, 'stale', None)

    def test_transfer_requires_event_and_empty_srv_dock_preserves_ship(self):
        self.baseline()
        self.append('Embark', SRV=False, ID=51, Taxi=False, Multicrew=False)
        self.assert_table(self.read(), 20, 20, 'confirmed', 40)
        self.append('Embark', SRV=True, ID=52, Taxi=False, Multicrew=False)
        self.append('CargoTransfer', Transfers=[dict(Type='monazite', Count=20, Direction='toship')])
        self.assert_table(self.read(), 0, 40, 'tracked', 40)
        self.cargo('Ship', 40)
        for _ in range(2):
            self.assert_table(self.read(), 0, 40, 'confirmed', 40)
        self.append('DockSRV', ID=52, SRVType='mev_rhino')
        for live in (True, False):
            result = self.read(live=live)
            self.assert_table(result, None, 40, 'confirmed', None)

    def test_game_restart_in_rhino_requires_fresh_ship_confirmation(self):
        for inline, saved_present in ((True, False), (True, True), (False, True)):
            for helper_first in (False, True):
                for srv_sidecar in (False, True):
                    with self.subTest(inline=inline, saved=saved_present,
                                      helper_first=helper_first, srv_sidecar=srv_sidecar):
                        # Each combination uses independent files, settings and a fresh reader.
                        with tempfile.TemporaryDirectory() as directory:
                            self.folder = Path(directory)
                            self.sessions = []
                            self.session('cobramkiii', 51)
                            previous = self.baseline(inline)
                            settings = QSettings(str(self.folder / 'saved.ini'), QSettings.IniFormat)
                            key = 'materials/mining/cargo_checkpoints/1'
                            if saved_present:
                                save_values(settings, {key: previous.checkpoints})
                            saved = QSettings(settings.fileName(), QSettings.IniFormat).value(key, {})
                            self.append('Shutdown')
                            if helper_first:
                                self.assert_table(self.read(saved), 20, 20, 'confirmed', 40)
                            self.session('mev_rhino', 52)
                            if srv_sidecar:
                                self.cargo('SRV', 20, inline=False)
                            else:
                                (self.folder / 'Cargo.json').unlink()
                            restored = self.read(saved)
                            self.assert_table(restored, 20, None, 'stale', None)
                            historical = self.read(restored.checkpoints, live=False)
                            self.assert_table(historical, 20, None, 'stale', None)
                            self.append('Embark', SRV=False, ID=51, Taxi=False, Multicrew=False)
                            self.assert_table(self.read(restored.checkpoints), 20, None, 'stale', None)
                            self.cargo('Ship', 20)
                            self.assert_table(self.read(restored.checkpoints), 20, 20, 'confirmed', 40)

    def test_restart_identity_changes_do_not_promote_ship_history(self):
        previous = self.baseline()
        self.session('mev_rhino', 99)
        self.cargo('SRV', 20)
        self.assert_table(self.read(previous.checkpoints), 20, None, 'stale', None)
        self.append('Loadout', Ship='anaconda', ShipID=100, Modules=[])
        self.assert_table(self.read(previous.checkpoints), None, None, 'unknown', None)
        self.session('mev_rhino', 52, fid='F2', cid=2)
        self.cargo('SRV', 20)
        self.assert_table(self.read(previous.checkpoints, cid=2, fid='F2'), 20, None, 'unknown', None)

    def test_status_colors_include_zero_tracking_and_explicit_carrier_error(self):
        item = self.view.items['monazite']
        for light, green, yellow, grey, red in (
                (False, '#79d45a', '#f0ad4e', '#8e969e', '#ff6b6b'),
                (True, '#37852d', '#b36a00', '#65717c', '#b83232')):
            self.view.set_light_mode(light)
            unchanged = [(item.foreground(c), item.background(c)) for c in (0, 5, 6)]
            for quality, amount, color in (('confirmed', 20, green), ('confirmed', 0, green),
                                           ('tracked', 20, yellow), ('tracked', 0, yellow),
                                           ('unknown', None, grey)):
                inventory = MiningInventory(1, 'F1', srv={},
                    ship=None if amount is None else {'monazite': amount}, carrier={'monazite': 0},
                    vehicle_records={'Ship': {'quality': quality}})
                self.view.set_inventory(inventory)
                self.assertEqual(item.foreground(2).color().name(), color)
                self.assertEqual(item.foreground(4).color().name(), color)
                self.assertEqual(item.data(2, Qt.UserRole), amount)
                self.assertIn(tr('mining.stock_' + quality), item.toolTip(2))
                self.assertIn(tr('mining.stock_' + quality), item.toolTip(4))
                option = QStyleOptionViewItem()
                option.state |= QStyle.StateFlag.State_Selected
                self.view.carrier_delegate.initStyleOption(option, self.view.tree.indexFromItem(item, 2))
                self.assertEqual(option.palette.color(QPalette.ColorRole.Text).name(), color)
            for status, count, color in (('manual', 0, green), ('tracked', 0, yellow),
                                         ('inconsistent', None, red)):
                inventory = MiningInventory(1, 'F1', srv={}, ship={}, carrier={'monazite': count},
                    carrier_records={'monazite': dict(status=status, count=count,
                        confirmed_at='2026-10-30T12:00:00Z')})
                self.view.set_inventory(inventory)
                self.assertEqual(item.foreground(3).color().name(), color)
                self.assertEqual(item.foreground(4).color().name(), grey if count is None else color)
                self.assertEqual(item.data(3, Qt.UserRole), count)
                if status == 'inconsistent':
                    self.assertIn(tr('mining.carrier_inconsistent'), item.toolTip(3))
                    self.assertEqual(item.text(3), tr('mining.carrier_marked', value='—'))
            self.assertEqual([(item.foreground(c), item.background(c)) for c in (0, 5, 6)], unchanged)

    def test_compact_legend_in_all_languages_and_themes(self):
        self.addCleanup(set_language, get_language())
        keys = ('confirmed', 'last_known', 'unknown', 'inconsistent')
        for language, translations in _TRANSLATIONS.items():
            set_language(language)
            view = MiningView(self.settings)
            self.addCleanup(view.deleteLater)
            view.resize(1100, 430)
            for light in (False, True):
                with self.subTest(language=language, light=light):
                    view.set_light_mode(light)
                    view.grab()  # Offscreen layout/paint, without showing a desktop window.
                    labels = view.stock_legend_labels
                    self.assertEqual([label.text() for label in labels],
                                     [translations['mining.legend_' + key] for key in keys])
                    self.assertEqual(len({label.y() for label in labels}), 1)
                    self.assertLessEqual(view.stock_legend.height(), labels[0].fontMetrics().height() + 8)
                    self.assertLess(view.stock_legend.geometry().bottom(), view.tree.y())
                    for label, dot, index in zip(labels, view.stock_legend_dots, (1, 2, 0, 3)):
                        self.assertGreaterEqual(label.width(), label.sizeHint().width())
                        self.assertTrue(label.toolTip())
                        self.assertEqual(dot.text(), '●')
                        self.assertIn(view._stock_colors[index], dot.styleSheet())
                    self.assertIn(tr('mining.carrier_inconsistent'), labels[3].toolTip())
