"""Metadata validation must not certify a damaged archive as imported."""
import json
import tempfile
import unittest
from pathlib import Path

from cmdrhelper.valuation import journal_valuation_context, _journal_context
from cmdrhelper.journal_reader import classify_journal_file
from cmdrhelper.database import CMDRDatabase


class ValuationJournalStructureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(_journal_context.cache_clear)
        self.folder = Path(self.temp.name)
        self.path = self.folder / 'Journal.2026-10-01T120000.01.log'
        self.header = {'event': 'Fileheader', 'gameversion': '4.4', 'Odyssey': False}
        self.load = {'event': 'LoadGame', 'FID': 'TEST', 'Commander': 'Synthetic', 'Odyssey': True}

    def write(self, middle=''):
        _journal_context.cache_clear()
        self.path.write_text(json.dumps(self.header)+'\n'+middle+json.dumps(self.load)+'\n', encoding='utf-8')

    def test_valid_metadata_unchanged(self):
        self.write()
        self.assertEqual(journal_valuation_context(self.path), {'game_version': '4.4', 'odyssey': True})

    def test_invalid_structures_between_valid_events(self):
        values = [[], 12, 1.5, 'text', True, False, None, {}, {'event': None},
                  {'event': []}, {'event': 4}, {'event': ''}, {'event': '  '},
                  {'event': 'LoadGame', 'FID': 123, 'Odyssey': False}]
        for raw in [json.dumps(value) for value in values] + ['{broken}']:
            with self.subTest(raw=raw):
                self.write(raw+'\n')
                with self.assertLogs('cmdrhelper.journal_reader', level='WARNING') as logs:
                    result = journal_valuation_context(self.path)
                self.assertEqual(result, {'game_version': '4.4', 'odyssey': True})
                self.assertEqual(len(logs.output), 1)
                self.assertIn('invalid_journal_structure', logs.output[0])
                self.assertEqual(classify_journal_file(self.path)['attribution_status'], 'unknown')

    def test_warning_bounded_and_cached(self):
        self.write('[]\nnull\n{bad}\n')
        with self.assertLogs('cmdrhelper.journal_reader', level='WARNING') as logs:
            journal_valuation_context(self.path)
            journal_valuation_context(self.path)
        self.assertEqual(len(logs.output), 1)

    def test_unfinished_tail_identity_rule_unchanged(self):
        self.write()
        with self.path.open('a') as handle:
            handle.write('{"event":')
        self.assertEqual(classify_journal_file(self.path)['attribution_status'], 'identified')
        self.assertEqual(journal_valuation_context(self.path), {'game_version': '4.4', 'odyssey': True})

    def test_multiple_files_and_damaged_import_marker(self):
        self.write()
        good = self.path.with_name('Journal.2026-10-01T130000.01.log')
        good.write_text(self.path.read_text(), encoding='utf-8')
        db = CMDRDatabase(self.folder/'test.db')
        db.import_journal_archive(self.folder)
        with db._connect() as con:
            previous = con.execute('SELECT * FROM journal_imports WHERE journal_file=?', (str(good),)).fetchall()
        for raw in ('[]', '{broken}', '{"event": null}'):
            with self.subTest(raw=raw):
                damaged = self.path.with_name('Journal.2026-10-01T140000.01.log')
                damaged.write_text(json.dumps(self.header)+'\n'+raw+'\n'+json.dumps(self.load)+'\n')
                # The metadata reader continues; archive error policy is unchanged.
                self.assertEqual(journal_valuation_context(damaged)['odyssey'], True)
                if raw == '[]':
                    with self.assertRaisesRegex(RuntimeError, 'Fehler beim Journal-Import'):
                        db.import_journal_archive(self.folder)
                else:
                    db.import_journal_archive(self.folder)
                with db._connect() as con:
                    self.assertEqual(con.execute('SELECT attribution_status,fully_imported FROM journal_sessions WHERE journal_file=?', (str(damaged),)).fetchone(), ('unknown', 0))
                    self.assertEqual(con.execute('SELECT * FROM journal_imports WHERE journal_file=?', (str(damaged),)).fetchall(), [])
                    self.assertEqual(con.execute('SELECT * FROM journal_imports WHERE journal_file=?', (str(good),)).fetchall(), previous)
