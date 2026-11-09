"""Station-only 90-day policy, persisted retry state and committed live triggers.

All responses are local fixtures. No EDSM/INARA or real Spansh requests.
"""
import io
import json
import tempfile
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from cmdrhelper.spansh_cache import SystemCache, normalize, TTL
from cmdrhelper.spansh_stations import SpanshStations, LiveEntryGate
from cmdrhelper.spansh_market import DEFAULT_CACHE_TTL
from test_spansh_stations import raw, NOW


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.clock = NOW
        self.fetch = Mock(side_effect=lambda address: raw(address))
        self.cache = SystemCache(Path(self.tmp.name), self.fetch, lambda: self.clock)

    def old(self):
        data = normalize(raw(), 1, NOW - timedelta(days=91))
        self.cache.write(data)
        return data

    def restart(self):
        return SystemCache(self.cache.root, self.fetch, lambda: self.clock)

    def test_exact_boundary_and_station_only_ttl(self):
        self.assertEqual(TTL, timedelta(days=90))
        self.assertEqual(DEFAULT_CACHE_TTL, 300)
        data = normalize(raw(), 1, NOW)
        self.clock += timedelta(days=90) - timedelta(microseconds=1)
        self.assertTrue(self.cache.fresh(data))
        self.clock += timedelta(microseconds=1)
        self.assertFalse(self.cache.fresh(data))

    def test_empty_full_success_is_persisted_and_fresh_for_90_days(self):
        self.fetch.side_effect = lambda address: {'system': dict(id64=address, name='Empty', stations=[], bodies=[])}
        data, success = self.cache.request(1, automatic=True)
        self.assertTrue(success)
        self.assertEqual(data['stations'], [])
        self.clock += timedelta(days=89)
        self.assertEqual(self.restart().request(1, automatic=True), (data, None))
        self.fetch.assert_called_once_with(1)
        self.clock += timedelta(days=1)
        self.assertTrue(self.restart().request(1, automatic=True)[1])
        self.assertEqual(self.fetch.call_count, 2)

    def test_failure_retains_old_data_and_restart_pause_is_system_scoped(self):
        old = self.old()
        self.fetch.side_effect = OSError('controlled offline')
        self.assertEqual(self.cache.request(1, automatic=True), (old, False))
        cache = self.restart()
        self.assertEqual(cache.read(1), old)
        self.assertEqual(cache.request(1, automatic=True), (old, None))
        self.assertTrue(cache.automatic_allowed(2))
        self.fetch.side_effect = lambda address: raw(address)
        self.assertTrue(cache.request(2, automatic=True)[1])
        self.clock += timedelta(minutes=5)
        self.assertTrue(cache.request(1, automatic=True)[1])
        self.assertEqual(self.restart().attempt(1), {})

    def test_legacy_day_records_do_not_block(self):
        directory = self.cache.root / 'attempts'; directory.mkdir()
        for record in (dict(system_address=1, local_date=NOW.date().isoformat()), {'broken': True}):
            (directory / '1.json').write_text(json.dumps(record))
            cache = self.restart()
            self.assertTrue(cache.automatic_allowed(1))
            self.assertTrue(cache.request(1, manual=True)[1])
            self.assertFalse((directory / '1.json').exists())

    def test_manual_bypasses_error_pause_and_same_day_success(self):
        self.fetch.side_effect = TimeoutError('offline')
        self.cache.request(1, automatic=True)
        self.fetch.side_effect = lambda address: raw(address)
        self.assertTrue(self.cache.request(1, manual=True)[1])
        first = self.cache.read(1)['fetched_at']
        self.clock += timedelta(seconds=1)
        self.assertTrue(self.cache.request(1, manual=True)[1])
        self.assertNotEqual(self.cache.read(1)['fetched_at'], first)
        self.assertEqual(self.restart().attempt(1), {})

    def test_retry_after_seconds_and_http_date_survive_restart_and_block_manual(self):
        for value in ('120', format_datetime(NOW + timedelta(seconds=120), usegmt=True)):
            with self.subTest(value=value):
                self.clock = NOW
                old = self.old()
                self.fetch.side_effect = HTTPError('https://example.invalid', 429, 'limited', {'Retry-After': value}, io.BytesIO())
                self.assertEqual(self.cache.request(1, manual=True), (old, False))
                cache = self.restart()
                self.assertIsNotNone(cache.server_wait(1))
                count = self.fetch.call_count
                self.assertEqual(cache.request(1, manual=True), (old, None))
                self.assertEqual(self.fetch.call_count, count)
                self.clock += timedelta(seconds=120)
                self.fetch.side_effect = lambda address: raw(address)
                self.assertTrue(cache.request(1, manual=True)[1])
                self.cache = cache

    def test_429_without_concrete_duration_invents_no_deadline(self):
        for value in (None, 'invalid', '-1'):
            self.fetch.side_effect = HTTPError('https://example.invalid', 429, 'limited',
                {'Retry-After': value} if value else {}, io.BytesIO())
            self.cache.request(1, manual=True)
            self.assertEqual(self.cache.attempt(1)['kind'], 'server')
            self.assertIsNone(self.cache.attempt(1)['retry_not_before'])
            self.assertIsNone(self.cache.server_wait(1))
            self.assertTrue(self.cache.automatic_allowed(1))

    def test_503_explicit_server_wait_is_also_respected(self):
        self.fetch.side_effect = HTTPError('https://example.invalid', 503, 'busy', {'Retry-After': '30'}, io.BytesIO())
        self.cache.request(1, manual=True)
        self.assertIsNotNone(self.cache.server_wait(1))
        self.assertEqual(self.cache.request(1, manual=True), (None, None))
        self.fetch.assert_called_once_with(1)

    def test_incomplete_invalid_and_conflicting_dumps_preserve_full_cache(self):
        old = self.old()
        fixtures = []
        for field in ('stations', 'bodies'):
            response = raw(); del response['system'][field]; fixtures.append(response)
        for row in (None, {}, {'id': 2, 'name': ''}, {'id': True, 'name': 'Invalid'},
                    {'id': 2, 'name': 'Invalid', 'services': 'Market'}):
            response = raw(); response['system']['stations'].append(row); fixtures.append(response)
        response = raw(); del response['system']['bodies'][0]['stations']; fixtures.append(response)
        response = raw(); response['system']['stations'].append(dict(id=100, name='Conflict')); fixtures.append(response)
        response = raw(2); fixtures.append(response)
        response = raw(); response['error'] = 'Incomplete'; fixtures.append(response)
        for response in fixtures:
            with self.subTest(response=response):
                self.fetch.side_effect = None; self.fetch.return_value = response
                self.assertEqual(self.cache.request(1, manual=True), (old, False))
                self.assertEqual(self.cache.read(1), old)

    def test_optional_type_missing_is_valid_and_carrier_only_result_is_empty(self):
        response = raw(); del response['system']['stations'][0]['type']
        self.assertEqual(len(normalize(response, 1)['stations']), 2)
        response = {'system': dict(id64=1, name='Carrier only', bodies=[], stations=[
            dict(id=2, name='Carrier', type='Drake-Class Carrier'),
            dict(id=3, name='Carrier services', services=['Fleet Carrier Fuel'])])}
        self.assertEqual(normalize(response, 1)['stations'], [])

    def test_old_events_in_long_running_session_do_not_qualify(self):
        clock = [NOW]
        gate = LiveEntryGate(lambda: clock[0]); gate.observe([], 'A', 1)
        clock[0] += timedelta(hours=1)
        self.assertIsNone(gate.observe([dict(event='FSDJump', SystemAddress=2,
            timestamp=(NOW+timedelta(minutes=1)).isoformat())], 'A', 2, live=True))


class SourceEntryTests(unittest.TestCase):
    """Exercise the actual source publication with no confirmed game process."""
    @classmethod
    def setUpClass(cls):
        from test_source_manager import ManagerTests
        ManagerTests.setUpClass.__func__(cls)

    def setUp(self):
        import test_source_manager
        self.fixture = test_source_manager.ManagerTests('test_all_sources_ingested_and_manual_switch_projects_identity')
        self.fixture.app = self.app
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.state = self.fixture.state
        self.runtime = next(iter(self.state.sources.runtimes.values()))
        self.state.select_viewed_commander(self.runtime.processor.sessions[-1]['commander_id'])
        self.path = Path(self.runtime.processor.sessions[-1]['journal_file'])
        self.fetch = Mock(side_effect=lambda address: raw(address))
        self.service = self.state.spansh_stations
        self.service.cache = SystemCache(self.fixture.root/'stations', fetch=self.fetch)
        self.service.pool = Mock()
        self.service.set_enabled(True)
        self.flags = []
        self.state.changed.connect(lambda: self.flags.append(self.state._watcher_live_refresh))

    def jump(self, address, timestamp=None, runtime=None):
        from test_import_catchup import append
        runtime = runtime or self.runtime
        path = Path(runtime.processor.sessions[-1]['journal_file'])
        append(path, dict(event='FSDJump', timestamp=(timestamp or datetime.now(timezone.utc)).isoformat(),
                         StarSystem='Diagnostic', SystemAddress=address))
        runtime.watcher.check_now(); self.fixture.drain()

    def test_current_committed_jump_without_process_starts_only_spansh(self):
        self.assertFalse(self.state.sources.snapshot.instances)
        self.jump(101)
        self.service.pool.start.assert_called_once()
        self.service.pool.start.call_args.args[0].run()
        self.fetch.assert_called_once_with(101)
        self.assertTrue(self.state.system_stations)
        self.assertFalse(any(self.flags))

    def test_old_events_and_archive_reimport_do_not_fetch(self):
        self.jump(102, datetime.now(timezone.utc)-timedelta(minutes=10))
        self.service.pool.start.assert_not_called()
        self.state.sources.reimport(); self.fixture.drain()
        self.service.pool.start.assert_not_called()

    def test_unselected_source_and_commander_switch_do_not_fetch(self):
        other = list(self.state.sources.runtimes.values())[1]
        self.jump(103, runtime=other)
        self.service.pool.start.assert_not_called()
        self.state.select_viewed_commander(other.processor.sessions[-1]['commander_id'])
        self.service.pool.start.assert_not_called()
        self.jump(104, runtime=other)
        self.service.pool.start.assert_called_once()


class StatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from PySide6.QtCore import QSettings
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.clock = NOW
        self.fetch = Mock(side_effect=lambda address: raw(address))
        self.cache = SystemCache(Path(self.tmp.name)/'cache', self.fetch, lambda: self.clock)
        settings = QSettings(str(Path(self.tmp.name)/'settings.ini'), QSettings.IniFormat)
        self.pool = Mock()
        self.service = SpanshStations(settings, cache=self.cache, pool=self.pool, now=lambda:self.clock)
        self.service.set_enabled(True)

    def test_overview_reports_all_states_and_rechecks_server_wait_on_click(self):
        from cmdrhelper.ui.system_overview import SystemOverviewDialog
        from cmdrhelper.i18n import tr
        self.cache.write(normalize(raw(),1,NOW-timedelta(days=91)))
        dialog = SystemOverviewDialog('Test', [], system_address=1, spansh=self.service)
        self.addCleanup(dialog.deleteLater);self.addCleanup(dialog.close)
        self.assertEqual(dialog.spansh_status.text(),tr('spansh.status_old'))
        dialog.spansh_button.click()
        self.assertEqual(dialog.spansh_status.text(),tr('spansh.refresh_busy'))
        self.pool.start.call_args.args[0].run()
        self.assertEqual(dialog.spansh_status.text(),tr('spansh.status_current'))
        self.fetch.side_effect = OSError('offline')
        dialog.spansh_button.click();self.pool.start.call_args.args[0].run()
        self.assertEqual(dialog.spansh_status.text(),tr('spansh.refresh_failed'))
        self.fetch.side_effect = HTTPError('https://example.invalid',429,'limit',{'Retry-After':'60'},io.BytesIO())
        dialog.spansh_button.click();self.pool.start.call_args.args[0].run()
        key, until = self.service.status(1)
        self.assertEqual(key,'spansh.status_server_wait')
        self.assertEqual(dialog.spansh_status.text(),tr(key,until=until))
        count=self.fetch.call_count;dialog.spansh_button.click()
        self.assertEqual(self.fetch.call_count,count)
        self.clock+=timedelta(seconds=60)
        self.fetch.side_effect=lambda address:raw(address)
        dialog.spansh_button.click();self.pool.start.call_args.args[0].run()
        self.assertEqual(dialog.spansh_status.text(),tr('spansh.status_current'))

    def test_queued_manual_checks_new_server_deadline_before_fetch(self):
        self.assertTrue(self.service.refresh_system(1))
        self.cache._record_error(1,HTTPError('https://example.invalid',429,'limit',{'Retry-After':'60'},io.BytesIO()))
        self.pool.start.call_args.args[0].run()
        self.fetch.assert_not_called()
        self.assertFalse(self.service.busy(1))
        self.assertEqual(self.service.status(1)[0],'spansh.status_server_wait')
