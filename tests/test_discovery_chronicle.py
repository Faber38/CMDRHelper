"""Discovery queries and the real chronicle controls, using isolated databases."""
import csv
import io
import itertools
import json
import os
from pathlib import Path
import string
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import Qt, QSettings, QDate, QObject, Signal
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.chronicle_filters import ChronicleFilters
from cmdrhelper.discovery_export import discovery_row, serialize_discoveries
from cmdrhelper.i18n import _TRANSLATIONS, tr, set_language, get_language
from cmdrhelper.ui.main_window import MainWindow
from qt_widget_cleanup import destroy_widget

TYPES = ('first_footfall', 'first_discovery', 'first_mapping')


def body(bid=7, **kw):
    return dict(dict(body_id=bid, name='Shared Ä 3', short_name='3', body_type='Planet',
                     planet_class='Rocky body', journal_scanned=True,
                     first_footfall=True, first_footfall_at='2026-11-10T08:08:56Z',
                     was_discovered=False, was_mapped=False, self_mapped=True,
                     mapped_at='2026-11-10T08:04:47Z'), **kw)


class DiscoveryDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'isolated.db'
        self.db = CMDRDatabase(self.path)
        self.a = self.db.upsert_commander('A', 'Älpha')
        self.b = self.db.upsert_commander('B', 'Beta')
        for cid in (self.a, self.b):
            self.seed(cid, [body()])

    def seed(self, cid, bodies, address=60, coords=True):
        data = dict(system_address=address, system='Shared Ä',
                    system_bodies=bodies, last_timestamp='2026-11-10T09:00:00Z')
        if coords:
            data['star_pos'] = [1, 2, 3]
        self.db.store_snapshot(data, cid)

    def query(self, ids=None, types=TYPES, **kw):
        return self.db.search_discoveries([self.a] if ids is None else ids, types, **kw)

    def test_all_combinations_and_identity(self):
        for n in range(4):
            for selected in itertools.combinations(TYPES, n):
                rows = self.query([self.a, self.b, self.a], selected)
                self.assertEqual(len(rows), n * 2)
                self.assertEqual({r['kind'] for r in rows}, set(selected))
                self.assertEqual(len({(r['commander_id'], r['system_address'], r['body_id'], r['kind'])
                                      for r in rows}), len(rows))
        self.assertEqual(self.query([]), [])
        self.assertEqual(len(self.query([self.b])), 3)

    def test_names_times_utc_bounds_and_unknowns(self):
        rows = self.query(query='shared')
        self.assertEqual([r['kind'] for r in rows], list(TYPES[::2]) + ['first_discovery'])
        self.assertIsNone(rows[-1]['timestamp'])
        self.assertEqual(len(self.query(query='3')), 3)
        self.assertEqual(self.query(query='missing'), [])
        self.seed(self.a, [body(8, name='Boundary', first_footfall_at='2026-11-11T00:30:00+01:00',
                                mapped_at='2026-11-10T00:00:00Z')])
        bounds = dict(visited_from='2026-11-10', visited_before='2026-11-11')
        rows = self.query(**bounds)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]['timestamp'], '2026-11-10T23:30:00.000000Z')
        self.assertNotIn('first_discovery', [r['kind'] for r in rows])
        self.assertEqual(self.query(visited_from='2026-11-11'), [])
        self.assertEqual(self.query(visited_before='2026-11-10'), [])
        self.seed(self.a, [body(9, first_footfall_at='invalid', mapped_at=None)])
        self.assertEqual(sum(r['timestamp'] is None for r in self.query()), 5)
        self.assertEqual(len(self.query(**bounds)), 4)

    def test_negative_flags_mappable_types_and_reload(self):
        self.seed(self.a, [body(8, first_footfall=False, was_discovered=None,
                               was_mapped=False, self_mapped=False),
                           body(9, first_footfall=False, was_discovered=True,
                                was_mapped=True),
                           body(10, first_footfall=False, was_discovered=True,
                                star_type='G', body_type='Star'),
                           body(11, first_footfall=False, was_discovered=True,
                                body_type='BeltCluster')])
        self.assertEqual(len(self.query()), 3)
        with self.db._connect() as con:
            con.execute('UPDATE commander_bodies SET scanned=0 WHERE commander_id=? AND body_id=7', (self.a,))
        self.assertEqual(len(self.query()), 2)
        self.db = CMDRDatabase(self.path)
        self.assertEqual(len(self.query()), 2)
        self.assertEqual(len(self.query([self.b])), 3)

    def test_repeat_archive_import_has_no_duplicates(self):
        folder = Path(self.tmp.name) / 'journal'; folder.mkdir()
        events = [dict(event='Commander', FID='ARCH', Name='Archive'),
                  dict(event='Location', StarSystem='Archive', SystemAddress=90, StarPos=[1,2,3]),
                  dict(event='Scan', SystemAddress=90, BodyID=7, BodyName='Archive 3',
                       PlanetClass='Rocky body', WasDiscovered=False, WasMapped=False, WasFootfalled=False),
                  dict(event='SAAScanComplete', SystemAddress=90, BodyID=7, BodyName='Archive 3'),
                  dict(event='Disembark', SystemAddress=90, BodyID=7, OnPlanet=True)]
        for n, e in enumerate(events):
            e['timestamp'] = f'2026-11-10T08:00:0{n}Z'
        (folder/'Journal.2026-11-10T080000.01.log').write_text(''.join(json.dumps(e)+'\n' for e in events))
        self.db.import_journal_archive(folder)
        cid = self.db.upsert_commander('ARCH', 'Archive')
        before = self.query([cid])
        self.db.import_journal_archive(folder)
        self.assertEqual(before, self.query([cid]))
        self.assertEqual(len(before), 3)


class CompletionSignals(QObject):
    journalCatchupReady = Signal(object, str)
    databaseImportFinished = Signal(object, str)


class ChronicleWindow(MainWindow):
    def __init__(self, db, settings, cid):
        QMainWindow.__init__(self)
        self.ui_theme = 'dark'
        self._chronicle_system_window = None
        self._chronicle_search_help_window = None
        self.state = SimpleNamespace(database=db, settings=settings, commander_id=cid,
                                     viewed_commander_id=cid, system_address=None)
        self.pages = SimpleNamespace(currentIndex=lambda: self.PAGE_CHRONICLE)
        self.setCentralWidget(self._chronicle())
        self._show_body_details = Mock()
        self.completions = CompletionSignals(self)
        self.completions.journalCatchupReady.connect(self._refresh_open_discoveries)
        self.completions.databaseImportFinished.connect(self._refresh_open_discoveries)


class DiscoveryUiTests(DiscoveryDatabaseTests):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        super().setUp()
        self.addCleanup(set_language, get_language())
        set_language('de')
        self.errors = []
        self.old_hook = sys.excepthook
        sys.excepthook = lambda *args: self.errors.append(args)
        self.addCleanup(setattr, sys, 'excepthook', self.old_hook)
        self.w = ChronicleWindow(self.db, QSettings(str(Path(self.tmp.name)/'ui.ini'), QSettings.IniFormat), self.a)
        self.addCleanup(destroy_widget, self.w, close=False)
        self.w.show(); self.app.processEvents()

    def tearDown(self):
        self.assertEqual(self.errors, [], 'Unhandled Qt callback exception')

    def apply(self, types=TYPES):
        for kind, check in zip(TYPES, (self.w.chronicle_footfall_check,
                                       self.w.chronicle_discovery_check, self.w.chronicle_mapping_check)):
            check.setChecked(kind in types)
        self.w.chronicle_apply_button.click()
        self.app.processEvents()

    def test_filters_commander_selection_reset_and_mining_preservation(self):
        w = self.w
        w.chronicle_planetary_mining_check.setChecked(True)
        w.chronicle_planetary_mining_minimum.setValue(4)
        w.chronicle_personally_mined_check.setChecked(True)
        w.chronicle_mining_commodity_combo.addItem('Gold', 'gold')
        w.chronicle_mining_commodity_combo.setCurrentIndex(1)
        for n in range(1, 4):
            for types in itertools.combinations(TYPES, n):
                self.apply(types)
                self.assertEqual(w.chronicle_search_results.count(), 2 * n)
        self.assertFalse(w.chronicle_planetary_mining_check.isEnabled())
        self.assertEqual(w.chronicle_planetary_mining_minimum.value(), 4)
        self.assertEqual(w.chronicle_mining_commodity_combo.currentData(), 'gold')
        w.chronicle_commander_checks[self.b].setChecked(False)
        self.assertEqual(w.chronicle_search_results.count(), 3)
        w.chronicle_commander_checks[self.a].setChecked(False)
        self.assertEqual(w.chronicle_search_results.count(), 0)
        self.assertFalse(w.chronicle_copy_list.isEnabled())
        w.chronicle_all_commanders.setChecked(True)
        self.assertEqual(w.chronicle_search_results.count(), 6)
        # Turning discovery filters off restores controls without resetting values.
        for c in (w.chronicle_footfall_check, w.chronicle_discovery_check, w.chronicle_mapping_check):
            c.setChecked(False)
        self.assertTrue(w.chronicle_planetary_mining_check.isEnabled())
        self.assertTrue(w.chronicle_mining_commodity_combo.isEnabled())
        self.assertEqual(w.chronicle_mining_commodity_combo.currentData(), 'gold')
        w.chronicle_reset_button.click()
        self.assertFalse(w._chronicle_filters().discovery_types)
        self.assertEqual(w.chronicle_search_results.count(), 0)

    def test_export_snapshot_copy_csv_unicode_cancel_failure_empty(self):
        self.seed(self.a, [body(name='Ä;"World\nLine', short_name='Ä;"3\nline')])
        self.apply()
        w = self.w
        expected = [list(w._discovery_headers), *map(list, w._discovery_rows)]
        # Unapplied edits must not affect either export.
        w.chronicle_search_edit.setText('no match')
        with patch.object(self.db, 'search_discoveries', side_effect=AssertionError('export queried DB')):
            w.chronicle_copy_list.click()
            copied = list(csv.reader(io.StringIO(QApplication.clipboard().text()), delimiter='\t'))
            self.assertEqual(copied, expected)
            target = Path(self.tmp.name)/'out.csv'
            with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(target), 'CSV')):
                w.chronicle_export_csv.click()
            with target.open(encoding='utf-8', newline='') as f:
                self.assertEqual(list(csv.reader(f, delimiter=';')), expected)
            with patch.object(QFileDialog, 'getSaveFileName', return_value=('', '')):
                w.chronicle_export_csv.click()
            with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(Path(self.tmp.name)/'missing'/'out.csv'), '')):
                w.chronicle_export_csv.click()
                self.assertIn('fehlgeschlagen', w.chronicle_status.text())
        self.assertTrue(any(r[0] == '' for r in w._discovery_rows))
        w.chronicle_apply_button.click()
        self.assertFalse(w.chronicle_export_csv.isEnabled())
        with patch.object(QFileDialog, 'getSaveFileName') as save:
            w._export_discovery_list(); save.assert_not_called()

    def test_details_dates_missing_coordinates_and_completion_refresh(self):
        self.seed(self.b, [body(8)], address=61, coords=False)
        self.apply()
        w = self.w
        self.assertEqual(w.chronicle_search_results.count(), 9)
        self.assertEqual(len(w.chronicle_map.systems), 1)
        self.assertEqual(w.chronicle_map.routes, [])
        for i in range(w.chronicle_search_results.count()):
            item = w.chronicle_search_results.item(i); result = item.data(Qt.UserRole)
            with patch.object(self.db, 'chronicle_system_details', wraps=self.db.chronicle_system_details) as details:
                w.chronicle_search_results.itemClicked.emit(item)
                details.assert_called_once_with(result['system_address'], commander_id=result['commander_id'])
                self.assertEqual(w._show_body_details.call_args.args[0]['body_id'], result['body_id'])
        w.chronicle_from_date.setDate(QDate(2026,11,10)); w.chronicle_from_check.setChecked(True)
        w.chronicle_to_date.setDate(QDate(2026,11,10)); w.chronicle_to_check.setChecked(True)
        w.chronicle_apply_button.click()
        self.assertEqual(w.chronicle_search_results.count(), 6)
        self.seed(self.a, [body(9)])
        w.chronicle_search_edit.setText('unapplied')
        w.completions.journalCatchupReady.emit([], '')
        self.assertEqual(w.chronicle_search_results.count(), 8)
        w.completions.databaseImportFinished.emit({}, '')
        self.assertEqual(w.chronicle_search_results.count(), 8)
        with patch.object(self.db, 'search_discoveries') as query:
            w.completions.journalCatchupReady.emit(None, 'failed')
            w.pages.currentIndex = lambda: -1
            w.completions.databaseImportFinished.emit({}, '')
            query.assert_not_called()

    def test_twelve_languages_complete_and_placeholders_match(self):
        keys = {k for k in _TRANSLATIONS['en'] if k.startswith(('discovery.', 'footfall.'))}
        self.assertGreater(len(keys), 20)
        def fields(value):
            return {f for _, f, _, _ in string.Formatter().parse(value) if f}
        for lang in ('de','en','el','es','fi','fr','it','nl','no','pl','sv','tr'):
            for key in keys:
                self.assertIn(key, _TRANSLATIONS[lang])
                self.assertTrue(_TRANSLATIONS[lang][key])
                self.assertEqual(fields(_TRANSLATIONS[lang][key]), fields(_TRANSLATIONS['en'][key]))
            set_language(lang)
            self.apply(('first_footfall',))
            self.assertIn(tr('discovery.event.first_footfall'), self.w.chronicle_search_results.item(0).text())
            self.assertNotIn('discovery.', self.w.chronicle_search_results.item(0).text())
