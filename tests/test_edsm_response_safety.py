"""Phase 1: real uploader, temporary journals/settings, synthetic HTTP only."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.error import URLError
from urllib.parse import parse_qs

from PySide6.QtCore import QSettings
from cmdrhelper import edsm_uploader as api
from cmdrhelper.edsm_upload_status import observe, publish
from cmdrhelper.ui.edsm_status import presentation


class Response(io.BytesIO):
    def __init__(self, reply, status=200):
        super().__init__(json.dumps(reply).encode())
        self.status = status


class ResponseSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / 'Journal.2026-01-01T000000.01.log'
        self.settings_path = self.root / 'settings.ini'
        self.settings = QSettings(str(self.settings_path), QSettings.IniFormat)
        guard = patch.object(api, 'urlopen', side_effect=AssertionError('No real network'))
        self.transport = guard.start()
        self.addCleanup(guard.stop)
        self.state = SimpleNamespace(commander_fid='F-A', edsm_enabled=True,
                                     changed=Mock(), _edsm_runtime_by_fid={})
        publish(self.state)

    def prepare(self, count, fid='F-A'):
        rows = [dict(event='Fileheader', gameversion='4.0', build='synthetic'),
                dict(event='Commander', FID='F-A', Name='Synthetic')]
        prefix = ''.join(json.dumps(e)+'\n' for e in rows).encode()
        self.start = len(prefix)
        self.event_bytes = [(json.dumps(dict(event='Scan', BodyID=i,
                           timestamp='2026-01-01T00:00:00Z'))+'\n').encode() for i in range(count)]
        self.original = prefix + b''.join(self.event_bytes)
        self.path.write_bytes(self.original)
        u = self.instance(fid)
        u.settings.setValue(u._initialized_key, True)
        u._set_position(self.path, self.start)
        return u

    def instance(self, fid='F-A', settings=None):
        u = api.EDSMJournalUploader('Synthetic', 'SYNTHETIC-KEY',
            settings if settings is not None else self.settings, fid)
        u._discarded = set()
        return u

    def run_reply(self, u, reply, status=200):
        self.transport.side_effect = None
        self.transport.return_value = Response(reply, status)
        result = u.process_folder(self.root)
        observe(self.state, u.fid, 'synthetic', result)
        self.assertEqual(self.path.read_bytes(), self.original)
        return result

    @staticmethod
    def reply(codes, total=100):
        return dict(msgnum=total, events=[dict(msgnum=code) for code in codes])

    def test_all_documented_and_unknown_event_codes(self):
        completed = {100, 101, 102, 103, 104, 304}
        registered = {100, 101, 102, 103}
        codes = [100, 101, 102, 103, 104, 201, 202, 203, 204, 205, 206, 207,
                 208, 301, 302, 303, 304, 401, 402, 451, 452, 453, 500, 501, 199, 599]
        for code in codes:
            with self.subTest(code=code):
                u = self.prepare(1)
                api.EDSMJournalUploader._retry_after.pop(u._identity, None)
                r = self.run_reply(u, self.reply([code]))
                self.assertEqual(u._stored_position(self.path),
                    len(self.original) if code in completed else self.start)
                self.assertEqual(r['events_stored'], int(code == 100))
                self.assertEqual(r['events_confirmed'], int(code in registered))
                self.assertEqual(r['confirmation_complete'], code in completed)
                self.assertEqual(bool(r['error']), code not in completed)
                self.assertEqual(r.get('retry_scheduled', False), code not in completed)
                self.assertEqual(r['event_outcomes'], {api.EVENT_OUTCOMES.get(code, 'unknown'): 1})
                if code not in registered:
                    self.assertNotEqual(presentation(self.state)[1], 'statusOk')
                    self.assertEqual(self.state.edsm_upload_details['confirmed'], 0)

    def test_full_success_and_duplicates_are_not_newly_stored(self):
        for codes, stored in [([100]*3, 3), ([101, 102, 103], 0)]:
            with self.subTest(codes=codes):
                u = self.prepare(3)
                r = self.run_reply(u, self.reply(codes))
                self.assertEqual(r['events_stored'], stored)
                self.assertEqual(r['events_confirmed'], 3)
                self.assertEqual(r['events_sent'], 3)
                self.assertEqual(u._stored_position(self.path), len(self.original))
                self.assertEqual(presentation(self.state)[1], 'statusOk')

    def test_missing_wrong_length_and_malformed_lists_never_advance(self):
        replies = [dict(msgnum=100), dict(msgnum=100, events=None), self.reply([]),
                   self.reply([100]), self.reply([100]*3), dict(msgnum=100, events={}),
                   dict(msgnum=100, events=[dict(msgnum=100), None]),
                   dict(msgnum=100, events=[dict(msgnum=100), {}])]
        for bad_code in (True, '100', 100.0, None, 0, 600):
            replies.append(self.reply([100, bad_code]))
        for reply in replies:
            with self.subTest(reply=reply):
                u = self.prepare(2)
                api.EDSMJournalUploader._retry_after.pop(u._identity, None)
                r = self.run_reply(u, reply)
                self.assertEqual(u._stored_position(self.path), self.start)
                self.assertEqual(r['events_confirmed'], 0)
                self.assertFalse(r['confirmation_complete'])
                self.assertNotEqual(presentation(self.state)[1], 'statusOk')

    def test_rejected_unknown_and_contradictory_envelopes_never_release_prefix(self):
        for total in (101, 104, 199, 203, 304, 402, 500, 501, 599, True, '100', None):
            with self.subTest(total=total):
                u = self.prepare(2)
                api.EDSMJournalUploader._retry_after.pop(u._identity, None)
                reply = self.reply([100, 100], total)
                r = self.run_reply(u, reply)
                self.assertTrue(r['error'])
                self.assertEqual(u._confirm_prefix(self.path, [self.start+1]*2, reply), 0)
                self.assertEqual(u._stored_position(self.path), self.start)
                self.assertNotEqual(presentation(self.state)[1], 'statusOk')

    def test_failed_or_unknown_http_cannot_be_overridden_by_api_success(self):
        for status in (None, 199, 302, 400, 500, '200', True):
            with self.subTest(status=status):
                u = self.prepare(1)
                api.EDSMJournalUploader._retry_after.pop(u._identity, None)
                r = self.run_reply(u, self.reply([100]), status)
                self.assertTrue(r['error'])
                self.assertEqual(u._stored_position(self.path), self.start)
                self.assertEqual(r['events_confirmed'], 0)

    def test_gap_retries_confirmed_suffix_without_local_journal_reprocessing(self):
        u = self.prepare(4)
        r = self.run_reply(u, self.reply([100, 100, 402, 100]))
        expected = self.start + sum(map(len, self.event_bytes[:2]))
        self.assertEqual(u._stored_position(self.path), expected)
        self.assertEqual(r['events_sent'], 2)
        self.assertEqual(r['events_confirmed'], 3)
        self.assertFalse(r['confirmation_complete'])
        self.assertNotEqual(presentation(self.state)[1], 'statusOk')
        deadline = u._retry_after[u._identity]
        with patch.object(api.time, 'monotonic', return_value=deadline + 1):
            r = self.run_reply(u, self.reply([100, 103]))
        sent = json.loads(parse_qs(self.transport.call_args.args[0].data.decode())['message'][0])
        self.assertEqual([e['BodyID'] for e in sent], [2, 3])
        self.assertEqual(r['events_stored'], 1)
        self.assertEqual(u._stored_position(self.path), len(self.original))
        # Only the uploader reads these files; no ingestion/merit callbacks exist.
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertEqual(self.transport.call_count, 2)
        u.process_folder(self.root)
        self.assertEqual(self.transport.call_count, 2)

    def test_transport_timeout_and_retry_after_unclear_response(self):
        for failure in (URLError('SYNTHETIC-PRIVATE'), TimeoutError('SYNTHETIC-PRIVATE'), None):
            with self.subTest(failure=type(failure).__name__):
                u = self.prepare(1)
                api.EDSMJournalUploader._retry_after.pop(u._identity, None)
                if failure is None:
                    r = self.run_reply(u, dict(msgnum=100))
                else:
                    self.transport.side_effect = failure
                    r = u.process_folder(self.root)
                self.assertTrue(r['error'])
                self.assertNotIn('SYNTHETIC-PRIVATE', r['error'])
                self.assertEqual(u._stored_position(self.path), self.start)
                before = self.transport.call_count
                self.assertTrue(u.process_folder(self.root)['retry_paused'])
                self.assertEqual(self.transport.call_count, before)
                with patch.object(api.time, 'monotonic', return_value=u._retry_after[u._identity]+1):
                    r = self.run_reply(u, self.reply([100]))
                self.assertFalse(r['error'])
                self.assertEqual(u._stored_position(self.path), len(self.original))

    def test_restart_reloads_pending_position_and_commander_isolation(self):
        u = self.prepare(2)
        self.run_reply(u, dict(msgnum=100))
        # New process: volatile retry state disappears, persistent offset remains.
        api.EDSMJournalUploader._retry_after.pop(u._identity, None)
        settings = QSettings(str(self.settings_path), QSettings.IniFormat)
        restarted = self.instance(settings=settings)
        self.assertEqual(restarted._stored_position(self.path), self.start)
        foreign = self.instance('F-B', settings)
        foreign.settings.setValue(foreign._initialized_key, True)
        before = self.transport.call_count
        foreign.process_folder(self.root)
        self.assertEqual(self.transport.call_count, before)
        self.assertEqual(foreign._stored_position(self.path), 0)
        restarted.is_current = lambda: False
        self.assertTrue(restarted.process_folder(self.root)['cancelled'])
        self.assertEqual(self.transport.call_count, before)
        restarted.is_current = lambda: True
        self.run_reply(restarted, self.reply([100, 100]))
        self.assertEqual(restarted._stored_position(self.path), len(self.original))
        self.assertEqual(foreign._stored_position(self.path), 0)

    def test_full_batch_boundary_uses_same_validation_as_tail(self):
        for reply in (dict(msgnum=100), self.reply([100, 500]), self.reply([100, 100])):
            with self.subTest(reply=reply), patch.object(api, 'BATCH_SIZE', 2):
                u = self.prepare(2)
                api.EDSMJournalUploader._retry_after.pop(u._identity, None)
                r = self.run_reply(u, reply)
                completed = 0 if 'events' not in reply else (1 if r['error'] else 2)
                self.assertEqual(u._stored_position(self.path),
                    self.start + sum(map(len, self.event_bytes[:completed])))

    def test_upload_retries_do_not_reapply_journal_or_merits(self):
        from datetime import date
        from cmdrhelper.database import CMDRDatabase
        from cmdrhelper.source_processing import SourceProcessor
        u = self.prepare(1)
        extra = [dict(event='Powerplay', Power='Synthetic', Rank=1, Merits=100,
                      timestamp='2026-01-01T00:00:00Z'),
                 dict(event='PowerplayMerits', Power='Synthetic', MeritsGained=50,
                      TotalMerits=150, timestamp='2026-01-01T00:01:00Z')]
        self.original += ''.join(json.dumps(e)+'\n' for e in extra).encode()
        self.path.write_bytes(self.original)
        db = CMDRDatabase(self.root/'synthetic.db')
        processor = SourceProcessor(db, self.root)
        with patch('cmdrhelper.powerplay_store.local_today', return_value=date(2026, 1, 1)):
            processor.process()
            cid = processor.sessions[0]['commander_id']
            self.assertEqual(db.powerplay_merits(cid, power='Synthetic'), 150)
            offsets = [row['last_read_offset'] for row in processor.sessions]
            self.run_reply(u, dict(msgnum=100))
            processor.process()
            self.assertEqual(processor.context['applied_events'], [])
            with patch.object(api.time, 'monotonic', return_value=u._retry_after[u._identity]+1):
                self.run_reply(u, self.reply([100, 100, 100]))
            processor.process()
            self.assertEqual(processor.context['applied_events'], [])
            self.assertEqual([row['last_read_offset'] for row in processor.sessions], offsets)
            self.assertEqual(db.powerplay_merits(cid, power='Synthetic'), 150)
