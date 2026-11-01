"""Synthetic X11 market stability measurements; no player data or settings.

QT_QPA_PLATFORM=xcb PYTHONDONTWRITEBYTECODE=1 venv/bin/python tools/benchmark_saved_market_stability.py
Optional --baseline-module loads a saved pre-change saved_markets_view.py.
"""
import argparse
from collections import Counter, defaultdict
from datetime import timedelta
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline-module', type=Path)
parser.add_argument('--output', type=Path)
args = parser.parse_args()
if args.baseline_module:
    name = 'cmdrhelper.ui.saved_markets_view'
    spec = importlib.util.spec_from_file_location(name, args.baseline_module)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

from PySide6.QtCore import QObject, QEvent, Qt
from test_saved_market_cargo_filter import CargoFilterTests
from test_saved_markets import MarketStore, observation, NOW, MATE
from cmdrhelper.ui import saved_markets_view as ui

CargoFilterTests.setUpClass()
fixture = CargoFilterTests()
fixture.setUp()
app, view, state = fixture.app, fixture.view, fixture.state
assert app.platformName() == 'xcb', app.platformName()
counts, times = Counter(), defaultdict(float)
patches, results, row_counts = [], [], []


def instrument(obj, name, label):
    original = getattr(obj, name)
    def measured(*a, **kw):
        counts[label] += 1
        started = time.perf_counter()
        try:
            return original(*a, **kw)
        finally:
            times[label] += (time.perf_counter() - started) * 1000
            if label == 'market_render':
                row_counts.append(view.markets_proxy.rowCount())
    p = patch.object(obj, name, measured)
    p.start(); patches.append(p)


def choose_all():
    if hasattr(view, 'all_goods'):
        view.all_goods.setChecked(True)
    else:
        view.mining_only.setChecked(False)
        view.cargo_only.setChecked(False)


def position():
    index = view.markets_table.currentIndex()
    return dict(selected=view._selected_id, current=index.row(),
                scroll=view.markets_table.verticalScrollBar().value(),
                rows=view.markets_proxy.rowCount(), goods=view.goods_proxy.rowCount(),
                sort=view.markets_proxy.sortColumn())


def measure(name, action):
    fixture.wait()
    before = position()
    counts.clear(); times.clear(); row_counts.clear()
    started = time.perf_counter()
    action()
    row_counts.append(view.markets_proxy.rowCount())
    fixture.wait()
    result = dict(case=name, counts=dict(counts),
                  duration_ms={k: round(v, 3) for k, v in times.items()},
                  settled_ms=round((time.perf_counter() - started) * 1000, 3),
                  min_visible_rows=min(row_counts), before=before, after=position())
    results.append(result)
    print(json.dumps(result), flush=True)


class VisibilityProbe(QObject):
    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Show, QEvent.Hide):
            counts['left_' + event.type().name] += 1
        return False


try:
    with MarketStore(fixture.market, clock=lambda: NOW) as store:
        for mid in range(4, 110):
            store.record_observation(observation(mid))
    view.reload(); fixture.wait(); fixture.select(MATE)
    # Retain the canonical three-commodity fixture for membership measurements.
    from cmdrhelper.commodity_master import lookup_by_symbol
    view._snapshot['commodities'] = [dict(commodity_id=lookup_by_symbol(n).frontier_id,
        symbol=n, commander_buy_price=10, commander_sell_price=9, supply=20, demand=30)
        for n in ('Gold', 'Beer', 'Platinum')]
    view._render_goods()
    view.radius.setValue(10)
    view.markets_table.sortByColumn(1, Qt.DescendingOrder)
    fixture.select(MATE)
    view.markets_table.verticalScrollBar().setValue(25)
    fixture.wait()
    for obj, name, label in ((view, '_cargo_filter', 'filter_evaluations'),
            (view.goods_proxy, 'invalidateFilter', 'goods_invalidations'),
            (view, '_render_markets', 'market_render'),
            (ui, 'read_reference', 'reference_reads'), (ui, 'read_markets', 'header_reads'),
            (ui, 'read_market', 'detail_reads')):
        instrument(obj, name, label)
    view.markets_model.modelReset.connect(lambda: counts.update(['market_resets']))
    original_connect = sqlite3.connect
    def connect(*a, **kw):
        con = original_connect(*a, **kw)
        con.set_trace_callback(lambda sql: counts.update(['sql_selects'])
            if sql.lstrip().upper().startswith('SELECT') else None)
        return con
    p = patch.object(sqlite3, 'connect', connect); p.start(); patches.append(p)
    probe = VisibilityProbe(); view.markets_table.installEventFilter(probe)
    measure('idle', lambda: None)
    measure('identical_signals_x5', lambda: [state.changed.emit() for _ in range(5)])
    measure('ship_quantity_same_types', lambda: fixture.cargo(Gold=8, Beer=2))
    measure('ship_add_type', lambda: fixture.cargo(Gold=8, Beer=2, Platinum=1))
    measure('ship_remove_type', lambda: fixture.cargo(Gold=8, Beer=2))
    measure('ship_to_srv', lambda: fixture.cargo(vessel='SRV', Gold=1))
    measure('srv_quantity', lambda: fixture.cargo(vessel='SRV', Gold=2))
    choose_all()
    measure('srv_filter_off', lambda: fixture.cargo(vessel='SRV', Gold=3))
    measure('mode_mining', lambda: view.mining_only.setChecked(True))
    measure('mode_all', choose_all)
    view.clock = lambda: NOW + timedelta(minutes=1)
    measure('reshow_same_reference_radius', lambda: (view.hide(), view.show()))
    measure('market_notification_unchanged', state.observedMarketsChanged.emit)
    output = dict(platform=app.platformName(), baseline=bool(args.baseline_module),
                  markets=110, results=results)
    if args.output:
        args.output.write_text(json.dumps(output, indent=2) + '\n')
finally:
    for p in reversed(patches):
        p.stop()
    fixture.doCleanups()
