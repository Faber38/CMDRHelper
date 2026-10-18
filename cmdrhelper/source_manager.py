"""GUI-owned source runtimes with one serialized database ingestion worker."""
from copy import copy
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
import time
from PySide6.QtCore import QObject, QTimer, Signal, Qt, QSettings
from .journal_sources import SourceRegistry, discover
from .journal_watcher import JournalWatcher
from .source_processing import SourceProcessor
from .game_instances import inspect_instances, confirmed_selection, ProcessSnapshot
from . import startup_runtime as startup


@dataclass
class SourceRuntime:
    source: object
    watcher: object
    processor: object
    generation: int
    tracking: object = None
    transfer_error: str = ''
    live_events: list = field(default_factory=list)
    last_transfer_at: float = 0
    transfer_results: dict = field(default_factory=dict)


class SourceManager(QObject):
    changed = Signal()
    finished = Signal(object, int, object, str)

    def __init__(self, state):
        super().__init__(state)
        self.state = state
        self.registry = SourceRegistry(state.settings, discover())
        from .journal_catchup import load_sessions
        retained = load_sessions(state.database)
        for source in self.registry.sources:
            # Historical observations come from the FID-checked database, not
            # from user-editable source labels. They are not process evidence.
            source.identities = sorted({(r['fid_seen'], r.get('commander_name_seen') or '')
                for r in retained if Path(r['journal_file']).parent == Path(source.path)
                and r.get('attribution_status') == 'identified' and r.get('fid_seen')})
        self.runtimes = {}
        self.queue = []
        self.running = False
        self.manual_requested = False
        self.manual_pending = None
        self.manual_errors = []
        self.manual_total = 0
        self.projecting = False
        self.generation = 0
        self.snapshot = ProcessSnapshot(False)
        self.preferred_source = state.settings.value('commander_view/source_id', '')
        self.projected_source = None
        self.projection_key = None
        saved_fid = state.settings.value('commander_view/fid', '')
        if saved_fid:
            matching = [c for c in state.database.list_commanders() if c['fid'] == saved_fid]
            state.viewed_commander_id = matching[0]['id'] if len(matching) == 1 else None
        self.finished.connect(self._finished, Qt.QueuedConnection)
        self.timer = QTimer(self)
        self.timer.setInterval(3000)
        self.timer.timeout.connect(self._tick)

    def start(self):
        self.reconcile()
        self.timer.start()
        self._tick()
        # An empty (or entirely disabled) source registry has no request callback.
        # Let the existing queue completion path finish startup in that case too.
        self._next()

    def stop(self):
        self.timer.stop()
        for runtime in self.runtimes.values():
            runtime.watcher.stop()
            for observer in runtime.watcher.live_observers:
                if hasattr(observer, 'close'):
                    observer.close()

    def reconcile(self):
        enabled = {s.id: s for s in self.registry.enabled()}
        for identity, runtime in list(self.runtimes.items()):
            if identity not in enabled or runtime.processor.path != Path(enabled[identity].path):
                runtime.watcher.stop()
                for observer in runtime.watcher.live_observers:
                    if hasattr(observer, 'close'):
                        observer.close()
                del self.runtimes[identity]
        for identity, source in enabled.items():
            if identity in self.runtimes:
                self.runtimes[identity].source = source
                continue
            self.generation += 1
            watcher = JournalWatcher(self)
            from .bounty_manager import BountyManager
            from .combat_bond_manager import CombatBondManager
            from .observed_market_observer import ObservedMarketObserver
            observers = []
            for manager_type, viewed in ((BountyManager, self.state.bounties),
                                         (CombatBondManager, self.state.combat_bonds)):
                observer = manager_type(root=viewed._root, parent=self)
                # Balances are commander keyed; input cursors/boundaries remain
                # source local. Keep the existing UI manager/signal connections.
                for attribute in ('states', 'damaged', 'known_snapshots', 'storage_errors'):
                    setattr(observer, attribute, getattr(viewed, attribute))
                observer.changed.connect(viewed.changed.emit)
                observers.append(observer)
            observers.append(ObservedMarketObserver(on_changed=self.state.observedMarketsChanged.emit,
                                                    use_market_store=True))
            watcher.live_observers = observers
            watcher.set_folder(source.path)
            runtime = SourceRuntime(source, watcher, SourceProcessor(copy(self.state.database), source.path), self.generation)
            from .odyssey_tracking import OdysseyCarrierTracking
            proxy = SimpleNamespace(settings=self.state.settings, database=runtime.processor.database,
                watcher=watcher, commander_id=None, commander_fid='', _journal_index_sessions=[],
                odysseySidecarsChanged=self.state.odysseySidecarsChanged)
            runtime.tracking = OdysseyCarrierTracking(proxy)
            watcher.odysseyTrackingUpdated.connect(runtime.tracking.poll)
            self.runtimes[identity] = runtime
            watcher.journalChanged.connect(lambda sid=identity: self.request(sid))
            watcher.odysseySidecarsChanged.connect(self.state.odysseySidecarsChanged.emit)
            watcher.start()
            self.request(identity)
        self.changed.emit()

    def request(self, identity):
        if identity in self.runtimes and identity not in self.queue:
            self.queue.append(identity)
        QTimer.singleShot(0, self._next)

    def reimport(self):
        self.manual_requested = True
        QTimer.singleShot(0, self._next)

    def _next(self):
        if self.running or self.state._startup_cancel.is_set():
            return
        if self.manual_requested:
            self.manual_requested = False
            self.manual_pending = set(self.runtimes)
            self.manual_total = len(self.manual_pending)
            self.manual_errors = []
            for identity, runtime in self.runtimes.items():
                runtime.processor.initialized = False
                if identity not in self.queue:
                    self.queue.append(identity)
        if self.manual_pending is not None:
            self.manual_pending.intersection_update(self.runtimes)
            if not self.manual_pending:
                self.manual_pending = None
                self.state.databaseImportFinished.emit(self.state.database.stats(), ', '.join(self.manual_errors))
        while self.queue:
            identity = self.queue.pop(0)
            runtime = self.runtimes.get(identity)
            if runtime is None:
                continue
            self.running = True
            runtime.source.status = 'reading'
            # Snapshot per-FID upload authorization on the GUI thread. The
            # ingestion worker never consults a mutable displayed commander.
            settings = self.state.settings
            fids = set()
            configs = {}
            for commander in self.state.database.list_commanders():
                fid = commander['fid']
                config = self.state.inara_settings_for_fid(fid)
                configs[fid] = (self.state.edsm_settings_for_fid(fid), config)
                if config['enabled'] and config['api_key']:
                    fids.add(fid)

            settings_path, settings_format = settings.fileName(), settings.format()
            legacy = settings.value('journal_folder', '')
            folders = [s.path for s in self.registry.sources]

            source_snapshot = copy(runtime.source)
            def worker(rt=runtime, allowed=fids, service_configs=configs, bound_source=source_snapshot):
                rows, error = None, ''
                try:
                    was_initialized = rt.processor.initialized
                    rows = rt.processor.process(cancel=self.state._startup_cancel, enqueue_fids=allowed)
                    rt.live_events = list(rt.processor.context.get('applied_events', [])) if was_initialized else []
                    from .source_transfers import transfer
                    current = lambda: (not self.state._startup_cancel.is_set()
                        and self.runtimes.get(rt.source.id) is rt and rt.source.enabled)
                    try:
                        results = transfer(rt.processor.database, bound_source, rows, service_configs,
                            QSettings(settings_path, settings_format), is_current=current,
                            legacy_folder=legacy, source_folders=folders)
                        rt.transfer_results = results
                        rt.transfer_error = 'service_pending' if any(
                            result.get('error') if isinstance(result, dict) else result[1]
                            for result in results.values()) else ''
                    except Exception as exc:
                        # Service failures must not revoke a committed journal
                        # batch or prevent another source from being processed.
                        rt.transfer_error = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
                    rt.last_transfer_at = time.monotonic()
                except startup.StartupCancelled:
                    return
                except Exception as exc:
                    error = getattr(exc, 'reason', None) or type(exc).__name__
                self.finished.emit(rt.source.id, rt.generation, rows, error)

            startup.start(self.state, worker, 'CMDRHelper-Source',
                          lambda exc: self.finished.emit(identity, runtime.generation, None, type(exc).__name__), ())
            self.changed.emit()
            return
        startup.complete(self.state)

    def _finished(self, identity, generation, rows, error):
        self.running = False
        if self.state._startup_cancel.is_set():
            return
        runtime = self.runtimes.get(identity)
        if self.manual_pending is not None and identity in self.manual_pending:
            self.manual_pending.discard(identity)
            if error:
                self.manual_errors.append(error)
            self.state.databaseImportProgress.emit(self.manual_total - len(self.manual_pending),
                self.manual_total, runtime.source.name if runtime else '')
        if runtime is not None and runtime.generation == generation:
            source = runtime.source
            for (fid, service), result in runtime.transfer_results.items():
                failed = result.get('error') if isinstance(result, dict) else bool(result[1])
                message = str(failed or '')
                cache = getattr(self.state, '_'+service+'_runtime_by_fid')
                cache[fid] = ('error' if failed else 'ok', message)
                if self.state.commander_fid == fid:
                    setattr(self.state, service+'_upload_status', cache[fid][0])
                    setattr(self.state, service+'_upload_message', cache[fid][1])
            source.status = 'unreachable' if not Path(source.path).is_dir() else 'error' if error else 'ready'
            if rows is not None:
                source.identities = sorted({(r['fid_seen'], r.get('commander_name_seen') or '')
                    for r in rows if r.get('attribution_status') == 'identified' and r.get('fid_seen')})
                if not rows or rows[-1].get('attribution_status') != 'identified':
                    source.status = 'unknown'
                latest = rows[-1] if rows else {}
                if latest.get('attribution_status') == 'identified':
                    for observer in runtime.watcher.live_observers:
                        if hasattr(observer, 'identify'):
                            observer.identify(latest['fid_seen'], latest.get('commander_name_seen') or '',
                                              latest['journal_file'])
                runtime.tracking.state.commander_id = latest.get('commander_id')
                runtime.tracking.state.commander_fid = latest.get('fid_seen') or ''
                runtime.tracking.state._journal_index_sessions = rows
                runtime.tracking.poll()
                context = runtime.processor.context
                runtime.watcher._catchup_signatures = {
                    name: context['baseline'][name]['signature']
                    for name in context['tracked'] if name in context['baseline']}
                runtime.watcher._catchup_requested = False
            runtime.watcher.refresh_finished(not error)
            if not error:
                self.state.database._bio_predictor_cache = None
                self.state.database._bio_predictor_revision = None
                for kind in self.state._inventory_revisions:
                    self.state._inventory_revisions[kind] += 1
                self.state.inventoryChanged.emit()
        self.choose()
        self.refresh_selected()
        self.state.changed.emit()
        self.changed.emit()
        self._next()

    def _tick(self):
        self.snapshot = inspect_instances()
        self.choose()
        for identity, runtime in self.runtimes.items():
            if not runtime.processor.initialized and runtime.source.status != 'reading':
                self.request(identity)
            elif time.monotonic() - runtime.last_transfer_at >= 30:
                if any(self.state.edsm_settings_for_fid(fid)['enabled']
                       or self.state.inara_settings_for_fid(fid)['enabled']
                       for fid, _ in runtime.source.identities):
                    self.request(identity)
        self.refresh_selected()

    def choose(self):
        state = self.state
        selected = confirmed_selection(self.snapshot, self.runtimes.values())
        if selected and state.follow_live_commander:
            self.preferred_source, cid, fid = selected
            if any(c['id'] == cid and c['fid'] == fid for c in state.database.list_commanders()):
                self._select(cid)
        elif state.viewed_commander_id is None:
            # First use only: a sole known commander needs no extra setup.
            known = state.database.list_commanders()
            if (len(known) == 1 and state._saved_viewed_commander_id() is None
                    and not state.settings.value('commander_view/fid', '')):
                self._select(known[0]['id'])

    def _select(self, cid):
        state = self.state
        changed = state.viewed_commander_id != cid
        state.viewed_commander_id = cid
        state.settings.setValue('commander_view/viewed_commander_id', cid)
        commander = next(c for c in state.database.list_commanders() if c['id'] == cid)
        state.settings.setValue('commander_view/fid', commander['fid'])
        state.settings.setValue('commander_view/follow_live', state.follow_live_commander)
        state.settings.setValue('commander_view/source_id', self.preferred_source)
        state.settings.sync()
        if changed:
            state.viewedCommanderChanged.emit(cid)

    def refresh_selected(self):
        state = self.state
        if self.running or self.projecting or state._startup_cancel.is_set():
            return False
        cid = state.viewed_commander_id
        summary = state.database.commander_summary(cid) if cid is not None else None
        if not summary:
            return False
        fid = summary['fid']
        candidates = []
        for runtime in self.runtimes.values():
            rows = [r for r in runtime.processor.sessions if r.get('commander_id') == cid
                    and r.get('fid_seen') == fid and r.get('attribution_status') == 'identified']
            if rows:
                candidates.append((runtime, rows))
        preferred = [pair for pair in candidates if pair[0].source.id == self.preferred_source]
        pair = preferred[0] if preferred else candidates[0] if len(candidates) == 1 else None
        if pair is None:
            if state.commander_id != cid or self.projected_source is not None:
                state._invalidate_inara_worker()
                state._invalidate_edsm_worker()
                state.reset_commander_runtime_state()
                self.projected_source = None
                self.projection_key = None
                state.journal_folder = None
                state._source_live_context = False
                state._journal_index_sessions = []
                state.commander_id, state.commander_fid = cid, fid
                state.database.set_active_commander(cid)
                state._restore_persistent_commander_state(summary)
                state._load_live_edsm_settings()
                state._load_live_inara_settings()
                state.commanderIdentityChanged.emit(cid, fid, state.commander)
                state.changed.emit()
            return True
        runtime, rows = pair
        try:
            stat = Path(rows[-1]['journal_file']).stat()
        except OSError:
            return False
        projection_key = (cid, fid, runtime.source.id, runtime.source.status, rows[-1]['journal_file'],
            rows[-1]['last_read_offset'], stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        if projection_key == self.projection_key and not runtime.live_events:
            return True
        from .journal_reader import read_latest_state
        try:
            data = read_latest_state(Path(runtime.source.path), indexed_sessions=rows, powerplay_history=False)
        except OSError:
            return False
        current = data.get('latest_journal_session') or {}
        if (data.get('commander_fid') != fid or current.get('fid_seen') != fid
                or current.get('attribution_status') != 'identified'):
            return False
        # Bind presentation to verified bytes, not to the latest notification
        # from an unrelated watcher. No ingestion runs during this projection.
        self.projecting = True
        if self.projected_source != runtime.source.id:
            state._invalidate_inara_worker()
            state._invalidate_edsm_worker()
            state.reset_commander_runtime_state()
        self.projected_source = runtime.source.id
        self.preferred_source = runtime.source.id
        state.settings.setValue('commander_view/source_id', self.preferred_source)
        state.watcher = runtime.watcher
        state.odyssey_carrier_tracking = runtime.tracking
        state.journal_folder = Path(runtime.source.path)
        state._journal_index_sessions = rows
        state._journal_index_current = str(runtime.watcher._current) if runtime.watcher._current else None
        state._source_projection_data = data
        state._source_live_context = bool(runtime.processor.sessions
            and current.get('journal_file') == runtime.processor.sessions[-1].get('journal_file')
            and runtime.source.status == 'ready')
        state._source_projection_events = [e for path, event_fid, e in runtime.live_events
            if path == current.get('journal_file') and event_fid == fid]
        selected = confirmed_selection(self.snapshot, self.runtimes.values())
        state._watcher_live_refresh = bool(state._source_projection_events and selected
            and selected[0] == runtime.source.id and selected[2] == fid)
        try:
            success = state.refresh()
            if success:
                runtime.live_events = []
                self.projection_key = projection_key
            return success
        finally:
            state._source_projection_data = None
            state._source_projection_events = []
            state._watcher_live_refresh = False
            self.projecting = False

    def rediscover(self):
        self.registry.merge(discover())
        self.reconcile()
