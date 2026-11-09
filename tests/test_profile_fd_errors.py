"""FD diagnostic policy only; synthetic failures, no live process inspection."""
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cmdrhelper import performance_profile as p


class FDErrorProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.now, self.cpu = [1_000_000_000], [0]
        self.r = p.Recorder(self.tmp.name, clock=lambda: self.now[0])
        self.r.cpu_clock = lambda: self.cpu[0]
        self.addCleanup(self.r.close)
        for name, value in [('ENABLED', True), ('_recorder', self.r)]:
            patcher = patch.object(p, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def fail(self, error, ms=1):
        try:
            with p.section('process.fd_resolve'):
                self.now[0] += int(ms*1_000_000)
                self.cpu[0] += 100_000
                raise error
        except (OSError, ValueError):
            pass

    def rows(self):
        self.r.queue.join()
        self.assertTrue(self.r.close())
        self.assertFalse(self.r.failed)
        return [json.loads(line) for line in self.r.path.read_text().splitlines()]

    def test_many_expected_errors_keep_counts_times_and_parentage(self):
        with p.section('source.tick'):
            with p.section('process.inspect_instances'):
                with p.section('process.fd_scan'):
                    for _ in range(10000):
                        self.fail(FileNotFoundError(errno.ENOENT, 'PRIVATE', '/secret/fd'))
                self.now[0] += 2_000_000
                self.cpu[0] += 200_000
        rows = self.rows()
        self.assertFalse(any(x['point'].startswith('process.fd_resolve') for x in rows))
        events = [x for x in rows if x['point'] == 'process.fd_errors']
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['fd_error_count'], 10000)
        self.assertEqual(events[0]['fd_error_ms'], 10000)
        self.assertEqual(events[0]['fd_error_cpu_ms'], 1000)
        self.assertEqual(events[0]['error_category'], 'missing')
        ends = {x['point']: x for x in rows if 'self_ms' in x}
        inspect = ends['process.inspect_instances.end']
        scan = ends['process.fd_scan.end']
        self.assertEqual(events[0]['span'], inspect['span'])
        self.assertEqual(scan['parent_span'], inspect['span'])
        self.assertEqual(inspect['parent_span'], ends['source.tick.end']['span'])
        self.assertEqual((inspect['duration_ms'], inspect['cpu_ms']), (10002, 1000.2))
        self.assertEqual((inspect['self_ms'], inspect['self_cpu_ms']), (2, .2))
        self.assertEqual((scan['self_ms'], scan['self_cpu_ms']), (0, 0))
        stats = next(x for x in self.r.snapshot()['aggregates']
                     if x['point'] == 'process.fd_resolve.end')
        self.assertEqual(stats['count'], 10000)
        self.assertEqual(stats['metrics']['duration_ms']['sum'], 10000)
        self.assertEqual(self.r.important_dropped, 0)
        text = self.r.path.read_text() + Path(str(self.r.path)+'.summary.json').read_text()
        self.assertNotIn('PRIVATE', text)
        self.assertNotIn('/secret', text)

    def test_categories_unexpected_failures_and_scope(self):
        with p.section('process.inspect_instances'):
            with p.section('process.fd_scan'):
                for code in [errno.ENOENT, errno.ESRCH, errno.EBADF, errno.EACCES, errno.EPERM]:
                    self.fail(OSError(code, 'PRIVATE'))
                self.fail(OSError(errno.EIO, 'PRIVATE'))
                self.fail(ValueError('PRIVATE'))
        # An unrelated caller does not get the handled-error policy.
        self.fail(FileNotFoundError(errno.ENOENT, 'PRIVATE'))
        rows = self.rows()
        events = [x for x in rows if x['point'] == 'process.fd_errors']
        self.assertEqual({x['error_category']: x['fd_error_count'] for x in events},
                         dict(missing=1, process_gone=1, closed=1, permission=2))
        errors = [x for x in rows if x['point'] == 'process.fd_resolve.end']
        self.assertEqual([x['error_category'] for x in errors],
                         ['other_os_error', 'other_exception', 'missing'])
        self.assertTrue(all(x['outcome'] == 'error' for x in errors))
        self.assertNotIn('PRIVATE', self.r.path.read_text())

    def test_slow_expected_failure_preserves_enclosing_measurements(self):
        with p.section('slot.mission_arrival.update'):
            with p.section('arrival.snapshot'):
                with p.section('process.inspect_instances'):
                    with p.section('process.enumerate'):
                        self.now[0] += 200_000_000
                    with p.section('process.fd_scan'):
                        self.fail(FileNotFoundError(errno.ENOENT, 'PRIVATE'), ms=300)
        self.r.emit('qt.event_delay', duration_ms=500)
        rows = self.rows()
        for point in ['slot.mission_arrival.update.end', 'arrival.snapshot.end',
                      'process.inspect_instances.end', 'process.enumerate.end',
                      'process.fd_scan.end', 'qt.event_delay']:
            self.assertTrue(any(x['point'] == point for x in rows), point)
        begins = {x['span'] for x in rows if x['point'].endswith('.begin')}
        ends = {x['span'] for x in rows if 'self_ms' in x}
        self.assertEqual(begins, ends)
        self.assertFalse(any(x['point'] == 'process.fd_resolve.end' for x in rows))

    def test_inactive_without_start_option(self):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        env.pop('CMDRHELPER_PROFILE', None)
        code = '''
import errno, threading
from unittest.mock import patch
from cmdrhelper import performance_profile as p
before=threading.active_count()
with patch.object(p, '_Section', side_effect=AssertionError('active')):
    for _ in range(1000):
        try:
            with p.section('process.fd_resolve'):
                raise FileNotFoundError(errno.ENOENT, 'private')
        except OSError: pass
    p.start(None)
assert p._recorder is None and p._timer is None
assert threading.active_count()==before
'''
        result = subprocess.run([sys.executable, '-B', '-c', code], env=env,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(os.name == 'posix', 'synthetic Linux proc directory')
    def test_existing_inspection_handles_dangling_and_pseudo_targets(self):
        from cmdrhelper.game_instances import inspect_instances
        proc = Path(self.tmp.name)/'synthetic-proc'
        entry = proc/'123'
        (entry/'fd').mkdir(parents=True)
        (proc/'uptime').write_text('1000 1000')
        (entry/'cmdline').write_bytes(b'EliteDangerous64.exe\0PRIVATE_ARGUMENT')
        (entry/'environ').write_bytes(b'PRIVATE_SECRET=never-log\0')
        (entry/'stat').write_text('123 (game) '+' '.join(['S']+['0']*18+['100']))
        (entry/'fd'/'0').symlink_to(proc/'missing')
        (entry/'fd'/'1').symlink_to('pipe:[12345]')
        result = inspect_instances(proc)
        self.assertTrue(result.available)
        self.assertEqual(len(result.instances), 1)
        rows = self.rows()
        errors = [x for x in rows if x['point'] == 'process.fd_errors']
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['fd_error_count'], 2)
        text = self.r.path.read_text()
        for private in ['PRIVATE', 'pipe:', str(proc)]:
            self.assertNotIn(private, text)


if __name__ == '__main__':
    unittest.main()
