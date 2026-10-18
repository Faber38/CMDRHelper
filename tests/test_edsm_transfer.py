"""Synthetic EDSM transfer regressions; all network transports are replaced."""
import io
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from cmdrhelper.edsm_uploader import EDSMJournalUploader, upload_events
from cmdrhelper.edsm_system_status import EdsmSystemStatus
from tests import test_edsm_commander_settings as settings_tests


class TransferTests(unittest.TestCase):
    def setUp(self):
        settings_tests.EDSMCommanderSettingsTests.setUp(self)
        for target in ('cmdrhelper.edsm_uploader.urlopen', 'cmdrhelper.online_services.urlopen'):
            guard = patch(target, side_effect=AssertionError('Unexpected network access'))
            guard.start()
            self.addCleanup(guard.stop)
        self.state.system = 'Synthetic'
        self.state._edsm_request_system = ''
        self.state.system_bodies = []
        self.state._edsm_receive_generation = 0
        self.state.edsm_receive_enabled = False

    def tearDown(self):
        self.temp.cleanup()

    def journal(self, fid='F-A', name='Journal.A.log', extra=()):
        path = Path(self.temp.name) / name
        events = [dict(event='Fileheader', gameversion='4.0', build='synthetic'),
                  dict(event='Commander', FID=fid, Name='Alpha'),
                  dict(event='Scan', BodyName='Synthetic A'), *extra]
        path.write_text(''.join(json.dumps(e)+'\n' for e in events))
        return path

    def uploader(self):
        uploader = EDSMJournalUploader('Alpha', 'SYNTHETIC', self.settings, 'F-A')
        self.settings.setValue(uploader._initialized_key, True)
        uploader._discarded = {'Fileheader', 'Commander', 'Music'}
        return uploader

    def test_four_combinations_and_no_key_receive(self):
        for send in (False, True):
            for receive in (False, True):
                self.state.set_edsm_settings('Alpha', 'SYNTHETIC', send,
                                             receive_enabled=receive)
                self.state._edsm_upload_running = False
                self.state._edsm_request_system = ''
                with patch('cmdrhelper.state.threading.Thread') as thread, patch(
                    'cmdrhelper.state.load_cached_edsm_bodies', return_value=None):
                    self.state._upload_journal_to_edsm()
                    self.assertEqual(thread.call_count, int(send))
                    self.state._request_edsm_for_current_system()
                    self.assertEqual(thread.call_count, int(send) + int(receive))
        self.state.set_edsm_settings(api_key='', enabled=True, receive_enabled=True)
        self.state._edsm_request_system = ''
        with patch('cmdrhelper.state.threading.Thread') as thread, patch(
                'cmdrhelper.state.load_cached_edsm_bodies', return_value=None):
            self.state._upload_journal_to_edsm()
            thread.assert_not_called()
            self.state._request_edsm_for_current_system()
            thread.assert_called_once()

    def test_legacy_preference_is_frozen_without_touching_credentials_or_positions(self):
        prefix = 'edsm/commanders/F-A/'
        self.settings.setValue(prefix+'enabled', True)
        self.settings.setValue(prefix+'api_key', 'SYNTHETIC')
        self.settings.setValue('edsm_upload/positions/old', 345)
        self.state.set_edsm_settings(enabled=False)
        config = self.state.edsm_settings_for_fid('F-A')
        self.assertTrue(config['receive_enabled'])
        self.assertFalse(config['enabled'])
        self.assertEqual(config['api_key'], 'SYNTHETIC')
        self.assertEqual(self.settings.value('edsm_upload/positions/old'), 345)
        self.state.set_edsm_settings(receive_enabled=False)
        self.assertFalse(self.state.edsm_enabled)

    def test_failed_batch_cannot_skip_pending_events_and_retry_is_not_duplicated(self):
        journal = self.journal(extra=[dict(event='Music')])
        uploader = self.uploader()
        with patch('cmdrhelper.edsm_uploader.upload_events', return_value=(False,None,'offline')) as post:
            self.assertEqual(uploader.process_folder(Path(self.temp.name))['error'], 'offline')
            self.assertLess(uploader._stored_position(journal), journal.stat().st_size)
            uploader.process_folder(Path(self.temp.name))
            self.assertEqual(post.call_count, 1)
        EDSMJournalUploader._retry_after[uploader._identity] = 0
        with patch('cmdrhelper.edsm_uploader.upload_events', return_value=(True,{},'')) as post:
            self.assertEqual(uploader.process_folder(Path(self.temp.name))['events_sent'], 1)
            self.assertEqual(uploader._stored_position(journal), journal.stat().st_size)
            uploader.process_folder(Path(self.temp.name))
            self.assertEqual(post.call_count, 1)

    def test_invalid_source_is_not_uploaded_or_advanced(self):
        journal = self.journal()
        with journal.open('a') as stream:
            stream.write('invalid json\n')
        uploader = self.uploader()
        before = uploader._stored_position(journal)
        with patch('cmdrhelper.edsm_uploader.upload_events') as post:
            uploader.process_folder(Path(self.temp.name))
            post.assert_not_called()
        self.assertEqual(uploader._stored_position(journal), before)

    def test_only_unambiguous_matching_fid_is_uploaded(self):
        self.journal()
        self.journal('F-B', 'Journal.B.log')
        self.journal('', 'Journal.C.log')
        self.journal('F-A', 'Journal.D.log', [dict(event='Commander', FID='F-B')])
        uploader = self.uploader()
        with patch('cmdrhelper.edsm_uploader.upload_events', return_value=(True,{},'')) as post:
            result = uploader.process_folder(Path(self.temp.name))
            self.assertEqual(result['events_sent'], 1)
            self.assertEqual(post.call_count, 1)
        self.assertEqual(uploader._stored_position(Path(self.temp.name)/'Journal.B.log'), 0)

    def test_truncation_and_initialization_preserve_progress(self):
        journal = self.journal()
        uploader = self.uploader()
        uploader._set_position(journal, 9999)
        self.settings.setValue(uploader._initialized_key, False)
        uploader.process_folder(Path(self.temp.name))
        self.assertEqual(uploader._stored_position(journal), 9999)
        self.assertTrue(uploader.process_folder(Path(self.temp.name))['error'])
        self.assertEqual(uploader._stored_position(journal), 9999)

    def test_partial_line_waits_and_partial_acknowledgement_fails(self):
        journal = self.journal()
        uploader = self.uploader()
        with journal.open('ab') as f:
            f.write(b'{"event":"Scan"')
        with patch('cmdrhelper.edsm_uploader.upload_events', return_value=(True,{},'')):
            uploader.process_folder(Path(self.temp.name))
        self.assertLess(uploader._stored_position(journal), journal.stat().st_size)
        with patch('cmdrhelper.edsm_uploader.urlopen', return_value=io.BytesIO(
                b'{"msgnum":100,"events":[{"msgnum":400}]}')):
            self.assertFalse(upload_events('Alpha','SYNTHETIC','4','test',[{}])[0])

    def test_receive_stale_response_and_hud_disabled(self):
        self.state.set_edsm_settings(enabled=False, receive_enabled=True)
        old = ('Synthetic', 'F-A', self.state._edsm_receive_generation)
        self.state.set_edsm_settings(receive_enabled=False)
        self.state._on_edsm_bodies_ready(old, {'bodies':[{'name':'Wrong'}]}, 'network')
        self.assertEqual(self.state.system_bodies, [])
        pool, fetch = Mock(), Mock()
        status = EdsmSystemStatus(self.settings, pool=pool, fetch=fetch,
                                 receive_allowed=lambda: self.state.edsm_receive_enabled)
        status.set_enabled(True)
        status.observe([dict(event='Location', StarSystem='Synthetic')], 'F-A')
        pool.start.assert_not_called()
        fetch.assert_not_called()

    def test_partial_batch_retries_only_after_confirmed_prefix(self):
        journal = self.journal(extra=[dict(event='Scan', BodyName='Synthetic B')])
        uploader = self.uploader()
        reply = {'msgnum':100, 'events':[{'msgnum':100}, {'msgnum':400}]}
        with patch('cmdrhelper.edsm_uploader.upload_events', return_value=(False,reply,'retry')):
            self.assertEqual(uploader.process_folder(Path(self.temp.name))['events_sent'], 1)
        EDSMJournalUploader._retry_after[uploader._identity] = 0
        with patch('cmdrhelper.edsm_uploader.upload_events', return_value=(True,{},'')) as post:
            uploader.process_folder(Path(self.temp.name))
        self.assertEqual([e['BodyName'] for e in post.call_args.args[4]], ['Synthetic B'])
        self.assertEqual(uploader._stored_position(journal), journal.stat().st_size)

    def test_transport_errors_and_credential_check_do_not_leak_keys(self):
        from urllib.error import URLError, HTTPError
        from cmdrhelper.online_services import test_edsm_connection
        for error in (URLError('offline'), TimeoutError(),
                      HTTPError('synthetic',429,'rate limit',{},None)):
            with patch('cmdrhelper.edsm_uploader.urlopen', side_effect=error):
                self.assertFalse(upload_events('Alpha','SYNTHETIC','4','test',[{}])[0])
        with patch('cmdrhelper.online_services.urlopen', side_effect=RuntimeError('SYNTHETIC_SECRET')), \
                self.assertLogs('cmdrhelper.online_services', level='WARNING') as logs:
            ok, message = test_edsm_connection('Alpha','SYNTHETIC_SECRET')
        self.assertFalse(ok)
        self.assertNotIn('SYNTHETIC_SECRET', message + ''.join(logs.output))

    def test_queued_receive_worker_is_cancelled_after_commander_switch(self):
        self.state.set_edsm_settings(enabled=False, receive_enabled=True)
        self.state._edsm_request_system = ''
        with patch('cmdrhelper.state.threading.Thread') as thread, patch(
                'cmdrhelper.state.load_cached_edsm_bodies', return_value=None), patch(
                'cmdrhelper.state.fetch_edsm_bodies') as fetch:
            self.state._request_edsm_for_current_system()
            worker = thread.call_args.kwargs['target']
            self.state.commander_fid = 'F-B'
            self.state._load_live_edsm_settings()
            worker()
            fetch.assert_not_called()

    def test_receive_merge_is_idempotent_and_never_calls_database(self):
        self.state.set_edsm_settings(enabled=False, receive_enabled=True)
        self.state.database = Mock()
        local = dict(body_id=1, name='Synthetic A', journal_scanned=True,
                     source='Journal', scan_value=999, was_discovered=False)
        self.state.system_bodies = [dict(local)]
        data = {'bodies':[dict(body_id=1, name='Synthetic A', scan_value=1,
                             was_discovered=True), dict(body_id=2, name='Synthetic B')]}
        self.state._merge_edsm_into_system(data)
        self.state._merge_edsm_into_system(data)
        self.assertEqual(len(self.state.system_bodies), 2)
        own = self.state.system_bodies[0]
        for key, value in local.items():
            self.assertEqual(own[key], value)
        self.assertEqual(self.state.database.mock_calls, [])

    def test_retry_after_is_respected_across_uploader_instances(self):
        from urllib.error import HTTPError
        self.journal()
        uploader = self.uploader()
        error = HTTPError('synthetic', 429, 'rate limit', {'Retry-After':'600'}, None)
        with patch('cmdrhelper.edsm_uploader.time.monotonic', return_value=100), patch(
                'cmdrhelper.edsm_uploader.urlopen', side_effect=error):
            result = uploader.process_folder(Path(self.temp.name))
        self.assertIn('429', result['error'])
        self.assertEqual(uploader._retry_after[uploader._identity], 700)
        other = self.uploader()
        with patch('cmdrhelper.edsm_uploader.time.monotonic', return_value=250):
            self.assertTrue(other.process_folder(Path(self.temp.name))['retry_paused'])
