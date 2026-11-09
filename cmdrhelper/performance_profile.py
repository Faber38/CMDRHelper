"""Startup-only diagnostics with bounded memory, not file sizes. No payloads."""
import os
from functools import wraps
from contextlib import nullcontext

ENABLED = os.environ.get('CMDRHELPER_PROFILE') == '1'
_recorder = None
_timer = None
_inactive_section = nullcontext()
# Stable technical page labels; never translated/user-provided widget text.
PAGES = ('overview', 'missions', 'explorer', 'chronicle', 'jump_tip', 'route_planner',
         'images', 'commander', 'settings', 'materials', 'trade', 'powerplay', 'navigation')


def measure(point, *, menu=False):
    def decorate(function):
        if not ENABLED:
            return function

        @wraps(function)
        def wrapped(*args, **kwargs):
            recorder = _recorder
            if recorder is None or recorder.closed or recorder.failed:
                return function(*args, **kwargs)
            context = {}
            if menu:
                index = args[1] if len(args) > 1 else kwargs.get('idx')
                if type(index) is int and 0 <= index < len(PAGES):
                    context['view'] = PAGES[index]
            token = recorder.begin(point, **context)
            outcome = 'success'
            try:
                return function(*args, **kwargs)
            except BaseException:
                outcome = 'error'
                raise
            finally:
                recorder.end(point, token, outcome=outcome, **context)
        return wrapped
    return decorate


def event(point, **context):
    if _recorder is not None:
        _recorder.emit(point, **context)


def mark(key):
    if _recorder is not None:
        _recorder.mark(key)


def receive(key, point):
    if _recorder is not None:
        _recorder.receive(key, point)


def call(point, function, *args, **kwargs):
    """Only called behind ENABLED guards; arguments never enter a record."""
    return measure(point)(function)(*args, **kwargs)


class _Section:
    def __init__(self, recorder, point):
        self.recorder, self.point = recorder, point

    def __enter__(self):
        self.token = self.recorder.begin(self.point)
        self.context = {}
        return self.context

    def __exit__(self, kind, value, traceback):
        outcome = 'error' if kind else 'success'
        if kind and self.point == 'process.fd_resolve':
            import errno
            # /proc descriptors can disappear, be inaccessible, or refer to
            # socket/pipe pseudo-targets that strict Path.resolve cannot open.
            # Only classify the existing, OSError-catching inspection path.
            stack = self.recorder.local.stack
            inspection = next((f for f in reversed(stack[:-1])
                               if f[7] == 'process.inspect_instances'), None)
            expected = {errno.ENOENT: 'missing', errno.ESRCH: 'process_gone',
                        errno.EBADF: 'closed', errno.EACCES: 'permission',
                        errno.EPERM: 'permission'}
            category = (expected.get(value.errno, 'other_os_error')
                        if isinstance(value, OSError) else 'other_exception')
            self.context['error_category'] = category
            if (isinstance(value, OSError) and value.errno in expected
                    and inspection is not None and len(stack) > 1
                    and stack[-2][7] == 'process.fd_scan'):
                outcome = 'expected_error'
        self.recorder.end(self.point, self.token, outcome=outcome, **self.context)


def section(point):
    """Measure an existing block without moving its returns or exception handling."""
    recorder = _recorder
    if not ENABLED or recorder is None or recorder.closed or recorder.failed:
        return _inactive_section
    return _Section(recorder, point)


def sql_call(point, function, *args, **kwargs):
    recorder = _recorder
    if recorder is None or not getattr(recorder.local, 'db_depth', 0):
        return function(*args, **kwargs)
    return call(point, function, *args, **kwargs)


def sql_next(function):
    # Per-row clocks but no per-row queue records. Include exhaustion checks.
    recorder = _recorder
    if (recorder is None or recorder.closed or recorder.failed
            or not getattr(recorder.local, 'db_depth', 0)):
        return function()
    frame = recorder.local.stack[-1]
    start, cpu = recorder.clock(), recorder.cpu_clock()
    previous_wall, previous_cpu = frame[4], frame[5]
    try:
        return function()
    finally:
        wall, used = recorder.clock()-start, recorder.cpu_clock()-cpu
        nested_wall, nested_cpu = frame[4]-previous_wall, frame[5]-previous_cpu
        frame[4] = previous_wall+wall
        frame[5] = previous_cpu+used
        frame[6][0] += max(0, wall-nested_wall)
        frame[6][1] += max(0, used-nested_cpu)
        frame[6][2] += 1


class Aggregate:
    """Constant-size moments and a logarithmic duration histogram (upper-bound percentiles)."""
    METRICS = ('duration_ms', 'cpu_ms', 'self_ms', 'self_cpu_ms',
               'sql_iteration_ms', 'sql_iteration_cpu_ms', 'sql_iteration_steps',
               'process_count', 'fd_count', 'elite_count',
               'fd_error_count', 'fd_error_ms', 'fd_error_cpu_ms',
               'scan_requests', 'scan_coalesced', 'scan_discarded')
    BOUNDS = tuple(0.001 * 2**i for i in range(36))

    def __init__(self):
        self.count = 0
        self.metrics = {}
        self.histogram = [0] * (len(self.BOUNDS)+1)

    def add(self, row):
        from bisect import bisect_left
        self.count += 1
        for key in self.METRICS:
            if key in row:
                value = row[key]
                stat = self.metrics.setdefault(key, [0, value, value, 0.0])
                stat[0] += 1
                stat[1] = min(stat[1], value)
                stat[2] = max(stat[2], value)
                stat[3] += value
        if 'duration_ms' in row:
            self.histogram[bisect_left(self.BOUNDS, row['duration_ms'])] += 1

    def export(self):
        result = dict(count=self.count, metrics={k: dict(count=v[0], min=v[1], max=v[2],
                     sum=v[3], mean=v[3]/v[0]) for k,v in self.metrics.items()})
        n = sum(self.histogram)
        if n:
            import math
            result['duration_percentiles_upper_ms'] = {}
            for label, q in [('p50', .5), ('p95', .95), ('p99', .99)]:
                total = 0
                for i, count in enumerate(self.histogram):
                    total += count
                    if total >= math.ceil(n*q):
                        result['duration_percentiles_upper_ms'][label] = (
                            min(self.BOUNDS[i], self.metrics['duration_ms'][2])
                            if i < len(self.BOUNDS) else self.metrics['duration_ms'][2])
                        break
        return result


class Recorder:
    """Nonblocking producers; all serialization and file I/O belong to the writer."""
    def __init__(self, directory='/tmp/cmdrhelper-profile', *,
                 capacity=2048, clock=None, detail_threshold_ms=None):
        import queue
        import threading
        import time
        self.clock = clock or time.perf_counter_ns
        self.cpu_clock = time.thread_time_ns
        self.origin = self.clock()
        self.wall = time.time()
        self.main_ident = threading.get_ident()
        self.local = threading.local()
        self.directory = directory
        self.queue = queue.Queue(maxsize=capacity)
        self.stop = threading.Event()
        self.closed = False
        self.dropped = 0
        self.important_dropped = 0
        self.aggregated = 0
        self.aggregate_overflow = 0
        self.queue_peak = 0
        self.aggregates = {}
        self.detail_threshold_ms = detail_threshold_ms
        self.failed = False
        self.pending = {}
        self.lock = threading.Lock()
        self.serial = 0
        self.path = None
        self.thread = threading.Thread(target=self._write, name='CMDRHelper-Profile', daemon=True)
        self.thread.start()
        self.emit('session.start', format_version=3)

    @staticmethod
    def _context(values):
        # No arbitrary strings, identities, exception text or function arguments.
        enums = {'receiver': {'QTimer', 'MainWindow', 'SourceManager', 'JournalWatcher',
                    'AppState', 'QWidget', 'QWindow', 'QApplication', 'other'}, 'view': set(PAGES), 'trigger': {'manual', 'automatic', 'other'},
                 'error_category': {'missing', 'process_gone', 'closed', 'permission',
                                    'other_os_error', 'other_exception'},
                 'outcome': {'success', 'error', 'expected_error', 'cache_hit', 'server_wait', 'error_pause',
                             'busy', 'inactive', 'started', 'skipped', 'retained', 'cache_miss'},
                 'event': {'FSDJump', 'Location', 'CarrierJump', 'Cargo', 'CargoTransfer',
                           'MarketBuy', 'MarketSell', 'CollectCargo', 'EjectCargo', 'TransferCargo'}}
        numbers = {'format_version', 'duration_ms', 'cpu_ms', 'retry_seconds', 'cache_age_seconds', 'count',
                   'event_type', 'span', 'parent_span', 'start_ns', 'http_status', 'nested_dispatches',
                   'origin_span', 'self_ms', 'self_cpu_ms', 'sql_iteration_ms', 'sql_iteration_cpu_ms', 'sql_iteration_steps',
                   'process_count', 'fd_count', 'elite_count',
                   'fd_error_count', 'fd_error_ms', 'fd_error_cpu_ms',
                   'scan_requests', 'scan_coalesced', 'scan_discarded'}
        import math
        return {k:v for k,v in values.items() if
                (k in enums and isinstance(v, str) and v in enums[k]) or
                (k in numbers and type(v) in (int, float) and math.isfinite(v) and v >= 0)}

    def _important(self, point, context):
        if point == 'process.fd_resolve.end' and context.get('outcome') == 'expected_error':
            return False  # Timings remain in aggregates and enclosing FD/inspection spans.
        if point.startswith('session.') or context.get('outcome') in {'error', 'server_wait', 'error_pause'}:
            return True
        if point in {'journal.events', 'journal.retry', 'journal.retry_wait'}:
            return True
        if point.startswith('spansh.') and 'duration_ms' not in context:
            return context.get('outcome') not in {'cache_hit', 'busy', 'inactive', 'skipped'}
        threshold = self.detail_threshold_ms
        if threshold is None:
            threshold = (20 if point.startswith(('db.', 'sql.')) else
                         100 if point.startswith(('menu.', 'gui.', 'state.', 'signal.', 'slot.', 'arrival.', 'process.', 'source.settings_'))
                         or 'handoff' in point else 200)
        return context.get('duration_ms', -1) >= threshold

    def _enqueue(self, row):
        import queue
        try:
            self.queue.put_nowait(row)
            self.queue_peak = max(self.queue_peak, self.queue.qsize())
        except queue.Full:
            self.dropped += 1
            self.important_dropped += 1

    def _promote(self):
        # Preserve the complete active ancestor chain of an interesting child.
        # Fast completed children remain represented by the parent's self times.
        for frame in getattr(self.local, 'stack', ()):
            if not frame[9]:
                frame[9] = True
                self._enqueue(dict(point=frame[7]+'.begin', monotonic_ns=frame[1],
                    thread=frame[10], span=frame[0], parent_span=frame[3], **frame[8]))

    def emit(self, point, **context):
        if self.closed or self.failed:
            return
        import threading
        if not isinstance(point, str) or not point.replace('.', '').replace('_', '').isalnum() or len(point)>80:
            return
        force = context.pop('_detail', False)
        context.setdefault('span', getattr(self.local, 'span', 0))
        context = self._context(context)
        row = dict(point=point, monotonic_ns=self.clock(),
                   thread='main' if threading.get_ident() == self.main_ident else 'worker', **context)
        important = force or self._important(point, context)
        key = (point, row['thread'], context.get('view'), context.get('outcome'),
               context.get('event'), context.get('error_category'))
        with self.lock:
            if key not in self.aggregates and len(self.aggregates) >= 512:
                self.aggregate_overflow += 1
            else:
                stats = self.aggregates.get(key)
                if stats is None:
                    stats = self.aggregates[key] = Aggregate()
                stats.add(row)
            if not important:
                self.aggregated += 1
        if important:
            self._promote()
            self._enqueue(row)

    def snapshot(self):
        with self.lock:
            rows = [dict(point=k[0], thread=k[1], view=k[2], outcome=k[3], event=k[4],
                         **({'error_category': k[5]} if k[5] is not None else {}),
                         **v.export()) for k, v in self.aggregates.items()]
            return dict(aggregates=rows, aggregated_routine=self.aggregated,
                        dropped=self.dropped, important_dropped=self.important_dropped,
                        aggregate_overflow=self.aggregate_overflow, queue_peak=self.queue_peak,
                        unmatched_handoffs=len(self.pending))

    def begin(self, point, **context):
        with self.lock:
            self.serial += 1
            serial = self.serial
        parent = getattr(self.local, 'span', 0)
        self.local.span = serial
        import threading
        token = [serial, self.clock(), self.cpu_clock(), parent, 0, 0, [0, 0, 0],
                 point, self._context(context), False,
                 'main' if threading.get_ident() == self.main_ident else 'worker',
                 {} if point == 'process.inspect_instances' else None]
        stack = getattr(self.local, 'stack', None)
        if stack is None:
            stack = self.local.stack = []
        stack.append(token)
        if point.startswith('db.'):
            self.local.db_depth = getattr(self.local, 'db_depth', 0)+1
        return token

    def end(self, point, token, **context):
        serial, start, cpu, parent, child_wall, child_cpu, iteration = token[:7]
        elapsed, used_cpu = self.clock()-start, self.cpu_clock()-cpu
        stack = self.local.stack
        if len(stack) > 1:
            stack[-2][4] += elapsed
            stack[-2][5] += used_cpu
        if point.startswith('db.'):
            self.local.db_depth -= 1
        if point == 'process.fd_resolve' and context.get('outcome') == 'expected_error':
            inspection = next(f for f in reversed(stack[:-1])
                              if f[7] == 'process.inspect_instances')
            totals = inspection[11].setdefault(context['error_category'], [0, 0, 0])
            totals[0] += 1
            totals[1] += elapsed
            totals[2] += used_cpu
        if point == 'process.inspect_instances':
            # One event per category and inspection, never one per failed FD.
            # These are accounting fields, not additional/nested durations.
            for category, (count, wall, used) in token[11].items():
                self.emit('process.fd_errors', _detail=True, error_category=category,
                          outcome='expected_error', fd_error_count=count,
                          fd_error_ms=wall/1e6, fd_error_cpu_ms=used/1e6)
        self.emit(point+'.end', _detail=token[9], span=serial, parent_span=parent, start_ns=start,
                  duration_ms=elapsed/1e6, cpu_ms=used_cpu/1e6,
                  self_ms=max(0, elapsed-child_wall)/1e6,
                  self_cpu_ms=max(0, used_cpu-child_cpu)/1e6,
                  sql_iteration_ms=iteration[0]/1e6, sql_iteration_cpu_ms=iteration[1]/1e6,
                  sql_iteration_steps=iteration[2], **context)
        stack.pop()
        self.local.span = parent

    def mark(self, key):
        if self.closed or self.failed:
            return
        self._promote()
        with self.lock:
            if len(self.pending) >= 2048:
                self.pending.pop(next(iter(self.pending)))
                self.dropped += 1
            self.pending[key] = (self.clock(), getattr(self.local, 'span', 0))

    def receive(self, key, point):
        with self.lock:
            start = self.pending.pop(key, None)
        if start is not None:
            start, origin_span = start
            self.emit(point, start_ns=start, origin_span=origin_span, duration_ms=(self.clock()-start)/1e6)

    def close(self):
        if not self.closed:
            self.closed = True
            self.stop.set()
        # Called after app.exec()/startup returns, never from a GUI event handler.
        self.thread.join(timeout=2)
        return not self.thread.is_alive()

    def _write(self):
        import datetime
        import json
        import pathlib
        import queue
        import shutil
        import stat
        import time
        import uuid
        totals, top = {}, {}
        written = 0
        try:
            root = pathlib.Path(self.directory)
            root.mkdir(mode=0o700, parents=True, exist_ok=True)
            info = root.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
                raise OSError('Unsafe diagnostic directory')
            def check_space():
                if shutil.disk_usage(root).free < 8*1024*1024:
                    raise OSError('Low free disk space')
            check_space()
            name = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            self.path = root / f'profile-{name}-{os.getpid()}-{uuid.uuid4().hex[:8]}.jsonl'
            fd = os.open(self.path, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                def write(row):
                    nonlocal written
                    row.setdefault('monotonic_ns', self.clock())
                    row['timestamp'] = datetime.datetime.fromtimestamp(
                        self.wall+(row['monotonic_ns']-self.origin)/1e9,
                        datetime.timezone.utc).isoformat()
                    line = json.dumps(row, separators=(',', ':'))+'\n'
                    stream.write(line)
                    written += len(line.encode('utf-8'))
                checkpoint = self.origin
                flushed = checked = time.monotonic()
                while not self.stop.is_set() or not self.queue.empty():
                    try:
                        row = self.queue.get(timeout=.25)
                    except queue.Empty:
                        row = None
                    if row is not None:
                        try:
                            write(row)
                            point = row['point']
                            count_key = point if point in totals or len(totals) < 512 else 'other'
                            totals[count_key] = totals.get(count_key, 0)+1
                            if 'duration_ms' in row:
                                bucket = category(row)
                                top.setdefault(bucket, []).append(row)
                                top[bucket] = sorted(top[bucket], key=lambda r:r['duration_ms'], reverse=True)[:20]
                        finally:
                            self.queue.task_done()
                    now = time.monotonic()
                    if now-checked >= 5:
                        check_space()
                        checked = now
                    if self.clock()-checkpoint >= 60_000_000_000:
                        write(dict(point='session.aggregate', **self.snapshot()))
                        checkpoint = self.clock()
                    if now-flushed >= 1 or row is None:
                        stream.flush()
                        flushed = now
                final = self.snapshot()
                write(dict(point='session.aggregate', **final))
                write(dict(point='session.end', duration_ms=(self.clock()-self.origin)/1e6,
                           **{k:v for k,v in final.items() if k != 'aggregates'}))
            summary = dict(format_version=3, counts=totals, top=top, bytes_written=written, **final)
            fd = os.open(str(self.path)+'.summary.json', os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump(summary, stream, indent=2)
        except Exception:
            self.failed = True
            self.stop.set()
            # Release queued references after failure; never propagate I/O errors.
            while True:
                try:
                    self.queue.get_nowait()
                    self.queue.task_done()
                    self.dropped += 1
                    self.important_dropped += 1
                except queue.Empty:
                    break
            import sys
            print('CMDRHelper profile: diagnostic writer unavailable; recording disabled.', file=sys.stderr)


def category(row):
    point = row['point']
    if point.startswith('db.') or point.startswith('sql.'): return 'database'
    if point.startswith('signal.') or point.startswith('slot.'): return 'signals'
    if point.startswith('state.'): return 'refresh_sections'
    if point.startswith('arrival.'): return 'arrival'
    if point.startswith('process.'): return 'process'
    if point.startswith('menu.'): return 'menu'
    if point.startswith('qt.'): return 'main_thread'
    if point.startswith('spansh.'): return 'spansh'
    if 'handoff' in point: return 'handoff'
    if point.startswith('journal.') or point.startswith('source.'): return 'journal'
    return 'background_and_gui'


def application_class(base):
    if not ENABLED:
        return base

    from threading import get_ident

    class ProfileApplication(base):
        def notify(self, receiver, event):
            recorder = _recorder
            if recorder is None or recorder.closed or recorder.failed:
                return super().notify(receiver, event)
            if get_ident() != recorder.main_ident:
                return super().notify(receiver, event)
            start, cpu = recorder.clock(), recorder.cpu_clock()
            kind = event.type().value
            receiver_name = type(receiver).__name__
            if receiver_name not in {'QTimer', 'MainWindow', 'SourceManager', 'JournalWatcher',
                                     'AppState', 'QWidget', 'QWindow', 'QApplication'}:
                receiver_name = 'other'
            self._profile_dispatch_serial = getattr(self, '_profile_dispatch_serial', 0)+1
            serial = self._profile_dispatch_serial
            try:
                return super().notify(receiver, event)
            finally:
                duration = (recorder.clock()-start)/1e6
                if duration >= 200:
                    recorder.emit('qt.dispatch', start_ns=start, duration_ms=duration,
                                  cpu_ms=(recorder.cpu_clock()-cpu)/1e6, event_type=kind,
                                  nested_dispatches=self._profile_dispatch_serial-serial, receiver=receiver_name)
    return ProfileApplication


def start(app):
    global _recorder, _timer
    if not ENABLED or _recorder is not None:
        return
    from PySide6.QtCore import QTimer, Qt
    try:
        _recorder = Recorder()
    except Exception:
        import sys
        print('CMDRHelper profile: recorder unavailable.', file=sys.stderr)
        return
    timer = QTimer(app)
    timer.setTimerType(Qt.PreciseTimer)
    timer.setInterval(100)
    expected = _recorder.clock()+100_000_000

    def tick():
        nonlocal expected
        if _recorder is None or _recorder.failed:
            timer.stop()
            return
        now = _recorder.clock()
        delay = max(0, (now-expected)/1e6)
        if delay >= 200:
            _recorder.emit('qt.event_delay', duration_ms=delay)
        expected = now+100_000_000

    timer.timeout.connect(tick)
    app.aboutToQuit.connect(timer.stop)
    timer.start()
    _timer = timer


def shutdown():
    global _recorder, _timer
    if _timer is not None:
        _timer.stop()
        _timer = None
    if _recorder is not None:
        recorder, _recorder = _recorder, None
        if not recorder.close():
            import sys
            print('CMDRHelper profile: writer shutdown incomplete.', file=sys.stderr)


def summarize(path):
    """Offline top durations, no application imports or network access."""
    import json
    from collections import Counter
    counts, top = Counter(), {}
    latest = {}
    completed = False
    version = None
    with open(path, encoding='utf-8') as stream:
        for line in stream:
            try:
                row = json.loads(line)
            except ValueError:
                continue  # A crash can leave an incomplete final record.
            if not isinstance(row, dict) or 'point' not in row:
                continue
            counts[row['point']] += 1
            if row['point'] == 'session.start': version = row.get('format_version', 1)
            if row['point'] == 'session.aggregate': latest = row
            if row['point'] == 'session.end': completed = True
            if 'duration_ms' in row:
                key = category(row)
                top.setdefault(key, []).append(row)
                top[key] = sorted(top[key], key=lambda r:r['duration_ms'], reverse=True)[:20]
    return dict(counts=dict(counts), top=top, format_version=version, completed=completed,
                **{k:v for k,v in latest.items() if k not in {'point', 'timestamp', 'monotonic_ns'}})


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description='Offline CMDRHelper profile summary')
    parser.add_argument('file')
    args = parser.parse_args()
    print(json.dumps(summarize(args.file), indent=2))
