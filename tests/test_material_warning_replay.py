"""Diagnostic coalescing must never replace or weaken material validation."""
import json
import logging
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cmdrhelper import material_inventory as mi
from cmdrhelper.logging_config import PrivacyFormatter
from test_material_inventory import event, snapshot


class MaterialWarningReplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.reader = mi.MaterialInventoryReader()
        self.bad = event('EngineerCraft', 2, Ingredients=[dict(Name='unknown_private', Count=1)])
        self.row = self.write('one', [snapshot(), self.bad])

    def write(self, name, events, cid=1, fid='TEST-PRIVATE'):
        path = self.root / (name + '.log')
        path.write_text(''.join(json.dumps(e) + '\n' for e in [event('Commander', FID=fid), *events]))
        return dict(journal_file=str(path), commander_id=cid, fid_seen=fid,
                    attribution_status='identified')

    def read(self, rows=None, cid=1, fid='TEST-PRIVATE'):
        with self.assertLogs('cmdrhelper', level='WARNING') as captured:
            inv = self.reader.reconstruct(cid, fid, [self.row] if rows is None else rows)
        records = captured.records
        full = [r for r in records if r.msg == 'Material inventory inconsistency: %s']
        summaries = [r.diagnostic_fields for r in records if r.msg == 'Material inventory repeated findings']
        return inv, full, summaries, records

    def test_first_pair_then_counted_replays_with_full_validation(self):
        first, full, summaries, records = self.read()
        self.assertEqual((len(full), len(records), summaries), (1, 2, []))
        self.assertEqual(records[1].diagnostic_fields['reason'], 'material_invalid_event')
        original = mi._Reducer.apply
        calls = []
        def apply(reducer, event, source):
            calls.append(source)
            return original(reducer, event, source)
        with patch.object(mi._Reducer, 'apply', apply):
            for _ in range(3):
                inv, full, summaries, records = self.read()
                self.assertEqual(inv, first)
                self.assertEqual((len(full), len(records)), (0, 1))
                self.assertEqual(summaries, [dict(component='materials', phase='history',
                    reason='material_invalid_event', status='partial', count=1)])
        self.assertEqual(len(calls), 6)  # Snapshot AND invalid event on every replay.

    def test_distinct_offsets_and_detailed_reasons_are_not_merged(self):
        self.row = self.write('one', [snapshot(), self.bad, self.bad,
            event('EngineerCraft', 3, Ingredients='invalid')])
        self.assertEqual(len(self.read()[1]), 3)
        self.assertEqual(self.read()[2][0]['count'], 3)
        # Same physical event, same broad code, different actual detail is new.
        previous = mi._WarningReplay({})
        with patch.object(mi, '_warn_material'):
            previous.warn('material_invalid_event', 'source:offset: missing field')
        current = mi._WarningReplay(previous.current)
        with patch.object(mi, '_warn_material') as emit:
            current.warn('material_invalid_event', 'source:offset: invalid quantity')
            current.warn('material_underflow', 'source:offset: missing field')
        self.assertEqual(emit.call_count, 2)

    def test_all_reasons_and_categories_keep_stock_status(self):
        events = [snapshot(raw=1, manufactured=1, encoded=1)]
        for category, name in [('Raw', 'sulphur'), ('Manufactured', 'gridresistors'), ('Encoded', 'consumerfirmware')]:
            events += [event('MaterialDiscarded', 2, Category=category, Name=name, Count=2),
                       event('MaterialCollected', 3, Category=category, Name=name, Count=1)]
        events.append(self.bad)
        self.row = self.write('one', events)
        first, full, _, _ = self.read()
        self.assertEqual(len(full), 7)
        second, full, summaries, _ = self.read()
        self.assertEqual(second, first)
        self.assertFalse(second.known)
        self.assertEqual(len(second.material_issues), 3)
        self.assertEqual({s['reason']: s['count'] for s in summaries},
                         dict(material_underflow=3, material_unknown=3, material_invalid_event=1))
        self.assertFalse(full)

    def test_new_error_after_append_visible_immediately(self):
        self.read(); self.read()
        with Path(self.row['journal_file']).open('a') as f:
            f.write(json.dumps(event('Synthesis', 4, Materials='invalid')) + '\n')
        _, full, summaries, _ = self.read()
        self.assertEqual(len(full), 2)  # Conservative generation reset also re-emits old error.
        self.assertEqual(summaries, [])

    def test_commander_and_source_switch_back_reemits(self):
        self.read(); self.read()
        other = self.write('other', [snapshot(), self.bad], cid=2, fid='TEST-OTHER')
        self.assertEqual(len(self.read([other], 2, 'TEST-OTHER')[1]), 1)
        self.assertEqual(len(self.read()[1]), 1)
        source = self.write('source', [snapshot(), self.bad])
        self.assertEqual(len(self.read([source])[1]), 1)
        self.assertEqual(len(self.read()[1]), 1)
        self.row['source_id'] = 'synthetic-other-source'
        self.assertEqual(len(self.read()[1]), 1)

    def test_historical_addition_reassignment_and_removal(self):
        self.read(); self.read()
        history = self.write('history', [snapshot(second=0)])
        self.assertEqual(len(self.read([history, self.row])[1]), 1)
        self.assertEqual(len(self.read()[1]), 1)
        ambiguous = dict(self.row, attribution_status='ambiguous')
        self.reader.reconstruct(1, 'TEST-PRIVATE', [ambiguous])
        self.assertEqual(len(self.read()[1]), 1)

    def test_fid_change_with_same_commander_and_path(self):
        self.read(); self.read()
        self.row = self.write('one', [snapshot(), self.bad], fid='TEST-OTHER')
        self.assertEqual(len(self.read(fid='TEST-OTHER')[1]), 1)
        self.assertFalse(self.read(fid='TEST-OTHER')[1])
        self.row = self.write('one', [snapshot(), self.bad])
        self.assertEqual(len(self.read()[1]), 1)

    def test_corrupt_history_requires_full_diagnostics_on_every_retry(self):
        self.read(); self.read()
        with Path(self.row['journal_file']).open('a') as f:
            f.write('not json\n')
        for _ in range(2):
            inv, full, summaries, _ = self.read()
            self.assertEqual(len(full), 1)
            self.assertFalse(summaries)
            self.assertFalse(inv.known)
            self.assertIsNone(self.reader._warning_basis)

    def test_replacement_even_identical_bytes_and_mtime(self):
        self.read(); self.read()
        path = Path(self.row['journal_file'])
        stat = path.stat()
        replacement = self.root / 'replacement'
        replacement.write_bytes(path.read_bytes())
        os.utime(replacement, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        os.replace(replacement, path)
        self.assertEqual(len(self.read()[1]), 1)

    def test_snapshot_recovers_but_historical_warning_is_counted(self):
        self.row = self.write('one', [snapshot(), self.bad, snapshot(second=4)])
        first = self.read()[0]
        self.assertTrue(first.known)
        self.assertEqual(first.issues, [])
        second, full, summaries, _ = self.read()
        self.assertEqual(first, second)
        self.assertFalse(full)
        self.assertEqual(summaries[0]['count'], 1)

    def test_fixed_then_reintroduced_error_is_visible(self):
        self.read(); self.read()
        self.row = self.write('one', [snapshot()])
        with self.assertNoLogs('cmdrhelper', level='WARNING'):
            self.assertTrue(self.reader.reconstruct(1, 'TEST-PRIVATE', [self.row]).known)
        self.row = self.write('one', [snapshot(), self.bad])
        self.assertEqual(len(self.read()[1]), 1)

    def test_missing_or_unreadable_history_never_suppresses(self):
        self.read(); self.read()
        missing = dict(self.row, journal_file=str(self.root / 'missing'))
        for _ in range(2):
            inv, full, summaries, _ = self.read([self.row, missing])
            self.assertFalse(inv.known)
            self.assertEqual(len(full), 1)
            self.assertFalse(summaries)
        self.assertEqual(len(self.read()[1]), 1)
        with patch.object(self.reader, '_read', side_effect=RuntimeError('synthetic read failure')):
            with self.assertRaises(RuntimeError):
                self.reader.reconstruct(1, 'TEST-PRIVATE', [self.row])
        self.assertEqual(len(self.read()[1]), 1)

    def test_bounded_cache_evicts_without_hiding_findings(self):
        self.row = self.write('one', [snapshot(), *[self.bad for _ in range(5)]])
        with patch.object(mi, '_WARNING_CACHE_LIMIT', 2):
            self.assertEqual(len(self.read()[1]), 5)
            for _ in range(3):
                _, full, summaries, _ = self.read()
                self.assertEqual(len(self.reader._warning_keys), 2)
                self.assertEqual(len(full), 3)
                self.assertEqual(summaries[0]['count'], 2)
                self.assertTrue(all(len(key) == 32 for key in self.reader._warning_keys))

    def test_formatted_first_and_summary_are_private_and_other_logs_unchanged(self):
        first = self.read()[3]
        repeated = self.read()[3]
        formatter = PrivacyFormatter('%(message)s')
        text = '\n'.join(formatter.format(r) for r in first + repeated)
        for secret in ('TEST-PRIVATE', 'unknown_private', self.tmp.name):
            self.assertNotIn(secret, text)
        self.assertIn('count=1', text)
        self.assertIn('reason=material_invalid_event', text)
        self.assertIn('status=partial', text)
        with self.assertLogs('cmdrhelper', level='WARNING') as other:
            mi.logger.warning('Independent warning')
        self.assertEqual(other.records[0].getMessage(), 'Independent warning')


if __name__ == '__main__':
    unittest.main()
