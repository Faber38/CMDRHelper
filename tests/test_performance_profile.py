"""Isolated profile tests: no application instance, journal ingestion or network."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from cmdrhelper import performance_profile as profile


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def recorder(self, **kw):
        kw.setdefault("detail_threshold_ms", 0)
        recorder = profile.Recorder(self.tmp.name, **kw)
        self.addCleanup(recorder.close)
        return recorder

    def rows(self, recorder):
        self.assertTrue(recorder.close())
        self.assertFalse(recorder.failed)
        return [json.loads(line) for line in recorder.path.read_text().splitlines()]

    def subprocess(self, code, enabled='1'):
        env = dict(os.environ, CMDRHELPER_PROFILE=enabled, QT_QPA_PLATFORM='offscreen',
                   XDG_CONFIG_HOME=self.tmp.name, XDG_DATA_HOME=self.tmp.name,
                   PYTHONDONTWRITEBYTECODE='1', PROFILE_TEST_DIR=self.tmp.name)
        prefix = """from cmdrhelper import performance_profile as _test_profile
_test_original = _test_profile.Recorder
def _test_recorder(*args, **kw):
    kw.setdefault('detail_threshold_ms', 0)
    return _test_original(*args, **kw)
_test_profile.Recorder = _test_recorder
"""
        result = subprocess.run([sys.executable, '-B', '-c', prefix+code], env=env,
            capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr+result.stdout)
        return result

    def test_disabled_is_identity_and_creates_nothing(self):
        for enabled in ('', '0', 'true'):
            self.subprocess('''
import threading
from unittest.mock import patch
from cmdrhelper import performance_profile as p
before=threading.active_count()
def f(): return 17
assert p.measure('menu.switch')(f) is f
assert p.application_class(object) is object
with patch.object(p, 'Recorder', side_effect=AssertionError('No recorder')):
    p.start(None)
assert p._timer is None and p._recorder is None
assert threading.active_count()==before
assert f()==17
''', enabled)

    def test_monotonic_duration_nested_spans_and_privacy(self):
        now=[1_000_000_000]
        r=self.recorder(clock=lambda:now[0]);r.cpu_clock=lambda:0
        outer=r.begin('menu.switch',view='trade')
        now[0]+=100_000_000
        inner=r.begin('gui.refresh')
        r.emit('spansh.result',outcome='success',api_key='SECRET',system='SECRET',count=2)
        now[0]+=200_000_000;r.end('gui.refresh',inner)
        now[0]+=100_000_000;r.end('menu.switch',outer)
        rows=self.rows(r)
        self.assertNotIn('SECRET',r.path.read_text())
        end=next(x for x in rows if x['point']=='menu.switch.end')
        self.assertEqual(end['duration_ms'],400)
        begin=next(x for x in rows if x['point']=='gui.refresh.begin')
        self.assertEqual(begin['parent_span'],end['span'])
        self.assertEqual(rows[-1]['point'],'session.end')

    def test_handoff_delay_and_bounded_pending(self):
        now=[1_000_000_000];r=self.recorder(clock=lambda:now[0])
        r.mark(('secret source',7));now[0]+=250_000_000
        r.receive(('secret source',7),'source.handoff')
        for i in range(3000):r.mark(i)
        self.assertEqual(len(r.pending),2048)
        rows=self.rows(r)
        self.assertEqual(next(x for x in rows if x['point']=='source.handoff')['duration_ms'],250)
        self.assertNotIn('secret source',r.path.read_text())

    def test_no_file_size_cutoff_and_summary(self):
        r=self.recorder()
        for _ in range(1000):r.emit('menu.switch.end',duration_ms=400,view='trade')
        rows=self.rows(r)
        self.assertGreater(r.path.stat().st_size,4096)
        self.assertNotIn('capped', rows[-1])
        summary=json.loads(Path(str(r.path)+'.summary.json').read_text())
        self.assertLessEqual(len(summary['top']['menu']),20)
        self.assertEqual(profile.summarize(r.path)['top']['menu'][0]['duration_ms'],400)

    def test_queue_overflow_never_waits_for_writer(self):
        gate=threading.Event()
        class Paused(profile.Recorder):
            def _write(self):
                gate.wait(5)
                super()._write()
        r=Paused(self.tmp.name,capacity=2)
        self.addCleanup(r.close);self.addCleanup(gate.set)
        for _ in range(100):r.emit('test.event', outcome='error')
        self.assertGreater(r.dropped,0)
        self.assertLessEqual(r.queue.qsize(),2)
        gate.set();self.rows(r)

    def test_writes_are_exclusively_off_caller_thread(self):
        original=os.open;ids=[]
        def opened(*args,**kw):ids.append(threading.get_ident());return original(*args,**kw)
        with patch('os.open',side_effect=opened):
            r=self.recorder();r.emit('test.event');self.rows(r)
        self.assertTrue(ids)
        self.assertNotIn(threading.get_ident(),ids)

    def test_unwritable_destination_is_nonfatal(self):
        target=Path(self.tmp.name)/'file';target.write_text('occupied')
        r=profile.Recorder(target);self.addCleanup(r.close)
        self.assertTrue(r.close());self.assertTrue(r.failed)
        r.emit('test.event')

    def test_decorator_preserves_results_and_exception(self):
        r=self.recorder()
        with patch.object(profile,'ENABLED',True),patch.object(profile,'_recorder',r):
            @profile.measure('test.function')
            def func(value):
                if value:raise ValueError('PRIVATE')
                return 42
            self.assertEqual(func(False),42)
            with self.assertRaisesRegex(ValueError,'PRIVATE'):func(True)
        rows=self.rows(r)
        self.assertEqual([x['outcome'] for x in rows if x['point']=='test.function.end'],['success','error'])
        self.assertNotIn('PRIVATE',r.path.read_text())

    def test_enabled_qt_dispatch_delay_and_shutdown(self):
        self.subprocess('''
import os,time,json
from pathlib import Path
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from cmdrhelper import performance_profile as p
original=p.Recorder
app=p.application_class(QApplication)([])
with patch.object(p,'Recorder',lambda:original(os.environ['PROFILE_TEST_DIR'])):
    p.start(app)
r=p._recorder
QTimer.singleShot(0,lambda:time.sleep(.4))
QTimer.singleShot(600,app.quit)
app.exec()
p.shutdown()
assert not r.thread.is_alive()
rows=[json.loads(line) for line in r.path.read_text().splitlines()]
assert any(x['point']=='qt.dispatch' and x['duration_ms']>=350 for x in rows)
assert any(x['point']=='qt.event_delay' and x['duration_ms']>=200 for x in rows)
assert rows[-1]['point']=='session.end'
assert p._timer is None and p._recorder is None
''')

    def test_manual_cache_logic_unchanged_with_instrumentation(self):
        self.subprocess('''
import os,json
from datetime import datetime,timezone
from pathlib import Path
from cmdrhelper import performance_profile as p
from cmdrhelper.spansh_cache import SystemCache
p._recorder=p.Recorder(Path(os.environ['PROFILE_TEST_DIR'])/'profile')
r=p._recorder
calls=[]
def fetch(address):
    calls.append(address)
    return {'system':{'id64':address,'name':'PRIVATE','stations':[],'bodies':[]}}
c=SystemCache(Path(os.environ['PROFILE_TEST_DIR'])/'cache',fetch=fetch)
assert c.request(42,automatic=True)[1] is True
assert c.request(42,automatic=True)[1] is None
assert c.request(42,manual=True)[1] is True
assert calls==[42,42]
p.shutdown()
text=r.path.read_text();assert 'PRIVATE' not in text
assert 'cache_hit' in text and 'manual' in text
''')

    def test_shutdown_is_idempotent(self):
        r=self.recorder();r.emit('test.event')
        self.assertTrue(r.close());self.assertTrue(r.close())
        size=r.path.stat().st_size;r.emit('test.late')
        self.assertEqual(r.path.stat().st_size,size)

    def test_qt_menu_wrapper_keeps_view_and_result(self):
        self.subprocess('''
import os,json
from cmdrhelper import performance_profile as p
from cmdrhelper.ui.main_window import MainWindow
from types import SimpleNamespace
from unittest.mock import Mock
p._recorder=p.Recorder(os.environ['PROFILE_TEST_DIR']);r=p._recorder
obj=SimpleNamespace(pages=Mock(),nav_buttons=[],material_view=None)
obj.pages.currentIndex.return_value=0
MainWindow._show_page(obj,2)
obj.pages.setCurrentIndex.assert_called_once_with(2)
p.shutdown()
rows=[json.loads(line) for line in r.path.read_text().splitlines()]
assert any(x['point']=='menu.switch.end' and x['view']=='explorer' for x in rows)
''')

    def test_real_start_path_isolated_off_and_on(self):
        for enabled in ('0', '1'):
            self.subprocess(self._startup_code('success'), enabled)

    def test_startup_exception_closes_profile(self):
        self.subprocess(self._startup_code('error'))

    def test_instance_lock_rejection_never_starts_profile(self):
        self.subprocess(self._startup_code('locked'))

    @staticmethod
    def _startup_code(mode):
        return "MODE="+repr(mode)+"\n"+'''
import os
from contextlib import ExitStack
from unittest.mock import Mock,patch
from PySide6.QtWidgets import QApplication
from cmdrhelper import app as module
from cmdrhelper import performance_profile as p
class App(QApplication):
    def exec(self):return 0
class Lock:
    def __init__(self,*a):pass
    def tryLock(self,*a):return MODE!='locked'
original=p.Recorder;created=[]
def recorder():
    r=original(os.environ['PROFILE_TEST_DIR']);created.append(r);return r
with ExitStack() as stack:
    for target,value in [('cmdrhelper.app.QApplication',App),
        ('cmdrhelper.app.QLockFile',Lock),('cmdrhelper.app.configure_logging',lambda:None),
        ('cmdrhelper.app.consume_update_status',lambda *_:None),
        ('cmdrhelper.app.MainWindow',Mock()),('cmdrhelper.app.QMessageBox.information',Mock()),
        ('cmdrhelper.app.AppState',Mock(side_effect=RuntimeError('expected')) if MODE=='error' else Mock()),
        ('cmdrhelper.database.default_database_path',lambda:os.environ['PROFILE_TEST_DIR']+'/db'),
        ('cmdrhelper.parent_migration.migration_required',lambda *_:False),
        ('cmdrhelper.performance_profile.Recorder',recorder)]:
        stack.enter_context(patch(target,value))
    try:module.run()
    except SystemExit as exc:assert exc.code==0 and MODE=='success'
    except RuntimeError:assert MODE=='error'
assert len(created)==int(p.ENABLED and MODE!='locked')
assert all(not r.thread.is_alive() for r in created)
assert p._recorder is None and p._timer is None
'''

    def test_directory_budget_retains_old_evidence(self):
        old=Path(self.tmp.name)/'profile-old.jsonl'
        with old.open('wb') as stream:stream.truncate(64*1024*1024)
        r=self.recorder()
        self.assertTrue(r.close())
        self.assertFalse(r.failed)
        self.assertEqual(old.stat().st_size,64*1024*1024)
        self.assertIsNotNone(r.path)

    def test_recorder_start_failure_does_not_abort_application(self):
        with patch.object(profile,'ENABLED',True),patch.object(profile,'_recorder',None), \
             patch.object(profile,'Recorder',side_effect=OSError('PRIVATE')):
            profile.start(None)
            self.assertIsNone(profile._recorder)

    def test_exclusive_times_do_not_double_count_nested_work(self):
        now=[1_000_000_000];cpu=[0]
        r=self.recorder(clock=lambda:now[0]);r.cpu_clock=lambda:cpu[0]
        a=r.begin('state.refresh')
        now[0]+=100_000_000;cpu[0]+=10_000_000
        b=r.begin('signal.changed')
        now[0]+=50_000_000;cpu[0]+=5_000_000
        c=r.begin('slot.trade.refresh')
        now[0]+=200_000_000;cpu[0]+=20_000_000;r.end('slot.trade.refresh',c)
        now[0]+=50_000_000;cpu[0]+=5_000_000;r.end('signal.changed',b)
        now[0]+=100_000_000;cpu[0]+=10_000_000;r.end('state.refresh',a)
        ends={x['point']:x for x in self.rows(r) if 'self_ms' in x}
        self.assertEqual(ends['state.refresh.end']['duration_ms'],500)
        self.assertEqual(ends['state.refresh.end']['self_ms'],200)
        self.assertEqual(ends['state.refresh.end']['self_cpu_ms'],20)
        self.assertEqual(sum(x['self_ms'] for x in ends.values()),500)

    def test_sql_semantics_privacy_fetch_and_connection_lifecycle(self):
        self.subprocess('''
import os,json,sqlite3
from pathlib import Path
from cmdrhelper import performance_profile as p
from cmdrhelper.database import CMDRDatabase
p._recorder=p.Recorder(Path(os.environ['PROFILE_TEST_DIR'])/'profile');r=p._recorder
obj=CMDRDatabase.__new__(CMDRDatabase);obj.path=Path(os.environ['PROFILE_TEST_DIR'])/'test.db'
@p.measure('db.test')
def run():
    con=obj._connect();con.row_factory=sqlite3.Row
    con.execute('CREATE TABLE secret_table(value TEXT)')
    with con:con.executemany('INSERT INTO secret_table VALUES(?)',[('PRIVATE',),('API_SECRET',)])
    # Context exit must not close; existing implicit transaction behavior retained.
    assert con.execute('SELECT COUNT(*) FROM secret_table').fetchone()[0]==2
    assert [x[0] for x in con.execute('SELECT value FROM secret_table')]==['PRIVATE','API_SECRET']
    assert len(con.execute('SELECT * FROM secret_table').fetchall())==2
    assert len(con.execute('SELECT * FROM secret_table').fetchmany(1))==1
    try:
        with con:
            con.execute('INSERT INTO secret_table VALUES(?)',('ROLLED_BACK',))
            raise ValueError('SECRET_ERROR')
    except ValueError:pass
    assert con.execute('SELECT COUNT(*) FROM secret_table').fetchone()[0]==2
    con.commit();con.rollback()
    con.cursor(factory=sqlite3.Cursor).execute('SELECT 1')
    con.close()
run();p.shutdown()
text=r.path.read_text();rows=[json.loads(l) for l in text.splitlines()]
assert not any(secret in text for secret in ('PRIVATE','API_SECRET','secret_table','SECRET_ERROR','ROLLED_BACK'))
points={x['point'] for x in rows}
assert {'db.open.end','db.connect.end','db.transaction_exit.end','db.commit.end','db.rollback.end','db.close.end','sql.execute.end','sql.fetchall.end','sql.fetchone.end','sql.fetchmany.end'}<=points
assert next(x for x in rows if x['point']=='db.test.end')['sql_iteration_steps']==3
''')

    def test_disabled_database_keeps_original_connection(self):
        self.subprocess('''
import os
from pathlib import Path
from cmdrhelper import database as db
from cmdrhelper import performance_profile as p
assert not hasattr(db,'_ProfileConnection')
obj=db.CMDRDatabase.__new__(db.CMDRDatabase);obj.path=Path(os.environ['PROFILE_TEST_DIR'])/'db'
con=obj._connect()
assert type(con) is db._DiagnosticConnection
assert not hasattr(db.CMDRDatabase._connect,'__wrapped__')
con.close()
assert p._recorder is None and p._timer is None
''', '0')

    def test_signal_slots_remain_nested_and_ordered(self):
        self.subprocess('''
import os,json
from PySide6.QtCore import QObject,Signal
from cmdrhelper import performance_profile as p
class Object(QObject):changed=Signal()
obj=Object();calls=[]
@p.measure('slot.first')
def first():calls.append(1)
@p.measure('slot.second')
def second():calls.append(2)
obj.changed.connect(first);obj.changed.connect(second)
p._recorder=p.Recorder(os.environ['PROFILE_TEST_DIR']);r=p._recorder
p.call('signal.changed',obj.changed.emit)
p.shutdown();rows=[json.loads(l)for l in r.path.read_text().splitlines()]
assert calls==[1,2]
signal=next(x for x in rows if x['point']=='signal.changed.end')
slots=[x for x in rows if x['point'] in ('slot.first.end','slot.second.end')]
assert all(x['parent_span']==signal['span'] for x in slots)
assert signal['self_ms']<=signal['duration_ms']
''')

    def test_qt_receiver_label_does_not_capture_object_name(self):
        self.subprocess('''
import os,time,json
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from cmdrhelper import performance_profile as p
app=p.application_class(QApplication)([]);original=p.Recorder
with patch.object(p,'Recorder',lambda:original(os.environ['PROFILE_TEST_DIR'])):p.start(app)
r=p._recorder;timer=QTimer();timer.setObjectName('PRIVATE_IDENTITY');timer.setSingleShot(True)
timer.timeout.connect(lambda:time.sleep(.22));timer.start(0)
QTimer.singleShot(400,app.quit);app.exec();p.shutdown()
text=r.path.read_text();assert 'PRIVATE_IDENTITY' not in text
assert any(x['point']=='qt.dispatch' and x.get('receiver')=='QTimer' for x in map(json.loads,text.splitlines()))
''')

    def test_sql_wait_is_in_execute_not_connection_open(self):
        self.subprocess('''
import os,json,sqlite3,threading,time
from pathlib import Path
from cmdrhelper import performance_profile as p
from cmdrhelper.database import CMDRDatabase
p._recorder=p.Recorder(Path(os.environ['PROFILE_TEST_DIR'])/'profile');r=p._recorder
obj=CMDRDatabase.__new__(CMDRDatabase);obj.path=Path(os.environ['PROFILE_TEST_DIR'])/'db'
con=obj._connect();con.execute('CREATE TABLE t(x)');con.commit()
locked=threading.Event()
def locker():
    other=sqlite3.connect(obj.path)
    other.execute('BEGIN IMMEDIATE');locked.set();time.sleep(.12)
    other.commit();other.close()
thread=threading.Thread(target=locker);thread.start();assert locked.wait(2)
@p.measure('db.test_wait')
def write():
    with con:con.execute('INSERT INTO t VALUES(1)')
write();thread.join();con.close();p.shutdown()
rows=[json.loads(l)for l in r.path.read_text().splitlines()]
assert max(x['duration_ms']for x in rows if x['point']=='sql.execute.end')>=80
assert any(x['point']=='db.open.end' for x in rows)
''')

    def test_cursor_iteration_excludes_instrumented_nested_row_factory(self):
        now=[1_000_000_000]
        r=self.recorder(clock=lambda:now[0]);r.cpu_clock=lambda:now[0]
        outer=r.begin('db.outer');now[0]+=10_000_000
        def row():
            now[0]+=10_000_000
            inner=r.begin('slot.row_factory');now[0]+=20_000_000;r.end('slot.row_factory',inner)
            now[0]+=10_000_000
            return 42
        with patch.object(profile,'_recorder',r):self.assertEqual(profile.sql_next(row),42)
        now[0]+=50_000_000;r.end('db.outer',outer)
        rows=self.rows(r);end=next(x for x in rows if x['point']=='db.outer.end')
        self.assertEqual(end['duration_ms'],100)
        self.assertEqual(end['self_ms'],60)
        self.assertEqual(end['sql_iteration_ms'],20)
        self.assertEqual(end['sql_iteration_cpu_ms'],20)

    def test_real_cargo_signal_is_nested_under_refresh_section(self):
        self.subprocess('''
import os,json
from PySide6.QtCore import QObject
from cmdrhelper import performance_profile as p
from cmdrhelper.state import AppState
state=AppState.__new__(AppState);QObject.__init__(state)
state.cargo_snapshot={'synthetic':True};seen=[]
state.cargoSnapshotChanged.connect(seen.append)
p._recorder=p.Recorder(os.environ['PROFILE_TEST_DIR']);r=p._recorder
state._apply_live_cargo_snapshot({},None)
assert seen==[None] and state.cargo_snapshot is None
p.shutdown();rows=[json.loads(l)for l in r.path.read_text().splitlines()]
outer=next(x for x in rows if x['point']=='state.apply_live_cargo_snapshot.end')
signal=next(x for x in rows if x['point']=='signal.cargoSnapshotChanged.end')
assert signal['parent_span']==outer['span']
''')
