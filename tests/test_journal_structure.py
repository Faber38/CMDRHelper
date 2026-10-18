import json
import tempfile
import unittest
from pathlib import Path
from cmdrhelper.journal_reader import classify_journal_file, read_latest_state, _LIVE_LINE_CACHE


class JournalStructureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(_LIVE_LINE_CACHE.clear)
        self.path = Path(self.tmp.name) / 'Journal.2026-10-18T000000.01.log'
        self.identity = {'event': 'Commander', 'FID': 'TEST-A', 'Name': 'Synthetic'}

    def write(self, extra):
        self.path.write_text(json.dumps(self.identity) + '\n' + extra, encoding='utf-8')

    def test_nonobject_and_invalid_event_sources_fail_closed(self):
        for value in (None, True, False, 12, 1.25, 'text', [], {}, {'other': 1}, {'event': 3}, {'event': []}):
            with self.subTest(kind=type(value).__name__, value=value):
                self.write(json.dumps(value) + '\n')
                result = classify_journal_file(self.path)
                self.assertEqual(result['attribution_status'], 'unknown')
                self.assertIsNone(result['fid_seen'])

    def test_conflict_not_hidden_by_invalid_line(self):
        self.write('null\n' + json.dumps(dict(self.identity, FID='TEST-B')) + '\n')
        self.assertEqual(classify_journal_file(self.path)['attribution_status'], 'ambiguous')

    def test_malformed_complete_line_and_unfinished_tail(self):
        self.write('{broken}\n')
        self.assertEqual(classify_journal_file(self.path)['attribution_status'], 'unknown')
        self.write('{"event":')
        self.assertEqual(classify_journal_file(self.path)['attribution_status'], 'identified')

    def test_live_cache_does_not_restore_invalid_source(self):
        self.write('')
        session = classify_journal_file(self.path)
        session['commander_id'] = 1
        read_latest_state(self.path.parent, indexed_sessions=[session])
        with self.path.open('a') as stream:
            stream.write('null\n')
        result = read_latest_state(self.path.parent, indexed_sessions=[session])
        current = result['latest_journal_session']
        self.assertEqual(current['attribution_status'], 'unknown')
        self.assertIsNone(current['commander_id'])

    def test_index_continues_and_invalid_source_cannot_commit_delta(self):
        from cmdrhelper.database import CMDRDatabase
        from cmdrhelper.journal_index import scan_journal_folder
        from cmdrhelper.journal_reader import read_journal_delta
        db = CMDRDatabase(self.path.parent / 'synthetic.db')
        self.write('')
        source = scan_journal_folder(db, self.path.parent)[0]
        cid = source['commander_id']
        events, offset = read_journal_delta(self.path, 0)
        db.apply_commander_journal_delta(cid, self.path, events, offset)
        with self.path.open('a') as stream:
            stream.write('null\n' + json.dumps({'event': 'MissionAccepted', 'MissionID': 111}) + '\n')
        other = self.path.with_name('Journal.2026-10-18T010000.01.log')
        other.write_text(json.dumps(dict(self.identity, FID='TEST-B')) + '\n')
        sessions = scan_journal_folder(db, self.path.parent)
        self.assertEqual([s['attribution_status'] for s in sessions], ['unknown', 'identified'])
        self.assertEqual(sessions[0]['last_read_offset'], offset)
        events, end = read_journal_delta(self.path, offset)
        before = db.path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'identity'):
            db.apply_commander_journal_delta(cid, self.path, events, end, enqueue_inara=True)
        self.assertEqual(db.path.read_bytes(), before)
        self.assertEqual(db.inara_pending(cid), [])
        self.assertEqual(db.commander_missions(cid), [])
        events, end = read_journal_delta(other, 0)
        db.apply_commander_journal_delta(sessions[1]['commander_id'], other, events, end)

    def test_invalid_fid_type_and_private_contents_are_not_logged(self):
        self.write(json.dumps({'event': 'Commander', 'FID': ['private-identifier'],
                               'secret': 'private-secret'}) + '\n')
        with self.assertLogs('cmdrhelper.journal_reader', level='WARNING') as captured:
            result = classify_journal_file(self.path)
        self.assertEqual(result['attribution_status'], 'unknown')
        self.assertEqual(len(captured.output), 1)
        self.assertNotIn('private', captured.output[0])
        self.assertNotIn(str(self.path), captured.output[0])
