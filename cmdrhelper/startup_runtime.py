"""Small lifecycle helpers for the existing startup threads; no Qt ownership."""
import logging
import sqlite3
import threading
import time

logger = logging.getLogger('cmdrhelper.startup_runtime')


class StartupCancelled(Exception):
    pass


class JournalPending(OSError):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def diagnostic(component, phase, error=None, *, reason=None, status='pending'):
    fields = dict(component=component, phase=phase, status=status,
                  reason=reason or getattr(error, 'reason', None) or (
                      'sqlite_error' if isinstance(error, sqlite3.Error) else
                      'os_error' if isinstance(error, OSError) else 'unexpected_error' if error is not None else None))
    for attribute, key in [('errno', 'errno'), ('winerror', 'winerror'),
                           ('sqlite_errorcode', 'sqlite_code')]:
        value = getattr(error, attribute, None)
        if type(value) is int:
            fields[key] = value
    logger.warning('Background operation status', extra={'diagnostic_fields': fields})


def prepare(state):
    if not hasattr(state, '_startup_cancel'):
        state._startup_cancel = threading.Event()
        state._startup_threads = []


def check(state):
    if getattr(state, '_startup_cancel', None) is not None and state._startup_cancel.is_set():
        raise StartupCancelled()


def emit(state, signal, *args):
    if getattr(state, '_startup_cancel', None) is not None and state._startup_cancel.is_set():
        return False
    try:
        getattr(state, signal).emit(*args)
        return True
    except RuntimeError as exc:
        diagnostic('startup', 'delivery', exc, reason='qt_signal_unavailable', status='critical')
        state.startup_status = 'critical'
        if signal == 'journalCatchupReady':
            state._journal_catchup_running = False
        return False


def issue(state, component, error=None):
    issues = getattr(state, 'startup_issues', [])
    if component not in issues:
        state.startup_issues = [*issues, component]
    diagnostic(component, 'history', error, status='partial')


def complete(state, error=''):
    if getattr(state, '_startup_cancel', None) is not None and state._startup_cancel.is_set():
        return
    if getattr(state, '_startup_completed', False):
        return
    state._startup_completed = True
    state.startup_status = 'critical' if error else ('partial' if getattr(state, 'startup_issues', []) else 'success')
    logger.info('Startup completed', extra={'diagnostic_fields': {
        'component': 'startup', 'phase': 'complete', 'status': state.startup_status}})
    emit(state, 'initializationFinished', error)


def start(state, target, name, failed, flags):
    prepare(state)
    if state._startup_cancel.is_set():
        return

    def run():
        try:
            check(state)
            target()
        except StartupCancelled:
            pass
        except Exception as exc:
            for flag in flags:
                setattr(state, flag, False)
            diagnostic('startup', 'failure', exc, status='critical')
            failed(exc)
        finally:
            if state._startup_cancel.is_set():
                for flag in flags:
                    setattr(state, flag, False)

    try:
        state._startup_threads = [t for t in state._startup_threads if t.is_alive()]
        thread = threading.Thread(target=run, daemon=True, name=name)
        state._startup_threads.append(thread)
        thread.start()
    except Exception as exc:
        for flag in flags:
            setattr(state, flag, False)
        diagnostic('startup', 'started', exc, reason='thread_start_failed', status='critical')
        failed(exc)


def shutdown(state, timeout=5.0):
    prepare(state)
    state._startup_cancel.set()
    mining = getattr(state, 'mining_inventory_controller', None)
    if mining is not None:
        mining.close()
    watcher = getattr(state, 'watcher', None)
    if watcher is not None:
        watcher.stop()
    deadline = time.monotonic() + timeout
    for thread in state._startup_threads:
        if thread is not threading.current_thread() and thread.is_alive():
            thread.join(max(0, deadline - time.monotonic()))
    remaining = sum(thread.is_alive() for thread in state._startup_threads)
    if getattr(state, '_shutdown_remaining', None) == remaining:
        return remaining == 0
    state._shutdown_remaining = remaining
    logger.info('Startup workers shutdown', extra={'diagnostic_fields': {
        'component': 'startup', 'phase': 'shutdown', 'status': 'pending' if remaining else 'cancelled',
        'remaining': remaining}})
    return remaining == 0
