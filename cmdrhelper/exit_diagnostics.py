"""Read-only, payload-free snapshots of the existing exit machinery.

No probing, retrying or waiting for workers. Futures/queues may change while a
snapshot is collected: counts are observations, not completion acknowledgements.
"""
import json
import logging
import time

from PySide6.QtWidgets import QApplication
from shiboken6 import isValid
from cmdrhelper.logging_config import log_event

logger = logging.getLogger(__name__)


def _category(task):
    module = type(task).__module__.split('.')
    name = module[-1]
    for category, parts in {
        'mining': ('mining',), 'screenshot': ('screenshot',),
        'download': ('download', 'update'), 'edsm': ('edsm',),
        'inara': ('inara',), 'history': ('history', 'repair'),
        'journal': ('journal', 'source', 'startup'),
    }.items():
        if module[0] == 'cmdrhelper' and any(part in name for part in parts):
            return category
    return 'other'


def snapshot(state=None, controller=None):
    now = time.monotonic()
    app = QApplication.instance()
    gate = controller.gate if controller else getattr(app, '_exit_tasks', None)
    phase = getattr(controller, 'phase', 'idle')
    if phase not in ('idle', 'drafts', 'draining', 'finished'):
        phase = 'unknown'
    result = dict(schema_version=1, phase=phase,
                  controller_available=controller is not None, state_available=state is not None,
                  wait_seconds=round(max(0, now - getattr(controller, 'started', now)), 1)
                  if phase == 'draining' else 0,
                  sealed=bool(getattr(controller, 'sealed', False)),
                  cancel_requested=bool(getattr(controller, 'cancel_requested', False)),
                  categories={}, reasons=[], writer_states={})
    categories, reasons = result['categories'], result['reasons']
    if getattr(controller, '_diagnostic_settings_error', False):
        reasons.append('settings_save_failed')
    workers = dict(queued=0, running=0, result_pending=0, failed=0,
                   python_running=0, qt_active=0, deferred=0, oldest_seconds=0)
    if gate:
        entries = list(gate.tasks.values())
        workers.update(failed=len(gate.failures), deferred=len(gate.deferred),
                       python_running=sum(t.is_alive() for t in list(gate.threads)),
                       qt_active=sum(p.activeThreadCount() for p in list(gate.pools) if isValid(p)))
        for _, task, tracked in entries:
            status = ('result_pending' if tracked.finished_at is not None else
                      'running' if tracked.started_at is not None else 'queued')
            workers[status] += 1
            category = categories.setdefault(_category(task), dict(queued=0, running=0, result_pending=0))
            category[status] += 1
            workers['oldest_seconds'] = max(workers['oldest_seconds'], int(max(0, now - tracked.submitted_at)))
        for thread in list(gate.threads):
            if not thread.is_alive():
                continue
            category = {'CMDRHelper-Source': 'journal', 'CMDRHelper-JournalIndex': 'journal',
                        'CMDRHelper-Database-Import': 'history', 'CMDRHelper-JournalCatchup': 'journal',
                        'CMDRHelper-Inara-Upload': 'inara', 'CMDRHelper-EDSM-Upload': 'edsm'}.get(thread.name, 'other')
            counts = categories.setdefault(category, {})
            counts['python_running'] = counts.get('python_running', 0) + 1
    result['workers'] = workers
    if workers['running'] or workers['python_running'] or workers['qt_active']:
        reasons.append('worker_still_running')
    if workers['result_pending']:
        reasons.append('result_pending')
    if workers['failed']:
        reasons.append('worker_failed')
    from cmdrhelper.market_writer import active_writers
    observers = list(getattr(controller, 'observers', ()))
    observer = getattr(state, 'observed_markets', None)
    if observer is not None and observer not in observers:
        observers.append(observer)
    sources = getattr(state, 'sources', None)
    watchers = [getattr(state, 'watcher', None)]
    watchers += [getattr(rt, 'watcher', None) for rt in getattr(sources, 'runtimes', {}).values()]
    for watcher in watchers:
        for observer in getattr(watcher, 'live_observers', ()):
            if hasattr(observer, 'pending') and hasattr(observer, 'writer') and observer not in observers:
                observers.append(observer)
    writers = set(active_writers()) | {o.writer for o in observers if getattr(o, 'writer', None) is not None}
    market = dict(writers=len(writers), threads_alive=0, queued=0, running=0,
                  pending=0, failed=0, initialization_failed=0, write_failed=0,
                  cleanup_failed=0, last_error_present=False, result_pending=0,
                  captures_open=0, captures_expired=0, discarded_writes=0,
                  discarded_captures=0, expired_captures_discarded=0, writers_with_discarded_errors=0)
    for writer in writers:
        status = writer.status
        if status not in ('starting', 'migrating', 'active', 'write_error', 'migration_error', 'closed'):
            status = 'unknown'
        result['writer_states'][status] = result['writer_states'].get(status, 0) + 1
        market['writers_with_discarded_errors'] += bool(getattr(writer, 'exit_errors_discarded', False))
        if 'market_observation_conflict' in getattr(writer, '_failure_codes', {}).values():
            if 'market_observation_conflict' not in reasons:
                reasons.append('market_observation_conflict')
        accepted = list(writer._accepted)
        market['threads_alive'] += not writer.is_stopped()
        market['queued'] += sum(not f.done() and not f.running() for f in accepted)
        market['running'] += sum(f.running() for f in accepted)
        market['pending'] += sum(not f.done() for f in accepted)
        market['last_error_present'] |= writer.last_error is not None
        # Keys also contain private identity and timestamps. Inspect only kind.
        failures = list(writer._failures)
        market['failed'] += len(failures)
        for key in failures:
            field = {'initialize': 'initialization_failed', 'record': 'write_failed',
                     'cleanup': 'cleanup_failed'}.get(key[0])
            if field:
                market[field] += 1
    for observer in observers:
        market['discarded_writes'] += getattr(observer, 'exit_discarded_writes', 0)
        market['discarded_captures'] += getattr(observer, 'exit_discarded_captures', 0)
        market['expired_captures_discarded'] += getattr(observer, 'exit_expired_captures', 0)
        market['result_pending'] += sum(f.done() for _, f in getattr(observer, '_writes', ()))
        pending = getattr(observer, 'pending', None)
        if pending is not None:
            market['captures_open'] += 1
            market['captures_expired'] += pending[2] <= observer.monotonic()
    result['market'] = market
    for field, code in (('discarded_writes', 'market_write_discarded'),
                        ('discarded_captures', 'market_capture_discarded'),
                        ('expired_captures_discarded', 'market_capture_expired'),
                        ('writers_with_discarded_errors', 'market_errors_discarded')):
        if market[field]:
            reasons.append(code)
    if market['running'] and 'worker_still_running' not in reasons:
        reasons.append('worker_still_running')
    if market['result_pending'] and 'result_pending' not in reasons:
        reasons.append('result_pending')
    for field, code in (('initialization_failed', 'market_initialization_failed'),
                        ('write_failed', 'market_write_failed'), ('cleanup_failed', 'market_cleanup_failed'),
                        ('captures_expired', 'market_capture_expired')):
        if market[field]:
            reasons.append(code)
    if market['last_error_present'] and not market['failed']:
        reasons.append('market_error_unclassified')
    mining = getattr(state, 'mining_inventory_controller', None)
    result['mining'] = dict(running=bool(getattr(mining, '_running', False)),
                            dirty=bool(getattr(mining, '_dirty', False)),
                            failed=bool(getattr(mining, '_exit_write_error', False)))
    for name in ('timer', 'cargo_retry'):
        timer = getattr(mining, name, None)
        result['mining'][name + '_active'] = bool(timer and timer.isActive())
    if result['mining']['failed']:
        reasons.append('mining_checkpoint_failed')
    result['journal'] = {key: bool(getattr(state, attr, False)) for key, attr in (
        ('index_running', '_initial_journal_index_running'), ('import_running', '_database_import_running'),
        ('catchup_running', '_journal_catchup_running'), ('startup_completed', '_startup_completed'))}
    result['journal'].update(source_running=bool(getattr(sources, 'running', False)),
                             ingesting=bool(getattr(sources, '_ingesting', False)),
                             projecting=bool(getattr(sources, 'projecting', False)),
                             queued=len(getattr(sources, 'queue', ())))
    result['transfers'] = dict(edsm_running=bool(getattr(state, '_edsm_upload_running', False)),
                               inara_running=bool(getattr(state, '_inara_upload_running', False)),
                               source_errors=sum(bool(getattr(rt, 'transfer_error', '')) for rt in
                                                 getattr(sources, 'runtimes', {}).values()),
                               source_deferred=sum(bool(getattr(rt, 'startup_transfer_deferred', False)) for rt in
                                                   getattr(sources, 'runtimes', {}).values()))
    # The existing controller owns the authoritative aggregate (which includes
    # failed work). Reporting it does not change its completion rules.
    result['pending_count'] = controller.pending() if controller else (
        gate.pending() if gate else 0) + market['pending'] + market['captures_open'] + bool(any(result['mining'].values()))
    return result


def record(controller, *, event='progress', force=False):
    """Use the existing polling loop; one sample/s, heartbeat every 30 seconds."""
    now = time.monotonic()
    if event == 'started':
        controller._diagnostic_settings_at = -100
    if event in ('started', 'cancelled', 'finished'):
        controller._diagnostic_settings_error = False
    if event == 'settings_failed':
        controller._diagnostic_settings_error = True
        if now - getattr(controller, '_diagnostic_settings_at', -100) < 30:
            return
        controller._diagnostic_settings_at = now
    if not force and now - getattr(controller, '_diagnostic_sample_at', -100) < 1:
        return
    controller._diagnostic_sample_at = now
    try:
        data = snapshot(controller.state, controller)
        controller._diagnostic_latest = data
        stable = dict(data)
        stable.pop('wait_seconds')
        stable['workers'] = {k: v for k, v in data['workers'].items() if k != 'oldest_seconds'}
        signature = json.dumps(stable, sort_keys=True)
        if (not force and signature == getattr(controller, '_diagnostic_signature', None)
                and now - getattr(controller, '_diagnostic_logged_at', -100) < 30):
            return
        controller._diagnostic_signature = signature
        controller._diagnostic_logged_at = now
        # Each section contains only fixed keys + numeric/boolean observations.
        log_event(logger, 'Exit diagnostic state', component='exit', phase=data['phase'],
                  exit_event=event, count=data['pending_count'], wait_seconds=int(data['wait_seconds']))
        for section in ('workers', 'market', 'mining', 'journal', 'transfers'):
            log_event(logger, 'Exit diagnostic detail', component='exit', exit_category=section,
                      **data[section])
        for status, count in data['writer_states'].items():
            log_event(logger, 'Exit market writer state', component='exit', writer_state=status, count=count)
        for category, counts in data['categories'].items():
            log_event(logger, 'Exit diagnostic tasks', component='exit', exit_category=category, **counts)
        for reason in data['reasons']:
            log_event(logger, 'Exit diagnostic reason', component='exit', reason=reason)
    except Exception:
        # Observation must never change the shutdown outcome or leak payloads.
        if now - getattr(controller, '_diagnostic_logged_at', -100) >= 30:
            controller._diagnostic_logged_at = now
            log_event(logger, 'Exit diagnostic unavailable', component='exit', reason='diagnostic_unavailable')
