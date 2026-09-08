import io
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QObject, QSettings, QRect, Qt, Signal, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from cmdrhelper.online_services import fetch_edsm_system_status, fetch_edsm_bodies
from cmdrhelper.edsm_system_status import EdsmSystemStatus, SETTING
from cmdrhelper.state import AppState
from cmdrhelper.ui.navigation_hud import NavigationHud, TargetWindow
from cmdrhelper.ui.cargo_hud import CargoHudData
from cmdrhelper.i18n import set_language, _TRANSLATIONS
from cmdrhelper.help_content.de import HELP_TOPICS
from tests.test_navigation_hud_windows import FakeApi
from cmdrhelper.ui.navigation_hud_windows import WindowsWindowTracker, OVERLAY_STYLES


def event(name='A', kind='FSDJump', address=None):
    return dict(event=kind, StarSystem=name, SystemAddress=address)


class EdsmResponseTests(unittest.TestCase):
    def request(self, data):
        with patch('cmdrhelper.online_services.urlopen', return_value=io.BytesIO(data)) as request:
            result = fetch_edsm_system_status('Sol', 10477373803)
            self.assertIn('/api-v1/system?systemName=Sol&showId=1', request.call_args.args[0].full_url)
            self.assertEqual(request.call_args.kwargs['timeout'], 8)
            return result

    def test_matching_system_is_known_even_without_bodies(self):
        self.assertEqual(self.request(b'{"id":27,"id64":10477373803,"name":"Sol"}'), 'known')

    def test_only_valid_empty_json_is_unknown(self):
        for payload in (b'{}', b'[]'):
            self.assertEqual(self.request(payload), 'unknown')

    def test_empty_invalid_error_or_mismatched_reply_is_no_response(self):
        for payload in (b'', b' ', b'null', b'false', b'"error"', b'<html>error</html>',
                        b'{"error":"offline"}', b'{"name":"Sol"}', b'{"id":true,"name":"Sol"}',
                        b'{"id":27,"name":"Other"}', b'{"id":27,"name":"Sol","id64":9}',
                        b'[{"id":27,"name":"Sol"}]'):
            with self.subTest(payload=payload):
                self.assertEqual(self.request(payload), 'no_response')

    def test_network_timeout_and_http_failures_are_never_unknown(self):
        for error in (TimeoutError(), URLError('offline'), HTTPError('url', 404, 'missing', {}, None),
                      HTTPError('url', 503, 'offline', {}, None)):
            with patch('cmdrhelper.online_services.urlopen', side_effect=error):
                self.assertEqual(fetch_edsm_system_status('Sol'), 'no_response')

    def test_no_reporter_is_guessed_from_body_or_commander_fields(self):
        data = dict(id=27, name='Sol', commander='Wrong', discovery=dict(commander='Unspecified'),
                    bodies=[dict(discovery=dict(commander='Body reporter'))])
        self.assertEqual(self.request(json.dumps(data).encode()), 'known')

    def test_cache_is_not_used_or_written_for_status(self):
        with patch('cmdrhelper.online_services.load_cached_edsm_bodies') as read, \
             patch('cmdrhelper.online_services._save_edsm_bodies_cache') as write:
            self.assertEqual(self.request(b'{}'), 'unknown')
            self.assertEqual(self.request(b'{"id":27,"name":"Sol"}'), 'known')
            read.assert_not_called()
            write.assert_not_called()

    def test_existing_body_fetch_uses_shared_transport_and_keeps_normalization(self):
        with patch('cmdrhelper.online_services.load_cached_edsm_bodies', return_value=None), \
             patch('cmdrhelper.online_services._save_edsm_bodies_cache') as saved, \
             patch('cmdrhelper.online_services.urlopen', return_value=io.BytesIO(b'{"id":27,"name":"Sol","bodies":[],"bodyCount":0}')):
            ok, data, source = fetch_edsm_bodies('Sol')
            self.assertTrue(ok)
            self.assertEqual(data, dict(system='Sol', body_count=0, bodies=[]))
            self.assertEqual(source, 'network')
            saved.assert_called_once()


class EdsmArrivalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        set_language('de')
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = str(Path(folder.name) / 'settings.ini')
        self.settings = QSettings(self.path, QSettings.IniFormat)
        self.pool = Mock()
        self.fetch = Mock(return_value='known')
        self.status = EdsmSystemStatus(self.settings, pool=self.pool, fetch=self.fetch)
        self.notices = []
        self.status.notice.connect(self.notices.append)

    def arrive(self, name='A', kind='FSDJump', fid='FID-A', address=None):
        self.status.observe([event(name, kind, address)], fid)

    def finish(self):
        self.pool.start.call_args.args[0].run()

    def test_default_off_and_persistent_setting(self):
        self.assertFalse(self.status.active)
        self.arrive()
        self.pool.start.assert_not_called()
        self.status.set_enabled(True)
        restored = EdsmSystemStatus(QSettings(self.path, QSettings.IniFormat), pool=Mock())
        self.assertTrue(restored.active)
        restored.set_enabled(False)
        self.assertFalse(EdsmSystemStatus(QSettings(self.path, QSettings.IniFormat), pool=Mock()).active)

    def test_fsdjump_reports_all_three_results(self):
        self.status.set_enabled(True)
        for name, result, text in [('A', 'known', 'EDSM: BEKANNT'), ('B', 'unknown', 'EDSM: NICHT BEKANNT'),
                                   ('C', 'no_response', 'EDSM: KEINE ANTWORT')]:
            self.fetch.return_value = result
            self.arrive(name)
            self.finish()
            self.assertEqual(self.notices[-1], (text,))

    def test_initial_location_repeats_and_carrier_return(self):
        self.status.set_enabled(True)
        self.arrive('A', 'Location', address=1)
        self.finish()
        self.arrive('A', 'Location', address=1)
        self.arrive('A', 'Location')  # missing address doesn't invent a new stay
        self.assertEqual(self.pool.start.call_count, 1)
        self.arrive('B', 'CarrierJump', address=2)
        self.finish()
        self.arrive('A', 'FSDJump', address=1)
        self.finish()
        self.assertEqual(len(self.notices), 3)

    def test_old_a_response_cannot_match_new_a_after_b(self):
        self.status.set_enabled(True)
        self.arrive('A')
        first = self.pool.start.call_args.args[0]
        self.arrive('B')
        self.arrive('A')
        first.signals.finished.emit(first.generation, 'unknown')
        self.assertEqual(self.notices, [])
        self.finish()
        self.assertEqual(self.notices, [('EDSM: BEKANNT',)])

    def test_disable_or_commander_change_invalidates_request(self):
        self.status.set_enabled(True)
        self.arrive()
        first = self.pool.start.call_args.args[0]
        self.status.set_enabled(False)
        first.signals.finished.emit(first.generation, 'known')
        self.assertEqual(self.notices, [])
        self.status.set_enabled(True)
        self.arrive(fid='FID-B')
        second = self.pool.start.call_args.args[0]
        self.status.observe([], '')
        second.signals.finished.emit(second.generation, 'known')
        self.assertEqual(self.notices, [])

    def test_non_position_events_do_not_trigger(self):
        self.status.set_enabled(True)
        for kind in ('Docked', 'CarrierJumpRequest', 'CarrierLocation', 'Scan'):
            self.arrive(kind=kind)
        self.pool.start.assert_not_called()

    def test_real_worker_leaves_qt_event_loop_responsive(self):
        release = threading.Event()
        entered = threading.Event()
        def fetch(*args):
            entered.set()
            release.wait(2)
            return 'known'
        status = EdsmSystemStatus(self.settings, fetch=fetch)
        status.set_enabled(True)
        notices, pulses = [], []
        status.notice.connect(notices.append)
        try:
            status.observe([event()], 'FID-A')
            QTimer.singleShot(0, lambda: pulses.append(True))
            QTest.qWait(40)
            self.assertTrue(entered.is_set())
            self.assertEqual(pulses, [True])
            self.assertFalse(notices)
        finally:
            release.set()
            status.pool.waitForDone(3000)
            self.app.processEvents()
        self.assertEqual(notices, [('EDSM: BEKANNT',)])

    def test_state_forwards_only_attributed_committed_positions_and_initial_location(self):
        state = AppState.__new__(AppState)
        QObject.__init__(state)
        state.commander_fid, state.commander_id = 'FID-A', 1
        received = []
        state.journalPositionsReady.connect(lambda events, fid: received.append((events, fid)))
        session = dict(fid_seen='FID-A', commander_id=1, attribution_status='identified')
        events = [event('A'), event('B', 'CarrierJump'), event('B', 'Location')]
        state._emit_journal_positions({}, session, events)
        self.assertEqual(received[-1], (events, 'FID-A'))
        state._emit_journal_positions(dict(last_position=dict(event_type='Location', system_name='C', system_address=3)), session, [])
        self.assertEqual(received[-1][0], [event('C', 'Location', 3)])
        session['fid_seen'] = 'FID-B'
        state._emit_journal_positions({}, session, events)
        self.assertEqual(received[-1], ([], ''))

    def test_real_sidebar_checkbox_defaults_off_and_restores(self):
        from tests.test_popup_ui_settings import PopupUiSettingsTests
        helper = PopupUiSettingsTests()
        helper.setUpClass()
        helper.setUp()
        self.addCleanup(helper.doCleanups)
        main = helper.main(self.settings)
        check = main.edsm_system_status_check
        self.assertIs(check.parent(), main.auto_show_frame)
        self.assertFalse(check.isChecked())
        check.setChecked(True)
        self.assertTrue(main._edsm_system_status.active)
        restored = helper.main(QSettings(self.path, QSettings.IniFormat))
        self.assertTrue(restored.edsm_system_status_check.isChecked())
        restored.edsm_system_status_check.setChecked(False)
        self.assertFalse(restored._edsm_system_status.active)
        self.assertFalse(QSettings(self.path, QSettings.IniFormat).value(SETTING, type=bool))

    def test_german_help_and_twelve_language_statuses(self):
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language, entries in _TRANSLATIONS.items():
            for key in ('settings.edsm_system_status', 'edsm_status.known', 'edsm_status.unknown', 'edsm_status.no_response'):
                self.assertTrue(entries[key], (language, key))
        help_text = HELP_TOPICS['settings'][1]
        for text in ('EDSM-Status-HUD', 'auto einblenden', 'standardmäßig AUS', '2,5 Sekunden',
                     'gültigen EDSM-Treffer', 'gültige EDSM-Antwort ohne Systemtreffer',
                     'Netzwerk-, HTTP-, Timeoutfehler oder eine ungültige Antwort',
                     'nicht dasselbe wie offizielle Elite-Erstentdeckung'):
            self.assertIn(text, help_text)
        self.assertNotIn("EDSM-Systemstatus", help_text)


class EdsmOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def hud(self, windows=False):
        class Controller(QObject):
            changed = Signal(object)
        controller = Controller()
        controller.state = SimpleNamespace(snapshot=None, solution=None)
        api = FakeApi()
        tracker = WindowsWindowTracker(api) if windows else Mock(reason='active', error='', last_target=None)
        if not windows:
            tracker.input_is_empty.return_value = True
            tracker.current.return_value = TargetWindow(42, QRect(0, 0, 800, 600))
        hud = NavigationHud(controller, tracker)
        self.addCleanup(hud.deleteLater)
        self.addCleanup(hud.close)
        hud._test_controller = controller
        return hud, api

    def test_linux_and_windows_no_focus_and_hud_off(self):
        for windows in (False, True):
            hud, api = self.hud(windows)
            with patch.object(hud, 'activateWindow', side_effect=AssertionError), \
                 patch.object(hud, 'setFocus', side_effect=AssertionError):
                hud.show_message(('EDSM: BEKANNT',), 25, channel='edsm')
                self.assertTrue(hud.isVisible())
                self.assertFalse(hud.enabled)
                self.assertFalse(hud.cargo_enabled)
                self.assertEqual(hud.focusPolicy(), Qt.NoFocus)
                if windows:
                    self.assertEqual(api.styles[int(hud.winId())], OVERLAY_STYLES)
                    self.assertEqual(api.foreground, 42)
                QTest.qWait(60)
                self.assertFalse(hud.isVisible())
                self.assertFalse(hud.edsm_message_lines)

    def test_cargo_and_quick_favorite_have_independent_visibility_and_timers(self):
        for windows in (False, True):
            hud, _ = self.hud(windows)
            hud.cargo_provider = lambda: CargoHudData('Rhino', 67, 72)
            hud.set_cargo_enabled(True)
            hud.show_message(('Favorite',), 1000)
            hud.show_message(('EDSM: NICHT BEKANNT',), 25, channel='edsm')
            self.assertEqual(hud.message_lines, ('Favorite',))
            self.assertTrue(hud.cargo_data)
            QTest.qWait(60)
            self.assertTrue(hud.isVisible())
            self.assertEqual(hud.message_lines, ('Favorite',))
            self.assertTrue(hud.cargo_enabled)
            hud.show_message(('EDSM: KEINE ANTWORT',), 1000, channel='edsm')
            hud.clear_message()
            self.assertTrue(hud.edsm_message_lines)
            hud.clear_message(channel='edsm')
            self.assertTrue(hud.isVisible())
            self.assertEqual(hud.cargo_data.capacity, 72)
