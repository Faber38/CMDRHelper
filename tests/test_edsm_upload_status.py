"""Volatile upload evidence: no files, requests, checkpoint or retry mutations."""
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from cmdrhelper.edsm_upload_status import observe, publish, retire_source
from cmdrhelper.ui.edsm_status import presentation
from cmdrhelper.i18n import tr


class UploadEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.state = SimpleNamespace(commander_fid='A', edsm_enabled=True,
            _edsm_runtime_by_fid={}, changed=Mock(), _startup_cancel=threading.Event())
        publish(self.state)

    def result(self, **result):
        observe(self.state, 'A', ('steam', 1), result)

    def confirmed(self, count=3):
        self.result(events_confirmed=count, events_sent=count,
                    confirmation_complete=True, upload_attempted=True)

    def assertStatus(self, key):
        self.assertEqual(presentation(self.state)[0], 'topbar.edsm_' + key)

    def test_confirmed_idle_and_restart(self):
        self.result(events_sent=0)
        self.assertStatus('unknown')
        self.confirmed()
        self.assertStatus('success')
        for _ in range(100):
            self.result(events_sent=0, error='')
        self.assertStatus('success')
        self.assertEqual(self.state.edsm_upload_details['confirmed'], 3)
        self.assertEqual(len(self.state._edsm_runtime_by_fid['A']['sources']), 1)
        self.state._edsm_runtime_by_fid = {}
        publish(self.state)
        self.assertStatus('unknown')

    def test_failure_retry_idle_and_recovery(self):
        self.confirmed()
        self.result(upload_attempted=True, error='EDSM HTTP-Fehler 429.', retry_scheduled=True)
        self.assertStatus('waiting')
        self.assertIn(tr('edsm_service.http', code=429), presentation(self.state)[2])
        self.result(error='')
        self.assertStatus('error')
        self.result(retry_paused=True, error='EDSM-Wiederholung pausiert (Netzwerk/Rate-Limit).')
        self.assertStatus('waiting')
        self.assertIn(tr('edsm_service.http', code=429), presentation(self.state)[2])
        self.result(running=True)
        self.assertStatus('waiting')
        self.result(upload_attempted=True, error='EDSM nicht erreichbar.')
        self.assertStatus('error')
        self.confirmed(2)
        self.assertStatus('success')
        self.assertFalse(self.state.edsm_upload_details['errors'])

    def test_abort_skip_partial_and_ambiguous_ack_do_not_create_success(self):
        for result in ({'cancelled': True}, {'error': '__cancelled__'},
                       {'skipped': True}, {'initialized': True},
                       {'events_sent': 50},
                       {'events_confirmed': 1, 'confirmation_complete': False, 'upload_attempted': True}):
            self.confirmed()
            self.result(running=True)
            self.result(**result)
            self.assertNotEqual(presentation(self.state)[1], 'statusOk')
        self.result(events_confirmed=1, confirmation_complete=False,
                    upload_attempted=True, error='EDSM hat nicht alle Ereignisse bestätigt.')
        self.assertStatus('error')
        self.assertEqual(self.state.edsm_upload_details['confirmed'], 1)
        self.assertIn(tr('edsm_service.partial'), presentation(self.state)[2])
        self.result(cancelled=True)
        self.assertStatus('error')
        self.result(skipped=True)
        self.assertStatus('error')

    def test_unrelated_data_and_disabled_priority(self):
        self.confirmed()
        for download in ('Cache', 'EDSM', 'Zeitüberschreitung bei EDSM.'):
            self.state.edsm_source_status = download
            self.state.edsm_settings_for_fid = Mock(side_effect=AssertionError('Must not read'))
            self.assertStatus('success')
        self.result(error='EDSM nicht erreichbar.', upload_attempted=True)
        self.state.edsm_source_status = 'EDSM'
        self.assertStatus('error')
        self.state.edsm_enabled = False
        publish(self.state)
        self.assertStatus('off')
        self.state.edsm_enabled = True
        publish(self.state)
        self.assertStatus('error')

    def test_fid_and_source_isolation_retirement_and_repeated_result(self):
        self.result(error='EDSM nicht erreichbar.', upload_attempted=True)
        confirmed = dict(events_confirmed=7, confirmation_complete=True, upload_attempted=True)
        observe(self.state, 'B', ('steam', 1), confirmed)
        self.assertStatus('error')
        observe(self.state, 'A', ('epic', 2), confirmed)
        self.assertStatus('error')
        self.state.commander_fid = 'B'
        publish(self.state)
        self.assertStatus('success')
        self.state.commander_fid = 'A'
        publish(self.state)
        self.assertStatus('error')
        retire_source(self.state, ('steam', 1))
        self.assertStatus('success')
        observe(self.state, 'A', ('epic', 2), confirmed)
        self.assertEqual(self.state.edsm_upload_details['confirmed'], 7)

    def test_source_manager_rejects_stale_generation_and_preserves_original_fid(self):
        from cmdrhelper.source_manager import SourceManager
        manager = SimpleNamespace(state=self.state, runtimes={'steam': SimpleNamespace(generation=2)})
        deliver = lambda generation, fid, result: SourceManager._edsm_upload_changed(
            manager, 'steam', generation, fid, result)
        success = dict(events_confirmed=2, confirmation_complete=True)
        deliver(1, 'A', success)
        self.assertStatus('unknown')
        deliver(2, 'B', success)
        self.assertStatus('unknown')
        self.state.commander_fid = 'B'; publish(self.state)
        self.assertStatus('success')
        self.state._startup_cancel.set()
        deliver(2, 'B', {'error': 'EDSM nicht erreichbar.', 'upload_attempted': True})
        self.assertStatus('success')

    def test_expired_retry_with_no_pending_events_is_not_permanent_waiting(self):
        self.result(retry_paused=True, error='EDSM-Wiederholung pausiert (Netzwerk/Rate-Limit).')
        self.assertStatus('waiting')
        self.result(events_sent=0)
        self.assertStatus('unknown')
        self.confirmed()
        self.result(retry_paused=True, error='EDSM-Wiederholung pausiert (Netzwerk/Rate-Limit).')
        self.result(events_sent=0)
        self.assertStatus('success')

    def test_transfer_observation_is_owner_bound_and_cannot_change_results(self):
        from cmdrhelper.source_transfers import transfer
        source = SimpleNamespace(id='steam', path='/synthetic')
        sessions = [{'fid_seen': 'A', 'attribution_status': 'identified'}]
        configs = {'A': ({'commander': 'Alpha', 'api_key': 'synthetic', 'enabled': True}, {})}
        result = dict(events_confirmed=2, events_sent=2, confirmation_complete=True)
        notifications = []
        class Uploader:
            def __init__(self, *args, **kwargs):
                self.start = kwargs['on_upload_start']
                self._upload_attempted = True
            def process_folder(self, path):
                self.start()
                return result
        with patch('cmdrhelper.source_transfers.EDSMJournalUploader', Uploader):
            observed = transfer(None, source, sessions, configs, None, is_current=lambda: True,
                legacy_folder=None, source_folders=(),
                edsm_status=lambda fid, value: notifications.append((fid, value)))
            self.assertEqual(notifications, [('A', {'running': True}), ('A', result)])
            self.assertEqual(observed, {('A', 'edsm'): result})
            observer = Mock(side_effect=RuntimeError('UI unavailable'))
            self.assertEqual(transfer(None, source, sessions, configs, None, is_current=lambda: True,
                legacy_folder=None, source_folders=(), edsm_status=observer), observed)
            self.assertEqual(observer.call_count, 2)

    def test_transfer_exception_reaches_status_without_swallowing_original_failure(self):
        from cmdrhelper.source_transfers import transfer
        class Uploader:
            def __init__(self, *args, **kwargs):
                self._upload_attempted = True
            def process_folder(self, path):
                raise ValueError('synthetic private detail')
        notify = Mock()
        with patch('cmdrhelper.source_transfers.EDSMJournalUploader', Uploader):
            with self.assertRaisesRegex(ValueError, 'synthetic private detail'):
                transfer(None, SimpleNamespace(id='steam', path='/synthetic'),
                    [{'fid_seen': 'A', 'attribution_status': 'identified'}],
                    {'A': ({'commander': 'Alpha', 'api_key': 'synthetic', 'enabled': True}, {})},
                    None, is_current=lambda: True, legacy_folder=None, source_folders=(),
                    edsm_status=notify)
        notify.assert_called_once_with('A', {'error': 'EDSM-Upload fehlgeschlagen.', 'upload_attempted': True})
