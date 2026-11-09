"""Isolated /proc, QSettings and Qt signal timing; no real application startup."""
import os
import subprocess
import sys
import unittest

SETUP = r'''
import json,tempfile,time,threading
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch,Mock
from PySide6.QtCore import QObject,Signal,QSettings
from cmdrhelper import performance_profile as p
from cmdrhelper import game_instances as game
from cmdrhelper.source_manager import SourceManager
root=tempfile.TemporaryDirectory();base=Path(root.name);proc=base/'proc';proc.mkdir()
(proc/'uptime').write_text('1000.00 1000.00')
def process(pid,elite=True,fds=1,target=None):
    entry=proc/str(pid);entry.mkdir()
    (entry/'cmdline').write_bytes(b'EliteDangerous64.exe\0PRIVATE_ARGUMENT' if elite else b'python\0PRIVATE_ARGUMENT')
    (entry/'stat').write_text(str(pid)+' (game) '+' '.join(['S']+['0']*18+['100']))
    (entry/'environ').write_bytes(b'PRIVATE_SECRET=never-log\0')
    (entry/'fd').mkdir()
    for n in range(fds):(entry/'fd'/str(n)).symlink_to(target or base/'absent')
    return entry
class State(QObject):
    viewedCommanderChanged=Signal(int)
    journalPositionsReady=Signal(object,str)
state=State();state.settings=QSettings(str(base/'settings.ini'),QSettings.IniFormat)
state.viewed_commander_id=state.commander_id=1;state.commander_fid='A';state.follow_live_commander=True
state._startup_cancel=threading.Event()
state.database=NS(list_commanders=Mock(return_value=[{'id':1,'fid':'A'},{'id':2,'fid':'B'}]))
state.edsm_settings_for_fid=lambda fid:{'enabled':False}
state.inara_settings_for_fid=lambda fid:{'enabled':False}
manager=SourceManager.__new__(SourceManager);QObject.__init__(manager)
manager.state=state;manager._process_observation=game.ProcessObservation();manager.preferred_source='steam'
manager._ingesting=True;manager.projecting=False;manager.runtimes={}
def runtime(name,cid,fid):
    folder=base/name;folder.mkdir();path=folder/'Journal.2026-01-01T120000.01.log';path.write_text('')
    row=dict(journal_file=str(path),commander_id=cid,fid_seen=fid,attribution_status='identified')
    manager.runtimes[name]=NS(source=NS(id=name,path=str(folder),enabled=True,status='ready',identities=[(fid,'Synthetic')]),
        processor=NS(initialized=True,sessions=[row]),last_transfer_at=0)
    return path
journal=runtime('steam',1,'A');other=runtime('heroic',2,'B')
scan_patch=patch('cmdrhelper.source_manager.inspect_instances',side_effect=lambda:game.inspect_instances(proc));scan_patch.start()
r=p.Recorder(base/'profile',detail_threshold_ms=0);p._recorder=r

def stats(point):
    return [a for a in r.snapshot()['aggregates']if a['point']==point]
def count(point):return sum(a['count']for a in stats(point))
'''
END = '''
p.shutdown();scan_patch.stop();root.cleanup()
'''


class SourceTickProfileTests(unittest.TestCase):
    def run_case(self,code,enabled='1'):
        env=dict(os.environ,CMDRHELPER_PROFILE=enabled,QT_QPA_PLATFORM='offscreen',PYTHONDONTWRITEBYTECODE='1')
        result=subprocess.run([sys.executable,'-B','-c',SETUP+code+END],env=env,capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)

    def test_no_one_multiple_and_stable_identity(self):
        self.run_case('''
manager._tick();assert manager.snapshot.instances==[]
entry=process(1,target=journal)
manager._tick();identity=manager.snapshot.instances[0].identity
for _ in range(5):manager._tick();assert manager.snapshot.instances[0].identity==identity
assert count('source.settings_sync.end')==1
assert count('source.settings_write.end')==4
assert count('source.select.end')==6
assert count('source.transfer_check.end')==7 and count('source.project.end')==7
process(2,target=other);manager._tick();assert len(manager.snapshot.instances)==2
assert count('source.settings_sync.end')==1
p.shutdown()
rows=[json.loads(line)for line in r.path.read_text().splitlines()]
scans=[x for x in rows if x['point']=='process.inspect_instances.end']
assert [(x['process_count'],x['fd_count'],x['elite_count'])for x in scans]==[(0,0,0)]+[(1,1,1)]*6+[(2,2,2)]
assert not any(v in r.path.read_text()for v in ['PRIVATE_ARGUMENT','PRIVATE_SECRET',str(base)])
''')

    def test_commander_source_switch_and_sync_signal_attribution(self):
        self.run_case('''
entry=process(1,target=journal);manager._tick()
now=[r.clock()];cpu=[0];r.clock=lambda:now[0];r.cpu_clock=lambda:cpu[0]
@p.measure('slot.test_commander')
def received(cid):now[0]+=250_000_000;cpu[0]+=1_000_000
state.viewedCommanderChanged.connect(received)
(entry/'fd'/'0').unlink();(entry/'fd'/'0').symlink_to(other)
original=state.settings.sync
def slow_sync():
    original();now[0]+=300_000_000;cpu[0]+=2_000_000
with patch.object(state.settings,'sync',side_effect=slow_sync):manager._tick()
assert state.viewed_commander_id==2 and manager.preferred_source=='heroic'
assert count('source.settings_sync.end')==2
assert count('source.settings_write.end')==7
# Different source for the same commander still persists source_id.
alternate=runtime('alternate',2,'B')
(entry/'fd'/'0').unlink();(entry/'fd'/'0').symlink_to(alternate)
manager._tick();assert count('source.settings_sync.end')==3
assert count('source.settings_write.end')==8
p.shutdown();rows=[json.loads(l)for l in r.path.read_text().splitlines()]
ends={x['span']:x for x in rows if x['point'].endswith('.end') and 'span'in x}
sync=[x for x in ends.values()if x['point']=='source.settings_sync.end' and x['duration_ms']==300][0]
assert sync['cpu_ms']==2 and sync['self_ms']==300
slot=[x for x in ends.values()if x['point']=='slot.test_commander.end'][0]
assert ends[slot['parent_span']]['point']=='signal.viewedCommanderChanged.end'
tick=[x for x in ends.values()if x['point']=='source.tick.end' and x['duration_ms']==550][0]
assert tick['cpu_ms']==3 and tick['self_ms']==0
''')

    def test_large_proc_and_descriptor_counts(self):
        self.run_case('''
for i in range(1,1001):process(i,elite=False,fds=0)
process(1001,fds=1000,target=journal)
manager._tick()
a=stats('process.inspect_instances.end')[0]['metrics']
assert a['process_count']['sum']==1001 and a['fd_count']['sum']==1000 and a['elite_count']['sum']==1
assert count('process.cmdline.end')==1001
assert count('process.fd_resolve.end')==1000
assert count('process.identity.end')==count('process.identity_recheck.end')==1
''')

    def test_slow_proc_reads_are_attributed_to_exact_section(self):
        self.run_case('''
entry=process(1,target=journal)
now=[r.clock()];cpu=[0];r.clock=lambda:now[0];r.cpu_clock=lambda:cpu[0]
original_bytes=Path.read_bytes;original_resolve=Path.resolve;original_iter=Path.iterdir
for filename,point in [('cmdline','process.cmdline.end'),('environ','process.environ.end'),('fd','process.fd_resolve.end'),('proc','process.enumerate.end')]:
    def delay():now[0]+=400_000_000;cpu[0]+=2_000_000
    def read(path,*a,**kw):
        if path==entry/filename:delay()
        return original_bytes(path,*a,**kw)
    def resolve(path,*a,**kw):
        if filename=='fd' and path.parent==entry/'fd':delay()
        return original_resolve(path,*a,**kw)
    def entries(path):
        if filename=='proc' and path==proc:delay()
        return original_iter(path)
    with patch.object(Path,'read_bytes',read),patch.object(Path,'resolve',resolve),patch.object(Path,'iterdir',entries):
        result=game.inspect_instances(proc)
    assert len(result.instances)==1
    assert stats(point)[0]['metrics']['duration_ms']['max']==400
    assert stats(point)[0]['metrics']['cpu_ms']['max']==2
p.shutdown();rows=[json.loads(l)for l in r.path.read_text().splitlines()]
assert all(x['self_ms']==0 for x in rows if x['point']=='process.inspect_instances.end')
''')

    def test_disabled_has_no_active_sections_or_measurement(self):
        self.run_case('''
p._recorder=None;r.close();process(1,target=journal)
with patch.object(p,'_Section',side_effect=AssertionError('disabled')):
    manager._tick();assert len(manager.snapshot.instances)==1
assert not hasattr(SourceManager.choose,'__wrapped__')
assert p._recorder is None and p._timer is None
''','0')
