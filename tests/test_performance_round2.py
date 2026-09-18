"""Regression budgets for projection, live parsing, worker delivery and lazy UI."""
import json
import os
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QObject, QPointF, QTimer, QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_reader import _LIVE_LINE_CACHE, _live_complete_events, read_journal_delta
from cmdrhelper.journal_learning import JournalLearningController
from cmdrhelper.ui.chronicle_view import ChronicleMapWidget
from cmdrhelper.ui.commander_view import CommanderView
from cmdrhelper.mining_controller import MiningInventoryController
from cmdrhelper.material_controller import MaterialController
from cmdrhelper.odyssey_controller import OdysseyController


def legacy_project(widget, system):
    x, y, depth = widget._camera_coordinates(system)
    perspective = 1.0
    if widget.systems:
        depths = [widget._camera_coordinates(s)[2]
                  for s in widget.systems[::max(1, len(widget.systems) // 80)]]
        span = max(max(depths) - min(depths), 1.0)
        perspective = max(.82, min(1.18, 1 + depth / span * .16))
    return (QPointF(widget.width()/2 + x*widget.scale*perspective + widget.pan.x(),
                   widget.height()/2 - y*widget.scale*perspective + widget.pan.y()),
            depth, perspective)


class PerformanceRound2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        _LIVE_LINE_CACHE.clear()
        self.addCleanup(_LIVE_LINE_CACHE.clear)

    def chart(self):
        view = ChronicleMapWidget()
        view.resize(800, 600)
        points = [dict(system_address=i, name=f'S{i}', x=i*13., y=i % 7 * 21.,
                       z=i*i*.5, commanders=[]) for i in range(100)]
        view.set_systems(points, [dict(commander_id=1, system_addresses=list(range(100)))])
        self.addCleanup(view.close)
        return view

    def test_projection_and_render_pixels_match_previous_algorithm(self):
        view = self.chart()
        for point in view.systems:
            self.assertEqual(view._project(point), legacy_project(view, point))
        cached = view.grab().toImage()
        with patch.object(view, '_project', side_effect=lambda point: legacy_project(view, point)):
            previous = view.grab().toImage()
        self.assertEqual(cached, previous)

    def test_camera_changes_invalidate_but_hover_reuses_projection(self):
        view = self.chart()
        view.grab()
        with patch.object(view, '_camera_coordinates', wraps=view._camera_coordinates) as transform:
            view.hover_index = 5
            view.grab()
            self.assertEqual(transform.call_count, 0)
            for change in (lambda: setattr(view, 'scale', view.scale*2),
                           lambda: setattr(view, 'yaw', view.yaw+.1),
                           lambda: setattr(view, 'pitch', view.pitch+.1),
                           lambda: setattr(view, 'pan', view.pan+QPointF(20, 10)),
                           lambda: view.resize(820, 620),
                           lambda: view.set_systems(list(view.systems))):
                transform.reset_mock()
                change()
                self.assertEqual(view._project(view.systems[5]), legacy_project(view, view.systems[5]))
                self.assertGreater(transform.call_count, 0)

    def test_projection_work_is_per_system_not_per_route_endpoint(self):
        view = self.chart()
        view.routes = [dict(commander_id=1, system_addresses=list(range(100))*20)]
        with patch.object(view, '_camera_coordinates', wraps=view._camera_coordinates) as transform:
            view.grab()
            self.assertLessEqual(transform.call_count, 200)

    def journal(self):
        path = self.root/'Journal.2026-09-14T120000.01.log'
        path.write_text(json.dumps(dict(event='Commander', FID='A'))+'\n')
        return path

    def test_same_events_parse_once_and_delta_reuses_them(self):
        path = self.journal()
        with patch('cmdrhelper.journal_reader.json.loads', wraps=json.loads) as parse:
            events, end = _live_complete_events(path)
            self.assertEqual(parse.call_count, 1)
            self.assertEqual(_live_complete_events(path), (events, end))
            self.assertEqual(read_journal_delta(path, 0), (events, end))
            self.assertEqual(parse.call_count, 1)
            delta, _ = read_journal_delta(path, 0)
            delta[0]['FID'] = 'MUTATED'
            self.assertEqual(_live_complete_events(path)[0][0]['FID'], 'A')

    def test_growth_parses_only_new_complete_lines(self):
        path = self.journal()
        _, end = _live_complete_events(path)
        with path.open('a') as f:
            f.write('{"event":"Cargo","Count":1}')
        with patch('cmdrhelper.journal_reader.json.loads', wraps=json.loads) as parse:
            self.assertEqual(_live_complete_events(path)[1], end)
            self.assertEqual(parse.call_count, 0)
            with path.open('a') as f:
                f.write('\n')
            events, new_end = _live_complete_events(path)
            self.assertEqual(len(events), 2)
            self.assertEqual(parse.call_count, 1)
            self.assertEqual(read_journal_delta(path, end)[0], [events[-1]])
            self.assertEqual(parse.call_count, 1)
            self.assertGreater(new_end, end)

    def test_rotation_truncation_and_atomic_replacement_invalidate(self):
        path = self.journal()
        _live_complete_events(path)
        path.write_text('{"event":"Died"}\n')
        self.assertEqual(_live_complete_events(path)[0], [dict(event='Died')])
        other = self.root/'replacement'
        other.write_text('{"event":"Music"}\n')
        other.replace(path)
        self.assertEqual(_live_complete_events(path)[0], [dict(event='Music')])
        rotated = self.root/'Journal.2026-09-14T130000.01.log'
        rotated.write_text('{"event":"Commander","FID":"B"}\n')
        self.assertEqual(_live_complete_events(rotated)[0][0]['FID'], 'B')
        self.assertEqual(list(_LIVE_LINE_CACHE), [str(rotated)])

    def learner(self):
        state = QObject()
        state.database = SimpleNamespace(path=self.root/'test.db')
        state.journal_folder = self.root
        state.commander_id, state.commander_fid = 1, 'A'
        state.system_address, state.body, state.last_timestamp = 42, 'P1', 'T1'
        state._journal_index_sessions = []
        controller = JournalLearningController(state)
        return state, controller

    def wait_for(self, predicate):
        deadline = time.monotonic() + 3
        while not predicate() and time.monotonic() < deadline:
            QTest.qWait(10)
        self.assertTrue(predicate())

    def test_bio_and_cartography_learning_keep_gui_heartbeat(self):
        for kind in ('bio', 'cartography'):
            with self.subTest(kind=kind):
                state, controller = self.learner()
                ticks, threads, ready_threads = [], [], []
                def slow(*args, **kw):
                    threads.append(threading.get_ident())
                    time.sleep(.12)
                    return {'values_changed': 1}
                state.database.learn_bio_values_from_journals = slow
                state.database.learn_cartography_values_from_journals = slow
                timer = QTimer()
                timer.timeout.connect(lambda: ticks.append(time.monotonic()))
                timer.start(10)
                controller.ready.connect(lambda result: ready_threads.append(threading.get_ident()))
                start = time.monotonic()
                controller.request({kind})
                self.assertLess(time.monotonic()-start, .08)
                self.wait_for(lambda: bool(ready_threads))
                timer.stop()
                self.assertGreaterEqual(len(ticks), 5)
                self.assertNotEqual(threads[0], threading.get_ident())
                self.assertEqual(ready_threads, [threading.get_ident()])

    def test_commander_or_session_change_discards_old_delivery(self):
        for mutate in (lambda s: setattr(s, 'commander_id', 2),
                       lambda s: setattr(s, '_journal_index_sessions', [{'journal_file': 'new'}]),
                       lambda s: setattr(s, 'system_address', 99),
                       lambda s: setattr(s, 'system', 'Unknown address system')):
            state, controller = self.learner()
            called = []
            def slow(*args, **kw):
                called.append(kw['commander_id'])
                time.sleep(.08)
                return {'values_changed': 1}
            state.database.learn_bio_values_from_journals = slow
            ready = Mock()
            controller.ready.connect(ready)
            controller.request({'bio'})
            mutate(state)
            self.wait_for(lambda: not controller.running)
            if state.commander_id != 1:
                self.assertEqual(called, [1])
                ready.assert_not_called()
            else:
                self.assertEqual(called, [1, 1])  # Revalidated in a fresh job.
                self.assertEqual(ready.call_count, 1)

    def test_larger_rewrite_on_same_inode_replaces_cached_events(self):
        path = self.journal()
        _live_complete_events(path)
        path.write_text('{"event":"Commander","FID":"B","Name":"Replacement"}\n')
        events, offset = _live_complete_events(path)
        self.assertEqual([event['FID'] for event in events], ['B'])
        self.assertEqual(offset, path.stat().st_size)

    def test_indexed_worker_preserves_bio_and_cartography_learning_results(self):
        from cmdrhelper.valuation import calculate_body_values
        events = [dict(event='Commander', FID='A', Name='A'),
                  dict(event='Location', StarSystem='S', SystemAddress=42),
                  dict(event='Scan', SystemAddress=42, BodyID=1, BodyName='S 1',
                       PlanetClass='High metal content body', MassEM=1),
                  dict(event='SellOrganicData', BioData=[dict(
                      Genus='Bacterium', Species='Bacterium Aurasus', Value=1000000)]),
                  dict(event='MultiSellExplorationData', BaseValue=100000, TotalEarnings=100000)]
        path = self.journal()
        path.write_text(''.join(json.dumps({**event, 'timestamp': f'2026-09-14T12:00:0{i}Z'},
                                          separators=(',', ':'))+'\n'
                                for i, event in enumerate(events)))
        direct = CMDRDatabase(self.root/'direct.db')
        direct.upsert_commander('A', 'A')
        expected = {
            'bio': direct.learn_bio_values_from_journals(self.root, commander_id=1),
            'cartography': direct.learn_cartography_values_from_journals(
                self.root, commander_id=1, valuation_func=calculate_body_values),
        }
        self.assertGreater(expected['bio']['values_changed'], 0)
        self.assertGreater(expected['cartography']['sales_stored'], 0)
        state, controller = self.learner()
        state.database = CMDRDatabase(self.root/'worker.db')
        state.database.upsert_commander('A', 'A')
        state._journal_index_sessions = [dict(journal_file=str(path), fid_seen='A',
            attribution_status='identified', file_size=path.stat().st_size,
            modified_ns=path.stat().st_mtime_ns)]
        results = []
        controller.ready.connect(results.append)
        controller.request({'bio', 'cartography'})
        self.wait_for(lambda: bool(results))
        self.assertEqual(results[0], expected)
        self.assertEqual(state.database.learned_bio_values(), direct.learned_bio_values())

    def test_index_identity_reused_only_for_matching_signature(self):
        db = CMDRDatabase(self.root/'db.sqlite')
        path = self.journal()
        row = dict(journal_file=str(path), attribution_status='identified', fid_seen='A',
                   file_size=path.stat().st_size, modified_ns=path.stat().st_mtime_ns)
        with patch('cmdrhelper.journal_reader.classify_journal_file', wraps=__import__(
                'cmdrhelper.journal_reader', fromlist=['classify_journal_file']).classify_journal_file) as classify:
            self.assertEqual(db._learning_journals(self.root, 'A', [row]), [path])
            classify.assert_not_called()
            path.write_text('{"event":"Commander","FID":"B"}\n')
            self.assertEqual(db._learning_journals(self.root, 'A', [row]), [])
            self.assertEqual(classify.call_count, 1)

    def test_open_missions_query_keeps_closed_history_available(self):
        db = CMDRDatabase(self.root/'db.sqlite')
        cid = db.upsert_commander('A', 'A')
        with db._connect() as con:
            con.executemany('INSERT INTO commander_missions(commander_id,mission_id,is_open) VALUES(?,?,?)',
                            [(cid, 1, 1), (cid, 2, 0)])
        self.assertEqual([m['mission_id'] for m in db.commander_missions(cid, only_open=True)], [1])
        self.assertEqual(len(db.commander_missions(cid)), 2)

    def test_hidden_commander_view_is_dirty_and_loads_latest_on_show(self):
        from test_commander_view import make_state
        db = CMDRDatabase(self.root/'db.sqlite')
        cid = db.upsert_commander('A', 'First')
        state = make_state(db)
        state.commander_id = cid
        with patch.object(db, 'commander_summary', wraps=db.commander_summary) as summary:
            view = CommanderView(state)
            self.addCleanup(view.close)
            state.changed.emit()
            summary.assert_not_called()
            db.upsert_commander('A', 'Latest')
            view.show()
            self.app.processEvents()
            self.assertEqual(summary.call_count, 1)
            self.assertEqual(view.values['name'].text(), 'Latest')

    def test_visible_commander_accepts_empty_shared_refresh_summary(self):
        from test_commander_view import make_state
        state = make_state(CMDRDatabase(self.root/'empty.db'))
        view = CommanderView(state)
        self.addCleanup(view.close)
        view.show()
        state._refresh_summary = (None, {})
        view.refresh()
        self.assertEqual(view.values['name'].text(), '–')
        self.assertEqual(view.missions_table.rowCount(), 0)

    def test_refresh_loads_one_summary_and_one_open_missions_list(self):
        from contextlib import ExitStack
        from cmdrhelper.state import AppState
        path = self.journal()
        with path.open('a') as stream:
            for event in (dict(event='LoadGame', FID='A', Commander='A', ShipID=1, Ship='CobraMkIII'),
                          dict(event='Loadout', ShipID=1, Ship='CobraMkIII', CargoCapacity=16, Modules=[]),
                          dict(event='Location', StarSystem='S', SystemAddress=42)):
                stream.write(json.dumps(event)+'\n')
        db = CMDRDatabase(self.root/'app.db')
        settings = QSettings(str(self.root/'ui.ini'), QSettings.IniFormat)
        settings.setValue('journal_folder', str(self.root))
        with ExitStack() as stack:
            stack.enter_context(patch('cmdrhelper.state.QSettings', return_value=settings))
            stack.enter_context(patch('cmdrhelper.state.CMDRDatabase', return_value=db))
            stack.enter_context(patch('cmdrhelper.state.QTimer.singleShot'))
            state = AppState()
            for name in ('_request_edsm_for_current_system', '_upload_journal_to_edsm',
                         '_upload_pending_to_inara', '_load_edsm_cache_for_current_system'):
                stack.enter_context(patch.object(state, name))
            self.assertTrue(state.refresh())
            with patch.object(db, 'commander_summary', wraps=db.commander_summary) as summary, \
                 patch.object(db, 'commander_missions', wraps=db.commander_missions) as missions:
                self.assertTrue(state.refresh())
                self.assertEqual(summary.call_count, 1)
                missions.assert_called_once_with(state.commander_id, only_open=True)

    def test_hidden_explorer_and_missions_render_only_on_open(self):
        from cmdrhelper.ui.main_window import MainWindow
        state = SimpleNamespace(system='Latest', system_bodies=[{'name': 'Current'}])
        view = SimpleNamespace(state=state, PAGE_EXPLORER=2, PAGE_MISSIONS=1,
            pages=SimpleNamespace(currentIndex=lambda: 0), _explorer_dirty=True,
            _missions_dirty=True, system_map=Mock(), _refresh_explorer_tables=Mock(),
            explorer_tabs=SimpleNamespace(currentIndex=lambda: 0, setTabText=Mock()),
            _refresh_missions_table=Mock())
        view._mark_explorer_tabs_dirty = lambda: MainWindow._mark_explorer_tabs_dirty(view)
        MainWindow._refresh_visible_details(view)
        view.system_map.set_system.assert_not_called()
        view._refresh_missions_table.assert_not_called()
        view.pages.currentIndex = lambda: 2
        MainWindow._refresh_visible_details(view)
        view.system_map.set_system.assert_called_once_with('Latest', state.system_bodies, [])
        self.assertFalse(view._explorer_dirty)
        view.pages.currentIndex = lambda: 1
        MainWindow._refresh_visible_details(view)
        view._refresh_missions_table.assert_called_once()
        self.assertFalse(view._missions_dirty)

    def test_inventory_revision_skips_unchanged_but_manual_refresh_forces(self):
        from test_mining_controller import State
        state = State()
        state.database = SimpleNamespace(path=self.root/'db.sqlite')
        state.settings = QSettings(str(self.root/'settings.ini'), QSettings.IniFormat)
        state.commander_id, state.commander_fid = 1, 'A'
        state._journal_index_sessions = []
        state._inventory_revisions = dict(materials=0, mining=0, odyssey=0)
        for cls in (MiningInventoryController, MaterialController, OdysseyController):
            controller = cls(state)
            controller.request()
            controller.timer.stop()
            controller._dirty = False
            controller.request()
            self.assertFalse(controller._dirty)
            with patch.object(controller, '_start') as start:
                controller.refresh_now()
                self.assertTrue(controller._dirty)
                start.assert_called_once()
            controller.timer.stop()
