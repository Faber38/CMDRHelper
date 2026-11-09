"""Bounded aggregation and virtual long-session diagnostics without application startup."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from cmdrhelper import performance_profile as p


class LongProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def recorder(self, **kwargs):
        r = p.Recorder(self.tmp.name, **kwargs)
        self.addCleanup(r.close)
        return r

    def test_fast_aggregate_moments_and_slow_ancestry(self):
        now = [1_000_000_000]
        r = self.recorder(clock=lambda: now[0]); r.cpu_clock = lambda: now[0]
        outer = r.begin('gui.state_refresh')
        for ms in [1, 2, 3]:
            token = r.begin('db.connect'); now[0] += ms*1_000_000; r.end('db.connect', token)
        signal = r.begin('signal.changed')
        slot = r.begin('slot.mission_arrival.update')
        now[0] += 400_000_000
        r.end('slot.mission_arrival.update', slot)
        r.end('signal.changed', signal)
        r.end('gui.state_refresh', outer)
        self.assertTrue(r.close())
        summary = p.summarize(r.path)
        db = next(x for x in summary['aggregates'] if x['point']=='db.connect.end')
        self.assertEqual(db['count'], 3)
        self.assertEqual(db['metrics']['duration_ms'], dict(count=3,min=1,max=3,sum=6,mean=2))
        self.assertEqual(summary['aggregated_routine'], 3)
        rows = [json.loads(x) for x in r.path.read_text().splitlines()]
        self.assertFalse(any(x['point']=='db.connect.end' for x in rows))
        ends = {x['point']: x for x in rows if x['point'].endswith('.end') and 'self_ms' in x}
        self.assertEqual(ends['gui.state_refresh.end']['self_ms'], 0)
        self.assertEqual(ends['signal.changed.end']['parent_span'], outer[0])
        self.assertEqual(ends['slot.mission_arrival.update.end']['parent_span'], signal[0])
        self.assertEqual(len([x for x in rows if x['point'].endswith('.begin')]), 3)

    def test_routine_flood_cannot_displace_slow_records(self):
        gate = threading.Event()
        class Paused(p.Recorder):
            def _write(self):
                gate.wait(5)
                super()._write()
        r = Paused(self.tmp.name, capacity=4)
        self.addCleanup(r.close); self.addCleanup(gate.set)
        for _ in range(10000): r.emit('sql.execute.end', duration_ms=.1)
        r.emit('qt.event_delay', duration_ms=300)
        self.assertEqual(r.aggregated, 10000)
        self.assertEqual(r.important_dropped, 0)
        self.assertEqual(r.queue.qsize(), 2)
        for _ in range(10): r.emit('qt.event_delay', duration_ms=300)
        self.assertEqual(r.queue.qsize(), 4)
        self.assertEqual(r.important_dropped, 8)
        gate.set(); self.assertTrue(r.close())
        self.assertEqual(sum(x['count'] for x in r.snapshot()['aggregates']), 10012)

    def test_aggregate_key_count_is_bounded(self):
        r = self.recorder()
        for i in range(2000): r.emit('routine.point_'+str(i), duration_ms=.1)
        self.assertLessEqual(len(r.aggregates), 512)
        self.assertGreater(r.aggregate_overflow, 0)

    def test_low_free_space_and_write_error_disable_only_diagnostics(self):
        with patch('shutil.disk_usage', return_value=type('Space', (), {'free':0})()):
            r = self.recorder(); self.assertTrue(r.close()); self.assertTrue(r.failed)
        with patch('os.fdopen') as opened:
            opened.return_value.__enter__.return_value.write.side_effect = OSError('private detail')
            r = self.recorder(); self.assertTrue(r.close()); self.assertTrue(r.failed)
            r.emit('qt.event_delay', duration_ms=500)
            self.assertEqual(r.queue.qsize(), 0)

    def test_crash_recovery_and_legacy_reader(self):
        code = '''import os,time
from cmdrhelper.performance_profile import Recorder
now=[1_000_000_000]
r=Recorder(os.environ['PROFILE_DIR'],clock=lambda:now[0])
for _ in range(100):r.emit('sql.execute.end',duration_ms=.1)
now[0]+=61_000_000_000
r.emit('qt.event_delay',duration_ms=400)
limit=time.monotonic()+3
while time.monotonic()<limit:
 if r.path and r.path.exists() and 'session.aggregate' in r.path.read_text():break
 time.sleep(.02)
else:raise RuntimeError('checkpoint not flushed')
os._exit(0)
'''
        subprocess.run([sys.executable,'-B','-c',code], env=dict(os.environ,PROFILE_DIR=self.tmp.name),check=True,timeout=5)
        path = next(Path(self.tmp.name).glob('*.jsonl'))
        summary = p.summarize(path)
        self.assertFalse(summary['completed'])
        self.assertEqual(summary['aggregated_routine'],100)
        with path.open('a') as stream: stream.write('{"partial":')
        self.assertEqual(p.summarize(path)['aggregated_routine'],100)
        legacy = Path(self.tmp.name)/'legacy.jsonl'
        legacy.write_text('{"point":"session.start","format_version":2}\n'
                          '{"point":"qt.event_delay","duration_ms":400}\n'
                          '{"point":"session.end"}\n')
        self.assertTrue(p.summarize(legacy)['completed'])
        self.assertEqual(p.summarize(legacy)['format_version'],2)

    def test_more_than_old_session_limit_does_not_stop_recording(self):
        r = self.recorder()
        for batch in range(90):
            for _ in range(1000):
                r.emit('qt.dispatch', duration_ms=300, cpu_ms=1, receiver='QTimer',
                       event_type=1, nested_dispatches=0)
            r.queue.join()
        self.assertTrue(r.close())
        self.assertFalse(r.failed)
        self.assertEqual(r.important_dropped, 0)
        self.assertGreater(r.path.stat().st_size, 16*1024*1024)
        self.assertEqual(p.summarize(r.path)['counts']['qt.dispatch'], 90000)

    def test_worker_handoff_retains_origin_and_receiving_span(self):
        now=[1_000_000_000]
        r=self.recorder(clock=lambda:now[0])
        def worker():
            token=r.begin('worker.pool')
            r.mark('private source')
            r.end('worker.pool',token)
        thread=threading.Thread(target=worker);thread.start();thread.join()
        now[0]+=300_000_000
        receiver=r.begin('source.finished')
        r.receive('private source','worker.handoff')
        r.end('source.finished',receiver)
        self.assertTrue(r.close())
        rows=[json.loads(x)for x in r.path.read_text().splitlines()]
        origin=next(x for x in rows if x['point']=='worker.pool.end')
        handoff=next(x for x in rows if x['point']=='worker.handoff')
        self.assertEqual(handoff['origin_span'],origin['span'])
        self.assertEqual(handoff['span'],receiver[0])
        self.assertNotIn('private source',r.path.read_text())

    def test_virtual_60_minutes_with_bursts(self):
        directory = os.environ.get('PROFILE_SIMULATION_DIR',self.tmp.name)
        now = [1_000_000_000]; cpu = [0]
        r = p.Recorder(directory, clock=lambda: now[0])
        self.addCleanup(r.close); r.cpu_clock = lambda: cpu[0]
        start = time.perf_counter()
        for minute in range(60):
            now[0] = r.origin+minute*60_000_000_000
            for _ in range(10000):
                token = r.begin('sql.execute')
                now[0] += 100_000; cpu[0] += 50_000
                r.end('sql.execute',token)
            outer = r.begin('gui.state_refresh')
            signal = r.begin('signal.changed')
            slot = r.begin('slot.mission_arrival.update')
            now[0] += 400_000_000; cpu[0] += 20_000_000
            r.end('slot.mission_arrival.update',slot)
            r.end('signal.changed',signal); r.end('gui.state_refresh',outer)
            r.mark('synthetic'); now[0] += 300_000_000
            r.receive('synthetic','worker.handoff')
            r.emit('qt.event_delay',duration_ms=500)
            if minute in (30,59):
                for _ in range(250):
                    token=r.begin('db.transaction_exit'); now[0]+=25_000_000
                    r.end('db.transaction_exit',token)
            r.queue.join()
        now[0] = r.origin+3600_000_000_000
        r.emit('qt.event_delay',duration_ms=700)
        self.assertTrue(r.close()); self.assertFalse(r.failed)
        summary=json.loads(Path(str(r.path)+'.summary.json').read_text())
        self.assertEqual(summary['aggregated_routine'],600000)
        self.assertEqual(summary['important_dropped'],0)
        self.assertEqual(summary['aggregate_overflow'],0)
        rows=[json.loads(x)for x in r.path.read_text().splitlines()]
        important=[x for x in rows if 'duration_ms'in x and x['point']!='session.end']
        self.assertEqual(len(important),801)
        self.assertEqual(rows[-1]['duration_ms'],3600000)
        self.assertTrue(any(x['point']=='qt.event_delay' and x['monotonic_ns']==now[0] for x in rows))
        sql=next(x for x in summary['aggregates'] if x['point']=='sql.execute.end')
        self.assertEqual(sql['count'],600000)
        self.assertAlmostEqual(sql['metrics']['duration_ms']['sum'],60000,places=5)
        self.assertAlmostEqual(sql['metrics']['cpu_ms']['sum'],30000,places=5)
        result=dict(path=str(r.path),virtual_minutes=60,routine_events=600000,
                    equivalent_begin_end_events=1200000,important_retained=len(important),
                    important_dropped=r.important_dropped,jsonl_bytes=r.path.stat().st_size,
                    summary_bytes=Path(str(r.path)+'.summary.json').stat().st_size,
                    queue_peak=r.queue_peak,elapsed_seconds=round(time.perf_counter()-start,3),
                    lines=len(rows))
        print('SIMULATION',json.dumps(result))
        if os.environ.get('PROFILE_SIMULATION_DIR'):
            Path(directory,'simulation-result.json').write_text(json.dumps(result,indent=2))
