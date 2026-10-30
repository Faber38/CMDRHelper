"""Isolated real-window benchmark. Never opens productive journals/settings.

QT_QPA_PLATFORM=xcb venv/bin/python tools/benchmark_inventory_invalidation.py
Use --baseline-dir with pre-change source_manager.py/source_processing.py/state.py.
"""
import argparse
from collections import Counter, defaultdict
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
parser = argparse.ArgumentParser()
parser.add_argument('--baseline-dir', type=Path)
parser.add_argument('--without-readers', action='store_true')
parser.add_argument('--batches', type=int, default=8)
args = parser.parse_args()
if args.baseline_dir:
    class Baseline(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if fullname in ('cmdrhelper.state', 'cmdrhelper.source_manager', 'cmdrhelper.source_processing'):
                return importlib.util.spec_from_file_location(fullname, args.baseline_dir / (fullname.rsplit('.', 1)[1] + '.py'))
    sys.meta_path.insert(0, Baseline())

from unittest.mock import patch
from PySide6.QtCore import QObject, QEvent, QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from test_source_manager import ManagerTests
from test_import_catchup import append, event
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.odyssey_controller import OdysseyController

ManagerTests.setUpClass()
fixture = ManagerTests()
fixture.setUp()
app, state = fixture.app, fixture.state
assert app.platformName() == 'xcb', app.platformName()
runtime = next(iter(state.sources.runtimes.values()))
state.select_viewed_commander(runtime.processor.sessions[-1]['commander_id'])
# Same deterministic historical workload in every run: 6 x 500 inventory deltas.
for day in range(1, 7):
    path = Path(runtime.source.path) / f'Journal.2026-09-{day:02}T120000.01.log'
    append(path, event('Commander', FID='TEST-Steam', Name='Steam'),
           event('Materials', Raw=[dict(Name='iron', Count=0)], Manufactured=[], Encoded=[]),
           event('Cargo', Vessel='Ship', Inventory=[]),
           event('ShipLocker', Items=[], Components=[], Data=[], Consumables=[]),
           *[event('MaterialCollected', Category='Raw', Name='iron', Count=1) for _ in range(500)])
state.sources.reimport()
fixture.drain()
update_patch = patch.object(MainWindow, '_check_for_updates')
update_patch.start()
fixture.addCleanup(update_patch.stop)
with patch('cmdrhelper.global_hotkey.GlobalHotkey.load', return_value=True):
    window = MainWindow(state)
window.resize(1280, 850)
window.show()
odyssey = OdysseyController(state)
controllers = [window.material_view.controller, state.mining_inventory_controller, odyssey]

def pump(seconds):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(.001)

pump(2)
if args.without_readers:
    # Keep the real UI/signals, but suppress job starts after initial warm-up.
    for controller in controllers:
        controller.timer.timeout.disconnect()
        controller.timer.stop()
        if hasattr(controller, 'cargo_retry'):
            controller.cargo_retry.stop()

counts, cpu = Counter(), defaultdict(float)
patches = []
for kind, controller in zip(('materials', 'mining', 'odyssey'), controllers):
    original = controller.reader.reconstruct
    def measured(*a, _kind=kind, _original=original, **kw):
        counts[_kind] += 1
        start = time.thread_time()
        try:
            return _original(*a, **kw)
        finally:
            cpu[_kind] += time.thread_time() - start
    p = patch.object(controller.reader, 'reconstruct', side_effect=measured)
    p.start()
    patches.append(p)

class PaintProbe(QObject):
    def __init__(self):
        super().__init__()
        self.pending = None
        self.samples = defaultdict(list)
    def eventFilter(self, watched, event):
        if event.type() == QEvent.Paint and self.pending:
            page, started = self.pending
            if watched is window.pages.widget(page):
                self.samples[page].append((time.perf_counter() - started) * 1000)
                self.pending = None
        return False
probe = PaintProbe()
for page in (window.PAGE_EXPLORER, window.PAGE_PP2):
    window.pages.widget(page).installEventFilter(probe)
last = time.perf_counter()
lags = []
def tick():
    global last
    now = time.perf_counter()
    lags.append(max(0, (now - last) * 1000 - 10))
    last = now
heartbeat = QTimer()
heartbeat.setInterval(10)
heartbeat.timeout.connect(tick)
heartbeat.start()
output = []
try:
    for inventory in (False, True):
        counts.clear(); cpu.clear(); lags.clear(); probe.samples.clear()
        revisions = dict(state._inventory_revisions)
        for index in range(args.batches):
            window._show_page(0)
            pump(.03)
            events = [event('FSDJump', StarSystem=f'Jump {index}', SystemAddress=100 + index)]
            if inventory:
                events += [event('MaterialCollected', Category='Raw', Name='iron', Count=1),
                           event('Cargo', Vessel='Ship', Inventory=[]),
                           event('ShipLocker', Items=[], Components=[], Data=[], Consumables=[])]
            append(Path(runtime.processor.sessions[-1]['journal_file']), *events)
            runtime.watcher.check_now()
            # Click queued during worker/debounce activity, measured to page paint.
            page = window.PAGE_EXPLORER if index % 2 == 0 else window.PAGE_PP2
            started = time.perf_counter()
            probe.pending = (page, started)
            QTimer.singleShot(0, lambda page=page: QTest.mouseClick(window.nav_buttons[page], Qt.LeftButton))
            fixture.drain()
            pump(.65)
        output.append(dict(batch='inventory' if inventory else 'FSDJump',
            revisions={k: state._inventory_revisions[k] - revisions[k] for k in revisions},
            reconstructions=dict(counts), reader_cpu_ms={k: round(v * 1000, 2) for k, v in cpu.items()},
            click_to_paint_ms={str(k): [round(v, 2) for v in values] for k, values in probe.samples.items()},
            max_eventloop_delay_ms=round(max(lags, default=0), 2)))
    print(json.dumps(dict(platform=app.platformName(), baseline=bool(args.baseline_dir),
        readers=not args.without_readers, batches=args.batches, results=output), indent=2), flush=True)
finally:
    heartbeat.stop()
    for controller in controllers:
        controller.timer.stop()
        controller.pool.waitForDone()
    for p in patches:
        p.stop()
    window.hide()
    fixture.doCleanups()
