import os
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QDate, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow, QDialog, QPushButton, QLabel

from cmdrhelper.chronicle_filters import ChronicleFilters, visit_utc_time
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.i18n import set_language, tr, _TRANSLATIONS
from cmdrhelper.ui.main_window import MainWindow


class ChronicleFixture:
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = CMDRDatabase(Path(self.temp.name) / 'test.db')
        self.a = self.db.upsert_commander('A', 'Alpha')
        self.b = self.db.upsert_commander('B', 'Bravo')
        with self.db._connect() as con:
            for address in range(1, 8):
                con.execute('INSERT INTO systems(system_address,name,x,y,z) VALUES(?,?,?,?,?)',
                            (address, f'Test {address}', address, 0, 0))
                con.execute('''INSERT INTO bodies(system_address,body_id,name,short_name,body_type,
                               planet_class,planetary_mining_signals) VALUES(?,1,?,?,'Planet','Water world',24)''',
                            (address, f'Test {address} A', 'A'))
                for commander in (self.a, self.b):
                    con.execute('''INSERT INTO commander_systems(commander_id,system_address,first_seen,last_seen)
                                   VALUES(?,?,'2026-06-01T00:00:00Z','2026-08-31T23:59:59Z')''',
                                (commander, address))
                    con.execute('INSERT INTO commander_bodies(commander_id,system_address,body_id) VALUES(?,?,1)',
                                (commander, address))
                    con.execute('''INSERT INTO biology(commander_id,system_address,body_id,genus,species)
                                   VALUES(?,?,1,'Bacterium','Vesicula')''', (commander, address))
                    con.execute('INSERT INTO codex_entries(commander_id,system_address,name) VALUES(?,?,?)',
                                (commander, address, 'Phenomenon'))
                    con.execute('''INSERT INTO surface_mining_commodities(commander_id,system_address,body_id,
                                   frontier_name,display_name,quantity,first_mined_at,last_mined_at)
                                   VALUES(?,?,1,'copper','Kupfer',56,'2026-01-01T00:00:00Z','2026-08-01T00:00:00Z')''',
                                (commander, address))
                con.execute("INSERT INTO materials(system_address,body_id,material_name,percentage) VALUES(?,1,'iron',12)",
                            (address,))
        self.visit(1, '2026-06-30T23:59:59.999999Z')
        self.visit(2, '2026-07-01T00:00:00.000000Z')
        self.visit(3, '2026-07-21T23:59:59.999999Z')
        self.visit(4, '2026-07-22T00:00:00Z')
        self.visit(5, '2026-06-01T00:00:00Z')
        self.visit(5, '2026-08-01T00:00:00Z')
        self.visit(6, '2026-07-10T00:00:00Z', self.b)
        self.visit(2, '2026-07-15T12:00:00Z')
        self.visit(7, '2026-07-22T01:30:00+02:00')  # Still July 21 in UTC.
        self.bounds = ChronicleFilters(date_from=date(2026,7,1), date_to=date(2026,7,21)).visit_bounds()

    def visit(self, address, stamp, commander=None):
        self.db.store_visit(address, timestamp=stamp, commander_id=commander or self.a)

    def systems(self, **bounds):
        return {s['system_address'] for s in self.db.multi_commander_chronicle([self.a], **bounds)['systems']}


class PeriodDatabaseTests(ChronicleFixture, unittest.TestCase):
    def test_open_bounds_last_day_fraction_and_next_day(self):
        self.assertEqual(self.systems(), {1,2,3,4,5,7})
        self.assertEqual(self.systems(visited_from='2026-07-01'), {2,3,4,5,7})
        self.assertEqual(self.systems(visited_before='2026-07-22'), {1,2,3,5,7})
        self.assertEqual(self.systems(**self.bounds), {2,3,7})
        self.assertEqual(self.systems(**ChronicleFilters().visit_bounds()), self.systems())

    def test_counts_route_and_first_last_use_only_filtered_visits(self):
        data = self.db.multi_commander_chronicle([self.a], **self.bounds)
        system = next(s for s in data['systems'] if s['system_address']==2)
        self.assertEqual(system['visits'], 2)
        self.assertEqual(system['first_seen'], '2026-07-01T00:00:00.000000Z')
        self.assertEqual(system['last_seen'], '2026-07-15T12:00:00.000000Z')
        self.assertEqual(data['routes'][0]['system_addresses'], [2,2,7,3])
        self.assertNotIn(5, self.systems(**self.bounds))

    def test_month_year_and_invalid_bounds(self):
        self.visit(1, '2026-12-31T23:59:59.999999Z')
        self.visit(6, '2027-01-01T00:00:00Z')
        december = ChronicleFilters(date_from=date(2026,12,31), date_to=date(2026,12,31)).visit_bounds()
        self.assertEqual(december['visited_before'], '2027-01-01')
        self.assertEqual(self.systems(**december), {1})
        self.assertEqual(ChronicleFilters(date_to=date(2026,7,31)).visit_bounds()['visited_before'], '2026-08-01')
        with self.assertRaises(ValueError):
            ChronicleFilters(date_from=date(2026,7,22), date_to=date(2026,7,21)).visit_bounds()
        self.assertIsNone(visit_utc_time('invalid'))

    def test_each_freetext_branch_uses_same_commander_visit(self):
        for query, kind in [('Test','System'),('Water','Körper'),('Vesicula','BIO'),
                            ('iron','Material'),('Phenomenon','Codex')]:
            with self.subTest(query=query):
                results = self.db.search_chronicle(query, self.a, **self.bounds)
                self.assertEqual({r['system_address'] for r in results}, {2,3,7})
                self.assertIn(kind, {r['kind'] for r in results})
                self.assertEqual({r['system_address'] for r in self.db.search_chronicle(query, self.b, **self.bounds)}, {6})
        self.assertEqual(len(self.db.search_chronicle('Water', self.a, **self.bounds)), 3)

    def test_no_period_preserves_search_results_and_bad_legacy_timestamps(self):
        self.visit(6, 'legacy timestamp')
        self.assertIn(6, self.systems())
        self.assertNotIn(6, self.systems(**self.bounds))
        for query in ('Test', 'Water', 'Vesicula', 'iron', 'Phenomenon'):
            unfiltered = self.db.search_chronicle(query, self.a)
            self.assertEqual(unfiltered, self.db.search_chronicle(query, self.a,
                             **ChronicleFilters().visit_bounds()))
            self.assertEqual({r['system_address'] for r in unfiltered}, set(range(1,8)))

    def test_period_is_applied_before_system_search_limit(self):
        # More out-of-period matches than the 500-system limit must not hide
        # an in-period match that sorts after them.
        with self.db._connect() as con:
            for address in range(100, 605):
                con.execute('INSERT INTO systems(system_address,name) VALUES(?,?)',
                            (address, f'AAA Test {address}'))
                con.execute('INSERT INTO commander_systems(commander_id,system_address) VALUES(?,?)',
                            (self.a,address))
        results = self.db.search_chronicle('Test',self.a,**self.bounds)
        self.assertEqual({r['system_address'] for r in results}, {2,3,7})

    def test_mining_combinations_preserve_total_quantities(self):
        for query in ('', 'Water', 'Vesicula', 'iron', 'Phenomenon'):
            for extra in ({'planetary_mining_only':True},
                          {'personally_mined_only':True, 'mining_commodity':'copper'},
                          {'planetary_mining_only':True, 'minimum_planetary_mining_signals':20,
                           'personally_mined_only':True, 'mining_commodity':'copper'}):
                with self.subTest(query=query, extra=extra):
                    results = self.db.search_chronicle(query, self.a, **extra, **self.bounds)
                    self.assertEqual({r['system_address'] for r in results}, {2,3,7})
                    self.assertEqual(len(results), 3)
                    self.assertTrue(all(r['surface_mining_commodities'][0]['quantity']==56 for r in results))
        self.assertFalse(self.db.search_chronicle('Water', self.a, personally_mined_only=True,
                                                mining_commodity='gold', **self.bounds))
        self.assertFalse(self.db.search_chronicle('Water', self.a, minimum_planetary_mining_signals=25,
                                                **self.bounds))


class PeriodUiTests(ChronicleFixture, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        super().setUp()
        set_language('de')
        self.window = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(self.window)
        self.window.state = SimpleNamespace(database=self.db, viewed_commander_id=self.a,
                                            commander_id=self.b, system='Test 4')
        self.window.ui_theme = 'dark'
        self.window._chronicle_system_window = None
        self.window._chronicle_search_help_window = None
        self.page = self.window._chronicle()
        self.window.setCentralWidget(self.page)
        self.window.show()
        self.app.processEvents()
        self.addCleanup(self.window.deleteLater)
        self.addCleanup(self.window.close)

    def enable_period(self):
        w=self.window
        w.chronicle_from_check.setChecked(True)
        w.chronicle_to_check.setChecked(True)
        w.chronicle_from_date.setDate(QDate(2026,7,1))
        w.chronicle_to_date.setDate(QDate(2026,7,21))

    def map_addresses(self):
        return {s['system_address'] for s in self.window.chronicle_map.systems}

    def test_enter_apply_refresh_and_no_separate_search_button(self):
        w=self.window
        self.enable_period()
        w.chronicle_search_edit.setText('Water')
        w.chronicle_planetary_mining_check.setChecked(True)
        w.chronicle_planetary_mining_minimum.setValue(20)
        w.chronicle_personally_mined_check.setChecked(True)
        w.chronicle_mining_commodity_combo.setCurrentIndex(1)
        w.chronicle_apply_button.click()
        self.assertEqual(self.map_addresses(), {2,3,7})
        self.assertEqual(w.chronicle_search_results.count(),3)
        first = list(w.chronicle_map.systems)
        QTest.keyClick(w.chronicle_search_edit, Qt.Key_Return)
        self.assertEqual(w.chronicle_map.systems, first)
        w.chronicle_refresh_button.click()
        self.assertEqual(w.chronicle_map.systems, first)
        self.assertNotIn(tr('chronicle.search'), [b.text() for b in self.page.findChildren(QPushButton)])
        self.assertIn('UTC', ' '.join(label.text() for label in self.page.findChildren(QLabel)))
        self.assertLessEqual(self.page.minimumSizeHint().width(), 1000)

    def test_combined_filter_routes_do_not_bridge_hidden_systems(self):
        self.enable_period()
        w = self.window
        w.chronicle_planetary_mining_check.setChecked(True)
        w.chronicle_search_edit.setText('Water')
        w._apply_chronicle_filters()
        self.assertEqual(w.chronicle_map.routes[0]['system_addresses'], [2,2,7,3])
        with self.db._connect() as con:
            con.execute('UPDATE bodies SET planetary_mining_signals=0 WHERE system_address=7')
        w.chronicle_refresh_button.click()
        self.assertEqual(self.map_addresses(), {2,3})
        segments = w.chronicle_map.route_segments()
        self.assertNotIn((2,3), [(start['system_address'], end['system_address'])
                                for _,start,end in segments])
        self.assertTrue(all(commander==self.a for commander,_,_ in segments))

    def test_invalid_dates_make_no_database_query(self):
        self.enable_period()
        self.window.chronicle_from_date.setDate(QDate(2026,7,22))
        with patch.object(self.db,'_connect',side_effect=AssertionError('unexpected query')):
            self.assertFalse(self.window._apply_chronicle_filters())
        self.assertEqual(self.window.chronicle_status.text(),tr('chronicle.filters.invalid_dates'))

    def test_reset_clears_every_filter_and_stale_context_but_not_commanders(self):
        w=self.window
        w._show_only_chronicle_commander(self.a)
        self.enable_period()
        w.chronicle_search_edit.setText('Water')
        w.chronicle_planetary_mining_check.setChecked(True)
        w.chronicle_personally_mined_check.setChecked(True)
        w.chronicle_planetary_mining_minimum.setValue(20)
        w.chronicle_mining_commodity_combo.setCurrentIndex(1)
        w.chronicle_detail.setText('old detail')
        dialog=QDialog(w); dialog.show(); w._chronicle_system_window=dialog
        w.chronicle_reset_button.click()
        self.assertEqual(w._chronicle_filters(),ChronicleFilters())
        self.assertEqual(w._selected_chronicle_commander_ids(),[self.a])
        self.assertEqual(self.map_addresses(),{1,2,3,4,5,7})
        self.assertEqual(w.chronicle_search_results.count(),0)
        self.assertEqual(w.chronicle_detail.text(),tr('chronicle.no_system_selected'))
        self.assertIsNone(w._chronicle_system_window)
        self.assertFalse(dialog.isVisible())

    def test_zero_results_clear_previous_map_routes_and_details(self):
        w=self.window
        self.enable_period(); w._apply_chronicle_filters()
        self.assertTrue(w.chronicle_map.routes)
        w.chronicle_detail.setText('old detail')
        w.chronicle_search_edit.setText('no such finding')
        w._apply_chronicle_filters()
        self.assertEqual(w.chronicle_map.systems,[])
        self.assertEqual(w.chronicle_map.routes,[])
        self.assertEqual(w.chronicle_search_results.count(),0)
        self.assertEqual(w.chronicle_detail.text(),tr('chronicle.no_system_selected'))

    def test_commander_switch_keeps_map_selection_separate_from_personal_search(self):
        w=self.window
        w._show_only_chronicle_commander(self.b)
        self.enable_period(); w.chronicle_search_edit.setText('Water')
        w._apply_chronicle_filters()
        self.assertEqual(self.map_addresses(),{2,3,7})
        w.state.viewed_commander_id=self.b
        w._chronicle_viewed_commander_changed(self.b)
        self.assertEqual(self.map_addresses(),{6})
        self.assertEqual(w._selected_chronicle_commander_ids(),[self.b])
        w.chronicle_search_edit.clear(); w._apply_chronicle_filters()
        self.assertEqual(self.map_addresses(),{6})

    def test_search_help_uses_viewed_commander_and_preserves_filters(self):
        w = self.window
        self.enable_period()
        w.chronicle_planetary_mining_check.setChecked(True)
        with patch.object(self.db, 'chronicle_search_terms', wraps=self.db.chronicle_search_terms) as terms, \
             patch('cmdrhelper.ui.main_window.ChronicleSearchHelpDialog'):
            w._open_chronicle_search_help()
            terms.assert_called_once_with(commander_id=self.a)
        w._chronicle_search_term_clicked('Water')
        self.assertEqual(self.map_addresses(), {2,3,7})
        self.assertTrue(w.chronicle_planetary_mining_check.isChecked())
        self.assertTrue(w.chronicle_from_check.isChecked())

    def test_current_position_honors_period(self):
        w=self.window
        self.enable_period(); w.chronicle_current_button.click()
        self.assertNotIn(4,self.map_addresses())
        self.assertTrue(w.chronicle_from_check.isChecked())
        self.assertEqual(w.chronicle_status.text(),tr('chronicle.filters.current_missing'))
        w.state.system='Test 2'
        w.chronicle_current_button.click()
        self.assertEqual(w.chronicle_map.current_system_address,2)

    def test_all_new_keys_translated_with_matching_placeholders(self):
        from tools.check_i18n import placeholders
        keys={k for k in _TRANSLATIONS['en'] if k.startswith('chronicle.filters.')}
        self.assertEqual(len(_TRANSLATIONS),12)
        for language, table in _TRANSLATIONS.items():
            for key in keys:
                with self.subTest(language=language,key=key):
                    self.assertIn(key,table)
                    self.assertEqual(placeholders(table[key]),placeholders(_TRANSLATIONS['en'][key]))
