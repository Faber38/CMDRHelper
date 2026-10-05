"""Station card pad projection: committed DB reads, without journal or network IO."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication
from cmdrhelper.i18n import get_language, set_language
from cmdrhelper.pad_metadata import resolve_station_pad_counts
from cmdrhelper.station_pad_store import create_schema
from cmdrhelper.ui.stations_view import StationsView


class PadDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.addCleanup(set_language, get_language())
        set_language('de')
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        self.db = self.folder / 'pads.db'
        with sqlite3.connect(self.db) as con:
            create_schema(con)
            con.execute('INSERT INTO station_pad_journals VALUES(1,?,?,?,?,?,?,?,?)',
                        (str(self.folder / 'Journal.log'), str(self.folder), '[]', 100, 1, '{}', b'', b''))
        self.station = dict(market_id=2, station_name='Port', station_type='Outpost', parent_body_id=None)
        self.view = StationsView()
        self.addCleanup(self.view.close)
        self.addCleanup(self.view.deleteLater)

    def evidence(self, counts=(7, 13, 9), name='Port', address=42):
        with sqlite3.connect(self.db) as con:
            con.execute('INSERT INTO station_pad_evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                        (1, (2).to_bytes(8, 'big'), address.to_bytes(8, 'big'), 'Test', name,
                         'Outpost', counts[2], counts[1], counts[0], 'local_elite', 'Docked',
                         '2026-01-01T00:00:00Z', 0))

    def display(self, stations=None):
        model = resolve_station_pad_counts(stations or [self.station], 'Test', 42, self.db, self.folder)
        self.view.set_system(42, 'Test', model)
        return self.view.cards[0]

    def test_local_and_details_share_counts_preserving_unknown(self):
        self.evidence()
        card = self.display()
        self.assertEqual(card.subtitle.text(), 'Außenposten · Unbekannt | Landeplätze: L: 7 · M: 13 · S: 9')
        card._toggle(True)
        self.assertIn('Landeplätze: L: 7 · M: 13 · S: 9', card.details.external_info.text())

    def test_settlement_with_zero_large_and_medium(self):
        self.station.update(station_type='OnFootSettlement', parent_body_id=5, body_name='Test B 5 b')
        self.evidence((0, 0, 1))
        self.assertEqual(self.display().subtitle.text(),
                         'Siedlung · B 5 b | Landeplätze: L: 0 · M: 0 · S: 1')

    def test_unknown_unchanged(self):
        self.assertEqual(self.display().subtitle.text(), 'Außenposten · Unbekannt')

    def test_spansh_fallback_and_local_priority(self):
        self.station['spansh'] = {'landing_pads': dict(large=1, medium=2, small=3)}
        self.assertIn('L: 1 · M: 2 · S: 3', self.display().subtitle.text())
        self.evidence()
        self.assertIn('L: 7 · M: 13 · S: 9', self.display().subtitle.text())
        self.assertEqual(self.station['spansh']['landing_pads']['large'], 1)

    def test_incomplete_invalid_and_zero_counts(self):
        for pads in ({'large': 1}, dict(large=True, medium=1, small=2),
                     dict(large=-1, medium=1, small=2)):
            self.station['spansh'] = {'landing_pads': pads}
            self.assertEqual(self.display().subtitle.text(), 'Außenposten · Unbekannt')
        self.evidence((0, 0, 0))
        self.assertIn('L: 0 · M: 0 · S: 0', self.display().subtitle.text())

    def test_identity_mismatch_not_guessed(self):
        self.evidence(name='Other Port')
        self.assertEqual(self.display().subtitle.text(), 'Außenposten · Unbekannt')

    def test_batch_one_query_no_journal_read_or_import(self):
        self.evidence()
        queries = []
        connect = sqlite3.connect
        def traced(*args, **kwargs):
            self.assertTrue(kwargs['uri'])
            self.assertTrue(args[0].endswith('?mode=ro'))
            con = connect(*args, **kwargs)
            con.set_trace_callback(queries.append)
            return con
        stations = [dict(self.station, market_id=i) for i in range(1, 15)]
        with patch('cmdrhelper.pad_metadata.sqlite3.connect', side_effect=traced), \
             patch('cmdrhelper.station_pad_store.read_local', side_effect=AssertionError('import')), \
             patch('cmdrhelper.spansh_stations.SpanshStations.refresh_system', side_effect=AssertionError('network')), \
             patch.object(Path, 'open', side_effect=AssertionError('file read')):
            self.display(stations)
            for card in self.view.cards:
                card._toggle(True)
        self.assertEqual(len(queries), 1)
        self.assertTrue(queries[0].startswith('SELECT'))

    def test_main_window_refresh_supplies_local_counts(self):
        from cmdrhelper.ui.main_window import MainWindow
        self.evidence()
        window = SimpleNamespace(stations_view=self.view, explorer_tabs=Mock(),
            state=SimpleNamespace(system='Test', system_address=42, system_stations=[self.station],
                                  database=SimpleNamespace(path=self.db), journal_folder=self.folder))
        MainWindow._refresh_stations_tab(window)
        self.assertIn('L: 7 · M: 13 · S: 9', self.view.cards[0].subtitle.text())

    def test_db_error_is_visible_in_log_without_import(self):
        with patch('cmdrhelper.pad_metadata.sqlite3.connect', side_effect=sqlite3.OperationalError('broken')), \
             self.assertLogs('cmdrhelper.pad_metadata', level='ERROR'):
            self.assertEqual(self.display().subtitle.text(), 'Außenposten · Unbekannt')
