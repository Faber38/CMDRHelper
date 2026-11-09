"""Arrival instrumentation through isolated synthetic data and real Qt signals."""
import os
import subprocess
import sys
import unittest

SETUP = r'''
import json,tempfile
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from PySide6.QtCore import QObject,Signal,QTimer
from PySide6.QtWidgets import QApplication,QTableWidget,QTableWidgetItem
from cmdrhelper import performance_profile as p
from cmdrhelper import game_instances
from cmdrhelper.source_processing import SourceProcessor
from cmdrhelper.ui.mission_arrival import MissionArrivalController,ARRIVAL_PLACE_ROLE
import test_mission_arrival as fixture
app=QApplication.instance() or QApplication([])
f=fixture.ArrivalSourceTests();f.setUp()
class State(QObject):changed=Signal()
state=State()
for key,value in vars(f.state).items():setattr(state,key,value)
source_signals=State();state.sources.changed=source_signals.changed;state.sources.timer=QTimer()
proc=Path(f.tmp.name)/'proc';proc.mkdir();(proc/'uptime').write_text('1000.00 1000.00')
entry=proc/'12';entry.mkdir();(entry/'cmdline').write_bytes(b'EliteDangerous64.exe\0')
(entry/'stat').write_text('12 (game) '+' '.join(['S']+['0']*18+['100']))
(entry/'environ').write_bytes(b'');(entry/'fd').mkdir();(entry/'fd'/'0').symlink_to(f.path)
f.mock_process.side_effect=lambda:game_instances.inspect_instances(proc)
processor=SourceProcessor(None,f.path.parent);processor.sessions=[f.session]
f.runtime.processor=processor
payload={}
def publish():
    processor._projection=(processor._projection_key(processor.sessions),
        dict(commander_fid='A',latest_journal_session=deepcopy(f.session),**payload))
publish()
state.missions=[fixture.mission(i+1) for i in range(100)]
table=QTableWidget(100,3);table.arrival_commander=1
for row,mission in enumerate(state.missions):
    item=QTableWidgetItem('Synthetic');item.setData(ARRIVAL_PLACE_ROLE,'Synthetic');item.mission=mission
    table.setItem(row,2,item)
controller=MissionArrivalController(state,table)
table.show()
tmp=tempfile.TemporaryDirectory()
r=p.Recorder(tmp.name,detail_threshold_ms=0);p._recorder=r
'''
CLEANUP = '''
p.shutdown();table.close();f.doCleanups();tmp.cleanup()
'''


class ArrivalProfileTests(unittest.TestCase):
    def run_case(self, code, enabled='1'):
        env=dict(os.environ,CMDRHELPER_PROFILE=enabled,QT_QPA_PLATFORM='offscreen',
                 PYTHONDONTWRITEBYTECODE='1')
        result=subprocess.run([sys.executable,'-B','-c',SETUP+code+CLEANUP],env=env,
                              capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)

    def test_stable_process_journal_and_repeated_signals(self):
        self.run_case('''
for _ in range(20):state.changed.emit()
assert len(controller.hits)==100
snapshot=r.snapshot()['aggregates']
def stat(point,outcome='success'):
    return next(x for x in snapshot if x['point']==point and x['outcome']==outcome)
assert stat('arrival.cache','cache_miss')['count']==1
assert stat('arrival.cache','cache_hit')['count']==19
assert stat('arrival.inspect_instances.end')['count']==20
assert stat('arrival.projection.end')['count']==20
assert stat('arrival.table_update.end')['count']==20
assert stat('arrival.status_read.end')['count']==20
assert stat('arrival.cache_rebuild.end')['count']==1
p.shutdown()
rows=[json.loads(x) for x in r.path.read_text().splitlines()]
ends={x['span']:x for x in rows if x['point'].endswith('.end') and 'span'in x}
for x in ends.values():
    if x['point'].startswith('arrival.'):
        assert 'cpu_ms' in x and 'self_cpu_ms' in x and 'parent_span' in x
assert any(x['point']=='arrival.inspect_instances.end' and
    ends[x['parent_span']]['point']=='arrival.process_check.end' for x in ends.values())
assert not any(secret in r.path.read_text() for secret in ['HIP 97950','Donoso','Synthetic',str(f.path)])
''')

    def test_commander_switch_and_new_arrival_keep_behavior(self):
        self.run_case('''
state.changed.emit();assert len(controller.hits)==100
state.viewed_commander_id=2;state.changed.emit();assert not controller.hits
state.viewed_commander_id=1;state.changed.emit();assert len(controller.hits)==100
f.events.append(fixture.event('SupercruiseEntry',StarSystem='HIP 97950'));f.write();publish()
state.changed.emit();assert not controller.hits
f.events.append(fixture.dock());f.write();publish()
state.changed.emit();assert len(controller.hits)==100 and controller.timer.isActive()
assert next(x for x in r.snapshot()['aggregates']if x['point']=='arrival.cache' and x['outcome']=='cache_miss')['count']==3
''')

    def test_wait_attribution_and_synchronous_receiver_nesting(self):
        self.run_case('''
now=[1_000_000_000];cpu=[0];r.clock=lambda:now[0];r.cpu_clock=lambda:cpu[0]
inspect=f.mock_process.side_effect
# Controlled waiting-time model, not a claim about real process inspection.
def wait_inspect():
    result=inspect();now[0]+=350_000_000;cpu[0]+=2_000_000;return result
f.mock_process.side_effect=wait_inspect
@p.measure('slot.test_arrival')
def received():now[0]+=40_000_000;cpu[0]+=1_000_000
controller.arrivalChanged.connect(received)
state.changed.emit();p.shutdown()
rows=[json.loads(x)for x in r.path.read_text().splitlines()]
ends={x['point']:x for x in rows if x['point'].endswith('.end')}
a=ends['arrival.inspect_instances.end'];assert a['duration_ms']==350 and a['cpu_ms']==2
assert ends['slot.test_arrival.end']['parent_span']==ends['signal.arrivalChanged.end']['span']
assert ends['slot.mission_arrival.update.end']['duration_ms']==390
assert ends['slot.mission_arrival.update.end']['self_ms']==0
''')

    def test_actual_mission_detail_receiver_is_nested(self):
        self.run_case("""
import test_mission_arrival_ui as ui_fixture
ui_fixture.ArrivalUiTests.setUpClass()
ui=ui_fixture.ArrivalUiTests();ui.setUp()
try:
    before=r.serial
    ui.arrive()
    p.shutdown()
    rows=[json.loads(x)for x in r.path.read_text().splitlines()]
    ends={x['span']:x for x in rows if x['point'].endswith('.end') and x.get('span',0)>before}
    receivers=[x for x in ends.values() if x['point']=='slot.missions.selection_changed.end']
    assert receivers
    assert any(ends[x['parent_span']]['point']=='signal.arrivalChanged.end' for x in receivers)
finally:ui.doCleanups()
""")

    def test_disabled_does_not_measure_or_change_result(self):
        self.run_case('''
p._recorder=None;r.close()
with patch.object(p,'_Section',side_effect=AssertionError('No active sections')):
    state.changed.emit();assert len(controller.hits)==100
assert not hasattr(MissionArrivalController.update,'__wrapped__')
assert p._recorder is None and p._timer is None
''','0')

    def test_large_journal_and_history_remain_read_only(self):
        self.run_case('''
for i in range(500):
    (f.path.parent/('Journal.2025-01-01T000000.%02d.log'%i)).write_text('')
f.events[2:2]=[fixture.event('FuelScoop',Scooped=1)]*20000
f.write();publish();before=f.path.read_bytes()
for _ in range(3):state.changed.emit()
assert f.path.read_bytes()==before and len(controller.hits)==100
assert next(x for x in r.snapshot()['aggregates']if x['point']=='arrival.cache' and x['outcome']=='cache_miss')['count']==1
''')
