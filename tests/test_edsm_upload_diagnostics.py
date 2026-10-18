"""Upload diagnostics with disposable journals and simulated transports only."""
import io
import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from PySide6.QtCore import QSettings
from cmdrhelper import edsm_uploader as uploader
from cmdrhelper.logging_config import PrivacyFormatter, log_event, sanitize


class Response(io.BytesIO):
    status = 200


class UploadDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.stream = io.StringIO()
        self.logger = uploader.logger
        previous = self.logger.handlers[:], self.logger.level, self.logger.propagate
        def restore():
            self.logger.handlers, self.logger.level, self.logger.propagate = previous
        self.addCleanup(restore)
        handler = logging.StreamHandler(self.stream)
        handler.setFormatter(PrivacyFormatter('%(message)s'))
        self.logger.handlers = [handler]
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self.guard = patch.object(uploader, 'urlopen', side_effect=AssertionError('No real requests'))
        self.transport = self.guard.start()
        self.addCleanup(self.guard.stop)

    def upload(self, reply=None, error=None, count=2):
        self.transport.side_effect = error
        self.transport.return_value = Response(json.dumps(reply).encode())
        return uploader.upload_events('SYNTHETIC-NAME', 'SYNTHETIC-KEY', '4', 'test',
                                      [{'event': 'Scan', 'ServerToken': 'SYNTHETIC-TOKEN'}] * count)

    def test_success_and_private_payloads(self):
        result = self.upload({'msgnum': 100, 'msg': 'SYNTHETIC-RESPONSE',
                              'events': [{'msgnum': 100}, {'msgnum': 500}]})
        self.assertTrue(result[0])
        text = self.stream.getvalue()
        for field in ('http_status=200', 'prepared_events=2', 'confirmed_events=2',
                      'response_check=accepted', 'edsm_code=100'):
            self.assertIn(field, text)
        for secret in ('SYNTHETIC-NAME', 'SYNTHETIC-KEY', 'SYNTHETIC-TOKEN',
                       'SYNTHETIC-RESPONSE', 'Scan', 'commanderName', 'message='):
            self.assertNotIn(secret, text)
        self.assertEqual(self.transport.call_count, 1)

    def test_http_200_rejection_is_not_success(self):
        self.assertFalse(self.upload({'msgnum': 203})[0])
        text = self.stream.getvalue()
        self.assertIn('http_status=200', text)
        self.assertIn('response_check=rejected', text)
        self.assertIn('confirmed_events=unknown', text)

    def test_rate_limit_preserves_retry_after(self):
        error = HTTPError('synthetic', 429, 'SYNTHETIC-KEY', {'Retry-After': '600'}, None)
        result = self.upload(error=error)
        self.assertEqual(result[1], {'retry_after_seconds': 600.0})
        self.assertIn('http_status=429', self.stream.getvalue())
        self.assertIn('response_check=transport_error', self.stream.getvalue())
        self.assertNotIn('SYNTHETIC-KEY', self.stream.getvalue())

    def test_timeout_has_no_invented_status_or_confirmation(self):
        self.assertFalse(self.upload(error=TimeoutError('SYNTHETIC-KEY'))[0])
        self.assertIn('http_status=unknown', self.stream.getvalue())
        self.assertIn('confirmed_events=unknown', self.stream.getvalue())
        self.assertIn('response_check=transport_error', self.stream.getvalue())

    def test_partial_confirmation_counts_explicit_acknowledgements(self):
        self.assertFalse(self.upload({'msgnum': 100, 'events': [
            {'msgnum': 100}, {'msgnum': 400}, {'msgnum': 100}]}, count=3)[0])
        self.assertIn('confirmed_events=2', self.stream.getvalue())
        self.assertIn('response_check=partial', self.stream.getvalue())

    def test_missing_malformed_or_mismatched_confirmations_stay_unknown(self):
        for reply in ({'msgnum': 100}, {'msgnum': 100, 'events': []},
                      {'msgnum': 100, 'events': [{'msgnum': 100}, {}]},
                      {'msgnum': 100, 'events': [{'msgnum': 100}, {'msgnum': True}]},
                      {'msgnum': 100, 'events': [{'msgnum': 100}, {'msgnum': '100'}]}, []):
            with self.subTest(reply=reply):
                self.stream.seek(0); self.stream.truncate()
                self.upload(reply)
                self.assertIn('confirmed_events=unknown', self.stream.getvalue())
        # Preserve the existing aggregate-success contract without inventing a count.
        self.assertTrue(self.upload({'msgnum': 100})[0])

    def process(self, reply, *, skip=False):
        p = self.root / 'Journal.synthetic.log'
        header = [{'event': 'Fileheader', 'gameversion': '4', 'build': 'test'},
                  {'event': 'Commander', 'FID': 'F-SYNTHETIC', 'Name': 'Synthetic'}]
        prefix = ''.join(json.dumps(e)+'\n' for e in header).encode()
        events = [{'event': 'Scan'}, {'event': 'Scan'}]
        if skip:
            events.append({'event': 'Music'})
        p.write_bytes(prefix + ''.join(json.dumps(e)+'\n' for e in events).encode())
        settings = QSettings(str(self.root/'settings.ini'), QSettings.IniFormat)
        u = uploader.EDSMJournalUploader('Synthetic', 'SYNTHETIC-KEY', settings, 'F-SYNTHETIC')
        settings.setValue(u._initialized_key, True)
        u._set_position(p, len(prefix))
        u._discarded = {'Music'}
        self.transport.side_effect = None
        self.transport.return_value = Response(json.dumps(reply).encode())
        result = u.process_folder(self.root)
        return result, u._stored_position(p), len(prefix), p

    def test_progress_and_skipped_events(self):
        result, position, start, p = self.process(
            {'msgnum': 100, 'events': [{'msgnum': 100}, {'msgnum': 100}]}, skip=True)
        self.assertEqual(result['events_skipped'], 1)
        self.assertEqual(position, p.stat().st_size)
        self.assertIn('skipped_events=1', self.stream.getvalue())
        self.assertIn('position_advanced=True', self.stream.getvalue())
        self.assertEqual(self.transport.call_count, 1)
        self.assertNotIn(str(self.root), self.stream.getvalue())

    def test_failure_does_not_advance_pending_events(self):
        result, position, start, _ = self.process({'msgnum': 203})
        self.assertTrue(result['error'])
        self.assertEqual(position, start)
        self.assertIn('position_advanced=False', self.stream.getvalue())

    def test_partial_response_advances_only_confirmed_prefix(self):
        result, position, start, p = self.process(
            {'msgnum': 100, 'events': [{'msgnum': 100}, {'msgnum': 400}]})
        self.assertEqual(result['events_sent'], 1)
        self.assertGreater(position, start)
        self.assertLess(position, p.stat().st_size)
        self.assertIn('confirmed_events=1', self.stream.getvalue())
        self.assertIn('position_advanced=True', self.stream.getvalue())

    def test_allowlist_and_argument_suppression(self):
        log_event(self.logger, 'Synthetic diagnostic', prepared_events=2, confirmed_events='unknown',
                  http_status=200, position_advanced=True, api_key='SYNTHETIC-KEY',
                  ServerToken='SYNTHETIC-TOKEN', FID='F999999', response_body='SYNTHETIC-BODY')
        log_event(self.logger, 'Invalid fields', prepared_events=True, confirmed_events=-1,
                  skipped_events='SYNTHETIC-KEY', http_status=999, position_advanced=1,
                  response_check='SYNTHETIC-TOKEN', edsm_code={'secret': 123})
        self.logger.info('Arguments %s %s', 42, 'SYNTHETIC-KEY')
        text = self.stream.getvalue()
        self.assertIn('prepared_events=2', text)
        self.assertIn('Arguments [redacted] [redacted]', text)
        self.assertIn('Invalid fields\n', text)
        for secret in ('SYNTHETIC-KEY', 'SYNTHETIC-TOKEN', 'SYNTHETIC-BODY', 'F999999'):
            self.assertNotIn(secret, text)

    def test_process_authentication_arguments_are_redacted(self):
        for key in ('ServerToken', '--api-key', 'Authorization', 'OAuthToken', 'password', 'FID'):
            for separator in (' ', '=', ':'):
                value = f'process {key}{separator}SYNTHETIC-SECRET SECOND-TOKEN /other option'
                self.assertNotIn('SYNTHETIC-SECRET', sanitize(value))
                self.assertNotIn('SECOND-TOKEN', sanitize(value))
                self.logger.info(value)
        self.assertNotIn('SYNTHETIC-SECRET', self.stream.getvalue())
        self.assertNotIn('SECOND-TOKEN', self.stream.getvalue())

    def test_no_request_means_no_server_confirmation_log(self):
        self.assertTrue(uploader.upload_events('Synthetic', 'SYNTHETIC', '4', 'test', [])[0])
        self.assertFalse(uploader.upload_events('', 'SYNTHETIC', '4', 'test', [{}])[0])
        self.transport.assert_not_called()
        self.assertEqual(self.stream.getvalue(), '')

    def test_invalid_json_retains_http_status_but_not_body(self):
        self.transport.side_effect = None
        self.transport.return_value = Response(b'SYNTHETIC-PRIVATE-BODY')
        result = uploader.upload_events('Synthetic', 'SYNTHETIC', '4', 'test', [{}])
        self.assertFalse(result[0])
        text = self.stream.getvalue()
        self.assertIn('http_status=200', text)
        self.assertIn('response_check=unknown', text)
        self.assertNotIn('SYNTHETIC-PRIVATE-BODY', text)

    def test_complete_rejection_has_explicit_zero_confirmations(self):
        self.assertFalse(self.upload({'msgnum': 100, 'events': [
            {'msgnum': 400}, {'msgnum': 400}]})[0])
        self.assertIn('confirmed_events=0', self.stream.getvalue())
        self.assertIn('response_check=rejected', self.stream.getvalue())

    def test_full_batch_path_keeps_request_count_and_progress(self):
        with patch.object(uploader, 'BATCH_SIZE', 2):
            result, position, _, p = self.process(
                {'msgnum': 100, 'events': [{'msgnum': 100}, {'msgnum': 100}]})
        self.assertEqual(result['events_sent'], 2)
        self.assertEqual(position, p.stat().st_size)
        self.assertEqual(self.transport.call_count, 1)
        self.assertIn('confirmed_events=2', self.stream.getvalue())

    def test_formatter_revalidates_direct_extra(self):
        self.logger.info('Synthetic extra', extra={'diagnostic_fields': {
            'prepared_events': 'SYNTHETIC-SECRET', 'response_check': 'SYNTHETIC-SECRET',
            'http_status': 200, 'request_body': 'SYNTHETIC-SECRET'}})
        self.assertIn('http_status=200', self.stream.getvalue())
        self.assertNotIn('SYNTHETIC-SECRET', self.stream.getvalue())
