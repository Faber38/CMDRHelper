"""Real X11 window, synthetic journals and controlled transfer/status responses.

QT_QPA_PLATFORM=xcb venv/bin/python tools/benchmark_edsm_publication.py
--baseline-dir loads the saved source_manager.py and edsm_system_status.py only.
No real EDSM/Inara requests, credentials or productive databases are used.
"""
import argparse
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys
import threading
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
parser = argparse.ArgumentParser()
parser.add_argument('--baseline-dir', type=Path)
parser.add_argument('--samples', type=int, default=3)
args = parser.parse_args()
if args.baseline_dir:
    class Baseline(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if fullname in ('cmdrhelper.source_manager', 'cmdrhelper.edsm_system_status'):
                return importlib.util.spec_from_file_location(fullname,
                    args.baseline_dir / (fullname.rsplit('.', 1)[1] + '.py'))
    sys.meta_path.insert(0, Baseline())

from PySide6.QtCore import QObject, QEvent
from PySide6.QtGui import QTextDocument
from test_source_manager import ManagerTests
from test_import_catchup import append, event
from cmdrhelper.ui.main_window import MainWindow

ManagerTests.setUpClass()
fixture = ManagerTests()
fixture.setUp()
state, app = fixture.state, fixture.app
assert app.platformName() == 'xcb', app.platformName()
runtime = next(iter(state.sources.runtimes.values()))
state.select_viewed_commander(runtime.processor.sessions[-1]['commander_id'])
for target in ('cmdrhelper.online_services.urlopen', 'cmdrhelper.edsm_uploader.urlopen',
               'cmdrhelper.inara_uploader.urlopen'):
    guard = patch(target, side_effect=AssertionError('Unexpected real network request'), create=True)
    guard.start(); fixture.addCleanup(guard.stop)
updates = patch.object(MainWindow, '_check_for_updates')
updates.start(); fixture.addCleanup(updates.stop)
with patch('cmdrhelper.global_hotkey.GlobalHotkey.load', return_value=True):
    window = MainWindow(state)
window.resize(1280, 850)
window._show_page(window.PAGE_EXPLORER)
window.show()
status = window._edsm_system_status
status.receive_allowed = lambda: True  # Only the controlled status transport.
status.set_enabled(True)
current = None
records = []
gui_thread = threading.get_ident()

def pump_until(condition, timeout=10):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        app.processEvents()
        if condition():
            return
        time.sleep(.001)
    raise AssertionError('measurement timed out: ' + repr(current))

def local_changed():
    if current is not None and state.system == current['system']:
        current.setdefault('local', time.perf_counter())
state.changed.connect(local_changed)

def fetch(name, address):
    assert threading.get_ident() != gui_thread
    record = current
    assert record['system'] == name
    record['status_start'] = time.perf_counter()
    time.sleep(.04)  # Controlled response time, NOT a real server measurement.
    record['response_end'] = time.perf_counter()
    return record['response']
status.fetch = fetch

def accepted(*args):
    if current is not None and status.name == current['system']:
        current['gui'] = time.perf_counter()
status.notice.connect(accepted)

class PaintProbe(QObject):
    def eventFilter(self, watched, event):
        if (event.type() == QEvent.Paint and current is not None
                and 'gui' in current and state.system == current['system']
                and status.status == current['response']):
            current.setdefault('paint', time.perf_counter())
        return False
probe = PaintProbe()
window.system_scan_header.installEventFilter(probe)

def transfer(*args, **kwargs):
    assert threading.get_ident() != gui_thread
    record = current
    record['transfer_start'] = time.perf_counter()
    time.sleep(record['upload_delay_ms'] / 1000)
    record['transfer_end'] = time.perf_counter()
    if record['upload_failure']:
        raise TimeoutError('controlled upload timeout')
    return {}

# Warm-up local readers/rendering before any measurement.
start = time.monotonic()
pump_until(lambda: time.monotonic() - start > 1)
try:
    with patch('cmdrhelper.source_transfers.transfer', side_effect=transfer):
        for delay, failure in ((0, False), (500, False), (1500, False), (500, True)):
            for sample in range(args.samples):
                index = len(records)
                current = dict(system=f'Synthetic {index}', upload_delay_ms=delay,
                    upload_failure=failure, response=('known', 'unknown', 'no_response')[sample % 3])
                current['jump'] = time.perf_counter()
                append(Path(runtime.processor.sessions[-1]['journal_file']),
                       event('FSDJump', StarSystem=current['system'], SystemAddress=1000 + index))
                # Starts at journal append; an immediate poll removes polling jitter.
                runtime.watcher.check_now()
                pump_until(lambda: ('paint' in current and not state.sources.running
                                     and not state.sources.queue))
                document = QTextDocument()
                document.setHtml(window.system_scan_header.text())
                current['display_text'] = document.toPlainText()
                current['transfer_error'] = runtime.transfer_error
                for key in ('local', 'status_start', 'gui', 'paint', 'transfer_start', 'transfer_end'):
                    current[key + '_ms'] = round((current[key] - current['jump']) * 1000, 3)
                current['answer_to_gui_ms'] = round((current['gui'] - current['response_end']) * 1000, 3)
                current['answer_to_paint_ms'] = round((current['paint'] - current['response_end']) * 1000, 3)
                records.append({k: v for k, v in current.items() if k not in
                    ('jump', 'local', 'status_start', 'gui', 'paint', 'transfer_start', 'transfer_end', 'response_end')})
    print(json.dumps(dict(platform=app.platformName(), baseline=bool(args.baseline_dir),
        polling='immediate after synthetic append', status_response_delay_ms=40,
        real_network_requests=0, samples=records), indent=2), flush=True)
finally:
    current = None
    status.observe([], '')
    status.pool.waitForDone(3000)
    window.material_view.controller.pool.waitForDone()
    window.hide()
    fixture.doCleanups()
