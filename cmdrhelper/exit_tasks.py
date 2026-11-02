"""Admission and completion tracking for the application's existing workers.

No executor is replaced. Completion stays queued behind the worker's result
signals, so an idle thread alone never counts as an applied result.
"""
import threading
import time
from weakref import WeakSet
from shiboken6 import isValid
from PySide6.QtCore import QObject, Signal, Slot, QRunnable, QThreadPool, Qt
from PySide6.QtWidgets import QApplication


class _Done(QObject):
    ready = Signal(int)


class _Tracked(QRunnable):
    def __init__(self, task, token, signals):
        super().__init__()
        self.task, self.token, self.signals = task, token, signals
        # Diagnostic timestamps only; completion still follows queued signals.
        self.submitted_at = time.monotonic()
        self.started_at = self.finished_at = None

    def run(self):
        self.started_at = time.monotonic()
        try:
            self.task.run()
        except Exception:
            self.task._exit_failed = True
            raise
        finally:
            self.finished_at = time.monotonic()
            self.signals.ready.emit(self.token)


class ExitTasks(QObject):
    def __init__(self, app):
        super().__init__(app)
        self.draining = False
        self.owner = None
        self.tasks = {}
        self.pools = WeakSet()
        self.threads = []
        self.deferred = []
        self.failures = []
        self.serial = 0
        self.signals = _Done(self)
        self.signals.ready.connect(self.completed, Qt.QueuedConnection)

    @Slot(int)
    def completed(self, token):
        entry = self.tasks.pop(token, None)
        if entry and self.draining and getattr(entry[1], '_exit_failed', False):
            self.failures.append(entry[1])

    def submit(self, pool, task, essential=False):
        self.pools.add(pool)
        if self.draining and not essential:
            self.deferred.append(lambda: self.submit(pool, task))
            return
        self.serial += 1
        wrapper = _Tracked(task, self.serial, self.signals)
        self.tasks[self.serial] = (pool, task, wrapper)
        try:
            pool.start(wrapper)
        except BaseException:
            self.tasks.pop(self.serial, None)
            raise

    def start_thread(self, thread):
        if self.draining:
            self.deferred.append(lambda: self.start_thread(thread))
            return
        self.threads = [t for t in self.threads if t.is_alive()]
        self.threads.append(thread)
        thread.start()

    def begin(self, owner=None):
        self.owner = owner
        self.draining = True
        for _, task, _ in list(self.tasks.values()):
            cancel = getattr(task, 'cancel', None)
            if callable(cancel):
                cancel()
            elif isinstance(cancel, threading.Event):
                cancel.set()
            cancelled = getattr(task, 'cancelled', None)
            if isinstance(cancelled, threading.Event):
                cancelled.set()

    def pending(self):
        running = sum(pool.activeThreadCount() for pool in list(self.pools) if isValid(pool))
        return max(len(self.tasks), running) + len(self.failures) + sum(t.is_alive() for t in self.threads)

    def resume(self):
        self.draining = False
        self.owner = None
        self.failures.clear()
        deferred, self.deferred = self.deferred, []
        for start in deferred:
            start()

    def finish(self):
        self.deferred.clear()


def task_gate():
    app = QApplication.instance()
    if app is None:
        return None
    if not hasattr(app, '_exit_tasks'):
        app._exit_tasks = ExitTasks(app)
    return app._exit_tasks


def submit(pool, task, *, essential=False):
    gate = task_gate()
    # Keep injectable synchronous test executors working as before.
    if gate is None or not isinstance(pool, QThreadPool):
        pool.start(task)
    else:
        gate.submit(pool, task, essential)


def start_thread(thread):
    gate = task_gate()
    if gate is None:
        thread.start()
    else:
        gate.start_thread(thread)


def try_take(pool, task):
    """Preserve the existing cancellation of obsolete queued Qt jobs."""
    gate = task_gate()
    if gate is not None and isinstance(pool, QThreadPool):
        for token, (owner, original, wrapper) in list(gate.tasks.items()):
            if owner is pool and original is task:
                if pool.tryTake(wrapper):
                    gate.tasks.pop(token, None)
                    return True
                return False
    return pool.tryTake(task)
