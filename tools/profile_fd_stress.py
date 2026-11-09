"""Controlled FD diagnostic load. No /proc, game, GUI, network or app state access.

Run with python -B tools/profile_fd_stress.py --output /tmp/<new-directory>.
For a before/after comparison, pass --recorder-source <saved-before-module.py>
to one run. --inactive measures the same synthetic workload without profiling.
"""
import argparse
from collections import Counter
import errno
import hashlib
import importlib.util
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--recorder-source', type=Path,
                        default=Path(__file__).resolve().parents[1]/'cmdrhelper/performance_profile.py')
    parser.add_argument('--errors', type=int, default=2_500_000)
    parser.add_argument('--inactive', action='store_true')
    args = parser.parse_args()
    if args.errors < 500 or args.errors % 500:
        parser.error('--errors must be a positive multiple of 500')
    args.output.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('fd_stress_profile', args.recorder_source)
    p = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(p)
    p.ENABLED = not args.inactive
    now, cpu = [1_000_000_000], [0]
    started, process_cpu, producer_cpu = time.perf_counter(), time.process_time(), time.thread_time()
    r = None
    if not args.inactive:
        r = p.Recorder(args.output, clock=lambda: now[0])
        r.cpu_clock = lambda: cpu[0]
        p._recorder = r
    controls = 0
    for batch in range(args.errors//500):
        root = 'source.tick' if batch % 2 == 0 else 'slot.mission_arrival.update'
        with p.section(root):
            with p.section('process.inspect_instances'):
                with p.section('process.enumerate'):
                    if batch % 100 == 0:
                        now[0] += 250_000_000
                        cpu[0] += 2_000_000
                with p.section('process.fd_scan'):
                    for _ in range(500):
                        try:
                            with p.section('process.fd_resolve'):
                                now[0] += 100_000
                                cpu[0] += 20_000
                                raise FileNotFoundError(errno.ENOENT, 'SYNTHETIC_PRIVATE')
                        except OSError:
                            pass
                    if batch % 100 == 0:
                        now[0] += 250_000_000
                        cpu[0] += 2_000_000
        if batch % 100 == 0:
            controls += 1
            p.event('qt.event_delay', duration_ms=550)
        # Identical pacing in both active runs: compare complete output, not
        # queue-loss artifacts. This is a test harness, never producer behavior.
        if r is not None:
            r.queue.join()
        now[0] += 1_000_000_000
        if (batch+1) % 1000 == 0:
            print(json.dumps(dict(progress_errors=(batch+1)*500)), flush=True)
    if r is not None:
        p._recorder = None
        assert r.close() and not r.failed
    result = dict(errors=args.errors, inactive=args.inactive,
                  source_sha256=hashlib.sha256(args.recorder_source.read_bytes()).hexdigest(),
                  wall_seconds=time.perf_counter()-started,
                  process_cpu_seconds=time.process_time()-process_cpu,
                  producer_cpu_seconds=time.thread_time()-producer_cpu,
                  virtual_seconds=(now[0]-1_000_000_000)/1e9)
    result['background_cpu_seconds'] = result['process_cpu_seconds']-result['producer_cpu_seconds']
    if r is not None:
        summary = json.loads(Path(str(r.path)+'.summary.json').read_text())
        counts, opened = Counter(), set()
        per_inspection, checkpoints = 0, 0
        slow = Counter()
        for line in r.path.open():
            assert 'SYNTHETIC_PRIVATE' not in line
            row = json.loads(line)
            point = row['point']
            counts[point] += 1
            if point.endswith('.begin'):
                opened.add(row['span'])
            elif 'self_ms' in row:
                assert row['span'] in opened
                opened.remove(row['span'])
            if point == 'process.fd_errors':
                assert row['span'] in opened
                per_inspection += row['fd_error_count']
            if point == 'session.aggregate':
                checkpoints += 1
            if point in ['process.inspect_instances.end', 'process.fd_scan.end',
                         'process.enumerate.end', 'source.tick.end',
                         'slot.mission_arrival.update.end', 'qt.event_delay']:
                if row['duration_ms'] >= 100:
                    slow[point] += 1
        assert row['point'] == 'session.end' and not opened
        assert not any(summary[k] for k in ['dropped', 'important_dropped', 'aggregate_overflow'])
        fd = [a for a in summary['aggregates'] if a['point'] == 'process.fd_resolve.end']
        assert sum(a['count'] for a in fd) == args.errors
        assert abs(sum(a['metrics']['duration_ms']['sum'] for a in fd)-args.errors*.1) < .01
        assert abs(sum(a['metrics']['cpu_ms']['sum'] for a in fd)-args.errors*.02) < .01
        assert all(slow[k] == controls for k in ['process.inspect_instances.end',
                   'process.fd_scan.end', 'process.enumerate.end', 'qt.event_delay'])
        if any(a.get('outcome') == 'expected_error' for a in fd):
            assert counts['process.fd_resolve.end'] == 0
            assert per_inspection == args.errors
        else:
            assert counts['process.fd_resolve.end'] == args.errors
        result.update(jsonl_path=str(r.path), jsonl_bytes=r.path.stat().st_size,
                      summary_bytes=Path(str(r.path)+'.summary.json').stat().st_size,
                      lines=sum(counts.values()), fd_detail_ends=counts['process.fd_resolve.end'],
                      fd_error_summary_events=counts['process.fd_errors'],
                      fd_error_summary_count=per_inspection, aggregate_fd_count=args.errors,
                      checkpoints=checkpoints, slow_retained=dict(slow),
                      dropped=r.dropped, important_dropped=r.important_dropped,
                      aggregate_overflow=r.aggregate_overflow, queue_peak=r.queue_peak)
    (args.output/'stress-result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
